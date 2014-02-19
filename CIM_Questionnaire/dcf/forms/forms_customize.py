
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
__date__ ="Jun 12, 2013 12:17:09 PM"

"""
.. module:: forms_customize

Summary of module goes here

"""

from django.forms import *
from django.forms.models import BaseModelFormSet, BaseInlineFormSet
from django.forms.models import inlineformset_factory
from django.forms.models import modelformset_factory
from django.utils.functional import curry

from dcf.models import *
from dcf.utils import *

from dcf.forms.forms_categorize import save_standard_categories, save_scientific_categories

class MetadataModelCustomizerForm(ModelForm):

    class Meta:
        model   = MetadataModelCustomizer
        fields  = ( "name","description","default","model_title","model_description",      \
                    "model_show_all_categories","model_show_all_properties",               \
                    "model_nested","model_root_component","categorization","vocabularies", \
                    "project","version","model" )

    customizer_fields   = ("name","description","default","categorization","vocabularies",)
    model_fields        = ("model_title","model_description","model_show_all_categories","model_show_all_properties","model_nested","model_root_component")
    model_fields_for_subform = ("model_title","model_description","model_show_all_categories","model_show_all_properties",)

    # actual values for these fields is set below
    #version         = ModelChoiceField(label="Metadata Version",required=False,queryset=MetadataVersion.objects.none())
    categorization  = ModelChoiceField(label="Categorization",required=False,queryset=MetadataCategorization.objects.none())
    vocabularies    = ModelMultipleChoiceField(label="Controlled Vocabularies",required=False,queryset=MetadataVocabulary.objects.all())

    standard_categories                 = ModelMultipleChoiceField(queryset=MetadataStandardCategory.objects.none(),required=False) # the categories themselves
    standard_categories_tags            = CharField(label="Available Categories",required=False)                               # the field that is used for the tagging widget
    standard_categories_content         = CharField(required=False)                                                         # and the actual (JSON) content of the db
    standard_categories_tags.help_text  = "This widget contains the standard set of categories associated with the metdata version.  If this set is unsuitable, or empty, then the categorization should be updated.  Please contact your administrator."
    scientific_categories_content       = CharField(required=False)
    
    def __init__(self,*args,**kwargs):
        component_list = kwargs.pop("component_list",[])
        super(MetadataModelCustomizerForm,self).__init__(*args,**kwargs)
        customizer_instance = self.instance

        model_data = self.data or self.initial
        
        self.fields["project"].widget           = HiddenInput()
        self.fields["version"].widget           = HiddenInput()
        self.fields["model"].widget             = HiddenInput()


        categorization                          = self.initial["categorization"]
#        vocabularies                            = self.initial["vocabularies"]
        vocabularies = customizer_instance.project.vocabularies.all().filter(document_type__iexact=customizer_instance.model)

        self.fields["vocabularies"].queryset    = MetadataVocabulary.objects.filter(pk__in=[vocabulary.pk for vocabulary in vocabularies])
        self.fields["categorization"].queryset  = MetadataCategorization.objects.filter(pk__in=[categorization.pk])
        #self.fields["vocabularies"].initial     = vocabularies
        self.fields["categorization"].initial   = categorization
        
        try:
            current_standard_categories = categorization.categories.all().order_by("order")
            self.fields["standard_categories"].queryset = current_standard_categories
            self.fields["standard_categories_tags"].initial="|".join([category.name for category in current_standard_categories])

        except AttributeError:
            # if there was no categorization assigned,
            # then attributes will not be associated w/ any categories
            # that's unfortunate, but it's not an error
            pass

        try:
            scientific_categories_dict = json.loads(model_data["scientific_categories_content"])
            for component_name in component_list:
                field_name = component_name.lower() + "_scientific_categories_tags"
                self.fields[field_name] = CharField(label="Available Categories",required=False)
                self.fields[field_name].initial = \
                    "|".join([category["fields"]["name"] for category in scientific_categories_dict
                    if category["fields"]["component_name"].lower() == component_name.lower()
                ])
                update_field_widget_attributes(self.fields[field_name],{"class":"tags"})

        except KeyError:
            # when this form is used as a result of the customize_subform button
            # I don't bother including scientific properties
            pass

        self.fields["description"].widget.attrs["rows"]         = 2
        self.fields["model_description"].widget.attrs["rows"]   = 4
