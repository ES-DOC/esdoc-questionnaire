
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
from CIM_Questionnaire.questionnaire.models import MetadataStandardPropertyProxy, MetadataModel, MetadataCustomizer, MetadataVocabulary

__author__="allyn.treshansky"
__date__ ="Apr 4, 2014 12:01:26 PM"

"""
.. module:: forms_edit

Summary of module goes here

"""

import time

from django.utils import timezone

from django.forms import *

from django.forms.models import BaseModelFormSet, BaseInlineFormSet
from django.forms.models import modelformset_factory, inlineformset_factory

from django.utils.functional import curry

from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel, MetadataStandardProperty, MetadataScientificProperty
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy, MetadataStandardPropertyProxy, MetadataScientificPropertyProxy
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary

from CIM_Questionnaire.questionnaire.forms import MetadataEditingForm

from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes, MetadataAtomicFieldTypes, CachedModelChoiceField, METADATA_ATOMICFIELD_MAP, EMPTY_CHOICE, NULL_CHOICE, OTHER_CHOICE

from CIM_Questionnaire.questionnaire.utils import QuestionnaireError, find_in_sequence, update_field_widget_attributes
from CIM_Questionnaire.questionnaire.utils import get_initial_data, find_in_sequence, update_field_widget_attributes, set_field_widget_attributes, get_data_from_formset, get_data_from_form
from CIM_Questionnaire.questionnaire.utils import LIL_STRING, SMALL_STRING, BIG_STRING, HUGE_STRING

from CIM_Questionnaire.questionnaire.utils import model_to_data

def create_model_form_data(model,model_customizer):

    model_form_data = model_to_data(
        model,
        exclude = [ "tree_id", "lft", "rght", "level", "parent", ], # ignore mptt fields
        include = {
            "last_modified" : time.strftime("%c"),
        }
    )
    # model_form_data = get_initial_data(model,{
    #     "last_modified" : time.strftime("%c"),
    #     #"parent" : model.parent,
    # })

    return model_form_data

class MetadataModelFormSet(BaseModelFormSet):

    # these are instance-level variables that should be set in the factory functions below
    #number_of_models = 0        # lets me keep track of the number of forms w/out having to actually render them
    #prefix_iterator  = None     # pass a list of form prefixes all at once to the formset (lets me associate forms w/ elements in the comopnent hierarchy)

    def _construct_form(self, i, **kwargs):

        print 'calling construct form'
        if self.prefix_iterator:
            form_prefix = next(self.prefix_iterator)
            kwargs["prefix"] = form_prefix

        # this section rewrites the original fn from BaseModelFormSet b/c I am using a separate prefix for each form
        # (see django.forms.models.BaseModelFormSet._construct_form
        if self.is_bound and i < self.initial_form_count():
            # Import goes here instead of module-level because importing
            # django.db has side effects
            from django.db import connections
            pk_key = "%s-%s" % (form_prefix, self.model._meta.pk.name)    # THIS IS THE DIFFERENT BIT!
            pk = self.data[pk_key]
            pk_field = self.model._meta.pk
            pk = pk_field.get_db_prep_lookup('exact', pk,
                connection=connections[self.get_queryset().db])
            if isinstance(pk, list):
                pk = pk[0]
            kwargs['instance'] = self._existing_object(pk)
        if i < self.initial_form_count() and not kwargs.get('instance'):
            kwargs['instance'] = self.get_queryset()[i]
        if i >= self.initial_form_count() and self.initial_extra:
            # Set initial values for extra forms
            try:
                kwargs['initial'] = self.initial_extra[i-self.initial_form_count()]
            except IndexError:
                pass
        form = super(BaseModelFormSet, self)._construct_form(i, **kwargs)
        # end section

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

class MetadataModelSubFormSet(BaseModelFormSet):

    # these are instance-level variables that should be set in the factory functions below
    #number_of_models = 0        # lets me keep track of the number of forms w/out having to actually render them
    #min = 0
    #max = 1

    def _construct_form(self, i, **kwargs):

        # when these forms are being constructed via AJAX for adding new subforms
        # I need to increment the prefix of individual forms to take into account any existing forms
        if self.increment_prefix > 0:

            form_prefix = self.add_prefix(i+self.increment_prefix)
            kwargs["prefix"] = form_prefix

            # this section rewrites the original fn from BaseModelFormSet b/c I am using a separate prefix for each form
            # (see django.forms.models.BaseModelFormSet._construct_form
            if self.is_bound and i < self.initial_form_count():
                # Import goes here instead of module-level because importing
                # django.db has side effects
                from django.db import connections
                pk_key = "%s-%s" % (form_prefix, self.model._meta.pk.name)    # THIS IS THE DIFFERENT BIT!
                pk = self.data[pk_key]
                pk_field = self.model._meta.pk
                pk = pk_field.get_db_prep_lookup('exact', pk,
                    connection=connections[self.get_queryset().db])
                if isinstance(pk, list):
                    pk = pk[0]
                kwargs['instance'] = self._existing_object(pk)
            if i < self.initial_form_count() and not kwargs.get('instance'):
                kwargs['instance'] = self.get_queryset()[i]
            if i >= self.initial_form_count() and self.initial_extra:
                # Set initial values for extra forms
                try:
                    kwargs['initial'] = self.initial_extra[i-self.initial_form_count()]
                except IndexError:
                    pass
            # end section

        form = super(MetadataModelSubFormSet, self)._construct_form(i, **kwargs)

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

    def get_min(self):
        # not using the built-in min_num attribute
        # b/c that's not available until Django 1.7+
        return self.min

    def get_max(self):
        # not using the built-in max_num attribute
        # b/c that uses None instead of "*"
        return self.max


class MetadataModelAbstractForm(MetadataEditingForm):
    class Meta:
        abstract = True

    def __init__(self,*args,**kwargs):
        # customizer was passed in via curry() in the factory function below
        customizer = kwargs.pop("customizer",None)

        super(MetadataModelAbstractForm,self).__init__(*args,**kwargs)

        if customizer:
            self.customize(customizer)

    def get_hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)

    def get_header_fields(self):
        return self.get_fields_from_list(self._header_fields)

    def customize(self,customizer):

        # customization is done both in the form and in the template

        self.customizer = customizer

        # (but in the case of this class, MetadataModelForm, it's _all_ done in the template)

        pass


class MetadataModelForm(MetadataModelAbstractForm):

    class Meta:
        model   = MetadataModel
        fields  = [
            # hidden fields...
            "proxy", "project", "version", "is_document","is_root", "vocabulary_key", "component_key", "active", "name", "description", "order", 
            # header fields...
            "title",
        ]

    # set of fields that will be the same for all members of a formset; allows me to cache the query (for relationship fields)
    cached_fields = []

    _header_fields = ["title",]
    _hidden_fields = ["proxy", "project", "version", "is_document", "is_root", "vocabulary_key", "component_key", "active", "name", "description", "order", ]

    def has_changed(self):
        return True


    def __init__(self,*args,**kwargs):

        print "calling init"
        super(MetadataModelForm,self).__init__(*args,**kwargs)

        set_field_widget_attributes(self.fields["title"],{"size":64})

