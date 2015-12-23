####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

"""
.. module:: q_utils

utility fns used by the Q
"""

from django.core.exceptions import ValidationError
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.utils.deconstruct import deconstructible
from django.forms.fields import MultiValueField
from django.forms.models import BaseInlineFormSet
from lxml import etree as et
import urllib
import re
import os

from Q.questionnaire.q_constants import *

rel = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)


##################
# error handling #
##################

class QError(Exception):
    """
    Custom exception class

    .. note:: As the CIM Questionnaire is a web-application, it often makes more sense to use the :func`questionnaire.q_error` view with an appropriate message instead of raising an explicit QError

    """

    def __init__(self, msg='unspecified questionnaire error'):
        self.msg = msg

    def __str__(self):
        return "QError: " + self.msg


####################
# enumerated types #
####################

class EnumeratedType(object):

    def __init__(self, type=None, name=None):
        self._type = type  # the key of this type
        self._name = name  # the pretty name of this type

    def get_type(self):
        return self._type

    def get_name(self):
        return self._name

    # comparisons are made via the _type attribute...
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            # comparing two enumeratedtypes
            return self.get_type() == other.get_type()
        else:
            # comparing an enumeratedtype with a string
            return self.get_type() == other

    def __ne__(self, other):
        return not self.__eq__(other)


class EnumeratedTypeError(Exception):

    def __init__(self, msg='invalid enumerated type'):
        self.msg = msg

    def __str__(self):
        return "EnumeratedTypeError: " + self.msg


class EnumeratedTypeList(list):

    def __getattr__(self, etype):
        for et in self:
            if et.get_type() == etype:
                return et
        raise EnumeratedTypeError("unable to find %s" % str(etype))

    def get(self, etype):
        for et in self:
            if et.get_type() == etype:
                return et
        return None

    # a method for sorting these lists
    # order is a list of EnumeratatedType._types
    @classmethod
    def comparator(cls, et, et_list):
        etype = et.get_type()
        if etype in et_list:
            # if the type being compared is in the orderList, return it's position
            return et_list.index(etype)
        # otherwise return a value greater than the last position of the orderList
        return len(et_list)+1


##############
# validators #
##############

# in order for these validators to be handled by migration,
# I have to explicitly add a "deconstruct" fn
# (see https://code.djangoproject.com/ticket/21275#comment:3)

@deconstructible
class QValidator(object):
    """
    Some of these validators can be used by Angular for client-side validation
    this just requires that there is a suitable js fn to do the actual work
    (I've made a design decision not to validate via AJAX - it defeats the purpose of client-side validation)
    """

    def __call__(self, value):
        # this is not very Pythonic
        # but it does ensure that every validator works as a "custom_potential_error" in the form
        assert False, "validators must define a __call__ method"

    def __init__(self):
        assert hasattr(self, "name"), "validators must have a name"
        assert hasattr(self, "msg"), "validators must have an error msg"
        # force name to have no spaces, underscores, or uppercases
        # (JavaScript / Angular is picky)
        self.name = self.name.replace(' ', '').replace('_', '').lower()


BAD_CHARS = "\ / < > % # % { } [ ] $ |"
BAD_CHARS_REGEX = "[\\\/<>&#%{}\[\]\$\|]"
BAD_CHARS_LIST = ", ".join(BAD_CHARS.split(' '))

class ValidateNoBadChars(QValidator):

    name = "ValidateNoBadChars"
    msg = u"Value may not contain any of the following characters: '%s'." % BAD_CHARS_LIST

    def __call__(self, value):
        if re.search(BAD_CHARS_REGEX, value):
            raise ValidationError(self.msg)

validate_no_bad_chars = ValidateNoBadChars()

class ValidateNotBlank(QValidator):
    """
    validator function to use with charFields;
    ensures there is more than just whitespace in the field
    """
    name = "ValidateNotBlank"
    msg = u"Value must have content"

    def __call__(self, value):
        if not value.strip():
            raise ValidationError(self.msg)

validate_not_blank = ValidateNotBlank()

