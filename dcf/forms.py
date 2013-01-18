from django.forms import *
from django.forms.models import BaseForm, BaseFormSet, BaseInlineFormSet, BaseModelFormSet, formset_factory, inlineformset_factory, modelform_factory, modelformset_factory
from django.utils.datastructures import SortedDict
from django.utils.functional import curry

from django.core.exceptions import ObjectDoesNotExist

import inspect
import sys

from dcf.models import *

##############################################
# the types of subforms that a form can have #
##############################################

class SubFormType(EnumeratedType):
    pass

SubFormTypes = EnumeratedTypeList([
    SubFormType("FORM","Form",BaseForm),
    SubFormType("FORMSET","FormSet",BaseFormSet),
])

##########################################
# forms to be used for Customization GUI #
##########################################

class FieldCategoryForm(ModelForm):
    class Meta:
        model = FieldCategory
        exclude = ('name',) # I am purposefully not displaying the "name" field
                            # it causes ridiculous problems
                            # if you want to change a category name
                            # just delete it and re-create it
        
    def __init__(self,*args,**kwargs):
        super(FieldCategoryForm,self).__init__(*args,**kwargs)        
        self.fields["description"].widget.attrs["rows"] = 2
        self.fields["order"].widget.attrs["size"] = 2
        self.fields["order"].widget.attrs["readonly"] = True
        updateFieldWidgetAttributes(self.fields["order"],{"class":"readonly"})


class ModelCustomizerForm(ModelForm):
    class Meta:
        model = ModelCustomizer
        fields = ("name","description","default","tags","expandedTags","fields")

    _subForms = {}

    # tags is the form field used for the tagging widget
    tags = forms.CharField()
    tags.label = "Available Field Categories"
    tags.help_text =    "Categories can be added by simply typing them into the widget.\
                        Categories can be deleted by clicking the close icon.\
                        Categories can be edited by clicking the pencil icon.\
                        Click the light bulb icon to toggle displaying fields belonging to a specific category.\
                        Fields can be re-ordered by dragging and droping."
    # and expanded tags is used to store the corresponding JSON content created by that tagging widget
    expandedTags = forms.CharField()

    def __init__(self,*args,**kwargs):
        request = kwargs.pop('request', None)
        super(ModelCustomizerForm,self).__init__(*args,**kwargs)
        modelInstance = self.instance
        modelName = modelInstance.getModelName()
        appName = modelInstance.getAppName()
        customizerGUID = modelInstance.getGUID()

        qs = FieldCustomizer.objects.filter(modelName=modelName,appName=appName,_customizerGUID=customizerGUID)

        # subForm[0] is the type, [1] is the class, [2] is the (current) instance
        # (don't really need this level of detail for the customization form;
        # but it helps to re-use code in the templates)
        self._subForms["fields"] = [
            SubFormTypes.FORMSET,
            FieldCustomizerFormSet,
     
            # if the form is being instantiated b/c of a POST, then copy over the request
            # otherwise use the queryset specified above
            FieldCustomizerFormSet(request.POST) if (request.method=="POST") else FieldCustomizerFormSet(queryset=qs)

        ]

        self.fields["name"].widget.attrs["required"] = True
        self.fields["description"].widget.attrs["rows"] = 2
        self.fields["tags"].widget.attrs["id"] = "field-types"
        updateFieldWidgetAttributes(self.fields["expandedTags"],{"class":"hidden"})
        currentCategoryList = [category.name for category in FieldCategory.objects.filter(modelName=modelName,appName=appName)]
        self.fields["tags"].initial="|".join(currentCategoryList)
        

    def getModelInstance(self):
        return self.instance

    def getModelClass(self):
        return self.Meta.model

    def getAllSubForms(self):
        # no need to look at ancestors; there is no hierarchy in Customizer models like there is in the actual Metadata Models
        allSubForms = self._subForms
        return allSubForms


    def clean(self):
        # set the cleaned_data for any fields that have been replaced w/ a subform
        # (in the case of these CustomizationForms, I know that that is always only the "fields" field)
        # to the ids of the models underlying those subforms
        cleaned_data = self.cleaned_data
        instance = self.getModelInstance()

        # I ONLY REALLY HAVE TO CHECK THE "fields" FIELD; BUT THIS IS GOOD CODING PRACTISE
        for key,value in self.getAllSubForms().iteritems():
            subFormType = value[0]
            subFormClass = value[1]
            subFormInstance = value[2]

            # SIMILARLY, I ONLY HAVE TO CHECK THE "formset" TYPE
            if subFormType == SubFormTypes.FORMSET:

                # TODO: SHOULDN'T is_valid() HAVE ALREADY BEEN CALLED BY THIS POINT!?!
                if subFormInstance.is_valid():

                    cleaned_data[key] = [subForm.save() for subForm in subFormInstance]
                    activeSubForms = [subForm.save() for subForm in subFormInstance if subForm.cleaned_data] ## and subForm not in subFormInstance.deleted_forms]
                    cleaned_data[key] = activeSubForms


        # work out which fields are unique_together
        unique_filter = {}
        unique_fields = instance.getUniqueTogether()
        if unique_fields:
            for unique_field in unique_fields:
                field = instance.getField(unique_field)
                if field.editable: # get the value from the form
                    unique_filter[unique_field] = cleaned_data[unique_field]
                else: # get the value from the model
                    unique_filter[unique_field] = getattr(instance,unique_field)
            existing_instances = type(instance).objects.filter(**unique_filter).exclude(_guid=instance.getGUID())
            if existing_instances:
                # if we've gotten to this point, then there is a pre-existing model matching the unique filter
                # so record the relevant errors
                for unique_field in unique_fields:
                    self.errors[unique_field] = "This value must be unique."

        return cleaned_data


    def is_valid(self):
        # explicitly check the validity of all subforms
        validity = [subForm[2].is_valid() for subForm in self.getAllSubForms().itervalues() if subForm[2]]
        validity = all(validity) and super(ModelCustomizerForm,self).is_valid()
        return validity