class MetadataModelSubForm(MetadataModelAbstractForm):

    class Meta:
        model   = MetadataModel
        fields  = [
            # hidden fields...
            "proxy", "project", "version", "is_document","is_root", "vocabulary_key", "component_key", "active", "name", "description", "order",
            # header fields...
            "title",
        ]

    # set of fields that will be the same for all members of a formset; allows me to cache the query (for relationship fields)
    cached_fields = []

    _header_fields = ["title",]
    _hidden_fields = ["proxy", "project", "version", "is_document", "is_root", "vocabulary_key", "component_key", "active", "name", "description", "order", ]

    def __init__(self,*args,**kwargs):
        super(MetadataModelSubForm,self).__init__(*args,**kwargs)

        # this is really really important!
        # this ensures that there is something to compare field data against so that I can truly tell is the model has changed
        # [http://stackoverflow.com/questions/11710845/in-django-1-4-do-form-has-changed-and-form-changed-data-which-are-undocument]
# actually, just check if the standard_properties have changed...
# (see has_changed() below)
#        for field_name in self._meta.fields:
#            if field_name not in self._hidden_fields:
#                self.fields[field_name].show_hidden_initial = True

    def has_changed(self):
        # so I explicitly do not check the validity of modelsubforms (instead relying on propertysubforms)
        # see save_valid_forms() below
        return True


def MetadataModelFormSetFactory(*args,**kwargs):
    DEFAULT_PREFIX = "form"

    _prefixes    = kwargs.pop("prefixes",[])
    _data        = kwargs.pop("data",None)
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
    formset_prefix = DEFAULT_PREFIX

    if _prefixes:
        _formset.prefix_iterator = iter(_prefixes)

    if _initial:
        _formset.number_of_models = len(_initial)
    elif _queryset:
        _formset.number_of_models = len(_queryset)
    elif _data:
        _formset.number_of_models = int(_data[u"%s-TOTAL_FORMS"%(formset_prefix)])
    else:
        _formset.number_of_models = 0

    if _data:
        return _formset(_data, prefix=formset_prefix)

    # notice how both "queryset" and "initial" are passed
    # this handles both existing and new models
    # (in the case of existing models, "queryset" is used)
    # (in the case of new models, "initial" is used)
    # but both arguments are needed so that "extra" is used properly
    return _formset(queryset=_queryset, initial=_initial, prefix=formset_prefix)

def MetadataModelSubFormSetFactory(*args,**kwargs):
    DEFAULT_PREFIX = "_subform"

    _prefix       = kwargs.pop("prefix","")+DEFAULT_PREFIX
    _data         = kwargs.pop("data",None)
    _initial      = kwargs.pop("initial",[])
    _queryset     = kwargs.pop("queryset",MetadataModel.objects.none())
    _customizer   = kwargs.pop("customizer",None)
    _min          = kwargs.pop("min",0)
    _max          = kwargs.pop("max",1)
    _increment_prefix = kwargs.pop("increment_prefix",0)
    new_kwargs = {
        "can_delete"   : True,
        "extra"        : kwargs.pop("extra",0),
        "formset"      : MetadataModelSubFormSet,
        "form"         : MetadataModelSubForm,
        # TODO: "min_num", and "validate_min" IS ONLY VALID FOR DJANGO 1.7+
        # (that's why I explicitly add it below)
        # "min_num"      : _min,
        #"validate_min" : True,
        "max_num"      : None if _max == u"*" else _max,   # (a value of None implies no limit)
        "validate_max" : True,
    }
    new_kwargs.update(kwargs)

    # using curry() to pass arguments to the individual formsets
    _formset = modelformset_factory(MetadataModel,*args,**new_kwargs)
    _formset.form = staticmethod(curry(MetadataModelSubForm,customizer=_customizer))
    _formset.min = _min
    _formset.max = _max
    _formset.increment_prefix = _increment_prefix

    if _initial:
        _formset.number_of_models = len(_initial)
    elif _queryset:
        _formset.number_of_models = len(_queryset)
    elif _data:
        _formset.number_of_models = int(_data[u"%s-TOTAL_FORMS"%(_prefix)])
    else:
        _formset.number_of_models = 0

    if _data:
        return _formset(_data, prefix=_prefix)

    # notice how both "queryset" and "initial" are passed
    # this handles both existing and new models
    # (in the case of existing models, "queryset" is used)
    # (in the case of new models, "initial" is used)
    # but both arguments are needed so that "extra" is used properly
    return _formset(queryset=_queryset, initial=_initial, prefix=_prefix)

#######################
# standard properties #
#######################


def create_standard_property_form_data(model,standard_property,standard_property_customizer=None):


    standard_property_form_data = model_to_data(
        standard_property,
        exclude = [ "model" ],
        include = {
            "last_modified" : time.strftime("%c"),
        }
    )
    # standard_property_form_data = get_initial_data(standard_property,{
    #     "last_modified" : time.strftime("%c"),
    #     # no need to pass model, since this is handled by virtue of being an "inline" formset
    # })

    if standard_property_customizer:

        field_type = standard_property_form_data["field_type"]

        if field_type == MetadataFieldTypes.ATOMIC:
            value_field_name = "atomic_value"
            pass

        elif field_type == MetadataFieldTypes.ENUMERATION:
            value_field_name = "enumeration_value"
            current_enumeration_value = standard_property_form_data[value_field_name]
            if current_enumeration_value:
                if standard_property_customizer.enumeration_multi:
                    standard_property_form_data[value_field_name] = current_enumeration_value.split("|")

        elif field_type == MetadataFieldTypes.RELATIONSHIP:
            value_field_name = "relationship_value"
            pass

        else:
            msg = "invalid field type for standard property: %s" % (field_type)
            raise QuestionnaireError(msg)

        standard_property_form_data[value_field_name] = standard_property_customizer.default_value

        # further customization is done in the customize() fn below

    return standard_property_form_data


