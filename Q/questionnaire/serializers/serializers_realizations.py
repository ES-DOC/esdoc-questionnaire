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

from rest_framework import serializers

from Q.questionnaire.models.models_realizations import QModel, QStandardProperty

class QPropertyValueField(serializers.RelatedField):

    def to_representation(self, property):
        import ipdb; ipdb.set_trace()
        value = property.get_value()
        # TODO: ADD SOME CONDITIONAL PROCESSING DEPENDING ON WHAT TYPE OF FIELD PROPERTY IS
        return '%s' % value

class QStandardPropertySerializer(serializers.ModelSerializer):

    class Meta:
        model = QStandardProperty
        fields = (
            'id',
            # 'guid',
            # 'created',
            # 'modified',
            'model',
            'field_type',
            'is_label',
            'name',
        )

    # TODO: UNCOMMENT THIS TO HAVE A HYPERLINKED RELATION
    # model = serializers.HyperlinkedRelatedField(read_only=True, view_name="model-detail")

class QModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = QModel
        fields = (
            'id',
            # 'guid',
            # 'created',
            # 'modified',
            'version',
            'project',
            'is_document',
            'is_root',
            'is_published',
            'is_active',
            'standard_properties',
            'parent',
            "name",
            "description",
        )

    standard_properties = QStandardPropertySerializer(many=True)

    def create(self, validated_data):
        """
        ensures that nested fields (properties) are updated/created along w/ parent model
        :param validated_data
        :return the created model
        """
        standard_properties_data = validated_data.pop("standard_properties", [])
        model_instance = QModel.objects.create(**validated_data)
        for standard_property_data in standard_properties_data:
            standard_property_pk = standard_property_data.get("id")
            try:
                standard_property = QStandardProperty.objects.get(pk=standard_property_pk)
                standard_property.update(**standard_property_data)
            except QStandardProperty.DoesNotExist:
                standard_property = QStandardProperty.objects.create(**standard_property_data)
                model_instance.standard_properties.add(standard_property)
        return model_instance

    def update(self, model_instance, validated_data):
        """
        ensures that nested fields (properties) are updated/created along w/ parent model
        :param instance:
        :param validated_data:
        :return:
        """
        standard_properties_data = validated_data.pop("standard_properties", [])
        QModel.objects.update(**validated_data)
        for standard_property_data in standard_properties_data:
            standard_property_pk = standard_property_data.get("id")
            try:
                standard_property = QStandardProperty.objects.get(pk=standard_property_pk)
                standard_property.update(**standard_property_data)
            except QStandardProperty.DoesNotExist:
                standard_property = QStandardProperty.objects.create(**standard_property_data)
                model_instance.standard_properties.add(standard_property)
        return model_instance
