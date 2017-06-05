####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import models
from django.db.models.signals import post_delete
from django.forms import CharField
from jsonschema.exceptions import ValidationError as JSONValidationError
from jsonschema.validators import validate as json_validate
import contextlib
import json
import os
import re
import types

from Q.questionnaire.q_utils import Version, EnumeratedType, EnumeratedTypeList, sort_sequence_by_key
from Q.questionnaire.q_constants import *

##############################################################
# some clever ways of dealing w/ unsaved relationship fields #
##############################################################


@contextlib.contextmanager
def allow_unsaved_fk(model_class, field_names):
    """"
    temporarily allows the fk "model_class.field_name" to point to a model not yet saved in the db
    that used to be the default behavior in Django <= 1.6
    (see https://www.caktusgroup.com/blog/2015/07/28/using-unsaved-related-models-sample-data-django-18/)
    """
    assert isinstance(field_names, list), "allow_unsaved_fk takes a list of fields, not a single field"

    field_saved_values = {}
    for field_name in field_names:
        model_field = model_class._meta.get_field(field_name)
        field_saved_values[model_field] = model_field.allow_unsaved_instance_assignment
        model_field.allow_unsaved_instance_assignment = True

    yield

    for field, saved_value in field_saved_values.iteritems():
        field.allow_unsaved_instance_assignment = saved_value


class QUnsavedManager(models.Manager):
    """
    a manager to cope w/ UNSAVED models being used in m2m fields (actually, it is usually used w/ the reverse of fk fields)
    (this is not meant to be possible in Django)
    The manager accomplishes this by storing the would-be field content in an instance variable;
    in the case of unsaved models, this is purely done to get around Django ickiness
    in the case of saved models, this is done so that QuerySets are never cloned (which would overwrite in-progress data)
    a side-effect of this technique is that the output of this manager is not chainable;
    but the Q doesn't use standard Django methods for saving models (instead serializing from JSON), so I don't really care
    """

    def get_cached_qs_name(self):
        """
        overwrite this as needed for different types of managers
        :return: a unique name to represent the cached queryset of saved & unsaved instances
        """
        return "_cached_{0}".format(
            self.field_name
        )

    def get_real_field_manager(self):
        """
        overwrite this as needed for different types of managers
        :return: the _real_ model manager used by this field
        """
        field_name = self.field_name
        return getattr(self.instance, field_name)

    def count(self):
        return len(self.get_query_set())

    def all(self):
        return self.get_query_set()

    def get(self, *args, **kwargs):
        filtered_qs = self.filter_potentially_unsaved(*args, **kwargs)
        n_filtered_qs = len(filtered_qs)
        if n_filtered_qs == 0:
            msg = "{0} matching query does not exist".format(self.model)
            raise ObjectDoesNotExist(msg)
        elif n_filtered_qs > 1:
            msg = "get() returned more than 1 {0} -- it returned {1}!".format(self.model, n_filtered_qs)
            raise MultipleObjectsReturned(msg)
        else:
            return filtered_qs[0]

    def order_by(self, key, **kwargs):
        cached_qs = self.get_query_set()
        sorted_qs = sorted(
            cached_qs,
            key=lambda o: getattr(o, key),
            reverse=kwargs.pop("reverse", False),
        )
        return sorted_qs

    def get_query_set(self):
        instance = self.instance
        cached_qs_name = self.get_cached_qs_name()
        if not hasattr(instance, cached_qs_name):
            field_manager = self.get_real_field_manager()
            saved_qs = field_manager.all()
            unsaved_qs = []
            cached_qs = list(saved_qs) + unsaved_qs
            setattr(instance, cached_qs_name, cached_qs)
        return getattr(instance, cached_qs_name)

    # unlike the above fns, I cannot simply overload the 'add' or 'remove' fns
    # b/c managers are created dynamically in "django.db.models.fields.related.py#create_foreign_related_manager"
    # Django is annoying

    def add_potentially_unsaved(self, *objs):
        instance = self.instance
        cached_qs = self.get_query_set()
        objs = list(objs)

        unsaved_objs = [o for o in objs if
                        o.pk is None or instance.pk is None]  # (unsaved can refer to either the models to add or the model to add to)
        saved_objs = [o for o in objs if o not in unsaved_objs]

        for obj in objs:
            if not isinstance(obj, self.model):
                raise TypeError("'%s' instance expected, got %r" % (self.model._meta.object_name, obj))
            if obj not in cached_qs:
                cached_qs.append(obj)
        setattr(
            instance,
            self.get_cached_qs_name(),
            cached_qs,
        )

        # even though I am not saving models w/ these custom managers in the normal Django way,
        # I go ahead and add what I can using normal Django methods (just to avoid any confusion later)...
        if saved_objs:
            self.add(*saved_objs)

    def remove_potentially_unsaved(self, *objs):
        instance = self.instance
        cached_qs = self.get_query_set()
        objs = list(objs)

        unsaved_objs = [o for o in objs if
                        o.pk is None or instance.pk is None]  # (unsaved can refer to either the models to add or the model to add to)
        saved_objs = [o for o in objs if o not in unsaved_objs]

        for obj in objs:
            cached_qs.remove(obj)
        setattr(
            instance,
            self.get_cached_qs_name(),
            cached_qs,
        )

        # even though I am not saving models w/ these custom managers in the normal Django way,
        # I go ahead and remove what I can using normal Django methods (just to avoid any confusion later)...
        if saved_objs:
            self.remove(*saved_objs)

    # and I have to define filter separately, b/c the parent 'filter' fn is used internally by other code

    def filter_potentially_unsaved(self, *args, **kwargs):
        cached_qs = self.get_query_set()
        filtered_qs = filter(
            lambda o: all([getattr(o, key) == value for key, value in kwargs.items()]),
            cached_qs
        )
        return filtered_qs


