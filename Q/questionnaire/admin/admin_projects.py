####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

"""
.. module:: admin_projects

Summary of module goes here

"""

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.files import File
from django.forms import ModelForm, ChoiceField
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
            "order",
            "email",
            "url",
            "logo",
            "display_logo",
            "authenticated",
            "is_active",
            "is_displayed",
            "is_legacy",
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


class QProjectChangeForm(ModelForm):
    """
    This form is used on the "change" template rather than the "detail" template;
    I customize it only to change the widget used by the "order" field;
    See "QProjectAdmin.get_changelist_form()" below.
    """
    class Meta:
        model = QProject
        fields = [
            "name",
            "order",
        ]

    def __init__(self, *args, **kwargs):
        super(QProjectChangeForm, self).__init__(*args, **kwargs)
        self.fields["order"] = ChoiceField(
            choices=[(i, str(i)) for i in range(QProject.objects.count())],
        )


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
    list_display = ("__str__", "order",)
    list_editable = ("order",)
    readonly_fields = ("order",)

    def get_changelist_form(self, request, **kwargs):
        return QProjectChangeForm


admin.site.register(QProject, QrojectAdmin)
