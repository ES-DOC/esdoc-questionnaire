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
.. module:: serializers_customizations_models

DRF Serializers for customization classes

"""


from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as RestValidationError
from rest_framework import serializers

from Q.questionnaire.serializers.serializers_customizations import QCustomizationSerializer, QCustomizationListSerializer
from Q.questionnaire.serializers.serializers_customizations_categories import QCategoryCustomizationSerializer
from Q.questionnaire.serializers.serializers_customizations_properties import QPropertyCustomizationSerializer
from Q.questionnaire.models.models_customizations import QModelCustomization

class QModelCustomizationSerializer(QCustomizationSerializer):

    class Meta:
        model = QModelCustomization
        fields = (
            'id',
            'name',
            'owner',
            'shared_owners',
            'description',
            'is_default',
            'ontology',
            'proxy',
            'project',
            'model_title',
            'model_description',
            'model_show_all_categories',
            'categories',
            'properties',
            # these next fields are not part of the model
            # but they are used to facilitate ng interactivity on the client
            'key',
            'proxy_name',
            'display_detail',  # obviously, this is only relevant for subforms
        )

        # there is no need to explicitly add QUniqueTogetherValidator
        # b/c that is done automatically in "QSerializer.get_unique_together_validators()"
        # validators = [
        #     QUniqueTogetherValidator(
        #         queryset=QModelCustomization.objects.all(),
        #         # fields=('name', 'proxy', 'project'),
        #     )
        # ]

    key = serializers.SerializerMethodField(read_only=True)  # name="get_key"
    proxy_name = serializers.SerializerMethodField(read_only=True)  # name="get_proxy_name"
    display_detail = serializers.SerializerMethodField(read_only=True)  # name="get_display_detail"

    shared_owners = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    categories = QCategoryCustomizationSerializer(many=True, required=False, source="category_customizations")
    properties = QPropertyCustomizationSerializer(many=True, required=False, source="property_customizations")

    def get_key(self, obj):
        # using a SerailizerMethodField instead of guid directly b/c guid is a non-editable field
        return obj.get_key()

    def get_proxy_name(self, obj):
        """
        not a _real_ field
        just helps me w/ interactivity
        :param obj:
        :return:
        """
        return str(obj.proxy)

    def get_display_detail(self, obj):
        """
        not a _real_ field
        just helps me w/ interactivity
        I always load the customizer w/ display_detail = False
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

        categories_serializer = self.fields['categories']
        properties_serializer = self.fields["properties"]

        categories_data = validated_data.pop(categories_serializer.source, [])
        properties_data = validated_data.pop(properties_serializer.source, [])

        try:
            model_customization = QModelCustomization.objects.create(**validated_data)
        except DjangoValidationError as e:
            model_customization = None
            print(e.message)
            validation_errors.detail.update(e.message_dict)

        try:
            for category_data in categories_data:
                category_data["model_customization"] = model_customization
            categories_serializer.create(categories_data)
        except DjangoValidationError as e:
            print(e.message)
            validation_errors.detail.update(e.message_dict)

        try:
            for property_data in properties_data:
                property_data["model_customization"] = model_customization
            properties_serializer.create(properties_data)
        except DjangoValidationError as e:
            print(e.message)
            validation_errors.detail.update(e.message_dict)

        if len(validation_errors.detail):
            raise validation_errors

        return model_customization

    def update(self, instance, validated_data):
        """
        ensures that nested fields are updated/created along w/ parent model
        :param instance:
        :param validated_data:
        :return:
        """
        # notice how all the calls to create or update are wrapped in a try/catch block;
        # I translate every django error into a django-rest-framework error
        # but, I still try to validate the rest of the data
        # (this ensures _all_ errors will be caught)
        # TODO: DOUBLE-CHECK THAT THIS WORKS IF THE ERROR MESSAGE IS NOT A LIST
        # TODO: (B/C I THINK THAT DRF REQUIRES LISTS BUT DJANGO DOESN'T CARE)
        validation_errors = RestValidationError({})

        categories_serializer = self.fields["categories"]
        properties_serializer = self.fields["properties"]

        categories_data = validated_data.pop(categories_serializer.source, instance.category_customizations.values())
        properties_data = validated_data.pop(properties_serializer.source, instance.property_customizations.values())

        try:
            model_customization = super(QModelCustomizationSerializer, self).update(instance, validated_data)
        except DjangoValidationError as e:
            validation_errors.detail.update(e.message_dict)

        try:
            categories_serializer.update(model_customization.category_customizations.all(), categories_data)
        except DjangoValidationError as e:
            validation_errors.detail.update(e.message_dict)

        try:
            properties_serializer.update(model_customization.property_customizations.all(), properties_data)
        except DjangoValidationError as e:
            validation_errors.detail.update(e.message_dict)

        if len(validation_errors.detail):
            raise validation_errors

        return model_customization

