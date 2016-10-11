####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

"""
.. module:: q_fields

all of the custom fields used by the questionnaire forms
"""


from django.db import models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.files.storage import FileSystemStorage
from django.forms import ValidationError, CharField
from django.forms.fields import Field, ChoiceField, MultipleChoiceField, MultiValueField
from django.forms.widgets import MultiWidget, Select
from django.forms.widgets import TextInput, CheckboxInput, DateInput, DateTimeInput, NumberInput, EmailInput, Textarea, TimeInput, URLInput
from django.utils.translation import ugettext_lazy as _
from django.forms.utils import flatatt
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.db.models.signals import post_delete
import contextlib
import types
import json
import os
import re

from Q.questionnaire.q_utils import EnumeratedType, EnumeratedTypeList, Version, sort_list_by_key
from Q.questionnaire.q_constants import NIL_PREFIX, NIL_REASONS, HUGE_STRING

#############
# constants #
#############

# these fields are automatically added by MPTT (usually, I want to ignore processing them)
MPTT_FIELDS = ["rght", "lft", "parent", "level", "tree_id"]

##############################################################
# some clever ways of dealing w/ unsaved relationship fields #
##############################################################

@contextlib.contextmanager
def allow_unsaved_fk(model_class, field_names):
    """"
    temporarily allows the fk "model_class.field_name" to point to a model not yet saved in the db
    that used to be the default behavior in Django <= 1.6
    (see https://www.caktusgroup.com/blog/2015/07/28/using-unsaved-related-models-sample-data-django-18/)
    """
    assert isinstance(field_names, list), "allow_unsaved_fk takes a list of fields, not a single field"

    field_saved_values = {}
    for field_name in field_names:
        model_field = model_class._meta.get_field(field_name)
        field_saved_values[model_field] = model_field.allow_unsaved_instance_assignment
        model_field.allow_unsaved_instance_assignment = True

    yield

    for field, saved_value in field_saved_values.iteritems():
        field.allow_unsaved_instance_assignment = saved_value


