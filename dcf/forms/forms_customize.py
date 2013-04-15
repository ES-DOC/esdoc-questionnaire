
####################
#   Django-CIM-Forms
#   Copyright (c) 2012 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Feb 1, 2013 4:42:47 PM"

"""
.. module:: forms_customize

Summary of module goes here

"""
from django.forms import *
from django.forms.models import BaseForm, BaseFormSet, BaseInlineFormSet, BaseModelFormSet, formset_factory, inlineformset_factory, modelform_factory, modelformset_factory

from dcf.models import *
from dcf.utils import *


class MetadataModelCustomizerForm(ModelForm):
    class Meta:
        model   = MetadataModelCustomizer
        fields  = ("name","description","default","version","categorization","vocabularies","model_title","model_description","model_show_all_categories","model_show_all_attributes","properties")#,"model_vocabulary","standard_categories","special_categories","fields","properties")

    _subForms = {}

    customizer_fields   = ("name","description","default","version","categorization","vocabularies")
    model_fields        = ("model_title","model_description","model_show_all_categories","model_show_all_attributes")

###    attribute_fields    = ("attributes")
    property_fields     = ("properties")

    version         = CharField(label="Metadata Version",required=False)
    # TODO: IS THERE A BETTER WAY THAT I CAN SPECIFY THE QS? THIS SEEMS INNEFICIENT    
    vocabularies    = ModelMultipleChoiceField(label="Controlled Vocabularies",required=False,queryset=MetadataVocabulary.objects.none())   # qs set to none() b/c actual value is set in init below
    categorization  = ModelChoiceField(label="Categorization",required=False,queryset=MetadataCategorization.objects.none())                # qs set to none() b/c actual value is set in init below

    attribute_categories = ModelMultipleChoiceField(queryset=MetadataAttributeCategory.objects.none(),required=False)
    attribute_categories_tags = CharField(label="Available Categories",required=False)
    attribute_categories_tags.help_text = "This widget contains the standard set of attribute categories associated with the metdata version.  If this set is unsuitable, or empty, then the categorization should be updated.  Please contact your administrator."

    property_categories = ModelMultipleChoiceField(queryset=MetadataPropertyCategory.objects.none(),required=False)
    property_categories_tags = CharField(label="Available Categories",required=False)
    property_categories_tags.help_text  = "This widget is used to customize the categories used to display scientific properties."
    
    def __init__(self,*args,**kwargs):
        request = kwargs.pop('request', None)
        super(MetadataModelCustomizerForm,self).__init__(*args,**kwargs)
        customizer_instance = self.instance

###        attribute_qs = MetadataAttributeCustomizer.objects.filter(project=customizer_instance.project,version=customizer_instance.version,model=customizer_instance.model,parentGUID=customizer_instance.getGUID())

        if customizer_instance.pk:
            qs = MetadataAttributeCustomizer.objects.filter(parent=customizer_instance)
            initial = None
            FormSet = MetadataAttributeCustomizerInlineFormSetFactory(extra=0)
        else:
            qs = MetadataAttributeCustomizer.objects.none()
            initial = [model_to_dict(temporary_attribute_customizer) for temporary_attribute_customizer in customizer_instance.temporary_attributes]
            FormSet = MetadataAttributeCustomizerInlineFormSetFactory(extra=len(initial))

        self._subForms["attributes"] = [
            SubFormTypes.FORMSET,
            FormSet,
            FormSet(request.POST,instance=customizer_instance) if (request.method == "POST") else FormSet(initial=initial,instance=customizer_instance)
        ]

        try:
            current_attribute_categories = customizer_instance.getCategorization().getAttributeCategories()
            self.fields["attribute_categories"].queryset = MetadataAttributeCategory.objects.filter(id__in=[category.id for category in current_attribute_categories])
            self.fields["attribute_categories_tags"].initial="|".join([category.name for category in current_attribute_categories])
        except AttributeError:
            # if there was no categorization assigned,
            # then attributes will not be associated w/ any categories
            # that's unfortunate, but it's not an error
            pass

        property_qs = MetadataPropertyCustomizer.objects.filter(project=customizer_instance.project,version=customizer_instance.version,model=customizer_instance.model,parentGUID=customizer_instance.getGUID())

        self._subForms["properties"] = [
            SubFormTypes.FORMSET,
            MetadataPropertyCustomizerFormSet,
            MetadataPropertyCustomizerFormSet(request.POST) if (request.method=="POST") else MetadataPropertyCustomizerFormSet(queryset=property_qs)
        ]

        # get all categories with a mapping to this model
        model_key = u'"%s":' % customizer_instance.model
        current_property_categories = MetadataPropertyCategory.objects.filter(mapping__contains=model_key)

        self.fields["property_categories"].queryset = current_property_categories
        self.fields["property_categories_tags"].initial="|".join([category.name for category in current_property_categories])

        # add specific attributes to the remaining fields...
        self.fields["description"].widget.attrs["rows"] = 2
        self.fields["model_description"].widget.attrs["rows"] = 4

        self.fields["categorization"].queryset  = customizer_instance.getCategorizations()
        self.fields["vocabularies"].queryset    = customizer_instance.getVocabularies()

        update_field_widget_attributes(self.fields["attribute_categories_tags"],{"class":"tags"})
        update_field_widget_attributes(self.fields["property_categories_tags"],{"class":"tags"})

        self.fields["version"].initial          = customizer_instance.version
        self.fields["categorization"].initial   = customizer_instance.getCategorization()
        self.fields["vocabularies"].initial     = [customizer_instance.getVocabulary()]

        self.fields["version"].widget.attrs["readonly"] = True
        self.fields["categorization"].widget.attrs["disabled"] = True
        self.fields["vocabularies"].widget.attrs["disabled"] = True
        update_field_widget_attributes(self.fields["version"],{"class":"readonly"})
        update_field_widget_attributes(self.fields["categorization"],{"class":"readonly"})
        update_field_widget_attributes(self.fields["vocabularies"],{"class":"readonly"})

        update_field_widget_attributes(self.fields["attribute_categories"],{"class":"hidden"})
        update_field_widget_attributes(self.fields["property_categories"],{"class":"hidden"})

    def getCustomizerFields(self):
        fields = list(self)
        return [field for field in fields if field.name in self.customizer_fields]

    def getModelFields(self):
        fields = list(self)
        return [field for field in fields if field.name in self.model_fields]

    def getAllSubForms(self):
        # this fn does fancy stuff when called w/ a MetadataModel (it searches the full hierarchy of forms)
        # for a customizer, just return the list
        return self._subForms 
    
    def is_valid(self):
        print "CALLING IS_VALID FOR MODELCUSTOMIZER"
        subFormValidity = [subForm[2].is_valid() for subForm in self.getAllSubForms().itervalues() if subForm[2]]
        formValidity = all(subFormValidity) and super(MetadataModelCustomizerForm,self).is_valid()
        return formValidity

    def clean(self):

