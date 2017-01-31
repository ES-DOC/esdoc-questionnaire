####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

"""
.. module:: admin_ontologies

Summary of module goes here

"""

from django.contrib import admin
from django.forms import *

from Q.questionnaire.models.models_ontologies import QOntology
from Q.questionnaire.models.models_proxies import QModelProxy


# these next 2 classes allow me to view all of the QProxyModels belonging to a given QOntology in the admin

class QModelProxyInlineForm(ModelForm):
    """
    A silly ModelForm for the admin that shows no fields
    It is used in conjunction w/ the StackedInline below
    """
    class Meta:
        model = QModelProxy
        fields = []


class QModelProxyInline(admin.StackedInline):
    """
    A silly StackedInline which includes a link to the admin of a given QProxyProperty
    """
    model = QModelProxy
    form = QModelProxyInlineForm
    show_change_link = True
    extra = 0


def register_ontologies(modeladmin, request, queryset):
    for ontology in queryset:
        # passing 'request' kwarg in-case I need to pass messages back to the admin
        ontology.register(request=request)
        ontology.save()
register_ontologies.short_description = "Register all of the QProxies belonging to the Questionnaire Ontology."


class QOntologyAdminForm(ModelForm):
    class Meta:
        model = QOntology

        fields = (
            # "created",
            # "modified",
            "name",
            "version",
            "documentation",
            "ontology_type",
            "parent",
            "url",
            "file",
            "is_registered",
            "is_active",
        )


class QOntologyAdmin(admin.ModelAdmin):
    readonly_fields = ("is_registered", "key", "created", "modified",)
    inlines = (QModelProxyInline,)
    actions = [register_ontologies]
    form = QOntologyAdminForm

admin.site.register(QOntology, QOntologyAdmin)
