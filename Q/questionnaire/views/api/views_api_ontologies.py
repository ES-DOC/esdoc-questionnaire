####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from rest_framework import generics, filters
import django_filters

from Q.questionnaire.models.models_ontologies import QOntology, QOntologyTypes
from Q.questionnaire.serializers.serializers_ontologies import QOntologySerializer
from Q.questionnaire.views.api.views_api_base import BetterBooleanFilter


class QOntologyFilter(django_filters.FilterSet):

    class Meta:
        model = QOntology
        fields = [
            "id",
            "created",
            "modified",
            "name",
            "version",
            "documentation",
            "url",
            "is_registered",
            'is_active',
            # "ontology_type",  # ontology_type is not listed here b/c it is explicitly defined below
            # "key",  # key is not listed here b/c it is a property and not a field
        ]

    ontology_type = django_filters.ChoiceFilter(choices=[(ot.get_type(), ot.get_name()) for ot in QOntologyTypes])

    is_registered = BetterBooleanFilter(name="is_registered")
    is_active = BetterBooleanFilter(name="is_active")
    project = django_filters.MethodFilter(action='filter_project')

    def filter_project(self, queryset, value):
        # returns all QOntologies that are supported by a given QProject (specified by pk)
        return queryset.filter(qproject__in=[value])

    @classmethod
    def get_field_names(cls):
        """
        Simple way to make sure that _all_ filtered fields
        are available to the views below
        """
        return tuple(cls.Meta.fields)


class QOntologyList(generics.ListAPIView):

    serializer_class = QOntologySerializer
    filter_class = QOntologyFilter
    filter_backends = [filters.DjangoFilterBackend]
    filter_fields = QOntologyFilter.get_field_names()

    def get_queryset(self):
        # 'key' is a property, so I can't order by that
        # so I explicitly order by 'name' & 'version' (which comprise the key anyway)
        return QOntology.objects.order_by("name", "version")
