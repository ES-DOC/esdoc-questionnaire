
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
__date__ ="Apr 4, 2014 12:01:26 PM"

"""
.. module:: forms_edit

Summary of module goes here

"""

import time
from django.utils import timezone

from django.forms import *

from django.forms.models import BaseFormSet, BaseInlineFormSet, BaseModelFormSet
from django.forms.models import modelformset_factory, inlineformset_factory

from django.template.defaultfilters import slugify
from django.utils.functional        import curry

from questionnaire.utils        import *
from questionnaire.models       import *
from questionnaire.forms        import MetadataEditingForm
from questionnaire.fields       import MetadataFieldTypes, MetadataAtomicFieldTypes, METADATA_ATOMICFIELD_MAP, EMPTY_CHOICE, NULL_CHOICE, OTHER_CHOICE

def create_model_form_data(model,model_customizer):

    model_form_data = get_initial_data(model,{
        "last_modified" : time.strftime("%c"),
#        "parent"        : model.parent,
    })

    return model_form_data

class MetadataModelFormSet(BaseModelFormSet):

    number_of_models = 0        # lets me keep track of the number of forms w/out having to actually render them
    prefix_iterator  = None     # pass a list of form prefixes all at once to the formset (lets me associate forms w/ elements in the comopnent hierarchy)

    def _construct_form(self, i, **kwargs):

        if self.prefix_iterator:
            kwargs["prefix"] = next(self.prefix_iterator)

        form = super(MetadataModelFormSet,self)._construct_form(i,**kwargs)

        # this speeds up loading time
        # (see "cached_fields" attribute in the form class below)
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

class MetadataModelForm(MetadataEditingForm):

    class Meta:
        model   = MetadataModel
        fields  = [
            # hidden fields...
            "proxy", "project", "version", "is_document","is_root", "vocabulary_key", "component_key", "active", "name", "description", "order", 
            # header fields...
            "title",
        ]

    _hidden_fields       = ["proxy", "project", "version", "is_document", "vocabulary_key", "component_key", "active", "name", "description", "order", ]
    _header_fields       = ["title",]

    # set of fields that will be the same for all members of a formset; allows me to cache the query (for relationship fields)
    cached_fields       = []

    def get_hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)
    
    def get_header_fields(self):
        return self.get_fields_from_list(self._header_fields)
        
    def __init__(self,*args,**kwargs):
        # customizer was passed in via curry() in the factory function below
        customizer = kwargs.pop("customizer",None)

        super(MetadataModelForm,self).__init__(*args,**kwargs)

        update_field_widget_attributes(self.fields["title"],{"class":"label","readonly":"readonly","size":"50%"})
        
        if customizer:
            self.customize(customizer)

    def customize(self,customizer):

        # customization is done both in the form and in the template

        self.customizer = customizer
        
        # (but in the case of a modelform, it's _all_ done in the template)

        pass
        
def MetadataModelFormSetFactory(*args,**kwargs):
    _prefixes    = kwargs.pop("prefixes",[])
    _request     = kwargs.pop("request",None)
    _initial     = kwargs.pop("initial",[])
    _queryset    = kwargs.pop("queryset",MetadataModel.objects.none())
    _customizer  = kwargs.pop("customizer",None)
    new_kwargs = {
        "can_delete" : False,
        "extra"      : kwargs.pop("extra",0),
        "formset"    : MetadataModelFormSet,
        "form"       : MetadataModelForm,
    }
    new_kwargs.update(kwargs)

    # using curry() to pass arguments to the individual formsets
    _formset = modelformset_factory(MetadataModel,*args,**new_kwargs)
    _formset.form = staticmethod(curry(MetadataModelForm,customizer=_customizer))
    
    if _prefixes:
        _formset.prefix_iterator = iter(_prefixes)
    if _initial:
        _formset.number_of_models = len(_initial)
    elif _queryset:
        _formset.number_of_models = len(_queryset)
    else: # assuming data was passed in via POST
        _formset.number_of_models = int(_request.POST[u"form-TOTAL_FORMS"])

    if _request and _request.method == "POST":
        return _formset(_request.POST)
    else:
        # notice how both "queryset" and "initial" are passed
        # this handles both existing and new models
        # (in the case of existing models, "queryset" is used)
        # (in the case of new models, "initial" is used)
        # but both arguments are needed so that "extra" is used properly
        return _formset(initial=_initial,queryset=_queryset)

#######################
# standard properties #
#######################