class FieldCustomizerForm(ModelForm):
    class Meta:
        model = FieldCustomizer

    def __init__(self,*args,**kwargs):
        super(FieldCustomizerForm,self).__init__(*args,**kwargs)        
        #self.fields["order"].widget = HiddenInput()    # can't actually disable this field b/c I need to set it's value after any sort events,
                                                        # so instead I wrap it in a hidden div in the template

        updateFieldWidgetAttributes(self.fields["displayed"],{"class":"linked","onchange":"link(this,'false',{'required' : 'false'});"})
        updateFieldWidgetAttributes(self.fields["category"],{"class":"set-label","onchange":"setLabel(this);"})
        updateFieldWidgetAttributes(self.fields["replace"],{"onchange":"enable(this,['customize-subform']);"})
        
    def getFieldInstance(self):
        return self.instance

    def getModelInstance(self):
        # even though I know that the underlying "model" of this form is a field,
        # this fn gets called by a templatetag that doesn't know what type of form it's dealing with;
        # hence, this redirect
        return self.getFieldInstance()

    
FieldCustomizerFormSet = modelformset_factory(FieldCustomizer,FieldCustomizerForm,extra=0)

################################
# and now for the actual forms #
################################


###############################################################
# callback to customise _any_ widgets used by metadata fields #
# without having to hard-code _all_ of them                   #
###############################################################

def metadata_formfield_callback(field):
    formfield = field.formfield()

    return formfield

########################################
# the base class for all MetadataForms #
########################################

class MetadataForm(ModelForm):

    _subFormType    = SubFormTypes.FORM
    _request        = None      # store the HTTP request so that it can be passed onto subForms
    _prefix         = None      # a prefix to distinguish this formset from others on the same page
    customizer      = None

    _subForms       = {}        # a dictionary associating fields with subForms (the field should be replaced with a subform during rendering)

    def getModelInstance(self):
        return self.instance

    def getModelClass(self):
        return self.Meta.model

    def getSubFormType(self):
        return self._subFormType
    
    def __init__(self,*args,**kwargs):
        request = kwargs.pop('request', None)
        super(MetadataForm,self).__init__(*args,**kwargs)

        self.request = request
        modelInstance = self.instance
        
        for customField in self.customizer.fields.all():
            fieldName = customField.getName()
            modelField = modelInstance.getField(fieldName)
                        
            # first customize the model field...
            modelField.customize(customField)
            # and the formfield...
            self.initial[fieldName] = modelField.get_custom_default_value()

            # then register if it should be replaced by a subform
            if customField.replace:
                subModelClass = modelField.getTargetModelClass()
                subModelAppName = subModelClass.getAppName().lower()
                subModelName = subModelClass.getName().lower()

                customizer = getCustomizer(subModelAppName,subModelName)

                try:
                    qs = getattr(modelInstance,fieldName,None).all()
                except ValueError:
                    # a ValueError ocurrs when m2m fields are queried before modelInstance has been saved
                    qs = subModelClass.objects.none()

                if modelField.getType()=="manytomanyfield":
                    # formset
                    subFormType = SubFormTypes.FORMSET
                    subFormClass = MetadataFormSetFactory(subModelClass,customizer)
                    subFormInstance = subFormClass(request.POST,prefix=fieldName) if (request.method=="POST") else subFormClass(queryset=qs,prefix=fieldName)
                else:
                    # form
                    subFormType = SubFormTypes.FORM
                    subFormClass = MetadataFormFactory(subModelClass,customizer)
                    subFormInstance = subFormClass(request.POST) if (request.method=="POST") else subFormClass(queryset=qs)

                self._subForms[fieldName] = [ subFormType, subFormClass, subFormInstance ]

            

###########################################
# the base class for all MetadataFormSets #
###########################################

class MetadataFormSet(BaseModelFormSet):
    _subFormType    = SubFormTypes.FORMSET  # the type of subform
    _request        = None                  # store the HTTP request so that it can be passed onto child forms
    _prefix         = None                  # a prefix to distinguish this formset from others on the same page
    customizer      = None

    def getSubFormType(self):
        return self._subFormType

    def getPrefix(self):
        return self._prefix
    
    def __init__(self,*args,**kwargs):
        self.form = curry(self.form,request=self._request)
        super(MetadataFormSet,self).__init__(*args,**kwargs)
        self._prefix = kwargs.get("prefix")



###############################################
# Factory Methods to create forms dynamically #
###############################################

def MetadataFormFactory(ModelClass,customizer,*args,**kwargs):

    kwargs["form"] = kwargs.pop("form",MetadataForm)
    kwargs["formfield_callback"] = metadata_formfield_callback

    _form = modelform_factory(ModelClass,**kwargs)
    _form.customizer = customizer


    return _form

def MetadataFormSetFactory(ModelClass,customizer,*args,**kwargs):

    kwargs["formset"] = kwargs.pop("formset",MetadataFormSet)
    kwargs["formfield_callback"] = metadata_formfield_callback

    _formset = modelformset_factory(ModelClass,**kwargs)
    _formset.customizer = customizer

    # TODO: DOUBLE-CHECK THIS CALL TO staticmethod(curry(...))
    # this ensures that the request and other kwargs passed to formsets gets propagated to all the child forms
    FormClass = MetadataFormFactory(ModelClass,customizer)
    _formset.form = staticmethod(curry(FormClass,request=MetadataFormSet._request))


    return _formset
