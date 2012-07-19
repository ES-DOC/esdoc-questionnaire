from django.forms import *
from django.forms.models import BaseForm, BaseFormSet, BaseInlineFormSet, BaseModelFormSet, formset_factory, inlineformset_factory, modelform_factory, modelformset_factory
from django.utils.datastructures import SortedDict
from django.utils.functional import curry

import inspect
import sys

from django_cim_forms.models import *

##############################################
# the types of subforms that a form can have #
##############################################

class SubFormType(EnumeratedType):
    pass

SubFormTypes = EnumeratedTypeList([
    SubFormType("FORM","Form",BaseForm),
    SubFormType("FORMSET","FormSet",BaseFormSet),
])

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
    form_name = ModelClass.getName() + "_form"
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

########################################
# the base class for all MetadataForms #
########################################

class MetadataForm(ModelForm):

    _subFormType = SubFormTypes.FORM

    _initialize = False # flag indicating whether or not the underlying model should use initial values
    _request = None     # store the HTTP request so that it can be passed onto subForms
    _subForms = {}      # a dictionary associating fields with subForms (the field should be replaced with a subform during rendering)

    def getModelClass(self):
        return self.Meta.model

    def getModelInstance(self):
        return self.instance          
        #return self.save(commit=False)  # whoops; this causes is_valid to be called prematurely

    def getModelName(self):
        return u'%s' % self.getModelInstance()
    
    def getModelId(self):
        modelInstance = self.getModelInstance()
        return modelInstance.getGuid()

    def getSubFormType(self):
        return self._subFormType

    def getAllSubForms(self):
        # returns the union of all subforms for all ancestor classes
        allSubForms = {}
        modelClass = self.getModelClass()
        for ancestor in reversed(inspect.getmro(modelClass)):
            if issubclass(ancestor,MetadataModel):
                ancestorForm = getFormClassFromModelClass(ancestor)
                if ancestorForm:
                    allSubForms = dict(allSubForms.items() + ancestorForm._subForms.items())
        return allSubForms

    
    def isPropertyForm(self):
        # MetadataProperties are treated a bit differently, b/c they can have nested tabs
        ModelClass = self.getModelClass()
        return issubclass(ModelClass,MetadataProperty)
        
    def __init__(self,*args,**kwargs):
        initialize = kwargs.pop("initialize",False)
        request = kwargs.pop('request', None)
        super(MetadataForm,self).__init__(*args,**kwargs)
        
        
        
        #modelInstance = self.getModelInstance()
        modelInstance = self.instance
        self._initialize = initialize
        self._request = request

        # order / exclude the fields according to the order of the corresponding model        
        fieldOrder = modelInstance._fieldOrder
        if fieldOrder:
            tmpFields = self.fields.copy()
            self.fields = SortedDict()
            for fieldName in fieldOrder:
                try:
                    self.fields[fieldName] = tmpFields[fieldName]
                except KeyError:
                    msg = "invalid field ('%s') specified in fieldOrder" % fieldName
                    raise MetadataError(msg)

        if initialize:
            self.initialize()

        # have to setup the subForms here
        # (by the time this fn is called, I can be certain POTENTIAL_SUBFORMS is complete)
        for (key,value) in self._subForms.iteritems():
            # if the subForm hasn't yet been set, then set it
            if isinstance(value,basestring):
                self._subForms[key] = POTENTIAL_SUBFORMS[value]

        for (key,value) in self._subForms.iteritems():

            subFormType = value[0]
            subFormClass = value[1]
            #value[2] = subFormInstance

            if subFormType == SubFormTypes.FORM:

                subModelInstance = getattr(modelInstance,key,None)
                if self._request and self._request.method == "POST":
                    value[2] = subFormClass(self._request.POST,instance=subModelInstance,request=self._request,prefix=key)
                else:
                    value[2] = subFormClass(instance=subModelInstance,request=self._request,initialize=self._initialize,prefix=key)

            elif subFormType == SubFormTypes.FORMSET:

                try:
                    qs = getattr(modelInstance,key,None).all()
                except (ValueError,AttributeError):
                    # note that the form is a curried function
                    # so I have to _call_ it in order to access the subForm class
                    qs = subFormClass.form().getModelClass().objects.none()

                if self._request and self._request.method == "POST":
                    value[2] = subFormClass(self._request.POST,request=self._request,prefix=key)
                else:
                    if self._initialize:
                        # b/c formsets are used w/ relationship fields
                        # and relationship fields can't be set until both models have a pk
                        # I have to copy the initial values for this field here in the form constructor
                        try:
                            qs = modelInstance.getInitialValues()[key]
                        except KeyError:
                            # if we get here, it means this formset must not have had initialValues specified
                            pass
                    value[2] = subFormClass(queryset=qs,request=self._request,initialize=self._initialize,prefix=key)
            else:
                msg = "unknown or invalid subFormType"
                raise MetadataError(msg)


    def initialize(self):
        # every model can have a set of initial values
        # if this is is a new model then those initial values should be set
        modelInstance = self.getModelInstance()
        initial_values = modelInstance.getInitialValues()
        for (key,value) in initial_values.iteritems():
            self.initial[key] = value
       
    def clean(self):
        modelInstance = self.getModelInstance()
        modelClass = self.getModelClass()

        # have to check "_unique" fields explicitly
        # b/c that customization ocurrs after the db is setup;
        # therefore, I can't rely on the validation happening automatically by Django
        cleaned_data = self.cleaned_data
        for cleaned_field_name in cleaned_data:
            model_field = modelInstance.getField(cleaned_field_name)
            if isinstance(model_field,MetadataField) and model_field.isUnique():
                filter_args = { 
                    cleaned_field_name : cleaned_data[cleaned_field_name]
                }
                # returns a list of all models whose field values match the field values in this model for fields marked as "_unique"
                # (the exclude function prevents this model from matching)
                # if this list is not empty, add an error to the list of errors for that field
                if modelClass.objects.filter(**filter_args).exclude(_guid=modelInstance._guid):
                    msg = "this value must be unique"
                    self._errors[cleaned_field_name] = self.error_class([msg])

        for key,value in self.getAllSubForms().iteritems():
            subFormType = value[0]
            subFormClass = value[1]
            subFormInstance = value[2]

            if subFormType == SubFormTypes.FORM:
                # TODO: SHOULDN'T is_valid() HAVE ALREADY BEEN CALLED BY THIS POINT!?!
                if subFormInstance.is_valid():
                    ModelClass = subFormInstance.getModelClass()
                    modelInstance = subFormInstance.getModelInstance()
                    try:
                        # if I'm replacing an existing modelInstance...
                        model = ModelClass.objects.get(guid=modelInstance.guid)
                        # just delete it
                        model.delete()
                    except ModelClass.DoesNotExist:
                        pass
                    cleaned_data[key] = subFormInstance.save()

            elif subFormType == SubFormTypes.FORMSET:
                # TODO: SHOULDN'T is_valid() HAVE ALREADY BEEN CALLED BY THIS POINT!?!
                if subFormInstance.is_valid():

                    # set the field to the set of subForms that are not marked for deletion and are not empty
                    # (is_valid() will have been called by this point so empty forms that _shouldn't_ be empty won't exist)
                    activeSubForms = [subForm.save() for subForm in subFormInstance if subForm.cleaned_data and subForm not in subFormInstance.deleted_forms]
                    cleaned_data[key] = activeSubForms

        return cleaned_data

    def is_valid(self):
        
        validity = [subForm[2].is_valid() for subForm in self.getAllSubForms().itervalues() if subForm[2]]
        validity = all(validity) and super(MetadataForm,self).is_valid()
        return validity

