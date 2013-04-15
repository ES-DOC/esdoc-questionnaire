
####################
#   Django-CIM-Forms
#   Copyright (c) 2012 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Jan 31, 2013 11:42:56 AM"

"""
.. module:: utils

This module contains utility code (constants, error-handling, etc.).

"""

from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured, ValidationError
from django.conf import settings
from django.core import serializers
from lxml import etree as et



import re

#############
# constants #
#############

#: the name of the DCF django application
APP_LABEL  = "dcf"

#: the default names that metadata versions have (change this at your peril)
METADATA_NAME = "CIM"

# no need for this; just use TextField instead of CharField
##: a constant max_value for really really big strings
#ENORMOUS_STRING = 4800

#: a constant max_value for really big strings
HUGE_STRING = 1200
#: a constant max_value for big strings
BIG_STRING  = 400
#: a constant max_value for normal strings
LIL_STRING  = 100

#: a serializer to use throughout the app; defined once to avoid too many fn calls
JSON_SERIALIZER = serializers.get_serializer("json")()
#: a parser to use throughout the app; defined once to avoid too many fn calls
XML_PARSER      = et.XMLParser(remove_blank_text=True)

##################
# error handling #
##################

class MetadataError(Exception):
    """
    Custom exception class for DCF

    .. note:: As DCF is a web-application, it often makes more sense to use the :func`dcf.error` view with an appropriate message instead of raising an explicit MetadataError

    """

    def __init__(self,msg='unspecified metadata error'):
        self.msg = msg
    def __str__(self):
        return "MetadataError: " + self.msg

################################
# some custom field validators #
################################

def validate_file_extension(value,valid_extensions):
    """
    Validator function to use with fileFields.
    Ensures the file attemping to be uploaded matches a set of extensions.
    :param value: file being validated
    :param valid_extensions: list of valid extensions
    """
    if not value.name.split(".")[-1] in valid_extensions:
        raise ValidationError(u'Invalid File Extension')

def validate_file_schema(value,schema_path):
    """
    validator function to use with fileFields;
    validates a file against an XML Schema.
    """

    contents = et.parse(value)

    try:
        schema = et.XMLSchema(et.parse(schema_path))
    except IOError:
        msg = "Unable to find suitable schema to validate file against"
        raise ValidationError(msg)

    try:
        schema.assertValid(contents)
    except et.DocumentInvalid, e:
        msg = "Invalid File Contents: %s" % str(e)
        raise ValidationError(msg)

def validate_no_spaces(value):
    """
    validator function to use with charFields;
    ensures there is no whitespace in the field
    """

    # TODO: WHY DOESN'T THIS WORK?
    #if re.match('\s',value):
    if ' ' in value:
        raise ValidationError(u'%s may not contain spaces' % value)

##############################
# enumerated types in Python #
##############################

class EnumeratedType(object):

    def __init__(self, type=None, name=None, cls=None):
        self._type  = type  # the key of this type
        self._name  = name  # the pretty name of this type
        self._class = cls   # the Python class used by this type (not always relevant)

    def getType(self):
        return self._type

    def getName(self):
        return self._name

    def getClass(self):
        return self._class

    def __unicode__(self):
        name = u'%s' % self._type
        return name

    # comparisons are made via the _type attribute...
    def __eq__(self,other):
        if isinstance(other,self.__class__):
            return self.getType() == other.getType()
        return False
    def __ne__(self,other):
        return not self.__eq__(other)

class EnumeratedTypeError(Exception):
    def __init__(self,msg='invalid enumerated type'):
        self.msg = msg
    def __str__(self):
        return "EnumeratedTypeError: " + self.msg

# this used to be based on deque to preserve FIFO order...
# but since I changed to adding fields to this list as needed in class's __init__() fn,
# that doesn't make much sense; so I'm basing it on a simple list
# and adding an ordering fn
class EnumeratedTypeList(list):

    def __getattr__(self,type):
        for et in self:
            if et.getType() == type:
                return et
        raise EnumeratedTypeError("unable to find %s" % str(type))

    # a method for sorting these lists
    # order is a list of EnumeratatedType._types
    @classmethod
    def comparator(cls,et,etOrderList):
        etType = et.getType()
        if etType in etOrderList:
            # if the type being compared is in the orderList, return it's position
            return etOrderList.index(etType)
        # otherwise return a value greater than the last position of the orderList
        return len(etOrderList)+1

