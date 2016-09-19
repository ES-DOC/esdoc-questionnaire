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
.. module:: serializers_customizations_properties

DRF Serializers for customization classes

"""

from rest_framework import serializers
from uuid import UUID as generate_uuid

from Q.questionnaire.serializers.serializers_customizations import QCustomizationSerializer, QCustomizationListSerializer, QCustomizationManagedRelatedField
from Q.questionnaire.models.models_customizations import QModelCustomization, QCategoryCustomization, QPropertyCustomization

class QSubFormCustomizationField(QCustomizationManagedRelatedField):
    """
    This is a custom field; it presents a relational field (actually, the reverse of a fk) to QModelCustomizations
    but it can cope w/ unsaved models!
    """

    # TODO: WHY DO I STILL HAVE TO PASS "queryset" TO THE FIELD CONSTRUCTOR BELOW IF IT'S IN THE CLASS DEFINITION HERE ?
    queryset = QModelCustomization.objects.all()

    def to_representation(self, value):
        if not value:
            return {}

        # need to import w/in this fn to prevent circular dependencies
        from .serializers_customizations_models import QModelCustomizationSerializer
        model_serializer = QModelCustomizationSerializer()
        representation = model_serializer.to_representation(value)
        return representation

    def to_internal_value(self, data):
        if not data:
            return None

        # need to import w/in this fn to prevent circular dependencies
        from .serializers_customizations_models import QModelCustomizationSerializer
        model_serializer = QModelCustomizationSerializer()
        internal_value = model_serializer.to_internal_value(data)

        internal_value.update({
            "guid": generate_uuid(data.get("key")),
        })

        pk = data.get("id")
        if pk:
            internal_value.update({
                "id": pk,  # put id back so that update/create will work for QListSerializer
            })

        return internal_value

    def create(self, validated_data):
        if not validated_data:
            return None

        # need to import w/in this fn to prevent circular dependencies
        from .serializers_customizations_models import QModelCustomizationSerializer
        model_serializer = QModelCustomizationSerializer()
        return model_serializer.create(validated_data)

    def update(self, model_instance, validated_data):
        if not validated_data:
            return model_instance

        # need to import w/in this fn to prevent circular dependencies
        from .serializers_customizations_models import QModelCustomizationSerializer
        model_serializer = QModelCustomizationSerializer()
        return model_serializer.update(model_instance, validated_data)


class QPropertyCustomizationSerializer(QCustomizationSerializer):

    class Meta:
        model = QPropertyCustomization
        list_serializer_class = QCustomizationListSerializer
        fields = (
            'id',
            'name',
            'property_title',
            'order',
            'field_type',
            'is_hidden',
            'is_required',
            'is_nillable',
            'is_editable',
            'documentation',
            'inline_help',
            'model_customization',
            'proxy',
            'category',
            'atomic_default',
            'atomic_type',
            'atomic_suggestions',
            # 'enumeration_choices',
            # 'enumeration_default',
            'enumeration_open',
            'relationship_target_model_customizations',
            'relationship_show_subform',
            # these next fields are not part of the model
            # but they are used to facilitate ng interactivity on the client
            'key',
            'proxy_name',
            'category_key',
            'display_detail',
            'use_subforms',
        )

    key = serializers.SerializerMethodField(read_only=True)  # name="get_key"
    proxy_name = serializers.SerializerMethodField(read_only=True)  # name="get_proxy_name"
    category_key = serializers.SerializerMethodField(read_only=True)  # name="get_category_key"
    display_detail = serializers.SerializerMethodField(read_only=True)  # name="get_display_detail"
    use_subforms = serializers.SerializerMethodField(read_only=True)  # name="get_use_subforms"

    # enumeration_choices = QEnumerationSerializerField(allow_null=True)
    # enumeration_default = QEnumerationSerializerField(allow_null=True)

    # even though 'model_customization' is a required field of the QPropertyCustomization model,
    # it cannot possibly be set before the parent model_customization itself has been saved;
    # so I set 'allow_null' to True here...
    model_customization = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    relationship_target_model_customizations = \
        QSubFormCustomizationField(
            many=True,
            required=False,
            allow_null=True,
            # allow_unsaved=True,
            manager=QModelCustomization.allow_unsaved_relationship_target_model_customizations_manager,
            queryset=QModelCustomization.objects.all(),
        )

    def get_key(self, obj):
        # using a SerailizerMethodField instead of guid directly b/c guid is a non-editable field
        return obj.get_key()

    def get_category_key(self, obj):
        return obj.category.get_key()

    def get_display_detail(self, obj):
        """
        not a _real_ field
        just helps me w/ interactivity
        I always load the customizer w/ display_detail = False
        :param obj:
        :return:
        """
        return False

    def get_proxy_name(self, obj):
        """
        not a _real_ field
        just helps me w/ interactivity
        :param obj:
        :return:
        """
        return str(obj.proxy)

    def get_use_subforms(self, obj):
        """

        :param obj:
        :return:
        """
        return obj.use_subforms()

    def to_internal_value(self, data):
        internal_value = super(QPropertyCustomizationSerializer, self).to_internal_value(data)

        internal_value.update({
            "guid": generate_uuid(data.get("key")),
            "category_key": generate_uuid(data.get("category_key")),  # put the category key back so that I can use it to locate the correct category in 'create' and/or 'update' below
        })

        pk = data.get("id")
        if pk:
            internal_value.update({
                "id": pk,  # put id back so that update/create will work for QListSerializer
            })

        return internal_value

    def create(self, validated_data):

        subform_serializer = self.fields["relationship_target_model_customizations"]
        subform_data = validated_data.pop(subform_serializer.source, [])

        category_key = validated_data.pop("category_key", None)
        category = QCategoryCustomization.objects.get_by_key(category_key)
        validated_data["category"] = category

        property_customization = super(QPropertyCustomizationSerializer, self).create(validated_data)

        if subform_data:
            # recall that "relationship_target_model_customizations" is a reverse relationship
            # the _real_ field is the "relationship_source_property_customization" fk on the target_model
            # so set it accordingly
            relationship_target_model_customizations = subform_serializer.create(subform_data)
            for relationship_target_model_customization in relationship_target_model_customizations:
                relationship_target_model_customization.relationship_source_property_customization = property_customization
                # TODO: DO I REALLY HAVE TO RE-SAVE THE TARGET?
                relationship_target_model_customization.save()

        return property_customization

    def update(self, instance, validated_data):

        subform_serializer = self.fields["relationship_target_model_customizations"]
        subform_data = validated_data.pop(subform_serializer.source, [])

        # since I cannot change a property's category (as of v0.15), there is no need to re-set it here as above
        # category_key = validated_data.pop("category_key", None)
        # category = QCategoryCustomization.objects.get_by_key(category_key)
        # validated_data["category"] = category

        property_customization = super(QPropertyCustomizationSerializer, self).update(instance, validated_data)

        if subform_data:
            # the fk will already be set, so there is no need to deal w/ it or re-save the targets here as above
            subform_serializer.update(instance.relationship_target_model_customizations.all(), subform_data)

        return property_customization
