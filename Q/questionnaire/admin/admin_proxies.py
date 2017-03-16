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
.. module:: admin_proxies

Summary of module goes here

"""

from django.contrib import admin
from django.forms import ModelForm
from Q.questionnaire.models.models_proxies import QModelProxy, QCategoryProxy, QPropertyProxy


# these next 2 classes let me view all the QPropertyProxies belonging to a given QModelProxy or QCategoryProxy

class QPropertyProxyInlineForm(ModelForm):
    """
    A silly ModelForm for the admin that shows no fields
    It is used in conjunction w/ the StackedInline below
    """
    class Meta:
        model = QPropertyProxy
        fields = []


class QPropertyProxyInline(admin.StackedInline):
    """
    A silly StackedInline which includes a link to the admin of a given QPropertyProxy
    """
    model = QPropertyProxy
    form = QPropertyProxyInlineForm
    verbose_name_plural = "properties:"
    show_change_link = True
    extra = 0


# these next 2 classes let me view all the QCategoryProxies belonging to a given QModelProxy

class QCategoryProxyInlineForm(ModelForm):
    """
    A silly ModelForm for the admin that shows no fields
    It is used in conjunction w/ the StackedInline below
    """
    class Meta:
        model = QCategoryProxy
        fields = []


class QCategoryProxyInline(admin.StackedInline):
    """
    A silly StackedInline which includes a link to the admin of a given QCategoryProxy
    """
    model = QCategoryProxy
    form = QCategoryProxyInlineForm
    show_change_link = True
    extra = 0


class QModelProxyAdminForm(ModelForm):
    class Meta:
        model = QModelProxy
        fields = [
            "cim_id",
            "name",
            "package",
            "documentation",
            "ontology",
            "order",
            "is_meta",
            "is_document",
            "label",
        ]


class QModelProxyAdmin(admin.ModelAdmin):
    """
    Custom ModelAdmin for QModelProxy
    Provides an inline form for viewing QPropertyProxies & QCategoryProxies
    """
    inlines = [QCategoryProxyInline, QPropertyProxyInline]
    form = QModelProxyAdminForm


class QCategoryProxyAdminForm(ModelForm):
    class Meta:
        model = QCategoryProxy
        fields = [
            "cim_id",
            "name",
            "documentation",
            "model_proxy",
            "order",
            "is_meta",
            "is_uncategorized",
        ]


class QCategoryProxyAdmin(admin.ModelAdmin):
    """
    Custom ModelAdmin for QCategoryProxy
    Provides an inline form for viewing QPropertyProxies
    """
    inlines = [QPropertyProxyInline]
    form = QCategoryProxyAdminForm
    readonly_fields = ("is_uncategorized",)


class QPropertyProxyAdminForm(ModelForm):
    class Meta:
        model = QPropertyProxy
        fields = [
            "cim_id",
            "name",
            "documentation",
            "order",
            "model_proxy",
            "is_hierarchical",
            "is_meta",
            "category_proxy",
            "is_nillable",
            "cardinality_min",
            "cardinality_max",
            "field_type",
            "atomic_type",
            "enumeration_is_open",
            "enumeration_choices",
            "relationship_target_names",
            "relationship_target_models",
            "values",
        ]


class QPropertyProxyAdmin(admin.ModelAdmin):
    """
    Custom ModelAdmin for QCategoryProxy
    """
    form = QPropertyProxyAdminForm


admin.site.register(QModelProxy, QModelProxyAdmin)
admin.site.register(QCategoryProxy, QCategoryProxyAdmin)
admin.site.register(QPropertyProxy, QPropertyProxyAdmin)
