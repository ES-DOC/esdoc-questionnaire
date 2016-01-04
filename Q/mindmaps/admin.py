####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"

from django.contrib import admin

from .models import MindMapSource, MindMapDomain

class MindMapDomainAdmin(admin.TabularInline):
    model = MindMapDomain

class MindMapSourceAdmin(admin.ModelAdmin):
    inlines = (MindMapDomainAdmin, )

admin.site.register(MindMapSource, MindMapSourceAdmin)
