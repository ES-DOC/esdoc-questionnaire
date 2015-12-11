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

import os

from django.conf import settings
from django.db import models
from django.db.models.fields import smart_text
from django.forms import ValidationError, Select, CheckboxSelectMultiple, RadioSelect
from django.forms import CheckboxInput, DateInput, DateTimeInput, NumberInput, EmailInput, Textarea, TextInput, TimeInput, URLInput
from django.forms.fields import CharField, MultipleChoiceField, MultiValueField
from django.forms.widgets import MultiWidget
from django.core.files.storage import FileSystemStorage
from django.utils.html import format_html
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
# from south.modelsinspector import introspector


from Q.questionnaire.q_utils import EnumeratedType, EnumeratedTypeList, BIG_STRING, HUGE_STRING, QError

#############
# constants #
#############

# THIS IS A RIDICULOUS HACK,
# DJANGO ADDS SOME TEXT TO M2M FIELD'S HELP ("django.forms.models.ModelMultipleChoiceField#__init__")
# I HAVE TO MANUALLY REMOVE IT IN VARIOUS FORMS
# TODO: THIS SHOULD BE FIXED IN FUTURE VERSIONS OF DJANGO

MULTIPLECHOICEFIELD_HELP_TEXT = 'Hold down "Control", or "Command" on a Mac, to select more than one.'


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
            print("deleted existing %s file" % file_path)
        return name

######################
# enumeration fields #
######################

#: the bit to add onto a field's choices when an explicit empty choice is required
EMPTY_CHOICE = [("", "---------")]
#: the bit to add onto a field's choices when an explicit NONE choice is required
NULL_CHOICE = [("_NONE", "---NONE---")]
#: the bit to add onto a field's choices when an explicit OTHER choice is required
OTHER_CHOICE = [("_OTHER", "---OTHER---")]

# there is a distinction between "enumeration" fields and "multiselect" widgets
# although the former must use the latter
# any ModelField which uses a Select FormField can potentially use one the following 2 "multiselect" Widgets
# this just provides hooks for JQuery code to make it look pretty
# an "enumeration" field adds the ability to change the "choices" parameter at will
# as well as handling "NONE" and "OTHER" choices (it is meant for enumeration properties)


# TODO: COLLAPSE MultipleSelectWidget AND SingleSelectWidget INTO A SINGLE CLASS

class MultipleSelectWidget(CheckboxSelectMultiple):
    """
    the widget to use for enumeration fields that have "multiple" set to True
    """

    def render(self, name, value, attrs=None, choices=()):
        """
        custom render fn that wraps the entire <ul> in a <div> w/ appropriate classes
        that div can then be manipulated via JQuery in the template
        :param name:
        :param value:
        :param attrs:
        :param choices:
        :return: HTML representation of the widget
        """

        # get rid of widget class attributes before rendering
        # so that they are not added to every sub-widget,
        # and I can just add them once to the top-level widget
        if attrs and "class" in attrs:
            classes_to_render = attrs.pop("class")
            self.attrs.pop("class", None)
        else:
            classes_to_render = self.attrs.pop("class", [])
        if classes_to_render:
            classes_to_render = classes_to_render.split(' ')

        renderer = self.get_renderer(name, value, attrs, choices)

        # rendered_widget = renderer.render()
        # return rendered_widget

        id_ = renderer.attrs.get("id", None)
        container = format_html("<div class='{0}'>", " ".join(classes_to_render))
        header = format_html("<button class='multiselect_header' type='button'><span class='multiselect_header_title'>&nbsp;</span></button>")
        content = format_html("<div class='multiselect_content ui-widget ui-widget-content ui-corner-all'>")
        start_tag = format_html("<ul id='{0}'>", id_) if id_ else "<ul>"
        output = [container, header, content, start_tag]
        for widget in renderer:
            # add a class to the rendered <input> element
            try:
                current_classes = widget.attrs["class"]
                widget.attrs["class"] = "%s %s" % (current_classes, "multiselect_input")
            except KeyError:
                widget.attrs["class"] = "multiselect_input"
            output.append(format_html("<li>{0}</li>", force_text(widget)))
        output.append("</ul></div></div>")  # end start_tag, content, container
        rendered_widget = mark_safe('\n'.join(output))
        return rendered_widget


