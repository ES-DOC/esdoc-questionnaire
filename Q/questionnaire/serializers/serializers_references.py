####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

# from django.core.exceptions import ValidationError as DjangoValidationError
# from rest_framework.exceptions import ValidationError as RestValidationError
from rest_framework.serializers import ModelSerializer, ListSerializer

from Q.questionnaire.models.models_references import QReference, QReferenceMap

# this is a bit of a strange serializer b/c the representation is necessarily a simple JSON array
# (b/c it comes from the ES-DOC search API)
# it and must therefore be converted to the sort of content expected by rest_framework


class QReferenceListSerializer(ListSerializer):

    # TODO: NOT SURE WHY I HAVE TO OVERWRITE "to_internal_value" ON THE LIST CLASS
    # TODO: BUT I HAVE TO OVERWRITE "to_representation" ON THE DETAIL CLASS

    def to_internal_value(self, data):
        actual_data = [d for d in data if d is not None]
        converted_data = [
            {
                field_name: ad[list_index]
                for field_name, list_index in QReferenceMap.items()
            }
            for ad in actual_data
        ]
        internal_value = super(QReferenceListSerializer, self).to_internal_value(converted_data)
        return internal_value

    def create(self, validated_data):
        return self.create_or_update(validated_data)

    def update(self, instances, validated_data):
        # note that it is up to the parent QProperty to remove those instances that are not returned by this function
        return self.create_or_update(validated_data)

    def create_or_update(self, validated_data):
        references = []
        for attrs in validated_data:
            try:
                existing_reference = QReference.objects.get(**attrs)
                references.append(self.child.update(existing_reference, attrs))
            except QReference.DoesNotExist:
                references.append(self.child.create(attrs))
        return references


class QReferenceSerializer(ModelSerializer):

    # TODO: NOT SURE WHY I HAVE TO OVERWRITE "to_internal_value" ON THE LIST CLASS
    # TODO: BUT I HAVE TO OVERWRITE "to_representation" ON THE DETAIL CLASS

    class Meta:
        model = QReference
        list_serializer_class = QReferenceListSerializer
        fields = (
            # 'id',
            'guid',
            'model',
            'experiment',
            'institute',
            'name',
            'canonical_name',
            'alternative_name',
            'long_name',
            'version',
            'document_type',
        )

    def to_representation(self, instance):
        data_dict = super(QReferenceSerializer, self).to_representation(instance)
        ret = []
        for field_name, field_value in QReferenceMap.items():
            ret.append(data_dict[field_name])
        return ret
