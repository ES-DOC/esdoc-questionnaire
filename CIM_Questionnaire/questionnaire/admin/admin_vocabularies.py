
####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Jan 23, 2014 10:18:46 AM"

"""
.. module:: admin_vocabularies

Summary of module goes here

"""

from django.contrib import admin

from questionnaire.models import MetadataVocabulary

def register_metadata_vocabularies(modeladmin, request, queryset):
    for vocabulary in queryset:
        # passing 'request' kwarg in-case I need to pass messages back to the admin
        vocabulary.register(request=request)
        vocabulary.save()
register_metadata_vocabularies.short_description = "Register all of the MetadataProperties belonging to the selected MetadataVocabularies."

def unregister_metadata_vocabularies(modeladmin, request, queryset):
    for vocabulary in queryset:
        # passing 'request' kwarg in-case I need to pass messages back to the admin
        vocabulary.unregister(request=request)
        vocabulary.save()
unregister_metadata_vocabularies.short_description = "Unregister all of the MetadataProperties belonging to the selected MetadataVocabularies."

class MetadataVocabularyAdmin(admin.ModelAdmin):
    readonly_fields  = ("registered",)
    actions          = [register_metadata_vocabularies,unregister_metadata_vocabularies]

admin.site.register(MetadataVocabulary,MetadataVocabularyAdmin)
