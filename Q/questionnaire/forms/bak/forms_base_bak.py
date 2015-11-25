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
.. module:: forms_base

Base classes for CIM Questionnaire form creation & manipulation
"""

from django.forms import ValidationError
from django.forms.models import InlineForeignKeyField
from django.utils.translation import ungettext
from django.forms.fields import BooleanField, FileField, MultiValueField
from django.forms.models import ModelForm, BaseModelFormSet, BaseInlineFormSet
from django.forms.util import ErrorDict
from django.forms.formsets import TOTAL_FORM_COUNT, INITIAL_FORM_COUNT, MAX_NUM_FORM_COUNT
from django.forms import model_to_dict


MANAGEMENT_FORM_FIELD_NAMES = [
    TOTAL_FORM_COUNT,
    INITIAL_FORM_COUNT,
    MAX_NUM_FORM_COUNT
]

# THIS TOOK A WHILE TO FIGURE OUT
# model_to_dict IGNORES FOREIGNKEY FIELDS & MANYTOMANY FIELDS
# THIS FN WILL UPDATE THE MODEL_DATA ACCORDING TO THE "update_fields" ARGUMENT
def get_initial_data(model, update_fields={}):
    _dict = model_to_dict(model)
    _dict.update(update_fields)
    for key, value in _dict.iteritems():
        if isinstance(value, tuple):
            # TODO: SOMETIMES THIS RETURNS A TUPLE INSTEAD OF A STRING, NOT SURE WHY
            _dict[key] = value[0]
    return _dict

# TODO: REPLACE THE ABOVE FN W/ THIS FN IN CODE
def model_to_data(model, exclude=[], include={}):
    model_data = model_to_dict(model)
    model_data.update(include)
    model_data_copy = model_data.copy()
    for key, value in model_data_copy.iteritems():
        if key in exclude:
            model_data.pop(key)
    return model_data

def get_form_by_prefix(formset, prefix):
    """
    returns the form in a formset w/ a prefix of prefix
    :param formset: formset to check
    :param prefix: value of prefix to look for
    :return: matching form or none
    """
    for form in formset:
        if form.prefix == prefix:
            return form
    return None

def get_data_from_form(form, existing_data={}):

    data = {}

    form_prefix = form.prefix
    for field_name, field in form.fields.iteritems():
        try:
            if field_name in existing_data:
                field_value = existing_data[field_name]
            else:
                field_value = form.get_current_field_value(field_name)
        except:
            if field_name in existing_data:
                field_value = existing_data[field_name]
            else:
                field_value = form.get_current_field_value(field_name)

        if form_prefix:
            field_key = u"%s-%s" % (form_prefix, field_name)
        else:
            field_key = u"%s" % field_name

        # this checks if I am dealing w/ a MultiValueField
        # Django automatically separates this into its constituent fields when gathering data via POST
        # this fn has to do this manually b/c it's usually called outside of the standard GET/POST view paradigm
        # (ie: via the testing framework)
        # TODO: AM I SURE THAT THE FIELD_VALUE WILL ALWAYS BE A LIST AND NOT A TUPLE?
        if isinstance(field, MultiValueField) and isinstance(field_value, list):
            for i, v in enumerate(field_value):
                data[u"%s_%s" % (field_key, i)] = v
        else:
            # obviously, a non-MultiValueField is much easier
            data[field_key] = field_value

    return data


def get_data_from_formset(formset, existing_data={}):
    data = {}
    current_data = {}

    for form in formset:
        current_data.clear()
        current_data.update(existing_data)

        # in general, this is only needed when calling this fn outside of the interface
        # ie: in the testing framework
        # (the hidden pk & fk fields do not get passed in via the queryset for existing model formsets)
        pk_field_name = formset.model._meta.pk.name
        current_data[pk_field_name] = form.fields[pk_field_name].initial
        if isinstance(formset, BaseInlineFormSet):
            fk_field_name = formset.fk.name
            current_data[fk_field_name] = form.fields[fk_field_name].initial

        if formset.can_delete:
            current_data["DELETE"] = False

        form_data = get_data_from_form(form, current_data)
        data.update(form_data)

    formset_prefix = formset.prefix
    if formset_prefix:
        total_forms_key = u"%s-TOTAL_FORMS" % formset_prefix
        initial_forms_key = u"%s-INITIAL_FORMS" % formset_prefix
    else:
        total_forms_key = u"TOTAL_FORMS"
        initial_forms_key = u"INITIAL_FORMS"
    data[total_forms_key] = formset.total_form_count()
    data[initial_forms_key] = formset.initial_form_count()

    return data


def remove_non_loaded_data(data, loaded_prefixes, management_form_prefix):
    # it is much easier to work out which forms w/in a formset are loaded than which are non-loaded
    # so even though this removes the non-loaded data, I pass it the loaded prefixes
    data_copy = data.copy()
    for key, value in data.iteritems():
        if any(key == u"%s-%s" % (management_form_prefix, management_form_field_name) for management_form_field_name in MANAGEMENT_FORM_FIELD_NAMES):
            # but don't get rid of management form stuff
            continue
        if not any(key.startswith(loaded_key) for loaded_key in loaded_prefixes):
            # if this item doesn't begin w/ one of the loaded_prefixes, then it must be unloaded
            # which means it shouldn't appear in the POST
            data_copy.pop(key)
    return data_copy


def remove_null_data(data):
    data_copy = data.copy()
    for key, value in data.iteritems():
        if value == None:
            data_copy.pop(key)
    return data_copy

class MetadataForm(ModelForm):

    cached_fields = []

    # these fields raise form validation errors with string Nones
    _fields_none_string_overload = ('id', 'enumeration_value', 'relationship_value')

    loaded = BooleanField(initial=False, required=False)

    def __init__(self, *args, **kwargs):

        super(MetadataForm, self).__init__(*args, **kwargs)

        # TODO: remove during form refactoring. this is a hack to avoid "None" strings of uncertain origin.
        if self.data != {}:
            for k, v in self.data.iteritems():
                for f in self._fields_none_string_overload:
                    if k.endswith('-'+f) and v == 'None':
                        self.data[k] = None

    def is_loaded(self):
        try:
            loaded = self.get_current_field_value("loaded")
            # True is what it ought to be,
            # "true" is what AJAX converts it to,
            # "on" is what Django seems to be using for some Django-is-stupid reason
            return loaded == True or loaded == "true" or loaded == "on"
        except KeyError:
            return False

    def load(self):
        if self.is_bound:
            self.data[self.add_prefix("loaded")] = True
            try:
                self.cleaned_data["loaded"] = True
            except AttributeError:
                # if I'm here, I can assume form has not yet been validated
                pass
        self.initial["loaded"] = True
        self.fields["loaded"].initial = True

    def _clean_fields(self, loaded=True):
        for name, field in self.fields.items():
            if name == "loaded":
                value = loaded
            else:
                if loaded:
                    # this is the normal behavior (for loaded forms)...
                    value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))
                else:
                    # this is the special behavior (for non-loaded forms)...
                    try:
                        value = self.initial[name]
                    except KeyError:
                        # IN SOME CASES I HAVE TO PASS "None" TO CREATE_<WHATEVER>_INLINEFORMSET_DATA AS THE FK MODEL
                        # THAT IS AS IT SHOULD BE (I EXCLUDE IT FROM model_to_dict ANYWAY)
                        # AND I RESET IT LATER ON IN THE SAVE PROCESS
                        if not isinstance(self.fields[name], InlineForeignKeyField):
                            # TODO: IS THIS REALLY THE CORRECT BEHAVIOR?
                            # TODO: THIS IS HAPPENING FOR "DELETE" FIELD AS WELL
                            # print("IF YOU ARE HERE THEN YOU SHOULD DOUBLE-CHECK WHAT'S GOING ON IN IN MetadataForm._clean_fields()")
                            # print("couldn't find %s in %s" % (name, type(self)))
                            pass
                        value = None
            try:
                if isinstance(field, FileField):
                    initial = self.initial.get(name, field.initial)
                    value = field.clean(value, initial)
                else:
                    value = field.clean(value)
                self.cleaned_data[name] = value
                if hasattr(self, 'clean_%s' % name):
                    value = getattr(self, 'clean_%s' % name)()
                    self.cleaned_data[name] = value
            except ValidationError as e:
                self._errors[name] = self.error_class(e.messages)
                if name in self.cleaned_data:
                    del self.cleaned_data[name]

    def full_clean(self, loaded=True):
        """
        Cleans all of self.data and populates self._errors and
        self.cleaned_data based either on data (for loaded forms - the usual way of doing things)
        or initial (for unloaded forms)
        """
        self._errors = ErrorDict()
        if not self.is_bound:  # Stop further processing.
            return
        self.cleaned_data = {}
        # If the form is permitted to be empty, and none of the form data has
        # changed from the initial data, short circuit any validation.
        if self.empty_permitted and not self.has_changed():
            return
        self._clean_fields(loaded=loaded)
        self._clean_form()
        self._post_clean()

    def is_valid(self, loaded=True):
        """
        Overloads is_valid fn to compute validity based on either data or initial
        (depending on the value of loaded)
        """
        if self._errors is None:
            self.full_clean(loaded=loaded)

        return self.is_bound and not bool(self._errors)

    def get_fields_from_list(self, field_names_list):
        """
        returns the fields corresponding to the names in field_names_list
        note that getting them explicitly as keys is more efficient than looping through self
        :param field_names_list:
        :return: fields corresponding to the names in field_names_list
        """
        fields = [self[field_name] for field_name in field_names_list]
        return fields

    def get_current_field_value(self, *args):
        """
        Return the field value from either "data" or "initial". The key will be reformatted to account for the form
        prefix.

        :param str key:
        :param default: If provided as a second argument, this value will be returned in case of a KeyError.

        >>> self.get_current_field_value('a')
        >>> self.get_current_field_value('a', None)
        """

        if len(args) == 1:
            key = args[0]
            has_default = False
        else:
            key, default = args
            has_default = True

        try:
            if self.prefix:
                key_prefix = '{0}-{1}'.format(self.prefix, key)
                ret = self.data[key_prefix]
            else:  # (the model_customizer_form does not have a prefix)
                ret = self.data[key]
        except KeyError:
            try:
                ret = self.initial[key]
            except KeyError:
                if has_default:
                    ret = default
                else:
                    msg = 'The key "{0}" was not found in "data" or "initial" for form of type {1} with prefix "{2}".'.format(key, type(self), self.prefix)
                    raise KeyError(msg)
        return ret

    def get_id_from_field_name(self, field_name):
        """
        returns the HTML id of the rendered field
        this works w/ bound or unbound fields
        (used by inheritance)
        """

        field_id = self.auto_id % self.add_prefix(field_name)
        return field_id


class MetadataFormSet(BaseModelFormSet):

    def get_loaded_forms(self):
        loaded_forms = []
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            if form.is_loaded():
                loaded_forms.append(form)
        return loaded_forms

    def full_clean(self, loaded_prefixes=[]):
        """
        Cleans all of self.data and populates self._errors and
        self._non_form_errors.
        """
        self._errors = []
        self._non_form_errors = self.error_class()

        if not self.is_bound:  # Stop further processing.
            return
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            prefix = form.prefix

            if form._errors is None:
                if prefix in loaded_prefixes:
                    form.full_clean(loaded=True)
                else:
                    form.full_clean(loaded=False)
            self._errors.append(form._errors)

        try:
            if (self.validate_max and
                self.total_form_count() - len(self.deleted_forms) > self.max_num):
                raise ValidationError(ungettext(
                    "Please submit %d or fewer forms.",
                    "Please submit %d or fewer forms.", self.max_num) % self.max_num,
                    code='too_many_forms',
                )
            # Give self.clean() a chance to do cross-form validation.
            self.clean()
        except ValidationError as e:
            self._non_form_errors = self.error_class(e.messages)

    def is_valid(self, loaded_prefixes=[]):
        """
        Returns True if the forms in the formset are valid
        if 'loaded_prefixes' is not empty, forms w/ those prefixes are validated against data
        while all others are validated against initial
        """

        if not self.is_bound:
            return False

        # We loop over every form.errors here rather than short circuiting on the
        # first failure to make sure validation gets triggered for every specified form
        forms_valid = True
        # RATHER THAN CALL THE errors PROPERTY I REPRODUCE IT'S FUNCTIONALITY
        # HERE SO THAT I CAN PASS loaded_prefixes TO full_clean
        if self._errors is None:
            self.full_clean(loaded_prefixes=loaded_prefixes)

        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            prefix = form.prefix

            if self.can_delete:
                if self._should_delete_form(form):
                    continue

            if prefix in loaded_prefixes:
                forms_valid &= form.is_valid(loaded=True)
            else:
                forms_valid &= form.is_valid(loaded=False)

        return forms_valid and not bool(self.non_form_errors())


class MetadataInlineFormSet(BaseInlineFormSet):

    def get_loaded_forms(self):
        loaded_forms = []
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            if form.is_loaded():
                loaded_forms.append(form)
        return loaded_forms

    def full_clean(self, loaded_prefixes=[]):
        """
        Cleans all of self.data and populates self._errors and
        self._non_form_errors.
        """
        self._errors = []
        self._non_form_errors = self.error_class()

        if not self.is_bound:  # Stop further processing.
            return
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            prefix = form.prefix

            if form._errors is None:
                if prefix in loaded_prefixes:
                    form.full_clean(loaded=True)
                else:
                    form.full_clean(loaded=False)
            self._errors.append(form._errors)

        try:
            if (self.validate_max and
                self.total_form_count() - len(self.deleted_forms) > self.max_num) or \
                self.management_form.cleaned_data["TOTAL_FORMS"] > self.absolute_max:
                raise ValidationError(ungettext(
                    "Please submit %d or fewer forms.",
                    "Please submit %d or fewer forms.", self.max_num) % self.max_num,
                    code='too_many_forms',
                )
            # Give self.clean() a chance to do cross-form validation.
            self.clean()
        except ValidationError as e:
            self._non_form_errors = self.error_class(e.messages)

    def is_valid(self, loaded_prefixes=[]):

        """
        Returns True if the forms in the formset are valid
        if 'loaded_prefixes' is not empty, forms w/ those prefixes are validated against data
        while all others are validated against initial
        """

        if not self.is_bound:
            return False
        # We loop over every form.errors here rather than short circuiting on the
        # first failure to make sure validation gets triggered for every form.
        forms_valid = True
        # RATHER THAN CALL THE errors PROPERTY I REPRODUCE ITS FUNCTIONALITY
        # HERE SO THAT I CAN PASS loaded_prefixes TO full_clean
        if self._errors is None:
            self.full_clean(loaded_prefixes=loaded_prefixes)

        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            prefix = form.prefix

            if self.can_delete:
                if self._should_delete_form(form):
                    continue

            if prefix in loaded_prefixes:
                forms_valid &= form.is_valid(loaded=True)
            else:
                forms_valid &= form.is_valid(loaded=False)

        return forms_valid and not bool(self.non_form_errors())
