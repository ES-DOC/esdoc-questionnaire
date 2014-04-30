
####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Jan 23, 2014 10:19:02 AM"

"""
.. module:: admin_categorizations

Summary of module goes here

"""


from django.forms import *

from django.contrib import admin

from questionnaire.models import MetadataCategorization, MetadataStandardCategoryProxy
from questionnaire.utils  import *
def register_metadata_categorization(modeladmin, request, queryset):
    for categorization in queryset:
        # passing 'request' kwarg in-case I need to pass messages back to the admin
        categorization.register(request=request)
        categorization.save()
register_metadata_categorization.short_description = "Register all of the MetadataCategories belonging to the selected MetadataCategorization."

def unregister_metadata_categorization(modeladmin, request, queryset):
    for categorization in queryset:
        # passing 'request' kwarg in-case I need to pass messages back to the admin
        categorization.unregister(request=request)
        categorization.save()
unregister_metadata_categorization.short_description = "Unregister all of the MetadataCategories belonging to the selected MetadataCategorization."

class MetadataCategorizationAdminForm(ModelForm):
    class Meta:
        model = MetadataCategorization
        fields = ("file","name","registered","standard_category_proxies",)
        readonly_fields = ("registered","standard_category_proxies")

    standard_category_proxies = ModelMultipleChoiceField(label="Categories",required=False,queryset=MetadataStandardCategoryProxy.objects.none())

    def __init__(self,*args,**kwargs):
        super(MetadataCategorizationAdminForm,self).__init__(*args,**kwargs)
        current_standard_category_proxies = self.instance.categories.all()
        self.fields["standard_category_proxies"].queryset = current_standard_category_proxies
        self.fields["standard_category_proxies"].initial  = current_standard_category_proxies
        update_field_widget_attributes(self.fields["standard_category_proxies"],{"disabled":"disabled"})

class MetadataCategorizationAdmin(admin.ModelAdmin):
    readonly_fields  = ("registered",) # standard_category_proxies is set as readonly in the __init__ fn above
    actions          = [register_metadata_categorization,unregister_metadata_categorization]
    form             = MetadataCategorizationAdminForm

admin.site.register(MetadataCategorization,MetadataCategorizationAdmin)