##################################################
# and here are some enumerated types used by DCF #
##################################################

from django.forms.models import BaseForm, BaseFormSet, BaseInlineFormSet, BaseModelFormSet

class SubFormType(EnumeratedType):
    """
    An enumeration of the different types of subForms that can be used by a parent form.
    """
    pass

SubFormTypes = EnumeratedTypeList([
    SubFormType("FORM","Form",BaseForm),
    SubFormType("FORMSET","FormSet",BaseFormSet),
])

class CategoryType(EnumeratedType):
    """
    An enumeration of the different types of categories that can be specified in a customization
    """
    pass

CategoryTypes = EnumeratedTypeList([
    CategoryType("ATTRIBUTE","Attribute"),
    CategoryType("PROPERTY","Property"),
])

###########################
# a useful decorator      #
# (adds a guid to models) #
###########################

from django.db.models.signals import post_init
from django.db import models
from django.forms.fields import CharField
from django.forms.widgets import HiddenInput
from uuid import uuid4
import types

class GUIDField(models.CharField):
    """
    A modelField to store a GUID
    .. note:: this field shouldn't be used directly, the @guid decorator handles adding it to classes
    """

    def __init__(self, *args, **kwargs):
        """
        initialize a GUIDField;
        it must be 64 chars, unique (for this class) in the db, not editable by any form, required, and already have a default guid value
        """
        kwargs['max_length'] = kwargs.get('max_length', 64 )
        kwargs['unique']     = kwargs.get('unique', True )
        kwargs['editable']   = kwargs.get('editable', True )
        kwargs['blank']      = kwargs.get('blank', False )
        kwargs['default']    = kwargs.get('default',lambda:str(uuid4()))
 
        super(GUIDField, self).__init__(*args, **kwargs)

    def formfield(self,**kwwargs):

        return CharField(initial=self.default,widget=HiddenInput)
    
    def contribute_to_class(self,cls,name):
        """
        called when a GUIDField is (dynamically) added to a class
        this inserts the "getGUID" fn to that class
        it also registers a callback w/ the cls post_init signal
        (so that I can give it a unique value then)
        """
        def _getGUID(self):
            return self._guid

        cls.getGUID = types.MethodType(_getGUID,None,cls)
#        post_init.connect(self.setValue,cls)

        super(GUIDField,self).contribute_to_class(cls,name)
            
    def setValue(self,*args,**kwargs):

        instance = kwargs.get("instance",None)
        if instance:
            # don't overwrite an existing guid
            if not instance._guid:
                instance._guid = str(uuid4())


#    def pre_save(self, model_instance, add):
#        """
#        just in case the value wasn't already set
#        (by the "default" kwarg in __init__),
#        go ahead and set it before storing in the db
#        """
#        value = getattr(model_instance, self.attname, None)
#        if not value:
#            value = str(uuid4())
#            setattr(model_instance,self.attname,value)
#        return value

def guid():
    """
    decorator that specifies that a model has a _guid element,
    which can be accessed using the getGUID() method.
    this is a unique way of identifying models, fields, customizers, whatever
    (which is important when having to distinguish them in a Django Templage)
    """
    def decorator(obj):
        
        # create the field
        guid_field = GUIDField()#default=lambda:str(uuid4()))
        # add it to the object
        guid_field.contribute_to_class(obj, "_guid")
        # return the modified object
        return obj

    return decorator

##################
# some other fns #
##################

def get_subclasses(parent,_subclasses=None):
    """
    Given a Django Class, recursively gets all subclasses.
    """
    if _subclasses is None:
        _subclasses = set()
    subclasses = parent.__subclasses__()
    for subclass in subclasses:
        if subclass not in _subclasses:
            _subclasses.add(subclass)
            get_subclasses(subclass,_subclasses)
    return _subclasses
