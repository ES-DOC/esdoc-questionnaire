import sys
import inspect
from django.utils.datastructures import SortedDict

# module imports

from django.forms import *
from django.forms.models import BaseForm, BaseFormSet, BaseInlineFormSet, BaseModelFormSet, formset_factory, inlineformset_factory, modelform_factory, modelformset_factory
from django.utils.functional import curry

# intra/inter-package imports

from django_cim_forms.models import *

###########################
# get a form from a model #
###########################

# this relies on...
#   1) having the form called "<ModelClass._name>_form"
#   2) having the module where the form is defined already loaded at this point
# the former can be handled by code-generation
# the latter can be handled by adding imports to __init__.py

# previously I had code that checked all subclasses of MetadataForm
# to see which one had ModelClass as their meta model
# but that would have broken if for some reason an app had more than one form for the same model

def getFormClassFromModelClass(ModelClass):
    form_name = ModelClass._name + "_form"
    app_name = ModelClass._meta.app_label
    # I assume that the form class is defined in 'app_name.forms.form_name' but I can't be certain
    # so I loop through all valid variants of app_name using this list comprehension
    for (full_app_name,app_module) in [(key,value) for (key,value) in sys.modules.iteritems() if app_name in key and value]:
        try:
            FormClass = getattr(app_module,form_name)
            return FormClass
        except AttributeError:
            pass
    return None

##############################################
# the types of subforms that a form can have #
##############################################

class SubFormType(EnumeratedType):
    pass

SubFormTypes = EnumeratedTypeList([
    SubFormType("FORM","Form",BaseForm),
    SubFormType("FORMSET","FormSet",BaseFormSet),
    SubFormType("INLINE_FORMSET","Inline FormSet",BaseInlineFormSet),
])

##########################################################################
# this is a way to customise _any_ widgets used by metadata forms        #
# without having to hard-code _all_ of them; it inserts some css classes #
# and the template knows what to do with that (currently JQuery stuff)   #
##########################################################################

def customize_metadata_widgets(field):
    formfield = field.formfield()
    try:
        # some fields have the isFixed method, which means they should be readonly
        if field.isFixed():
            formfield.widget.attrs.update({"readonly" : "readonly"})
    except AttributeError:
        pass

    if isinstance(field,models.DateField):
        formfield.widget.attrs.update({"class" : "datepicker"})
    if isinstance(field,MetadataEnumerationField):
        if field.isOpen():
            formfield.widget.attrs.update({"class" : "editable"})
    if isinstance(field,MetadataCVField):
        pass
    if isinstance(field,MetadataEnablerField):
        java_string = "toggleFields([%s])" % ",".join([u'"%s"'%f for f in field.getFieldsToEnable()])
        formfield.widget.attrs.update({"onclick" : java_string})
        if not field.getStartEnabled():
            formfield.widget.attrs.update({"class" : "enabler start-disabled"})
        else:
            formfield.widget.attrs.update({"class" : "enabler start-enabled"})

    if isinstance(field,MetadataDocumentField):
        formfield.widget.attrs.update({"class" : "adder"})
        formfield.widget.attrs.update({"title": u'%s/%s'%(field.getAppName(),field.getModelName())})

    if isinstance(field,MetadataAbstractField):
        java_string = "toggleForm($(this).val(),[%s])" % ",".join([u'"%s"' % choice[0] for choice in field.getChoices()])
        formfield.widget.attrs.update({"onclick" : java_string})
        formfield.widget.attrs.update({"class":"abstract-choice"})
        
    # TODO: other if branches for other field types?
    
    return formfield

#######################################
# base classes for all Metadata Forms #
#######################################

