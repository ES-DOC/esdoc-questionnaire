
####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Dec 28, 2013 4:56:56 PM"

"""
.. module:: forms_customize

Summary of module goes here

"""

import time
from collections        import OrderedDict

from django.core    import serializers

from django.forms.models import BaseInlineFormSet
from django.forms.models import inlineformset_factory

from django.utils import timezone
from django.utils.functional        import curry
from django.template.defaultfilters import slugify
from django.forms.util  import ErrorList

from django.forms import *

from CIM_Questionnaire.questionnaire.utils import find_in_sequence, get_initial_data, JSON_SERIALIZER, QuestionnaireError
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataModelCustomizer, MetadataStandardCategoryCustomizer, MetadataStandardPropertyCustomizer, MetadataScientificCategoryCustomizer, MetadataScientificPropertyCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy, MetadataStandardPropertyProxy, MetadataScientificPropertyProxy
from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes, EMPTY_CHOICE
from CIM_Questionnaire.questionnaire.utils import set_field_widget_attributes, update_field_widget_attributes

from CIM_Questionnaire.questionnaire.forms import MetadataCustomizerForm

def save_valid_forms(model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets):

    model_customizer_instance = model_customizer_form.save()

    active_vocabularies                 = model_customizer_form.cleaned_data["vocabularies"]
    standard_categories_to_process      = model_customizer_form.standard_categories_to_process
    scientific_categories_to_process    = model_customizer_form.scientific_categories_to_process

    # save (or delete) the standard category customizers...
    active_standard_categories = []
    for standard_category_to_process in standard_categories_to_process:
        standard_category_customizer = standard_category_to_process.object
        if standard_category_customizer.pending_deletion:
            standard_category_to_process.delete()
        else:
            standard_category_customizer.model_customizer = model_customizer_instance
            standard_category_to_process.save()
            active_standard_categories.append(standard_category_customizer)

    # save (or delete) the scientific category customizers...
    active_scientific_categories = {}
    for vocabulary_key,scientific_categories_to_process_dict in scientific_categories_to_process.iteritems():
        active_scientific_categories[vocabulary_key] = {}
        for component_key,scientific_categories_to_process_list in scientific_categories_to_process_dict.iteritems():
            active_scientific_categories[vocabulary_key][component_key] = []
            for scientific_category_to_process in scientific_categories_to_process_list:
                scientific_category_customizer = scientific_category_to_process.object
                if scientific_category_customizer.pending_deletion:
                    scientific_category_customizer.delete()
                else:
                    scientific_category_customizer.model_customizer = model_customizer_instance
                    scientific_category_customizer.vocabulary_key = vocabulary_key
                    scientific_category_customizer.component_key = component_key
                    scientific_category_customizer.model_key = u"%s_%s" % (vocabulary_key,component_key)
                    scientific_category_customizer.save()
                    active_scientific_categories[vocabulary_key][component_key].append(scientific_category_customizer)

    # save the standard property customizers...
    standard_property_customizer_instances = standard_property_customizer_formset.save(commit=False)
    for standard_property_customizer_instance in standard_property_customizer_instances:
        category_key = slugify(standard_property_customizer_instance.category_name)
        category = find_in_sequence(lambda category: category.key==category_key,active_standard_categories)
        standard_property_customizer_instance.category = category
        standard_property_customizer_instance.save()

    # save the scientific property customizers...
    for (vocabulary_key,formset_dictionary) in scientific_property_customizer_formsets.iteritems():
        if find_in_sequence(lambda vocabulary: slugify(vocabulary.name)==vocabulary_key,active_vocabularies):
            for (component_key,scientific_property_customizer_formset) in formset_dictionary.iteritems():
                scientific_property_customizer_instances = scientific_property_customizer_formset.save(commit=False)
                for scientific_property_customizer_instance in scientific_property_customizer_instances:
                    category_key = slugify(scientific_property_customizer_instance.category_name)
                    category = find_in_sequence(lambda category: category.key==category_key,active_scientific_categories[vocabulary_key][component_key])
                    scientific_property_customizer_instance.category = category
                    scientific_property_customizer_instance.save()

