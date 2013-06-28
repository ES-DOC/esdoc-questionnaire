
####################
#   Django-CIM-Forms
#   Copyright (c) 2012 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Jan 31, 2013 11:27:48 AM"

"""
.. module:: admin

Summary of module goes here

"""

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import ModelForm


from dcf.models import *

def register_metadata_versions(modeladmin, request, queryset):
    """

    This admin function (re)loads all of the :class:`dcf.models.MetadataModel`s into a :class:`dcf.models.MetadataVersion`.
    For each version in the queryset, it checks all models in the same application.
    If a model is a subclass of :class:`dcf.models.MetadataModel`, it adds that model's name to the list of model_names stored by the :class:`dcf.models.MetadataVersion`.

    .. note:: During a MetadataVersion's :func:`dcf.models.MetadataVersion.__init__` function, that list of names is used to create a dictionary of the actual model classes themselves.

    .. warning:: This function should never be called directly; it is accessible only via the Django Admin.

    """

    for version in queryset:
        version.register()
        version.save()

register_metadata_versions.short_description = "Register all of the MetadataModels belonging to the selected MetadataVersions."


class MetadataVersionAdmin(admin.ModelAdmin):
    """
    Custom Django Admin class for MetadataVersions.

    .. warning:: This class should never be accessed directly; it is used only by the Django Admin.

    """
    actions = [register_metadata_versions]

def register_metadata_categorizations(modeladmin, request, queryset):
    for categorization in queryset:
        categorization.register()
        #categorization.save()

register_metadata_categorizations.short_description = "Register all of the MetadataCategories belonging to the selected Metadata Categorization."

class MetadataCategorizationAdmin(admin.ModelAdmin):
    """
    Custom Django Admin class for MetadataCategorizations.

    .. warning:: This class should never be accessed directly; it is used only by the Django Admin.

    """
    actions = [register_metadata_categorizations]


def register_metadata_vocabularies(modeladmin, request, queryset):
    for vocabulary in queryset:
        vocabulary.register()
        #vocabulary.save()

register_metadata_vocabularies.short_description = "Register all of the MetadataProperties belonging to the selected Metadata Vocabulary."

class MetadataVocabularyAdmin(admin.ModelAdmin):
    """
    Custom Django Admin class for MetadataVocabularies.

    .. warning:: This class should never be accessed directly; it is used only by the Django Admin.

    """
    actions = [register_metadata_vocabularies]



###############################################################
# here are the actual classes that DjangoAdmin has access to  #
###############################################################

admin.site.register(MetadataVersion,MetadataVersionAdmin)
admin.site.register(MetadataCategorization,MetadataCategorizationAdmin)
admin.site.register(MetadataVocabulary,MetadataVocabularyAdmin)
admin.site.register(MetadataProject)

# TODO: REMOVE AFTER DEBUGGING...
#admin.site.register(MetadataStandardCategory)
#admin.site.register(MetadataScientificCategory)
#admin.site.register(MetadataModelCustomizer)
#admin.site.register(MetadataStandardPropertyCustomizer)
#admin.site.register(MetadataScientificPropertyCustomizer)
#admin.site.register(MetadataStandardPropertyProxy)
#admin.site.register(MetadataScientificPropertyProxy)
#admin.site.register(MetadataProperty)