class ValidateNoSpaces(QValidator):
    """
    validator function to use with charFields;
    ensures there is no whitespace in the field
    """
    name = "ValidateNoSpaces"
    msg = u"Value may not contain spaces."

    def __call__(self, value):
        if ' ' in value:
            raise ValidationError(self.msg)

validate_no_spaces = ValidateNoSpaces()

class ValidateNoReservedWords(QValidator):
    """
    validator function to use with charFields;
    ensures specified words are not used
    """
    name = "ValidateNoReservedWords"
    msg = u"This is a reserved word."

    def __call__(self, value):
        if value.lower() in RESERVED_WORDS:
            raise ValidationError(self.msg)

validate_no_reserved_words = ValidateNoReservedWords()

class ValidateNoProfanities(QValidator):
    """
    validator function to use with charFields;
    ensures profane words are not used
    """
    name = "ValidateNoProfanities"
    msg = u"Watch your language!"

    def __call__(self, value):
        for profanity in PROFANITIES_LIST:
            # this is subject to the "scunthorpe problem" by checking for word fragments...
            # if profanity in value:
            #     raise ValidationError(self.msg)

            # this tries to avoid the "scunthorpe problem" by only checking for complete words...
            if re.search(r"\b" + re.escape(profanity) + r"\b", value):
                raise ValidationError(self.msg)

validate_no_profanities = ValidateNoProfanities()

#############################################

# validators below this line use simple fns
# (they don't work w/ client-side validation)

def validate_password(value):
    # passwords have a minimum length...
    if len(value) < PASSWORD_LENGTH:
        raise ValidationError("A password must contain at least %s characters.  " % PASSWORD_LENGTH)
    # and a mixture of letters and non-letters...
    if not (re.match(r'^.*[A-Za-z]', value) and
            re.match(r'^.*[0-9!@#$%^&*()\-_=+.,?:;></\\\[\]\{\}]', value)):
        raise ValidationError("A password must contain both letters and non-letters.  ")


def validate_file_extension(value, valid_extensions):
    """
    Validator function to use with fileFields.
    Ensures the file attempting to be uploaded matches a set of extensions.
    :param value: file being validated
    :param valid_extensions: list of valid extensions
    """
    if not value.name.split(".")[-1] in valid_extensions:
        raise ValidationError(u'Invalid File Extension.  ')


def validate_file_schema(value, schema_path):
    """
    validator function to use with fileFields;
    validates a file against an XML Schema.
    """

    contents = et.parse(value)

    try:
        schema = et.XMLSchema(et.parse(schema_path))
    except IOError:
        msg = "Unable to find suitable schema to validate file against (%s).  " % schema_path
        raise ValidationError(msg)

    try:
        schema.assertValid(contents)
    except et.DocumentInvalid as e:
        msg = "Invalid File Contents: %s" % str(e)
        raise ValidationError(msg)


####################
# xml manipulation #
####################

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


def get_tag_without_namespace(node):
    """
    gets tag from lxml element but w/out embedded namespace
    (and w/out dealing w/ all the complexity of namespace managers)
    this allows me to perform comparisons (in tests)
    :param node: lxml element node
    :return: string tag
    """
    full_tag = node.tag
    return full_tag.split("}")[-1]


def get_attribute_without_namespace(node,attribute_name):
    """
    gets tag from lxml element but w/out embedded namespace
    (and w/out dealing w/ all the complexity of namespace managers)
    this allows me to perform comparisons (in tests)
    :param node: lxml element node
    :param attribute_name: name of attribute to search for
    :return: attribute value (or None if not found)
    """
    attributes = node.attrib
    for key, value in attributes.iteritems():
        key_without_namespace = key.split("}")[-1]
        if attribute_name == key_without_namespace:
            return value
    return None

def get_index(lst, i):
    """
    gets index from list only if it exists
    (used to deal w/ XML nodes in registration fns)
    :param lst: list to search
    :param i: index to find
    :return: item or None
    """
    try:
        return lst[i]
    except IndexError:
        return None


#######################
# string manipulation #
#######################

def remove_spaces_and_linebreaks(str):
    return ' '.join(str.split())


