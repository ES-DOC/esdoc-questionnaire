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

"""
.. module:: serializers_realizations_models

DRF Serializers for realization classes

"""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as RestValidationError
from rest_framework import serializers

from Q.questionnaire.serializers.serializers_base import QVersionSerializerField
from Q.questionnaire.serializers.serializers_realizations import QRealizationSerializer, QRealizationListSerializer
from Q.questionnaire.serializers.serializers_realizations_properties import QPropertyRealizationSerializer
from Q.questionnaire.models.models_realizations import QModel


class QModelRealizationSerializer(QRealizationSerializer):

    class Meta:
        model = QModel
        fields = (
            'id',
            'name',
            'description',
            'version',
            'owner',
            'shared_owners',
            'properties',
            'project',
            'ontology',
            'proxy',
            'is_document',
            'is_root',
            'is_published',
            'is_active',
            'is_complete',
            # these next fields are not part of the model
            # but they are used to facilitate ng interactivity on the client
            'key',
            'display_detail',
            'display_properties',
        )

    key = serializers.SerializerMethodField(read_only=True)  # name="get_key"
    # is_complete = serializers.SerializerMethodField(read_only=True)  # name="get_is_complete"
    display_detail = serializers.SerializerMethodField(read_only=True)  # name="get_display_detail"
    display_properties = serializers.SerializerMethodField(read_only=True)  # name="get_display_properties"

    version = QVersionSerializerField(allow_null=True)

    shared_owners = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    properties = QPropertyRealizationSerializer(many=True, required=False)

    def get_key(self, obj):
        # using a SerailizerMethodField instead of guid directly b/c guid is a non-editable field
        return obj.get_key()

    # def get_is_complete(self, obj):
    #     return obj.is_complete()

    def get_display_detail(self, obj):
        """
        not a _real_ field
        just helps me w/ interactivity
        I always load the customizer w/ display_detail = False
        :param obj:
        :return:
        """
        return False

    def get_display_properties(self, obj):
        """
        not a _real_ field
        just helps me w/ interactivity
        I always load the customizer w/ display_properties = False
        :param obj:
        :return:
        """
        return False

    def create(self, validated_data):
        """
        ensures that nested fields are updated/created along w/ parent model
        :param validated_data
        :return the created model
        """
        # notice how all the calls to create are wrapped in a try/catch block;
        # I translate every django error into a django-rest-framework error
        # but, I still try to validate the rest of the data
        # (this ensures _all_ errors will be caught)
        # TODO: DOUBLE-CHECK THAT THIS WORKS IF THE ERROR MESSAGE IS NOT A LIST
        # TODO: (B/C I THINK THAT DRF REQUIRES LISTS BUT DJANGO DOESN'T CARE)
        validation_errors = RestValidationError({})

        properties_serializer = self.fields["properties"]
        properties_data = validated_data.pop(properties_serializer.source, [])

        try:
            model_realization = QModel.objects.create(**validated_data)
        except DjangoValidationError as e:
            model_realization = None
            validation_errors.detail.update(e.message_dict)

        try:
            for property_data in properties_data:
                property_data["model"] = model_realization
            properties_serializer.create(properties_data)
        except DjangoValidationError as e:
            print(e.message)
            validation_errors.detail.update(e.message_dict)

        if len(validation_errors.detail):
            raise validation_errors

        return model_realization

    def update(self, instance, validated_data):
        """
        ensures that nested fields are updated/created along w/ parent model
        :param validated_data
        :return the created model
        """
        # notice how all the calls to create or update are wrapped in a try/catch block;
        # I translate every django error into a django-rest-framework error
        # but, I still try to validate the rest of the data
        # (this ensures _all_ errors will be caught)
        # TODO: DOUBLE-CHECK THAT THIS WORKS IF THE ERROR MESSAGE IS NOT A LIST
        # TODO: (B/C I THINK THAT DRF REQUIRES LISTS BUT DJANGO DOESN'T CARE)
        validation_errors = RestValidationError({})

        properties_serializer = self.fields["properties"]
        properties_data = validated_data.pop(properties_serializer.source, [])

        try:
            model_realization = super(QModelRealizationSerializer, self).update(instance, validated_data)
        except DjangoValidationError as e:
            model_realization = None
            validation_errors.detail.update(e.message_dict)

        try:
            for property_data in properties_data:
                property_data["model"] = model_realization
            # TODO: CHECK THE ORDER OF THINGS AGAIN (THEY MAY HAVE A CUSTOM ORDER)
            properties_serializer.update(model_realization.properties.all(), properties_data)
        except DjangoValidationError as e:
            print(e.message)
            validation_errors.detail.update(e.message_dict)

        if len(validation_errors.detail):
            raise validation_errors

        return model_realization