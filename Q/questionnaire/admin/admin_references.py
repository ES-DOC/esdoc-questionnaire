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
.. module:: admin_references

Summary of module goes here

"""

from django.contrib import admin, messages
from Q.questionnaire.models.models_references import QReference


def delete_unused_references(modeladmin, request, queryset):
    for reference in queryset:
        if reference.is_unused:
            reference.delete()
            messages.add_message(request, messages.SUCCESS, "successfully deleted {0}".format(reference))
        else:
            messages.add_message(request, messages.WARNING, "did not delete {0}; it is not unused.".format(reference))
delete_unused_references.short_description = "Delete selected unused {0}".format(QReference._meta.verbose_name_plural.title())


class QReferenceAdmin(admin.ModelAdmin):
    actions = [delete_unused_references]
    readonly_fields = ["is_pending", "is_unused"]

admin.site.register(QReference, QReferenceAdmin)