def create_model_customizer_form_data(model_customizer,standard_category_customizers,scientific_category_customizers,vocabularies=[]):

    model_customizer_form_data = get_initial_data(model_customizer,{
        "last_modified"                 : time.strftime("%c"),
        "standard_categories_content"   : JSON_SERIALIZER.serialize(standard_category_customizers),
        "standard_categories_tags"      : "|".join([standard_category.name for standard_category in standard_category_customizers]),
        "vocabularies"                  : vocabularies,
    })

    # if not model_customizer.pk:
    #     # if this is a new customizer, by default all of the vocabularies should be active
    #     # if this is not a new customizer, then the vocabulary order will have been set previously
    #     model_customizer_form_data["vocabulary_order"]  = ",".join(map(str,[vocabulary.pk for vocabulary in vocabularies]))

    for vocabulary_key,scientific_category_customizer_dict in scientific_category_customizers.iteritems():
        for component_key,scientific_category_customizer_list in scientific_category_customizer_dict.iteritems():
            scientific_categories_content_field_name = u"%s_%s_scientific_categories_content" % (vocabulary_key,component_key)
            scientific_categories_tags_field_name = u"%s_%s_scientific_categories_tags" % (vocabulary_key,component_key)
            model_customizer_form_data[scientific_categories_content_field_name] = JSON_SERIALIZER.serialize(scientific_category_customizer_list)
            model_customizer_form_data[scientific_categories_tags_field_name] = "|".join([scientific_category.name for scientific_category in scientific_category_customizer_list])

    return model_customizer_form_data


