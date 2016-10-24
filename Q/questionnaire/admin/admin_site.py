####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.forms import ModelForm
from django.core.exceptions import ValidationError
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from django.contrib.sites.models import Site
from django.db.models import Q
from Q.questionnaire.models.models_sites import QSite

__author__ = 'allyn.treshansky'


class SiteAdminForm(ModelForm):
    class Meta:
        model = Site
        fields = ("name", "domain")

    def clean(self):
        """
        prevents duplicate sites
        :return:
        """
        cleaned_data = super(SiteAdminForm, self).clean()
        site = self.instance
        existing_sites = Site.objects.filter(
            Q(name=cleaned_data["name"]) |
            Q(domain=cleaned_data["domain"]))\
            .exclude(pk=site.pk)
        if existing_sites:
            msg = "Sites must have unique names and domains."
            raise ValidationError(msg)
        return cleaned_data


class QSiteInline(admin.StackedInline):
    model = QSite
    can_delete = False
    verbose_name = "Questionnaire Site Type"
    verbose_name_plural = "Questionnaire Site Types"


class QSiteAdmin(admin.ModelAdmin):
    inlines = (QSiteInline, )
    form = SiteAdminForm

# when db is 1st setup, built-in Site may be registered before Q classes
try:
    admin.site.register(Site, QSiteAdmin)
except AlreadyRegistered:
    admin.site.unregister(Site)
    admin.site.register(Site, QSiteAdmin)
