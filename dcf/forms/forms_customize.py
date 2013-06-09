
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
#from django.forms.models import BaseForm
#from django.forms.models import BaseFormSet
#from django.forms.models import BaseInlineFormSet
#from django.forms.models import BaseModelFormSet
#from django.forms.models import formset_factory
from django.forms.models import inlineformset_factory
#from django.forms.models import modelform_factory
from django.forms.models import modelformset_factory
from django.utils.functional import curry

from dcf.models import *
from dcf.utils import *

class MetadataModelCustomizerForm(ModelForm):
    class Meta:
        model   = MetadataModelCustomizer
        fields  = ("name","description","default","version","categorization","vocabularies","model_title","model_description","model_show_all_categories","model_show_all_attributes","model_nested")

    _subForms = {}
    
    customizer_fields   = ("name","description","default","version","categorization","vocabularies")
    model_fields        = ("model_title","model_description","model_show_all_categories","model_show_all_attributes","model_nested")

    version         = CharField(label="Metadata Version",required=False)
    # TODO: IS THERE A BETTER WAY THAT I CAN SPECIFY THE QS? THIS SEEMS INNEFICIENT    
    vocabularies    = ModelMultipleChoiceField(label="Controlled Vocabularies",required=False,queryset=MetadataVocabulary.objects.none())   # qs set to none() b/c actual value is set in init below
    categorization  = ModelChoiceField(label="Categorization",required=False,queryset=MetadataCategorization.objects.none())                # qs set to none() b/c actual value is set in init below

    attribute_categories = ModelMultipleChoiceField(queryset=MetadataAttributeCategory.objects.none(),required=False) # the categories themselves
    attribute_categories_tags = CharField(label="Available Categories",required=False)  # the field that is used for the tagging widget
    attribute_categories_tags.help_text = "This widget contains the standard set of attribute categories associated with the metdata version.  If this set is unsuitable, or empty, then the categorization should be updated.  Please contact your administrator."
    attribute_categories_content = CharField(required=False)    # a hidden field used to store the current content of the categories during javascript manipulation

    property_categories = ModelMultipleChoiceField(queryset=MetadataPropertyCategory.objects.none(),required=False)
    property_categories_tags = CharField(label="Available Categories",required=False)
    property_categories_tags.help_text  = "This widget is used to customize the categories used to display scientific properties."
    property_categories_content = CharField(required=False)  # a hidden field used to store the current content of the categories during javascript manipulation
    
    def __init__(self,*args,**kwargs):
        _request = kwargs.pop("request",None)
        super(MetadataModelCustomizerForm,self).__init__(*args,**kwargs)
        customizer_instance = self.instance


        # initialize the subforms...
        if customizer_instance.pk:
            initial_attributes_data=None
            extra_attributes=0
        else:
            initial_attributes_data = [model_to_dict(temporary_attribute_customizer) for temporary_attribute_customizer in customizer_instance.temporary_attributes]
            extra_attributes = len(initial_attributes_data)

        AttributesFormSet = MetadataAttributeCustomizerInlineFormSetFactory(extra=extra_attributes,method=_request.method)
        self._subForms["attributes"] = [
            SubFormTypes.FORMSET,
            AttributesFormSet,
            AttributesFormSet(_request.POST,instance=customizer_instance) if (_request.method == "POST") else AttributesFormSet(initial=initial_attributes_data,instance=customizer_instance)
        ]        

        try:
            current_attribute_categories = customizer_instance.getCategorization().getCategories()
      
            self.fields["attribute_categories"].queryset = MetadataAttributeCategory.objects.filter(id__in=[category.id for category in current_attribute_categories])
            self.fields["attribute_categories_tags"].initial="|".join([category.name for category in current_attribute_categories])
        except AttributeError:
            # if there was no categorization assigned,
            # then attributes will not be associated w/ any categories
            # that's unfortunate, but it's not an error
            pass


        try:
            current_property_categories = customizer_instance.getVocabulary().getCategories()

            # TODO: ALSO ADD CUSTOM PROPERTIES!!!
            self.fields["property_categories"].queryset = MetadataPropertyCategory.objects.filter(id__in=[category.id for category in current_property_categories])
            self.fields["property_categories_tags"].initial="|".join([category.name for category in current_property_categories])

            component_tree = customizer_instance.getVocabulary().getComponents()
            component_list_generator = list_from_tree(component_tree)
            for component_name in component_list_generator:
                tag_field_name = component_name[0].lower()+"_property_categories_tags"                
                self.fields[tag_field_name] = CharField(label="Available Categories",required=False)
                self.fields[tag_field_name].initial="|".join([category.name for category in current_property_categories if category.component_name==component_name[0].lower()])
                update_field_widget_attributes(self.fields[tag_field_name],{"class":"tags"})

                if customizer_instance.pk:
                    extra_properties = 0
                    initial_properties_data=None
                else:
                    initial_properties_data = [model_to_dict(temporary_property_customizer) for temporary_property_customizer in customizer_instance.temporary_properties if temporary_property_customizer.property.component_name.lower()==component_name[0].lower()]
                    extra_properties = len(initial_properties_data)
                formset_field_name = component_name[0].lower()+"_properties"
                PropertiesFormSet = MetadataPropertyCustomizerInlineFormSetFactory(extra=extra_properties,method=_request.method)
                self._subForms[formset_field_name] = [
                    SubFormTypes.FORMSET,
                    PropertiesFormSet,
                    PropertiesFormSet(_request.POST,instance=customizer_instance) if (_request.method == "POST") else PropertiesFormSet(initial=initial_properties_data,instance=customizer_instance)
                ]
                


        except AttributeError:
            # if there were categories
            # then that's unfortunate, but it's not an error
            pass
        