class MetadataModelCustomizerForm(MetadataCustomizerForm):

    class Meta:
        model   = MetadataModelCustomizer
        
        fields  = [
                    # hidden fields...
                    "proxy","project","version","vocabulary_order",
                    # customizer fields...
                    "name","description","vocabularies","default",
                    # document fields...
                    "model_title","model_description","model_show_all_categories","model_show_all_properties","model_show_hierarchy","model_hierarchy_name","model_root_component",
                    # other fields...
                    "standard_categories_content","standard_categories_tags",
                  ]

    _hidden_fields       = ("proxy","project","version","vocabulary_order",)
    _customizer_fields   = ("name","description","default","vocabularies",)
    _document_fields     = ("model_title","model_description","model_show_all_categories","model_show_all_properties","model_show_hierarchy","model_hierarchy_name","model_root_component",)
    
    standard_categories_content = CharField(required=False,widget=Textarea)                 # the categories themselves
    standard_categories_tags    = CharField(label="Available Categories",required=False)    # the field used by the tagging widget
    standard_categories_tags.help_text = "This widget contains the standard set of categories associated with the CIM version. If this set is unsuitable, or empty, then the categorization should be updated. Please contact your administrator."

    # scientific categories are done on a per-cv / per-component basis in __init__ below

    standard_categories_to_process = []
    scientific_categories_to_process = {}
    
    def get_hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)

    def get_customizer_fields(self):
        return self.get_fields_from_list(self._customizer_fields)

    def get_document_fields(self):
        return self.get_fields_from_list(self._document_fields)

    def __init__(self,*args,**kwargs):
        is_subform = kwargs.pop("is_subform",False)
        all_vocabularies = kwargs.pop("all_vocabularies",[])
        
        super(MetadataModelCustomizerForm,self).__init__(*args,**kwargs)

        if is_subform:
            #update_field_widget_attributes(self.fields["name"],{"class":"readonly","readonly":"readonly"})
            #update_field_widget_attributes(self.fields["default"],{"class":"readonly","readonly":"readonly"})
            del(self.fields["name"])
            del(self.fields["default"])
            del(self.fields["vocabularies"])
            del(self.fields["vocabulary_order"])
            del(self.fields["model_show_hierarchy"])
            del(self.fields["model_root_component"])
            all_vocabularies = []
        else:
            self.fields["vocabularies"].queryset = all_vocabularies
            update_field_widget_attributes(self.fields["vocabularies"],{"class":"multiselect"})
            update_field_widget_attributes(self.fields["model_show_hierarchy"],{"class":"enabler"})
            set_field_widget_attributes(self.fields["model_show_hierarchy"],{"onchange":"enable(this,'true',['model_root_component','model_hierarchy_name']);",})

        set_field_widget_attributes(self.fields["description"],{"cols":"60","rows":"4"})

        set_field_widget_attributes(self.fields["model_description"],{"cols":"60","rows":"4"})

        update_field_widget_attributes(self.fields["standard_categories_tags"],{"class":"tags"})

        for vocabulary in all_vocabularies:
            vocabulary_key = slugify(vocabulary.name)
            for component_proxy in vocabulary.component_proxies.all():
                component_key = slugify(component_proxy.name)
                scientific_categories_content_field_name                = vocabulary_key+"_"+component_key + "_scientific_categories_content"
                scientific_categories_tags_field_name                   = vocabulary_key+"_"+component_key + "_scientific_categories_tags"
                self.fields[scientific_categories_content_field_name]   = CharField(required=False,widget=Textarea)               # the categories themselves
                self.fields[scientific_categories_tags_field_name]      = CharField(label="Available Categories",required=False)  # the field used by the tagging widget
                self.fields[scientific_categories_tags_field_name].help_text = "This widget contains the set of categories associated with this component of this CV.  Users can add to this set via this customization."
                update_field_widget_attributes(self.fields[scientific_categories_tags_field_name],{"class":"tags"})
        
        
    def clean_default(self):
        cleaned_data = self.cleaned_data
        default = cleaned_data.get("default") # using the get fn instead of directly accessing the dictionary in-case the field is missing, as w/ subform customizers
        if default:
            other_customizer_filter_kwargs = {
                "default"   : True,
                "proxy"     : cleaned_data["proxy"],
                "project"   : cleaned_data["project"],
                "version"   : cleaned_data["version"],
            }
            other_customizers = MetadataModelCustomizer.objects.filter(**other_customizer_filter_kwargs)
            this_customizer = self.instance
            if this_customizer.pk:
                other_customizers = other_customizers.exclude(pk=this_customizer.pk)
            if other_customizers.count() != 0:
                raise ValidationError("A default customizer already exists.")
            
        return default

    def clean(self):
        # calling the parent class's clean fun automatically sets a
        # flag that forces unique (and unique_together) validation
        super(MetadataModelCustomizerForm,self).clean()
        cleaned_data = self.cleaned_data

        # categories have to be saved separately
        # since they are manipulated via a JQuery tagging widget
        # and therefore aren't part of the form

        # NOTE: MAKE SURE NOT TO ACCESS THE CATEGORY_CONTENT FIELDS BEFORE DESERIALIZING THEM, AS THIS CAUSES ERRORS LATER ON
        self.standard_categories_to_process[:] = [] # fancy way of clearing the list, making sure any references are also updated
        for deserialized_standard_category_customizer in serializers.deserialize("json", cleaned_data["standard_categories_content"],ignorenonexistent=True):
            self.standard_categories_to_process.append(deserialized_standard_category_customizer)
        try:
            for vocabulary in self.cleaned_data["vocabularies"]:
                vocabulary_key = slugify(vocabulary.name)
                self.scientific_categories_to_process[vocabulary_key] = {}
                for component_proxy in vocabulary.component_proxies.all():
                    component_key = slugify(component_proxy.name)
                    scientific_categories_content_field_name = vocabulary_key+"_"+component_key+"_scientific_categories_content"
                    self.scientific_categories_to_process[vocabulary_key][component_key] = []
                    for deserialized_scientific_category_customizer in serializers.deserialize("json", self.data[scientific_categories_content_field_name],ignorenonexistent=True):
                        self.scientific_categories_to_process[vocabulary_key][component_key].append(deserialized_scientific_category_customizer)
        except KeyError:
            # this takes care of the case when this being called on a subform
            pass
        except:
            import ipdb; ipdb.set_trace()

        return cleaned_data
        
    def validate_unique(self):        
        model_customizer = self.instance
        try:
            model_customizer.validate_unique()
        except ValidationError, e:
            # if there is a validation error then apply that error to the individual fields
            # so it shows up in the form and is rendered nicely via JQuery
            unique_together_fields_list = model_customizer.get_unique_together()
            for unique_together_fields in unique_together_fields_list:
                if any(field.lower() in " ".join(e.messages).lower() for field in unique_together_fields):
                    msg = "Customizer with this %s already exists" % (", ".join(unique_together_fields))
                    for unique_together_field in unique_together_fields:
                        self.errors[unique_together_field] = msg


class MetadataPropertyCustomizerInlineFormSet(BaseInlineFormSet):

    number_of_properties = 0
    
    # just using this class to automatically sort the forms based on the field order

    def __iter__(self):
        """Yields the forms in the order they should (initially) be rendered"""
        forms = list(self.forms)
        try:
            forms.sort(key = lambda x: x.initial["order"])
        except KeyError:
            forms.sort(key = lambda x: x.data["%s-order"%(x.prefix)])
        return iter(forms)

    def __getitem__(self, index):
        """Returns the form at the given index, based on the rendering order"""
        forms = list(self.forms)
        try:
            forms.sort(key = lambda x: x.initial["order"])
        except KeyError:
            forms.sort(key = lambda x: x.data["%s-order"%(x.prefix)])
        return forms[index]

    # also using it to cache fk or m2m fields to avoid needless (on the order of 30K!) db hits

    def _construct_form(self, i, **kwargs):

        form = super(MetadataPropertyCustomizerInlineFormSet,self)._construct_form(i,**kwargs)

        for cached_field_name in form.cached_fields:
            cached_field = form.fields[cached_field_name]
            cached_field_key = u"%s_%s" % (self.prefix,cached_field_name)
            cached_field.cache_choices = True
            choices = getattr(self, '_cached_choices_%s'%(cached_field_key), None)
            if choices is None:
                choices = list(cached_field.choices)
                setattr(self, '_cached_choices_%s'%(cached_field_key), choices)
            cached_field.choice_cache = choices

        return form

