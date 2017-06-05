####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as RestValidationError
from rest_framework import serializers
from uuid import UUID as generate_uuid

from Q.questionnaire.serializers.serializers_base import QListSerializer, QSerializer, QRelatedSerializerField
from Q.questionnaire.models.models_customizations import QModelCustomization, QCategoryCustomization, QPropertyCustomization


################
# base classes #
################

class QCustomizationSerializer(QSerializer):
    pass


class QCustomizationListSerializer(QListSerializer):
    pass


class QCustomizationRelatedField(QRelatedSerializerField):
    class Meta:
        list_serializer_class = QCustomizationListSerializer

###################
# subform classes #
###################

class QSubformCustomizationField(QCustomizationRelatedField):

    def to_representation(self, value):
        if not value:
            return {}

        model_serializer = QModelCustomizationSerializer()
        representation = model_serializer.to_representation(value)
        return representation

    def to_internal_value(self, data):
        if not data:
            return None

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

        model_serializer = QModelCustomizationSerializer()
        return model_serializer.create(validated_data)

    def update(self, model_instance, validated_data):
        if not validated_data:
            return model_instance

        model_serializer = QModelCustomizationSerializer()
        return model_serializer.update(model_instance, validated_data)


####################
# property classes #
####################


class QPropertyCustomizationSerializer(QCustomizationSerializer):
    class Meta:
        model = QPropertyCustomization
        list_serializer_class = QCustomizationListSerializer
        fields = (
            'id',
            'name',
            'property_title',
            'property_description',
            'order',
            'proxy',
            'project',
            'model_customization',
            'field_type',
            'cardinality',
            'category_customization',
            'can_inherit',
            'inline_help',
            'is_editable',
            'is_hidden',
            'is_meta',
            'is_nillable',
            'is_required',
            'default_values',
            'atomic_suggestions',
            'atomic_type',
            'enumeration_display_all',
            'enumeration_is_open',
            'relationship_show_subforms',
            'relationship_target_model_customizations',
            'relationship_is_hierarchical',
            # these next fields are not part of the model
            # but they are used to facilitate ng interactivity on the client
            'proxy_title',
            'proxy_id',
            'category_key',
            'key',
            'display_detail',
        )

    category_key = serializers.SerializerMethodField(read_only=True)  # name="get_category_key"
    display_detail = serializers.SerializerMethodField(read_only=True)  # name="get_display_detail"
    proxy_title = serializers.SerializerMethodField(read_only=True)  # name="get_proxy_title"
    proxy_id = serializers.SerializerMethodField(read_only=True)  # name="get_proxy_id"

    default_values = serializers.JSONField(required=False, allow_null=True)

    relationship_target_model_customizations = QSubformCustomizationField(
        many=True,
        required=False,
        allow_null=True,
        queryset=QModelCustomization.objects.all(),
        manager=QModelCustomization.allow_unsaved_relationship_target_model_customizations_manager,
    )

    # even though 'model_customization' is a required field of the QPropertyCustomization model,
    # it cannot possibly be set before the parent model_customization itself has been saved;
    # so I set 'allow_null' to True here...
    model_customization = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    def get_display_detail(self, obj):
        return False

    def get_proxy_title(self, obj):
        return str(obj.proxy)

    def get_proxy_id(self, obj):
        return obj.proxy.cim_id

    def get_category_key(self, obj):
        return obj.category_customization.key

    def to_internal_value(self, data):
        internal_value = super(QPropertyCustomizationSerializer, self).to_internal_value(data)
        # add the original key to use as guid so that a new key is not automatically generated
        internal_value.update({
            "guid": generate_uuid(data.get("key")),
            "category_key": generate_uuid(data.get("category_key")),  # also put category_key back so I can use it to locate the correct category in 'create' below
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
        category_customization = QCategoryCustomization.objects.filter(guid=category_key).first()
        # don't make this assertion... category_customization may be none b/c there were errors creating _it_
        # assert category_customization is not None, "Unable to locate category customization"
        validated_data["category_customization"] = category_customization

        property_customization = super(QPropertyCustomizationSerializer, self).create(validated_data)

        if subform_data:
            # recall that "relationship_target_model_customizations" is a reverse relationship
            # the _real_ field is the "relationship_source_property_customization" fk on the target_model
            # so set it accordingly...
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
        # category_customization = QCategoryCustomization.objects.filter(guid=category_key).first()
        # validated_data["category_customization"] = category_customization

        property_customization = super(QPropertyCustomizationSerializer, self).update(instance, validated_data)

        if subform_data:
            # the fk will already be set, so there is no need to deal w/ it or re-save the targets here as above
            subform_serializer.update(instance.relationship_target_model_customizations.all(), subform_data)

        return property_customization


####################
# category classes #
####################


class QCategoryCustomizationSerializer(QCustomizationSerializer):
    class Meta:
        model = QCategoryCustomization
        list_serializer_class = QCustomizationListSerializer
        fields = (
            'id',
            'name',
            'category_title',
            'category_description',
            'is_hidden',
            'order',
            'proxy',
            'project',
            'model_customization',
            # these next fields are not part of the model
            # but they are used to facilitate ng interactivity on the client
            'proxy_title',
            'proxy_id',
            'key',
            'is_empty',
            'num_properties',
            'display_detail',
            'display_properties',
        )

    display_properties = serializers.SerializerMethodField(read_only=True)  # name="get_display_properties"
    display_detail = serializers.SerializerMethodField(read_only=True)  # name="get_display_detail"
    proxy_title = serializers.SerializerMethodField(read_only=True)  # name="get_proxy_title"
    proxy_id = serializers.SerializerMethodField(read_only=True)  # name="get_proxy_id"
    num_properties = serializers.SerializerMethodField(read_only=True)  # name="get_num_properties"

    # even though 'model_customization' is a required field of the QStandardCategoryCustomization model,
    # it cannot possibly be set before the parent model_customization itself has been saved;
    # so I set 'allow_null' to True here...
    model_customization = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    def get_display_detail(self, obj):
        return False

    def get_display_properties(self, obj):
        return True

    def get_proxy_title(self, obj):
        return str(obj.proxy)

    def get_proxy_id(self, obj):
        return obj.proxy.cim_id

    def get_num_properties(self, obj):
        return obj.property_customizations(manager="allow_unsaved_category_customizations_manager").count()

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
        return super(QCategoryCustomizationSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        return super(QCategoryCustomizationSerializer, self).update(instance, validated_data)


#################
# model classes #
#################

class QModelCustomizationSerializer(QCustomizationSerializer):

    class Meta:
        model = QModelCustomization
        fields = (
            'id',
            'name',
            'owner',
            'shared_owners',
            'proxy',
            'project',
            'documentation',
            'is_document',
            'is_meta',
            'is_default',
            'order',
            'model_title',
            'model_description',
            'model_hierarchy_title',
            'model_show_empty_categories',
            'categories',
            'properties',
            # these next fields are not part of the model
            # but they are used to facilitate ng interactivity on the client
            'proxy_title',
            'proxy_id',
            'key',
            'display_detail',
        )

    shared_owners = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    proxy_title = serializers.SerializerMethodField()
    proxy_id = serializers.SerializerMethodField()
    display_detail = serializers.SerializerMethodField()

    categories = QCategoryCustomizationSerializer(many=True, required=False, source="category_customizations")
    properties = QPropertyCustomizationSerializer(many=True, required=False, source="property_customizations")

    def get_proxy_title(self, obj):
        return str(obj.proxy)

    def get_proxy_id(self, obj):
        return obj.proxy.cim_id

    def get_display_detail(self, obj):
        # obviously, this field only comes into play for subforms
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

        categories_serializer = self.fields["categories"]
        properties_serializer = self.fields["properties"]

        categories_data = validated_data.pop(categories_serializer.source, [])
        properties_data = validated_data.pop(properties_serializer.source, [])

        try:
            model_customization = QModelCustomization.objects.create(**validated_data)
        except DjangoValidationError as e:
            model_customization = None
            validation_errors.detail.update(e.message_dict)

        try:
            for category_data in categories_data:
                category_data["model_customization"] = model_customization
            categories_serializer.create(categories_data)
        except DjangoValidationError as e:
            validation_errors.detail.update(e.message_dict)
        except ValueError as e:
            # if we couldn't save the category_customization just b/c there were problems w/ the model_customization, that's okay...
            if model_customization is not None:
                raise e

        try:
            for property_data in properties_data:
                property_data["model_customization"] = model_customization
            properties_serializer.create(properties_data)
        except DjangoValidationError as e:
            validation_errors.detail.update(e.message_dict)
        except ValueError as e:
            # as above, if we couldn't save the property_customization just b/c there were problems w/ the model_customization, that's okay...
            if model_customization is not None:
                raise e

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