### OLD WAY OF DOING THINGS. YUCK.
###        # get all categories with a mapping to this model
###        model_key = u'"%s":' % customizer_instance.model
###        current_property_categories = MetadataPropertyCategory.objects.filter(mapping__contains=model_key)
###
###        self.fields["property_categories"].queryset = current_property_categories
###        self.fields["property_categories_tags"].initial="|".join([category.name for category in current_property_categories])

        # add specific attributes to the remaining fields...
        self.fields["description"].widget.attrs["rows"] = 2
        self.fields["model_description"].widget.attrs["rows"] = 4

        self.fields["categorization"].queryset  = customizer_instance.getCategorizations()
        self.fields["vocabularies"].queryset    = customizer_instance.getVocabularies()

        update_field_widget_attributes(self.fields["attribute_categories_tags"],{"class":"tags"})
        update_field_widget_attributes(self.fields["property_categories_tags"],{"class":"tags"})
        update_field_widget_attributes(self.fields["attribute_categories_content"],{"class":"hidden"})
        update_field_widget_attributes(self.fields["property_categories_content"],{"class":"hidden"})

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
        subFormValidity = [subForm[2].is_valid() for subForm in self.getAllSubForms().itervalues() if subForm[2]]

        if not all(subFormValidity):
            for subForm in self.getAllSubForms().itervalues():
                print "subform errors:"
                print subForm[2].errors
        
        formValidity = all(subFormValidity) and super(MetadataModelCustomizerForm,self).is_valid()
        return formValidity

    def clean(self):
        
        customizer_instance = self.instance
        cleaned_data = self.cleaned_data

        # this is clearly overkill to just check one field
        # but it's future-proofed in case I want to check multiple fields at some later date
        fields_to_update = {}
        fields_to_check = ["name",]
        if customizer_instance.pk:
            for field_to_check in fields_to_check:
                if cleaned_data[field_to_check] != getattr(customizer_instance,field_to_check):
                    fields_to_update[field_to_check] = cleaned_data[field_to_check]

        if fields_to_update:
            for attributeSubForm in self._subForms["attributes"][2]:
                if hasattr(attributeSubForm,"cleaned_data"):
                    attribute_validated = True
                    attribute_data = attributeSubForm.cleaned_data
                else:
                    # TODO: NOT SURE IF THIS MAKES SENSE;
                    # IF THIS HASN'T VALIDATED, THEN AN ERROR WILL BE RAISED AND THINGS WON'T GET SAVED
                    # BUT THIS WOULD BE CALLED AGAIN ONCE THAT ERROR IS FIXED AND THE FORM IS RE-SUBMITTED
                    attribute_validated = False
                    for key,value in attributeSubForm.data.iteritems():
                        if key.startswith(attributeSubForm.prefix+"-"):
                            attribute_data[key.split(attributeSubForm.prefix+"-")[1]] = value

                # if this attribute is valid (ie: will be saved), and is a relationshipfield, and has 'customize_subform' set to True, and has created a subform_customizer...
                if attribute_validated and is_relationship_field(attribute_data["attribute_type"]) and attribute_data["customize_subform"] and attribute_data["subform_customizer"]:
                    # then update the fields of that subform_customizer
                    subform_customizer = attribute_data["subform_customizer"]
                    subform_customizer.recursivelyUpdateFields(fields_to_update)

        return cleaned_data

    def save_subforms(self,*args,**kwargs):
        print "TWO.ONE %s"%len(self.instance.attributes.all())
        _commit = kwargs.pop("commit",True)
        for key,value in self._subForms.iteritems():
            subFormType     = value[0]
            subFormClass    = value[1]
            subFormInstance = value[2]
            if subFormType == SubFormTypes.FORM:
                blah = subFormInstance.save(commit=False)
                blah.save()
                subFormInstance.save_m2m()
            elif subFormType == SubFormTypes.FORMSET:
                for blah in subFormInstance.forms:
                    foo = blah.save(commit=False)
                    print "before saving, pk=%s"%foo.pk
                    foo.save()
                    blah.save_m2m()
                    print "after saving, pk=%s"%foo.pk