class QUnsavedManager(models.Manager):
    """
    a manager to cope w/ UNSAVED models being used in m2m fields (actually, it is used w/ the reverse of fk fields)
    (this is not meant to be possible in Django)
    The manager accomplishes this by storing the would-be field content in an instance variable;
    in the case of unsaved models, this is purely done to get around Django ickiness
    in the case of saved models, this is done so that QuerySets are never cloned (which would overwrite in-progress data)
    a side-effect of this technique is that the output of this manager is not chainable;
    but the Q doesn't use standard Django methods for saving models (instead serializing from JSON), so I don't really care
    """

    def get_cached_qs_name(self):
        return "_cached_{0}".format(self.get_real_field_manager().name)

    def get_real_field_manager(self):
        """
        overwrite this as needed for different types of managers
        :return: the _real_ model manager used by this field
        """
        field_name = self.field_name
        return getattr(self.instance, field_name)

    def count(self):
        return len(self.get_query_set())

    def all(self):
        return self.get_query_set()

    def get(self, *args, **kwargs):
        filtered_qs = self.filter_potentially_unsaved(*args, **kwargs)
        n_filtered_qs = len(filtered_qs)
        if n_filtered_qs == 0:
            msg = "{0} matching query does not exist".format(self.model)
            raise ObjectDoesNotExist(msg)
        elif n_filtered_qs > 1:
            msg = "get() returned more than 1 {0} -- it returned {1}!".format(self.model, n_filtered_qs)
            raise MultipleObjectsReturned(msg)
        else:
            return filtered_qs.pop()

    def order_by(self, key, **kwargs):
        cached_qs = self.get_query_set()
        sorted_qs = sorted(
            cached_qs,
            key=lambda o: getattr(o, key),
            reverse=kwargs.pop("reverse", False),
        )
        return sorted_qs

    def get_query_set(self):
        instance = self.instance
        cached_qs_name = self.get_cached_qs_name()
        if not hasattr(instance, cached_qs_name):
            field_manager = self.get_real_field_manager()
            saved_qs = field_manager.all()
            unsaved_qs = []
            cached_qs = list(saved_qs) + unsaved_qs
            setattr(instance, cached_qs_name, cached_qs)
        return getattr(instance, cached_qs_name)

    # unlike the above fns, I cannot simply overload the 'add' or 'remove' fns
    # b/c managers are created dynamically in "django.db.models.fields.related.py#create_foreign_related_manager"
    # Django is annoying

    def add_potentially_unsaved(self, *objs):
        instance = self.instance
        cached_qs = self.get_query_set()
        objs = list(objs)

        unsaved_objs = [o for o in objs if o.pk is None or instance.pk is None]  # (unsaved can refer to either the models to add or the model to add to)
        saved_objs = [o for o in objs if o not in unsaved_objs]

        for obj in objs:
            if not isinstance(obj, self.model):
                raise TypeError("'%s' instance expected, got %r" % (self.model._meta.object_name, obj))
            if obj not in cached_qs:
                cached_qs.append(obj)
        setattr(
            instance,
            self.get_cached_qs_name(),
            cached_qs,
        )

        # even though I am not saving models w/ these custom managers in the normal Django way,
        # I go ahead and add what I can using normal Django methods (just to avoid any confusion later)...
        if saved_objs:
            self.add(*saved_objs)

    def remove_potentially_unsaved(self, *objs):
        instance = self.instance
        cached_qs = self.get_query_set()
        objs = list(objs)

        unsaved_objs = [o for o in objs if o.pk is None or instance.pk is None]  # (unsaved can refer to either the models to add or the model to add to)
        saved_objs = [o for o in objs if o not in unsaved_objs]

        for obj in objs:
            cached_qs.remove(obj)
        setattr(
            instance,
            self.get_cached_qs_name(),
            cached_qs,
        )

        # even though I am not saving models w/ these custom managers in the normal Django way,
        # I go ahead and remove what I can using normal Django methods (just to avoid any confusion later)...
        if saved_objs:
            self.remove(*saved_objs)

    # and I have to define filter separately, b/c the parent 'filter' fn is used internally by other code

    def filter_potentially_unsaved(self, *args, **kwargs):
        cached_qs = self.get_query_set()
        filtered_qs = filter(
            lambda o: all([getattr(o, key) == value for key, value in kwargs.items()]),
            cached_qs
        )
        return filtered_qs


class QUnsavedRelatedManager(QUnsavedManager):

    use_for_related_fields = True

    def get_real_field_manager(self):
        """
        overwritten from parent manager class
        :return:
        """
        related_field = self.model.get_field(self.field_name).related
        related_field_name = related_field.name
        return getattr(self.instance, related_field_name)


#######################################
# the types of fields used by the CIM #
#######################################

class QPropertyType(EnumeratedType):

    def __str__(self):
        return "{0}".format(self.get_type())

QPropertyTypes = EnumeratedTypeList([
    QPropertyType("ATOMIC", "Atomic"),
    QPropertyType("RELATIONSHIP", "Relationship"),
    QPropertyType("ENUMERATION", "Enumeration"),
])


class QAtomicPropertyType(EnumeratedType):

    def __str__(self):
        return "{0}".format(self.get_type())

QAtomicPropertyTypes = EnumeratedTypeList([
    QAtomicPropertyType("DEFAULT", "Character Field (default)"),
    QAtomicPropertyType("BOOLEAN", "Boolean Field"),
    QAtomicPropertyType("DATE", "Date Field"),
    # TODO: GET TIME FIELDS WORKING IN BOOTSTRAP
    QAtomicPropertyType("DATETIME", "Date Time Field"),
    QAtomicPropertyType("DECIMAL", "Decimal Field"),
    QAtomicPropertyType("EMAIL", "Email Field"),
    QAtomicPropertyType("INTEGER", "Integer Field"),
    QAtomicPropertyType("TEXT", "Text Field (large block of text as opposed to a small string)"),
    # TODO: GET TIME FIELDS WORKING IN BOOTSTRAP
    QAtomicPropertyType("TIME", "Time Field"),
    QAtomicPropertyType("URL", "URL Field"),
])


