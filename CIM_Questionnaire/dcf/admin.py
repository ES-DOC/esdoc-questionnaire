
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


def update_metadata_modelcustomizers(modeladmin, request, queryset):
    for customizer in queryset:
        customizer.updateScientificProperties()
        #customizer.save()

update_metadata_modelcustomizers.short_description = "Updates an existing MetadataModelCustomizer with any missing (scientific) property customizers."

class MetadataModelCustomizerAdmin(admin.ModelAdmin):
    """
    Custom Django Admin class for MetadataModelCustomizers.

    .. warning:: This class should never be accessed directly; it is used only by the Django Admin.

    """
    actions = [update_metadata_modelcustomizers]

###############################################################
# here are the actual classes that DjangoAdmin has access to  #
###############################################################

admin.site.register(MetadataVersion,MetadataVersionAdmin)
admin.site.register(MetadataCategorization,MetadataCategorizationAdmin)
admin.site.register(MetadataVocabulary,MetadataVocabularyAdmin)
admin.site.register(MetadataProject)

admin.site.register(MetadataModelCustomizer,MetadataModelCustomizerAdmin)

from django.db.models import Q

from django.contrib.sites.models import Site

from dcf.models import MetadataSite

class MetadataSiteAdminForm(ModelForm):
    class Meta:
        model = Site

    def clean(self):
        cleaned_data = super(MetadataSiteAdminForm, self).clean()
        site = self.instance
        existing_sites = Site.objects.filter(Q(name=cleaned_data["name"]) | Q(domain=cleaned_data["domain"])).exclude(pk=site.pk)
        if existing_sites:
            msg = "Sites must have unique names and domains."
            raise forms.ValidationError(msg)
        return cleaned_data

class MetadataSiteInline(admin.StackedInline):
    model = MetadataSite
    can_delete = False

class MetadataSiteAdmin(admin.ModelAdmin):

    inlines = (MetadataSiteInline, )
    form    = MetadataSiteAdminForm

admin.site.unregister(Site)
admin.site.register(Site, MetadataSiteAdmin)



from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from dcf.models import MetadataUser

class MetadataUserInline(admin.StackedInline):
    model = MetadataUser
    can_delete = False

class MetadataAdmin(UserAdmin):
    inlines = (MetadataUserInline, )

    # this took a while to figure out...
    # I want to update the group membership of a user based on which projects they belong to, but...
    # 1) the save method on metadata_user gets called before the save_m2m method of the inlineform here (so the contents of 'projects' would be invalid)
    # 2) there is a known Django bug in the m2m_changed signal
    # so I do it here after save_m2m has been called
    # (see models/metadata_authentication.py for more info)
    def save_formset(self,request,form,formset,change):
        try:
            # since this is based off a one-to-one field, there will only ever be a single form in the formset
            metadata_user = formset.save(commit=False)[0]
        except IndexError:
            # ...except for the case where the admin has not yet been assocated w/ a metadata_user
            return
        metadata_user.save()
        old_projects = set(metadata_user.projects.all())
        formset.save_m2m()
        new_projects = set(metadata_user.projects.all())

        for project in old_projects.difference(new_projects):
            metadata_user.leave_project(project)
        for project in new_projects.difference(old_projects):
            metadata_user.join_project(project)

admin.site.unregister(User)
admin.site.register(User, MetadataAdmin)


# TODO: REMOVE AFTER DEBUGGING...
#admin.site.register(MetadataStandardCategory)
#admin.site.register(MetadataScientificCategory)
#admin.site.register(MetadataStandardPropertyCustomizer)
admin.site.register(MetadataScientificPropertyCustomizer)
#admin.site.register(MetadataStandardPropertyProxy)
#admin.site.register(MetadataScientificPropertyProxy)
#admin.site.register(MetadataProperty)
