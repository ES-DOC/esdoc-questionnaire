####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.db import models
from Q.questionnaire import APP_LABEL, q_logger
from Q.questionnaire.q_constants import *

# institutes come from: https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_institution_id.json

class QInstitute(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "Questionnaire Institute"
        verbose_name_plural = "Questionnaire Institutes"
        ordering = ("name", )

    name = models.CharField(max_length=BIG_STRING, blank=False)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