def pretty_string(string):
    """
    break camelCase string into words
    :param string:
    :return:
    """

    pretty_string_re_1 = re.compile('(.)([A-Z][a-z]+)')
    pretty_string_re_2 = re.compile('([a-z0-9])([A-Z])')

    s1 = pretty_string_re_1.sub(r'\1 \2', string)
    s2 = pretty_string_re_2.sub(r'\1 \2', s1)
    return s2.title()


####################
# url manipulation #
####################

def add_parameters_to_url(path, **kwargs):
    """
    slightly less error-prone way to add GET parameters to the url
    """
    return path + "?" + urllib.urlencode(kwargs)


#####################
# list manipulation #
#####################

def sort_list_by_key(list, key_name, reverse=False):
    """
    often when setting up initial serializations (especially during testing),
    I pass a list of dictionaries representing a QS to some fn.
    That list may or may not be sorted according to the underlying model's "order" attribute
    This fn sorts the list according to the value of "key" in each list item;
    typically, "key" should match the "order" attribute of the model
    :param key_name: name of key to sort by
    :param list: list to sort
    :return:
    """
    sorted_list = sorted(
        list,
        key=lambda item: item.get(key_name),
        reverse=reverse,
    )
    return sorted_list


#############################
# form / field manipulation #
#############################

def set_field_widget_attributes(field, widget_attributes):
    """
    set a Django field widget attribute
    :param field: form field to modify
    :param widget_attributes: dictionary of widget attributes
    :return:
    """
    for (key, value) in widget_attributes.iteritems():
        field.widget.attrs[key] = value
        if key == "class":
            # djangular overwrites widget classes using the built-in "widget_css_classes" attribute
            # so be sure to re-set it here
            field.widget_css_classes = value


def update_field_widget_attributes(field, widget_attributes):
    """
    rather than overriding an attribute (as above),
    this fn appends it to any existing ones
    as with class='old_class new_class'
    :param field: form field to modify
    :widget_attributes: dictionary of widget attributes
    """
    for (key,value) in widget_attributes.iteritems():
        try:
            current_attributes = field.widget.attrs[key]
            field.widget.attrs[key] = "%s %s" % (current_attributes, value)
        except KeyError:
            field.widget.attrs[key] = value
        if key == "class":
            # djangular overwrites widget classes using the built-in "widget_css_classes" attribute
            # so be sure to re-set it here
            try:
                current_widget_css_classes = field.widget_css_classes
                field.widget_css_classes = "%s %s" % (current_widget_css_classes, value)
            except AttributeError:
                field.widget_css_classes = value

def get_data_from_form(form, include={}):
    """
    returns a dictionary of form field names / values
    this works regardless of whether the form is bound or not
    :param form: the form to check
    :param existing_data: an existing dictionary to use
    :return:
    """

    data = {}

    # just in-case I specified a field name to include
    # that doesn't exist in this form,
    # add it anyway
    # (I'm assuming I know what I'm doing!)
    for included_key, included_value in include.iteritems():
        if included_key not in form.fields.keys():
            data[included_key] = included_value

    form_prefix = form.prefix
    for field_name, field in form.fields.iteritems():

        if form_prefix:
            field_key = u"%s-%s" % (form_prefix, field_name)
        else:
            field_key = field_name

        if field_name in include:
            field_value = include[field_name]

        else:
            try:
                field_value = form.data[field_key]
            except KeyError:
                field_value = field.initial
                # TODO: CHECK THAT I CONSISTENTLY USE "field.initial" INSTEAD OF "form.initial[field_name]"
                # try:
                #     field_value = form.initial[field_name]
                # except KeyError:
                #     msg = "unable to find %s in %s" % (field_key, form)
                #     raise KeyError(msg)

        if isinstance(field, MultiValueField) and isinstance(field_value, list):
            for i, v in enumerate(field_value):
                data[u"%s_%s" % (field_key, i)] = v
        else:
            data[field_key] = field_value

    return data


