
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
__date__ ="Jan 23, 2014 10:18:54 AM"

"""
.. module:: admin_versions

Summary of module goes here

"""

from django.contrib import admin

from CIM_Questionnaire.questionnaire.models import MetadataModel, MetadataModelSerialization

def serialize_metadata_serializations(modeladmin, request, queryset):
    for serialization in queryset:
        model = serialization.model
        version = serialization.version
        model.serialize(serialization_version=version)
serialize_metadata_serializations.short_description = "Re-serialize the models corresponding to the selected serializations based on their current state."

def write_metadata_serializations(modeladmin, request, queryset):
    for serialization in queryset:
        serialization.write()
write_metadata_serializations.short_description = "Write out the serializations to file."

class MetadataModelSerializationAdmin(admin.ModelAdmin):
    actions = [serialize_metadata_serializations, write_metadata_serializations]

admin.site.register(MetadataModelSerialization, MetadataModelSerializationAdmin)
