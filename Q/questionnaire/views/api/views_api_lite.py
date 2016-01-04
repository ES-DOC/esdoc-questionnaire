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


from rest_framework import generics, filters
import django_filters

# from Q.questionnaire.models.models_realizations import QModel
from Q.questionnaire.models.models_realizations_bak import MetadataModel
from Q.questionnaire.models.models_customizations import QModelCustomization
from Q.questionnaire.serializers.serializers_lite import QModelCustomizationSerializerLite, MetadataModelSerializerLite
from Q.questionnaire.views.api.views_api_realizations import QModelFilter
from Q.questionnaire.views.api.views_api_customizations import QModelCustomizationFilter
from Q.questionnaire.views.api.views_api_base import BetterBooleanFilter


# TODO: REMOVE THIS STUFF FOR POST v0.15
class MetadataModelFilter(django_filters.FilterSet):

    class Meta:
        model = MetadataModel
        fields = [
            "id", "guid", "created", "last_modified", "name", "document_version",
            "description", "version", "proxy", "project", "is_document",
            "is_root", "is_published",
        ]

    is_document = BetterBooleanFilter(name="is_document")
    is_root = BetterBooleanFilter(name="is_root")
    is_published = BetterBooleanFilter(name="is_published")

    @classmethod
    def get_field_names(cls):
        """
        Simple way to make sure that _all_ filtered fields
        are available to the views below
        """
        return tuple(cls.Meta.fields)

class QModelLiteList(generics.ListAPIView):
    # TODO: CHANGE THIS STUFF BACK TO "QModel" STUFF FOR POST v0.15
    # queryset = QModel.objects.root_documents()
    queryset = MetadataModel.objects.filter(is_document=True, is_root=True)
    serializer_class = MetadataModelSerializerLite
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    # filter_class = QModelFilter
    # filter_fields = QModelFilter.get_field_names()
    filter_class = MetadataModelFilter
    filter_fields = MetadataModelFilter.get_field_names()


class QCustomizationLiteList(generics.ListAPIView):
    queryset = QModelCustomization.objects.documents()
    serializer_class = QModelCustomizationSerializerLite
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = QModelCustomizationFilter
    filter_fields = QModelCustomizationFilter.get_field_names()
    ordering_fields = ("name", )
    ordering = "name"
