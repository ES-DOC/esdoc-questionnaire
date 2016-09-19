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

from Q.questionnaire.models.models_realizations import QModel
from Q.questionnaire.models.models_customizations import QModelCustomization
from Q.questionnaire.serializers.serializers_lite import QModelCustomizationSerializerLite, QModelRealizationSerializerLite
from Q.questionnaire.views.api.views_api_realizations import QModelRealizationFilter
from Q.questionnaire.views.api.views_api_customizations import QModelCustomizationFilter


class QRealizationLiteList(generics.ListAPIView):
    queryset = QModel.objects.root_documents()
    serializer_class = QModelRealizationSerializerLite
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = QModelRealizationFilter
    filter_fields = QModelRealizationFilter.get_field_names()


class QCustomizationLiteList(generics.ListAPIView):
    queryset = QModelCustomization.objects.documents()
    serializer_class = QModelCustomizationSerializerLite
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = QModelCustomizationFilter
    filter_fields = QModelCustomizationFilter.get_field_names()
    ordering_fields = ("name", )
    ordering = "name"
