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

from Q.questionnaire.serializers.serializers_base import QEnumerationSerializerField
from Q.questionnaire.serializers.serializers_customizations import QCustomizationSerializer, QCustomizationListSerializer
from Q.questionnaire.models.models_customizations import QStandardCategoryCustomization, QScientificCategoryCustomization, QStandardPropertyCustomization, QScientificPropertyCustomization
from Q.questionnaire.models.models_customizations import QModelCustomization
from Q.questionnaire.q_fields import allow_unsaved_fk


class QSubFormCustomizationField(serializers.RelatedField):

    # TODO: WHY DO I STILL HAVE TO PASS "queryset" TO THE FIELD CONSTRUCTOR BELOW?
    queryset = QModelCustomization.objects.all()

    # I AM HERE; model_customization.pk == 14 is the one to check!

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


class QStandardPropertyCustomizationSerializer(QCustomizationSerializer):

    class Meta:
        model = QStandardPropertyCustomization
        list_serializer_class = QCustomizationListSerializer
        fields = (
            'id',
            'name',
            'order',
            'cardinality',
            'field_type',
            'displayed',
            'required',
            'editable',
            'unique',
            'verbose_name',
            'documentation',
            'inline_help',
            'model_customization',
            'proxy',
            'category',
            'inherited',
            'atomic_default',
            'atomic_type',
            'atomic_suggestions',
            'enumeration_choices',
            'enumeration_default',
            'enumeration_open',
            'enumeration_multi',
            'enumeration_nullable',
            'relationship_show_subform',
            'relationship_subform_customization',
            # these next 3 fields are not part of the model
            # but they are used to facilitate ng interactivity on the client
            'key',
            'category_key',
            'display_detail',
        )

    key = serializers.SerializerMethodField(read_only=True)  # name="get_key"
    display_detail = serializers.SerializerMethodField(read_only=True)  # name="get_display_detail"
    category_key = serializers.SerializerMethodField(read_only=True)  # name="get_category_key"

    enumeration_choices = QEnumerationSerializerField(allow_null=True)
    enumeration_default = QEnumerationSerializerField(allow_null=True)

    # even though 'model_customization' is a required field of the QStandardCategoryCustomization model,
    # it cannot possibly be set before the parent model_customization itself has been saved;
    # so I set 'allow_null' to True here...
    model_customization = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    relationship_subform_customization = QSubFormCustomizationField(required=False, allow_null=True, queryset=QModelCustomization.objects.all())

    def get_key(self, obj):
        # using a SerailizerMethodField instead of guid directly b/c guid is a non-editable field
        return obj.get_key()

    def get_category_key(self, obj):
        if obj.category:
            return obj.category.get_key()
        return None

    def get_display_detail(self, obj):
        """
        not a _real_ field
        just helps me w/ interactivity
        I always load the customizer w/ display_detail = False
        :param obj:
        :return:
        """
        return False

    def get_use_subform(self, obj):
        """

        :param obj:
        :return:
        """
        return obj.use_subform()

    def to_internal_value(self, data):
        internal_value = super(QStandardPropertyCustomizationSerializer, self).to_internal_value(data)

        internal_value.update({
            "guid": generate_uuid(data.get("key")),
        })

        # put the category_key back so that I can use it to locate the correct category in "create" and/or "update" below
        try:
            internal_value.update({
                "category_key": generate_uuid(data.get("category_key")),
            })
        except TypeError:
            # note that this may not work for standard_properties of subforms (b/c they have not necessarily been categorized)
            # that's okay... hence this try/except block
            pass

        pk = data.get("id")
        if pk:
            internal_value.update({
                "id": pk,  # put id back so that update/create will work for QListSerializer
            })

        return internal_value

    def create(self, validated_data):

        category_key = validated_data.pop("category_key", None)
        if category_key:
            # it's okay if there is no category key
            # if this is a standard_property in a subform then it may not have been categorized
            category = QStandardCategoryCustomization.objects.get_by_key(category_key)
            validated_data["category"] = category

        subform_serializer = self.fields["relationship_subform_customization"]
        subform_data = validated_data.pop(subform_serializer.source, {})
        if subform_data:
            subform = subform_serializer.create(subform_data)
            validated_data["relationship_subform_customization"] = subform

        return super(QStandardPropertyCustomizationSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        category_key = validated_data.pop("category_key", None)
        # since I cannot change a property's category (as of v0.15), there is no need to re-set it here
        # category = QStandardCategoryCustomization.objects.get_by_key(category_key)
        # validated_data["category"] = category
        subform_serializer = self.fields["relationship_subform_customization"]
        subform_data = validated_data.pop(subform_serializer.source, {})
        if subform_data:
            subform_serializer.update(instance.relationship_subform_customization, subform_data)

        return super(QStandardPropertyCustomizationSerializer, self).update(instance, validated_data)


class QScientificPropertyCustomizationSerializer(QCustomizationSerializer):

    class Meta:
        model = QScientificPropertyCustomization
        list_serializer_class = QCustomizationListSerializer
        fields = (
            'id',
            'name',
            'order',
            'cardinality',
            'field_type',
            'displayed',
            'required',
            'editable',
            'unique',
            'verbose_name',
            'documentation',
            'inline_help',
            'model_customization',
            'proxy',
            'category',
            'choice',
            'display_extra_standard_name',
            'display_extra_description',
            'display_extra_units',
            'edit_extra_standard_name',
            'edit_extra_description',
            'edit_extra_units',
            'atomic_default',
            'atomic_type',
            'atomic_suggestions',
            'enumeration_choices',
            'enumeration_default',
            'enumeration_open',
            'enumeration_multi',
            'enumeration_nullable',
            'vocabulary_key',
            'component_key',
            # these next 3 fields are not part of the model
            # but they are used to facilitate ng interactivity on the client
            'key',
            'category_key',
            'display_detail',
        )
    key = serializers.SerializerMethodField(read_only=True)  # name="get_key"
    vocabulary_key = serializers.SerializerMethodField(read_only=True)  # name="get_vocabulary_key"
    component_key = serializers.SerializerMethodField(read_only=True)  # name="get_component_key"

    category_key = serializers.SerializerMethodField(read_only=True)  # name="get_category_key"
    display_detail = serializers.SerializerMethodField(read_only=True)  # name="get_display_detail"

    enumeration_choices = QEnumerationSerializerField(allow_null=True)
    enumeration_default = QEnumerationSerializerField(allow_null=True)

    # even though 'model_customization' is a required field of the QStandardCategoryCustomization model,
    # it cannot possibly be set before the parent model_customization itself has been saved;
    # so I set 'allow_null' to True here...
    model_customization = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    def get_key(self, obj):
        # using a SerailizerMethodField instead of guid directly b/c guid is a non-editable field
        return obj.get_key()

    def get_vocabulary_key(self, obj):
        return obj.get_vocabulary_key()

    def get_component_key(self, obj):
        return obj.get_component_key()

    def get_category_key(self, obj):
        if obj.category:
            return obj.category.get_key()
        return None

    def get_display_detail(self, obj):
        """
        not a _real_ field
        just helps me w/ interactivity
        I always load the customizer w/ display_detail = False
        :param obj:
        :return:
        """
        return False

    def to_internal_value(self, data):
        internal_value = super(QScientificPropertyCustomizationSerializer, self).to_internal_value(data)
        # put the category_key back so that I can use it to locate the correct category in "create" and/or "update" below
        internal_value.update({
            "guid": generate_uuid(data.get("key")),
            "category_key": generate_uuid(data.get("category_key")),
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
        category_key = validated_data.pop("category_key")
        category = QScientificCategoryCustomization.objects.get_by_key(category_key)
        validated_data["category"] = category
        return super(QScientificPropertyCustomizationSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        category_key = validated_data.pop("category_key")
        # since I cannot change a property's category (as of v0.15), there is no need to re-set it here
        # category = QScientificCategoryCustomization.objects.get_by_key(category_key)
        # validated_data["category"] = category
        return super(QScientificPropertyCustomizationSerializer, self).update(instance, validated_data)