class SingleSelectWidget(RadioSelect):
    """
    the widget to use for enumeration fields that have "multiple" set to False
    """

    def render(self, name, value, attrs=None, choices=()):
        """
        custom render fn that wraps the entire <ul> in a <div> w/ appropriate classes
        that div can then be manipulated via JQuery in the template
        :param name:
        :param value:
        :param attrs:
        :param choices:
        :return: HTML representation of the widget
        """

        # get rid of widget class attributes before rendering
        # so that they are not added to every sub-widget,
        # and I can just add them once to the top-level widget
        if attrs and "class" in attrs:
            classes_to_render = attrs.pop("class")
            self.attrs.pop("class", None)
        else:
            classes_to_render = self.attrs.pop("class", [])
        if classes_to_render:
            classes_to_render = classes_to_render.split(' ')

        renderer = self.get_renderer(name, value, attrs, choices)

        # rendered_widget = renderer.render()
        # return rendered_widget

        id_ = renderer.attrs.get("id", None)
        container = format_html("<div class='{0}'>", " ".join(classes_to_render))
        header = format_html("<button class='multiselect_header' type='button'><span class='multiselect_header_title'>&nbsp;</span></button>")
        content = format_html("<div class='multiselect_content ui-widget ui-widget-content ui-corner-all'>")
        start_tag = format_html("<ul id='{0}'>", id_) if id_ else "<ul>"
        output = [container, header, content, start_tag]
        for widget in renderer:
            # add a class to the rendered <input> element
            try:
                current_classes = widget.attrs["class"]
                widget.attrs["class"] = "%s %s" % (current_classes, "multiselect_input")
            except KeyError:
                widget.attrs["class"] = "multiselect_input"
            output.append(format_html("<li>{0}</li>", force_text(widget)))
        output.append("</ul></div></div>")  # end start_tag, content, container
        rendered_widget = mark_safe('\n'.join(output))
        return rendered_widget


class EnumerationFormField(MultipleChoiceField):
    """
    the form field to use for EnumeationFields
    behaves like a MultipleChoiceField,
    except that everything is stored as a string in the db
    """

    # HERE IS A CHANGE TO COPE W/ v0.15...
    empty_values = [
        None, u'', [], (), {}, [u''],
    ]

    def set_choices(self, choices, multi=True):
        """
        explicitly set the choices of this form field
        since this is where I set the widget,
        I also make sure to add "enumeration" to the rendered class
        :param choices: the options to render
        :param multi: boolean indicating whether to allow multiple selections or not
        :return:
        """
        self._choices = choices
        class_attrs = {"class": "enumeration"}
        if multi:
            self.widget = MultipleSelectWidget(choices=choices, attrs=class_attrs)
        else:
            self.widget = SingleSelectWidget(choices=choices, attrs=class_attrs)

    def clean(self, value):

        original_value = value
        # if this is _not_ a multi enumeration,
        # then the value will be a single string rather than a list;
        # (this is why I am explicitly calling to_python - see note below)
        value = self.to_python(value)

        # an enumeration can be invalid in 2 ways:
        # 1) specifying a value other than that provided by choices (choices is set during form initialization)
        # 2) not specifying a value when field is required

        try:
            if any(value):
                # this block is mostly taken from the super validate() fn
                for val in value:
                    if not self.valid_value(val):
                        msg = "Select a valid choice, '%s' is not among the available choices" % val
                        raise ValidationError(msg)
                self.run_validators(value)
            elif self.required:
                raise ValidationError(self.error_messages["required"])
            else:
                value = []
        except Exception as e:
            import ipdb; ipdb.set_trace()
            new_value = self.to_python(original_value)
            pass

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
        if type(self.widget) == MultipleSelectWidget:  # multi

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
    """
    a custom model field to use for enumerations
    allows choices to specified as-needed
    allows widget to change based on whether it's multiple or not
    has hooks for JQuery functionality to support logic of using OTHER  or NONE choices
    """

    def formfield(self, **kwargs):
        # new_kwargs = {
        #     "label": self.verbose_name.capitalize(),
        #     "required": not self.blank,
        #     "form_class": EnumerationFormField,
        # }
        # new_kwargs.update(kwargs)
        # return super(EnumerationField, self).formfield(**new_kwargs)
        return EnumerationFormField(
            required=not self.blank,
            label=self.verbose_name.capitalize(),
        )

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

    # def south_field_triple(self):
    #     field_class_path = self.__class__.__module__ + "." + self.__class__.__name__
    #     args, kwargs = introspector(self)
    #     return (field_class_path, args, kwargs)