#########################################
# MetadataProperties are a special case #
#########################################

class Property_form(MetadataForm):

    class Meta:
        model = MetadataProperty
        fields = ("shortName","longName","value")        

    name = ""
    
    _fieldTypes = {}            # a dictionary associating fieldTypes with lists of fields
    _fieldTypeOrder = None      # a list describing the order of fieldTypes (tabs); if a type is absent from this list it is not rendered
    
#    def registerFieldType(self,fieldType,fieldNames):
#        for ft in self._fieldTypes:
#            if fieldType == ft: # fieldType equality is based on .getType()
#                                # therefore, even if a new FieldType instance is being registered
#                                # a new key will only be added if it has a new type
#                currentTypes = self._fieldTypes[ft]
#                #self._fieldTypes[ft] += fieldNames
#                self._fieldTypes[ft] = list(set(currentTypes)|set(fieldNames)) # union of the new set of fields and the existing set
#                return
#        self._fieldTypes[fieldType] = fieldNames


    def clean(self):
        modelInstance = self.instance
        cleaned_data = self.cleaned_data
        cleaned_data["shortName"] = modelInstance.shortName
        cleaned_data["longName"] = modelInstance.longName
        return cleaned_data
    
    def __init__(self,*args,**kwargs):
        super(Property_form,self).__init__(*args,**kwargs)
        modelInstance = self.instance

        # don't want to exclude these fields (b/c they're used by javascript to locate things)
        # so I'm just making them hidden
        self.fields["shortName"].widget = django.forms.fields.TextInput(attrs={"readonly":"readonly","class":"hidden"})
        self.fields["longName"].widget = django.forms.fields.TextInput(attrs={"readonly":"readonly","class":"hidden"})

        if modelInstance.hasValues():
            custom_choices = modelInstance.getValueChoices()
            if modelInstance.open and OTHER_CHOICE[0] not in custom_choices:
                custom_choices += OTHER_CHOICE
            if modelInstance.nullable and NONE_CHOICE[0] not in custom_choices:
                custom_choices += NONE_CHOICE

            if EMPTY_CHOICE[0] not in custom_choices:
                custom_choices.insert(0,EMPTY_CHOICE[0])
            
            self.fields["value"] = MetadataBoundFormField(choices=custom_choices,multi=modelInstance.multi,empty=True,blank=True)
            self.fields["value"].widget.attrs.update({"onchange":"setPropertyTitle(this)"})

        if modelInstance.isCustom():
            self.fields["value"] = MetadataBoundFormField(choices=OTHER_CHOICE,multi=False,empty=True,blank=True,custom=True)
            self.fields["value"].widget.attrs.update({"onchange":"setPropertyTitle(this)"})
                
        self.name = self.instance.shortName