#        print "ABOUT TO CLEAN THIS CUSTOMIZER"
#        print "IT'S ID IS: %s" % self.instance.getGUID()

        customizer_instance = self.instance
        cleaned_data = self.cleaned_data

        print "CLEANING FORM: %s" % customizer_instance.getGUID()


        for attributeSubForm in self._subForms["attributes"][2]:
            if attributeSubForm.is_valid():
                attribute_instance = attributeSubForm.save(commit=False)
                attribute_instance.setParent(customizer_instance)
                attribute_instance.save()

###
###        # I ONLY REALLY HAVE TO CHECK THE "properties" & "attributes" FIELDS; BUT THIS IS GOOD CODING PRACTISE
###        for key,value in self.getAllSubForms().iteritems():
###            subFormType = value[0]
###            subFormClass = value[1]
###            subFormInstance = value[2]
###
###            print "checking %s" % key
###
### #           print "going to clean '%s'" % key
### #           print "it is a '%s'" % subFormClass
### #           print "and it thinks its parent id is: %s" % (subFormInstance[0].instance.parentGUID)
###
###            # SIMILARLY, I ONLY HAVE TO CHECK THE "formset" TYPE
###            if subFormType == SubFormTypes.FORMSET:
###
###
###                for subForm in subFormInstance:
###
###                                customizer_instance = form.save(commit=False)
###
###                    subForm.setParent(customizer_instance)
###                    subForm.save()
###
###                # TODO: SHOULDN'T is_valid() HAVE ALREADY BEEN CALLED BY THIS POINT!?!
###
####                if subFormInstance.is_valid():
### #
###  #                  activeSubForms = []
###   #                 for subForm in subFormInstance:
###    #                    subForm.parent = self
###     #                   activeSubForms.append(subForm.save())
###      #              #activeSubForms = [subForm.save() for subForm in subFormInstance]# if subForm.cleaned_data] ## and subForm not in subFormInstance.deleted_forms]
###       #             cleaned_data[key] = activeSubForms
###
        return cleaned_data