class QUnsavedRelatedManager(QUnsavedManager):

    use_for_related_fields = True

    def get_cached_qs_name(self):
        """
        overwritten from parent manager class
        :return
        """
        related_field = self.model.get_field(self.field_name).related
        return "_cached_{0}".format(
            related_field.name
        )

    def get_real_field_manager(self):
        """
        overwritten from parent manager class
        :return:
        """
        related_field = self.model.get_field(self.field_name).related
        return getattr(self.instance, related_field.name)


#######################################
# the types of fields used by the CIM #
#######################################


class QPropertyType(EnumeratedType):

    def __str__(self):
        return "{0}".format(self.get_type())

QPropertyTypes = EnumeratedTypeList([
    QPropertyType("ATOMIC", "Atomic"),
    QPropertyType("RELATIONSHIP", "Relationship"),
    QPropertyType("ENUMERATION", "Enumeration"),
])


class QAtomicType(EnumeratedType):

    def __str__(self):
        return "{0}".format(self.get_type())

# TODO: GET DATE/DATETIME/TIME TO RENDER NICELY IN BOOTSTRAP...

QAtomicTypes = EnumeratedTypeList([
    QAtomicType("DEFAULT", "Character Field (default)"),
    # QAtomicType("STRING", "Character Field (default)"),
    QAtomicType("TEXT", "Text Field (large block of text as opposed to a small string)"),
    QAtomicType("BOOLEAN", "Boolean Field"),
    QAtomicType("INTEGER", "Integer Field"),
    QAtomicType("DECIMAL", "Decimal Field"),
    QAtomicType("URL", "URL Field"),
    QAtomicType("EMAIL", "Email Field"),
    QAtomicType("DATE", "Date Field"),
    QAtomicType("DATETIME", "Date Time Field"),
    QAtomicType("TIME", "Time Field"),
])

from django.forms.widgets import *
from djng.forms.widgets import *

ATOMIC_PROPERTY_MAP = {
    # maps the above QAtomicTypes to their corresponding widget classes,
    # to be used by "forms.forms_realizations.QPropertyRealizationForm#customize"
    QAtomicTypes.DEFAULT.get_type(): [TextInput, {}],
    QAtomicTypes.TEXT.get_type(): [Textarea, {"rows": 4}],
    QAtomicTypes.BOOLEAN.get_type(): [CheckboxInput, {}],
    QAtomicTypes.INTEGER.get_type(): [NumberInput, {}],
    QAtomicTypes.DECIMAL.get_type(): [NumberInput, {}],
    QAtomicTypes.URL.get_type(): [URLInput, {}],
    QAtomicTypes.EMAIL.get_type(): [EmailInput, {}],
    # TODO: GET THESE WORKING IN BOOTSTRAP / DJANGULAR
    QAtomicTypes.DATE.get_type(): [TextInput, {}],
    QAtomicTypes.DATETIME.get_type(): [TextInput, {}],
    QAtomicTypes.TIME.get_type(): [TextInput, {}],
}


class QNillableType(EnumeratedType):

    def __str__(self):
        return self.get_name()

QNillableTypes = EnumeratedTypeList([
    QNillableType(nil_reason[0].upper(), "{0}:{1}".format(NIL_PREFIX, nil_reason[0]), nil_reason[1])
    for nil_reason in NIL_REASONS
])

##################################
# field for storing JSON content #
##################################


