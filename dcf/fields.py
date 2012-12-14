from django.db import models
from django import forms

import django.forms.models
import django.forms.widgets
import django.forms.fields

from dcf.helpers import *

def updateFieldAttributes(field,fieldAttributes):
    for (key,value) in fieldAttributes.iteritems():
        try:
            currentAttrs = field.widget.attrs[key]
            field.widget.attrs[key] = "%s %s" % (currentAttrs,value)
        except KeyError:
            field.widget.attrs[key] = value

####################################################
# the types of fields that a model can have.       #
# these are rendered as tabs in the template,      #
# with each tab displaying all fields of that type #
# they function a bit like tags,                   #
# but each field can only have one type            #
####################################################

#class FieldType(EnumeratedType):
#    pass



################################
# the base class of all fields #
################################

class MetadataField(models.Field):
    class Meta:
        abstract = True

    _type = ""

    def getName(self):
        return self.name

    def getType(self):
        return self._type.strip()

    def init(self,*args,**kwargs):
        super(MetadataField,self).__init__(*args,**kwargs)

        self._name = self.name



#############################################################
# the set of customizable atomic fields for metadata models #
# each item consists of a name, a corresponding class,      #
# and a set of default kwargs required for that class.      #
#############################################################

MODELFIELD_MAP = {
    "booleanfield"          : [models.BooleanField, {}],
    "charfield"             : [models.CharField, { "max_length" : BIG_STRING}],
    "datefield"             : [models.DateField, {}],
    "datetimefield"         : [models.DateTimeField, {}],
    "decimalfield"          : [models.DecimalField, { "null" : True}],
    "emailfield"            : [models.EmailField, {}],
    "integerfield"          : [models.IntegerField, { "null" : True}],
    "nullbooleanfield"      : [models.NullBooleanField, {}],
    "positiveintegerfield"  : [models.PositiveIntegerField, {}],
    "textfield"             : [models.TextField, {}],
    "timefield"             : [models.TimeField, {}],
    "urlfield"              : [models.URLField, { "verify_exists" : False}],
}

class MetadataAtomicField(MetadataField):

    def __init__(self,*args,**kwargs):
        super(MetadataAtomicField,self).__init__(**kwargs)


    @classmethod
    def Factory(cls,modelFieldClassName,**kwargs):
        modelFieldClassInfo = MODELFIELD_MAP[modelFieldClassName.lower()]
        modelFieldClass = modelFieldClassInfo[0]
        modelFieldKwargs = modelFieldClassInfo[1]

# in theory, I could also have created a new metaclass to achieve multiple inheritance
# but in practise, these two field types are just too dissimilar for that
#       class _MetadataAtomicFieldMetaClass(MetadataField.Meta,modelFieldClass.Meta):
#           pass

        class _MetadataAtomicField(cls,modelFieldClass):
            def __init__(self,*args,**kwargs):
                # set of kwargs passed to constructor
                # should be default set plus any overrides
                for (key,value) in modelFieldKwargs.iteritems():
                    if not key in kwargs:
                        kwargs[key] = value
                super(_MetadataAtomicField,self).__init__(**kwargs)
                self._type = modelFieldClassName


        return _MetadataAtomicField(**kwargs)
