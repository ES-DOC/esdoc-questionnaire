####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'


from django.core.exceptions import ValidationError as DjangoValidationError, ObjectDoesNotExist
from django.db.models.fields.related import RelatedField
from django.utils.translation import ugettext_lazy as _

from rest_framework.serializers import ModelSerializer, ListSerializer, Field as SerializerField, LIST_SERIALIZER_KWARGS
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty
from rest_framework.fields import SkipField
from rest_framework.compat import OrderedDict
from rest_framework.settings import api_settings

from ast import literal_eval

from Q.questionnaire.q_utils import QError, pretty_string, serialize_model_to_dict
from Q.questionnaire.q_fields import allow_unsaved_fk

################################
# custom serializer validators #
################################

class QUniqueTogetherValidator(UniqueTogetherValidator):
    """
    Just like the base class...
    except that the validation error is placed on the individual fields rather than the form as a whole
    (this lets users view the error in the template better, especially if some of the unique fields are hidden)
    also, I allow some fields to be missing on the assumption that (if they are fk to the parent model), they will be set later on
    """

    def __init__(self, *args, **kwargs):
        """
        automatically works out the queryset and unique_fields based on the model this validator is being applied to
        :param args:
        :param kwargs:
        :return:
        """
        assert "fields" in kwargs and "queryset" in kwargs, "'fields' and 'queryset' are required arguments to QUniqueTogetherValidator"
        kwargs.update({
            "message": _("An instance with this {pretty_field_names} already exists."),
        })
        super(QUniqueTogetherValidator, self).__init__(*args, **kwargs)
        self.model = None  # this gets reset in "set_context" below
        self.exempt_fields = []  # this gets reset in "set_context" below

    def __call__(self, attrs):
        """
        this is basically like the parent class __call__ fn,
        except that I allow certain missing fields for new instances,
        and any error messages are spread out among all the "unique_together" fields
        """

        # if this is a CREATE then check for missing fields;
        # so long as the missing field is exempt, assume it will be added in later
        # and the model will validate eventually
        missing_fields = None
        if self.instance is None:
            missing_fields = dict([
              (field_name, self.missing_message)
                for field_name in self.fields
                if field_name not in attrs
            ])
            if set(missing_fields.keys()) - set(self.exempt_fields):
                raise ValidationError(missing_fields)

        # If this is an UPDATE, then any unprovided field should
        # have it's value set based on the existing instance attribute.
        if self.instance is not None:
            for field_name in self.fields:
                if field_name not in attrs:
                    attrs[field_name] = getattr(self.instance, field_name)

        # narrow down the queryset...
        queryset = self.queryset
        filter_kwargs = dict([
            (field_name, attrs[field_name])
            for field_name in self.fields
            if field_name in attrs
        ])
        queryset = queryset.filter(**filter_kwargs)
        if self.instance is not None:
            # "self.instance" will have been set by "QSerializer.to_internal_value" below
            queryset = queryset.exclude(pk=self.instance.pk)

        if not missing_fields and queryset.exists():
            # the validation error is a dictionary of strings keyed by field_name
            # rather than a single string w/ the 'non_field_errors' key as w/ the base UniqueTogetherValidator class
            field_names = self.fields
            pretty_field_names = " / ".join([pretty_string(f) for f in field_names])
            msg = self.message.format(pretty_field_names=pretty_field_names)
            raise ValidationError({
                f: msg
                for f in field_names
            })

    def set_context(self, serializer_field):
        super(QUniqueTogetherValidator, self).set_context(serializer_field)
        if isinstance(serializer_field.parent, QListSerializer):
            # self.instance is already set internally,
            # but I want to know what the model is as well,
            # so that I can decide whether to ignore non-existent data in "call()" above
            # (I ignore missing data if it is the fk field for a non-saved instance)
            self.model = serializer_field.get_model()
            self.exempt_fields = [
                field.name for field in self.model._meta.fields
                if isinstance(field, RelatedField) and field.related_query_name() == serializer_field.source
            ]
    #         # THIS IS NO LONGER NEEDED B/C "instance" IS SET IN "QSerializer.to_internal_value" BELOW
    #         # if this validator is being applied on a custom m2m field (QListSerializer),
    #         # then set its instance using the initial_data generator attribute set in "QListSerializer.bind" below
    #         initial_data = serializer_field.parent.initial_data.next()
    #         instance_class = serializer_field.get_model()
    #         try:
    #             self.instance = instance_class.objects.get(pk=initial_data.get("id", None))
    #         except ObjectDoesNotExist:
    #             pass

