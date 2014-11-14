
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
__date__ ="Jan 23, 2014 10:17:50 AM"

"""
.. module:: admin_site

Summary of module goes here

"""

from django.forms import ModelForm

from django.db.models import Q

from django.contrib import admin
from django.contrib.sites.models import Site

from django.contrib.admin.sites import AlreadyRegistered

from CIM_Questionnaire.questionnaire.models.metadata_site import MetadataSite

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

try:
    admin.site.register(Site,MetadataSiteAdmin)
except AlreadyRegistered:
    admin.site.unregister(Site)
    admin.site.register(Site,MetadataSiteAdmin)