class MetadataAttributeCustomizerForm(ModelForm):
    class Meta:
        model = MetadataAttributeCustomizer
        fields = ("attribute_name", "attribute_type", "order", "category", "displayed", "verbose_name", "default_value", "documentation", "required", "editable", "unique", "cardinality", "customize_subform", "subform_customizer")
        
    def __init__(self,*args,**kwargs):
        super(MetadataAttributeCustomizerForm,self).__init__(*args,**kwargs)

        attribute = self.instance

        # don't want to show these fields, but still need access to them
        self.fields["attribute_name"].widget = HiddenInput()
        self.fields["attribute_type"].widget = HiddenInput()
        self.fields['order'].widget = HiddenInput()     # don't want to show this field, but still need acccess to it from js

        self.fields['documentation'].widget.attrs["rows"] = 3
        update_field_widget_attributes(self.fields["displayed"],{"class":"linked","onchange":"link(this,'false',{'required' : 'false'});"})
        update_field_widget_attributes(self.fields["required"],{"class":"linked","onchange":"link(this,'true',{'cardinality' : ['1','None']});link(this,'false',{'cardinality' : ['0','None']});"})
        update_field_widget_attributes(self.fields["order"],{"class":"set-label","onchange":"set_label(this,'field-order');"})
        #update_field_widget_attributes(self.fields["category"],{"class":"set-label","onchange":"set_label(this,'field-category');"})
        update_field_widget_attributes(self.fields["customize_subform"],{"onchange":"enable(this,'true',['customize-subform']);"})

        try:
            # a little bit of jiggery-pokery to handle the case where it's a new attributecustomizer
            # (won't have a name yet; also won't have any initial data - that only gets set via POST)
            attribute_type = attribute.attribute_type or self.initial["attribute_type"]
        except KeyError:
            attribute_type = None
            
        if (attribute_type == "booleanfield"):
            # default_value should be a T/F combobox for boolean fields
            self.fields["default_value"].widget = Select(choices=((True,"True"),(False,"False")))

        if not (attribute_type in [field._type.lower() for field in MetadataRelationshipField.__subclasses__()]):
            # only bother showing the "replace" and "cardinality" widget if this is a relationship field
            del self.fields["customize_subform"]
            del self.fields["cardinality"]

        # no longer displaying category; all customization of categories for attributes must come from categorization file
        #category = attribute.category
        #if category and category.getType()==CategoryTypes.ATTRIBUTE:
        #    # only bother showing the "category" widget if this is not a standard field
        #    del self.fields["category"]



    def getAttributeName(self):
        try:
            if self.is_bound:
                return self.instance.attribute_name
            else:
                return self.initial["attribute_name"]
        except AttributeError:
            return None

    def getAttributeOrder(self):
        try:
            if self.is_bound:
                return self.instance.order
            else:
                return self.initial["order"]
        except AttributeError:
            return None

    def getCategoryName(self):
        try:
            if self.is_bound:
                return self.instance.category.name
            else:
                category_pk = self.initial["category"]
                name = MetadataAttributeCategory.objects.get(pk=category_pk).name
                print "pk=%s" % category_pk
                print "name=%s" % name
                return name
        except AttributeError:
            return None

    def is_valid(self):
        print "IS VALID ATTRIBUTECUSTOMIZER"
        return super(MetadataAttributeCustomizerForm,self).is_valid()

def MetadataAttributeCustomizerInlineFormSetFactory(*args,**kwargs):
    new_kwargs = {
        "can_delete" : False,
        "form"       : MetadataAttributeCustomizerForm,
        "fk_name"    : "parent" # required b/c there are 2 foreignkeys to 'metadatamodelcustomizer'; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)
    _formset = inlineformset_factory(MetadataModelCustomizer,MetadataAttributeCustomizer,**new_kwargs)
    return _formset

class BaseMetadataAttributeCustomizerFormSet(BaseModelFormSet):
#    _subFormType    = SubFormTypes.FORMSET  # the type of subform
#    _request        = None                  # store the HTTP request so that it can be passed onto child forms
#    _prefix         = None                  # a prefix to distinguish this formset from others on the same page
    pass

    def clean(self):
        print "CLEANING SUBFORM"
        super(BaseMetadataAttributeCustomizerFormSet,self).clean()



MetadataAttributeCustomizerFormSet = modelformset_factory(MetadataAttributeCustomizer,MetadataAttributeCustomizerForm,extra=0)

def MetadataAttributeCustomizerFormSetFactory(*args,**kwargs):
    kwargs["formset"] = BaseMetadataAttributeCustomizerFormSet
    _formset = modelformset_factory(MetadataAttributeCustomizer,MetadataAttributeCustomizerForm,**kwargs)
    return _formset

class MetadataPropertyCustomizerForm(ModelForm):
    class Meta:
        model = MetadataPropertyCustomizer
        fields = ("order", "category", "displayed", "verbose_name", "default_value", "documentation", "required", "editable", "open", "multi", "nullable","values")

    values = MultipleChoiceField(label="which choices should be provided");

    def __init__(self,*args,**kwargs):
        super(MetadataPropertyCustomizerForm,self).__init__(*args,**kwargs)

        property = self.instance

        # by default a property exposes _all_ value choices
        choices = property.getValues()
        self.fields["values"].choices = choices
        self.fields["values"].initial = [choice[0] for choice in choices]

        self.fields['order'].widget = HiddenInput()     # don't want to show this field, but still need acccess to it from js
        self.fields['documentation'].widget.attrs["rows"] = 3
        update_field_widget_attributes(self.fields["displayed"],{"class":"linked","onchange":"link(this,'false',{'required' : 'false'});"})
        update_field_widget_attributes(self.fields["order"],{"class":"set-label","onchange":"set_label(this,'field-order');"})
        update_field_widget_attributes(self.fields["category"],{"class":"set-label","onchange":"set_label(this,'field-category');"})
        update_field_widget_attributes(self.fields["values"],{"class":"dropdownchecklist"})
                


    def getPropertyName(self):
        try:
            return self.instance.property.short_name
        except AttributeError:
            return None

    def getPropertyOrder(self):
        return self.instance.order

    def getCategoryName(self):
        try:
            return self.instance.category.name
        except AttributeError:
            return None

MetadataPropertyCustomizerFormSet = modelformset_factory(MetadataPropertyCustomizer,MetadataPropertyCustomizerForm,extra=0)