class MetadataAbstractStandardPropertyForm(MetadataEditingForm):
    class Meta:
        abstract = True

    cached_fields       = []
    _value_fields       = ["atomic_value", "enumeration_value", "enumeration_other_value", "relationship_value",]
    _hidden_fields      = ["proxy", "field_type", "name", "order", "is_label"]

    # TODO: FILTER THESE BY PROJECT & VERSION?
    proxy = CachedModelChoiceField(queryset=MetadataStandardPropertyProxy.objects.all())

    def __init__(self,*args,**kwargs):

        # customizers was passed in via curry in the factory function below
        customizers = kwargs.pop("customizers",None)

        super(MetadataAbstractStandardPropertyForm,self).__init__(*args,**kwargs)

        # this is really really important!
        # this ensures that there is something to compare field data against so that I can truly tell is the model has changed
        # [http://stackoverflow.com/questions/11710845/in-django-1-4-do-form-has-changed-and-form-changed-data-which-are-undocument]
        #for field_name in self._meta.fields:
        # actually, let's assume that the properties have always changed
        # and override the has_changed() class on model sub forms
        #    try:
        #        self.fields[field_name].show_hidden_initial = True
        #    except KeyError:
        #        # inline formsets treat pk fields strangely, just ignore them in this context
        #        pass

        proxy_pk = int(self.get_current_field_value("proxy"))
        field_type = self.get_current_field_value("field_type")

        if customizers:
            customizer = find_in_sequence(lambda c: c.proxy.pk == proxy_pk , customizers)
            assert(customizer.name==self.get_current_field_value("name"))   # this is new code; just make sure it works
        else:
            customizer = None

        property = self.instance
        if property.pk:
            # ordinarily, this is done in create_scientific_property_form_data above
            # but if this is an existing model, I still need to do this jiggery-pokery someplace
            if field_type == MetadataFieldTypes.ENUMERATION:
                current_enumeration_value = self.get_current_field_value("enumeration_value")
                if isinstance(current_enumeration_value,basestring) and customizer.enumeration_multi:
                    self.initial["enumeration_value"] = current_enumeration_value.split("|")

        if field_type == MetadataFieldTypes.ATOMIC:
            pass

        elif field_type == MetadataFieldTypes.ENUMERATION:
            update_field_widget_attributes(self.fields["enumeration_value"],{"class":"multiselect"})
            update_field_widget_attributes(self.fields["enumeration_other_value"],{"class":"other"})

        elif field_type == MetadataFieldTypes.RELATIONSHIP:
            # TODO: FILTER BY PROJECT AS WELL
            proxy = MetadataStandardPropertyProxy.objects.select_related("relationship_target_model").get(pk=proxy_pk)
            self.fields["relationship_value"].queryset = MetadataModel.objects.filter(proxy=proxy.relationship_target_model)
            self.subform_tuple = (None,)    # I should only ever access this once it's been setup in customize()
                                            # hence the assert statements in get_subform_tuple()

        else:
            msg = "invalid field type for standard property: '%s'." % (field_type)
            raise QuestionnaireError(msg)

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

        property = self.instance

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
            custom_widget_attributes = { "class" : "multiselect"}
            all_enumeration_choices = customizer.enumerate_choices()
            if customizer.enumeration_nullable:
                all_enumeration_choices += NULL_CHOICE
                custom_widget_attributes["class"] += " nullable"
            if customizer.enumeration_open:
                all_enumeration_choices += OTHER_CHOICE
                custom_widget_attributes["class"] += " open"
            if customizer.enumeration_multi:
                self.fields["enumeration_value"].set_choices(all_enumeration_choices,multi=True)
            else:
                all_enumeration_choices = EMPTY_CHOICE + all_enumeration_choices
                self.fields["enumeration_value"].set_choices(all_enumeration_choices,multi=False)
            update_field_widget_attributes(self.fields["enumeration_value"],custom_widget_attributes)

        elif customizer.field_type == MetadataFieldTypes.RELATIONSHIP:
            if customizer.relationship_show_subform:
                subform_customizer = customizer.subform_customizer

                (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
                    MetadataCustomizer.get_existing_customizer_set(subform_customizer, MetadataVocabulary.objects.none())
                standard_property_proxies = [standard_property_customizer.proxy for standard_property_customizer in standard_property_customizers]
                scientific_property_proxies = {}
                scientific_property_customizers = {}
                for vocabulary_key,scientific_property_customizer_dict in nested_scientific_property_customizers.iteritems():
                    for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
                        model_key = u"%s_%s" % (vocabulary_key, component_key)
                        # I have to restructure this; in the customizer views it makes sense to store these as a dictionary of dictionaries
                        # but here, they should only be one level deep (hence the use of "nested_" above)
                        scientific_property_customizers[model_key] = scientific_property_customizer_list
                        scientific_property_proxies[model_key] = [scientific_property_customizer.proxy for scientific_property_customizer in scientific_property_customizer_list]

                # determine if the subforms ought to be a 1-to-1 (ie: a subformset w/ 1 item) or a m-to-m (ie: a subformset w/ multiple items)
                # even though the underlying model uses a m-to-m field, this restricts how many items users can add
                render_as_formset = customizer.render_as_formset()
                subform_min, subform_max = [int(val) if val != "*" else val for val in customizer.relationship_cardinality.split("|")]

                if property.pk:

                    models = property.relationship_value.all()
                    if models:
                        (models, standard_properties, scientific_properties) = \
                            MetadataModel.get_existing_realization_set(models, model_customizer, is_subrealization=True)

                        if not self.is_bound:
                            (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
                                create_existing_edit_subforms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix=self.prefix, subform_min=subform_min, subform_max=subform_max)
                        else:
                            (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
                                create_edit_subforms_from_data(self.data, models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix=self.prefix, subform_min=subform_min, subform_max=subform_max)
                            self.subform_validity = all(validity)
                            if self.subform_validity:
                                for standard_properties_formset in standard_properties_formsets.values():
                                    standard_properties_formset.force_clean()

                    else:
                        (models, standard_properties, scientific_properties) = \
                            MetadataModel.get_new_realization_set(subform_customizer.project, subform_customizer.version, subform_customizer.proxy, standard_property_proxies, scientific_property_proxies, model_customizer, MetadataVocabulary.objects.none())

                        if not self.is_bound:
                            (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
                                create_new_edit_subforms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix=self.prefix, subform_min=subform_min, subform_max=subform_max)
                        else:
                            (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
                                create_edit_subforms_from_data(self.data, models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix=self.prefix, subform_min=subform_min, subform_max=subform_max)
                            self.subform_validity = all(validity)
                            if self.subform_validity:
                                for standard_properties_formset in standard_properties_formsets.values():
                                    standard_properties_formset.force_clean()

                else:
                    (models, standard_properties, scientific_properties) = \
                        MetadataModel.get_new_realization_set(subform_customizer.project, subform_customizer.version, subform_customizer.proxy, standard_property_proxies, scientific_property_proxies, model_customizer, MetadataVocabulary.objects.none())

                    if not self.is_bound:
                        (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
                            create_new_edit_subforms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix=self.prefix, subform_min=subform_min, subform_max=subform_max)

                    else:
                        (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
                            create_edit_subforms_from_data(self.data, models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix=self.prefix, subform_min=subform_min, subform_max=subform_max)
                        self.subform_validity = all(validity)
                        if self.subform_validity:
                            for standard_properties_formset in standard_properties_formsets.values():
                                standard_properties_formset.force_clean()

                self.subform_tuple = (subform_customizer, model_formset, standard_properties_formsets, scientific_properties_formsets)

        # the other stuff is common to all and can be generic (ie: use 'value_field_name')

        self.fields[value_field_name].help_text = customizer.documentation

        if customizer.required:
            update_field_widget_attributes(self.fields[value_field_name], {"class": "required"})
        else:
            update_field_widget_attributes(self.fields[value_field_name], {"class": "optional"})

        if not customizer.editable:
            update_field_widget_attributes(self.fields[value_field_name], {"class": "readonly", "readonly": "readonly"})

        if customizer.inherited:
            update_field_widget_attributes(self.fields[value_field_name], {"class": "inherited", "onchange": "inherit(this);"})

        if customizer.suggestions:
            update_field_widget_attributes(self.fields[value_field_name], {"class": "autocomplete"})
            update_field_widget_attributes(self.fields[value_field_name], {"suggestions": customizer.suggestions})

        self.customizer = customizer

    def clean(self):
        super(MetadataAbstractStandardPropertyForm, self).clean()

        cleaned_data = self.cleaned_data

        field_type = cleaned_data["field_type"]

        if "field_type" != MetadataFieldTypes.ATOMIC:
            pass

        elif "field_type" != MetadataFieldTypes.ENUMERATION:
            cleaned_data["enumeration_value"] = u""  # don't try anything fancy w/ enumeration fields

        elif "field_type" != MetadataFieldTypes.RELATIONSHIP:
            pass

        return cleaned_data

    def is_valid(self):

        validity = super(MetadataAbstractStandardPropertyForm, self).is_valid()

        field_type = self.get_current_field_value("field_type")
        if field_type == MetadataFieldTypes.RELATIONSHIP:
            if self.customizer.relationship_show_subform:
                validity = validity and self.subform_validity

        return validity

    def get_subform_tuple(self):
        field_type = self.get_current_field_value("field_type")
        assert(field_type == MetadataFieldTypes.RELATIONSHIP)
        assert(len(self.subform_tuple) == 4)
        return self.subform_tuple

    def get_subform_customizer(self):
        subform_tuple = self.get_subform_tuple()
        return subform_tuple[0]

    def get_model_subformset(self):
        subform_tuple = self.get_subform_tuple()
        model_subformset = subform_tuple[1]
        # (thought I could get away w/ just returning the single form)
        # (but b/c I'm dealing w/ a formset, I need the whole thing)
        # (in order to get access to the management form)
        return model_subformset

    def get_standard_properties_subformsets(self):
        subform_tuple = self.get_subform_tuple()
        return subform_tuple[2]

    def get_scientific_properties_subformsets(self):
        subform_tuple = self.get_subform_tuple()
        return subform_tuple[3]


class MetadataStandardPropertyForm(MetadataAbstractStandardPropertyForm):

    class Meta:
        model   = MetadataStandardProperty
        fields = [
            # hidden fields...
            "proxy", "field_type", "name", "order", "is_label",
            # value fields...
            "atomic_value", "enumeration_value", "enumeration_other_value", "relationship_value",
        ]

    # set of fields that will be the same for all members of a formset; allows me to cache the query (for relationship fields)
    cached_fields       = []

    _value_fields       = ["atomic_value", "enumeration_value", "enumeration_other_value", "relationship_value",]
    _hidden_fields      = ["proxy", "field_type", "name", "order", "is_label"]


    def has_changed(self):
        return True

class MetadataStandardPropertySubForm(MetadataAbstractStandardPropertyForm):

    class Meta:
        model   = MetadataStandardProperty
        fields = [
            # hidden fields...
            "proxy", "field_type", "name", "order", "is_label",
            # value fields...
            "atomic_value", "enumeration_value", "enumeration_other_value", "relationship_value",
        ]

    # set of fields that will be the same for all members of a formset; allows me to cache the query (for relationship fields)
    cached_fields       = []

    _value_fields       = ["atomic_value", "enumeration_value", "enumeration_other_value", "relationship_value",]
    _hidden_fields      = ["proxy", "field_type", "name", "order", "is_label"]

    def __init__(self,*args,**kwargs):

        super(MetadataStandardPropertySubForm,self).__init__(*args,**kwargs)

        # this is really really important!
        # this ensures that there is something to compare field data against so that I can truly tell is the model has changed
        # [http://stackoverflow.com/questions/11710845/in-django-1-4-do-form-has-changed-and-form-changed-data-which-are-undocument]
        for field_name in self._meta.fields:
            try:
                self.fields[field_name].show_hidden_initial = True
            except KeyError:
                # inline formsets treat pk fields strangely, just ignore them in this context
                pass

    def force_clean(self):
        # alright, this is very confusing...
        # in __init__ I add hidden initial fields to let me know if something has changed
        # that work fine when I am determining whether or not to save a subform
        # but, subform_has_changed uses the boolean "any" to work out whether to save the full set
        # for those subforms in the subformset that have not changed, they will have not run a full clean
        # therefore their "cleaned_data" will be emtpy
        # therefore saving them will create properties w/ emtpy content
        # so this function exists to do what full_clean would have done if has_changed had returned True
        # I call it in save_valid_subforms below
        # [code is taken from "full_clean" in django.forms.forms.BaseForm.full_clean()]
        self._clean_fields()
        self._clean_form()
        self._post_clean()

class MetadataStandardPropertyInlineFormSet(BaseInlineFormSet):

    number_of_properties = 0       # lets me keep track of the number of forms w/out having to actually render them

    def _construct_form(self, i, **kwargs):

        if self.is_bound and i < self.initial_form_count():
            # Import goes here instead of module-level because importing
            # django.db has side effects.
            from django.db import connections
            pk_key = "%s-%s" % (self.add_prefix(i), self.model._meta.pk.name)
            pk = self.data[pk_key]
            pk_field = self.model._meta.pk
            pk = pk_field.get_db_prep_lookup('exact', pk,
                connection=connections[self.get_queryset().db])
            if isinstance(pk, list):
                pk = pk[0]
            kwargs['instance'] = self._existing_object(pk)
        if i < self.initial_form_count() and not kwargs.get('instance'):

            try:
                kwargs['instance'] = self.get_queryset()[i]
            except IndexError:
                # if this formset has changed based on add/delete via AJAX
                # then the underlying queryset may not have updated
                # if so - since I've already worked out the pk above - just get the model directly
                kwargs['instance'] = MetadataStandardProperty.objects.get(pk=pk)

        if i >= self.initial_form_count() and self.initial_extra:
            # Set initial values for extra forms
            try:
                kwargs['initial'] = self.initial_extra[i-self.initial_form_count()]
            except IndexError:
                pass
        form = super(BaseModelFormSet, self)._construct_form(i, **kwargs)

        if self.save_as_new:
            # Remove the primary key from the form's data, we are only
            # creating new instances
            form.data[form.add_prefix(self._pk_field.name)] = None

            # Remove the foreign key from the form's data
            form.data[form.add_prefix(self.fk.name)] = None

        # Set the fk value here so that the form can do its validation.
        setattr(form.instance, self.fk.get_attname(), self.instance.pk)

        # this speeds up loading time
        # (see "cached_fields" attribute in the form class)
        for cached_field_name in form.cached_fields:
            cached_field = form.fields[cached_field_name]
            cached_field_key = u"%s_%s" % (self.prefix, cached_field_name)
            cached_field.cache_choices = True

            if hasattr(cached_field,"_choices"):
                # it's a ChoiceField or something similar
                cached_choices = getattr(self, '_cached_choices_%s' % (cached_field_key), None)
                if cached_choices is None:
                    cached_choices = list(cached_field.choices)
                    setattr(self, "_cached_choices_%s" % (cached_field_key), cached_choices)
                cached_field.choices = cached_choices

            # this is not working for modelchoicefields
            # instead I use a custom "CachedModelChoiceField" directly in the form
            # elif hasattr(cached_field,"_queryset"):
            #     # it's a ModelChoiceField or something similar
            #     cached_queryset = getattr(self, '_cached_queryset_%s' % (cached_field_key), None)
            #     if cached_queryset is None:
            #         cached_queryset = cached_field.queryset
            #         setattr(self, "_cached_queryset_%s" % (cached_field_key), cached_queryset)
            #     cached_field.queryset = cached_queryset

        return form

    def force_clean(self):
        for form in self.forms:
            form.force_clean()

def MetadataStandardPropertyInlineFormSetFactory(*args,**kwargs):
    DEFAULT_PREFIX = "_standard_properties"

    _prefix      = kwargs.pop("prefix","")+DEFAULT_PREFIX
    _data        = kwargs.pop("data",None)
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
        # no longer dealing w/ iterators and making sure everything is in the same order
        # now I just pass the entire set of customizers and work out which one to use in the __init__ method
        #_formset.customizers = iter(_customizers)
        _formset.form = staticmethod(curry(MetadataStandardPropertyForm,customizers=_customizers))


    if _initial:
        _formset.number_of_properties = len(_initial)
    elif _queryset:
        _formset.number_of_properties = len(_queryset)
    elif _data:
        _formset.number_of_properties = int(_data[u"%s-TOTAL_FORMS"%(_prefix)])
    else:
        _formset.number_of_properties = 0

    if _data:
        return _formset(_data, instance=_instance, prefix=_prefix)

    # notice how both "queryset" and "initial" are passed
    # this handles both existing and new models
    # (in the case of existing models, "queryset" is used)
    # (in the case of new models, "initial" is used)
    # but both arguments are needed so that "extra" is used properly
    return _formset(queryset=_queryset, initial=_initial, instance=_instance, prefix=_prefix)

def MetadataStandardPropertyInlineSubFormSetFactory(*args,**kwargs):
    DEFAULT_PREFIX = "_standard_properties"

    _prefix      = kwargs.pop("prefix","")+DEFAULT_PREFIX
    _data        = kwargs.pop("data",None)
    _initial     = kwargs.pop("initial",[])
    _queryset    = kwargs.pop("queryset",MetadataStandardProperty.objects.none())
    _instance    = kwargs.pop("instance")
    _customizers = kwargs.pop("customizers",None)
    new_kwargs = {
        "can_delete" : True,
        "extra"      : kwargs.pop("extra",0),
        "formset"    : MetadataStandardPropertyInlineFormSet,
        "form"       : MetadataStandardPropertySubForm,
        "fk_name"    : "model" # required in-case there are more than 1 fk's to "metadatamodel"; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)

    _formset = inlineformset_factory(MetadataModel,MetadataStandardProperty,*args,**new_kwargs)
    if _customizers:
        # no longer dealing w/ iterators and making sure everything is in the same order
        # now I just pass the entire set of customizers and work out which one to use in the __init__ method
        #_formset.customizers = iter(_customizers)
        _formset.form = staticmethod(curry(MetadataStandardPropertySubForm,customizers=_customizers))

    if _initial:
        _formset.number_of_properties = len(_initial)
    elif _queryset:
        _formset.number_of_properties = len(_queryset)
    elif _data:
        _formset.number_of_properties = int(_data[u"%s-TOTAL_FORMS"%(_prefix)])
    else:
        _formset.number_of_properties = 0

    if _data:
        return _formset(_data, instance=_instance, prefix=_prefix)

    # notice how both "queryset" and "initial" are passed
    # this handles both existing and new models
    # (in the case of existing models, "queryset" is used)
    # (in the case of new models, "initial" is used)
    # but both arguments are needed so that "extra" is used properly
    return _formset(queryset=_queryset, initial=_initial, instance=_instance, prefix=_prefix)

#########################
# scientific properties #
#########################

def create_scientific_property_form_data(model,scientific_property,scientific_property_customizer=None):

    scientific_property_form_data = model_to_data(
        scientific_property,
        exclude = [ "model" ],
        include = {
            "last_modified" : time.strftime("%c"),
        }
    )

    # scientific_property_form_data = get_initial_data(scientific_property,{
    #     "last_modified" : time.strftime("%c"),
    #     # no need to pass model, since this is handled by virtue of being an "inline" formset
    # })

    if scientific_property_customizer:

        if scientific_property_customizer.is_enumeration:
            # enumeration fields...
            current_enumeration_value = scientific_property_form_data["enumeration_value"]
            if current_enumeration_value:
                if scientific_property_customizer.enumeration_multi:
                    scientific_property_form_data["enumeration_value"] = current_enumeration_value.split("|")

        else:
            # atomic fields...
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

        # customizers was passed in via curry() in the factory function below
        customizers = kwargs.pop("customizers",None)

        super(MetadataScientificPropertyForm,self).__init__(*args,**kwargs)

        if customizers:
            proxy = MetadataScientificPropertyProxy.objects.get(pk=self.get_current_field_value("proxy"))
            customizer = find_in_sequence(lambda c: c.proxy == proxy, customizers)
        else:
            customizer = None

        property = self.instance
        is_enumeration = self.get_current_field_value("is_enumeration",False)

        if property.pk:
            # ordinarily, this is done in create_scientific_property_form_data above
            # but if this is an existing model, I still need to do this jiggery-pokery someplace
            if is_enumeration:
                current_enumeration_value = self.get_current_field_value("enumeration_value")
                if isinstance(current_enumeration_value,basestring) and customizer.enumeration_multi:
                    self.initial["enumeration_value"] = current_enumeration_value.split("|")

        if not is_enumeration:
            update_field_widget_attributes(self.fields["atomic_value"],{"onchange":"copy_value(this,'%s-scientific_property_value');"%(self.prefix)})
            update_field_widget_attributes(self.fields["atomic_value"],{"class":"atomic_value"})

        else:
            update_field_widget_attributes(self.fields["enumeration_value"],{"class":"multiselect"})
            # multiselect widgets are annoyingly annoying
            # I can't do this on the actual field here
            # instead I have to do it on the widget in js
            #update_field_widget_attributes(self.fields["enumeration_value"],{"onchange":"copy_value(this,'%s-scientific_property_value');"%(self.prefix)})

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
            widget_attributes = { "class" : "multiselect" }
            all_enumeration_choices = customizer.enumerate_choices()
            if customizer.enumeration_nullable:
                all_enumeration_choices += NULL_CHOICE
                widget_attributes["class"] += " nullable"
            if customizer.enumeration_open:
                all_enumeration_choices += OTHER_CHOICE
                widget_attributes["class"] += " open"
            if customizer.enumeration_multi:
                self.fields["enumeration_value"].set_choices(all_enumeration_choices,multi=True)
            else:
                all_enumeration_choices = EMPTY_CHOICE + all_enumeration_choices
                self.fields["enumeration_value"].set_choices(all_enumeration_choices,multi=False)

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

        is_enumeration = self.get_current_field_value("is_enumeration",False)

        if not is_enumeration:
            return "atomic_value"
        else:
            return "enumeration_value"


class MetadataScientificPropertyInlineFormSet(BaseInlineFormSet):

    number_of_properties = 0

    # also using it to cache fk or m2m fields to avoid needless (on the order of 30K!) db hits

    def _construct_form(self, i, **kwargs):
        
        # no longer dealing w/ iterators and keeping everything in order
        # instead using find_in_sequence in the __init__ method
        # if self.customizers:
        #     try:
        #         kwargs["customizer"] = next(self.customizers)
        #     except StopIteration:
        #         # don't worry about not having a customizer for the extra form
        #         pass

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
    _data        = kwargs.pop("data",None)
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

    assert(len(_initial)==new_kwargs["extra"])

    _formset = inlineformset_factory(MetadataModel,MetadataScientificProperty,*args,**new_kwargs)
    if _customizers:
        # no longer dealing w/ iterators and making sure everything is in the same order
        # now I just pass the entire set of customizers and work out which one to use in the __init__ method
        #_formset.customizers = iter(_customizers)
        _formset.form = staticmethod(curry(MetadataScientificPropertyForm,customizers=_customizers))

    if _initial:
        _formset.number_of_properties = len(_initial)
    elif _queryset:
        _formset.number_of_properties = len(_queryset)
    elif _data:
        _formset.number_of_properties = int(_data[u"%s-TOTAL_FORMS"%(_prefix)])
    else:
        _formset.number_of_properties = 0

    if _data:
        return _formset(_data, instance=_instance, prefix=_prefix)

    # notice how both "queryset" and "initial" are passed
    # this handles both existing and new models
    # (in the case of existing models, "queryset" is used)
    # (in the case of new models, "initial" is used)
    # but both arguments are needed so that "extra" is used properly
    return _formset(queryset=_queryset, initial=_initial, instance=_instance, prefix=_prefix)


def create_new_edit_forms_from_models(models,model_customizer,standard_properties,standard_property_customizers,scientific_properties,scientific_property_customizers):

    model_keys = [u"%s_%s" % (model.vocabulary_key, model.component_key) for model in models]

    models_data = [create_model_form_data(model, model_customizer) for model in models]
    model_formset = MetadataModelFormSetFactory(
        initial = models_data,
        extra = len(models_data),
        prefixes = model_keys,
        customizer = model_customizer,
    )

    standard_properties_formsets = {}
    scientific_properties_formsets = {}
    for model_key, model in zip(model_keys,models):

        standard_properties_data = [
            create_standard_property_form_data(model, standard_property, standard_property_customizer)
            for standard_property, standard_property_customizer in
            zip(standard_properties[model_key], standard_property_customizers)
            if standard_property_customizer.displayed
        ]
        standard_properties_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
            instance = model,
            prefix = model_key,
            initial = standard_properties_data,
            extra = len(standard_properties_data),
            customizers = standard_property_customizers,
        )

        # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
        if model_key not in scientific_property_customizers:
            scientific_property_customizers[model_key] = []

        scientific_properties_data = [
            create_scientific_property_form_data(model, scientific_property, scientific_property_customizer)
            for scientific_property, scientific_property_customizer in
            zip(scientific_properties[model_key], scientific_property_customizers[model_key])
            if scientific_property_customizer.displayed
        ]
        assert(len(scientific_properties_data)==len(scientific_properties[model_key]))
        scientific_properties_formsets[model_key] = MetadataScientificPropertyInlineFormSetFactory(
            instance = model,
            prefix = model_key,
            initial = scientific_properties_data,
            extra = len(scientific_properties_data),
            customizers = scientific_property_customizers[model_key],
        )

    return (model_formset, standard_properties_formsets, scientific_properties_formsets)



def create_existing_edit_forms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers):

    model_keys = [u"%s_%s" % (model.vocabulary_key, model.component_key) for model in models]

    model_formset = MetadataModelFormSetFactory(
        queryset = models,
        prefixes = model_keys,
        customizer = model_customizer,
    )

    standard_properties_formsets = {}
    scientific_properties_formsets = {}
    for model_key, model in zip(model_keys,models):

        standard_properties_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
            instance=model,
            prefix = model_key,
            queryset=standard_properties[model_key],
            customizers=standard_property_customizers,
        )

        # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
        if model_key not in scientific_property_customizers:
            scientific_property_customizers[model_key] = []

        scientific_properties_formsets[model_key] = MetadataScientificPropertyInlineFormSetFactory(
            instance = model,
            prefix = model_key,
            queryset = scientific_properties[model_key],
            customizers = scientific_property_customizers[model_key],
        )

    return (model_formset, standard_properties_formsets, scientific_properties_formsets)


def create_new_edit_subforms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix="", subform_min=0, subform_max=1,  increment_prefix=0):

    model_keys = [model.get_model_key() for model in models]

    models_data = [create_model_form_data(model, model_customizer) for model in models]
    model_formset = MetadataModelSubFormSetFactory(
        initial = models_data,
        extra = len(models_data),
        prefix = subform_prefix,
        customizer = model_customizer,
        min = subform_min,
        max = subform_max,
        increment_prefix = increment_prefix,
    )

    standard_properties_formsets = {}
    scientific_properties_formsets = {}
    for model_key, model, model_form in zip(model_keys, models, model_formset.forms):

        adjusted_prefix = model_form.prefix
        submodel_key = model_key
        if model.pk:
            submodel_key += str(model.pk)

        standard_properties_data = [
            create_standard_property_form_data(model, standard_property, standard_property_customizer)
            for standard_property, standard_property_customizer in
            zip(standard_properties[model_key], standard_property_customizers)
            if standard_property_customizer.displayed
        ]
        standard_properties_formsets[submodel_key] = MetadataStandardPropertyInlineSubFormSetFactory(
            instance = model,
            prefix = adjusted_prefix,
            initial = standard_properties_data,
            extra = len(standard_properties_data),
            customizers = standard_property_customizers,
        )

        # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
        if model_key not in scientific_property_customizers:
            scientific_property_customizers[model_key] = []

        scientific_properties_data = [
            create_scientific_property_form_data(model, scientific_property, scientific_property_customizer)
            for scientific_property, scientific_property_customizer in
            zip(scientific_properties[model_key], scientific_property_customizers[model_key])
            if scientific_property_customizer.displayed
        ]
        assert(len(scientific_properties_data)==len(scientific_properties[model_key]))
        scientific_properties_formsets[submodel_key] = MetadataScientificPropertyInlineFormSetFactory(
            instance = model,
            prefix = adjusted_prefix,
            initial = scientific_properties_data,
            extra = len(scientific_properties_data),
            customizers = scientific_property_customizers[model_key],
        )

    return (model_formset, standard_properties_formsets, scientific_properties_formsets)


def create_existing_edit_subforms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix="", subform_min=0, subform_max=1, increment_prefix=0):

    model_keys = [model.get_model_key() for model in models]

    model_formset = MetadataModelSubFormSetFactory(
        queryset = models,
        prefix = subform_prefix,
        customizer = model_customizer,
        min = subform_min,
        max = subform_max,
        increment_prefix = increment_prefix,
    )

    for model_form in model_formset.forms:
        assert(model_form.instance.pk is not None)

    standard_properties_formsets = {}
    scientific_properties_formsets = {}
    for model_key, model, model_form in zip(model_keys, models, model_formset.forms):

        adjusted_prefix = model_form.prefix
        submodel_key = model_key + str(model.pk)

        standard_properties_formsets[submodel_key] = MetadataStandardPropertyInlineSubFormSetFactory(
            instance=model,
            prefix = adjusted_prefix,
            queryset=standard_properties[submodel_key],
            customizers=standard_property_customizers,
        )

        # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
        if model_key not in scientific_property_customizers:
            scientific_property_customizers[model_key] = []

        scientific_properties_formsets[submodel_key] = MetadataScientificPropertyInlineFormSetFactory(
            instance = model,
            prefix = adjusted_prefix,
            queryset = scientific_properties[submodel_key],
            customizers = scientific_property_customizers[model_key],
        )

    return (model_formset, standard_properties_formsets, scientific_properties_formsets)


