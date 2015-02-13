####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2014 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"
__date__ = "Dec 01, 2014 3:00:00 PM"

"""
.. module:: forms_edit_model

classes for CIM Questionnaire model edit form creation & manipulation
"""

import time
from django.utils.functional import curry
from django.forms.fields import BooleanField
from django.forms.models import modelformset_factory

from CIM_Questionnaire.questionnaire.forms.forms_edit import MetadataEditingForm, MetadataEditingFormSet
from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
from CIM_Questionnaire.questionnaire.utils import model_to_data, find_in_sequence, set_field_widget_attributes


def create_model_form_data(model, model_customizer):

    model_form_data = model_to_data(
        model,
        exclude=["tree_id", "lft", "rght", "level", "parent", ],  # ignore mptt fields
        include={
            "last_modified": time.strftime("%c"),
            "loaded": False,
        }
    )
    # model_form_data = get_initial_data(model,{
    #     "last_modified" : time.strftime("%c"),
    #     #"parent" : model.parent,
    # })

    return model_form_data


def save_valid_model_formset(model_formset, model_parent_dictionary={}):

    # just save everything, regardless of whether it was loaded or not
    # (all of the logic of dealing w/ non-loaded forms is dealt with in the creation & validation fns)
    # loaded_model_forms = model_formset.get_loaded_forms()
    model_forms = model_formset.forms

    # force model_formset to save instances even if they haven't changed
    # TODO: MAKE THE commit KWARG CONDITIONAL ON WHETHER THE FORM CHANGED (OR IS NEW) TO CUT DOWN ON DB HITS
    # TODO: (NOTE, I'LL HAVE TO CHANGE THE LOOP BELOW ONCE I'VE DONE THIS)
    model_instances = [model_form.save(commit=True) for model_form in model_forms]

    for model_instance in model_instances:
        try:
            model_parent_key = model_parent_dictionary[model_instance.get_model_key()]
            model_instance.parent = find_in_sequence(lambda m: m.get_model_key() == model_parent_key, model_instances)
        except KeyError:
            pass  # maybe this model didn't have a parent (or the dict was never passed to this fn)
        model_instance.save()

    return model_instances


class MetadataAbstractModelForm(MetadataEditingForm):

    class Meta:
        abstract = True

    def has_changed(self):
        # so I explicitly do not check the validity of modelsubforms (instead relying on propertysubforms)
        # see save_valid_forms() below
        return True

    def customize(self, customizer):

        self.customizer = customizer

        # customization is done both in the form and in the template
        # (but in the case of this class, MetadataModelForm, it's _all_ done in the template)
        pass


class MetadataModelForm(MetadataAbstractModelForm):

    class Meta:
        model = MetadataModel
        fields = [
            # hidden fields...
            "proxy", "project", "version", "is_document", "is_root", "vocabulary_key", "component_key", "active", "name", "description", "order", "id",
            # header fields...
            "title",
        ]

    # set of fields that will be the same for all members of a formset;
    # allows me to cache the query (for relationship fields)
    cached_fields = []

    _header_fields = ["title", ]
    _hidden_fields = ["proxy", "active", "project", "version", "is_document", "is_root", "vocabulary_key", "component_key", "name", "description", "order", "id", ]

    active = BooleanField(required=False)   # allow checked or unchecked as per https://docs.djangoproject.com/en/1.4/ref/forms/fields/#booleanfield

    def __init__(self, *args, **kwargs):

        super(MetadataModelForm, self).__init__(*args, **kwargs)

        set_field_widget_attributes(self.fields["title"], {"size": 64})

    def get_model_key(self):
        return self.prefix

    def get_vocabulary_key(self):
        split_prefix = self.prefix.split('_')
        n_splits = len(split_prefix)
        return "_".join(split_prefix[:(n_splits/2)])

    def get_component_key(self):
        split_prefix = self.prefix.split('_')
        n_splits = len(split_prefix)
        return "_".join(split_prefix[(n_splits/2):])


class MetadataModelSubForm(MetadataAbstractModelForm):

    class Meta:
        model = MetadataModel
        fields = [
            # hidden fields...
            "proxy", "project", "version", "is_document", "is_root", "vocabulary_key", "component_key", "active", "name", "description", "order",
            # header fields...
            "title",
        ]

    # set of fields that will be the same for all members of a formset; allows me to cache the query
    cached_fields = []

    _header_fields = ["title", ]
    _hidden_fields = ["proxy", "project", "version", "is_document", "is_root", "vocabulary_key", "component_key", "active", "name", "description", "order", ]

    active = BooleanField(required=False)   # allow checked or unchecked as per https://docs.djangoproject.com/en/1.4/ref/forms/fields/#booleanfield


class MetadataModelFormSet(MetadataEditingFormSet):

    def add_prefix(self, index):
        return "%s" % self.prefixes_list[index]

    # note that there is no _construct_form() fn
    # instead, I have overloaded the parent class