############################
# custom serializer fields #
############################

class QEnumerationSerializerField(SerializerField):
    """
    model QEnumerationField is based on a TextField
    but QEnumerationFormField correctly deals w/ lists
    however, I need to ensure that the output of the _serializer_ fields
    converts the text back into a list (the underlying model field will store it as text)
    """

    # TODO: I EXPECTED THIS TO SAVE ENUMERATIONS AS "one|two|three"
    # TODO: BUT IT SAVES THEM AS "[u'one', u'two', u'three']"
    # TODO: ALL THE SURROUNDING CODE SEEMS TO WORK, SO DOES IT REALLY MATTER?

    def to_representation(self, obj):
        if isinstance(obj, list):
            # return [o for o in obj if o != '']
            return "|".join(obj)
        elif isinstance(obj, basestring):
            return obj

    def to_internal_value(self, data):
        if isinstance(data, list):
            return data
        else:
            try:
                return data.split('|')
            except:
                return []

# TODO: DO I NEED A SPECIAL SERIALIZER FIELD FOR CARDINALITY?!?

######################
# custom serializers #
######################

class QListSerializer(ListSerializer):

    # THIS IS NO LONGER NEEDED B/C "instance" IS SET IN "QSerializer.to_internal_value" BELOW
    # def bind(self, field_name, parent):
    #     super(QListSerializer, self).bind(field_name, parent)
    #     if hasattr(parent, "initial_data"):
    #         initial_list_data = parent.initial_data.get(field_name)
    #         if initial_list_data:
    #             self.initial_data = (child_data for child_data in initial_list_data)  # this is a generator so I can access the initial data of each child in turn via "next()"
    #         else:
    #             self.initial_data = None

    def create(self, validated_data):
        return [self.child.create(attrs) for attrs in validated_data]
        # using "bulk_create" is probably faster,
        # but I really ought to defer to the "child.create" fn in-case it has any special behaviors
        # child_class = self.child.get_model()
        # return child_class.objects.bulk_create([child_class(**item) for item in validated_data])

    def update(self, instances, validated_data):
        updated_models = []

        # generate maps for id->instance and id->validated_data...
        instance_mapping = {
            instance.id: instance
            for instance in instances
        }
        data_mapping = {
            data['id']: data
            for data in validated_data
        }

        # perform creations or updates based on the above maps...
        for model_id, model_data in data_mapping.items():
            model = instance_mapping.get(model_id, None)
            if model is None:
                updated_models.append(self.child.create(model_data))
            else:
                updated_models.append(self.child.update(model, model_data))

        # perform deletes based on the above maps...
        for model_id, model in instance_mapping.items():
            if model_id not in data_mapping:
                model.delete()

        return updated_models

    def get_model(self):
        return self.child.get_model()


