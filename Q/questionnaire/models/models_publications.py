####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

from django.db import models
from django.conf import settings
from django.utils import timezone
import os

from Q.questionnaire.q_utils import EnumeratedType, EnumeratedTypeList
from Q.questionnaire.q_constants import *
from Q.questionnaire import APP_LABEL

###################
# local constants #
###################

class QPublicationFormat(EnumeratedType):

    def __unicode__(self):
        return u"%s" % (self.get_name())

QPublicationFormats = EnumeratedTypeList([
    QPublicationFormat("ESDOC_XML", "ES-DOC XML"),
    QPublicationFormat("CIM_XML", "CIM XML"),
])

UPLOAD_DIR = "publications"

####################
# the actual class #
####################

class QPublication(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "Questionnaire Publication"
        verbose_name_plural = "Questionnaire Publications"

    name = models.CharField(max_length=64, blank=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now_add=True, editable=False)
    version = models.IntegerField(blank=False)

    format = models.CharField(
        max_length=LIL_STRING,
        blank=False,
        choices=[(pf.get_type(), pf.get_name()) for pf in QPublicationFormats]
    )

    model = models.ForeignKey("MetadataModel", blank=False, null=False, related_name="publications")

    content = models.TextField()

    def __unicode__(self):
        return u"%s_%s" % (self.name, self.version)

    def save(self, *args, **kwargs):
        self.modified = timezone.now()
        super(QPublication, self).save(*args, **kwargs)

    def get_file_path(self):
        file_name = u"%s_%s.xml" % (self.name, self.version)
        file_path = os.path.join(
            settings.MEDIA_ROOT,
            APP_LABEL,
            UPLOAD_DIR,
            self.model.project.name,
            file_name
        )
        return file_path

    def write(self):
        publication_path = self.get_file_path()
        if not os.path.exists(os.path.dirname(publication_path)):
            os.makedirs(os.path.dirname(publication_path))
        with open(publication_path, "w") as file:
            file.write(self.content)
        file.closed