def create_standard_property_form_data(model,standard_property,standard_property_customizer=None):

    standard_property_form_data = get_initial_data(standard_property,{
        "last_modified" : time.strftime("%c"),
        # no need to pass model, since this is handled by virtue of being an "inline" formset
    })

    if standard_property_customizer:

        field_type = standard_property_customizer.field_type

        if field_type == MetadataFieldTypes.ATOMIC:
            value_field_name = "atomic_value"

        elif field_type == MetadataFieldTypes.ENUMERATION:
            value_field_name = "enumeration_value"

        elif field_type == MetadataFieldTypes.RELATIONSHIP:
            value_field_name = "relationship_value"

        standard_property_form_data[value_field_name] = standard_property_customizer.default_value

    return standard_property_form_data

class MetadataStandardPropertyForm(MetadataEditingForm):

    class Meta:
        model   = MetadataStandardProperty
        fields = [
            # hidden fields...
            "proxy", "field_type", "name", "order", "model",
            # value fields...
            "atomic_value", "enumeration_value", "enumeration_other_value", "relationship_value",
        ]

    _hidden_fields      = ["proxy", "field_type", "name", "order", "model",]
    _value_fields       = ["atomic_value", "enumeration_value", "enumeration_other_value", "relationship_value",]

    # set of fields that will be the same for all members of a formset; allows me to cache the query (for relationship fields)
    cached_fields       = []

    def __init__(self,*args,**kwargs):
        
        # customizer was passed in via curry() in the factory function below
        customizer = kwargs.pop("customizer",None)

        super(MetadataStandardPropertyForm,self).__init__(*args,**kwargs)

        if customizer:
            self.customize(customizer)

    def get_hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)

    def get_value_field(self):
        value_field_name = self.get_value_field_name()
        value_fields = self.get_fields_from_list([value_field_name])
        try:
            return value_fields[0]
        except:
            return None

    def get_value_field_name(self):

        field_type = self.get_current_field_value("field_type")

        if field_type == MetadataFieldTypes.ATOMIC:
            return "atomic_value"
        elif field_type == MetadataFieldTypes.ENUMERATION:
            return "enumeration_value"
        elif field_type == MetadataFieldTypes.RELATIONSHIP:
            return  "relationship_value"
        else:
            msg = "unable to determine 'value' field for fieldtype '%s'" % (field_type)
            raise QuestionnaireError(msg)

    def customize(self,customizer):

        # customization is done both in the form (here) and in the template
        
        value_field_name = self.get_value_field_name()

        # the stuff that gets done specifically for atomic/enumeration/relationship fields can be hard-coded

        if customizer.field_type == MetadataFieldTypes.ATOMIC:
            atomic_type = customizer.atomic_type
            if atomic_type and atomic_type != MetadataAtomicFieldTypes.DEFAULT:
                custom_widget_class = METADATA_ATOMICFIELD_MAP[atomic_type][0]
                custom_widget_args  = METADATA_ATOMICFIELD_MAP[atomic_type][1]
                self.fields["atomic_value"].widget = custom_widget_class(**custom_widget_args)
                update_field_widget_attributes(self.fields["atomic_value"],{"class":atomic_type.lower()})

   
        elif customizer.field_type == MetadataFieldTypes.ENUMERATION:
            widget_attributes = { "class" : "multiselect"}
            choices = [(slugify(choice),choice) for choice in customizer.enumeration_choices.split('|')]
            if customizer.enumeration_nullable:
                choices += NULL_CHOICE
                widget_attributes["class"] += " nullable "
            if customizer.enumeration_open:
                choices += OTHER_CHOICE
                widget_attributes["class"] += " open "
            if customizer.enumeration_multi:
                self.fields["enumeration_value"].widget = SelectMultiple(choices=choices)
            else:
                self.fields["enumeration_value"].widget = Select(choices=EMPTY_CHOICE + choices)

            update_field_widget_attributes(self.fields["enumeration_value"],widget_attributes)
            update_field_widget_attributes(self.fields["enumeration_other_value"],{"class":"other"})

        # the other stuff is common to all and can be generic (ie: use 'value_field_name')

        self.fields[value_field_name].help_text = customizer.documentation

        if customizer.required:
            update_field_widget_attributes(self.fields[value_field_name],{"class":"required"})
        else:
            update_field_widget_attributes(self.fields[value_field_name],{"class":"optional"})

        if not customizer.editable:
            update_field_widget_attributes(self.fields[value_field_name],{"class":"readonly","readonly":"readonly"})

        if customizer.inherited:
            update_field_widget_attributes(self.fields[value_field_name],{"class":"inherited","onchange":"inherit(this);"})

        if customizer.suggestions:
            update_field_widget_attributes(self.fields[value_field_name],{"class":"autocomplete"})
            update_field_widget_attributes(self.fields[value_field_name],{"suggestions":customizer.suggestions})

        self.customizer = customizer