class MetadataForm(ModelForm):

    _subFormType = SubFormTypes.FORM

    _fieldOrder = ()
    _ordered = False
    
    _subForms = {}      # a form can have subforms
    _request = None     # those subforms need to have HTTP requests passed to them

    _id = None      # the form's corresponding model id
    _guid = None    # the form's corresponding model guid

    _name = ""  # the name of the form class

    def getId(self):
        return self._id

    def getGuid(self):
        return self._guid

    def getName(self):
        return self._name

    def getFullyQualifiedName(self):
        # returns the unicode name of the model
        return u'%s' % self.instance

    def getSubFormType(self):
        return self._subFormType

    def getSubForms(self):
        return self._subForms

    def getAllSubForms(self):
        # returns the union of all subforms for all ancestor classes
        allSubForms = {}
        for ancestor in reversed(inspect.getmro(self.Meta.model)):
            if issubclass(ancestor,MetadataModel):
                ancestorForm = getFormClassFromModelClass(ancestor)
                if ancestorForm:
                    allSubForms = dict(allSubForms.items() + ancestorForm._subForms.items())
        return allSubForms

    @log_class_fn()
    def __init__(self,*args,**kwargs):
        self._request = kwargs.pop('request', None)
        super(MetadataForm,self).__init__(*args,**kwargs)

        self._id = self.instance.id
        self._guid = self.instance.guid

        if self._fieldOrder and not self._ordered:
            # going to re-order the fields...
            # (if you do this, then any fields that aren't specified will not be displayed)
            tmpFields = self.fields.copy()
            self.fields = SortedDict()
            for field in self._fieldOrder:
                self.fields[field] = tmpFields[field]
            self._ordered = True

        # because there are no forward declarations in Python,
        # double-check that all subforms have been set properly
        for key,value in self._subForms.iteritems():
            if isinstance(value,basestring):
                self._subForms[key] = PotentialSubForms[value]
                print "%s in %s was still set to %s; it is now set to %s" % (key,self.getName(),value,self._subForms[key])
                
                
        for key,value in self.getAllSubForms().iteritems():                
        #for key,value in self._subForms.iteritems():
        
            subFormType = value[0]
            subFormClass = value[1]

            if subFormType == SubFormTypes.FORMSET:
                # note that the form attribute is now a curried function
                # (in order for me to propagate request to all subforms)
                # so I have to _call_ it in order to access the subForm
                qs = subFormClass.form().Meta.model.objects.none()
                try:
                    print "TRYING TO GET QUERYSET FOR %s FROM %s" % (key,self.instance)
                    qs = getattr(self.instance,key,None).all()
                except ValueError,AttributeError:
                    # TODO: this doesn't seem to be catching the possible error if the form is malformed?
                    print "failed to get queryset"
                    pass

                if self._request and self._request.method == "POST":
                    # TODO: NOT SURE IF I NEED THE QUERYSET KWARG HERE (DON'T THINK SO)
                    value[2] = subFormClass(self._request.POST,prefix=key,request=self._request)
                else:
                    value[2] = subFormClass(queryset=qs,prefix=key,request=self._request)

            elif subFormType == SubFormTypes.FORM:
                subInstance = None
                if self.instance:
                    subInstance = getattr(self.instance,key,None)

                if self._request and self._request.method == "POST":
                    # TODO: NOT SURE IF I NEED THE INSTANCE KWARG HERE (DON'T THINK SO)
                    value[2] = subFormClass(self._request.POST,request=self._request)
                else:
                    value[2] = subFormClass(instance=subInstance,request=self._request)

#            elif subFormType == SubFormTypeList.INLINE_FORMSET:
#                pass

            else:
                print "unable to determine the type of subform that %s should use for %s" % (self.getName(),key)
                pass


    @log_class_fn()
    def clean(self):
        cleaned_data = self.cleaned_data

        for key,value in self.getAllSubForms().iteritems():
        #for key,value in self._subForms.iteritems():
            subFormType = value[0]
            subFormClass = value[1]
            subFormInstance = value[2]

            if subFormType == SubFormTypes.FORMSET:

                # set the field to the set of subForms that are not marked for deletion and are not empty
                # (is_valid() will have been called by this point so empty forms that _shouldn't_ be empty won't exist)
                for subForm in subFormInstance:
                    if subForm in subFormInstance.deleted_forms:
                        print "deleted"
                    elif subForm.cleaned_data:
                        print "cleaned"
                    else:
                        print "going to save"
                        print subForm.save()

                activeSubForms = [subForm.save() for subForm in subFormInstance if subForm not in subFormInstance.deleted_forms and subForm.cleaned_data]
                cleaned_data[key] = activeSubForms

            elif subFormType == SubFormTypes.FORM:
                # TODO: SHOULDN'T is_valid() HAVE ALREADY BEEN CALLED BY THIS POINT!?!
                if subFormInstance.is_valid():
                    cleaned_data[key] = subFormInstance.save()
                pass
