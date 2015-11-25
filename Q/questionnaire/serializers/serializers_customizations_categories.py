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
.. module:: serializers_customizations_categories

DRF Serializers for customization classes

"""


from rest_framework import serializers
from uuid import UUID as generate_uuid

from Q.questionnaire.serializers.serializers_customizations import QCustomizationSerializer, QCustomizationListSerializer
from Q.questionnaire.models.models_customizations import QStandardCategoryCustomization, QScientificCategoryCustomization


class QStandardCategoryCustomizationSerializer(QCustomizationSerializer):
    class Meta:
        model = QStandardCategoryCustomization
        list_serializer_class = QCustomizationListSerializer
        fields = (
            'id',
            'name',
            'description',
            'order',
            'model_customization',
            'proxy',
            # these next 3 fields are not part of the model
            # but they are used to facilitate ng interactivity on the client
            'key',
            'display_properties',
            'display_detail',
        )

    display_properties = serializers.SerializerMethodField(read_only=True)  # name="get_display_properties"
    display_detail = serializers.SerializerMethodField(read_only=True)  # name="get_display_detail"

    key = serializers.SerializerMethodField(read_only=False)  # name="get_key"

    # even though 'model_customization' is a required field of the QStandardCategoryCustomization model,
    # it cannot possibly be set before the parent model_customization itself has been saved;
    # so I set 'allow_null' to True here...
    model_customization = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    def get_display_properties(self, obj):
        """
        not a _real_ field
        just helps me w/ interactivity
        I always load the customizer w/ display_properties = True
        :param obj:
        :return:
        """
        return True

    def get_display_detail(self, obj):
        """
        not a _real_ field
        just helps me w/ interactivity
        I always load the customizer w/ display_detail = False
        :param obj:
        :return:
        """
        return False

    def get_key(self, obj):
        # using a SerailizerMethodField instead of guid directly b/c guid is a non-editable field
        return obj.get_key()

    def to_internal_value(self, data):
        internal_value = super(QStandardCategoryCustomizationSerializer, self).to_internal_value(data)
        # add the original key to use as guid so that a new key is not automatically generated
        internal_value.update({
            "guid": generate_uuid(data.get("key"))
        })
        pk = data.get("id")
        if pk:
            internal_value.update({
                "id": pk,  # put id back so that update/create will work for QListSerializer
            })
        return internal_value

    def create(self, validated_data):
        # validated_data = self.remove_superfluous_data(validated_data)
        return super(QStandardCategoryCustomizationSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        # validated_data = self.remove_superfluous_data(validated_data)
        return super(QStandardCategoryCustomizationSerializer, self).update(instance, validated_data)


class QScientificCategoryCustomizationSerializer(QCustomizationSerializer):
    class Meta:
        model = QScientificCategoryCustomization
        list_serializer_class = QCustomizationListSerializer
        fields = (
            'id',
            'name',
            'description',
            'order',
            'model_customization',
            'proxy',
            'vocabulary_key',
            'component_key',
            # these next 3 fields are not part of the model
            # but they are used to facilitate ng interactivity on the client
            'key',
            'display_properties',
            'display_detail',
        )

    vocabulary_key = serializers.SerializerMethodField(read_only=False)  # name="get_vocabulary_key"
    component_key = serializers.SerializerMethodField(read_only=False)  # name="get_component_key"

    key = serializers.SerializerMethodField(read_only=False)  # name="get_key"

    display_properties = serializers.SerializerMethodField(read_only=True)  # name="get_display_properties"
    display_detail = serializers.SerializerMethodField(read_only=True)  # name="get_display_detail"

    # even though 'model_customization' is a required field of the QStandardCategoryCustomization model,
    # it cannot possibly be set before the parent model_customization itself has been saved;
    # so I set 'allow_null' to True here...
    model_customization = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    def get_display_properties(self, obj):
        """
        not a _real_ field
        just helps me w/ interactivity
        I always load the customizer w/ display_properties = True
        :param obj:
        :return:
        """
        return True

    def get_display_detail(self, obj):
        """
        not a _real_ field
        just helps me w/ interactivity
        I always load the customizer w/ display_detail = False
        :param obj:
        :return:
        """
        return False

    def get_key(self, obj):
        # using a SerializerMethodField instead of guid directly b/c guid is a non-editable field
        return obj.get_key()

    def get_vocabulary_key(self, obj):
        return obj.get_vocabulary_key()

    def get_component_key(self, obj):
        return obj.get_component_key()

    def to_internal_value(self, data):
        internal_value = super(QScientificCategoryCustomizationSerializer, self).to_internal_value(data)
        # add the original key to use as guid so that a new key is not automatically generated
        # and put back the vocabulary/component keys (have to convert them back from strings)
        internal_value.update({
            "guid": generate_uuid(data.get("key")),
            "vocabulary_key": generate_uuid(data.get("vocabulary_key")),
            "component_key": generate_uuid(data.get("component_key")),
        })
        pk = data.get("id")
        if pk:
            internal_value.update({
                "id": pk,  # put id back so that update/create will work for QListSerializer
            })
        return internal_value

    def create(self, validated_data):
        # validated_data = self.remove_superfluous_data(validated_data)
        return super(QScientificCategoryCustomizationSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        # validated_data = self.remove_superfluous_data(validated_data)
        return super(QScientificCategoryCustomizationSerializer, self).update(instance, validated_data)