class QSerializer(ModelSerializer):

    def get_model(self):
        return self.Meta.model

    def remove_superfluous_data(self, data_dict):
        """
        gets rid of any fields in the serializer's data
        that do not correspond to fields in the underlying model
        """
        model = self.get_model()
        for field_name in data_dict.keys():
            if not model.get_field(field_name):
                data_dict.pop(field_name)
        return data_dict

    def is_valid(self, *args, **kwargs):
        # I MAY WANT TO OVERRIDE THIS FOR CUSTOM VALIDATION
        # import ipdb; ipdb.set_trace()
        return super(QSerializer, self).is_valid(*args, **kwargs)

    def validate(self, attrs):
        # I MAY WANT TO OVERRIDE THIS FOR CUSTOM VALIDATION
        # import ipdb; ipdb.set_trace()
        return super(QSerializer, self).validate(attrs)

    def run_validation(self, data=empty):
        # I MAY WANT TO OVERRIDE THIS FOR CUSTOM VALIDATION
        # import ipdb; ipdb.set_trace()
        return super(QSerializer, self).run_validation(data)
    #     """
    #     This is just like the parent class 'run_validation' fn,
    #     except it goes ahead and completes validation on all fields even if there is an exception
    #     This allows all errors to be rendered nicely in the templates
    #     """
    #     (is_empty_value, data) = self.validate_empty_values(data)
    #     if is_empty_value:
    #         return data
    #
    #     value = self.to_internal_value(data)
    #     try:
    #         # HERE IS WHAT I WOULD CHANGE...
    #         # DON'T BREAK ON THE 1ST EXCEPTION!
    #         # RUN ALL VALIDATORS AND CHECK ALL VALUES!
    #         self.run_validators(value)
    #         value = self.validate(value)
    #         assert value is not None, '.validate() should return the validated data'
    #     except (ValidationError, DjangoValidationError) as e:
    #         raise ValidationError(detail=get_validation_error_detail(e))
    #
    #     return value

    def to_internal_value(self, data):

        # this is as good a place as any to set the instance
        try:
            model_class = self.get_model()
            self.instance = model_class.objects.get(pk=data.get("id"))
        except ObjectDoesNotExist:
            pass

        return super(QSerializer, self).to_internal_value(data)
        #
        # if not isinstance(data, dict):
        #     message = self.error_messages['invalid'].format(
        #         datatype=type(data).__name__
        #     )
        #     raise ValidationError({
        #         api_settings.NON_FIELD_ERRORS_KEY: [message]
        #     })
        #
        # ret = OrderedDict()
        # errors = OrderedDict()
        # fields = [
        #     field for field in self.fields.values()
        #     if (not field.read_only) or (field.default is not empty)
        # ]
        #
        # for field in fields:
        #     validate_method = getattr(self, 'validate_' + field.field_name, None)
        #     primitive_value = field.get_value(data)
        #     try:
        #         validated_value = field.run_validation(primitive_value)
        #         if validate_method is not None:
        #             validated_value = validate_method(validated_value)
        #     except ValidationError as exc:
        #         errors[field.field_name] = exc.detail
        #     except DjangoValidationError as exc:
        #         errors[field.field_name] = list(exc.messages)
        #     except SkipField:
        #         pass
        #     else:
        #         set_value(ret, field.source_attrs, validated_value)
        #
        # if errors:
        #     raise ValidationError(errors)
        #
        # return ret

    # @classmethod
    # def many_init(cls, *args, **kwargs):
    #     """
    #     This method implements the creation of a `ListSerializer` parent
    #     class when `many=True` is used. You can customize it if you need to
    #     control which keyword arguments are passed to the parent, and
    #     which are passed to the child.
    #
    #     Note that we're over-cautious in passing most arguments to both parent
    #     and child classes in order to try to cover the general case. If you're
    #     overriding this method you'll probably want something much simpler, eg:
    #
    #     @classmethod
    #     def many_init(cls, *args, **kwargs):
    #         kwargs['child'] = cls()
    #         return CustomListSerializer(*args, **kwargs)
    #     """
    #     child_serializer = cls(*args, **kwargs)
    #     list_kwargs = {'child': child_serializer}
    #     list_kwargs.update(dict([
    #         (key, value) for key, value in kwargs.items()
    #         if key in LIST_SERIALIZER_KWARGS
    #     ]))
    #     meta = getattr(cls, 'Meta', None)
    #     list_serializer_class = getattr(meta, 'list_serializer_class', ListSerializer)
    #     return list_serializer_class(*args, **list_kwargs)
    #

    def get_unique_together_validators(self):
        """
        makes sure the validators are instances of QUniqueTogetherValidator
        instead of the default UniqueTogetherValidator
        :return:
        """
        validators = []
        for validator in super(QSerializer, self).get_unique_together_validators():
            new_validator = QUniqueTogetherValidator(
                queryset=validator.queryset,
                fields=validator.fields,
                message=validator.message,
            )
            validators.append(new_validator)
        return validators
