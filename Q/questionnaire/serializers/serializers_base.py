####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.db.models.fields.related import RelatedField
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, ListSerializer, Field as SerializerField
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.exceptions import ValidationError

from Q.questionnaire.q_utils import QError, Version, pretty_string, legacy_code

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


class QVersionSerializerField(SerializerField):
    """
    QVersionField is based on an IntegerField
    but the client deals w/ strings
    so make sure I convert them appropriately
    """

    def to_representation(self, obj):
        # given a Pythonic representation of a version, return a serialized representation
        assert isinstance(obj, Version)
        return obj.fully_specified()
        # if isinstance(obj, Version):
        #     return obj.fully_specified()
        # if isinstance(obj, basestring):
        #     return Version(obj).fully_specified()

    def to_internal_value(self, data):
        # given a serialized representation of a version, return a Pythonic representation
        # (this should basically do the same thing as "QVersionField.to_python")
        if isinstance(data, Version):
            return data
        if isinstance(data, basestring):
            return Version(data)
        if data is None:
            return None
        return Version(Version.int_to_string(data))


class QRelatedSerializerField(serializers.RelatedField):

    def __init__(self, **kwargs):
        manager = kwargs.pop("manager")
        super(QRelatedSerializerField, self).__init__(**kwargs)
        self.manager = manager

    @classmethod
    def many_init(cls, *args, **kwargs):
        """
        This method handles creating a parent `ManyRelatedField` instance
        when the `many=True` keyword argument is passed.

        Typically you won't need to override this method.

        Note that we're over-cautious in passing most arguments to both parent
        and child classes in order to try to cover the general case. If you're
        overriding this method you'll probably want something much simpler, eg:

        @classmethod
        def many_init(cls, *args, **kwargs):
            kwargs['child'] = cls()
            return CustomManyRelatedField(*args, **kwargs)
        """
        # list_kwargs = {'child_relation': cls(*args, **kwargs)}
        # for key in kwargs.keys():
        #     if key in MANY_RELATION_KWARGS:
        #         list_kwargs[key] = kwargs[key]
        # return ManyRelatedField(**list_kwargs)
        list_kwargs = {'child': cls(*args, **kwargs)}
        list_serializer_class = getattr(cls.Meta, 'list_serializer_class', ListSerializer)
        return list_serializer_class(*args, **list_kwargs)

    # these abstract methods are implemented in the fields that inherit from QRelatedSerializerField, like QCustomizationRelatedField
    # def to_representation(self, value):
    #     pass
    #
    # def to_internal_value(self, data):
    #     pass

######################
# custom serializers #
######################


class QListSerializer(ListSerializer):

    def create(self, validated_data):
        return [self.child.create(attrs) for attrs in validated_data]
        # using "bulk_create" below is probably faster,
        # but I really ought to defer to the "child.create" fn above in-case it has any special behaviors
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
            # just in-case I am dealing w/ unsaved data,
            # use the built-in 'id' fn to come up w/ a key that won't conflict w/ 'instance_mapping' or anything else in 'data_mapping'
            data.get('id', id(data)): data
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

    @legacy_code
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

    # def is_valid(self, *args, **kwargs):
    #     # I MAY WANT TO OVERRIDE THIS FOR CUSTOM VALIDATION
    #     # import ipdb; ipdb.set_trace()
    #     return super(QSerializer, self).is_valid(*args, **kwargs)
    #
    # def validate(self, attrs):
    #     # I MAY WANT TO OVERRIDE THIS FOR CUSTOM VALIDATION
    #     # import ipdb; ipdb.set_trace()
    #     return super(QSerializer, self).validate(attrs)
    #
    # def run_validation(self, data=empty):
    #     # I MAY WANT TO OVERRIDE THIS FOR CUSTOM VALIDATION
    #     # import ipdb; ipdb.set_trace()
    #     return super(QSerializer, self).run_validation(data)

    def to_internal_value(self, data):

        # this is as good a place as any to set the instance...
        try:
            model_class = self.get_model()
            self.instance = model_class.objects.get(pk=data.get("id"))
        except ObjectDoesNotExist:
            pass

        return super(QSerializer, self).to_internal_value(data)

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
