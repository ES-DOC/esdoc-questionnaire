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

from Q.questionnaire.models.models_realizations import QModelRealization, QCategoryRealization, QPropertyRealization
from Q.questionnaire.models.models_references import QReference
from Q.questionnaire.serializers.serializers_base import QListSerializer, QSerializer, QRelatedSerializerField, QVersionSerializerField
from Q.questionnaire.serializers.serializers_references import QReferenceSerializer



################
# base classes #
################

class QRealizationSerializer(QSerializer):
    pass


class QRealizationListSerializer(QListSerializer):
    pass


class QRealizationRelatedField(QRelatedSerializerField):
    class Meta:
        list_serializer_class = QRealizationListSerializer


###################
# subform classes #
###################

class QRelationshipValueRealizationField(QRealizationRelatedField):

    def to_representation(self, value):
        if not value:
            return {}

        model_serializer = QModelRealizationSerializer()
        representation = model_serializer.to_representation(value)
        return representation

    def to_internal_value(self, data):
        if not data:
            return None

        model_serializer = QModelRealizationSerializer()
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

        model_serializer = QModelRealizationSerializer()
        return model_serializer.create(validated_data)

    def update(self, model_instance, validated_data):
        if not validated_data:
            return model_instance

        model_serializer = QModelRealizationSerializer()
        return model_serializer.update(model_instance, validated_data)

####################
# property classes #
####################


class QPropertyRealizationSerializer(QRealizationSerializer):
    class Meta:
        model = QPropertyRealization
        list_serializer_class = QRealizationListSerializer
        fields = (
            'id',
            'proxy',
            'model',
            'order',
            'name',
            'field_type',
            'category',
            'atomic_value',
            'enumeration_value',
            'enumeration_other_value',
            'relationship_values',
            'relationship_references',
            'is_nil',
            'nil_reason',
            'is_complete',
            # these next fields are not part of the model
            # but they are used to facilitate ng interactivity on the client
            'key',
            'category_key',
            'cardinality_min',
            'cardinality_max',
            'is_multiple',
            'is_infinite',
            'is_hierarchical',
            'possible_relationship_target_types',
            'display_detail',
        )

    enumeration_value = serializers.JSONField(required=False, allow_null=True)

    relationship_values = QRelationshipValueRealizationField(
        many=True,
        required=False,
        allow_null=True,
        queryset=QModelRealization.objects.all(),
        manager=QModelRealization.allow_unsaved_relationship_values_manager,
    )

    relationship_references = QReferenceSerializer(
        many=True,
        required=False,
        allow_null=True,
    )

    possible_relationship_target_types = serializers.SerializerMethodField()
    display_detail = serializers.SerializerMethodField(read_only=True)  # name="get_display_detail"

    # even though 'model_customization' is a required field of the QPropertyCustomization model,
    # it cannot possibly be set before the parent model_customization itself has been saved;
    # so I set 'allow_null' to True here...
    model = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    def get_possible_relationship_target_types(self, obj):
        return obj.get_potential_relationship_target_types()

    def get_display_detail(self, obj):
        return False

    def to_internal_value(self, data):
        internal_value = super(QPropertyRealizationSerializer, self).to_internal_value(data)
        # add the original key to use as guid so that a new key is not automatically generated
        internal_value.update({
            "guid": generate_uuid(data.get("key")),
        })
        pk = data.get("id")
        if pk:
            internal_value.update({
                # put id back so that update/create will work for QListSerializer
                "id": pk,
            })
        else:
            internal_value.update({
                # also put "category_key" back iff this is a new instance
                # so that I can find the correct category in "create" below (it's not needed for "update")
                "category_key": generate_uuid(data.get("category_key")),
            })
        return internal_value

    def create(self, validated_data):
        subform_serializer = self.fields["relationship_values"]
        subform_data = validated_data.pop(subform_serializer.source, [])

        reference_serializer = self.fields["relationship_references"]
        reference_data = validated_data.pop(reference_serializer.source, [])

        category_key = validated_data.pop("category_key", None)
        category_realization = QCategoryRealization.objects.filter(guid=category_key).first()
        assert category_realization is not None
        validated_data["category"] = category_realization

        property_realization = super(QPropertyRealizationSerializer, self).create(validated_data)

        if subform_data:
            # recall that "relationship_values" is a reverse relationship
            # the _real_ field is the "relationship_property" fk on the target_model
            # so set it accordingly...
            relationship_values = subform_serializer.create(subform_data)
            for relationship_value in relationship_values:
                relationship_value.relationship_property = property_realization
                # TODO: DO I REALLY HAVE TO RE-SAVE THE VALUE?
                relationship_value.save()

        if reference_data:
            references = reference_serializer.create(reference_data)
            for reference in references:
                property_realization.relationship_references.add(reference)
                reference.save()
            property_realization.save()

        return property_realization

    def update(self, instance, validated_data):

        subform_serializer = self.fields["relationship_values"]
        subform_data = validated_data.pop(subform_serializer.source, [])

        reference_serializer = self.fields["relationship_references"]
        reference_data = validated_data.pop(reference_serializer.source, [])

        # there is no need to update category, b/c it will have been set in "create" above and it cannot change
        # category_key = validated_data.pop("category_key", None)
        # category_realization = QCategoryRealization.objects.filter(guid=category_key).first()
        # validated_data["category"] = category_realization

        property_realization = super(QPropertyRealizationSerializer, self).update(instance, validated_data)

        if subform_data:
            # recall that "relationship_values" is a reverse relationship
            # the _real_ field is the "relationship_property" fk on the relationship_value model
            # so set it accordingly
            relationship_values = subform_serializer.update(instance.relationship_values.all(), subform_data)
            for relationship_value in relationship_values:
                if relationship_value.relationship_property != property_realization:
                    relationship_value.relationship_property = property_realization
                    # TODO: DO I REALLY HAVE TO RE-SAVE THE MODEL?
                    relationship_value.save()

        if reference_data:
            import ipdb; ipdb.set_trace()
            # see the comment in QReferenceListSerializer about having to do removal of deleted references here
            updated_references = False
            old_references = instance.relationship_references.all()
            new_references = reference_serializer.update(old_references, reference_data)
            for new_reference in new_references:
                if new_reference not in old_references:
                    updated_references = True
                    property_realization.relationship_references.add(new_reference)
                    new_reference.save()
            for old_reference in old_references:
                if old_reference not in new_references:
                    updated_references = True
                    property_realization.relationship_references.remove(old_reference)
                    old_reference.save()
            if updated_references:
                property_realization.save()

        return property_realization


