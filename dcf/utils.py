
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
__date__ ="Jun 10, 2013 4:17:21 PM"

"""
.. module:: utils

Summary of module goes here

"""

from django.conf import settings

from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured, ValidationError

from django.db import models
from django.forms import model_to_dict

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
import inspect

from django.utils import simplejson as json

from django.core import serializers
from lxml import etree as et

from uuid import uuid4

import re



#############
# constants #
#############

#: the name of the DCF django application
APP_LABEL  = "dcf"

#: the default names that metadata versions have (change this at your peril)
METADATA_NAME = "cim"

#: a constant max_value for really really big strings
ENORMOUS_STRING = 4800 # (no real need for this; just use TextField instead of CharField)
#: a constant max_value for really big strings
HUGE_STRING = 1200
#: a constant max_value for big strings
BIG_STRING  = 400
#: a constant max_value for normal strings
LIL_STRING  = 255


#: a constant tuple to add to "open" enumerations
OPEN_CHOICE = [(u'OTHER',u'--OTHER--')]
#: a constant tuple to add to "nullable" enumerations
NULL_CHOICE  = [(u'NONE',u'--NONE--')]

#: a hard-coded list of possible document types that these forms can support
CIM_DOCUMENT_TYPES = [
    ("modelcomponent","modelcomponent"),
    ("statisticalmodelcomponent","statisticalmodelcomponent"),
]
#: a serializer to use throughout the app; defined once to avoid too many fn calls
JSON_SERIALIZER = serializers.get_serializer("json")()
#: a parser to use throughout the app; defined once to avoid too many fn calls
XML_PARSER      = et.XMLParser(remove_blank_text=True)

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
        print schema_path
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
        raise ValidationError(u"'%s' may not contain spaces" % value)

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
            # comparing two enumeratedtypes
            return self.getType() == other.getType()
        else:
            # comparing an enumeratedtype with a string
            return self.getType() == other
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

def yield_list(list_to_yield):
    """
    creates a generator from a sequence
    was using this to pass portions of initial to formsets
    (via curried function); but wound up not doing that anymore
    """
    for list_element in list_to_yield:
        yield list_element

def get_from_model_or_dict(model,dict,attribute_name):
    """
    loads of form intialization is conditional on field values
    however, if the form is rendered via GET then the underlying
    model might not have fields set yet and data will have been passed in
    by initial
    """
    pass

# THIS TOOK A WHILE TO FIGURE OUT
# model_to_dict IGNORES FOREIGNKEY FIELDS & MANYTOMANY FIELDS
# THIS FN WILL UPDATE THE MODEL_DATA ACCORDING TO THE "update_fields" ARGUMENT
def get_initial_data(model,update_fields={}):
    dict = model_to_dict(model)
    dict.update(update_fields)
    for key,value in dict.iteritems():
        if isinstance(value,tuple):
            # TODO: model_to_dict IS BEHAVING WIERD W/ ScientificPropertyValue Fields
            # UNTIL I CAN FIX IT, HERE IS HACK
            #print "MODEL_TO_DICT RETURNED A TUPLE (%s) INSTEAD OF A STRING; CHANGING IT BACK"
            dict[key] = value[0]
    return dict


def dict_to_html_aux(dict,html):
  for key,value in dict.iteritems():
    html.append(u"<li id='%s'>%s"% (key.lower(),key))
    if value:
        html.append("<ul>")
        for v in value:
            dict_to_html_aux(v,html)
        html.append("</ul>")

def dict_to_html(dict):
  html = ["<ul>"]
  dict_to_html_aux(dict,html)
  html.append("</ul>")
  return "".join(html)

def user_has_permission(user,restriction=""):
    if restriction:
        return user.has_perm(restriction)
    return True
