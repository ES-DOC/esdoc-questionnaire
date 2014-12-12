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
from django.utils.translation import ungettext
from django.forms.fields import BooleanField, FileField
from django.forms.models import ModelForm, BaseModelFormSet, BaseInlineFormSet
from django.forms.util import ErrorDict


class MetadataForm(ModelForm):

    cached_fields = []

    # these fields raise form validation errors with string Nones
    _fields_none_string_overload = ('id', 'enumeration_value', 'relationship_value')

    loaded = BooleanField(initial=False, required=False)

    def __init__(self, *args, **kwargs):

        super(MetadataForm, self).__init__(*args, **kwargs)

        ## TODO: remove during form refactoring. this is a hack to avoid "None" strings of uncertain origin.
        if self.data != {}:
            for k, v in self.data.iteritems():
                for f in self._fields_none_string_overload:
                    if k.endswith('-'+f) and v == 'None':
                        self.data[k] = None

    def is_loaded(self):
        try:
            loaded = self.get_current_field_value("loaded")
            return loaded == "on" or loaded == True
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
                        # TODO: IS THIS REALLY THE CORRECT BEHAVIOR?
                        # IN SOME CASES I HAVE TO PASS "None" TO CREATE_<WHATEVER>_INLINEFORMSET_DATA AS THE FK MODEL
                        # THAT IS AS IT SHOULD BE (I EXCLUDE IT FROM model_to_dict ANYWAY)
                        # AND I RESET IT LATER ON IN THE SAVE PROCESS
                        try:
                            assert name == "model"
                        except:
                            import ipdb; ipdb.set_trace()
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
        # I _think_ that iterating over self causes _all_ fields to be evaluated
        # which is expensive (especially w/ relationship fields)
        #fields = [field for field in self if field.name in field_names_list]
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

