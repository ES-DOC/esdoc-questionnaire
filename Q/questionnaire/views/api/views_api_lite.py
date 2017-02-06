####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.http import Http404
from rest_framework import generics, filters, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from Q.questionnaire.models.models_customizations import QModelCustomization
from Q.questionnaire.models.models_projects import QProject
from Q.questionnaire.models.models_realizations import QModelRealization
from Q.questionnaire.serializers.serializers_lite import QProjectSerializerLite, QModelCustomizationSerializerLite, QModelRealizationSerializerLite
from Q.questionnaire.views.api.views_api_customizations import QModelCustomizationFilter
from Q.questionnaire.views.api.views_api_realizations import QModelRealizationFilter


class QProjectLitePermission(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # anybody can submit GET, HEAD, or OPTIONS requests
        if request.method in permissions.SAFE_METHODS:
            return True
        # nobody can submit PUT, POST, or DELETE requests
        # (this is the "lite" serialization, after all)
        return False


class QProjectLiteDetail(APIView):
    """
    Retrieve, update or delete a model instance.
    """

    permission_classes = [QProjectLitePermission]

    def get_object(self, pk):

        try:
            return QProject.objects.get(pk=pk)
        except QProject.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        model = self.get_object(pk)
        serializer = QProjectSerializerLite(model, context={"request": request})
        return Response(serializer.data)


class QProjectLiteList(generics.ListAPIView):
    queryset = QProject.objects.active_projects()
    serializer_class = QProjectSerializerLite


class QCustomizationLiteList(generics.ListAPIView):
    queryset = QModelCustomization.objects.documents()
    serializer_class = QModelCustomizationSerializerLite
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = QModelCustomizationFilter
    filter_fields = QModelCustomizationFilter.get_field_names()
    ordering_fields = ("name", )
    ordering = "name"


class QRealizationLiteList(generics.ListAPIView):
    queryset = QModelRealization.objects.root_documents()
    serializer_class = QModelRealizationSerializerLite
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = QModelRealizationFilter
    filter_fields = QModelRealizationFilter.get_field_names()