def create_standard_property_customizer_form_data(model_customizer,standard_property_customizer):

    standard_property_customizer_form_data = get_initial_data(standard_property_customizer,{
        "last_modified"                 : time.strftime("%c"),
    })
    
    field_type = standard_property_customizer_form_data["field_type"]

    if field_type == MetadataFieldTypes.ATOMIC:
        pass

    elif field_type == MetadataFieldTypes.ENUMERATION:
        current_enumeration_choices = standard_property_customizer_form_data["enumeration_choices"]
        current_enumeration_default = standard_property_customizer_form_data["enumeration_default"]
        if current_enumeration_choices:
            standard_property_customizer_form_data["enumeration_choices"] = current_enumeration_choices.split("|")
        if current_enumeration_default:
            standard_property_customizer_form_data["enumeration_default"] = current_enumeration_default.split("|")

        # BE AWARE THAT CHECKING THIS DICT ITEM (WHOSE VALUE AS A LIST) WON'T GIVE THE FULL LIST
        # APPARENTLY, THIS IS A "FEATURE" AND NOT A "BUG" [https://code.djangoproject.com/ticket/1130]

    elif field_type == MetadataFieldTypes.RELATIONSHIP:
        pass

    else:
        msg = "invalid field type for standard property: '%s'" % (field_type)
        raise QuestionnaireError(msg)

    standard_category = standard_property_customizer.category
    if standard_category:
        standard_property_customizer_form_data["category"] = standard_category.key
        standard_property_customizer_form_data["category_name"] = standard_category.name

    return standard_property_customizer_form_data

class MetadataStandardPropertyCustomizerForm(MetadataCustomizerForm):

    class Meta:
        model = MetadataStandardPropertyCustomizer
        fields  = [
                # hidden fields...
                "field_type","proxy","category",
                # header fields...
                "name","category_name","order",
                # common fields...
                "displayed", "required", "editable", "unique", "verbose_name", "default_value", "documentation","inline_help","inherited",
                # atomic fields...
                "atomic_type","suggestions",
                # enumeration fields...
                "enumeration_choices","enumeration_default","enumeration_open","enumeration_multi","enumeration_nullable",
                # relationship fields...
                "relationship_cardinality","relationship_show_subform",
              ]

    category_name = CharField(label="Category",required=False)
    category      = ChoiceField(required=False)

    _hidden_fields       = ("field_type","proxy","category",)
    _header_fields       = ("name","category_name","order")
    _common_fields       = ("displayed","required","editable","unique","verbose_name","documentation","inline_help","default_value","inherited")
    _atomic_fields       = ("atomic_type","suggestions",)
    _enumeration_fields  = ("enumeration_choices","enumeration_default","enumeration_open","enumeration_multi","enumeration_nullable",)
    _relationship_fields = ("relationship_cardinality","relationship_show_subform",)


    # set of fields that will be the same for all members of a formset; thus I can cache the query (for relationship fields)
    cached_fields       = []

    def get_hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)

    def get_header_fields(self):
        return self.get_fields_from_list(self._header_fields)

    def get_atomic_fields(self):
        fields = list(self)

        common_fields = [field for field in fields if field.name in self._common_fields]
        atomic_fields = [field for field in fields if field.name in self._atomic_fields]

        all_fields = common_fields + atomic_fields
        all_fields.sort(key=lambda field: fields.index(field))
        return all_fields

    def get_enumeration_fields(self):
        fields = list(self)

        common_fields = [field for field in fields if field.name in self._common_fields]
        atomic_fields = [field for field in fields if field.name in self._enumeration_fields]

        all_fields = common_fields + atomic_fields
        all_fields.sort(key=lambda field: fields.index(field))
        return all_fields

    def get_relationship_fields(self):
        fields = list(self)

        common_fields = [field for field in fields if field.name in self._common_fields]
        atomic_fields = [field for field in fields if field.name in self._relationship_fields]

        all_fields = common_fields + atomic_fields
        all_fields.sort(key=lambda field: fields.index(field))
        return all_fields

    def __init__(self,*args,**kwargs):
        # category_choices was passed in via curry() in the factory function below
        category_choices = kwargs.pop("category_choices",[])

        super(MetadataStandardPropertyCustomizerForm,self).__init__(*args,**kwargs)
        
        property_customizer = self.instance
        # this attribute is needed b/c I access it in the customize_template to decide which other templates to include
        self.type = self.get_current_field_value("field_type")

        if property_customizer.pk:
            # ordinarily, this is done in create_scientific_property_customizer_form_data above
            # but if this is an existing model, I still need to do this jiggery-pokery someplace
            # not displaying category field for standard_properties (so I should be able to get away w/ not doing this)
            #self.initial["category"] = property_customizer.category.key
            if self.type == MetadataFieldTypes.ENUMERATION:
                current_enumeration_choices = self.get_current_field_value("enumeration_choices")
                current_enumeration_default = self.get_current_field_value("enumeration_default")
                if current_enumeration_choices:
                    self.initial["enumeration_choices"] = current_enumeration_choices.split("|")
                if current_enumeration_default:
                    self.initial["enumeration_default"] = current_enumeration_default.split("|")

        if self.type == MetadataFieldTypes.ATOMIC:
            update_field_widget_attributes(self.fields["atomic_type"], {"class": "multiselect"})

        elif self.type == MetadataFieldTypes.ENUMERATION:
            proxy = MetadataStandardPropertyProxy.objects.get(pk=self.get_current_field_value("proxy"))
            all_enumeration_choices = proxy.enumerate_choices()
            self.fields["enumeration_choices"].set_choices(all_enumeration_choices)
            self.fields["enumeration_default"].set_choices(all_enumeration_choices)
