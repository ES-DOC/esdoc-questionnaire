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
from django.core.files.storage import FileSystemStorage
from django.forms import ValidationError, Select, CharField, MultipleChoiceField
from django.forms.fields import MultiValueField
from django.forms.widgets import MultiWidget
from django.db.models.signals import post_delete
import contextlib
import types
import os
import re

from Q.questionnaire.q_utils import EnumeratedType, EnumeratedTypeList, QError


# these fields are automatically added by MPTT (usually, I want to ignore processing them)
MPTT_FIELDS = ["rght", "lft", "parent", "level", "tree_id"]

#: the bit to add onto a field's choices when an explicit empty choice is required
EMPTY_CHOICE = [("", "---------")]
#: the bit to add onto a field's choices when an explicit NONE choice is required
NULL_CHOICE = [("_NONE", "---NONE---")]
#: the bit to add onto a field's choices when an explicit OTHER choice is required
OTHER_CHOICE = [("_OTHER", "---OTHER---")]

#######################################
# the types of fields used by the CIM #
#######################################

class QPropertyType(EnumeratedType):

    def __unicode__(self):
        return u"%s" % (self.get_type())

QPropertyTypes = EnumeratedTypeList([
    QPropertyType("ATOMIC", "Atomic"),
    QPropertyType("RELATIONSHIP", "Relationship"),
    QPropertyType("ENUMERATION", "Enumeration"),
])

PROPERTY_TYPE_CHOICES = [(pt.get_type(), pt.get_name()) for pt in QPropertyTypes]

class QAtomicPropertyType(EnumeratedType):

    def __unicode__(self):
        return u"%s" % (self.get_type())

QAtomicPropertyTypes = EnumeratedTypeList([
    QAtomicPropertyType("DEFAULT", "Character Field (default)"),
    QAtomicPropertyType("BOOLEAN", "Boolean Field"),
    QAtomicPropertyType("DATE", "Date Field"),
    QAtomicPropertyType("DATETIME", "Date Time Field"),
    QAtomicPropertyType("DECIMAL", "Decimal Field"),
    QAtomicPropertyType("EMAIL", "Email Field"),
    QAtomicPropertyType("INTEGER", "Integer Field"),
    QAtomicPropertyType("TEXT", "Text Field (large block of text as opposed to a small string)"),
    QAtomicPropertyType("TIME", "Time Field"),
    QAtomicPropertyType("URL", "URL Field"),
])

ATOMIC_PROPERTY_TYPE_CHOICES = [(pt.get_type(), pt.get_name()) for pt in QPropertyTypes]

##########################
# fields used by Q forms #
##########################

######################
# enumeration fields #
######################

class EnumerationFormField(MultipleChoiceField):

    def set_choices(self, choices, multi=True):
        """
        explicitly set the choices of this form field
        since this is where I set the widget,
        :param choices: the options to render
        :param multi: boolean indicating whether to allow multiple selections or not
        :return:
        """
        # self._choices = [(choice, choices) for choice in choices]
        self.choices = [(choice, choice) for choice in choices]


class QEnumerationField(models.TextField):
    """
    encodes enumerations as '|' separated text
    """

    def formfield(self, **kwargs):
        new_kwargs = {
            "label": self.verbose_name,
            "required": not self.blank,
            # "form_class": EnumerationFormField,
        }
        new_kwargs.update(kwargs)
        # return super(QEnumerationField, self).formfield(**new_kwargs)
        return EnumerationFormField(**new_kwargs)

    def to_python(self, value):
        """
        db to code; text to list as needed
        """
        if isinstance(value, list):
            return value
        else:
            try:
                return value.split('|')
            except:
                return []

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

    def contribute_to_class(self, cls, name, **kwargs):
        """
        adds "get_<field_name>_value" fns to the class
        :param cls:
        :param name:
        :param kwargs:
        :return:
        """
        super(QEnumerationField, self).contribute_to_class(cls, name, **kwargs)

        def _get_enumeration_value(instance, field_name=name):
            """
            notice how I pass the name of the field from the parent "contribute_to_class" fn;
            this lets me access it from the instance
            :param instance:
            :param field_name:
            :return:
            """
            enumeration_field_value = getattr(instance, field_name)
            return self.to_python(enumeration_field_value)

        get_enumeration_value_fn_name = u"get_{0}_value".format(name)
        setattr(cls, get_enumeration_value_fn_name, types.MethodType(_get_enumeration_value, None, cls))

    def get_enumeration(self):
        pass

