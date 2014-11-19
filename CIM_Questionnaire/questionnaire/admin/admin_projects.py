
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
__date__ ="Jan 23, 2014 10:21:47 AM"

"""
.. module:: admin_projects

Summary of module goes here

"""

from django.contrib import admin
from CIM_Questionnaire.questionnaire.models.metadata_project import MetadataProject, MetadataProjectVocabulary


class MetadataProjectVocabularyInline(admin.TabularInline):
    model = MetadataProjectVocabulary
    extra = 1

class MetadataProjectAdmin(admin.ModelAdmin):
    inlines = (MetadataProjectVocabularyInline,)

admin.site.register(MetadataProject, MetadataProjectAdmin)