#            self.fields["enumeration_choices"].widget = SelectMultiple(choices=all_enumeration_choices)
#            self.fields["enumeration_default"].widget = SelectMultiple(choices=all_enumeration_choices)
            # TODO: I CANNOT GET THE MULTISELECT PLUGIN TO WORK W/ THE RESTRICT_OPTIONS FN
            #update_field_widget_attributes(self.fields["enumeration_choices"],{"class":"multiselect","onchange":"restrict_options(this,['%s-enumeration_default']);"%(self.prefix)})
            update_field_widget_attributes(self.fields["enumeration_choices"], {"class": "multiselect"})
            update_field_widget_attributes(self.fields["enumeration_default"], {"class": "multiselect"})

        elif self.type == MetadataFieldTypes.RELATIONSHIP:
            update_field_widget_attributes(self.fields["relationship_show_subform"], {"class": "enabler", "onchange": "enable_customize_subform_button(this);"})
            if not property_customizer.pk:
                update_field_widget_attributes(self.fields["relationship_show_subform"], {"class": "readonly", "readonly": "readonly"})

        else:
            msg = "invalid field type for standard property: '%s'" % (self.type)
            raise QuestionnaireError(msg)

        update_field_widget_attributes(self.fields["name"], {"class": "label", "readonly": "readonly"})
        update_field_widget_attributes(self.fields["category_name"], {"class": "label", "readonly": "readonly"})
        update_field_widget_attributes(self.fields["order"], {"class": "label", "readonly": "readonly"})

        set_field_widget_attributes(self.fields["documentation"], {"cols": "60", "rows": "4" })
        set_field_widget_attributes(self.fields["suggestions"], {"cols": "60", "rows": "4" })
    
    def clean(self):
        cleaned_data = self.cleaned_data

        # the "category" field is a special case
        # it was working off of _unsaved_ models
        # so there is no pk associated w/ it
        # the form will, however, have stored the name in the "category_name" field
        # I will use that to find the appropriate category to map to in the view
        self.cleaned_data["category"] = None
        try:
            del self.errors["category"]
        except KeyError:
            pass

        return cleaned_data