#            subFormInstance.save(commit=_commit)
        print "TWO.TWO %s"%len(self.instance.attributes.all())


class MetadataAttributeCustomizerForm(ModelForm):
    class Meta:
        model = MetadataAttributeCustomizer
        fields = ("attribute_name", "attribute_type", "order", "category", "displayed", "verbose_name", "default_value", "documentation", "required", "editable", "unique", "cardinality", "enumerations", "default_enumerations", "open", "multi", "nullable", "enumeration_choices", "customize_subform")#, "subform_customizer")

    def __init__(self,*args,**kwargs):
        
        method = kwargs.pop("method","GET")
        super(MetadataAttributeCustomizerForm,self).__init__(*args,**kwargs)

        attribute_customizer = self.instance
        
        # get the form data...
        # if this is being loaded via POST, then the request will have been passed into the formset constructor
        # so I just need to work out which part of that request applies to _this_ form
        # if this is being loaded via GET, then the initial value will have been passed into the formset constructor
        # so I can use that directly
        attribute_data = {}
        if method=="POST":
            # (not sure why I can't do this in a list comprehension)
            for key,value in self.data.iteritems():
                if key.startswith(self.prefix+"-"):
                    attribute_data[key.split(self.prefix+"-")[1]] = value
        else:
            attribute_data = self.initial

        attribute_type = attribute_data["attribute_type"]
        attribute_name = attribute_data["attribute_name"]

        # don't want to show these fields, but still want access to them
        self.fields["attribute_name"].widget = HiddenInput()
        self.fields["attribute_type"].widget = HiddenInput()
        self.fields["order"].widget = HiddenInput()
        self.fields["category"].widget = HiddenInput()
        self.fields["enumeration_choices"].widget = HiddenInput()

        self.fields['documentation'].widget.attrs["rows"] = 3

        update_field_widget_attributes(self.fields["displayed"],{"class":"linked","onchange":"link(this,'false',{'required' : 'false'});"})
        update_field_widget_attributes(self.fields["required"],{"class":"linked","onchange":"link(this,'true',{'cardinality' : ['1','None']});link(this,'false',{'cardinality' : ['0','None']});"})
        update_field_widget_attributes(self.fields["order"],{"class":"set-label","onchange":"set_label(this,'field-order');"})
        update_field_widget_attributes(self.fields["customize_subform"],{"onchange":"enable(this,'true',['customize-subform']);"})

        if (attribute_type == "booleanfield"):
            # default_value should be a T/F combobox for boolean fields
            self.fields["default_value"].widget = Select(choices=((True,"True"),(False,"False")))

        if not is_relationship_field(attribute_type):                    
            del self.fields["customize_subform"]
            del self.fields["cardinality"]
        else:
            del self.fields["default_value"]
            pass

        if not is_atomic_field(attribute_type):
            del self.fields["unique"]
        else:
            pass

        if not is_enumeration_field(attribute_type):
            del self.fields["open"]
            del self.fields["multi"]
            del self.fields["nullable"]
            del self.fields["enumerations"]
            del self.fields["default_enumerations"]
            del self.fields["enumeration_choices"]
        else:
            del self.fields["default_value"]

            current_choices = [(choice,choice) for choice in attribute_data["enumeration_choices"].split("|")]
            self.fields["default_enumerations"].widget = SelectMultiple(choices=current_choices)
            self.fields["enumerations"].widget = SelectMultiple(choices=current_choices)
            self.initial["enumerations"] = [choice[0] for choice in current_choices]
            # TODO: I WOULD MUCH RATHER NOT HAVE TO DO THE ABOVE TWO LINES
            # AND JUST USE A CUSTOM ENUMERATION FIELD (SEE FIELDS.PY)
            # BUT I CAN'T GET "CHOICES" TO PROPAGATE TO THE WIDGET
            update_field_widget_attributes(self.fields["enumerations"],{"class":"dropdownchecklist","onchange":"restrict_options(this,['default_enumerations']);"})
            update_field_widget_attributes(self.fields["default_enumerations"],{"class":"dropdownchecklist"})

        # no longer displaying category; all customization of categories for attributes must come from categorization file
        #category = attribute.category
        #if category and category.getType()==CategoryTypes.ATTRIBUTE:
        #    # only bother showing the "category" widget if this is not a standard field
        #    del self.fields["category"]

