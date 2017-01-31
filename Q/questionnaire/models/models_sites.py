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
.. module:: models_sites

Q-specific sites

"""

from django.contrib.sites.models import Site
from django.db import models

from Q.questionnaire import APP_LABEL
from Q.questionnaire.q_utils import EnumeratedType, EnumeratedTypeList
from Q.questionnaire.q_constants import *

__author__ = 'allyn.treshansky'


class QSiteType(EnumeratedType):
    pass

QSiteTypes = EnumeratedTypeList([
    QSiteType("LOCAL", "Local"),
    QSiteType("TEST", "Test"),
    QSiteType("DEV", "Development"),
    QSiteType("PROD", "Production"),
])


class QSite(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = 'Questionnaire Site'
        verbose_name_plural = 'Questionnaire Sites'

    # 1to1 relationship w/ standard Django Site...
    site = models.OneToOneField(Site, on_delete=models.CASCADE, related_name="q_site")

    # extra info associated w/ a Questionnaire Site...
    type = models.CharField(
        max_length=LIL_STRING,
        blank=True,
        choices=[(type.get_type(), type.get_name()) for type in QSiteTypes]
    )

    def __str__(self):
        return "{0}".format(self.site)

    def get_type(self):
        return self.type

    # def save(self, *args, **kwargs):
    #     super(QSite, self).save(*args, **kwargs)


def get_site_type(site):
    try:
        q_site = site.q_site
        return q_site.type
    except QSite.DoesNotExist:
        return None
