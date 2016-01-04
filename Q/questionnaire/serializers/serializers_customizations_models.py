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
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from uuid import UUID as generate_uuid
from ast import literal_eval

from Q.questionnaire.serializers.serializers_customizations import QCustomizationSerializer
from Q.questionnaire.serializers.serializers_customizations_vocabularies import QModelCustomizationVocabularySerializer
from Q.questionnaire.serializers.serializers_customizations_categories import QStandardCategoryCustomizationSerializer, QScientificCategoryCustomizationSerializer
from Q.questionnaire.serializers.serializers_customizations_properties import QStandardPropertyCustomizationSerializer, QScientificPropertyCustomizationSerializer
from Q.questionnaire.models.models_customizations import QModelCustomization


class QModelCustomizationSerializer(QCustomizationSerializer):

    class Meta:
        model = QModelCustomization
        fields = (
            'id',
            'name',
            'description',
            'is_default',
            'ontology',
            'proxy',
            'project',
            'vocabularies',
            'model_title',
            'model_description',
            'model_show_all_categories',
            'model_show_hierarchy',
            'model_hierarchy_name',
            'model_root_component',
            'standard_categories',
            'standard_properties',
            'scientific_categories',
            'scientific_properties',
        )

        # there is no need to explicitly add QUniqueTogetherValidator
        # b/c that is done automatically in "QSerializer.get_unique_together_validators()"
        # validators = [
        #     QUniqueTogetherValidator(
        #         queryset=QModelCustomization.objects.all(),
        #         # fields=('name', 'proxy', 'project'),
        #     )
        # ]

    # TODO: I NEED TO USE THE "source" KWARG TO SPECIFY RELATED FIELDS WHEN THE NAME OF THE SERIALIZER FIELD DOESN'T MATCH THE NAME OF THE MODEL FIELD
    # TODO: WOULDN'T IT JUST BE EASIER TO USE THE SAME NAME (SEE COMMENTS IN model_customizations)
    vocabularies = QModelCustomizationVocabularySerializer(many=True, required=False, source="link_to_model_customization", read_only=False)
    standard_categories = QStandardCategoryCustomizationSerializer(many=True, required=False, source="standard_category_customizations")
    standard_properties = QStandardPropertyCustomizationSerializer(many=True, required=False)
    scientific_categories = QScientificCategoryCustomizationSerializer(many=True, required=False, source="scientific_category_customizations")
    scientific_properties = QScientificPropertyCustomizationSerializer(many=True, required=False)

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
        validation_errors = ValidationError({})

        vocabularies_serializer = self.fields["vocabularies"]
        standard_categories_serializer = self.fields['standard_categories']
        standard_properties_serializer = self.fields["standard_properties"]
        scientific_categories_serializer = self.fields["scientific_categories"]
        scientific_properties_serializer = self.fields["scientific_properties"]

        vocabulary_customizations_data = validated_data.pop(vocabularies_serializer.source, [])
        standard_categories_data = validated_data.pop(standard_categories_serializer.source, [])
        standard_properties_data = validated_data.pop(standard_properties_serializer.source, [])
        scientific_categories_data = validated_data.pop(scientific_categories_serializer.source, [])
        scientific_properties_data = validated_data.pop(scientific_properties_serializer.source, [])

        try:
            model_customization = QModelCustomization.objects.create(**validated_data)
        except DjangoValidationError as e:
            model_customization = None
            print(e.message)
            validation_errors.detail.update(e.message_dict)

        try:
            for vocabulary_customization_data in vocabulary_customizations_data:
                vocabulary_customization_data["model_customization"] = model_customization
            vocabularies_serializer.create(vocabulary_customizations_data)
        except DjangoValidationError as e:
            print(e.message)
            validation_errors.detail.update(e.message_dict)

        try:
            for standard_category_data in standard_categories_data:
                standard_category_data["model_customization"] = model_customization
            standard_categories_serializer.create(standard_categories_data)
        except DjangoValidationError as e:
            print(e.message)
            validation_errors.detail.update(e.message_dict)

        try:
            for standard_property_data in standard_properties_data:
                standard_property_data["model_customization"] = model_customization
                # TODO: I WOULD HANDLE ENUMERATION FIELDS W/ A CUSTOM FIELD, BUT THIS WILL DO FOR NOW
                # standard_property_data["enumeration_choices"] = literal_eval(standard_property_data["enumeration_choices"])
                # standard_property_data["enumeration_default"] = literal_eval(standard_property_data["enumeration_default"])
            standard_properties_serializer.create(standard_properties_data)
        except DjangoValidationError as e:
            print(e.message)
            validation_errors.detail.update(e.message_dict)

        try:
            for scientific_category_data in scientific_categories_data:
                scientific_category_data["model_customization"] = model_customization
            scientific_categories_serializer.create(scientific_categories_data)
        except DjangoValidationError as e:
            print(e.message)
            validation_errors.detail.update(e.message_dict)

        try:
            for scientific_property_data in scientific_properties_data:
                scientific_property_data["model_customization"] = model_customization
                # TODO: I WOULD HANDLE ENUMERATION FIELDS W/ A CUSTOM FIELD, BUT THIS WILL DO FOR NOW
                # scientific_property_data["enumeration_choices"] = literal_eval(scientific_property_data["enumeration_choices"])
                # scientific_property_data["enumeration_default"] = literal_eval(scientific_property_data["enumeration_default"])
            scientific_properties_serializer.create(scientific_properties_data)
        except DjangoValidationError as e:
            print(e.message)
            validation_errors.detail.update(e.message_dict)

        if len(validation_errors.detail):
            raise validation_errors

        return model_customization

    def update(self, model_instance, validated_data):
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
        validation_errors = ValidationError({})

        vocabularies_serializer = self.fields["vocabularies"]
        standard_categories_serializer = self.fields["standard_categories"]
        standard_properties_serializer = self.fields["standard_properties"]
        scientific_categories_serializer = self.fields["scientific_categories"]
        scientific_properties_serializer = self.fields["scientific_properties"]

        vocabulary_customizations_data = validated_data.pop(vocabularies_serializer.source, [])
        standard_categories_data = validated_data.pop(standard_categories_serializer.source, model_instance.standard_category_customizations.values())
        standard_properties_data = validated_data.pop(standard_properties_serializer.source, model_instance.standard_properties.values())
        scientific_categories_data = validated_data.pop(scientific_categories_serializer.source, model_instance.scientific_category_customizations.values())
        scientific_properties_data = validated_data.pop(scientific_properties_serializer.source, model_instance.scientific_properties.values())

        model_customization = model_instance

        try:
            # deserialize_dict_to_model(model_customization, validated_data)
            # model_customization.save()
            super(QModelCustomizationSerializer, self).update(model_customization, validated_data)
        except DjangoValidationError as e:
            validation_errors.detail.update(e.message_dict)

        try:
            vocabularies_serializer.update(model_instance.get_vocabularies_through(), vocabulary_customizations_data)
        except DjangoValidationError as e:
            validation_errors.detail.update(e.message_dict)

        try:
            standard_categories_serializer.update(model_instance.standard_category_customizations.all(), standard_categories_data)
        except DjangoValidationError as e:
            validation_errors.detail.update(e.message_dict)

        try:
            # for standard_property_data in standard_properties_data:
            #     # TODO: I WOULD HANDLE ENUMERATION FIELDS W/ A CUSTOM FIELD, BUT THIS WILL DO FOR NOW
            #     # standard_property_data["enumeration_choices"] = literal_eval(standard_property_data["enumeration_choices"])
            #     # standard_property_data["enumeration_default"] = literal_eval(standard_property_data["enumeration_default"])
            #     pass
            standard_properties_serializer.update(model_instance.standard_properties.all(), standard_properties_data)
        except DjangoValidationError as e:
            validation_errors.detail.update(e.message_dict)

        try:
            scientific_categories_serializer.update(model_instance.scientific_category_customizations.all(), scientific_categories_data)
        except DjangoValidationError as e:
            validation_errors.detail.update(e.message_dict)

        try:
            # for scientific_property_data in scientific_properties_data:
            #     # TODO: I WOULD HANDLE ENUMERATION FIELDS W/ A CUSTOM FIELD, BUT THIS WILL DO FOR NOW
            #     # scientific_property_data["enumeration_choices"] = literal_eval(scientific_property_data["enumeration_choices"])
            #     # scientific_property_data["enumeration_default"] = literal_eval(scientific_property_data["enumeration_default"])
            #     pass
            scientific_properties_serializer.update(model_instance.scientific_properties.all(), scientific_properties_data)
        except DjangoValidationError as e:
            validation_errors.detail.update(e.message_dict)

        if len(validation_errors.detail):
            raise validation_errors

        return model_customization