##################
# version fields #
##################

class Version(object):

    N_BITS = (8, 8, 16)

    def __init__(self, string):
        self.integer = Version.string_to_int(string)
        self.string = string

    def __str__(self):
        return self.string

    def __int__(self):
        return self.integer

    def __eq__(self, other):
        if not other:
            return False

        if isinstance(other, basestring):
            return self == Version(other)
        else:
            return int(self) == int(other)

    def __gt__(self, other):
        if isinstance(other, basestring):
            other = Version(other)
        return int(self) > int(other)

    def __ge__(self, other):
        if isinstance(other, basestring):
            other = Version(other)
        return int(self) >= int(other)

    def __lt__(self, other):
        if isinstance(other, basestring):
            other = Version(other)
        return int(self) < int(other)

    def __le__(self, other):
        if isinstance(other, basestring):
            other = Version(other)
        return int(self) <= int(other)

    def major(self):
        string = str(self)
        numbers = [int(n) for n in string.split(".")]
        try:
            return numbers[0]
        except IndexError:
            return 0

    def minor(self):
        string = str(self)
        numbers = [int(n) for n in string.split(".")]
        try:
            return numbers[1]
        except IndexError:
            return 0

    def patch(self):
        string = str(self)
        numbers = [int(n) for n in string.split(".")]
        try:
            return numbers[2]
        except IndexError:
            return 0

    def fully_specified(self):
        return "{0}.{1}.{2}".format(
            self.major(),
            self.minor(),
            self.patch(),
        )

    @classmethod
    def string_to_int(cls, string):

        numbers = [int(n) for n in string.split(".")]

        if len(numbers) > len(cls.N_BITS):
            msg = "Versions with more than {0} decimal places are not supported".format(len(Version.N_BITS)-1)
            raise NotImplementedError(msg)

        #  add 0s for missing numbers
        numbers.extend([0] * (len(cls.N_BITS) - len(numbers)))

        #  convert to single int and return
        number = 0
        total_bits = 0
        for n, b in reversed(zip(numbers, cls.N_BITS)):
            max_num = (b+1) - 1
            if n >= 1 << max_num:
                msg = "Number {0} cannot be stored with only {1} bits. Max is {2}".format(n, b, max_num)
                raise ValueError(msg)
            number += n << total_bits
            total_bits += b

        return number

    @classmethod
    def int_to_string(cls, integer):
        number_strings = []
        total_bits = sum(cls.N_BITS)
        for b in Version.N_BITS:
            shift_amount = (total_bits - b)
            number_segment = integer >> shift_amount
            number_strings.append(str(number_segment))
            total_bits = total_bits - b
            integer = integer - (number_segment << shift_amount)

        return ".".join(number_strings)

class QVersionFormField(CharField):

    def clean(self, value):
        # check string format (only numbers and the '.' character

        if not re.match(r'^([0-9]\.?)+$', value):
            msg = "Versions must be of the format 'major.minor.patch'"
            raise ValidationError(msg)

        return value

class QVersionField(models.IntegerField):

    # TODO: models w/ this field have to call refresh_from_db if set manually

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


###########################
# storage for file fields #
###########################

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


####################################################
# allow unsaved models to be assigned as fk fields #
####################################################

# TODO: IS THIS THREAD-SAFE?

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
        # saved = model_field.allow_unsaved_instance_assignment
        # yield
        # model_field.allow_unsaved_instance_assignment = saved
        field_saved_values[model_field] = model_field.allow_unsaved_instance_assignment
        model_field.allow_unsaved_instance_assignment = True

    yield

    for field, saved_value in field_saved_values.iteritems():
        field.allow_unsaved_instance_assignment = saved_value