# TODO: MARKING THESE AS "disabled" MEANS THEIR VALUES DON'T GET PROPAGATED THROUGH THE SYSTEM
# SO I HAVE COMMENTED THIS OUT; BUT I STILL NEED A WAY TO PREVENT THEM FROM BEING SELECTED
#        self.fields["categorization"].widget.attrs["disabled"]    = True
        update_field_widget_attributes(self.fields["categorization"],{"class":"readonly"})
        update_field_widget_attributes(self.fields["standard_categories_tags"],{"class":"tags"})
        update_field_widget_attributes(self.fields["standard_categories"],{"class":"hidden"})
        update_field_widget_attributes(self.fields["standard_categories_content"],{"class":"hidden"})
        update_field_widget_attributes(self.fields["scientific_categories_content"],{"class":"hidden"})

    def getCustomizerFields(self):
        fields = list(self)
        return [field for field in fields if field.name in self.customizer_fields]

    def getModelFields(self):
        fields = list(self)
        return [field for field in fields if field.name in self.model_fields]

    def getModelFieldsForSubForm(self):
        fields = list(self)
        return [field for field in fields if field.name in self.model_fields_for_subform]

    # TODO: THIS IS THE ONLY FN I'M NOT HAPPY W/
    # I HAVE TO SAVE THE CATEGORIES HERE JUST IN CASE THERE ARE NEW ONES THAT SCIENTIFIC PROPERTIES REFER TO
    # OTHERWISE WHEN I TRY TO CLEAN SCIENTIFIC PROPERTIES, IT WILL FAIL
    def clean(self):
        cleaned_data = self.cleaned_data
        project = cleaned_data["project"]
        try:
            # categories have to be explicitly saved separately
            # b/c they are manipulated via a JQuery tagging widget and therefore aren't bound to a form
            save_standard_categories(json.loads(self.data["standard_categories_content"]),project)
            save_scientific_categories(json.loads(self.data["scientific_categories_content"]),project)
        except:
            # if this form is being evaluated in the context of a subform,
            # then the categories will have been blank,
            # and json.loads will raise an error
            pass

        return cleaned_data


#    def validate_unique(self):
#        model_customizer = self.instance
#        try:
#            model_customizer.validate_unique()
#        except ValidationError, e:
#            print "UNIQUEERROR"
#            # TODO: THIS IS RECORDING AN ERROR FOR EVERY FIELD
#            # IN THEORY, THERE COULD BE MULTIPLE UNIQUE_FIELD_SETS
#            # ONLY SOME OF WHICH HAVE FAILED THIS VALIDATION
#            for unique_field_set in model_customizer.getUniqueTogether():
#                for unique_field in unique_field_set:
#                    self.errors[unique_field] = "This value must be unique."
   