# I want some of these custom atomic widgets to look pretty in Bootstrap
# so overload their rendering methods as needed...

class QDateInput(DateInput):
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_text(self._format_value(value))
        final_attrs.update({
            "uib-datapicker-popup": True,
            "is-open": "display_datepicker",
        })
        rendered_html = format_html(_(
            "<div class='input-group'>"
                "<input{} />"
                "<span class='input-group-button'>"
                    "<button type='button' class='btn btn-default' ng-click='display_datepicker = true' ng-disabled='current_model.is_nil'>"
                        "<span class='glyphicon glyphicon-calendar'/>"
                    "</button>"
                "</span>"
            "</div>"),
            flatatt(final_attrs)
        )
        return rendered_html

# TODO: GET THIS WORKING IN BOOTSTRAP
# MADE AN EXECUTIVE DECISION NOT TO SUPPORT TIME FIELDS FOR NOW
# class QTimeInput(TimeInput):
#     def render(self, name, value, attrs=None):
#         if value is None:
#             value = ''
#         final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
#         if value != '':
#             # Only add the 'value' attribute if a value is non-empty.
#             final_attrs['value'] = force_text(self._format_value(value))
#         rendered_html = format_html(_(
#             "<uib-timepicker hour-step='timepicker_hour_step' minute-step='timepicker_minute_step' show-meridian='timepicker_show_meridian' {} />"),
#             flatatt(final_attrs)
#         )
#         return rendered_html
#


from Q.questionnaire.q_constants import DATE_FORMAT_JS
from datetime import datetime
class QDateTimeInput(DateTimeInput):
    def render(self, name, value, attrs=None):
        if value is None:
            value = datetime.now()
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        final_attrs['value'] = force_text(self._format_value(value))

        rendered_html = format_html(
            "<datetimepicker ng-model='current_model' date-format='{0}'></datepicker>".format(DATE_FORMAT_JS),
            flatatt(final_attrs)
        )
        return rendered_html

#     def render(self, name, value, attrs=None):
#         if value is None:
#             value = ''
#         final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
#         if value != '':
#             # Only add the 'value' attribute if a value is non-empty.
#             final_attrs['value'] = force_text(self._format_value(value))
#         rendered_html = format_html(_(
#             "<uib-timepicker hour-step='timepicker_hour_step' minute-step='timepicker_minute_step' show-meridian='timepicker_show_meridian' {} />"),
#             flatatt(final_attrs)
#         )
#         return rendered_html

ATOMIC_PROPERTY_MAP = {
    # maps the above QAtomicPropertyTypes to their corresponding widget classes,
    # to be used by "forms/forms_edit_properties.py#customize"
    QAtomicPropertyTypes.DEFAULT.get_type(): [TextInput, {}],
    QAtomicPropertyTypes.BOOLEAN.get_type(): [CheckboxInput, {}],
    QAtomicPropertyTypes.DATE.get_type(): [QDateInput, {}],
    # TODO: GET THIS WORKING IN BOOTSTRAP
    QAtomicPropertyTypes.DATETIME.get_type(): [QDateTimeInput, {}],
    QAtomicPropertyTypes.DECIMAL.get_type(): [NumberInput, {}],
    QAtomicPropertyTypes.EMAIL.get_type(): [EmailInput, {}],
    QAtomicPropertyTypes.INTEGER.get_type(): [NumberInput, {}],
    QAtomicPropertyTypes.TEXT.get_type(): [Textarea, {}],  # "cols": "60", "rows": "4", }],
    # TODO: GET THIS WORKING IN BOOTSTRAP
    # MADE AN EXECUTIVE DECISION NOT TO SUPPORT TIME FIELDS FOR NOW
    # QAtomicPropertyTypes.TIME.get_type(): [QTimeInput, {}],
    QAtomicPropertyTypes.URL.get_type(): [URLInput, {}],
}


