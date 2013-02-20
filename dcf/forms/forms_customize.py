
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
        fields  = ("name","description","default","version","categorization","vocabularies","model_title","model_description","attributes","properties")#,"model_vocabulary","standard_categories","special_categories","fields","properties")

    _subForms = {}

    customizer_fields   = ("name","description","default","version","categorization","vocabularies")
    model_fields        = ("model_title","model_description")
    attribute_fields    = ("attributes")
    property_fields     = ("properties")

    version         = CharField(label="Metadata Version",required=False)
    # TODO: IS THERE A BETTER WAY THAT I CAN SPECIFY THE QS? THIS SEEMS INNEFICIENT    
    vocabularies    = ModelMultipleChoiceField(label="Controlled Vocabularies",required=False,queryset=MetadataVocabulary.objects.none())   # qs set to none() b/c actual value is set in init below
    categorization  = ModelChoiceField(label="Categorization",required=False,queryset=MetadataCategorization.objects.none())                # qs set to none() b/c actual value is set in init below

    attribute_categories = ModelMultipleChoiceField(queryset=MetadataAttributeCategory.objects.none())
    attribute_categories_tags = CharField(label="Available Categories",required=False)
    attribute_categories_tags.help_text = "This widget contains the standard set of attribute categories associated with the metdata version.  If this set is unsuitable, or empty, then the categorization should be updated.  Please contact your administrator."

    property_categories = ModelMultipleChoiceField(queryset=MetadataPropertyCategory.objects.none())
    property_categories_tags = CharField(label="Avaialble Categories",required=False)
    property_categories_tags.help_text  = "This widget is used to customize the categories used to display scientific properties."


    
    def __init__(self,*args,**kwargs):
        request = kwargs.pop('request', None)
        super(MetadataModelCustomizerForm,self).__init__(*args,**kwargs)
        customizer_instance = self.instance

        attribute_qs = MetadataAttributeCustomizer.objects.filter(project=customizer_instance.project,version=customizer_instance.version,model=customizer_instance.model,parentGUID=customizer_instance.getGUID())
        self._subForms["attributes"] = [
            SubFormTypes.FORMSET,
            MetadataAttributeCustomizerFormSet,
            MetadataAttributeCustomizerFormSet(request.POST) if (request.method=="POST") else MetadataAttributeCustomizerFormSet(queryset=attribute_qs)
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

class MetadataAttributeCustomizerForm(ModelForm):
    class Meta:
        model = MetadataAttributeCustomizer
        fields = ("order", "category", "displayed", "verbose_name", "default_value", "documentation", "required", "editable", "unique", "replace")

    def __init__(self,*args,**kwargs):
        super(MetadataAttributeCustomizerForm,self).__init__(*args,**kwargs)

        attribute = self.instance

        self.fields['order'].widget = HiddenInput()     # don't want to show this field, but still need acccess to it from js
        self.fields['documentation'].widget.attrs["rows"] = 3
        update_field_widget_attributes(self.fields["displayed"],{"class":"linked","onchange":"link(this,'false',{'required' : 'false'});"})
        update_field_widget_attributes(self.fields["order"],{"class":"set-label","onchange":"set_label(this,'field-order');"})
        update_field_widget_attributes(self.fields["category"],{"class":"set-label","onchange":"set_label(this,'field-category');"})
        update_field_widget_attributes(self.fields["replace"],{"onchange":"enable(this,'true',['customize-subform']);"})

        attribute_type = attribute.getType()
        if not (attribute_type in [field._type.lower() for field in MetadataRelationshipField.__subclasses__()]):
            # only bother showing the "replace" widget if this is a relationship field
            del self.fields["replace"]

        category = attribute.category
        if category and category.getType()==CategoryTypes.ATTRIBUTE:
            # only bother showing the "category" widget if this is not a standard field
            del self.fields["category"]

        if (attribute_type == "booleanfield"):
            # default_value should be a T/F combobox for boolean fields
            self.fields["default_value"].widget = Select(choices=((True,"True"),(False,"False")))


    def getAttributeName(self):
        try:
            return self.instance.attribute_name
        except AttributeError:
            return None

    def getAttributeOrder(self):
        return self.instance.order

    def getCategoryName(self):
        try:
            return self.instance.category.name
        except AttributeError:
            return None

MetadataAttributeCustomizerFormSet = modelformset_factory(MetadataAttributeCustomizer,MetadataAttributeCustomizerForm,extra=0)

class MetadataPropertyCustomizerForm(ModelForm):
    class Meta:
        model = MetadataPropertyCustomizer
        fields = ("order", "category", "displayed", "verbose_name", "default_value", "documentation", "required", "editable", "open", "multi", "nullable","values")

    values = MultipleChoiceField(choices=[["a","b"]],label="which choices should be provided");

    def __init__(self,*args,**kwargs):
        super(MetadataPropertyCustomizerForm,self).__init__(*args,**kwargs)

        property = self.instance

        self.fields["values"].choices = property.getValues()
        self.fields["values"].initial = property.getValues()
        
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
