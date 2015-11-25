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


from django.http import Http404

from rest_framework import generics, filters, renderers, viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
import django_filters

from Q.questionnaire.models.models_realizations import QModel, QStandardProperty
from Q.questionnaire.serializers.serializers_realizations import QModelSerializer, QStandardPropertySerializer
from Q.questionnaire.views.api.views_api_base import BetterBooleanFilter


# I am purposefully NOT using the full power of class-based-views
# b/c I want finer control over how validation, etc. works
# so I explicitly define each endpoint below...


class QModelFilter(django_filters.FilterSet):

    class Meta:
        model = QModel
        fields = [
            "id", "created", "modified", "name", "version",
            "description", "ontology", "proxy", "project",
            "is_complete", "is_document", "is_root", "is_published",
            "is_active", "parent",
        ]

    is_document = BetterBooleanFilter(name="is_document")
    is_root = BetterBooleanFilter(name="is_root")
    is_published = BetterBooleanFilter(name="is_published")
    is_active = BetterBooleanFilter(name="is_active")
    is_complete = BetterBooleanFilter(name="is_active")

    @classmethod
    def get_field_names(cls):
        """
        Simple way to make sure that _all_ filtered fields
        are available to the views below
        """
        return tuple(cls.Meta.fields)


########################################
# these views are for the project page #
########################################


class QModelList(APIView):
    """
    List models, or create a new model.
    """
    def get(self, request, format=None):
        models = QModel.objects.all()
        serializer = QModelSerializer(models, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request, format=None):
        model = QModelSerializer(data=request.data, context={"request": request})
        if model.is_valid():
            model.save()
            return Response(model.data, status=status.HTTP_201_CREATED)
        else:
            return Response(model.errors, status=status.HTTP_400_BAD_REQUEST)


class QModelDetail(APIView):
    """
    Retrieve, update or delete a model instance.
    """
    def get_object(self, pk):
        try:
            return QModel.objects.get(pk=pk)
        except QModel.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        model = self.get_object(pk)
        serializer = QModelSerializer(model, context={"request": request})
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        model = self.get_object(pk)
        serializer = QModelSerializer(model, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        model = self.get_object(pk)
        model.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class QStandardPropertyList(APIView):
    """
    List models, or create a new standard_property.
    """
    def get(self, request, format=None):
        standard_properties = QStandardProperty.objects.all()
        serializer = QStandardPropertySerializer(standard_properties, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request, format=None):
        standard_property = QStandardPropertySerializer(data=request.data, context={"request": request})
        if standard_property.is_valid():
            standard_property.save()
            return Response(standard_property.data, status=status.HTTP_201_CREATED)
        else:
            return Response(standard_property.errors, status=status.HTTP_400_BAD_REQUEST)


class QStandardPropertyDetail(APIView):
    """
    Retrieve, update or delete a model instance.
    """
    def get_object(self, pk):
        try:
            return QStandardProperty.objects.get(pk=pk)
        except QStandardProperty.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        standard_property = self.get_object(pk)
        serializer = QStandardPropertySerializer(standard_property, context={"request": request})
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        standard_property = self.get_object(pk)
        serializer = QStandardPropertySerializer(standard_property, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        standard_property = self.get_object(pk)
        standard_property.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