class QJSONField(models.TextField):
    """
    encodes JSON in a text field
    optionally validates against a JSON Schema
    which gets passed in as a callable (so I can bind the schema at run-time rather than hard-coding it beforehand)
    """

    def __init__(self, *args, **kwargs):
        self.json_schema_fn = kwargs.pop("schema", None)
        if self.json_schema_fn:
            assert callable(self.json_schema_fn)
        super(QJSONField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        """
        db to code; text to JSON object
        """
        if value is None:
            return None
        try:
            # sometimes it's not _clean_ JSON,
            # (for example, fixtures pollute these strings w/ unicode garbage)
            # so clean it up here...
            clean_value = re.sub(r"(u')(.*?)(')", r'"\2"', value)
            json_content = json.loads(clean_value)
            if self.json_schema_fn:
                json_validate(json_content, self.json_schema_fn())
            return json_content
        except ValueError:
            msg = "Malformed content used in {0}: '{1}'.".format(
                self.__class__.__name__,
                clean_value
            )
            raise DjangoValidationError(msg)
        except JSONValidationError as e:
            msg = "Content used in {0} does not conform to schema: {1}".format(
                self.__class__.__name__,
                e.message
            )
            raise DjangoValidationError(msg)

    def get_prep_value(self, value):
        """
        code to db; JSON to text
        """
        if value is None:
            return None
        try:
            if self.json_schema_fn:
                json_validate(value, self.json_schema_fn())
            return json.dumps(value)
        except ValueError:
            msg = "Malformed content used in {0}: '{1}'.".format(
                self.__class__.__name__,
                value
            )
            raise DjangoValidationError(msg)
        except JSONValidationError as e:
            msg = "Content used in {0} does not conform to schema: {1}".format(
                self.__class__.__name__,
                e.message
            )
            raise DjangoValidationError(msg)

    def from_db_value(self, value, expression, connection, context):
        """
        does the same thing as "to_python",
        it's just called in different situations b/c of a quirk w/ Django 1.8
        (see https://docs.djangoproject.com/en/1.8/howto/custom-model-fields/)
        """
        return self.to_python(value)

######################
# enumeration fields #
######################

# this is mostly the same as a QJSONField
# w/ some additional fns displaying things nicely - and interactively - in the form

ENUMERATION_OTHER_PREFIX = "other"
ENUMERATION_OTHER_CHOICE = "---OTHER---"
ENUMERATION_OTHER_PLACEHOLDER = "Please enter a custom value"
ENUMERATION_OTHER_DOCUMENTATION = "<em>Select this option to add a custom value for this property.</em>"

from django.forms.fields import MultipleChoiceField


class QEnumerationFormField(MultipleChoiceField):

    # TODO: I WOULD RATHER JUST RELY ON QEnumerationFormField BEING SETUP CORRECTLY BY QEnumerationField BELOW
    # TODO: BUT THE CODE IN "QPropertyRealization.__init__" DOESN'T SEEM TO WORK,
    # TODO: SO I UPDATE THE FORM FIELD DIRECTLY IN "QPropertyRealizationForm.customize"
    # TODO: SEE THE COMMENTS THERE FOR MORE INFO

    def __init__(self, *args, **kwargs):
        is_multiple = kwargs.pop("is_multiple", False)
        display_all = kwargs.pop("display_all", False)
        complete_choices = kwargs.pop("complete_choices", [])

        choices = [(c.get("value"), c.get("value")) for c in complete_choices]
        kwargs["choices"] = choices
        super(QEnumerationFormField, self).__init__(*args, **kwargs)

        self._complete_choices = complete_choices
        self._is_multiple = is_multiple
        self._display_all = display_all

    @property
    def is_multiple(self):
        # (need to pass a string b/c this will be used as the argument to an NG directive)
        return json.dumps(self._is_multiple)

    @property
    def display_all(self):
        # (need to pass a string b/c this will be used as the argument to an NG directive)
        return json.dumps(self._display_all)

    @property
    def complete_choices(self):
        # (need to pass a string b/c this will be used as the argument to an NG directive)
        return json.dumps(self._complete_choices)


class QEnumerationField(QJSONField):

    def __init__(self, *args, **kwargs):
        super(QEnumerationField, self).__init__(*args, **kwargs)
        self._complete_choices = []
        self._is_multiple = False
        self._display_all = False

    @property
    def is_multiple(self):
        return self._is_multiple

    @is_multiple.setter
    def is_multiple(self, is_multiple):
        self._is_multiple = is_multiple

    @property
    def complete_choices(self):
        return sort_sequence_by_key(
            self._complete_choices,
            "order"
        )

    @complete_choices.setter
    def complete_choices(self, complete_choices):
        self._complete_choices = complete_choices

    @property
    def display_all(self):
        return self._display_all

    @display_all.setter
    def display_all(self, display_all):
        self._display_all = display_all

    def formfield(self, **kwargs):
        new_kwargs = {
            "label": self.verbose_name,
            "is_multiple": self.is_multiple,
            "display_all": self.display_all,
            "complete_choices": self.complete_choices,
        }
        new_kwargs.update(kwargs)

        return QEnumerationFormField(**new_kwargs)


###############
# file fields #
###############


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
        return name


class QFileField(models.FileField):
    """
    just like a standard Django FileField,
    except it uses the above OverwriteStorage class,
    and it deletes the file when the corresponding class instance is deleted
    (so long as no other class members are using it)
    """

    default_help_text = "Note that files with the same names will be overwritten"

    def __init__(self, *args, **kwargs):
        """
        ensure that OverwriteStorage is used,
        and provide help_text (if none was specified)
        :param args:
        :param kwargs:
        :return:
        """

        help_text = kwargs.pop("help_text", self.default_help_text)
        kwargs.update({
            "storage": OverwriteStorage(),
            "help_text": help_text
        })
        super(QFileField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        """
        attach the "post_delete" signal of the model class
        to the "delete_file" fn of the field class
        :param cls:
        :param name:
        :return: None
        """
        super(QFileField, self).contribute_to_class(cls, name, **kwargs)
        post_delete.connect(self.delete_file, sender=cls)

    def delete_file(self, sender, **kwargs):
        """
        delete the file iff no other class instance point to it
        :param sender:
        :return: None
        """
        instance = kwargs.pop("instance")
        instance_field_name = self.name
        instance_field = getattr(instance, instance_field_name)
        filter_parameters = {
            instance_field_name: instance_field.name,
        }
        other_instances_with_same_file = sender.objects.filter(**filter_parameters)
        if not len(other_instances_with_same_file):
            # if there are no other instances w/ the same file...
            # delete the file...
            instance_field.delete(save=False)  # save=False prevents model from re-saving itself


##################
# version fields #
##################

class QVersionFormField(CharField):

    def clean(self, value):
        # check string format (only numbers and the '.' character

        if not re.match(r'^([0-9]\.?)+$', value):
            msg = "Versions must be of the format 'major.minor.patch'"
            raise DjangoValidationError(msg)

        return value


class QVersionField(models.IntegerField):

    # TODO: models w/ this field have to call refresh_from_db if set manually
    # TODO: (ie: if set in tests)

    def formfield(self, **kwargs):
        default_kwargs = {
            "form_class": QVersionFormField,
        }
        default_kwargs.update(kwargs)
        return super(QVersionField, self).formfield(**default_kwargs)

    def to_python(self, value):
        """
        db to code; int to Version
        """
        if isinstance(value, Version):
            return value

        if isinstance(value, basestring):
            return Version(value)

        if value is None:
            return None

        return Version(Version.int_to_string(value))

    def get_prep_value(self, value):
        """
        code to db; Version to int
        """
        if isinstance(value, basestring):
            return Version.string_to_int(value)

        if value is None:
            return None

        return int(value)

    def from_db_value(self, value, expression, connection, context):
        """
        does the same thing as "to_python",
        it's just called in different situations b/c of a quirk w/ Django 1.8
        (see https://docs.djangoproject.com/en/1.8/howto/custom-model-fields/)
        """
        return self.to_python(value)

    def contribute_to_class(self, cls, name, **kwargs):
        """
        adds "get/<field_name>_major/minor/patch" fns to the class
        :param cls:
        :param name:
        :param kwargs:
        :return:
        """
        super(QVersionField, self).contribute_to_class(cls, name, **kwargs)

        def _get_major(instance, field_name=name):
            """
            notice how I pass the name of the field from the parent "contribute_to_class" fn;
            this lets me access it from the instance
            :param instance:
            :param field_name:
            :return:
            """
            version_value = getattr(instance, field_name)
            return version_value.major()

        def _get_minor(instance, field_name=name):
            """
            notice how I pass the name of the field from the parent "contribute_to_class" fn;
            this lets me access it from the instance
            :param instance:
            :param field_name:
            :return:
            """
            version_value = getattr(instance, field_name)
            return version_value.minor()

        def _get_patch(instance, field_name=name):
            """
            notice how I pass the name of the field from the parent "contribute_to_class" fn;
            this lets me access it from the instance
            :param instance:
            :param field_name:
            :return:
            """
            version_value = getattr(instance, field_name)
            return version_value.patch()

        get_major_fn_name = u"get_{0}_major".format(name)
        get_minor_fn_name = u"get_{0}_minor".format(name)
        get_patch_fn_name = u"get_{0}_patch".format(name)
        setattr(cls, get_major_fn_name, types.MethodType(_get_major, None, cls))
        setattr(cls, get_minor_fn_name, types.MethodType(_get_minor, None, cls))
        setattr(cls, get_patch_fn_name, types.MethodType(_get_patch, None, cls))
