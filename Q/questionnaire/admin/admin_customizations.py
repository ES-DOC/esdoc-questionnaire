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
.. module:: admin_customizations

Summary of module goes here

"""

from django.contrib import admin
from django.forms import ModelForm
from Q.questionnaire.models.models_customizations import QModelCustomization, QCategoryCustomization, QPropertyCustomization
from Q.questionnaire.q_utils import update_field_widget_attributes

# these next few classes let me view all the QPropertyCustomizations and/or QCategoryCustomizations belonging to a given QModelCustomization and/or QCategoryCustomization


class QPropertyCustomizationInlineForm(ModelForm):
    """
    A silly ModelForm for the admin that shows no fields
    It is used in conjunction w/ the StackedInline below
    """
    class Meta:
        model = QPropertyCustomization
        fields = []


class QPropertyCustomizationInline(admin.StackedInline):
    """
    A silly StackedInline which includes a link to the admin of a given QPropertyCustomization
    """
    model = QPropertyCustomization
    form = QPropertyCustomizationInlineForm
    show_change_link = True
    extra = 0


class QCategoryCustomizationInlineForm(ModelForm):
    """
    A silly ModelForm for the admin that shows no fields
    It is used in conjunction w/ the StackedInline below
    """
    class Meta:
        model = QCategoryCustomization
        fields = []


class QCategoryCustomizationInline(admin.StackedInline):
    """
    A silly StackedInline which includes a link to the admin of a given QCategoryCustomization
    """
    model = QCategoryCustomization
    form = QCategoryCustomizationInlineForm
    show_change_link = True
    extra = 0


# now define the actual admins & forms...

class QPropertyCustomizationAdminForm(ModelForm):
    class Meta:
        model = QPropertyCustomization
        fields = [
            "name",
            "project",
            "proxy",
            "model_customization",
            "category_customization",
            "property_title",
            "is_required",
            "is_hidden",
            "is_editable",
            "is_nillable",
            "property_description",
            "inline_help",
            "order",
            "field_type",
            "can_inherit",
            "default_values",
            "atomic_type",
            "atomic_suggestions",
            "enumeration_is_open",
            "relationship_show_subforms",
            # TODO: relationship_target_model_customizations
            # "relationship_target_model_customizations",
        ]


class QPropertyCustomizationAdmin(admin.ModelAdmin):
    """
    Custom ModelAdmin for QPropertyCustomization
    """
    form = QPropertyCustomizationAdminForm


class QCategoryCustomizationAdminForm(ModelForm):
    class Meta:
        model = QCategoryCustomization
        fields = [
            "name",
            "project",
            "proxy",
            "model_customization",
            "order",
            "category_title",
            "category_description",
            "is_hidden",
        ]


class QCategoryCustomizationAdmin(admin.ModelAdmin):
    """
    Custom ModelAdmin for QCategoryCustomization
    Provides an inline form for viewing QPropertyCustomizations
    """
    inlines = (QPropertyCustomizationInline,)
    form = QCategoryCustomizationAdminForm


class QModelCustomizationAdminForm(ModelForm):
    class Meta:
        model = QModelCustomization
        fields = [
            "name",
            "owner",
            "shared_owners",
            "project",
            "proxy",
            "synchronization",
            "order",
            "documentation",
            "is_default",
            "model_title",
            "model_description",
            "model_hierarchy_title",
            "model_show_empty_categories",
        ]


class QModelCustomizationAdmin(admin.ModelAdmin):
    """
    Custom ModelAdmin for QModelCustomization
    Provides an inline form for viewing QPropertyCustomizations
    """
    inlines = (QCategoryCustomizationInline, QPropertyCustomizationInline,)
    form = QModelCustomizationAdminForm


admin.site.register(QModelCustomization, QModelCustomizationAdmin)
admin.site.register(QCategoryCustomization, QCategoryCustomizationAdmin)
admin.site.register(QPropertyCustomization, QPropertyCustomizationAdmin)