def create_edit_forms_from_data(data, models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers):
    """This creates and validates forms based on POST data"""

    model_keys = [model.get_model_key() for model in models]

    model_formset = MetadataModelFormSetFactory(
        data = data,
        prefixes = model_keys,
        customizer = model_customizer,
    )

    model_formset_validity = model_formset.is_valid()
    if model_formset_validity:
        # force model_formset to save instances even if they haven't changed
        #model_instances = model_formset.save(commit=False)
        model_instances = [model_form.save(commit=False) for model_form in model_formset.forms]
    validity = [model_formset_validity]

    standard_properties_formsets = {}
    scientific_properties_formsets = {}


    for (i, model_key) in enumerate(model_keys):

        standard_properties_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
            instance = model_instances[i] if model_formset_validity else models[i],
            prefix = model_key,
            data = data,
            customizers = standard_property_customizers,
        )

        validity += [standard_properties_formsets[model_key].is_valid()]

        # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
        if model_key not in scientific_property_customizers:
            scientific_property_customizers[model_key] = []

        scientific_properties_formsets[model_key] = MetadataScientificPropertyInlineFormSetFactory(
            instance = model_instances[i] if model_formset_validity else models[i],
            prefix = model_key,
            data = data,
            customizers = scientific_property_customizers[model_key],
        )

        validity += [scientific_properties_formsets[model_key].is_valid()]

    return (validity, model_formset, standard_properties_formsets, scientific_properties_formsets)


