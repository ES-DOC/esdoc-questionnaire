####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.core.exceptions import ValidationError
from django.db.models.fields.related import ManyToManyField
from django.utils.deconstruct import deconstructible
from functools import wraps
from jsonschema.exceptions import ValidationError as JSONValidationError
from jsonschema import validate as json_validate
import json
import os
import re
import urllib

from Q.questionnaire import q_logger
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
        super(QError, self).__init__(msg)

        self.msg = msg

        q_logger.exception(self)

    def __str__(self):
        return "QError: " + self.msg


def legacy_code(func):
    """
    decorator that raises an error if a fn is run
    used to mark sections of code as "legacy"
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        msg = "{0} is legacy code".format(func.__name__)
        raise QError(msg)

    return wrapper


####################
# enumerated types #
####################

class EnumeratedType(object):

    def __init__(self, type=None, name=None, description=None):
        self._type = type  # the key of this type
        self._name = name  # the pretty name of this type
        self._description = description  # some descriptive info for this type

    def get_type(self):
        return self._type

    def get_name(self):
        return self._name

    def get_description(self):
        return self._description

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

    def first(self):
        try:
            return self[0]
        except:
            return None

    def last(self):
        try:
            return self[-1]
        except:
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

#######################
# string manipulation #
#######################


def remove_spaces_and_linebreaks(strng):
    return ' '.join(strng.split())


def pretty_string(strng):
    """
    break camelCase string into words
    and turns underscores into spaces
    :param string:
    :return:
    """

    pretty_string_re_1 = re.compile('(.)([A-Z][a-z]+)')
    pretty_string_re_2 = re.compile('([a-z0-9])([A-Z])')

    s1 = pretty_string_re_1.sub(r'\1 \2', strng)
    s2 = pretty_string_re_2.sub(r'\1 \2', s1)
    s3 = s2.replace('_', ' ')

    return s3.title()


def convert_to_camelCase(strng):
    def camelcase():
        yield str.lower
        while True:
            yield str.capitalize
    strng = remove_spaces_and_linebreaks(strng)
    c = camelcase()
    return "".join(c.next()(str(x)) for x in re.split(" |_", strng))

#########################
# sequence manipulation #
#########################


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


def sort_sequence_by_key(sequence, key_name, reverse=False):
    """
    often when setting up initial serializations (especially during testing),
    I pass a list of dictionaries representing a QS to some fn.
    That list may or may not be sorted according to the underlying model's "order" attribute
    This fn sorts the list according to the value of "key" in each list item;
    typically, "key" would match the "order" attribute of the model
    :param key_name: name of key to sort by
    :param list: list to sort
    :return:
    """
    def _sorting_fn(item):
        # using this fn ensures that 'sort_sequence_by_key' will work
        # for a list of dictionaries or a list of objects
        # (the latter is a special use-case; a QS can use the '.order_by' filter, but an actual list of models cannot)
        try:
            return item.get(key_name)
        except AttributeError:
            return getattr(item, key_name)

    sorted_sequence = sorted(
        sequence,
        key=lambda item: _sorting_fn(item),
        reverse=reverse,
    )
    return sorted_sequence

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

####################
# url manipulation #
####################


def add_parameters_to_url(path, **kwargs):
    """
    slightly less error-prone way to add GET parameters to the url
    """
    return path + "?" + urllib.urlencode(kwargs)


#######################
# object manipulation #
#######################

from django.utils.functional import empty as uninitialized_lazy_object
LAZY_OBJECT_NAME = "_wrapped"  # defined here in-case Django changes "django.utils.functional.LazyObject" in the future


def evaluate_lazy_object(obj):
    """
    if this is a LazyObject, then get the actual object rather than the lazy indirection
    written in support of #523 to cope w/ pickling changes _after_ serializing a session
    (recall I cache stuff on the session)
    :param obj: object to evaluate
    :return: evaluated object
    """
    wrapped_obj = getattr(obj, LAZY_OBJECT_NAME, None)
    if wrapped_obj is None:
        # if it isn't a lazy object then just return the original object...
        return obj
    if wrapped_obj is uninitialized_lazy_object:
        # if it is a lazy object but, hasn't been initialized yet
        # then initialize it & return it
        obj._setup()
        return getattr(obj, LAZY_OBJECT_NAME)
    # return the lazy object...
    return wrapped_obj


#################
# serialization #
#################

# in general, I will be using DRF for serialization
# but sometimes (for example, during testing), I don't want that complexity
# in that case, the built-in "model_to_dict" fn doesn't handle ManyToMany fields well
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

#########################
# dealing w/ versioning #
#########################


class Version(object):

    N_BITS = (8, 8, 16)

    def __init__(self, string):
        self.integer = Version.string_to_int(string)
        self.string = string

    def __str__(self):
        return self.string

    def __int__(self):
        return self.integer

    def __eq__(self, other):
        if not other:
            return False

        if isinstance(other, basestring):
            return self == Version(other)
        else:
            return int(self) == int(other)

    def __gt__(self, other):
        if isinstance(other, basestring):
            other = Version(other)
        return int(self) > int(other)

    def __ge__(self, other):
        if isinstance(other, basestring):
            other = Version(other)
        return int(self) >= int(other)

    def __lt__(self, other):
        if isinstance(other, basestring):
            other = Version(other)
        return int(self) < int(other)

    def __le__(self, other):
        if isinstance(other, basestring):
            other = Version(other)
        return int(self) <= int(other)

    # rather than have specific "increment" or "decrement" operators (for major/minor/patch),
    # I just overload "+=" and "-=" b/c I can...

    def __iadd__(self, other):
        # increment a version
        if not isinstance(other, Version):
            other = Version(str(other))
        return Version("{0}.{1}.{2}".format(
            self.major() + other.major(),
            self.minor() + other.minor(),
            self.patch() + other.patch(),
        ))

    def __isub__(self, other):
        # decrement a version
        # (just like __iadd__, except checks we don't go negative)
        if not isinstance(other, Version):
            other = Version(str(other))
        new_major = self.major() - other.major()
        new_minor = self.minor() - other.minor()
        new_patch = self.patch() - other.patch()
        assert new_major >= 0 and new_minor >= 0 and new_patch >= 0, "cannot have a negative version!"
        return Version("{0}.{1}.{2}".format(
            new_major,
            new_minor,
            new_patch,
        ))

    def major(self):
        string = str(self)
        numbers = [int(n) for n in string.split(".")]
        try:
            return numbers[0]
        except IndexError:
            return 0

    def minor(self):
        string = str(self)
        numbers = [int(n) for n in string.split(".")]
        try:
            return numbers[1]
        except IndexError:
            return 0

    def patch(self):
        string = str(self)
        numbers = [int(n) for n in string.split(".")]
        try:
            return numbers[2]
        except IndexError:
            return 0

    def fully_specified(self):
        return "{0}.{1}.{2}".format(
            self.major(),
            self.minor(),
            self.patch(),
        )

    @classmethod
    def string_to_int(cls, string):

        numbers = [int(n) for n in string.split(".")]

        if len(numbers) > len(cls.N_BITS):
            msg = "Versions with more than {0} decimal places are not supported".format(len(Version.N_BITS)-1)
            raise NotImplementedError(msg)

        #  add 0s for missing numbers
        numbers.extend([0] * (len(cls.N_BITS) - len(numbers)))

        #  convert to single int and return
        number = 0
        total_bits = 0
        for n, b in reversed(zip(numbers, cls.N_BITS)):
            max_num = (b+1) - 1
            if n >= 1 << max_num:
                msg = "Number {0} cannot be stored with only {1} bits. Max is {2}".format(n, b, max_num)
                raise ValueError(msg)
            number += n << total_bits
            total_bits += b

        return number

    @classmethod
    def int_to_string(cls, integer):
        number_strings = []
        total_bits = sum(cls.N_BITS)
        for b in Version.N_BITS:
            shift_amount = (total_bits - b)
            number_segment = integer >> shift_amount
            number_strings.append(str(number_segment))
            total_bits = total_bits - b
            integer = integer - (number_segment << shift_amount)

        return ".".join(number_strings)


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

    # TODO: ADD GT / GTE / LT / LTE
    # TODO: ADD NOTIMPLEMENTED ERROR FOR LOGICAL / BITWISE OPERATORS


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

# these next validators just use simple fns
# (therefore they don't work w/ client-side validation)


def validate_password(value):
    # passwords have a minimum length...
    if len(value) < MIN_PASSWORD_LENGTH:
        raise ValidationError("A password must contain at least %s characters.  " % MIN_PASSWORD_LENGTH)
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
        raise ValidationError("Invalid File Extension.")


def validate_file_schema(value, schema_path):
    """
    validator function to use with fileFields;
    validates a file against a JSON Schema.
    """
    try:
        with open(schema_path, 'r') as file:
            schema = json.load(file)
        file.closed
    except IOError:
        msg = "Unable to read from {0}".format(schema_path)
        raise ValidationError(msg)
    except ValueError:
        msg = "Malformed JSON content in {0}".format(schema_path)
        raise ValidationError(msg)

    content = json.load(value)
    validate_schema(content, schema)


def validate_schema(value, schema):
    try:
        json_validate(value, schema)
    except JSONValidationError as e:
        raise ValidationError(e.message)
