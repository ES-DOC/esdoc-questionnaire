
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
__date__ ="Jan 23, 2014 10:18:54 AM"

"""
.. module:: admin_versions

Summary of module goes here

"""

from django.contrib import admin

from django.forms import *

from questionnaire.models import MetadataVersion, MetadataModelProxy
from questionnaire.utils import *

def register_metadata_versions(modeladmin, request, queryset):
    for version in queryset:
        # passing 'request' kwarg in-case I need to pass messages back to the admin
        version.register(request=request)
        version.save()
register_metadata_versions.short_description = "Register all of the MetadataModels belonging to the selected MetadataVersions."

def unregister_metadata_versions(modeladmin, request, queryset):
    for version in queryset:
        # passing 'request' kwarg in-case I need to pass messages back to the admin
        version.unregister(request=request)
        version.save()
unregister_metadata_versions.short_description = "Unregister all of the MetadataModels belonging to the selected MetadataVersions."

# WAS DISPLAYING RELATED MODELPROXIES INLINE LIKE THIS...
#class MetadataVersionInline(admin.TabularInline):
#    model = MetadataModelProxy
#    def has_delete_permission(self, request, obj=None):
#        return False
#
# NOW USING A CUSTOM FORM W/ AN EXTRA FIELD...
class MetadataVersionAdminForm(ModelForm):
    class Meta:
        model = MetadataVersion
        fields = ("file","name","url","categorization","registered","model_proxies",)
        readonly_fields = ("registered","model_proxies")

    model_proxies = ModelMultipleChoiceField(label="Models",required=False,queryset=MetadataModelProxy.objects.none())

    def __init__(self,*args,**kwargs):
        super(MetadataVersionAdminForm,self).__init__(*args,**kwargs)
        current_model_proxies = self.instance.model_proxies.all()
        self.fields["model_proxies"].queryset = current_model_proxies
        self.fields["model_proxies"].initial  = current_model_proxies
        update_field_widget_attributes(self.fields["model_proxies"],{"disabled":"disabled"})

class MetadataVersionAdmin(admin.ModelAdmin):
#    fields          = ("file","name","registered",)
#    inlines         = [MetadataVersionInline,]
    readonly_fields  = ("registered",)   # model_proxies is set as readonly in the __init__ fn above
    actions          = [register_metadata_versions,unregister_metadata_versions]
    form             = MetadataVersionAdminForm

admin.site.register(MetadataVersion,MetadataVersionAdmin)