class MetadataStandardPropertyCustomizerForm(ModelForm):

    class Meta:
        model = MetadataStandardPropertyCustomizer
        fields  = ( "name","type","field_type","order","category","displayed","required","editable",    \
                    "default_value",  \
                    "unique","verbose_name","documentation","suggestions","inherited","enumeration_values",         \
                    "enumeration_default","enumeration_choices","enumeration_open","enumeration_multi", \
                    "enumeration_nullable","relationship_target_model","relationship_source_model",     \
                    "relationship_cardinality","customize_subform","subform_customizer", "proxy", )

    def __init__(self,*args,**kwargs):
        super(MetadataStandardPropertyCustomizerForm,self).__init__(*args,**kwargs)
        customizer_instance = self.instance

        # get the form data...
        # if this is being loaded via POST, then the request will have been passed into the formset constructor
        # so I just need to work out which part of that request applies to _this_ form
        # if this is being loaded via GET, then the initial value will have been passed into the formset constructor
        # so I can use that directly
        property_data = {}
        #if method=="POST":
        if self.data:
            # (not sure why I can't do this in a list comprehension)
            for key,value in self.data.iteritems():
                if key.startswith(self.prefix+"-"):
                    property_data[key.split(self.prefix+"-")[1]] = value
        else:
            property_data = self.initial

        # don't want to show these fields, but still want access to them
        self.fields["name"].widget       = HiddenInput()
        self.fields["type"].widget       = HiddenInput()
        self.fields["category"].widget   = HiddenInput()
        self.fields["order"].widget      = HiddenInput()
        self.fields["field_type"].widget = HiddenInput()
        self.fields["enumeration_choices"].widget = HiddenInput()
        self.fields["relationship_target_model"].widget = HiddenInput()
        self.fields["relationship_source_model"].widget = HiddenInput()
        self.fields["subform_customizer"].widget        = HiddenInput()
        self.fields["proxy"].widget  = HiddenInput()

        # customize some of the widgets
        self.fields["documentation"].widget.attrs["rows"] = 3
        self.fields["suggestions"].widget.attrs["rows"] = 2

        # attach javascript events to some of the widgets
        update_field_widget_attributes(self.fields["enumeration_open"],{"onchange":"enable(this,'true',['suggestions']);"})
        update_field_widget_attributes(self.fields["category"],{"onchange":"set_label(this,'property_category');"})
        update_field_widget_attributes(self.fields["order"],{"onchange":"set_label(this,'property_order');"})
        update_field_widget_attributes(self.fields["customize_subform"],{"onchange":"enable(this,'true',['customize-subform']);"})
        
        metadata_field_type = customizer_instance.type if customizer_instance.pk else property_data["type"]
        model_field_type = customizer_instance.field_type if customizer_instance.pk else property_data["field_type"]
            
        if not metadata_field_type == MetadataFieldTypes.ATOMIC:
            pass
        else:
            if (model_field_type == "booleanfield"):
                # default_value should be a T/F combobox for boolean fields
                self.fields["default_value"].widget = Select(choices=((True,"True"),(False,"False")))

        if not metadata_field_type == MetadataFieldTypes.RELATIONSHIP:
            del self.fields["relationship_cardinality"]
            del self.fields["relationship_source_model"]
            del self.fields["relationship_target_model"]
            del self.fields["customize_subform"]
            del self.fields["subform_customizer"]
        else:
            del self.fields["default_value"]
            del self.fields["suggestions"]
            if model_field_type == "manytoonefield":
                del self.fields["relationship_cardinality"]

        if not metadata_field_type == MetadataFieldTypes.ENUMERATION:
            del self.fields["enumeration_values"]
            del self.fields["enumeration_default"]
            del self.fields["enumeration_choices"]
            del self.fields["enumeration_open"]
            del self.fields["enumeration_multi"]
            del self.fields["enumeration_nullable"]
        else:

            enumeration_choices = customizer_instance.enumeration_choices if customizer_instance.pk else property_data["enumeration_choices"]
            try:
                enumeration_values  = customizer_instance.enumeration_values if customizer_instance.pk else property_data["enumeration_values"]
                enumeration_default = customizer_instance.enumeration_default if customizer_instance.pk else property_data["enumeration_default"]
            except KeyError:
                # default value for these fields is None
                # therefore, if it wasn't set in a previous POST (and hence in property_data), then it will need to be explicitly set here
                enumeration_values = enumeration_choices
                enumeration_default = ""


            enumeration_choices_tuple = [(choice,choice) for choice in enumeration_choices.split("|")]
            self.fields["enumeration_values"].widget    = SelectMultiple(choices=enumeration_choices_tuple)
            self.fields["enumeration_default"].widget   = SelectMultiple(choices=enumeration_choices_tuple)
            self.initial["enumeration_values"]          = enumeration_values.split("|") if enumeration_values else enumeration_choices.split("|")
            self.initial["enumeration_default"]         = enumeration_default.split("|") if enumeration_default else []

            # (have to do this down here b/c I change the widget above)
            update_field_widget_attributes(self.fields["enumeration_values"],{"class":"multiselect","onchange":"restrict_options(this,['enumeration_default']);"})
            update_field_widget_attributes(self.fields["enumeration_default"],{"class":"multiselect"})

def MetadataStandardPropertyCustomizerFormSetFactory(*args,**kwargs):
    _queryset   = kwargs.pop("queryset",None)
    _initial    = kwargs.pop("initial",None)
    _prefix     = kwargs.pop("prefix","standard_property")
    _request    = kwargs.pop("request",None)
    new_kwargs = {
        "extra"       : kwargs.pop("extra",0),
        "can_delete"  : False,
        "form"  : MetadataStandardPropertyCustomizerForm
    }
    new_kwargs.update(kwargs)

    _formset = modelformset_factory(MetadataStandardPropertyCustomizer,*args,**new_kwargs)
    #_formset.form = staticmethod(curry(MetadataStandardPropertyCustomizerForm,request=_request))

    if _request and _request.method == "POST":
        return _formset(_request.POST,prefix=_prefix)

    return _formset(queryset=_queryset,initial=_initial,prefix=_prefix)