#            elif subFormType == SubFormTypes.INLINE_FORMSET:
#                pass

        return cleaned_data

    @log_class_fn(LoggingTypes.FULL)
    def is_valid(self):
        validity = [subForm[2].is_valid() for subForm in self.getAllSubForms().itervalues() if subForm[2]]
        print "initial validity = %s" % all(validity)
        #validity = [subForm[2].is_valid() for subForm in self._subForms.itervalues() if subForm[2]]
        validity = all(validity) and super(MetadataForm,self).is_valid()
        print "final validity = %s" % validity
        return validity


############################################
# the base class for all Metadata Formsets #
############################################

class MetadataFormSet(BaseModelFormSet):

    _subFormType = SubFormTypes.FORMSET

    _request = None # the individual forms of a formset need to have HTTP requests passed to them
    _prefix = None

    _name = ""  # the name of the form class
    _title = "" # the title (to display) of the form class

    def getSubFormType(self):
        return self._subFormType

    def getPrefix(self):
        return self._prefix

    @log_class_fn()
    def is_valid(self,*args,**kwargs):
        return super(MetadataFormSet,self).is_valid(*args,**kwargs)

    def __init__(self,*args,**kwargs):
        # this adds an extra kwarg, 'request,' to the subforms of this formset
        self._request = kwargs.pop('request', None)
        self.form = curry(self.form,request=self._request)

        super(MetadataFormSet,self).__init__(*args,**kwargs)

        # TODO: do I need to ensure a more unique prefix?
        self._prefix = kwargs.get("prefix",self.get_default_prefix())



# NOT DEALING w/ INLINE-FORMSETS
# (they are an unneccessary complication)
####################################################
## the base class for all Metadata Inline Formsets #
####################################################
#
#class MetadataInlineFormSet(BaseModelFormSet):
#
#    _subFormType = SubFormTypes.INLINE_FORMSET



# decorator which adds generated forms & formsets to the above dictionary
def PotentialSubForm(subFormType=SubFormType("UNKNOWN","Unknown")):
    def decorator(factoryFunction):
        @wraps(factoryFunction)
        def wrapper(*args,**kwargs):
            _form = factoryFunction(*args,**kwargs)
            try:
                name  = kwargs["name"]
                PotentialSubForms[name] = [subFormType, _form, None]
            except KeyError:
                msg = "'name' kwarg is required for %s" % _form
                raise MetadataError(msg)
            _form._subFormType = subFormType
            return _form
        return wrapper
    return decorator


@PotentialSubForm(SubFormTypes.FORM)
def MetadataFormFactory(ModelClass,*args,**kwargs):
    name = kwargs.pop("name","Unnamed Form")
    subForms = kwargs.pop("subForms",{})
    fieldOrder = kwargs.pop("reorder",None)
    # these two kwarg _must_ have these values
    kwargs["form"] = MetadataForm
    kwargs["formfield_callback"] = customize_metadata_widgets
    # the remaining kwargs can be passed into the constructor as needed
    _form = modelform_factory(ModelClass,**kwargs)
    if fieldOrder:
        # the presence of this attribute
        # indicates that the form's fields have a custom order
        # which gets implemented in the __init__ fn
        _form._fieldOrder = fieldOrder
    _form._name = name
    _form._subForms = {} # reset any existing subForms...
    for key,value in subForms.iteritems():
        try:
            _form._subForms[key] = PotentialSubForms[value]        
        except KeyError:
            # no forward declarations in Python
            # I'll try setting this in the __init__ fn
            _form._subForms[key] = value
            pass
    return _form