###################
# nillable fields #
###################

class QNillableType(EnumeratedType):

    def __str__(self):
        return self.get_name()

QNillableTypes = EnumeratedTypeList([
    QNillableType(nil_reason[0].upper(), "{0}:{1}".format(NIL_PREFIX, nil_reason[0]), nil_reason[1])
    for nil_reason in NIL_REASONS
])

######################
# enumeration fields #
######################

ENUMERATION_TITLE_LIMIT = 2
ENUMERATION_OTHER_PREFIX = "other"
ENUMERATION_OTHER_CHOICE = ("_OTHER", "---OTHER---")
ENUMERATION_OTHER_PLACEHOLDER_TEXT = "Please enter a custom value"
ENUMERATION_OTHER_DOCUMENTATION = "<em>Select this option to add a custom value for this property.</em>"


class QEnumerationFormField(MultipleChoiceField):

    def __init__(self, *args, **kwargs):
        multiple = kwargs.pop("multiple", False)
        complete_choices = kwargs.pop("complete_choices", [])

        choices = [(c.get("value"), c.get("name")) for c in complete_choices]
        choices_documentation = [c.get("documentation") for c in complete_choices]

        kwargs["choices"] = choices
        super(QEnumerationFormField, self).__init__(*args, **kwargs)

        self.complete_choices = complete_choices
        self.choices_documentation = choices_documentation
        self.is_multiple = multiple

    def set_cardinality(self, min, max):
        # like set_cardinality below except called by QPropertyRealizationForm.__init__
        self.required = min != 0
        self.is_multiple = max == '*'

    def set_complete_choices(self, complete_choices):
        self.complete_choices = complete_choices
        self.choices = [(c.get("value"), c.get("name")) for c in complete_choices]
        self.choices_documentation = [c.get("documentation") for c in complete_choices]

    def add_complete_choice(self, choice, documentation=None):
        self.complete_choices.append({
            "value": choice[0],
            "name": choice[1],
            "documentation": documentation,
            "order": len(self.complete_choices) + 1,
        })
        self.choices.append(choice)
        self.choices_documentation.append(documentation)

    def get_complete_choices(self):
        return json.dumps(self.complete_choices)

    def get_is_multiple(self):
        # (recall that this is called in the context of JS, so I am using "true" & "false" instead of True & False
        # return self.is_multiple
        if self.is_multiple:
            return "true"
        else:
            return "false"


class QEnumerationField(models.TextField):
    """
    encodes enumerations as '|' separated text
    internally keeps track of "choices" and "complete_choices"
    the former mimics the normal Django field argument;
    the latter includes documentation as well and gets passed to Bootstrap via the ng "enumeration" directive
    (from the formfield above)
    """

    _SEPARATOR = '|'

    def get_initial_choices(self):
        raise NotImplementedError("I should not call this fn")

    def __init__(self, *args, **kwargs):
        super(QEnumerationField, self).__init__(*args, **kwargs)
        self._min = 0
        self._max = 1
        self._complete_choices = []
        self._choices = []
        self._choices_documentation = []

    def set_cardinality(self, min, max):
        self._min = min
        self._max = max

    def set_choices(self, complete_choices):
        self._complete_choices = complete_choices
        self._choices = [(c.get("value"), c.get("name")) for c in complete_choices]
        self._choices_documentation = [c.get("documentation") for c in complete_choices]

    def formfield(self, **kwargs):

        new_kwargs = {
            "label": self.verbose_name,
            "required": self._min != 0,
            "multiple": self._max == '*',
            "complete_choices": self._complete_choices,
        }
        new_kwargs.update(kwargs)

        return QEnumerationFormField(**new_kwargs)

    def to_python(self, value):
        """
        db to code; text to list as needed
        """
        if isinstance(value, list):
            return value
        else:
            return filter(bool, value.split('|'))  # this funny code prevents lists w/ empty content
            # try:
            #     return value.split('|')
            # except:
            #     return []

    def get_prep_value(self, value):
        """
        code to db; list to text as needed
        """
        if isinstance(value, basestring):
            return value
        elif isinstance(value, list):
            return "|".join(value)

    def from_db_value(self, value, expression, connection, context):
        """
        does the same thing as "to_python",
        it's just called in different situations b/c of a quirk w/ Django 1.8
        (see https://docs.djangoproject.com/en/1.8/howto/custom-model-fields/)
        """
        return self.to_python(value)


