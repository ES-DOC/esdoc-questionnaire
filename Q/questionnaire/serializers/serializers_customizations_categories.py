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
.. module:: serializers_customizations_categories

DRF Serializers for customization classes

"""


from rest_framework import serializers
from uuid import UUID as generate_uuid

from Q.questionnaire.serializers.serializers_customizations import QCustomizationSerializer, QCustomizationListSerializer
from Q.questionnaire.models.models_customizations import QCategoryCustomization

class QCategoryCustomizationSerializer(QCustomizationSerializer):
    class Meta:
        model = QCategoryCustomization
        list_serializer_class = QCustomizationListSerializer
        fields = (
            'id',
            'name',
            'category_title',
            'documentation',
            'order',
            'model_customization',
            'proxy',
            # these next fields are not part of the model
            # but they are used to facilitate ng interactivity on the client
            'key',
            'num_properties',
            'proxy_name',
            'display_properties',
            'display_detail',
        )

    display_properties = serializers.SerializerMethodField(read_only=True)  # name="get_display_properties"
    display_detail = serializers.SerializerMethodField(read_only=True)  # name="get_display_detail"
    num_properties = serializers.SerializerMethodField(read_only=True)  # name="get_num_properties"
    proxy_name = serializers.SerializerMethodField(read_only=True)  # name="get_proxy_name"
    key = serializers.SerializerMethodField(read_only=False)  # name="get_key"

    # even though 'model_customization' is a required field of the QStandardCategoryCustomization model,
    # it cannot possibly be set before the parent model_customization itself has been saved;
    # so I set 'allow_null' to True here...
    model_customization = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    def get_num_properties(self, obj):
        return obj.property_customizations(manager="allow_unsaved_categories_manager").count()

    def get_proxy_name(self, obj):
        """
        not a _real_ field
        just helps me w/ interactivity
        :param obj:
        :return:
        """
        return str(obj.proxy)

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
        internal_value = super(QCategoryCustomizationSerializer, self).to_internal_value(data)
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
        return super(QCategoryCustomizationSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        # validated_data = self.remove_superfluous_data(validated_data)
        return super(QCategoryCustomizationSerializer, self).update(instance, validated_data)