def MetadataStandardPropertyCustomizerInlineFormSetFactory(*args,**kwargs):
    _prefix      = kwargs.pop("prefix","standard_property")
    _request     = kwargs.pop("request",None)
    _initial     = kwargs.pop("initial",[])
    _instance    = kwargs.pop("instance")
    _categories  = kwargs.pop("categories",[])
    _queryset    = kwargs.pop("queryset",MetadataStandardPropertyCustomizer.objects.none())
    new_kwargs = {
        "can_delete" : False,
        "extra"      : kwargs.pop("extra",0),
        "formset"    : MetadataPropertyCustomizerInlineFormSet,
        "form"       : MetadataStandardPropertyCustomizerForm,
        "fk_name"    : "model_customizer" # required in-case there are more than 1 fk's to "metadatamodelcustomizer"; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)

    # using curry() to pass arguments to the individual formsets
    # in this case, the set of choices for scientific categories
    _formset = inlineformset_factory(MetadataModelCustomizer,MetadataStandardPropertyCustomizer,*args,**new_kwargs)
    _formset.form = staticmethod(curry(MetadataStandardPropertyCustomizerForm,category_choices=_categories))
    if _initial:
        _formset.number_of_properties = len(_initial)
    elif _queryset:
        _formset.number_of_properties = len(_queryset)
    elif _request and _request.POST:
        _formset.number_of_properties = int(_request.POST[u"%s-TOTAL_FORMS"%(_prefix)])
    
    if _request and _request.method == "POST":
        return _formset(_request.POST,instance=_instance,prefix=_prefix)

    return _formset(queryset=_queryset,initial=_initial,instance=_instance,prefix=_prefix)


#########################
# scientific properties #
#########################


def create_scientific_property_customizer_form_data(model_customizer,scientific_property_customizer):

    scientific_property_customizer_form_data = get_initial_data(scientific_property_customizer,{
        "last_modified"     : time.strftime("%c"),
    })

    if scientific_property_customizer.is_enumeration:
        # enumeration fields
        current_enumeration_choices = scientific_property_customizer_form_data["enumeration_choices"]
        current_enumeration_default = scientific_property_customizer_form_data["enumeration_default"]
        if current_enumeration_choices:
            scientific_property_customizer_form_data["enumeration_choices"] = current_enumeration_choices.split("|")
        if current_enumeration_default:
            scientific_property_customizer_form_data["enumeration_default"] = current_enumeration_default.split("|")


    # BE AWARE THAT CHECKING THIS DICT ITEM (WHOSE VALUE AS A LIST) WON'T GIVE THE FULL LIST
    # APPARENTLY, THIS IS A "FEATURE" AND NOT A "BUG" [https://code.djangoproject.com/ticket/1130]

    else:
        # atomic fields...
        pass

    scientific_category = scientific_property_customizer.category
    if scientific_category:
        scientific_property_customizer_form_data["category"] = scientific_category.key
        scientific_property_customizer_form_data["category_name"] = scientific_category.name

    return scientific_property_customizer_form_data


class MetadataScientificPropertyCustomizerForm(MetadataCustomizerForm):

    class Meta:
        model = MetadataScientificPropertyCustomizer

        fields  = [
                # hidden fields...
                "field_type","proxy","is_enumeration","vocabulary_key","component_key","model_key",
                # header fields...
                "name","category_name","order",
                # common fields...
                "category","displayed", "required", "editable", "unique", "verbose_name", "default_value", "documentation","inline_help",
                # keyboard fields...
                "atomic_type","atomic_default",
                # enumeration fields... 
                "enumeration_choices","enumeration_default","enumeration_open","enumeration_multi","enumeration_nullable",
                # extra fields..
                "display_extra_standard_name","edit_extra_standard_name","extra_standard_name","display_extra_description","edit_extra_description","extra_description","display_extra_units","edit_extra_units","extra_units",
        ]


    category_name = CharField(label="Category",required=False)
    category      = ChoiceField(required=False) # changing from the default fk field (ModelChoiceField)
                                                # since I'm potentially dealing w/ _unsaved_ category_customizers

    _hidden_fields       = ("field_type","proxy","is_enumeration","vocabulary_key","component_key","model_key",)
    _header_fields       = ("name","category_name","order")
    _common_fields       = ("category","displayed","required","editable","unique","verbose_name","documentation","inline_help","suggestions")
    _keyboard_fields     = ("atomic_type","atomic_default")
    _enumeration_fields  = ("enumeration_choices","enumeration_default","enumeration_open","enumeration_multi","enumeration_nullable")

    _extra_fields        = ("display_extra_standard_name","edit_extra_standard_name","extra_standard_name","display_extra_description","edit_extra_description","extra_description","display_extra_units","edit_extra_units","extra_units")


    # set of fields that will be the same for all members of a formset; thus I can cache the query (mostly for relationship fields)
    cached_fields       = ["field_type"]

    def get_hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)

    def get_header_fields(self):
        return self.get_fields_from_list(self._header_fields)

    def get_keyboard_fields(self):
        fields = list(self)

        common_fields   = [field for field in fields if field.name in self._common_fields]
        keyboard_fields = [field for field in fields if field.name in self._keyboard_fields]

        all_fields = common_fields + keyboard_fields
        all_fields.sort(key=lambda field: fields.index(field))
        return all_fields

    def get_enumeration_fields(self):
        fields = list(self)

        common_fields      = [field for field in fields if field.name in self._common_fields]
        enumeration_fields = [field for field in fields if field.name in self._enumeration_fields]

        all_fields = common_fields + enumeration_fields
        all_fields.sort(key=lambda field: fields.index(field))
        return all_fields

    def get_fields(self):
        is_enumeration = self.get_current_field_value("is_enumeration",False)
        if is_enumeration:
            return self.get_enumeration_fields()
        else:
            return self.get_keyboard_fields()
        
    def get_extra_fields(self):
        return self.get_fields_from_list(self._extra_fields)

    def get_extra_fieldsets(self):
        fields = self.get_extra_fields()
        fieldsets = OrderedDict()
        fieldsets["Standard Name"]    = [field for field in fields if "standard_name" in field.name]
        fieldsets["Description"]      = [field for field in fields if "description" in field.name]
        fieldsets["Scientific Units"] = [field for field in fields if "units" in field.name]
        return fieldsets

    def __init__(self,*args,**kwargs):
        # category_choices was passed in via curry() in the factory function below
        category_choices = kwargs.pop("category_choices",[])

        super(MetadataScientificPropertyCustomizerForm,self).__init__(*args,**kwargs)


        property_customizer = self.instance
        is_enumeration = self.get_current_field_value("is_enumeration")

        update_field_widget_attributes(self.fields["category"],{"class":"multiselect","onchange":"copy_value(this,'%s-category_name');"%(self.prefix)})
        self.fields["category"].choices = EMPTY_CHOICE + [(category.key,category.name) for category in category_choices]
        if property_customizer.pk:
            # ordinarily, this is done in create_scientific_property_customizer_form_data above
            # but if this is an existing model, I still need to do this jiggery-pokery someplace
            self.initial["category"] = property_customizer.category.key
            if is_enumeration:
                current_enumeration_choices = self.get_current_field_value("enumeration_choices")
                current_enumeration_default = self.get_current_field_value("enumeration_default")
                if current_enumeration_choices:
                    self.initial["enumeration_choices"] = current_enumeration_choices.split("|")
                if current_enumeration_default:
                    self.initial["enumeration_default"] = current_enumeration_default.split("|")

        # this attribute ("type") is needed b/c I can access it in the customize template
        if not is_enumeration:
            self.type = MetadataFieldTypes.ATOMIC
            update_field_widget_attributes(self.fields["atomic_type"],{"class":"multiselect"})

        else:
            self.type = MetadataFieldTypes.ENUMERATION
            proxy = MetadataScientificPropertyProxy.objects.get(pk=self.get_current_field_value("proxy"))
            all_enumeration_choices = proxy.enumerate_choices()
            self.fields["enumeration_choices"].set_choices(all_enumeration_choices)
            self.fields["enumeration_default"].set_choices(all_enumeration_choices)
