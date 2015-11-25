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

"""
.. module:: admin_vocabularies

Summary of module goes here

"""

from django.contrib import admin

from django.forms import *

from Q.questionnaire.models.models_vocabularies import QVocabulary
from Q.questionnaire.models.models_proxies import QComponentProxy
from Q.questionnaire.q_utils import update_field_widget_attributes

def register_vocabularies(modeladmin, request, queryset):
    for vocabulary in queryset:
        # passing 'request' kwarg in-case I need to pass messages back to the admin
        vocabulary.register(request=request)
        vocabulary.save()
register_vocabularies.short_description = "Register all of the QComponents belonging to the selected QVocabularies."


class QVocabularyAdminForm(ModelForm):
    class Meta:
        model = QVocabulary
        fields = ("name", "version", "description", "url", "document_type", "file", "is_registered", "component_proxies", )
        readonly_fields = ("is_registered", "component_proxies")

    component_proxies = ModelMultipleChoiceField(
        label="Registered Components",
        required=False,
        queryset=QComponentProxy.objects.none()
    )

    def __init__(self, *args, **kwargs):
        super(QVocabularyAdminForm, self).__init__(*args, **kwargs)
        current_component_proxies = self.instance.component_proxies.all()
        self.fields["component_proxies"].queryset = current_component_proxies
        self.fields["component_proxies"].initial = current_component_proxies
        update_field_widget_attributes(self.fields["component_proxies"], {"disabled": "disabled"})

class QVocabularyAdmin(admin.ModelAdmin):
    readonly_fields = ("is_registered", )  # component_proxies is set as readonly in the __init__ fn above
    actions = [register_vocabularies]
    form = QVocabularyAdminForm

admin.site.register(QVocabulary, QVocabularyAdmin)