def create_edit_subforms_from_data(data, models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix="", subform_min=0, subform_max=1):
    """This creates and validates forms based on POST data"""

    model_formset = MetadataModelSubFormSetFactory(
        data = data,
        prefix = subform_prefix,
        customizer = model_customizer,
        min = subform_min,
        max = subform_max,
    )

    # because this is a subform and has potentially been added/removed via AJAX
    # the underlying instances may not have been set;
    # this code fixes that
    for model_form in model_formset.forms:
        instance_pk = model_form.instance.pk
        form_pk = model_form.get_current_field_value("id")
        if (not instance_pk) and form_pk:
            model_form.instance = MetadataModel.objects.get(pk=form_pk)

    model_formset_validity = model_formset.is_valid()
    if model_formset_validity:
        # force model_formset to save instances even if they haven't changed
        #model_instances = model_formset.save(commit=False)
        model_instances = [model_form.save(commit=False) for model_form in model_formset.forms]
    validity = [model_formset_validity]

    standard_properties_formsets = {}
    scientific_properties_formsets = {}

    for (i, model_form) in enumerate(model_formset.forms):

        adjusted_prefix = model_form.prefix
        model_key = model_form.instance.get_model_key()

        standard_properties_formsets[adjusted_prefix] = MetadataStandardPropertyInlineSubFormSetFactory(
            instance = model_instances[i] if model_formset_validity else model_form.instance,
            prefix = adjusted_prefix,
            data = data,
            customizers = standard_property_customizers,
        )

        validity += [standard_properties_formsets[adjusted_prefix].is_valid()]

        # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
        if model_key not in scientific_property_customizers:
            scientific_property_customizers[model_key] = []

        scientific_properties_formsets[adjusted_prefix] = MetadataScientificPropertyInlineFormSetFactory(
            instance = model_instances[i] if model_formset_validity else model_form.instance,
            prefix = adjusted_prefix,
            data = data,
            customizers = scientific_property_customizers[model_key],
        )

        validity += [scientific_properties_formsets[adjusted_prefix].is_valid()]

    return (validity, model_formset, standard_properties_formsets, scientific_properties_formsets)


