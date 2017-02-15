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

from rest_framework import status
from rest_framework.response import Response
from rest_framework import generics, filters
from rest_framework.views import APIView
import django_filters

from Q.questionnaire.models.models_projects import QProject
from Q.questionnaire.serializers.serializers_projects import QProjectSerializer, QProjectTestSerializer
from Q.questionnaire.views.api.views_api_base import BetterBooleanFilter


class QProjectFilter(django_filters.FilterSet):

    class Meta:
        model = QProject
        fields = ['name', 'is_active', 'is_displayed', 'is_legacy']

    is_active = BetterBooleanFilter(name="is_active")
    is_displayed = BetterBooleanFilter(name="is_displayed")
    is_legacy = BetterBooleanFilter(name="is_legacy")


class QProjectList(generics.ListAPIView):
    queryset = QProject.objects.all()
    serializer_class = QProjectSerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_fields = ('name', 'is_active', 'is_displayed', "is_legacy")
    filter_class = QProjectFilter
    ordering_fields = ('name', 'title')
    ordering = "name"


class QProjectDetail(APIView):
    """
    Retrieve, update or delete a model instance.
    """

    def get_object(self, pk):
        try:
            return QProject.objects.get(pk=pk)
        except QProject.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        model = self.get_object(pk)
        serializer = QProjectSerializer(model, context={"request": request})
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        project = self.get_object(pk)
        serializer = QProjectSerializer(project, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        project = self.get_object(pk)
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class QProjectTestDetail(QProjectDetail):

    def get(self, request, pk, format=None):
        model = self.get_object(pk)
        serializer = QProjectTestSerializer(model, context={"request": request})
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        project = self.get_object(pk)
        serializer = QProjectTestSerializer(project, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