class MetadataModelSubFormSet(MetadataEditingFormSet):

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
        # (see "cached_fields" attribute in the form classes)
        for cached_field_name in form.cached_fields:
            cached_field = form.fields[cached_field_name]
            cached_field_key = u"%s_%s" % (self.prefix, cached_field_name)
            cached_field.cache_choices = True
            choices = getattr(self, '_cached_choices_%s' % cached_field_key, None)
            if choices is None:
                choices = list(cached_field.choices)
                setattr(self, '_cached_choices_%s' % cached_field_key, choices)
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

    def save_existing_objects(self, commit=True):
        """
        Overloads the base fn in order to prevent deleted subforms from _actually_ deleting underlying instances;
        This is b/c deleting a subform is meant to delete the _relationship_ not the _instances_;
        (which, btw, takes place in 'save_valid_standard_properties_formset')
        :param commit:
        :return:
        """
        self.changed_objects = []
        self.deleted_objects = []
        if not self.initial_forms:
            return []

        saved_instances = []
        forms_to_delete = self.deleted_forms
        for form in self.initial_forms:
            pk_name = self._pk_field.name
            raw_pk_value = form._raw_value(pk_name)

            # clean() for different types of PK fields can sometimes return
            # the model instance, and sometimes the PK. Handle either.
            pk_value = form.fields[pk_name].clean(raw_pk_value)
            pk_value = getattr(pk_value, 'pk', pk_value)

            obj = self._existing_object(pk_value)
            if form in forms_to_delete:
                # HERE BEGINS THE DIFFERENT BIT
                # don't actually delete the form or instance
                # self.deleted_objects.append(obj)
                # obj.delete()
                # but do store a placeholder in "saved_instances"
                # so that the looping in "create_edit_subforms_from_data" doesn't get out of sync
                saved_instances.append(None)
                # HERE ENDS THE DIFFERENT BIT
                continue
            if form.has_changed():
                self.changed_objects.append((obj, form.changed_data))
                saved_instances.append(self.save_existing(form, obj, commit=commit))
                if not commit:
                    self.saved_forms.append(form)
        return saved_instances

def MetadataModelFormSetFactory(*args, **kwargs):
    _DEFAULT_PREFIX = "form"

    _prefixes = kwargs.pop("prefixes", [])
    _data = kwargs.pop("data", None)
    _initial = kwargs.pop("initial", [])
    _queryset = kwargs.pop("queryset", MetadataModel.objects.none())
    _customizer = kwargs.pop("customizer", None)
    new_kwargs = {
        "can_delete": False,
        "extra": kwargs.pop("extra", 0),
        "formset": MetadataModelFormSet,
        "form": MetadataModelForm,
    }
    new_kwargs.update(kwargs)

    # using curry() to pass arguments to the individual formsets
    _formset = modelformset_factory(MetadataModel, *args, **new_kwargs)
    _formset.form = staticmethod(curry(MetadataModelForm, customizer=_customizer))
    formset_prefix = _DEFAULT_PREFIX

    if _prefixes:
        _formset.prefix_iterator = iter(_prefixes)
        _formset.prefixes_list = _prefixes

    if _initial:
        _formset.number_of_models = len(_initial)
    elif _queryset:
        _formset.number_of_models = len(_queryset)
    elif _data:
        _formset.number_of_models = int(_data[u"%s-TOTAL_FORMS" % formset_prefix])
    else:
        _formset.number_of_models = 0

    if _data:
        return _formset(_data, initial=_initial, prefix=formset_prefix)

    # notice how both "queryset" and "initial" are passed
    # this handles both existing and new models
    # (in the case of existing models, "queryset" is used)
    # (in the case of new models, "initial" is used)
    # but both arguments are needed so that "extra" is used properly
    return _formset(queryset=_queryset, initial=_initial, prefix=formset_prefix)


def MetadataModelSubFormSetFactory(*args, **kwargs):
    _DEFAULT_PREFIX = "_subform"

    _prefix = kwargs.pop("prefix", "") + _DEFAULT_PREFIX
    _data = kwargs.pop("data", None)
    _initial = kwargs.pop("initial", [])
    _queryset = kwargs.pop("queryset", MetadataModel.objects.none())
    _customizer = kwargs.pop("customizer", None)
    _min = kwargs.pop("min", 0)
    _max = kwargs.pop("max", 1)
    _increment_prefix = kwargs.pop("increment_prefix", 0)
    new_kwargs = {
        "can_delete": True,
        "extra": kwargs.pop("extra", 0),
        "formset": MetadataModelSubFormSet,
        "form": MetadataModelSubForm,
        # TODO: "min_num", and "validate_min" IS ONLY VALID FOR DJANGO 1.7+
        # (that's why I explicitly add it below)
        # "min_num" : _min,
        # "validate_min" : True,
        "max_num": None if _max == u"*" else _max,   # (a value of None implies no limit)
        "validate_max": True,
    }
    new_kwargs.update(kwargs)

    # using curry() to pass arguments to the individual formsets
    _formset = modelformset_factory(MetadataModel, *args, **new_kwargs)
    _formset.form = staticmethod(curry(MetadataModelSubForm, customizer=_customizer))
    _formset.min = _min
    _formset.max = _max
    _formset.increment_prefix = _increment_prefix

    if _initial:
        _formset.number_of_models = len(_initial)
    elif _queryset:
        _formset.number_of_models = len(_queryset)
    elif _data:
        _formset.number_of_models = int(_data[u"%s-TOTAL_FORMS" % _prefix])
    else:
        _formset.number_of_models = 0

    if _data:
        return _formset(_data, initial=_initial, prefix=_prefix)

    # notice how both "queryset" and "initial" are passed
    # this handles both existing and new models
    # (in the case of existing models, "queryset" is used)
    # (in the case of new models, "initial" is used)
    # but both arguments are needed so that "extra" is used properly
    return _formset(queryset=_queryset, initial=_initial, prefix=_prefix)