def save_valid_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, model_parent_dictionary={}):

    # force model_formset to save instances even if they haven't changed
    #model_instances = model_formset.save(commit=True)
    # TODO: MAKE THE commit KWARG CONDITIONAL ON WHETHER THE FORM CHANGED (OR IS NEW) TO CUT DOWN ON DB HITS
    # (NOTE, I'LL HAVE TO CHANGE THE LOOP BELOW ONCE I'VE DONE THIS)
    model_instances = [model_form.save(commit=True) for model_form in model_formset.forms]

    for model_instance in model_instances:
        try:
            model_parent_key = model_parent_dictionary[model_instance.get_model_key()]
            model_instance.parent = find_in_sequence(lambda m: m.get_model_key() == model_parent_key,model_instances)
        except KeyError:
            pass  # maybe this model didn't have a parent (or the dict was never passed to this fn)
        model_instance.save()

    # for standard_property_formset in standard_properties_formsets.values():
    #     standard_property_instances = standard_property_formset.save(commit=False)
    #     for standard_property_instance in standard_property_instances:
    #         standard_property_instance.save()

    for standard_property_formset in standard_properties_formsets.values():
        # using zip here is the only way that I managed to get saving to work
        # I have to save via the inlineformset (so that the inline fk gets saved appropriately)
        # but I also need access to the underlying form so I can check certain customization details
        for standard_property_instance, standard_property_form in zip(standard_property_formset.save(commit=True),standard_property_formset.forms):
            assert(standard_property_instance.name == standard_property_form.get_current_field_value("name"))
            if standard_property_instance.field_type == MetadataFieldTypes.RELATIONSHIP and standard_property_form.customizer.relationship_show_subform:

                (subform_customizer, model_subformset, standard_properties_subformsets, scientific_properties_subformsets) = \
                    standard_property_form.get_subform_tuple()

                for model_subform in model_subformset.forms:
                    property_key = model_subform.prefix

                    subform_has_changed = any([
                        # don't bother checking model_subformset - if the properties have changed, I'll be saving it regardless
                        #model_subform.has_changed(),
                        any([form.has_changed() for form in standard_properties_subformsets[property_key]]),
                        any([form.has_changed() for form in scientific_properties_subformsets[property_key]]),
                    ])

                    if subform_has_changed:
                        subform_model_instance = save_valid_subforms(model_subform,standard_properties_subformsets[property_key], scientific_properties_subformsets[property_key])
                        standard_property_instance.relationship_value.add(subform_model_instance)
                standard_property_instance.save()

    for scientific_property_formset in scientific_properties_formsets.values():
        scientific_property_instances = scientific_property_formset.save(commit=False)
        for scientific_property_instance in scientific_property_instances:
            scientific_property_instance.save()

    return model_instances


