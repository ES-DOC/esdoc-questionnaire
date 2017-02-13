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
.. module:: admin_realizations

Summary of module goes here

"""

from django.contrib import admin
from django.forms import ModelForm
from Q.questionnaire.models.models_realizations import QModelRealization, QCategoryRealization, QPropertyRealization

# these next few classes let me view all the QPropertyRealizations and/or QCategoryRealizaions belonging to a given QModelRealization and/or QCategoryRealization


class QPropertyRealizationInlineForm(ModelForm):
    """
    A silly ModelForm for the admin that shows no fields
    It is used in conjunction w/ the StackedInline below
    """
    class Meta:
        model = QPropertyRealization
        fields = []


class QPropertyRealizationInline(admin.StackedInline):
    """
    A silly StackedInline which includes a link to the admin of a given QPropertyRealization
    """
    model = QPropertyRealization
    form = QPropertyRealizationInlineForm
    verbose_name_plural = "properties:"
    can_delete = False
    show_change_link = True
    max_num = 0
    extra = 0


class QCategoryRealizationInlineForm(ModelForm):
    """
    A silly ModelForm for the admin that shows no fields
    It is used in conjunction w/ the StackedInline below
    """
    class Meta:
        model = QCategoryRealization
        fields = []


class QCategoryRealizationInline(admin.StackedInline):
    """
    A silly StackedInline which includes a link to the admin of a given QCategoryRealization
    """
    model = QCategoryRealization
    form = QCategoryRealizationInlineForm
    verbose_name_plural = "categories:"
    can_delete = False
    show_change_link = True
    max_num = 0
    extra = 0


class QModelRealizationInlineForm(ModelForm):
    """
    A silly ModelForm for the admin that shows no fields
    It is used in conjunction w/ the StackedInline below
    """
    class Meta:
        model = QModelRealization
        fields = []


class QModelRealizationInline(admin.StackedInline):
    """
    A silly StackedInline which includes a link to the admin of a given QModelRealization
    """
    model = QModelRealization
    form = QModelRealizationInlineForm
    verbose_name_plural = "relationship_values:"
    can_delete = False
    show_change_link = True
    max_num = 0
    extra = 0

# now define the actual admins & forms...

class QPropertyRealizationAdminForm(ModelForm):
    class Meta:
        model = QPropertyRealization
        fields = [
            "proxy",
            "model",
            "category",
            "order",
            "field_type",
            "atomic_value",
            "enumeration_value",
            "enumeration_other_value",
            # "relationship_values",
            "relationship_references",
            "is_complete",
        ]


class QPropertyRealizationAdmin(admin.ModelAdmin):
    """
    Custom ModelAdmin for QPropertyRealization
    """
    inlines = (QModelRealizationInline,)
    form = QPropertyRealizationAdminForm
    readonly_fields = ("is_complete",)


class QCategoryRealizationAdminForm(ModelForm):
    class Meta:
        model = QCategoryRealization
        fields = [
            "proxy",
            "model",
            "order",
            "category_value",
            "is_complete",
        ]


class QCategoryRealizationAdmin(admin.ModelAdmin):
    """
    Custom ModelAdmin for QCategoryRealization
    Provides an inline form for viewing QPropertyRealizations
    """
    inlines = (QPropertyRealizationInline,)
    form = QCategoryRealizationAdminForm
    readonly_fields = ("is_complete",)


class QModelRealizationAdminForm(ModelForm):
    class Meta:
        model = QModelRealization
        fields = [
            "owner",
            "shared_owners",
            "project",
            "proxy",
            "synchronization",
            "is_root",
            "is_published",
            "is_active",
            "is_complete",
        ]


class QModelRealizationAdmin(admin.ModelAdmin):
    """
    Custom ModelAdmin for QModelRealization
    Provides an inline form for viewing QPropertyRealizations
    """
    inlines = (QCategoryRealizationInline, QPropertyRealizationInline)
    # readonly_fields = ("is_published", "is_complete",)
    form = QModelRealizationAdminForm


admin.site.register(QModelRealization, QModelRealizationAdmin)
admin.site.register(QCategoryRealization, QCategoryRealizationAdmin)
admin.site.register(QPropertyRealization, QPropertyRealizationAdmin)