####################
# category classes #
####################


class QCategoryRealizationSerializer(QRealizationSerializer):
    class Meta:
        model = QCategoryRealization
        list_serializer_class = QRealizationListSerializer
        fields = (
            'id',
            'proxy',
            'model',
            'order',
            'is_complete',
            'name',
            'category_value',
            # these next fields are not part of the model
            # but they are used to facilitate ng interactivity on the client
            'key',
            'is_uncategorized',
            'properties_keys',
            'display_detail',
        )

    properties_keys = serializers.SerializerMethodField(read_only=True)
    display_detail = serializers.SerializerMethodField(read_only=True)

    # even though 'model' is a required field of the QStandardCategoryCustomization model,
    # it cannot possibly be set before the parent model_customization itself has been saved;
    # so I set 'allow_null' to True here...
    model = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    def get_properties_keys(self, obj):
        return obj.get_properties_keys()

    def get_display_detail(self, obj):
        return True

    def to_internal_value(self, data):
        internal_value = super(QCategoryRealizationSerializer, self).to_internal_value(data)
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
        return super(QCategoryRealizationSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        return super(QCategoryRealizationSerializer, self).update(instance, validated_data)


#################
# model classes #
#################

class QModelRealizationSerializer(QRealizationSerializer):

    class Meta:
        model = QModelRealization
        fields = (
            'id',
            'version',
            'order',
            'name',
            'owner',
            'shared_owners',
            'project',
            'proxy',
            'is_document',
            'is_root',
            'is_meta',
            'is_active',
            'is_complete',
            'categories',
            'properties',
            # these next fields are not part of the model
            # but they are used to facilitate ng interactivity on the client
            'key',
            'title',
            'is_selected',
            'display_detail',
        )

    version = QVersionSerializerField(allow_null=True)
    shared_owners = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    categories = QCategoryRealizationSerializer(many=True, required=False)
    properties = QPropertyRealizationSerializer(many=True, required=False)

    is_selected = serializers.SerializerMethodField()
    display_detail = serializers.SerializerMethodField()

    def get_title(self, obj):
        return "foobar"

    def get_is_selected(self, obj):
        return False

    def get_display_detail(self, obj):
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
            model_realization = QModelRealization.objects.create(**validated_data)
        except DjangoValidationError as e:
            model_realization = None
            validation_errors.detail.update(e.message_dict)

        try:
            for category_data in categories_data:
                category_data["model"] = model_realization
            categories_serializer.create(categories_data)
        except DjangoValidationError as e:
            validation_errors.detail.update(e.message_dict)
        except ValueError as e:
            # if we couldn't save the category_customization just b/c there were problems w/ the model_customization, that's okay...
            if model_realization is not None:
                raise e

        try:
            for property_data in properties_data:
                property_data["model"] = model_realization
            properties_serializer.create(properties_data)
        except DjangoValidationError as e:
            validation_errors.detail.update(e.message_dict)
        except ValueError as e:
            # as above, if we couldn't save the property_customization just b/c there were problems w/ the model_customization, that's okay...
            if model_realization is not None:
                raise e

        if len(validation_errors.detail):
            raise validation_errors

        return model_realization

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

        categories_data = validated_data.pop(categories_serializer.source, instance.categories.values())
        properties_data = validated_data.pop(properties_serializer.source, instance.properties.values())

        try:
            model_realization = super(QModelRealizationSerializer, self).update(instance, validated_data)
        except DjangoValidationError as e:
            validation_errors.detail.update(e.message_dict)

        try:
            categories_serializer.update(model_realization.categories.all(), categories_data)
        except DjangoValidationError as e:
            validation_errors.detail.update(e.message_dict)

        try:
            properties_serializer.update(model_realization.properties.all(), properties_data)
        except DjangoValidationError as e:
            validation_errors.detail.update(e.message_dict)

        if len(validation_errors.detail):
            raise validation_errors

        return model_realization
