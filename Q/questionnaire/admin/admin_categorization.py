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
.. module:: admin_categorization

Summary of module goes here

"""

from django.contrib import admin

from django.forms import *

from Q.questionnaire.models.models_categorizations import QCategorization
from Q.questionnaire.models.models_proxies import QStandardCategoryProxy
from Q.questionnaire.q_utils import update_field_widget_attributes

def register_categorizations(modeladmin, request, queryset):
    for categorization in queryset:
        # passing 'request' kwarg in-case I need to pass messages back to the admin
        categorization.register(request=request)
        categorization.save()
register_categorizations.short_description = "Register all of the QCategories belonging to the selected QCategorization."


class QCategorizationAdminForm(ModelForm):
    class Meta:
        model = QCategorization

        fields = ("name", "version", "description", "file", "is_registered", "category_proxies", )
        readonly_fields = ("is_registered", "category_proxies")

    category_proxies = ModelMultipleChoiceField(label="QCategories", required=False, queryset=QStandardCategoryProxy.objects.none())

    def __init__(self, *args, **kwargs):
        super(QCategorizationAdminForm,self).__init__(*args, **kwargs)
        current_category_proxies = self.instance.category_proxies.all()
        self.fields["category_proxies"].queryset = current_category_proxies
        self.fields["category_proxies"].initial = current_category_proxies
        update_field_widget_attributes(self.fields["category_proxies"], {"disabled": "disabled"})

class QCategorizationAdmin(admin.ModelAdmin):
    readonly_fields = ("is_registered", )  # category_proxies is set as readonly in the __init__ fn above
    actions = [register_categorizations]
    form = QCategorizationAdminForm

admin.site.register(QCategorization, QCategorizationAdmin)
