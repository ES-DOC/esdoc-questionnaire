
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

__author__ = "allyn.treshansky"
__date__ = "Dec 9, 2013 4:33:11 PM"

"""
.. module:: utils

Summary of module goes here

"""

from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from django.forms import model_to_dict
from django.forms.models import BaseModelFormSet, BaseInlineFormSet
from django.forms.fields import MultiValueField

import os
import re
import urllib

from django.core import serializers
from lxml import etree as et


from CIM_Questionnaire.questionnaire import get_version

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

LIL_STRING   = 128
SMALL_STRING = 256
BIG_STRING   = 512
HUGE_STRING  = 1024

#: a serializer to use throughout the app; defined once to avoid too many fn calls
JSON_SERIALIZER = serializers.get_serializer("json")()

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
DEFAULT_VOCABULARY = "DEFAULT_VOCABULARY"

##############
# assertions #
##############

def assert_no_string_nones(dct):
    """
    Asserts no string representations of NoneType (i.e. ``'None'``) are present in the dictionary.

    :param dict dct:
    """
    for k, v in dct.iteritems():
        if v == 'None':
            msg = 'The key "{0}" has value equal to "None" string.'.format(k)
            raise AssertionError(msg)


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
def get_initial_data(model, update_fields={}):
    dict = model_to_dict(model)
    dict.update(update_fields)
    for key, value in dict.iteritems():
        if isinstance(value,tuple):
            # TODO: SOMETIMES THIS RETURNS A TUPLE INSTEAD OF A STRING, NOT SURE WHY
            dict[key] = value[0]
    return dict

# TODO: REPLACE THE ABOVE FN W/ THIS FN IN CODE
def model_to_data(model, exclude=[], include={}):
    model_data = model_to_dict(model)
    model_data.update(include)
    model_data_copy = model_data.copy()
    for key, value in model_data_copy.iteritems():
        if key in exclude:
            model_data.pop(key)
    return model_data

def model_to_data_old(model, exclude=[], include={}):
    """
    serializes model to dictionary (like get_initial_data) but follows fk & m2m fields
    """
    model_data = {}
    for field in model._meta.fields:
        field_name = field.name
        if field_name not in exclude:
            if field_name in include:
                model_data[field_name] = include[field_name]
            else:
                model_data[field_name] = getattr(model,field_name)
    return model_data



def get_data_from_form(form, existing_data={}):

    data = {}

    form_prefix = form.prefix
    for field_name, field in form.fields.iteritems():
        if field_name in existing_data:
            field_value = existing_data[field_name]
        else:
            field_value = form.get_current_field_value(field_name)

        if form_prefix:
            field_key = u"%s-%s" % (form_prefix,field_name)
        else:
            field_key = u"%s" % (field_name)

        # this checks if I am dealing w/ a MultiValueField
        # Django automatically separates this into its constituent fields when gathering data via POST
        # this fn has to do this manually b/c it's called outside of the standard GET/POST view paradigm
        # TODO: AM I SURE THAT THE FIELD_VALUE WILL ALWAYS BE A LIST AND NOT A TUPLE?
        if isinstance(field,MultiValueField) and isinstance(field_value,list):
            for i, v in enumerate(field_value):
                data[u"%s_%s" % (field_key, i)] = v
        else:
            # obviously, a non-MultiValueField is much easier
            data[field_key] = field_value

    return data


def get_data_from_formset(formset):
    data = {}
    existing_data = {}

    for form in formset:
        existing_data.clear()

        # in general, this is only needed when calling this fn outside of the interface
        # ie: in the testing framework
        # (the hidden pk & fk fields do not get passed in via the queryset for existing model formsets)
        if form.instance.pk:
            pk_field_name = formset.model._meta.pk.name
            existing_data[pk_field_name] = form.fields[pk_field_name].initial
        if isinstance(formset,BaseInlineFormSet):
            fk_field_name = formset.fk.name
            existing_data[fk_field_name] = form.fields[fk_field_name].initial

        if formset.can_delete:
            existing_data["DELETE"] = False

        form_data = get_data_from_form(form, existing_data)
        data.update(form_data)

    formset_prefix = formset.prefix
    if formset_prefix:
        total_forms_key = u"%s-TOTAL_FORMS" % (formset_prefix)
        initial_forms_key = u"%s-INITIAL_FORMS" % (formset_prefix)
    else:
        total_forms_key = u"TOTAL_FORMS"
        initial_forms_key = u"INITIALFORMS"
    data[total_forms_key] = formset.total_form_count()
    data[initial_forms_key] = formset.initial_form_count()

    return data

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
# url manipulation #
####################

def add_parameters_to_url(path, **kwargs):
    """
    slightly less error-prone way to add GET parameters to the url
    """
    return path + "?" + urllib.urlencode(kwargs)

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

#################
# FuzzyIntegers #
#################

# this is a very clever idea for comparing integers against min/max bounds
# credit goes to http://lukeplant.me.uk/blog/posts/fuzzy-testing-with-assertnumqueries/

class FuzzyInt(int):

    def __new__(cls, lowest, highest):
        obj = super(FuzzyInt, cls).__new__(cls, highest)
        obj.lowest = lowest
        obj.highest = highest
        return obj

    def __eq__(self, other):
        return other >= self.lowest and other <= self.highest

    def __repr__(self):
        return "[%d..%d]" % (self.lowest, self.highest)

#####################################
# deal w/ hierarchies of components #
#####################################

import mptt
from mptt.fields import TreeForeignKey

def hierarchical(cls):
    TreeForeignKey(cls, null=True, blank=True, related_name='bens_children').contribute_to_class(cls,'parent')
    #ForeignKey(cls, null=True, blank=True,related_name="children").contribute_to_class(cls,'parent')
    #mptt.register(cls)
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
    if fn(item)==True:
      return item
  return None



########################
# flatten a dictionary #
########################

def get_joined_keys_dict(dct):
    """
    Convert 2D dictionary to 1D dictionary joining keys by an underscore.

    >>> dct = {'a': {'b': 1, 'c': 2}}
    >>> get_joined_keys_dict(dct)
    >>> {'a_b': 1, 'a_c': 2}

    :param dict dct: The input dictionary to collapse.
    :rtype: dict
    """

    ret = {}
    for k, v in dct.iteritems():
        for k2, v2 in v.iteritems():
            ret[u'{0}_{1}'.format(k, k2)] = v2
    return ret

################################################


def interate_through_node(node, filter_parameters={}):
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

