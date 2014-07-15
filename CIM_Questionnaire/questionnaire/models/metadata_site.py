
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
__date__ ="Jan 13, 2014 12:03:13 PM"

"""
.. module:: metadata_site

Summary of module goes here

"""

from django.db import models
from django.contrib.sites.models import Site

from questionnaire.utils import *


class MetadataSiteType(EnumeratedType):
    pass

MetadataSiteTypes = EnumeratedTypeList([
    MetadataSiteType("LOCAL","Local"),
    MetadataSiteType("TEST","Test"),
    MetadataSiteType("PROD","Production"),
])

class MetadataSite(models.Model):

    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        verbose_name        = 'Metadata Site'
        verbose_name_plural = 'Metadata Sites'

    # related name of 'metadata_site' was conflicting w/ debug_toolbar
    # so I changed it to 'questionnaire_site'
    site = models.OneToOneField(Site,related_name="questionnaire_site")

    type = models.CharField(
        max_length=SMALL_STRING,
        blank=True,
        null=True,
        choices=[(type.getType(),type.getName()) for type in MetadataSiteTypes]
    )

    def __unicode__(self):
        return u'%s' % (self.site)

    def get_type(self):
        return self.type

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db.utils import ProgrammingError

@receiver(post_save, sender=Site)
def site_post_save(sender, **kwargs):
    created = kwargs.pop("created",True)
    site = kwargs.pop("instance",None)
    if site and created:
        try:
            (metadata_site,created_metadata_site) = MetadataSite.objects.get_or_create(site=site)
        except ProgrammingError:
            if site.pk == 1:
                # this might fail in syncdb w/ the Django admin b/c the full set of db tables will not have been setup yet
                # print "skipped creating site profile for %s" % (site)
                pass
            else:
                msg = "Unable to create site profile for %s" % (site)
                raise MetadataError(msg)

def get_metadata_site_type(site):
    return site.questionnaire_site.get_type()