# structure of enumerations JSON is:
# [ {"value": "value", "name": "name", "documentation": "documentation", "order", order}]

ENUMERATION_KEYS = ["value", "name", "documentation", "order" ]


class QJSONField(models.TextField):
    """
    encodes enumerations as JSON objects
    used for proxies
    """

    def to_python(self, value):
        """
        db to code; text to JSON object
        """
        if not value:
            return None
        try:
            # sometimes it's not _clean_ JSON
            # (for example, fixtures pollute these strings w/ unicode garbage)
            # so clean it up here
            clean_value = re.sub(r"(u')(.*?)(')", r'"\2"', value)
            return json.loads(clean_value)
        except ValueError:
            msg = "Invalid JSON used in QEnumerationField: '{0}'".format(clean_value)
            raise ValidationError(msg)

    def get_prep_value(self, value):
        """
        code to db; JSON to text
        """
        if not value:
            return None
        try:
            assert isinstance(value, list)
            for member in value:
                assert set(member.keys()) == set(ENUMERATION_KEYS)
        except AssertionError:
            msg = "Invalid JSON used in QEnumerationField: '{0}'".format(value)
            raise ValidationError(msg)

        return json.dumps(value)

    def from_db_value(self, value, expression, connection, context):
        """
        does the same thing as "to_python",
        it's just called in different situations b/c of a quirk w/ Django 1.8
        (see https://docs.djangoproject.com/en/1.8/howto/custom-model-fields/)
        """
        return self.to_python(value)

    def contribute_to_class(self, cls, name, **kwargs):
        """
        adds "get_<field_name>_members" fns to the class,
        which sort the members by "order"
        :param cls:
        :param name:
        :param kwargs:
        :return:
        """
        super(QJSONField, self).contribute_to_class(cls, name, **kwargs)

        def _get_members(instance, field_name=name):
            """
            notice how I pass the name of the field from the parent "contribute_to_class" fn;
            this lets me access it from the instance
            :param instance:
            :param field_name:
            :return:
            """
            return sort_list_by_key(
                getattr(instance, field_name),
                key_name="order",
            )

        get_enumeration_value_fn_name = u"get_{0}_members".format(name)
        setattr(cls, get_enumeration_value_fn_name, types.MethodType(_get_members, None, cls))


##################
# version fields #
##################

class QVersionFormField(CharField):

    def clean(self, value):
        # check string format (only numbers and the '.' character

        if not re.match(r'^([0-9]\.?)+$', value):
            msg = "Versions must be of the format 'major.minor.patch'"
            raise ValidationError(msg)

        return value


