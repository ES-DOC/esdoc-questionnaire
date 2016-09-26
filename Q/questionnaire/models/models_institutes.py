__author__ = 'allyn.treshansky'

from django.db import models
from Q.questionnaire import APP_LABEL, q_logger
from Q.questionnaire.q_constants import *


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


