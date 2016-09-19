####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

"""
.. module:: admin_projects

Summary of module goes here

"""

from django.contrib import admin
from django.forms import ModelForm
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from PIL import Image
import os

from Q.questionnaire.models.models_projects import QProject, QProjectOntology

class QProjectAdminForm(ModelForm):
    class Meta:
        model = QProject
        fields = [
            "name",
            "title",
            "description",
            "email",
            "url",
            "logo",
            "display_logo",
            "authenticated",
            "is_active",
            "is_displayed",
            # "ontologies",
        ]

    def clean(self):
        logo = self.cleaned_data.get("logo")
        display_logo = self.cleaned_data.get("display_logo")
        if display_logo and not logo:
            msg = "You must provide a logo if you set display_logo to true."
            raise ValidationError(msg)

    def save(self, commit=True):
        project = super(QProjectAdminForm, self).save(commit)
        if project.logo:
            # force resizing of the logo...
            logo = Image.open(project.logo.file)
            logo = logo.resize(QProject.LOGO_SIZE, Image.ANTIALIAS)
            logo_path = os.path.join(
                settings.MEDIA_ROOT,
                project.logo.field.upload_to(project, project.logo.name)
            )
            logo_dir = os.path.dirname(logo_path)
            if not os.path.exists(logo_dir):
                os.makedirs(logo_dir)
            logo.save(logo_path)
            # (the fact that this uses OverwriteStorage means that a new filename will not be created)
            project.logo.save(os.path.basename(logo_path), File(open(logo_path), "rb"))

        return project

class QProjectOntologyInline(admin.TabularInline):
    model = QProjectOntology
    extra = 1

class QrojectAdmin(admin.ModelAdmin):
    """
    Custom ModelAdmin for QProjects
    Provides an inline form for adding QProjectOntologies
    """
    inlines = (QProjectOntologyInline,)
    form = QProjectAdminForm

admin.site.register(QProject, QrojectAdmin)