#            self.fields["enumeration_choices"].widget = SelectMultiple(choices=all_enumeration_choices)
#            self.fields["enumeration_default"].widget = SelectMultiple(choices=all_enumeration_choices)
            # TODO: I CANNOT GET THE MULTISELECT PLUGIN TO WORK W/ THE RESTRICT_OPTIONS FN
            #update_field_widget_attributes(self.fields["enumeration_choices"],{"class":"multiselect","onchange":"restrict_options(this,['%s-enumeration_default']);"%(self.prefix)})
            update_field_widget_attributes(self.fields["enumeration_choices"],{"class":"multiselect"})
            update_field_widget_attributes(self.fields["enumeration_default"],{"class":"multiselect"})

        update_field_widget_attributes(self.fields["name"],{"class":"label","readonly":"readonly"})
        update_field_widget_attributes(self.fields["category_name"],{"class":"label","readonly":"readonly"})
        update_field_widget_attributes(self.fields["order"],{"class":"label","readonly":"readonly"})

        set_field_widget_attributes(self.fields["documentation"],{"cols":"60","rows":"4"})
        set_field_widget_attributes(self.fields["extra_description"],{"rows":"4"})

    def clean(self):
        cleaned_data = self.cleaned_data

        # the "category" field is a special case
        # it was working off of _unsaved_ models
        # so there is no pk associated w/ it
        # the form will, however, have stored the name in the "category_name" field
        # I will use that to find the appropriate category to map to in the view
        try:
            self.cleaned_data["category"] = None
            del self.errors["category"]
        except KeyError:
            pass

        return cleaned_data

