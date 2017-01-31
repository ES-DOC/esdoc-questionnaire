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

from Q.questionnaire.serializers.serializers_base import QListSerializer, QSerializer, QVersionSerializerField
from Q.questionnaire.models.models_ontologies import QOntology
from Q.questionnaire.q_utils import serialize_model_to_dict
from Q.questionnaire.q_constants import *


################
# base classes #
################


class QOntologySerializer(QSerializer):

    class Meta:
        model = QOntology
        fields = (
            'id',
            'name',
            'version',
            'documentation',
            'file',
            'title',
            "url",
            'created',
            'modified',
            'ontology_type',
            'is_registered',
            'is_active',
            'key',
            'document_types',
        )
      
        # there is no need to explicitly add QUniqueTogetherValidator
        # b/c that is done automatically in "QSerializer.get_unique_together_validators()"
        # validators = [
        #     QUniqueTogetherValidator(
        #         queryset=QModelCustomization.objects.all(),
        #         # fields=('name', 'version'),
        #     )
        # ]

    version = QVersionSerializerField()
    title = serializers.SerializerMethodField()  # method_name="get_title"
    document_types = serializers.SerializerMethodField(method_name="get_supported_document_types")

    def get_title(self, obj):
        return str(obj)

    def get_supported_document_types(self, obj):
        """
        returns the model_proxies of the current ontology that can be used to create documents
        ie: those w/ the stereotype "document" and that are listed in SUPPORTED_DOCUMENTS
        :param obj:
        :return:
        """
        supported_document_model_proxies = obj.model_proxies.filter(
            is_document=True,
            name__iregex=r'(' + '|'.join(["^{0}$".format(sd) for sd in SUPPORTED_DOCUMENTS["CIM2"]]) + ')',
        ).order_by("name")
        return [
            serialize_model_to_dict(
                model_proxy,
                include={
                    "title": str(model_proxy),
                    "name": model_proxy.name.lower()
                },
                exclude=["guid", "created", "modified", "ontology"]
            )
            for model_proxy in supported_document_model_proxies
        ]