def save_valid_subforms(model_subform, standard_properties_subformset, scientific_properties_subformset, model_parent_dictionary={}):
    # almost like the above function, but works w/ a single form, formset, formset
    # b/c I deal w/ subforms one form at a time (in case anything has been added/removed via JS)

    # TODO: MAKE THE commit KWARG CONDITIONAL ON WHETHER THE FORM CHANGED (OR IS NEW) TO CUT DOWN ON DB HITS
    # (NOTE, I'LL HAVE TO CHANGE THE LOOP BELOW ONCE I'VE DONE THIS)
    model_instance = model_subform.save(commit=True)

    # for standard_property_formset in standard_properties_formsets.values():
    #     standard_property_instances = standard_property_formset.save(commit=False)
    #     for standard_property_instance in standard_property_instances:
    #         standard_property_instance.save()

    # using zip here is the only way that I managed to get saving to work
    # I have to save via the inlineformset (so that the inline fk gets saved appropriately)
    # but I also need access to the underlying form so I can check certain customization details
    # NOTE THAT force_clean() MUST HAVE BEEN CALLED AFTER VALIDATION BUT PRIOR TO SAVING FOR THIS TO WORK
 #   for standard_property_instance, standard_property_form in zip(standard_properties_subformset.save(commit=True),standard_properties_subformset.forms):


    standard_property_instances = [sp.save(commit=False) for sp in standard_properties_subformset.forms]
    for standard_property_instance, standard_property_form in zip(standard_property_instances, standard_properties_subformset.forms):
    #for standard_property_form in standard_properties_subformset.forms:
        assert(standard_property_instance.name == standard_property_form.get_current_field_value("name"))
        # TODO: NO IDEA WHY I HAVE TO EXPLICITLY ADD THIS HERE
        # BUT NOT IN THE ABOVE save_valid_forms FUNCTION?!?
        standard_property_instance.model = model_instance
        standard_property_instance.save()
        if standard_property_instance.field_type == MetadataFieldTypes.RELATIONSHIP and standard_property_form.customizer.relationship_show_subform:

            (subform_customizer, model_subformset, standard_properties_subformsets, scientific_properties_subformsets) = \
                standard_property_form.get_subform_tuple()

            for model_subform in model_subformset.forms:
                property_key = model_subform.prefix

                subform_has_changed = any([
                    # don't bother checking model_subformset - if the properties have changed, I'll be saving it regardless
                    #model_subform.has_changed(),
                    any([form.has_changed() for form in standard_properties_subformsets[property_key]]),
                    any([form.has_changed() for form in scientific_properties_subformsets[property_key]]),
                ])

                if subform_has_changed:
                    subform_model_instance = save_valid_subforms(model_subform,standard_properties_subformsets[property_key], scientific_properties_subformsets[property_key])
                    standard_property_instance.relationship_value.add(subform_model_instance)
            standard_property_instance.save()

    scientific_property_instances = scientific_properties_subformset.save(commit=False)
    for scientific_property_instance in scientific_property_instances:
        scientific_property_instance.save()

    return model_instance


