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


from django.http import Http404

from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
import django_filters

from Q.questionnaire.models.models_ontologies import QOntology
from Q.questionnaire.serializers.serializers_ontologies import QOntologySerializer
from Q.questionnaire.views.api.views_api_base import BetterBooleanFilter


class QOntologyFilter(django_filters.FilterSet):

    class Meta:
        model = QOntology
        fields = [
            "id", "created", "modified", "name", "version",
            "description", "type", "key", "url", "file",
            "categorization", "is_registered",
        ]

    is_registered = BetterBooleanFilter(name="is_registered")

    @classmethod
    def get_field_names(cls):
        """
        Simple way to make sure that _all_ filtered fields
        are available to the views below
        """
        return tuple(cls.Meta.fields)


class QOntologyList(generics.ListAPIView):
    queryset = QOntology.objects.all()
    serializer_class = QOntologySerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = QOntologyFilter
    filter_fields = QOntologyFilter.get_field_names()
    ordering_fields = QOntologyFilter.get_field_names()
    ordering = "key"

