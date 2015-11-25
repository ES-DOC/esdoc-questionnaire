####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

from django.db import  models

from Q.questionnaire import APP_LABEL
from Q.questionnaire.q_utils import validate_no_spaces, validate_no_bad_chars, validate_no_reserved_words
from Q.questionnaire.q_constants import *

class QTestModel(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = False

    name = models.CharField(max_length=LIL_STRING, blank=False, unique=True, validators=[validate_no_spaces, validate_no_bad_chars, validate_no_reserved_words, ])

    def __unicode__(self):
        return u"QTestModel: %s" % (self.name)
