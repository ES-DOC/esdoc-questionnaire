__author__ = 'allyn.treshansky'

from django.db import models
from django.contrib import messages
from django.conf import settings
from django.dispatch import Signal

from lxml import etree as et
from uuid import uuid4
import os
import re

from Q.questionnaire import APP_LABEL, q_logger
from Q.questionnaire.q_fields import QFileField, QVersionField, QAtomicPropertyTypes
from Q.questionnaire.models.models_proxies import QModelProxy, QPropertyProxy
from Q.questionnaire.q_utils import QError, EnumeratedType, EnumeratedTypeList, Version, validate_file_extension, validate_file_schema, validate_no_spaces, validate_no_bad_chars, xpath_fix, remove_spaces_and_linebreaks, get_index
from Q.questionnaire.q_constants import *


###################
# local constants #
###################

PUBLICATION_UPLOAD_DIR = "publications"
PUBLICATION_UPLOAD_PATH = os.path.join(APP_LABEL, PUBLICATION_UPLOAD_DIR)

class QPublicactionFormat(EnumeratedType):

    def __str__(self):
        return "{0}".format(self.get_type())

QPublicationFormats = EnumeratedTypeList([
    QPublicactionFormat("CIM2_XML", "CIM2 XML"),
])


####################
# the actual class #
####################

class QPublication(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        unique_together = ("name", "version")
        verbose_name = "Questionnaire Publication"
        verbose_name_plural = "Questionnaire Publications"

    name = models.UUIDField(blank=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)
    version = QVersionField(blank=False)

    format = models.CharField(max_length=LIL_STRING, blank=False, choices=[(pf.get_type(), pf.get_name()) for pf in QPublicationFormats])

    model = models.ForeignKey("QModel", blank=False, null=False, related_name="publications")

    content = models.TextField()

    def __str__(self):
        return "{0}_{1}".format(self.name, self.get_version_major())

    def get_file_path(self):
        file_name = "{0}.xml".format(str(self))
        file_path = os.path.join(
            settings.MEDIA_ROOT,
            PUBLICATION_UPLOAD_PATH,
            self.model.project.name,
            file_name
        )
        return file_path

    def write(self):
        publication_path = self.get_file_path()
        if not os.path.exists(os.path.dirname(publication_path)):
            os.makedirs(os.path.dirname(publication_path))
        with open(publication_path, "w") as f:
            f.write(self.content)
        f.closed
