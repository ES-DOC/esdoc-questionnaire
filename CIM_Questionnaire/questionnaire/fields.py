
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
__date__ ="Dec 18, 2013 1:32:37 PM"

"""
.. module:: questionnaire_fields

Summary of module goes here

"""

from django.forms import *

import django.forms.models
import django.forms.fields
import django.forms.widgets

from django.db import models
from django.db.models.fields import *

from south.modelsinspector import introspector

from CIM_Questionnaire.questionnaire.utils import *

EMPTY_CHOICE  = [("","----------")]
NULL_CHOICE   = [("_NONE", "---NONE---")]
OTHER_CHOICE  = [("_OTHER","---OTHER---")]


#################################
# fields used in the customizer #
#################################

class EnumerationFormField(django.forms.fields.MultipleChoiceField):

    def set_choices(self, choices, multi=True):
        self._choices = choices
        if multi:
            self.widget = SelectMultiple(choices=choices)
        else:
            self.widget = Select(choices=choices)

    def clean(self,value):

        # if this is _not_ a multi enumeration,
        # then the value will be a single string rather than a list;
        # (this is why I am explicitly calling to_python - see note below)
        value = self.to_python(value)

        # an enumeration can be invalid in 2 ways:
        # 1) specifying a value other than that provided by choices (recall that choices is set in the form initialization fns)
        # 2) not specifying a value when field is required

        if value:
            # this block is mostly taken from the super validate() fn
            for val in value:
                if not self.valid_value(val):
                    msg = "Select a valid choice, '%s' is not among the available choices" % (val)
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
        if type(self.widget) == SelectMultiple: # multi

            # this code taken from MultipleChoiceField.to_python ("django/forms/fields.py")
            if not value:
                return []
            elif not isinstance(value, (list, tuple)):
                raise ValidationError(self.error_messages['invalid_list'], code='invalid_list')
            return [smart_text(val) for val in value]

        else: # not multi

            # this code _not_ taken from ChoiceField.to_python (since I want it to return a list)
            if value in self.empty_values:
                return []
            return [smart_text(value)]