class MetadataStandardPropertyInlineFormSet(BaseInlineFormSet):

    number_of_properties = 0       # lets me keep track of the number of forms w/out having to actually render them

    def _construct_form(self, i,**kwargs):

        if self.customizers:
            try:
                kwargs["customizer"] = next(self.customizers)
            except StopIteration:
                # don't worry about not having a customizer for the extra form
                pass

        form = super(MetadataStandardPropertyInlineFormSet,self)._construct_form(i,**kwargs)

        # this speeds up loading time
        # (see "cached_fields" attribute in the form class above)
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

def MetadataStandardPropertyInlineFormSetFactory(*args,**kwargs):
    DEFAULT_PREFIX = "_standard_properties"

    _prefix      = kwargs.pop("prefix","")+DEFAULT_PREFIX
    _request     = kwargs.pop("request",None)
    _initial     = kwargs.pop("initial",[])
    _queryset    = kwargs.pop("queryset",MetadataStandardProperty.objects.none())
    _instance    = kwargs.pop("instance")
    _customizers = kwargs.pop("customizers",None)
    new_kwargs = {
        "can_delete" : False,
        "extra"      : kwargs.pop("extra",0),
        "formset"    : MetadataStandardPropertyInlineFormSet,
        "form"       : MetadataStandardPropertyForm,
        "fk_name"    : "model" # required in-case there are more than 1 fk's to "metadatamodel"; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)

    _formset = inlineformset_factory(MetadataModel,MetadataStandardProperty,*args,**new_kwargs)
    if _customizers:
        _formset.customizers = iter(_customizers)
    if _initial:
        _formset.number_of_properties = len(_initial)
    elif _queryset:
        _formset.number_of_properties = len(_queryset)
    else: # assuming data was passed in via POST
        _formset.number_of_properties = int(_request.POST[u"%s-TOTAL_FORMS"%(_prefix)])




    if _request and _request.method == "POST":
        return _formset(_request.POST,instance=_instance,prefix=_prefix)
    else:
        # notice how both "queryset" and "initial" are passed
        # this handles both existing and new models
        # (in the case of existing models, "queryset" is used)
        # (in the case of new models, "initial" is used)
        # but both arguments are needed so that "extra" is used properly
        return _formset(initial=_initial,queryset=_queryset,instance=_instance,prefix=_prefix)


#########################
# scientific properties #
#########################

def create_scientific_property_form_data(model,scientific_property,scientific_property_customizer=None):


    if scientific_property_customizer:
        if model.get_model_key() ==  "atmos_atmosdynamicalcore":
            if scientific_property.category_key != scientific_property_customizer.category.key:
                import ipdb; ipdb.set_trace()

        #assert(scientific_property.category_key == scientific_property_customizer.category.key)

    scientific_property_form_data = get_initial_data(scientific_property,{
        "last_modified" : time.strftime("%c"),
        # no need to pass model, since this is handled by virtue of being an "inline" formset
    })

    if scientific_property_customizer:

        pass

    return scientific_property_form_data

class MetadataScientificPropertyForm(MetadataEditingForm):

    class Meta:
        model   = MetadataScientificProperty

    # since I am only explicitly displaying the "value_field" I have to be sure to add any fields
    # that the django form init/saving process depends upon to this list
    _hidden_fields       = ["proxy", "field_type", "is_enumeration", "category_key", "name", "order",]

    # list of fields that will be the same for all members of a formset; thus I can cache the query
    cached_fields       = []


    def __init__(self,*args,**kwargs):

        # customizer was passed in via curry() in the factory function below
        customizer = kwargs.pop("customizer",None)

        super(MetadataScientificPropertyForm,self).__init__(*args,**kwargs)

        update_field_widget_attributes(self.fields["enumeration_value"],{"class":"multiselect"})
        update_field_widget_attributes(self.fields["atomic_value"],{"onchange":"copy_value(this,'%s-scientific_property_value');"%(self.prefix)})

        if customizer:
            self.customize(customizer)


    def customize(self,customizer):
      
        # customization is done in the form and in the template

        value_field_name = self.get_value_field_name()

        self.fields[value_field_name].help_text = customizer.documentation

        if not customizer.is_enumeration:
            atomic_type = customizer.atomic_type
            if atomic_type and atomic_type != MetadataAtomicFieldTypes.DEFAULT:
                custom_widget_class = METADATA_ATOMICFIELD_MAP[atomic_type][0]
                custom_widget_args  = METADATA_ATOMICFIELD_MAP[atomic_type][1]
                self.fields["atomic_value"].widget = custom_widget_class(**custom_widget_args)
                update_field_widget_attributes(self.fields["atomic_value"],{"class":atomic_type.lower()})

        else:
            widget_attributes = { "class" : "multiselect"}
            choices = [(slugify(choice),choice) for choice in customizer.enumeration_choices.split('|')]
            if customizer.enumeration_nullable:
                choices += NULL_CHOICE
                widget_attributes["class"] += " nullable "
            if customizer.enumeration_open:
                choices += OTHER_CHOICE
                widget_attributes["class"] += " open "
            if customizer.enumeration_multi:
                self.fields["enumeration_value"].widget = SelectMultiple(choices=choices)
            else:
                self.fields["enumeration_value"].widget = Select(choices=EMPTY_CHOICE + choices)

            update_field_widget_attributes(self.fields["enumeration_value"],widget_attributes)
            update_field_widget_attributes(self.fields["enumeration_other_value"],{"class":"other"})

        # extra_attributes...
        if not customizer.edit_extra_standard_name:
            update_field_widget_attributes(self.fields["extra_standard_name"],{"class":"readonly","readonly":"readonly"})

        if not customizer.edit_extra_description:
            update_field_widget_attributes(self.fields["extra_description"],{"class":"readonly","readonly":"readonly"})

        if not customizer.edit_extra_units:
            update_field_widget_attributes(self.fields["extra_units"],{"class":"readonly","readonly":"readonly"})

        set_field_widget_attributes(self.fields["extra_description"],{"cols":"60","rows":"4"})

        self.customizer = customizer

    def get_hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)


    def get_value_field(self):
        value_field_name = self.get_value_field_name()
        value_fields = self.get_fields_from_list([value_field_name])
        try:
            return value_fields[0]
        except:
            return None


    def get_value_field_name(self):

        is_enumeration = self.get_current_field_value("is_enumeration",False) # TODO: PREVIOUSLY IF "is_enumeration" WAS NOT FOUND I RETURNED FALSE

        if not is_enumeration:
            return "atomic_value"
        else:
            return "enumeration_value"


