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
.. module:: serializers_realizations_properties

DRF Serializers for realization classes

"""


from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as RestValidationError
from rest_framework import serializers

from uuid import UUID as generate_uuid
from Q.questionnaire.q_fields import QPropertyTypes
from Q.questionnaire.serializers.serializers_base import QEnumerationSerializerField
from Q.questionnaire.serializers.serializers_realizations import QRealizationSerializer, QRealizationListSerializer, QRealizationManagedRelatedField
from Q.questionnaire.models.models_realizations import QModel, QProperty

class QRelationshipModelRealizationField(QRealizationManagedRelatedField):
    """
    This is a custom field; it presents a relational field (actually, the reverse of a fk) to QProperty
    but it can cope w/ unsaved models!
    """

    # TODO: WHY DO I STILL HAVE TO PASS "queryset" TO THE FIELD CONSTRUCTOR BELOW IF IT'S IN THE CLASS DEFINITION HERE ?
    queryset = QModel.objects.all()

    def to_representation(self, value):
        if not value:
            return {}

        # need to import w/in this fn to prevent circular dependencies
        from .serializers_realizations_models import QModelRealizationSerializer
        model_serializer = QModelRealizationSerializer()
        representation = model_serializer.to_representation(value)
        return representation

    def to_internal_value(self, data):
        if not data:
            return None

        # need to import w/in this fn to prevent circular dependencies
        from .serializers_realizations_models import QModelRealizationSerializer
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

        # need to import w/in this fn to prevent circular dependencies
        from .serializers_realizations_models import QModelRealizationSerializer
        model_serializer = QModelRealizationSerializer()
        return model_serializer.create(validated_data)

    def update(self, model_instance, validated_data):
        if not validated_data:
            return model_instance

        # need to import w/in this fn to prevent circular dependencies
        from .serializers_realizations_models import QModelRealizationSerializer
        model_serializer = QModelRealizationSerializer()
        return model_serializer.update(model_instance, validated_data)


class QPropertyRealizationSerializer(QRealizationSerializer):

    class Meta:
        model = QProperty
        list_serializer_class = QRealizationListSerializer
        fields = (
            'id',
            'name',
            # 'model',  # (this is set explicitly by the parent serializer)
            'proxy',
            'order',
            'field_type',
            'cardinality',
            'atomic_value',
            'enumeration_value',
            'enumeration_other_value',
            'relationship_values',
            'is_nil',
            'nil_reason',
            'is_complete',
            # these next fields are not part of the model
            # but they are used to facilitate ng interactivity on the client
            'key',
            # TODO: 'is_multiple' IS COMPUTED IN THE NG CONTROLLER; NO NEED TO REPLICATE IT HERE
            'is_multiple',
            'is_required',
            'possible_relationship_targets',
            'display_detail',
        )

    enumeration_value = QEnumerationSerializerField(allow_null=True)

    relationship_values = \
        QRelationshipModelRealizationField(
            many=True,
            required=False,
            allow_null=True,
            # allow_unsaved=True,
            manager=QModel.allow_unsaved_relationship_values_manager,
            queryset=QModel.objects.all(),
        )

    key = serializers.SerializerMethodField(read_only=True)  # name="get_key"
    # is_complete = serializers.SerializerMethodField(read_only=True)  # name="get_is_complete"
    is_multiple = serializers.SerializerMethodField(read_only=True)  # name="get_is_multiple"
    is_required = serializers.SerializerMethodField(read_only=True)  # name="get_is_required
    possible_relationship_targets = serializers.SerializerMethodField(read_only=True)  # name="get_possible_relationship_targets"
    display_detail = serializers.SerializerMethodField(read_only=True)  # name="get_display_detail"

    def get_key(self, obj):
        # using a SerailizerMethodField instead of guid directly b/c guid is a non-editable field
        return obj.get_key()

    # def get_is_complete(self, obj):
    #     return obj.is_complete()

    def get_possible_relationship_targets(self, obj):
        return obj.get_possible_relationship_targets()

    def get_is_multiple(self, obj):
        return obj.is_multiple()

    def get_is_required(self, obj):
        """
        helps w/ determining completeness; if a property is not required then I don't bother adjusting the is_complete property
        even if it is set to nillable
        this serialization determines requiredness based on the default (proxy) cardinality
        however, the form can override this during customization
        :param obj:
        :return:
        """
        return int(obj.get_cardinality_min()) > 0

    def get_display_detail(self, obj):
        """
        not a _real_ field
        just helps me w/ interactivity
        I always load the editor w/ display_detail = False
        :param obj:
        :return:
        """
        return False

    def to_internal_value(self, data):
        internal_value = super(QPropertyRealizationSerializer, self).to_internal_value(data)

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

        subform_serializer = self.fields["relationship_values"]
        subform_data = validated_data.pop(subform_serializer.source, [])

        property_realization = super(QPropertyRealizationSerializer, self).create(validated_data)

        if subform_data:
            # recall that "relationship_values" is a reverse relationship
            # the _real_ field is the "relationship_property" fk on the relationship_value model
            # so set it accordingly
            relationship_values = subform_serializer.create(subform_data)
            for relationship_value in relationship_values:
                relationship_value.relationship_property = property_realization
                # TODO: DO I REALLY HAVE TO RE-SAVE THE MODEL?
                relationship_value.save()

        return property_realization


    def update(self, instance, validated_data):

        subform_serializer = self.fields["relationship_values"]
        subform_data = validated_data.pop(subform_serializer.source, [])

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

        return property_realization
