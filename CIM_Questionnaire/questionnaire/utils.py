
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
__date__ ="Dec 9, 2013 4:33:11 PM"

"""
.. module:: utils

Summary of module goes here

"""

from django.core.exceptions     import ValidationError
from django.core.files.storage  import FileSystemStorage
from django.conf                import settings

from django.forms   import model_to_dict

import os
import re

from django.core    import serializers
from lxml           import etree as et

from django.template.defaultfilters import slugify

from questionnaire  import get_version

def xpath_fix(node, xpath):
    """Helper function to address lxml smart strings memory leakage issue.

    :param lxml.etree.Element node: An xml element.
    :param str xpath: An xpath statement.

    :returns: Results of xpath expression evaluation.
    :rtype: list or lxml.etree.Element

    """
    if node is None:
        raise ValueError("Xpath expression cannot be evaluated against a null XML node.")
    if xpath is None or not len(xpath):
        raise ValueError("Xpath expression is invalid.")

    return node.xpath(xpath, smart_strings=False)

#############
# constants #
#############

APP_LABEL = "questionnaire"

LIL_STRING      = 128
SMALL_STRING    = 256
BIG_STRING      = 512
HUGE_STRING     = 1024

#: a serializer to use throughout the app; defined once to avoid too many fn calls
JSON_SERIALIZER   = serializers.get_serializer("json")()

CIM_STEREOTYPES = [
    "document",
]

#: the set of document types recognized by the questionnaire
CIM_DOCUMENT_TYPES = [
    "modelcomponent",
    "statisticalmodelcomponent",
    "experiment",
]

#: vocabulary name to use for cases where a model has no vocabulary, or where it is the root component of several vocabularies
DEFAULT_VOCABULARY  = "DEFAULT_VOCABULARY"

##################
# error handling #
##################

class QuestionnaireError(Exception):
    """
    Custom exception class

    .. note:: As the CIM Questionnaire is a web-application, it often makes more sense to use the :func`questionnaire.questionnaire_error` view with an appropriate message instead of raising an explicit QuestionnaireError

    """

    def __init__(self,msg='unspecified metadata error'):
        self.msg = msg
        
    def __str__(self):
        return "QuestionnaireError: " + self.msg

##############
# validators #
##############

def validate_no_spaces(value):
    """
    validator function to use with charFields;
    ensures there is no whitespace in the field
    """

    # TODO: WHY DOESN'T THIS WORK?
    #if re.match('\s',value):
    if ' ' in value:
        raise ValidationError(u"'%s' may not contain spaces" % value)

def valiate_no_bad_chars(value):
    INVALID_CHARS       = "< > % # % { } [ ] $"
    INVALID_CHARS_REGEX = "[<>&#%{}\[\]\$]"

    if re.search(INVALID_CHARS_REGEX,value):
        raise ValidationError(u"value may not contain any of the following characters: '%s'" % (INVALID_CHARS))#not contain any of the following invalid characters: '%'" % (value,INVALID_CHARS))

def validate_password(value):
    # passwords have a minimum length...
    PASSWORD_LENGTH = 6
    if len(value) < PASSWORD_LENGTH:
        raise ValidationError("A password must contain at least %s characters" % (PASSWORD_LENGTH))
    # and a mixture of letters and non-letters...
    if not (re.match(r'^.*[A-Za-z]', value) and
            re.match(r'^.*[0-9!@#$%^&*()\-_=+.,?:;></\\\[\]\{\}]',value)):
        raise ValidationError("A password must contain both letters and non-letters")

def validate_no_reserved_words(value):
    """
    validator function to use with charFields;
    ensures specified words are not used
    """
    
    RESERVED_WORDS = [
        # cannot have projects w/ these names, else the URLs won't make sense...
        "admin", "ajax", "customize", "edit", "help", "index", "login", "logout",
        "questionnaire", "register", "static", "site_media", "test", "user",
    ]

    if value.lower() in RESERVED_WORDS:
        raise ValidationError(u"'%s' is a reserved word" % value)

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
        msg = "Unable to find suitable schema to validate file against (%s)" % schema_path
        raise ValidationError(msg)

    try:
        schema.assertValid(contents)
    except et.DocumentInvalid, e:
        msg = "Invalid File Contents: %s" % str(e)
        raise ValidationError(msg)



###########################
# form/field manipulation #
###########################

def remove_form_errors(form):
    form.errors["__all__"] = form.error_class()
    for field in form.fields:
        form.errors[field] = form.error_class()


def set_field_widget_attributes(field,widget_attributes):
    for (key,value) in widget_attributes.iteritems():
        field.widget.attrs[key] = value

def update_field_widget_attributes(field,widget_attributes):
    """
    rather than overriding an attribute, this fn appends it to any existing ones
    as with class='old_class new_class'
    """
    for (key,value) in widget_attributes.iteritems():
        try:
            current_attributes = field.widget.attrs[key]
            field.widget.attrs[key] = "%s %s" % (current_attributes,value)
        except KeyError:
            field.widget.attrs[key] = value


# THIS TOOK A WHILE TO FIGURE OUT
# model_to_dict IGNORES FOREIGNKEY FIELDS & MANYTOMANY FIELDS
# THIS FN WILL UPDATE THE MODEL_DATA ACCORDING TO THE "update_fields" ARGUMENT
def get_initial_data(model,update_fields={}):
    dict = model_to_dict(model)
    dict.update(update_fields)
    for key,value in dict.iteritems():
        if isinstance(value,tuple):
            # TODO: SOMETIMES THIS RETURNS A TUBLE INSTEAD OF A STRING, NOT SURE WHY
            dict[key] = value[0]
    return dict

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
            file_path = os.path.join(settings.MEDIA_ROOT,name)
            os.remove(file_path)
            print "deleted existing %s file" % (file_path)
        return name

####################
# enumerated types #
####################

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

    def get(self,type):
        for et in self:
            if et.getType() == type:
                return et
        return None
    
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


#####################################
# deal w/ hierarchies of components #
#####################################

import mptt
from mptt.fields import TreeForeignKey

def hierarchical(cls):
    TreeForeignKey(cls, null=True, blank=True, related_name='children').contribute_to_class(cls,'parent')
    mptt.register(cls)
    return cls

######################################
# removes duplicates from a sequence #
# but preserves order                #
######################################

def ordered_set(sequence):
    seen_items = set()
    #seen_add = seen.add
    return [item for item in sequence if item not in seen_items and not seen_items.add(item)]

###########################################
# finds matching item in list             #
# (using this fn instead of standard loop #
# b/c it doesn't traverse the whole list) #
###########################################

def find_in_sequence(fn, sequence):
  for item in sequence:
    if fn(item):
      return item
  return None

def interate_through_node(node,filter_parameters={}):
    if filter_parameters:
        sibling_qs = node.get_siblings(include_self=True).filter(**filter_parameters)
    else:
        sibling_qs = node.get_siblings(include_self=True)
    for sibling in sibling_qs:
        return sibling
        if filter_parameters:
            child_qs = sibling.get_children(include_self=False).filter(**filter_parameters)
        else:
            child_qs = sibling.get_children(include_self=False)
        for child in child_qs:
            iterate_through_node(child,filter_parameters)