@PotentialSubForm(SubFormTypes.FORMSET)
def MetadataFormSetFactory(ModelClass,FormClass,*args,**kwargs):
    name = kwargs.pop("name","Unnamed FormSet")
    # these two kwargs _must_ have these values
    kwargs["formset"] = MetadataFormSet
    kwargs["can_delete"] = True
    # the remaining kwargs can be passed into the constructor as needed
    _formset = modelformset_factory(ModelClass,**kwargs)
# TODO: DOUBLE-CHECK THIS CALL TO staticmethod(curry(...))
    # this ensures that the request kwarg passed to formsets gets propagated to all the child forms
    _formset.form = staticmethod(curry(FormClass,request=MetadataFormSet._request))
    _formset._name = name
    return _formset

# nothing to see here,
# move along
#@PotentialSubForm(SubFormTypeList.INLINE_FORMSET)
#def MetadataInlineFormSetFactory(SourceModelClass,TargetModelClass,FormClass,*args,**kwargs):
#    pass

class ComponentProperty_form(MetadataForm):
    class Meta:
        model = ComponentProperty
        widgets = {
            'shortName' : django.forms.fields.TextInput(attrs={'readonly':'readonly'}),
            'longName' : django.forms.fields.TextInput(attrs={'readonly':'readonly'}),
            'value' : django.forms.fields.Select(),
        }
        
    pass

##########################################
# the non-abstract forms used by the CIM #
##########################################


DataSource_form = MetadataFormFactory(DataSource,name="DataSource_form")
DataSource_formset = MetadataFormSetFactory(DataSource,DataSource_form,name="DataSource_formset")

ComponentLanguage_form = MetadataFormFactory(ComponentLanguage,name="ComponentLanguage_form")
ComponentLanguage_formset = MetadataFormSetFactory(ComponentLanguage,ComponentLanguage_form,name="ComponentLanguage_formset")

SoftwareComponent_form = MetadataFormFactory(SoftwareComponent,name="SoftwareComponent_form")
SoftwareComponent_formset = MetadataFormSetFactory(SoftwareComponent,SoftwareComponent_form,name="SoftwareComponent_formset")

ResponsibleParty_form = MetadataFormFactory(ResponsibleParty,name="ResponsibleParty_form")
ResponsibleParty_formset = MetadataFormSetFactory(ResponsibleParty,ResponsibleParty_form,name="ResponsibleParty_formset")

Citation_form = MetadataFormFactory(Citation,name="Citation_form")
Citation_formset = MetadataFormSetFactory(Citation,Citation_form,name="Citation_formset")

Timing_form = MetadataFormFactory(Timing,name="Timing_form")
Timing_formset = MetadataFormSetFactory(Timing,Timing_form,name="Timing_formset")

TimeLag_form = MetadataFormFactory(TimeLag,name="TimeLag_form")
TimeLag_formset = MetadataFormSetFactory(TimeLag,TimeLag_form,name="TimeLag_formset")

SpatialRegriddingUserMethod_form = MetadataFormFactory(SpatialRegriddingUserMethod,name="SpatialRegriddingUserMethod_form")
SpatialRegriddingUserMethod_formset = MetadataFormSetFactory(SpatialRegriddingUserMethod,SpatialRegriddingUserMethod_form,name="SpatialRegriddingUserMethod_formset")

SpatialRegridding_form = MetadataFormFactory(SpatialRegridding,name="SpatialRegridding_form",subForms={"spatialRegriddingUserMethod":"SpatialRegriddingUserMethod_form"})
SpatialRegridding_formset = MetadataFormSetFactory(SpatialRegridding,SpatialRegridding_form,name="SpatialRegridding_formset",extra=3)

TimeTransformation_form = MetadataFormFactory(TimeTransformation,name="TimeTransformation_form")
TimeTransformation_formset = MetadataFormSetFactory(TimeTransformation,TimeTransformation_form,name="TimeTransformation_formset")

ModelComponent_form = MetadataFormFactory(ModelComponent,name="ModelComponent_form",subForms={"responsibleParties" : "ResponsibleParty_formset", "citations" : "Citation_formset"})
ModelComponent_formset = MetadataFormSetFactory(ModelComponent,ModelComponent_form,name="ModelComponent_formset")