class QVersionField(models.IntegerField):

    # TODO: models w/ this field have to call refresh_from_db if set manually
    # TODO: (ie: if set in tests)

    def formfield(self, **kwargs):
        default_kwargs = {
            "form_class": QVersionFormField,
        }
        default_kwargs.update(kwargs)
        return super(QVersionField, self).formfield(**default_kwargs)

    def to_python(self, value):
        """
        db to code; int to Version
        """
        if isinstance(value, Version):
            return value

        if isinstance(value, basestring):
            return Version(value)

        if value is None:
            return None

        return Version(Version.int_to_string(value))

    def get_prep_value(self, value):
        """
        code to db; Version to int
        """
        if isinstance(value, basestring):
            return Version.string_to_int(value)

        if value is None:
            return None

        return int(value)

    def from_db_value(self, value, expression, connection, context):
        """
        does the same thing as "to_python",
        it's just called in different situations b/c of a quirk w/ Django 1.8
        (see https://docs.djangoproject.com/en/1.8/howto/custom-model-fields/)
        """
        return self.to_python(value)

    def contribute_to_class(self, cls, name, **kwargs):
        """
        adds "get/<field_name>_major/minor/patch" fns to the class
        :param cls:
        :param name:
        :param kwargs:
        :return:
        """
        super(QVersionField, self).contribute_to_class(cls, name, **kwargs)

        def _get_major(instance, field_name=name):
            """
            notice how I pass the name of the field from the parent "contribute_to_class" fn;
            this lets me access it from the instance
            :param instance:
            :param field_name:
            :return:
            """
            version_value = getattr(instance, field_name)
            return version_value.major()

        def _get_minor(instance, field_name=name):
            """
            notice how I pass the name of the field from the parent "contribute_to_class" fn;
            this lets me access it from the instance
            :param instance:
            :param field_name:
            :return:
            """
            version_value = getattr(instance, field_name)
            return version_value.minor()

        def _get_patch(instance, field_name=name):
            """
            notice how I pass the name of the field from the parent "contribute_to_class" fn;
            this lets me access it from the instance
            :param instance:
            :param field_name:
            :return:
            """
            version_value = getattr(instance, field_name)
            return version_value.patch()

        get_major_fn_name = u"get_{0}_major".format(name)
        get_minor_fn_name = u"get_{0}_minor".format(name)
        get_patch_fn_name = u"get_{0}_patch".format(name)
        setattr(cls, get_major_fn_name, types.MethodType(_get_major, None, cls))
        setattr(cls, get_minor_fn_name, types.MethodType(_get_minor, None, cls))
        setattr(cls, get_patch_fn_name, types.MethodType(_get_patch, None, cls))


######################
# cardinality fields #
######################

MIN_CHOICES = [(str(i), str(i)) for i in range(0, 11)]
MAX_CHOICES = [('*', '*')] + [(str(i), str(i)) for i in range(0, 11)][1:]


class QCardinalityFormFieldWidget(MultiWidget):

    def __init__(self, *args, **kwargs):
        widgets = (
            Select(choices=MIN_CHOICES),
            Select(choices=MAX_CHOICES),
        )
        super(QCardinalityFormFieldWidget, self).__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        if value:
            return value.split("|")
        else:
            return [u'', u'']


class QCardinalityFormField(MultiValueField):

    def __init__(self, *args, **kwargs):
        fields = (
            CharField(max_length=2),
            CharField(max_length=2),
        )
        widget = QCardinalityFormFieldWidget()
        super(QCardinalityFormField, self).__init__(fields, widget, *args, **kwargs)
        self.widget = widget

    def compress(self, data_list):
        return "|".join(data_list)

    def clean(self, value):

        _min = value[0]
        _max = value[1]

        if not _min and not _max:
            return "|"

        _min_choice_keys = [choice[0] for choice in MIN_CHOICES]
        _max_choice_keys = [choice[0] for choice in MAX_CHOICES]
        if _min not in _min_choice_keys or _max not in _max_choice_keys:
            msg = "Invalid min/max chosen."
            raise ValidationError(msg)

        if (_min > _max) and (_max != "*"):
            msg = "Min must be less than or equal to max."
            raise ValidationError(msg)

        return "|".join([_min, _max])