###    def clean(self):
###        print "CLEANING SUBFORM"
###        super(MetadataAttributeCustomizerForm,self).clean()
###        return self.cleaned_data
###
    def save(self,*args,**kwargs):
        return super(MetadataAttributeCustomizerForm,self).save(*args,**kwargs)
###
###    def is_valid(self):
###        print "IS_VALID SUBFORM"
###        super(MetadataAttributeCustomizerForm,self).is_valid()

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
                return name
        except AttributeError:
            return None
        

def MetadataAttributeCustomizerInlineFormSetFactory(*args,**kwargs):
    _method = kwargs.pop("method","GET")
    new_kwargs = {
        "can_delete" : False,
        "form"       : MetadataAttributeCustomizerForm,
        "fk_name"    : "parent" # required b/c there are 2 foreignkeys to 'metadatamodelcustomizer'; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)

    _formset = inlineformset_factory(MetadataModelCustomizer,MetadataAttributeCustomizer,*args,**new_kwargs)
    _formset.form = staticmethod(curry(MetadataAttributeCustomizerForm,method=_method))
    return _formset


class MetadataPropertyCustomizerForm(ModelForm):
    class Meta:
        model   = MetadataPropertyCustomizer
        fields  = ("category","displayed","required","editable","verbose_name","default_value","documentation","open","multi","nullable","order")



    def __init__(self,*args,**kwargs):

        method = kwargs.pop("method","GET")
        super(MetadataPropertyCustomizerForm,self).__init__(*args,**kwargs)

        property_customizer = self.instance

        # don't want to show these fields, but still want access to them
        self.fields["order"].widget = HiddenInput()
        
        self.fields["category"].queryset = MetadataPropertyCategory.objects.none() # JQuery will take care of limiting this to the correct categories in the form

    def getPropertyName(self):
        try:
            if self.is_bound:
                return self.instance.property_name
            else:
                return self.initial["property_name"]
        except AttributeError:
            return None

    def getCategoryName(self):
        try:
            if self.is_bound:
                return self.instance.category.name
            else:
                category_pk = self.initial["category"]
                name = MetadataAttributeCategory.objects.get(pk=category_pk).name
                return name
        except AttributeError:
            return None

    def getPropertyOrder(self):
        try:
            if self.is_bound:
                return self.instance.order
            else:
                return self.initial["order"]
        except AttributeError:
            return None


def MetadataPropertyCustomizerInlineFormSetFactory(*args,**kwargs):
    _method = kwargs.pop("method","GET")
    new_kwargs = {
        "can_delete"  : False,
        "form"        : MetadataPropertyCustomizerForm
    }
    new_kwargs.update(kwargs)

    _formset = inlineformset_factory(MetadataModelCustomizer,MetadataPropertyCustomizer,*args,**new_kwargs)
    _formset.form = staticmethod(curry(MetadataPropertyCustomizerForm,method=_method))
    return _formset