def get_data_from_existing_edit_forms(model_formset,standard_properties_formsets,scientific_properties_formsets):

    data = {}

    model_formset_data = get_data_from_formset(model_formset)
    data.update(model_formset_data)

    # TODO: handle nested formsets here
    # I AM HERE
    for standard_property_formset in standard_properties_formsets.values():
        standard_property_formset_data = get_data_from_formset(standard_property_formset)
        data.update(standard_property_formset_data)


    for scientific_property_formset in scientific_properties_formsets.values():
        scientific_property_formset_data = get_data_from_formset(scientific_property_formset)
        data.update(scientific_property_formset_data)

    data_copy = data.copy()
    for key, value in data.iteritems():
        if value == None:
            data_copy.pop(key)

    return data_copy


def get_data_from_edit_forms(model_formset,standard_properties_formsets,scientific_properties_formsets):

    data = {}

    model_formset_data = get_data_from_formset(model_formset)
    data.update(model_formset_data)

    # TODO: handle nested formsets here
    # I AM HERE
    for standard_property_formset in standard_properties_formsets.values():
        standard_property_formset_data = get_data_from_formset(standard_property_formset)
        data.update(standard_property_formset_data)


    for scientific_property_formset in scientific_properties_formsets.values():
        scientific_property_formset_data = get_data_from_formset(scientific_property_formset)
        data.update(scientific_property_formset_data)

    data_copy = data.copy()
    for key, value in data.iteritems():
        if value == None:
            data_copy.pop(key)

    return data_copy