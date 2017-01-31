####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

"""
.. module:: admin_publications

Summary of module goes here

"""

from django.contrib import admin, messages
from Q.questionnaire.models.models_publications import QPublication


def republish_publications(modeladmin, request, queryset):
    for publication in queryset:
        model = publication.model
        try:
            model.publish(force_save=False)
            messages.add_message(request, messages.SUCCESS, "successfully republished {0}".format(publication))
        except:
            messages.add_message(request, messages.ERROR, "error republishing {0}".format(publication))
republish_publications.short_description = "Republish the models corresponding to the selected publications based on their current status."


def write_publications(modeladmin, request, queryset):
    for publication in queryset:
        try:
            publication.write()
            messages.add_message(request, messages.SUCCESS, "successfully wrote {0}".format(publication.get_file_path()))
        except:
            messages.add_message(request, messages.ERROR, "error writing {0}".format(publication.get_file_path()))
write_publications.short_description = "Write out the publications to file."


class QPublicationAdmin(admin.ModelAdmin):
    actions = [republish_publications, write_publications]

admin.site.register(QPublication, QPublicationAdmin)
