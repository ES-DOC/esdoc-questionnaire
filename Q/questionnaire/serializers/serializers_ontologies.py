####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

from rest_framework import serializers

from Q.questionnaire.models.models_ontologies import QOntology
from Q.questionnaire.q_constants import SUPPORTED_DOCUMENTS

# this is a pretty stripped-down serializer
# but it's only needed for the Project Page
# (to populate the "create new document" widgets)

class QOntologySerializer(serializers.ModelSerializer):

    class Meta:
        model = QOntology
        fields = (
            "id", "guid", "created", "modified", "name", "version",
            "description", "type", "key", "url", "file",
            "categorization", "is_registered", "title", "document_types"
        )

    title = serializers.SerializerMethodField()  # method_name="get_title"
    document_types = serializers.SerializerMethodField(method_name="get_supported_document_types")

    def get_title(self, obj):
        return str(obj)  # the __unicode__ method already does what I want, so just convert obj to a string

    def get_supported_document_types(self, obj):
        """
        returns the model_proxies of the current ontology that can be used to create documents
        ie: those w/ the stereotype "document" and that are listed in SUPPORTED_DOCUMENTS
        :param obj:
        :return:
        """
        supported_document_model_proxies = obj.model_proxies.filter(
            stereotype__iexact="document",
            name__iregex=r'(' + '|'.join(SUPPORTED_DOCUMENTS) + ')',
        ).order_by("name")
        return [
            {
                "id": dmp.pk,
                "name": dmp.name.lower(),
                "title": str(dmp),
                # "ontology_id": obj.pk,
            }
            for dmp in supported_document_model_proxies
        ]