class EnumerationField(models.TextField):

    def formfield(self,**kwargs):
        new_kwargs = {
            "label"       : self.verbose_name.capitalize(),
            "required"    : not self.blank,
#            "choices"     : self.get_enumeration(),
            "form_class"  : EnumerationFormField,
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
        args,kwargs = introspector(self)
        return (field_class_path,args,kwargs)

class CardinalityFormFieldWidget(django.forms.widgets.MultiWidget):
    def __init__(self,*args,**kwargs):
        widgets = (
            django.forms.fields.Select(choices=[(str(i),str(i)) for i in range(0,11)]),
            django.forms.fields.Select(choices=[('*','*')]+[(str(i),str(i)) for i in range(0,11)][1:]),
        )
        super(CardinalityFormFieldWidget,self).__init__(widgets,*args,**kwargs)

    def decompress(self,value):
        if value:
            return value.split("|")
        else:
            return [u'',u'']

class CardinalityFormField(django.forms.fields.MultiValueField):

    def __init__(self,*args,**kwargs):
        fields = (
            django.forms.fields.CharField(max_length=2),
            django.forms.fields.CharField(max_length=2)
        )
        widget = CardinalityFormFieldWidget()
        super(CardinalityFormField,self).__init__(fields,widget,*args,**kwargs)
        self.widget = widget

    def compress(self, data_list):
        return "|".join(data_list)

    def clean(self,value):
        min = value[0] or ""
        max = value[1] or ""
        
        if (min > max) and (max != "*"):
            msg = "min must be less than or equal to max"
            raise ValidationError(msg)

        return "|".join([min,max])

class CardinalityField(models.CharField):

    def formfield(self,**kwargs):
        return CardinalityFormField(label=self.verbose_name.capitalize())

    def __init__(self,*args,**kwargs):
        kwargs["max_length"] = 8

        super(CardinalityField,self).__init__(*args,**kwargs)

    def get_prep_value(self, value):
        if type(value) is list:
            return "|".join(value)
        else:
            return value
            
    def south_field_triple(self):
        field_class_path = self.__class__.__module__ + "." + self.__class__.__name__
        args,kwargs = introspector(self)
        return (field_class_path,args,kwargs)


class CachedModelChoiceIterator(forms.models.ModelChoiceIterator):

    def __init__(self, field):
        super(CachedModelChoiceIterator,self).__init__(field)

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
            #for obj in self.queryset.all();
            for obj in self.queryset:
                yield self.choice(obj)


class CachedModelChoiceField(forms.ModelChoiceField):
    # only purpose of this class is to use a non-standard ModelChoiceIterator (above)
    # see [http://stackoverflow.com/a/8211123]

    def __init__(self,*args,**kwargs):
        super(CachedModelChoiceField,self).__init__(*args,**kwargs)

    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices

        return CachedModelChoiceIterator(self)

    choices = property(_get_choices, forms.ModelChoiceField._set_choices)

# TODO: CachedModelMultipleChoiceField

## just a one-off for vocabularies
#class OrderedModelMultipleChoiceField(django.forms.ModelMultipleChoiceField):
#
#    def clean(self, value):
#        qs = super(OrderedModelMultipleChoiceField, self).clean(value)
#        return sorted(qs, lambda a,b: sorted(qs, key=lambda x:value.index(x.pk)))
#
#class OrderedManyToManyField(models.ManyToManyField):
#    pass
#
#    def formfield(self,**kwargs):
#        return OrderedModelMultipleChoiceField(kwargs)
#


#############################
# fields used in the editor #
#############################

class MetadataFieldType(EnumeratedType):
    pass

MetadataFieldTypes = EnumeratedTypeList([
    MetadataFieldType("ATOMIC","Atomic"),
    MetadataFieldType("RELATIONSHIP","Relationship"),
    MetadataFieldType("ENUMERATION","Enumeration"),
    MetadataFieldType("PROPERTY","Property"),
])

class MetadataUnitType(EnumeratedType):
    pass

MetadataUnitTypes = EnumeratedTypeList([
    MetadataUnitType("X","x"),
])

## SEE COMMENT BELOW

class MetadataAtomicFieldType(EnumeratedType):
    pass

MetadataAtomicFieldTypes = EnumeratedTypeList([
    MetadataAtomicFieldType("DEFAULT","Character Field (default)"),
    MetadataAtomicFieldType("BOOLEAN","Boolean Field"),
    MetadataAtomicFieldType("DATE","Date Field"),
    MetadataAtomicFieldType("DATETIME","Date Time Field"),
    MetadataAtomicFieldType("DECIMAL","Decimal Field"),
    MetadataAtomicFieldType("EMAIL","Email Field"),
    MetadataAtomicFieldType("INTEGER","Integer Field"),
    MetadataAtomicFieldType("TEXT","Text Field (large block of text as opposed to a small string)"),
    MetadataAtomicFieldType("TIME","Time Field"),
    MetadataAtomicFieldType("URL","URL Field"),
])

METADATA_ATOMICFIELD_MAP = {
    "DEFAULT"  : [ TextInput,     { } ],
    "BOOLEAN"  : [ CheckboxInput, { } ],
    "DATE"     : [ DateInput,     { } ],
    "DATETIME" : [ DateTimeInput, { } ],
    "DECIMAL"  : [ NumberInput,   { } ],
    "EMAIL"    : [ EmailInput,    { } ],
    "INTEGER"  : [ NumberInput,   { } ],
    "TEXT"     : [ Textarea,      { } ],#"cols" : "60", "rows" : "4" } ],
    "TIME"     : [ TimeInput,     { } ],
    "URL"      : [ URLInput,      { } ],
}

## NOTE THAT I AM NO LONGER USING MOST OF THIS CODE BELOW
## HARD-CODING CIM MODEL FIELDS IS DEPRACATED
## IN FAVOR OF REGISTERING THEM FROM A CONFIGURATION FILE
## THE CODE ABOVE FILLS THE VOID

#############################################################
# the set of customizable atomic fields for metadata models #
# each item consists of a name, a corresponding class,      #
# and a set of default kwargs required for that class.      #
#############################################################

MODELFIELD_MAP = {
    "booleanfield"         : [ models.BooleanField,         { } ],
    "charfield"            : [ models.CharField,            { "max_length" : BIG_STRING} ],
    "datefield"            : [ models.DateField,            { "null" : True, } ],
    "datetimefield"        : [ models.DateTimeField,        { "null" : True, } ],
    "decimalfield"         : [ models.DecimalField,         { "null" : True, "max_digits" : 10, "decimal_places" : 5 } ],
    "emailfield"           : [ models.EmailField,           { } ],
    "integerfield"         : [ models.IntegerField,         { "null" : True} ],
    "nullbooleanfield"     : [ models.NullBooleanField,     { } ],
    "positiveintegerfield" : [ models.PositiveIntegerField, { } ],
    "textfield"            : [ models.TextField,            { "null" : True } ],
    "timefield"            : [ models.TimeField,            { } ],
    "urlfield"             : [ models.URLField,             { } ],
}

