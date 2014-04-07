
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

from django.forms import *

from django.forms.models import BaseFormSet, BaseInlineFormSet
from django.forms.models import modelformset_factory, inlineformset_factory

from django.template.defaultfilters import slugify
from django.utils.functional        import curry

from questionnaire.utils        import *
from questionnaire.models       import *
from questionnaire.forms        import MetadataForm

class MetadataModelFormSet(BaseFormSet):

    number_of_models = 0                    # lets me keep track of the number of forms w/out having to render them
    custom_prefix_iterator = None           # pass a list of form prefixes all at once to the formset (lets me associate forms w/ elements in the comopnent hierarchy)

    def _construct_form(self, i, **kwargs):

        if self.custom_prefix_iterator:
            kwargs["prefix"] = next(self.custom_prefix_iterator)

        form = super(MetadataModelFormSet,self)._construct_form(i,**kwargs)
        
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

class MetadataModelForm(MetadataForm):

    class Meta:
        model   = MetadataModel
        fields  = [
            # hidden fields...
            "proxy", "project", "version", "is_document", "vocabulary_key", "component_key", "active", "name", "description", "order",
            # header fields...
            "title",
        ]

    hidden_fields       = ["proxy", "project", "version", "is_document", "vocabulary_key", "component_key", "active", "name", "description", "order",]
    header_fields       = ["title",]

    # set of fields that will be the same for all members of a formset; thus I can cache the query (for relationship fields)
    cached_fields       = []

    def get_hidden_fields(self):
        return self.get_fields_from_list(self.hidden_fields)
    
    def get_header_fields(self):
        return self.get_fields_from_list(self.header_fields)
        
    def __init__(self,*args,**kwargs):
        # customizer was passed in via curry() in the factory function below
        customizer = kwargs.pop("customizer",None)

        super(MetadataModelForm,self).__init__(*args,**kwargs)

        model = self.instance

        # when initializing formsets,
        # the fields aren't always setup in the underlying model
        # so this gets them either from the request (in the case of POST) or initial (in the case of GET)
        if self.data:
            # POST; (form already had data) request was passed into constructor
            # (not sure why I can't do this in a list comprehension)
            for key,value in self.data.iteritems():
                if key.startswith(self.prefix+"-"):
                    self.current_values[key.split(self.prefix+"-")[1]] = value
        else:
            # GET; initial was passed into constructor
            self.current_values = self.initial
    
        update_field_widget_attributes(self.fields["title"],{"class":"label","readonly":"readonly","size":"50%"})
        
        if customizer:
            self.customize(customizer)

    def customize(self,customizer):
        # customization is done in the form and in the template

        self.customizer = customizer
        
        # (in the case of a modelform, it's _all_ done in the template)
        pass

        
def MetadataModelFormSetFactory(*args,**kwargs):
    _prefixes    = kwargs.pop("prefixes",[])
    _request     = kwargs.pop("request",None)
    _initial     = kwargs.pop("initial",[])
    _queryset    = kwargs.pop("queryset",None)
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
        _formset.custom_prefix_iterator = iter(_prefixes)
    if _initial:
        _formset.number_of_properties = len(_initial)
    elif _queryset:
        _formset.number_of_properties = len(_queryset)

    if _request and _request.method == "POST":
        return _formset(_request.POST)
    else:
        return _formset(initial=_initial)


class MetadataStandardPropertyForm(MetadataForm):

    class Meta:
        model   = MetadataStandardProperty
#        fields  = [
#            # hidden fields...
#            "proxy", "project", "version", "is_document", "vocabulary_key", "component_key", "active", "name", "description", "order",
#            # header fields...
#            "title",
#        ]
#
#    hidden_fields       = ["proxy", "project", "version", "is_document", "vocabulary_key", "component_key", "active", "name", "description", "order",]
#    header_fields       = ["title",]

    # set of fields that will be the same for all members of a formset; thus I can cache the query (for relationship fields)
    cached_fields       = []

    def get_hidden_fields(self):
        return self.get_fields_from_list(self.hidden_fields)

    def get_header_fields(self):
        return self.get_fields_from_list(self.header_fields)

    def __init__(self,*args,**kwargs):

        # customizer was passed in via curry() in the factory function below
        customizer = kwargs.pop("customizer",None)

        super(MetadataStandardPropertyForm,self).__init__(*args,**kwargs)

        model = self.instance

        # when initializing formsets,
        # the fields aren't always setup in the underlying model
        # so this gets them either from the request (in the case of POST) or initial (in the case of GET)
        if self.data:
            # POST; (form already had data) request was passed into constructor
            # (not sure why I can't do this in a list comprehension)
            for key,value in self.data.iteritems():
                if key.startswith(self.prefix+"-"):
                    self.current_values[key.split(self.prefix+"-")[1]] = value
        else:
            # GET; initial was passed into constructor
            self.current_values = self.initial

        if customizer:
            self.customize(customizer)

    def customize(self,customizer):
        # customization is done in the form and in the template

        self.customizer = customizer

        # TODO
        pass

class MetadataStandardPropertyInlineFormSet(BaseInlineFormSet):

    number_of_properties = 0

    # also using it to cache fk or m2m fields to avoid needless (on the order of 30K!) db hits

    def _construct_form(self, i, **kwargs):
        form = super(MetadataStandardPropertyInlineFormSet,self)._construct_form(i,**kwargs)

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
    _prefix      = kwargs.pop("prefix","standard_property")
    _request     = kwargs.pop("request",None)
    _initial     = kwargs.pop("initial",[])
    _queryset    = kwargs.pop("queryset",None)
    _instance    = kwargs.pop("instance")
    _customizer  = kwargs.pop("customizer",None)
    new_kwargs = {
        "can_delete" : False,
        "extra"      : kwargs.pop("extra",0),
        "formset"    : MetadataStandardPropertyInlineFormSet,
        "form"       : MetadataStandardPropertyForm,
        "fk_name"    : "model" # required in-case there are more than 1 fk's to "metadatamodel"; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)

    # using curry() to pass arguments to the individual formsets
    _formset = inlineformset_factory(MetadataModel,MetadataStandardProperty,*args,**new_kwargs)
    if _initial:
        _formset.number_of_properties = len(_initial)
    elif _queryset:
        _formset.number_of_properties = len(_queryset)

    if _request and _request.method == "POST":
        return _formset(_request.POST,instance=_instance,prefix=_prefix)

    return _formset(queryset=_queryset,initial=_initial,instance=_instance,prefix=_prefix)

    # using curry() to pass arguments to the individual formsets
    _formset = modelformset_factory(MetadataModel,*args,**new_kwargs)
    _formset.form = staticmethod(curry(MetadataModelForm,customizer=_customizer))

    if _request and _request.method == "POST":
        return _formset(_request.POST)
    else:
        return _formset(initial=_initial)