#        if modelInstance.hasValues():
#            self.fields["value"].widget = django.forms.fields.Select(choices=modelInstance.getValueChoices())
#
#        if modelInstance.hasParent():
#            self.registerFieldType(FieldType(modelInstance.parentShortName,modelInstance.parentLongName),[])
            
    def is_valid(self):
        validity = False
        modelInstance = self.instance
        if modelInstance.hasValues():
            validity = super(Property_form,self).is_valid()    
        else:
            # if a property has no values (ie: if it is just a parent/category)
            # then there is nothing to check for its validity
            self.errors = None
            validity = True

        return validity

        
###########################################
# the base class for all MetadataFormSets #
###########################################

class MetadataFormSet(BaseModelFormSet):

    _subFormType = SubFormTypes.FORMSET

    _initialize = False # flag indicating whether or not the underlying models should use initial values
    _request = None     # store the HTTP request so that it can be passed onto child forms
    _prefix = None      # a prefix to distinguish this formset from others on the same page

    def getSubFormType(self):
        return self._subFormType

    def getPrefix(self):
        return self._prefix
    
    def __init__(self,*args,**kwargs):
        # this adds an extra kwarg, 'request,' to the subforms of this formset
        self._request = kwargs.pop('request', None)
        self._initalize = kwargs.pop("initialize",False)
        self.form = curry(self.form,request=self._request,initialize=self._initalize)

        super(MetadataFormSet,self).__init__(*args,**kwargs)

        # TODO: do I need to ensure a more unique prefix?
        self._prefix = kwargs.get("prefix",self.get_default_prefix())

        if self._initalize:
            self.initialize()

    def is_valid(self,*args,**kwargs):

        validity = super(MetadataFormSet,self).is_valid(*args,**kwargs)
        if validity == False:
            print "ERROR IN %s: %s" % (self._name,self.errors)
        return validity

    @classmethod
    def isPropertyForm(self):
        # MetadataProperties are treated a bit differently, b/c they can have nested tabs
        # (other forms can have sub-tabs, but properties can potentially have infinitely nested tabs)
        FormClass = self.form()
        return FormClass.isPropertyForm()


    def nestPropertyForms(self,nestedProperties,parent,properties):
        # call this recursively;
        # start w/ nestedProperties={}, parent=None, properties=[form.getModelInstance() for form in formset.forms]

        parentShortName = ""
        if parent:
            parentShortName = parent.shortName
        children = [p for p in properties if (p.parentShortName==parentShortName)]

        for child in children:
