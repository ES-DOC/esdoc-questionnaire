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

from Q.questionnaire.models.models_ontologies import QOntology
from Q.questionnaire.q_constants import SUPPORTED_DOCUMENTS

# this is a pretty stripped-down serializer
# but it's only needed for the Project Page
# (to populate the "create new document/customization" widgets)

class QOntologySerializer(serializers.ModelSerializer):

    class Meta:
        model = QOntology
        fields = (
            "id", "guid", "created", "modified",
            "name", "version", "url", "key", "description", "is_registered",
            "file", "categorization", "ontology_type",
            "title", "document_types"
        )

    title = serializers.SerializerMethodField()  # method_name="get_title"
#    projects = serializers.SerializerMethodField(method_name="get_supported_projects")
    document_types = serializers.SerializerMethodField(method_name="get_supported_document_types")

    def get_title(self, obj):
        return str(obj)  # the __str__ method already does what I want, so just convert obj to a string

    def get_supported_document_types(self, obj):
        """
        returns the model_proxies of the current ontology that can be used to create documents
        ie: those w/ the stereotype "document" and that are listed in SUPPORTED_DOCUMENTS
        :param obj:
        :return:
        """
        supported_document_model_proxies = obj.model_proxies.filter(
            stereotype__iexact="document",
            name__iregex=r'(' + '|'.join(["^{0}$".format(sd) for sd in SUPPORTED_DOCUMENTS["CIM2"]]) + ')',
        ).order_by("name")
        return [
            {
                "id": model_proxy.pk,
                "name": model_proxy.name.lower(),
                "title": str(model_proxy),
                # "ontology_id": obj.pk,
            }
            for model_proxy in supported_document_model_proxies
        ]

#    def get_supported_projects(self, obj):
#        """
#        returns the ids of the projects that support this ontology
#        (recall that QProject has a "through" model w/ QProjectOntology representing that relationship)
#        (this works off of the reverse of that m2m field)
#        :param obj:
#        :return:
#        """
#        return obj.qproject_set.values_list("id", flat=True)