class MetadataScientificPropertyInlineFormSet(BaseInlineFormSet):

    number_of_properties = 0

    # also using it to cache fk or m2m fields to avoid needless (on the order of 30K!) db hits

    def _construct_form(self, i, **kwargs):
        
        if self.customizers:
            try:
                kwargs["customizer"] = next(self.customizers)
            except StopIteration:
                # don't worry about not having a customizer for the extra form
                pass

        form = super(MetadataScientificPropertyInlineFormSet,self)._construct_form(i,**kwargs)

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

def MetadataScientificPropertyInlineFormSetFactory(*args,**kwargs):
    DEFAULT_PREFIX = "_scientific_properties"

    _prefix      = kwargs.pop("prefix","")+DEFAULT_PREFIX
    _request     = kwargs.pop("request",None)
    _initial     = kwargs.pop("initial",[])
    _queryset    = kwargs.pop("queryset",MetadataScientificProperty.objects.none())
    _instance    = kwargs.pop("instance")
    _customizers = kwargs.pop("customizers",None)
    new_kwargs = {
        "can_delete" : False,
        "extra"      : kwargs.pop("extra",0),
        "formset"    : MetadataScientificPropertyInlineFormSet,
        "form"       : MetadataScientificPropertyForm,
        "fk_name"    : "model" # required in-case there are more than 1 fk's to "metadatamodel"; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)

    if _prefix ==  "atmos_atmosdynamicalcore"+DEFAULT_PREFIX:
        import ipdb; ipdb.set_trace()

    assert(len(_initial)==new_kwargs["extra"])

    _formset = inlineformset_factory(MetadataModel,MetadataScientificProperty,*args,**new_kwargs)
    if _customizers:
        _formset.customizers = iter(_customizers)


    if _initial:
        _formset.number_of_properties = len(_initial)
    elif _queryset:
        _formset.number_of_properties = len(_queryset)

    if _request and _request.method == "POST":
        return _formset(_request.POST,instance=_instance,prefix=_prefix)
    else:
        # notice how both "queryset" and "initial" are passed
        # this handles both existing and new models
        # (in the case of existing models, "queryset" is used)
        # (in the case of new models, "initial" is used)
        # but both arguments are needed so that "extra" is used properly
        return _formset(initial=_initial,queryset=_queryset,instance=_instance,prefix=_prefix)