def MetadataScientificPropertyCustomizerInlineFormSetFactory(*args,**kwargs):
    _prefix      = kwargs.pop("prefix","scientific_property")
    _request     = kwargs.pop("request",None)
    _initial     = kwargs.pop("initial",[])
    _instance    = kwargs.pop("instance")
    _categories  = kwargs.pop("categories",[])
    _queryset    = kwargs.pop("queryset",MetadataScientificPropertyCustomizer.objects.none())
    new_kwargs = {
        "can_delete" : False,
        "extra"      : kwargs.pop("extra",0),
        "formset"    : MetadataPropertyCustomizerInlineFormSet,
        "form"       : MetadataScientificPropertyCustomizerForm,
        "fk_name"    : "model_customizer" # required in-case there are more than 1 fk's to "metadatamodelcustomizer"; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)

    # using curry() to pass arguments to the individual formsets
    _formset = inlineformset_factory(MetadataModelCustomizer,MetadataScientificPropertyCustomizer,*args,**new_kwargs)
    _formset.form = staticmethod(curry(MetadataScientificPropertyCustomizerForm,category_choices=_categories))

    if _initial:
        _formset.number_of_properties = len(_initial)
    elif _queryset:
        _formset.number_of_properties = len(_queryset)
    elif _request and _request.POST:
        _formset.number_of_properties = int(_request.POST[u"%s-TOTAL_FORMS"%(_prefix)])
   
    if _request and _request.method == "POST":
        return _formset(_request.POST,instance=_instance,prefix=_prefix)

    return _formset(queryset=_queryset,initial=_initial,instance=_instance,prefix=_prefix)


def create_new_customizer_forms_from_models(model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers,vocabularies_to_customize=MetadataScientificPropertyCustomizer.objects.none(),is_subform=False):

    model_customizer_data = create_model_customizer_form_data(model_customizer,standard_category_customizers,scientific_category_customizers,vocabularies=vocabularies_to_customize)
    model_customizer_form = MetadataModelCustomizerForm(initial=model_customizer_data,all_vocabularies=vocabularies_to_customize,is_subform=is_subform)

    standard_property_customizers_data = [create_standard_property_customizer_form_data(model_customizer,standard_property_customizer) for standard_property_customizer in standard_property_customizers]
    standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
        instance    = model_customizer,
        initial     = standard_property_customizers_data,
        extra       = len(standard_property_customizers_data),
        categories  = standard_category_customizers,
    )

    scientific_property_customizer_formsets = {}
    for vocabulary_key,scientific_property_customizer_dict in scientific_property_customizers.iteritems():
        scientific_property_customizer_formsets[vocabulary_key] = {}
        for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
            model_key = u"%s_%s" % (vocabulary_key,component_key)
            scientific_property_customizers_data = [
                create_scientific_property_customizer_form_data(model_customizer,scientific_property_customizer)
                for scientific_property_customizer in scientific_property_customizers[vocabulary_key][component_key]
            ]
            scientific_property_customizer_formsets[vocabulary_key][component_key] = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                instance    = model_customizer,
                initial     = scientific_property_customizers_data,
                extra       = len(scientific_property_customizers_data),
                prefix      = model_key,
                categories  = scientific_category_customizers[vocabulary_key][component_key]
            )

    return (model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets)

def create_existing_customizer_forms_from_models(model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers,vocabularies_to_customize=MetadataScientificPropertyCustomizer.objects.none(),is_subform=False):

    model_customizer_data = create_model_customizer_form_data(model_customizer,standard_category_customizers,scientific_category_customizers,vocabularies=vocabularies_to_customize)
    model_customizer_form = MetadataModelCustomizerForm(instance=model_customizer,initial=model_customizer_data,all_vocabularies=vocabularies_to_customize,is_subform=is_subform)

    standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
        instance    = model_customizer,
        queryset    = standard_property_customizers,
        # don't pass extra; w/ existing (queryset) models, extra ought to be 0
        #extra       = len(standard_property_customizers),
        categories  = standard_category_customizers,
    )

    scientific_property_customizer_formsets = {}
    for vocabulary_key,scientific_property_customizer_dict in scientific_property_customizers.iteritems():
        scientific_property_customizer_formsets[vocabulary_key] = {}
        for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
            scientific_property_customizer_formsets[vocabulary_key][component_key] = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                instance    = model_customizer,
                queryset    = scientific_property_customizer_list,
                # don't pass extra; w/ existing (queryset) models, extra ought to be 0
                #extra       = len(scientific_property_customizer_list),
                prefix      = u"%s_%s" % (vocabulary_key,component_key),
                categories  = scientific_category_customizers[vocabulary_key][component_key],
            )

    return (model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets)
