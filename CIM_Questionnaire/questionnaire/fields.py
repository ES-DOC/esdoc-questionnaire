
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
from django.template.defaultfilters import slugify

from south.modelsinspector import introspector, add_introspection_rules

from questionnaire.utils import *

EMPTY_CHOICE  = [("","----------")]
NULL_CHOICE   = [("_NONE", "---NONE---")]
OTHER_CHOICE  = [("_OTHER","---OTHER---")]


#################################
# fields used in the customizer #
#################################

class EnumerationFormField(django.forms.fields.MultipleChoiceField):

    def clean(self,value):
        # an enumeration can be invalid in 2 ways:
        # 1) specifying a value other than that provided by choices
        # 2) not specifying a value when field is required
        if value:
            value=set(value)
            current_choices = self.widget.choices
            if not value.issubset([choice[0] for choice in current_choices]):
                msg = "Select a valid choice, '%s' is not among the available choices" % (value)
                raise ValidationError(msg)
            else:
                # TODO: ALL OF THIS NONSENSE W/ LIST & SET MEANS SOMETHING SOMEWHERE IS NOT QUITE WORKING RIGHT
                return list(value)
        elif self.required:
            raise ValidationError(self.error_messages["required"])
        return []

class EnumerationField(models.TextField):
    enumeration = []

    def formfield(self,**kwargs):
        new_kwargs = {
            "label"       : self.verbose_name.capitalize(),
            "required"    : not self.blank,
            "choices"     : self.get_choices(),
            "form_class"  : EnumerationFormField,
        }
        new_kwargs.update(kwargs)
        return super(EnumerationField,self).formfield(**new_kwargs)

    def get_choices(self):
        return self.enumeration

    def set_choices(self,choices):
        self.enumeration = [(slugify(choice),choice) for choice in choices]

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
    "DEFAULT"   : [ TextInput,      { } ],
    "BOOLEAN"   : [ CheckboxInput,  { } ],
    "DATE"      : [ DateInput,      { } ],
    "DATETIME"  : [ DateTimeInput,  { } ],
    "DECIMAL"   : [ NumberInput,    { } ],
    "EMAIL"     : [ EmailInput,     { } ],
    "INTEGER"   : [ NumberInput,    { } ],
    "TEXT"      : [ Textarea,       { } ],
    "TIME"      : [ TimeInput,      { } ],
    "URL"       : [ URLInput,       { } ],
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
    "booleanfield"          : [ models.BooleanField,         { } ],
    "charfield"             : [ models.CharField,            { "max_length" : BIG_STRING} ],
    "datefield"             : [ models.DateField,            { "null" : True, } ],
    "datetimefield"         : [ models.DateTimeField,        { "null" : True, } ],
    "decimalfield"          : [ models.DecimalField,         { "null" : True, "max_digits" : 10, "decimal_places" : 5 } ],
    "emailfield"            : [ models.EmailField,           { } ],
    "integerfield"          : [ models.IntegerField,         { "null" : True} ],
    "nullbooleanfield"      : [ models.NullBooleanField,     { } ],
    "positiveintegerfield"  : [ models.PositiveIntegerField, { } ],
    "textfield"             : [ models.TextField,            { "null" : True } ],
    "timefield"             : [ models.TimeField,            { } ],
    "urlfield"              : [ models.URLField,             { } ],
}

class MetadataField(models.Field):
    """
    the base class for all metadata fields (attributes)
    """
    class Meta:
        abstract = True

    name = ""
    type = ""

    def contribute_to_class(self,cls,name,*args,**kwargs):
        ### in Django > 1.6 the virtual_only kwargs seems to be deprecated
        kwargs.pop("virtual_only",False)
        super(MetadataField,self).contribute_to_class(cls,name)

def isAtomicField(field_type):
    return field_type.lower() in MODELFIELD_MAP.iterkeys()

def isRelationshipField(field_type):
    return field_type.lower() in [field.type.lower() for field in MetadataRelationshipField.__subclasses__()]

def isEnumerationField(field_type):
    return field_type.lower() in [MetadataEnumerationField.type.lower()]

class MetadataAtomicField(MetadataField):
    type = "AtomicField"

    @classmethod
    def Factory(cls,field_class_name,**kwargs):
        try:
            field_class_info    = MODELFIELD_MAP[field_class_name.lower()]
            field_class         = field_class_info[0]
            field_class_kwargs  = field_class_info[1]
        except:
            msg = "unknown field type: '%s'" % field_class_name
            print msg
            raise QuestionnaireError(msg)

        class _MetadataAtomicField(cls,field_class):

            def __init__(self,*args,**kwargs):
                kwargs.update(field_class_kwargs)
                super(_MetadataAtomicField,self).__init__(**kwargs)
                self.type = field_class_name

            def south_field_triple(self):
                field_class_path = "django.db.models.fields" + "." + field_class.__name__
                args,kwargs = introspector(self)
                return (field_class_path,args,kwargs)

        return _MetadataAtomicField(**kwargs)


class MetadataRelationshipField(MetadataField):
    class Meta:
        abstract = True

    type = "RelationshipField"

    sourceModelName    = None
    sourceAppName      = None
    targetModelName    = None
    targetAppName      = None

    def __init__(self,*args,**kwargs):
        # explicitly call super on this base class
        # so that the next item in inheritance calls its initializer
        super(MetadataRelationshipField,self).__init__(*args,**kwargs)


class MetadataEnumerationField(MetadataField):
    type = "EnumerationField"
    pass

