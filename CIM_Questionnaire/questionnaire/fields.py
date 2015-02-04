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
.. module:: questionnaire_fields

Special fields used for CIM Questionnaire
"""

from django.conf import settings
from django.db import models
from django.db.models.fields import smart_text
from django.forms import Select, SelectMultiple, ValidationError, ModelChoiceField
from django.forms import CheckboxInput, DateInput, DateTimeInput, NumberInput, EmailInput, Textarea, TextInput, TimeInput, URLInput
from django.forms.fields import CharField, MultipleChoiceField, MultiValueField
from django.forms.widgets import MultiWidget
from django.forms.models import ModelChoiceIterator
from django.core.files.storage import FileSystemStorage

from south.modelsinspector import introspector

import os

from CIM_Questionnaire.questionnaire.utils import EnumeratedType, EnumeratedTypeList, BIG_STRING

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
            print "deleted existing %s file" % file_path
        return name

######################
# enumeration fields #
######################

EMPTY_CHOICE = [("", "----------")]
NULL_CHOICE = [("_NONE", "---NONE---")]
OTHER_CHOICE = [("_OTHER", "---OTHER---")]


class EnumerationFormField(MultipleChoiceField):

    def set_choices(self, choices, multi=True):
        self._choices = choices
        if multi:
            self.widget = SelectMultiple(choices=choices)
        else:
            self.widget = Select(choices=choices)

    def clean(self, value):

        # if this is _not_ a multi enumeration,
        # then the value will be a single string rather than a list;
        # (this is why I am explicitly calling to_python - see note below)
        value = self.to_python(value)

        # an enumeration can be invalid in 2 ways:
        # 1) specifying a value other than that provided by choices (choices is set during form initialization)
        # 2) not specifying a value when field is required

        if any(value):
            # this block is mostly taken from the super validate() fn
            for val in value:
                if not self.valid_value(val):
                    msg = "Select a valid choice, '%s' is not among the available choices" % val
                    raise ValidationError(msg)
            self.run_validators(value)
        elif self.required:
            # this block is here in-case there is any special processing I need to do b/c of customizers
            raise ValidationError(self.error_messages["required"])
        else:
            value = []
            
        return value

    def to_python(self, value):
        """
        need to override this b/c this form field is based on a MultipleChoiceField
        which uses the SelectMultiple widget by default (which provides lists on the clean callback)
        but it uses the Select widget if the customizer/proxy specifies it should not be multiple
        in this case it provides a string on the clean callback; I need to change that to a list
        :param value:
        :return:
        """
        if type(self.widget) == SelectMultiple:  # multi

            # this code taken from MultipleChoiceField.to_python ("django/forms/fields.py")
            if not value:
                return []
            elif not isinstance(value, (list, tuple)):
                raise ValidationError(self.error_messages['invalid_list'], code='invalid_list')
            return [smart_text(val) for val in value]

        else:  # not multi

            # this code _not_ taken from ChoiceField.to_python (since I want it to return a list)
            if value in self.empty_values:
                return []
            return [smart_text(value)]


class EnumerationField(models.TextField):

    def formfield(self, **kwargs):
        new_kwargs = {
            "label": self.verbose_name.capitalize(),
            "required": not self.blank,
            #"choices": self.get_enumeration(),
            "form_class": EnumerationFormField,
        }
        new_kwargs.update(kwargs)
        return super(EnumerationField,self).formfield(**new_kwargs)


#    def get_enumeration(self):
#        return self.enumeration
#
#    def set_enumeration(self,choices):
#        self.enumeration = [(slugify(choice),choice) for choice in choices]

    def get_db_prep_value(self, value, connection, prepared=False):
        if isinstance(value, basestring):
            return value
        elif isinstance(value, list):
            return "|".join(value)

    def to_python(self, value):
        if isinstance(value, list):
            return value
        else:
            try:
                return value.split("|")
            except:
                return []

    def south_field_triple(self):
        field_class_path = self.__class__.__module__ + "." + self.__class__.__name__
        args, kwargs = introspector(self)
        return (field_class_path, args, kwargs)

######################
# cardinality fields #
######################

MIN_CHOICES = [(str(i), str(i)) for i in range(0, 11)]
MAX_CHOICES = [('*', '*')]+[(str(i), str(i)) for i in range(0, 11)][1:]


class CardinalityFormFieldWidget(MultiWidget):

    def __init__(self, *args, **kwargs):
        widgets = (
            Select(choices=MIN_CHOICES),
            Select(choices=MAX_CHOICES),
        )
        super(CardinalityFormFieldWidget, self).__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        if value:
            return value.split("|")
        else:
            return [u'', u'']


class CardinalityFormField(MultiValueField):

    def __init__(self, *args, **kwargs):
        fields = (
            CharField(max_length=2),
            CharField(max_length=2)
        )
        widget = CardinalityFormFieldWidget()
        super(CardinalityFormField, self).__init__(fields, widget, *args, **kwargs)
        self.widget = widget

    def compress(self, data_list):
        return "|".join(data_list)

    def clean(self, value):

        _min = value[0] or ""
        _max = value[1] or ""

        _min_choice_keys = [choice[0] for choice in MIN_CHOICES]
        _max_choice_keys = [choice[0] for choice in MAX_CHOICES]
        if _min not in _min_choice_keys or _max not in _max_choice_keys:
            msg = "Invalid min/max chosen."
            raise ValidationError(msg)

        if (_min > _max) and (_max != "*"):
            msg = "Min must be less than or equal to max."
            raise ValidationError(msg)

        return "|".join([_min, _max])


class CardinalityField(models.CharField):

    def formfield(self, **kwargs):
        return CardinalityFormField(label=self.verbose_name.capitalize())

    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 8

        super(CardinalityField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        if type(value) is list:
            return "|".join(value)
        else:
            return value
            
    def south_field_triple(self):
        field_class_path = self.__class__.__module__ + "." + self.__class__.__name__
        args, kwargs = introspector(self)
        return (field_class_path, args, kwargs)


# TODO: ARE THESE CACHED FIELD CLASSES BEING USED?
class CachedModelChoiceIterator(ModelChoiceIterator):

    def __init__(self, field):
        super(CachedModelChoiceIterator, self).__init__(field)

    def __iter__(self):
        if self.field.empty_label is not None:
            yield (u"", self.field.empty_label)
        if self.field.cache_choices:
            if self.field.choice_cache is None:
                self.field.choice_cache = [
                    self.choice(obj) for obj in self.queryset.all()
                ]
            for choice in self.field.choice_cache:
                yield choice
        else:
            # here is the changed bit
            # for obj in self.queryset.all();
            for obj in self.queryset:
                yield self.choice(obj)


class CachedModelChoiceField(ModelChoiceField):
    # only purpose of this class is to use a non-standard ModelChoiceIterator (above)
    # see [http://stackoverflow.com/a/8211123]

    def __init__(self, *args, **kwargs):
        super(CachedModelChoiceField, self).__init__(*args, **kwargs)

    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices

        return CachedModelChoiceIterator(self)

    choices = property(_get_choices, ModelChoiceField._set_choices)

# TODO: CachedModelMultipleChoiceField?


class MetadataFieldType(EnumeratedType):
    pass

MetadataFieldTypes = EnumeratedTypeList([
    MetadataFieldType("ATOMIC", "Atomic"),
    MetadataFieldType("RELATIONSHIP", "Relationship"),
    MetadataFieldType("ENUMERATION", "Enumeration"),
    MetadataFieldType("PROPERTY", "Property"),
])


class MetadataUnitType(EnumeratedType):
    pass

MetadataUnitTypes = EnumeratedTypeList([
    MetadataUnitType("X","x"),
])


# SEE COMMENT BELOW

class MetadataAtomicFieldType(EnumeratedType):
    pass

MetadataAtomicFieldTypes = EnumeratedTypeList([
    MetadataAtomicFieldType("DEFAULT", "Character Field (default)"),
    MetadataAtomicFieldType("BOOLEAN", "Boolean Field"),
    MetadataAtomicFieldType("DATE", "Date Field"),
    MetadataAtomicFieldType("DATETIME", "Date Time Field"),
    MetadataAtomicFieldType("DECIMAL", "Decimal Field"),
    MetadataAtomicFieldType("EMAIL", "Email Field"),
    MetadataAtomicFieldType("INTEGER", "Integer Field"),
    MetadataAtomicFieldType("TEXT", "Text Field (large block of text as opposed to a small string)"),
    MetadataAtomicFieldType("TIME", "Time Field"),
    MetadataAtomicFieldType("URL", "URL Field"),
])

METADATA_ATOMICFIELD_MAP = {
    "DEFAULT": [TextInput, {}],
    "BOOLEAN": [CheckboxInput, {}],
    "DATE": [DateInput, {}],
    "DATETIME": [DateTimeInput, {}],
    "DECIMAL": [NumberInput, {}],
    "EMAIL": [EmailInput, {}],
    "INTEGER": [NumberInput, {}],
    "TEXT": [Textarea, {}],  # "cols": "60", "rows": "4", }],
    "TIME": [TimeInput, {}],
    "URL": [URLInput, {}],
}

# NOTE THAT I AM NO LONGER USING MOST OF THIS CODE BELOW
# HARD-CODING CIM MODEL FIELDS IS DEPRACATED
# IN FAVOR OF REGISTERING THEM FROM A CONFIGURATION FILE
# THE CODE ABOVE FILLS THE VOID

#############################################################
# the set of customizable atomic fields for metadata models #
# each item consists of a name, a corresponding class,      #
# and a set of default kwargs required for that class.      #
#############################################################

MODELFIELD_MAP = {
    "booleanfield": [models.BooleanField, {}],
    "charfield": [models.CharField, {"max_length": BIG_STRING, }],
    "datefield": [models.DateField, {"null": True, }],
    "datetimefield": [models.DateTimeField, {"null": True, }],
    "decimalfield": [models.DecimalField, {"null": True, "max_digits": 10, "decimal_places": 5, }],
    "emailfield": [models.EmailField, {}],
    "integerfield": [models.IntegerField, {"null": True, }],
    "nullbooleanfield": [models.NullBooleanField, {}],
    "positiveintegerfield": [models.PositiveIntegerField, {}],
    "textfield": [models.TextField, {"null": True, }],
    "timefield": [models.TimeField, {}],
    "urlfield": [models.URLField, {}],
}