class QCardinalityField(models.CharField):

    default_max_length = 8
    default_value = "0|1"

    def formfield(self, **kwargs):
        return QCardinalityFormField(label=self.verbose_name.capitalize())

    def __init__(self, *args, **kwargs):

        max_length = kwargs.pop("max_length", self.default_max_length)
        default_value = kwargs.pop("default", self.default_value)

        kwargs.update({
            "max_length": max_length,
            "default": default_value
        })

        super(QCardinalityField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        if type(value) is list:
            return "|".join(value)
        else:
            return value

    def contribute_to_class(self, cls, name, **kwargs):
        """
        adds "get/set_<field_name>_min/max" fns to the class
        :param cls:
        :param name:
        :param kwargs:
        :return:
        """
        super(QCardinalityField, self).contribute_to_class(cls, name, **kwargs)

        def _get_min(instance, field_name=name):
            """
            notice how I pass the name of the field from the parent "contribute_to_class" fn;
            this lets me access it from the instance
            :param instance:
            :param field_name:
            :return:
            """
            cardinality_field_value = getattr(instance, field_name)
            _min, _max = cardinality_field_value.split("|")
            return _min

        def _get_max(instance, field_name=name):
            """
            notice how I pass the name of the field from the parent "contribute_to_class" fn;
            this lets me access it from the instance
            :param instance:
            :param field_name:
            :return:
            """
            cardinality_field_value = getattr(instance, field_name)
            _min, _max = cardinality_field_value.split("|")
            return _max

        def _set_min(instance, value, field_name=name):
            """
            notice how I pass the name of the field from the parent "contribute_to_class" fn;
            this lets me access it from the instance
            :param instance:
            :param field_name:
            :return:
            """
            cardinality_field_value = getattr(instance, field_name)
            _min, _max = cardinality_field_value.split("|")
            setattr(instance, field_name, u"%s|%s" % (str(value), _max))

        def _set_max(instance, value, field_name=name):
            """
            notice how I pass the name of the field from the parent "contribute_to_class" fn;
            this lets me access it from the instance
            :param instance:
            :param field_name:
            :return:
            """
            cardinality_field_value = getattr(instance, field_name)
            _min, _max = cardinality_field_value.split("|")
            setattr(instance, field_name, u"%s|%s" % (_min, str(value)))

        get_min_fn_name = u"get_{0}_min".format(name)
        get_max_fn_name = u"get_{0}_max".format(name)
        set_min_fn_name = u"set_{0}_min".format(name)
        set_max_fn_name = u"set_{0}_max".format(name)
        setattr(cls, get_min_fn_name, types.MethodType(_get_min, None, cls))
        setattr(cls, get_max_fn_name, types.MethodType(_get_max, None, cls))
        setattr(cls, set_min_fn_name, types.MethodType(_set_min, None, cls))
        setattr(cls, set_max_fn_name, types.MethodType(_set_max, None, cls))


###############
# list fields #
###############

# LIST_DEFAULT_TOKEN = '|'
# LIST_DEFAULT_CARDINALITY = u"0|1"
# LIST_DEFAULT_MAX = 10
# LIST_DEFAULT_WIDGET = CharField
#
# class QListFormFieldWidget(MultiWidget):
#
#     def __init__(self, *args, **kwargs):
#         widget_class = kwargs.pop("widget")
#         cardinality = kwargs.pop("cardinality")
#         self.min, self.max = [int(m) for m in cardinality.split('|')]
#         widgets = (
#             widget_class()
#             for i in range(self.min, self.max)
#         )
#         super(QListFormFieldWidget, self).__init__(widgets, *args, **kwargs)
#
#     def decompress(self, value):
#         if value:
#             return value.split('|')
#         else:
#             return None
#
#
# class QListFormField(MultiValueField):
#
#     def __init__(self, *args, **kwargs):
#         widget_class = kwargs.pop("widget")
#         cardinality = kwargs.pop("cardinality")
#         self.token = kwargs.pop("token")
#         self.min, self.max = [int(m) for m in cardinality.split('|')]
#         fields = (
#             widget_class()
#             for i in range(self.min, self.max)
#         )
#         widget = QListFormFieldWidget()
#         super(QListFormField, self).__init__(fields, widget, *args, **kwargs)
#         self.widget = widget
#
#     def compress(self, data_list):
#         return self.token.join(data_list)
#
#     def clean(self, value):
#
#         for i in range(self.min, self.max):
#             if self.token in value[i]:
#                 msg = "Invalid character ('%s') in list item." % self.token
#                 raise ValidationError(msg)
#
#         return self.token.join(value)
#
#
# class QListField(models.TextField):
#
#     def formfield(self, **kwargs):
#         return QListFormField(label=self.verbose_name.capitalize(),
#                               widget_class=self.widget_class,
#                               cardinality=u"%s|%s" % (self.min, self.max)
#                               )
#
#     def __init__(self, *args, **kwargs):
#
#         token = kwargs.pop("token", LIST_DEFAULT_TOKEN)
#         widget_class = kwargs.pop("widget_class", LIST_DEFAULT_WIDGET)
#         cardinality = kwargs.pop("cardinality", LIST_DEFAULT_CARDINALITY)
#         _min, _max = cardinality.split('|')
#
#         super(QListField, self).__init__(*args, **kwargs)
#
#         self.token = token
#         self.widget_class = widget_class
#         self.min = int(_min)
#         if max == '*':
#             self.max = LIST_DEFAULT_MAX
#         else:
#             self.max = int(_max)
#             if self.max > LIST_DEFAULT_MAX:
#                 msg = u"Invalid number of list items."
#                 raise QError(msg)
#
#     def get_prep_value(self, value):
#         if type(value) is list:
#             return self.token.join(value)
#         else:
#             return value


###############
# file fields #
###############

class OverwriteStorage(FileSystemStorage):

    def get_available_name(self, name):
        """Returns a filename that's free on the target storage system, and
        available for new content to be written to.

        Found at http://djangosnippets.org/snippets/976/

        This file storage solves overwrite on upload problem. Another
        proposed solution was to override the save method on the model
        like so (from https://code.djangoproject.com/ticket/11663):

        def save(self, *args, **kwargs):
            try:
                this = MyModelName.objects.get(id=self.id)
                if this.MyImageFieldName != self.MyImageFieldName:
                    this.MyImageFieldName.delete()
            except: pass
            super(MyModelName, self).save(*args, **kwargs)
        """
        # If the filename already exists, remove it as if it was a true file system
        if self.exists(name):
            file_path = os.path.join(settings.MEDIA_ROOT, name)
            os.remove(file_path)
        return name


class QFileField(models.FileField):
    """
    just like a standard Django FileField,
    except it uses the above OverwriteStorage class,
    and it deletes the file when the corresponding class instance is deleted
    (so long as no other class members are using it)
    """

    default_help_text = "Note that files with the same names will be overwritten"

    def __init__(self, *args, **kwargs):
        """
        ensure that OverwriteStorage is used,
        and provide help_text (if none was specified)
        :param args:
        :param kwargs:
        :return:
        """

        help_text = kwargs.pop("help_text", self.default_help_text)
        kwargs.update({
            "storage": OverwriteStorage(),
            "help_text": help_text
        })
        super(QFileField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        """
        attach the "post_delete" signal of the model class
        to the "delete_file" fn of the field class
        :param cls:
        :param name:
        :return: None
        """
        super(QFileField, self).contribute_to_class(cls, name, **kwargs)
        post_delete.connect(self.delete_file, sender=cls)

    def delete_file(self, sender, **kwargs):
        """
        delete the file iff no other class instance point to it
        :param sender:
        :return: None
        """
        instance = kwargs.pop("instance")
        instance_field_name = self.name
        instance_field = getattr(instance, instance_field_name)
        filter_parameters = {
            instance_field_name: instance_field.name,
        }
        other_instances_with_same_file = sender.objects.filter(**filter_parameters)
        if not len(other_instances_with_same_file):
            # if there are no other instances w/ the same file...
            # delete the file...
            instance_field.delete(save=False)  # save=False prevents model from re-saving itself
