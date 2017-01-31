from django.db import models
from Q.questionnaire import APP_LABEL, q_logger


class ThingProject(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "Questionnaire Project"
        verbose_name_plural = "Questionnaire Project"

    pass

