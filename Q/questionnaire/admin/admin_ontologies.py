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

"""
.. module:: admin_ontologies

Summary of module goes here

"""

from django.contrib import admin

from django.forms import *

from Q.questionnaire.models.models_ontologies import QOntology
from Q.questionnaire.models.models_proxies import QModelProxy
from Q.questionnaire.q_utils import update_field_widget_attributes

def register_ontologies(modeladmin, request, queryset):
    for ontology in queryset:
        # passing 'request' kwarg in-case I need to pass messages back to the admin
        ontology.register(request=request)
        ontology.save()
register_ontologies.short_description = "Register all of the QModels belonging to the selected QOntologies."


class QOntologyAdminForm(ModelForm):
    class Meta:
        model = QOntology

        fields = ("name", "version", "type", "description", "url", "file", "categorization", "is_registered", "model_proxies", )
        readonly_fields = ("is_registered", "model_proxies")

    model_proxies = ModelMultipleChoiceField(
        label="Registered Models",
        required=False,
        queryset=QModelProxy.objects.none()
    )

    def __init__(self, *args, **kwargs):
        super(QOntologyAdminForm,self).__init__(*args, **kwargs)
        current_model_proxies = self.instance.model_proxies.all()
        self.fields["model_proxies"].queryset = current_model_proxies
        self.fields["model_proxies"].initial = current_model_proxies
        update_field_widget_attributes(self.fields["model_proxies"], {"disabled": "disabled"})

class QOntologyAdmin(admin.ModelAdmin):
    readonly_fields = ("is_registered", )  # model_proxies is set as readonly in the __init__ fn above
    actions = [register_ontologies]
    form = QOntologyAdminForm

admin.site.register(QOntology, QOntologyAdmin)