#           nestedProperties[child] = {}
# the filter will convert models to strings, so if I use guids I can figure out which form they mean
            nestedProperties[child.shortName] = {}
            self.nestPropertyForms(nestedProperties[child.shortName],child,properties)
        return nestedProperties
        
    def initialize(self):
        for i in range(0,self.total_form_count()):
            form = self.forms[i]
            form.initialize()
        


####################################
# how to create forms and formsets #
####################################

POTENTIAL_SUBFORMS = {}

# decorator which adds generated forms & formsets to the above dictionary
def PotentialSubForm(subFormType=SubFormType("UNKNOWN","Unknown")):
    def decorator(factoryFunction):
        @wraps(factoryFunction)
        def wrapper(*args,**kwargs):
            _form = factoryFunction(*args,**kwargs)
            try:
                name  = kwargs["name"]
                POTENTIAL_SUBFORMS[name] = [subFormType, _form, None]
            except KeyError:
                msg = "'name' kwarg is required for %s" % _form
                raise MetadataError(msg)
            _form._subFormType = subFormType
            return _form
        return wrapper
    return decorator


@PotentialSubForm(SubFormTypes.FORM)
def MetadataFormFactory(ModelClass,*args,**kwargs):

    subForms = kwargs.pop("subForms",{})
    name = kwargs.pop("name",None)

    kwargs["form"] = kwargs.pop("form",MetadataForm)
    kwargs["formfield_callback"] = customize_metadata_widgets

    _form = modelform_factory(ModelClass,**kwargs)
    _form._name = name

    # reset any existing subForms.
    _form._subForms = {}
    for (key,value) in subForms.iteritems():
        try:
            # then try to assign the subform to the list of information in POTENTIAL_SUBFORMS
            _form._subForms[key] = POTENTIAL_SUBFORMS[value]
        except KeyError:
            # this might fail if that information isn't in POTENTIAL_SUBFORMS yet
            # that's okay, I'll try again in the __init__ function
            _form._subForms[key] = value
        # Python doesn't have forward declarataions!
    return _form



@PotentialSubForm(SubFormTypes.FORMSET)
def MetadataFormSetFactory(ModelClass,FormClass,*args,**kwargs):

    name = kwargs.pop("name",None)

    kwargs["formset"] = kwargs.pop("formset",MetadataFormSet)
    kwargs["can_delete"] = True

    _formset = modelformset_factory(ModelClass,**kwargs)
    _formset._name = name

    # TODO: DOUBLE-CHECK THIS CALL TO staticmethod(curry(...))
    # this ensures that the request and other kwargs passed to formsets gets propagated to all the child forms
    _formset.form = staticmethod(curry(FormClass,request=MetadataFormSet._request))#,initialize=MetadataFormSet._initialize))

    return _formset