Activity_form = MetadataFormFactory(Activity,name="Activity_form",subForms={"responsibleParties" : "ResponsibleParty_formset"})
Activity_formset = MetadataFormSetFactory(Activity,Activity_form,name="Activity_formset")

DateRange_form = MetadataFormFactory(DateRange,name="DateRange_form")
DateRange_formset = MetadataFormSetFactory(DateRange,DateRange_form,name="DateRange_formset")

Calendar_form = MetadataFormFactory(Calendar,name="Calendar_form",subForms={"range":"DateRange_form"})
Calendar_formset = MetadataFormSetFactory(Calendar,Calendar_form,name="Calendar_formset")

NumericalActivity_form = MetadataFormFactory(NumericalActivity,name="NumericalActivity_form")
NumericalActivity_formset = MetadataFormSetFactory(NumericalActivity,NumericalActivity_form,name="NumericalActivity_formset")

CouplingEndPoint_form = MetadataFormFactory(CouplingEndPoint,name="CouplingEndPoint_form")
CouplingEndPoint_formset = MetadataFormSetFactory(CouplingEndPoint,CouplingEndPoint_form,name="CouplingEndPoint_formset")

Coupling_form = MetadataFormFactory(Coupling,name="Coupling_form",subForms={"timeProfile" : "Timing_form", "timeLag" : "TimeLag_form","spatialRegridding":"SpatialRegridding_formset","timeTransformation":"TimeTransformation_form","couplingSource":"CouplingEndPoint_form","couplingTarget":"CouplingEndPoint_form"})
Coupling_formset = MetadataFormSetFactory(Coupling,Coupling_form,name="Coupling_formset")

Conformance_form = MetadataFormFactory(Conformance,name="Conformance_form")
Conformance_formset = MetadataFormSetFactory(Conformance,Conformance_form,name="Conformance_formset")

Standard_form = MetadataFormFactory(Standard,name="Standard_form")
Standard_formset = MetadataFormSetFactory(Standard,Standard_form,name="Standard_formset")


StandardName_form = MetadataFormFactory(StandardName,name="StandardName_form",subForms={"standard":"Standard_formset"})
StandardName_formset = MetadataFormSetFactory(StandardName,StandardName_form,name="StandardName_formset")

DataCitation_form = MetadataFormFactory(DataCitation,name="DataCitation_form",subForms={"citation":"Citation_form"})
DataCitation_formset = MetadataFormSetFactory(DataCitation,DataCitation_form,name="DataCitation_formset")

DataExtent_form = MetadataFormFactory(DataExtent,name="DataExtent_form")
DataExtent_formset = MetadataFormSetFactory(DataExtent,DataExtent_form,name="DataExtent_formset")

DataTopic_form = MetadataFormFactory(DataTopic,name="DataTopic_form",subForms={"standardName":"StandardName_form"})
DataTopic_formset = MetadataFormSetFactory(DataTopic,DataTopic_form,name="DataTopic_formset")

DataContent_form = MetadataFormFactory(DataContent,name="DataContent_form",subForms={"topic":"DataTopic_form","citation":"DataCitation_formset"},reorder=("topic","frequency","aggregation","citation"))
DataContent_formset = MetadataFormSetFactory(DataContent,DataContent_form,name="DataContent_formset")

DataDistribution_form = MetadataFormFactory(DataDistribution,name="DataDistribution_form",subForms={"responsibleParties":"ResponsibleParty_formset"})
DataDistribution_formset = MetadataFormSetFactory(DataDistribution,DataDistribution_form,name="DataDistribution_formset")

License_form = MetadataFormFactory(License,name="License_form")
License_formset = MetadataFormSetFactory(License,License_form,name="License_formset")

DataRestriction_form = MetadataFormFactory(DataRestriction,name="DataRestriction_form",subForms={"license":"License_form"})
DataRestriction_formset = MetadataFormSetFactory(DataRestriction,DataRestriction_form,name="DataRestriction_formset")

