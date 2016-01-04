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
from Q.questionnaire import APP_LABEL

from Q.questionnaire.q_utils import EnumeratedType, EnumeratedTypeList
from Q.questionnaire.q_constants import *

class UnsynchronizedType(EnumeratedType):
    pass

UnsynchronizedTypes = EnumeratedTypeList([
    UnsynchronizedType("CV_ADDED", "Added CV"),
    UnsynchronizedType("CV_REMOVED", "Removed CV"),
    UnsynchronizedType("CV_CHANGED", "Changed CV"),
    UnsynchronizedType("ONTOLOGY_ADDED", "Added Ontology"),
    UnsynchronizedType("ONTOLOGY_REMOVED", "Removed Ontology"),
    UnsynchronizedType("ONTOLOGY_CHANGED", "Changed Ontology"),
    UnsynchronizedType("CUSTOMIZATION_ADDED", "Added Customization"),
    UnsynchronizedType("CUSTOMIZATION_REMOVED", "Removed Customization"),
    UnsynchronizedType("CUSTOMIZATION_CHANGED", "Changed Customization"),
])

UNSYNCHRONIZED_CHOICES = [(ut.get_type(), ut.get_name()) for ut in UnsynchronizedTypes]

class QSynchronization(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        # no verbose name needed
        # (not interacting w/ this in the admin)
        verbose_name = "Questionnaire (Un)Synchronization Type"
        verbose_name_plural = "Questionnaire (Un)Synchronization Types"

    type = models.CharField(max_length=LIL_STRING, blank=False, unique=True, choices=UNSYNCHRONIZED_CHOICES)
    description = models.TextField(blank=True, null=True)
    priority = models.PositiveIntegerField(blank=False, unique=True)

    def __unicode__(self):
        unsynchronized_type = UnsynchronizedTypes.get(self.type)
        return unsynchronized_type.get_name()