def MetadataStandardPropertyCustomizerInlineFormSetFactory(*args,**kwargs):
    _prefix     = kwargs.pop("prefix","standard_property")
    _request    = kwargs.pop("request",None)
    _initial    = kwargs.pop("initial",[])
    _instance   = kwargs.pop("instance")
    new_kwargs = {
        "can_delete" : False,
        "extra"      : kwargs.pop("extra",0),
        "form"       : MetadataStandardPropertyCustomizerForm,
        "fk_name"    : "parent" # required in-case there are more than 1 fk's to "metadatamodelcustomizer"; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)
 
    _formset = inlineformset_factory(MetadataModelCustomizer,MetadataStandardPropertyCustomizer,*args,**new_kwargs)
    #_formset.form = staticmethod(curry(MetadataStandardPropertyCustomizerForm,reques=_request))

    if _request and _request.method == "POST":
        return _formset(_request.POST,instance=_instance,prefix=_prefix)
    
    return _formset(initial=_initial,instance=_instance,prefix=_prefix)

class MetadataScientificPropertyCustomizerForm(ModelForm):

    class Meta:
        model = MetadataScientificPropertyCustomizer
        fields  = ( "name","type","order","component_name","vocabulary","choice","value_choices",   \
                    "category","displayed","required","editable","default_value","unique",          \
                    "verbose_name","documentation","value","value_default","suggestions","open",    \
                    "multi","nullable","value_format","value_units", "choice", "proxy",             \
                    "show_extra_attributes", "edit_extra_attributes", "standard_name", "long_name", \
                    "description" )
        #exclude = ("proxy","parent",)



    def __init__(self,*args,**kwargs):
        super(MetadataScientificPropertyCustomizerForm,self).__init__(*args,**kwargs)
        customizer_instance = self.instance

        # get the form data...
        # if this is being loaded via POST, then the request will have been passed into the formset constructor
        # so I just need to work out which part of that request applies to _this_ form
        # if this is being loaded via GET, then the initial value will have been passed into the formset constructor
        # so I can use that directly

        property_data = {}
        #if method=="POST":
        if self.data:
            # (not sure why I can't do this in a list comprehension)
            for key,value in self.data.iteritems():
                if key.startswith(self.prefix+"-"):
                    property_data[key.split(self.prefix+"-")[1]] = value[0] if isinstance(value,tuple) else value
        else:
            property_data = self.initial

        
        # customize some of the widgets
        self.fields["documentation"].widget.attrs["rows"] = 3
        self.fields["suggestions"].widget.attrs["rows"] = 2
        self.fields["description"].widget.attrs["rows"] = 3
        self.fields["category"].queryset = MetadataScientificCategory.objects.filter(component_name=property_data["component_name"])

        update_field_widget_attributes(self.fields["show_extra_attributes"],{"onchange":"enable(this,'true',['edit_extra_attributes','standard_name','long_name','description']);"})

        # don't want to show these fields, but still want access to them
        self.fields["name"].widget           = HiddenInput()
        self.fields["type"].widget           = HiddenInput()
        self.fields["order"].widget          = HiddenInput()
        self.fields["component_name"].widget = HiddenInput()
        self.fields["vocabulary"].widget     = HiddenInput()
        self.fields["choice"].widget         = HiddenInput()
        self.fields["value_choices"].widget  = HiddenInput()
        self.fields["proxy"].widget          = HiddenInput()

        property_choice_type = customizer_instance.choice if customizer_instance.pk else property_data["choice"]

        if property_choice_type == "keyboard":
            del self.fields["open"]
            del self.fields["multi"]
            del self.fields["nullable"]
            del self.fields["value"]
            del self.fields["value_default"]
        else:
            del self.fields["value_format"]
            del self.fields["value_units"]
            del self.fields["default_value"]
            del self.fields["unique"]
 
            value_choices = customizer_instance.value_choices if customizer_instance.pk else property_data["value_choices"]
            try:
                value  = customizer_instance.value if customizer_instance.pk else property_data["value"]
                value_default = customizer_instance.value_default if customizer_instance.pk else property_data["value_default"]
            except KeyError:
                # default value for these fields is None
                # therefore, if it wasn't set in a previous POST (and hence in property_data), then it will need to be explicitly set here
                value = value_choices
                value_default = ""

            value_choices_tuple = [(choice,choice) for choice in value_choices.split("|")]
            self.fields["value_default"].widget    = SelectMultiple(choices=value_choices_tuple)
            self.fields["value"].widget            = SelectMultiple(choices=value_choices_tuple)
            self.initial["value_default"]          = value_default.split("|") if value_default else []
            self.initial["value"]                  = value.split("|") if value else value_choices.split("|")

            # (have to do this down here b/c I change the widget above)
            update_field_widget_attributes(self.fields["value"],{"class":"multiselect","onchange":"restrict_options(this,['value_default']);"})
            update_field_widget_attributes(self.fields["value_default"],{"class":"multiselect"})

            if property_choice_type == "OR":
                self.initial["multi"] = True

            elif property_choice_type == "XOR":
                self.initial["multi"] = False

        update_field_widget_attributes(self.fields["category"],{"onchange":"set_label(this,'property_category');"})
        update_field_widget_attributes(self.fields["order"],{"onchange":"set_label(this,'property_order');"})

    def clean(self):

        cleaned_data = self.cleaned_data

        # handles the case where I set a property category to a new category
        if "category" not in cleaned_data:
            category_key = self.prefix+"-category"
            component_name_key = self.prefix+"-component_name"
            category = MetadataScientificCategory.objects.get(
                key=self.data[category_key],
                component_name=self.data[component_name_key],
            )
            cleaned_data["category"] = category
            del self.errors["category"]
            
        return cleaned_data


#
#class MetadataScientificPropertyCustomizerInlineFormSet(BaseInlineFormSet):
#    filter_properties = {}
#
#
#    def __init__(self,*args,**kwargs):
#        _filter = kwargs.pop("filter",None)
#        super(MetadataScientificPropertyCustomizerInlineFormSet,self).__init__(*args,**kwargs)
#        self.filter_properties = _filter
#        
#    def get_queryset(self):
#
#        qs = super(MetadataScientificPropertyCustomizerInlineFormSet,self).get_queryset()
#        if self.filter_properties:
#            return qs.filter(component_name="atmosadvection")
#        return qs

def MetadataScientificPropertyCustomizerFormSetFactory(*args,**kwargs):
    _queryset   = kwargs.pop("queryset",None)
    _initial    = kwargs.pop("initial",None)
    #_prefix     = kwargs.pop("prefix","scientific_property")
    _request    = kwargs.pop("request",None)
    new_kwargs = {
        "extra"       : kwargs.pop("extra",0),
        "can_delete"  : False,
        "form"  : MetadataScientificPropertyCustomizerForm
    }
    new_kwargs.update(kwargs)

    _formset = modelformset_factory(MetadataScientificPropertyCustomizer,*args,**new_kwargs)
    #_formset.form = staticmethod(curry(MetadataStandardPropertyCustomizerForm,request=_request))

    if _request and _request.method == "POST":
        return _formset(_request.POST,prefix=_prefix)

    return _formset(queryset=_queryset,initial=_initial,prefix=_prefix)

def MetadataScientificPropertyCustomizerInlineFormSetFactory(*args,**kwargs):
    _prefix     = kwargs.pop("prefix","scientific_property")
    _request    = kwargs.pop("request",None)
    _initial    = kwargs.pop("initial",[])
    _instance   = kwargs.pop("instance")
    _queryset   = kwargs.pop("queryset",None)
    _filter     = kwargs.pop("filter",None)
    new_kwargs = {
        "can_delete" : False,
        "extra"      : kwargs.pop("extra",0),
        #"formset"    : MetadataScientificPropertyCustomizerInlineFormSet,
        "form"       : MetadataScientificPropertyCustomizerForm,
        "fk_name"    : "parent" # required in-case there are more than 1 fk's to "metadatamodelcustomizer"; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)

    _formset = inlineformset_factory(MetadataModelCustomizer,MetadataScientificPropertyCustomizer,*args,**new_kwargs)
    #_formset.form = staticmethod(curry(MetadataScientificPropertyCustomizerForm,request=_request))

    if _request and _request.method == "POST":
        return _formset(_request.POST,queryset=_queryset,instance=_instance,prefix=_prefix)
    return _formset(initial=_initial,instance=_instance,prefix=_prefix)