def get_data_from_formset(formset, include={}):

    data = {}
    current_data = {}

    for form in formset:
        current_data.clear()
        current_data.update(include)

        # (the hidden pk & fk fields do not get passed in via the queryset for existing model formsets)
        pk_field_name = formset.model._meta.pk.name
        current_data[pk_field_name] = form.fields[pk_field_name].initial
        if isinstance(formset, BaseInlineFormSet):
            fk_field_name = formset.fk.name
            current_data[fk_field_name] = form.fields[fk_field_name].initial

        if formset.can_delete:
            current_data["DELETE"] = False

        form_data = get_data_from_form(form, current_data)
        data.update(form_data)

    formset_prefix = formset.prefix
    if formset_prefix:
        total_forms_key = u"%s-TOTAL_FORMS" % formset_prefix
        initial_forms_key = u"%s-INITIAL_FORMS" % formset_prefix
    else:
        total_forms_key = u"TOTAL_FORMS"
        initial_forms_key = u"INITIAL_FORMS"
    data[total_forms_key] = formset.total_form_count()
    data[initial_forms_key] = formset.initial_form_count()

    return data


#################
# serialization #
#################

# in general, I will be using DRF for serialization
# but sometimes, I don't want that complexity
# in that case, the built-in "model_to_dict" fn doesn't handle m2m fields well
# so I use this instead...

def serialize_model_to_dict(model, **kwargs):
    include = kwargs.pop("include", {})  # a dict of pre-computed values to replace
    exclude = kwargs.pop("exclude", [])  # a list of field names to ignore

    _dict = include
    for field in model._meta.concrete_fields + model._meta.many_to_many:
        field_name = field.name
        if field_name not in include and field_name not in exclude:
            if isinstance(field, ManyToManyField):
                if model.pk is None:
                    _dict[field_name] = []
                else:
                    _dict[field_name] = list(field.value_from_object(model).values_list('pk', flat=True))
            else:
                _dict[field.name] = field.value_from_object(model)
    return _dict


def deserialize_dict_to_model(model, dct):
    """
    lets me map a dictionary of field/value pairs onto a model
    see the serialization classes "update" fn for usage examples
    """
    for key, value in dct.iteritems():
        setattr(model, key, value)


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


#############################################
# finds matching item in list               #
# (using these fns instead of standard loop #
# b/c it doesn't traverse the whole list)   #
#############################################

def find_in_sequence(fn, sequence):
    for item in sequence:
        if fn(item) == True:
            return item
    return None

def find_dict_in_sequence(dct, sequence):

    # like above, but rather than passing a fn
    # passes a dictionary of attribute values to test

    def _is_dict_in_item(item):
        for k, v in dct.iteritems():
            if not hasattr(item, k) or getattr(item, k) != v:
                return False
        return True

    return find_in_sequence(lambda item: _is_dict_in_item(item), sequence)

########################
# flatten a dictionary #
########################

# TODO: THIS CAN BE REMOVED ONCE REALIZATIONS ARE CONVERTED TO RESTFUL STUFF

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

###########################
# iterate through options #
###########################

from collections import namedtuple
import itertools


def itr_row(key, sequence):
    for element in sequence:
        yield ({key: element})


def itr_product_keywords(keywords, as_namedtuple=False):
    if as_namedtuple:
        yld_tuple = namedtuple('ITesterKeywords', keywords.keys())

    iterators = [itr_row(ki, vi) for ki, vi in keywords.iteritems()]
    for dictionaries in itertools.product(*iterators):
        yld = {}
        for dictionary in dictionaries:
            yld.update(dictionary)
        if as_namedtuple:
            yld = yld_tuple(**yld)
        yield yld

# sample usage...
#
#     def test_iter(self):
#
#         standard_property_displayed_values = [True, False]
#         standard_property_inherited_values = [True, False]
#         standard_property_values_to_iterate_over = {
#             "displayed" : standard_property_displayed_values,
#             "inherited" : standard_property_inherited_values,
#         }
#
#         for k in itr_product_keywords(standard_property_values_to_iterate_over):
#               for field_name, field_value in k.iteritems():
#                   standard_property_customizers[i].setattr(field_name,field_value)
#
#               if an-exeception-happens:
#                   if k has invalid values:
#                       continue
#                   else:
#                       raise