####################
# list fields      #
# (for references) #
####################

LIST_DEFAULT_TOKEN = '|'
LIST_DEFAULT_CARDINALITY = u"0|*"
LIST_DEFAULT_MAX = 10

def get_min_and_max_from_cardinality(cardinality):
    _min, _max = cardinality.split('|')
    _min = int(_min)
    if _max == '*':
        _max = LIST_DEFAULT_MAX
    else:
        _max = int(_max)
        if _max > LIST_DEFAULT_MAX:
            msg = u"Invalid number of list items."
            raise QError(msg)
    return _min, _max

class ListFormField(MultipleChoiceField):

    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop("token")
        self.cardinality = kwargs.pop("cardinality")
        super(ListFormField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            return []
        elif not isinstance(value, (list, tuple)):
            raise ValidationError(self.error_messages['invalid_list'], code='invalid_list')
        return value

    def validate(self, value):
        """
        Validates that the input is a list or tuple.
        """
        if self.required and not value:
            raise ValidationError(self.error_messages['required'], code='required')
        # # Validate that each value in the value list is in self.choices.
        # for val in value:
        #     if not self.valid_value(val):
        #         raise ValidationError(
        #             self.error_messages['invalid_choice'],
        #             code='invalid_choice',
        #             params={'value': val},
        #         )

    def clean(self, value):

        # AS OF V0.15
        # THIS WAS NEEDED IN CASE initial_extra WAS NOT BEING COPIED TO initial
        # WHICH WOULD HAPPEN FOR UNLOADED FORMS
        # BUT NOW I FORCE LOADING OF AJAX-ADDED FORMS, SO I SHOULD NEVER GET TO THIS BIT OF CODE
        # (see views_ajax_bak.py)
        if value is None:
            return []

        for v in value:
            if self.token in v:
                msg = "Invalid character ('%s') was in list item." % self.token
                raise ValidationError(msg)

        return self.token.join(value)

    def set_choices(self, choices):
        empty_choice = ("", "")
        new_choices = []
        _min, _max = get_min_and_max_from_cardinality(self.cardinality)
        if _min == _max:
            # this is a special case,
            # if your cardinality is something like "5|5" then you want 5 items
            _max = _min
            _min = 0
        for index in range(_min, _max):
            try:
                new_choices.append((choices[index], choices[index]))
            except IndexError:
                new_choices.append(empty_choice)
        self.choices = new_choices

    def set_cardinality(self, cardinality):
        self.cardinality = cardinality
        _min, _max = get_min_and_max_from_cardinality(self.cardinality)
        assert _min < _max, "invalid cardinality"


class ListField(models.TextField):
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token', LIST_DEFAULT_TOKEN)
        self.cardinality = kwargs.pop('cardinality', LIST_DEFAULT_CARDINALITY)
        super(ListField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        # treat None and empty strings and lists differently here
        if not value:
            return []
        if isinstance(value, list):
            return value
        return value.split(self.token)

    def get_prep_value(self, value):
        # explicitly distinguish between None and empty strings and lists here
        if value is None:
            return []
        assert(isinstance(value, list) or isinstance(value, tuple))
        return self.token.join(value)

    # def get_db_prep_value(self, value):
    #     if not value:
    #         return []
    #     assert(isinstance(value, list) or isinstance(value, tuple))
    #     return self.token.join([s for s in value])

    def formfield(self, **kwargs):
        _min, _max = get_min_and_max_from_cardinality(self.cardinality)
        return ListFormField(
            token=self.token,
            cardinality=self.cardinality,
            required=_min > 0,
        )

    # def south_field_triple(self):
    #     field_class_path = self.__class__.__module__ + "." + self.__class__.__name__
    #     args, kwargs = introspector(self)
    #     return (field_class_path, args, kwargs)
    
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

    # def south_field_triple(self):
    #     field_class_path = self.__class__.__module__ + "." + self.__class__.__name__
    #     args, kwargs = introspector(self)
    #     return (field_class_path, args, kwargs)

#################
# cached fields #
#################

# TODO: ARE THESE CACHED FIELD CLASSES BEING USED?

from django.forms.models import ModelChoiceIterator
from django.forms import ModelChoiceField

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

