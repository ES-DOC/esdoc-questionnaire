from django.forms import *
from django.forms.models import BaseForm, BaseFormSet, BaseInlineFormSet, BaseModelFormSet, formset_factory, inlineformset_factory, modelform_factory, modelformset_factory
from django.utils.datastructures import SortedDict
from django.utils.functional import curry

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
        fields = ("description","order")    # I am purposefully not displaying the "name" field
                                            # it causes ridiculous problems
                                            # if you want to change a category name
                                            # just delete it and re-create it
        
    def __init__(self,*args,**kwargs):
        super(FieldCategoryForm,self).__init__(*args,**kwargs)        
        self.fields["description"].widget.attrs["rows"] = 2
        self.fields["order"].widget.attrs["size"] = 2
        self.fields["order"].widget.attrs["readonly"] = True
        updateFieldAttributes(self.fields["order"],{"class":"readonly"})


class ModelCustomizerForm(ModelForm):
    class Meta:
        model = ModelCustomizer
        fields = ("tags","fields")

    _subForms = {}

    tags = forms.CharField()
    tags.label = "Available Field Categories"
    tags.help_text =    "Categories can be added by simply typing them into the widget.\
                        Categories can be deleted by clicking the close icon.\
                        Categories can be edited by clicking the pencil icon.\
                        Click the light bulb icon to toggle displaying fields belonging to a specific category.\
                        Fields can be re-ordered by dragging and droping."

    def __init__(self,*args,**kwargs):
        request = kwargs.pop('request', None)
        super(ModelCustomizerForm,self).__init__(*args,**kwargs)
        modelInstance = self.instance
        modelName = modelInstance.getName()
        appName = modelInstance.getApp()

        qs = FieldCustomizer.objects.filter(_model=modelName,_app=appName)

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

        currentCategoryList = [category.name for category in FieldCategory.objects.filter(_model=modelName,_app=appName)]
        self.fields["tags"].initial="|".join(currentCategoryList)
        self.fields["tags"].widget.attrs["id"] = "field-types"

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

        #print "START"
        #print cleaned_data["tags"]
        #print "END"

        # I ONLY REALLY HAVE TO CHECK THE "fields" FIELD; BUT THIS IS GOOD CODING PRACTISE
        for key,value in self.getAllSubForms().iteritems():
            subFormType = value[0]
            subFormClass = value[1]
            subFormInstance = value[2]

            # SIMILARLY, I ONLY HAVE TO CHECK THE "formset" TYPE
            if subFormType == SubFormTypes.FORMSET:
                cleaned_data[key] = [subForm.save() for subForm in subFormInstance]

###                # TODO: SHOULDN'T is_valid() HAVE ALREADY BEEN CALLED BY THIS POINT!?!
###                if subFormInstance.is_valid():
                
                activeSubForms = [subForm.save() for subForm in subFormInstance if subForm.cleaned_data] ## and subForm not in subFormInstance.deleted_forms]
                cleaned_data[key] = activeSubForms

        return cleaned_data


    def is_valid(self):
        # explicitly check the validity of all subforms
        validity = [subForm[2].is_valid() for subForm in self.getAllSubForms().itervalues() if subForm[2]]
        validity = all(validity) and super(ModelCustomizerForm,self).is_valid()
        return validity

class FieldCustomizerForm(ModelForm):
    class Meta:
        model = FieldCustomizer
        fields = ("order","category", "displayed", "editable", "required", "unique", "verbose_name", "documentation", "replace",)

    def __init__(self,*args,**kwargs):
        super(FieldCustomizerForm,self).__init__(*args,**kwargs)        
        #self.fields["order"].widget = HiddenInput()    # can't actually disable this field b/c I need to set it's value after any sort events,
                                                        # so instead I wrap it in a hidden div in the template.

        # when value of this is false, then required must also be false
        #
        
        updateFieldAttributes(self.fields["displayed"],{"class":"linked","onchange":"link(this,'false',{'required' : 'false'});"})
        updateFieldAttributes(self.fields["category"],{"class":"set-label","onchange":"setLabel(this);"})
        
#        for (key,value) in newAttrs.iteritems():
#            try:
#                currentAttrs = self.fields["category"].widget.attrs[key]
#                self.fields["category"].widget.attrs[key] = "%s %s" % (currentAttrs,value)
#            except KeyError:
#                self.fields["category"].widget.attrs[key] = value






    def getFieldInstance(self):
        return self.instance

    def getModelInstance(self):
        # even though I know that the underlying "model" of this form is a field,
        # this fn gets called by a templatetag that doesn't know what type of form it's dealing with;
        # hence, this redirect
        return self.getFieldInstance()

    
FieldCustomizerFormSet = modelformset_factory(FieldCustomizer,FieldCustomizerForm,extra=0)
