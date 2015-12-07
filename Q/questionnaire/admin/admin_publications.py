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
.. module:: admin_publications

Summary of module goes here

"""

from django.contrib import admin

from Q.questionnaire.models.models_publications import QPublication

def republish_publications(modeladmin, request, queryset):
    for publication in queryset:
        model = publication.model
        # TODO: ONCE I CHANGE FROM "models_realzations_bak" TO "models_realizations"
        # TODO: I WILL HAVE TO CHANGE THIS TO USE "publish" RATHER THAN "serialize"
        # model.publish(force_save=False)
        model.serialize(serialization_version=publication.version)
republish_publications.short_description = "republish the models corresponding to the selected publications based on their current status."


def write_publications(modeladmin, request, queryset):
    for publication in queryset:
        publication.write()
write_publications.short_description = "Write out the publications to file."


class QPublicationAdmin(admin.ModelAdmin):
    actions = [republish_publications, write_publications]

admin.site.register(QPublication, QPublicationAdmin)
