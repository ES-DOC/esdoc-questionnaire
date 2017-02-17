####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from collections import OrderedDict
from django.db import models

from Q.questionnaire import APP_LABEL
# from Q.questionnaire.q_fields import QUnsavedManager, QUnsavedRelatedManager
from Q.questionnaire.q_constants import *

# this is an OrderedDict so that I can easily build up an array in "serializers_references"
QReferenceMap = OrderedDict([
    # according to "http://search.es-doc.org/media/js/search.data.mapper.js",
    # a reference's fields correspond to the following indices:
    ("experiment", 0),  # experiment
    ("institute", 1),  # institute
    ("long_name", 2),  # longName
    ("model", 3),  # model
    ("name", 4),  # name
    ("canonical_name", 5),  # canonicalName
    ("guid", 6),  # uuid
    ("version", 7),  # version
    ("alternative_name", 8),  # alternativeName
    # and these are unique to the Q...
    ("document_type", 9),
])


class QReference(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = 'Questionnaire Reference'
        verbose_name_plural = 'Questionnaire References'

    guid = models.UUIDField(blank=True, null=True, verbose_name="UUID")
    model = models.CharField(max_length=LIL_STRING, blank=True, null=True)
    experiment = models.CharField(max_length=LIL_STRING, blank=True, null=True)
    institute = models.CharField(max_length=LIL_STRING, blank=True, null=True)
    name = models.CharField(max_length=LIL_STRING, blank=True, null=True)
    canonical_name = models.CharField(max_length=LIL_STRING, blank=True, null=True)
    alternative_name = models.CharField(max_length=LIL_STRING, blank=True, null=True)
    long_name = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)

    document_type = models.CharField(max_length=BIG_STRING, blank=True, null=True)

    def __eq__(self, other):
        if isinstance(other, QReference):
            return self.guid == other.guid
        return NotImplemented

    def __ne__(self, other):
        equality_result = self.__eq__(other)
        if equality_result is NotImplemented:
            return equality_result
        return not equality_result

    def __str__(self):
        return "{0}".format(self.canonical_name)

    @property
    def key(self):
        # convert self.guid to str b/c UUID does not play nicely w/ JSON
        return str(self.guid)

    @property
    def is_pending(self):
        # a reference w/out a uuid must not yet have been resolved
        return self.guid is None

    @property
    def is_unused(self):
        # a reference used by no properties is unused
        return self.properties.count() == 0