#DataStorage_form = MetadataFormFactory(DataStorage,name="DataStorage_form")
#DataStorage_formset = MetadataFormSetFactory(DataStorage,DataStorage_form,name="DataStorage_formset")

FileStorage_form = MetadataFormFactory(FileStorage,name="FileStorage_form",reorder=("fileName","path","fileSystem","dataFormat","dataSize","dataLocation","modificationDate"))
FileStorage_formset = MetadataFormSetFactory(FileStorage,FileStorage_form,name="FileStorage_formset")

DBStorage_form = MetadataFormFactory(DBStorage,name="DBStorage_form",reorder=("dbName","dbAccessString","dbTable","owner","dataFormat","dataSize","dataLocation","modificationDate"))
DBStorage_formset = MetadataFormSetFactory(DBStorage,DBStorage_form,name="DBStorage_formset")

IPStorage_form = MetadataFormFactory(IPStorage,name="IPStorage_form",reorder=("fileName","path","host","protocol","dataFormat","dataSize","dataLocation","modificationDate"))
IPStorage_formset = MetadataFormSetFactory(IPStorage,IPStorage_form,name="IPStorage_formset")

DataObject_form = MetadataFormFactory(DataObject,name="DataObject_form",subForms={"content":"DataContent_formset","extent":"DataExtent_form","citation":"DataCitation_form","distribution":"DataDistribution_form","restriction":"DataRestriction_formset","fileStorage":"FileStorage_form","dBStorage":"DBStorage_form","iPStorage":"IPStorage_form"})
DataObject_formset = MetadataFormSetFactory(DataObject,DataObject_form,name="DataObject_formset")

Simulation_form = MetadataFormFactory(Simulation,name="Simulation_form",subForms={"calendar":"Calendar_form", "inputs" : "Coupling_formset", "outputs":"DataObject_formset", "restarts":"DataObject_formset","conformances":"Conformance_formset"})
Simulation_formset = MetadataFormSetFactory(Simulation,Simulation_form,name="Simulation_formset")

SimulationRun_form = MetadataFormFactory(SimulationRun,name="SimulationRun_form")
SimulationRun_formset = MetadataFormSetFactory(SimulationRun,SimulationRun_form,name="SimulationRun_formset")

Experiment_form = MetadataFormFactory(Experiment,name="Experiment_form")
Experiment_formset = MetadataFormSetFactory(Experiment,Experiment_form,name="Experiment_formset")


NumericalRequirement_form = MetadataFormFactory(NumericalRequirement,name="NumericalRequirement_form",reorder=("type","requirementId","name","description","sources"))
NumericalRequirement_formset = MetadataFormSetFactory(NumericalRequirement,NumericalRequirement_form,name="NumericalRequirement_formset")


RequirementOption_form = MetadataFormFactory(RequirementOption,name="RequirementOption_form",subForms={"requirement":"NumericalRequirement_form"})
RequirementOption_formset = MetadataFormSetFactory(RequirementOption,RequirementOption_form,name="RequirementOption_formset")

CompositeNumericalRequirement_form = MetadataFormFactory(CompositeNumericalRequirement,name="CompositeNumericalRequirement_form",subForms={"requirementOptions":"RequirementOption_formset"},reorder=("type","requirementId","name","description","isComposite","requirementOptions","sources"))
CompositeNumericalRequirement_formset = MetadataFormSetFactory(CompositeNumericalRequirement,CompositeNumericalRequirement_form,name="CompositeNumericalRequirement_formset")

NumericalExperiment_form = MetadataFormFactory(NumericalExperiment,name="NumericalExperiment_form",subForms={"calendar":"Calendar_form","numericalRequirements":"CompositeNumericalRequirement_formset","responsibleParties":"ResponsibleParty_formset"})
NumericalExperiment_formset = MetadataFormSetFactory(NumericalExperiment,NumericalExperiment_form,name="NumericalExperiment_formset")

GridSpec_form = MetadataFormFactory(GridSpec,name="GridSpec_form")
GridSpec_formset = MetadataFormSetFactory(GridSpec,GridSpec_form,name="GridSpec_formset")
