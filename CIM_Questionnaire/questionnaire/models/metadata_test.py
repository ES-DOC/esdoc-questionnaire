
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
__date__ ="Dec 18, 2013 1:19:49 PM"

"""
.. module:: metadata_test

Summary of module goes here

"""
from django.db import models


from CIM_Questionnaire.questionnaire.fields import TestField, EMPTY_CHOICE, NULL_CHOICE, OTHER_CHOICE
from CIM_Questionnaire.questionnaire.utils import APP_LABEL, LIL_STRING, SMALL_STRING, BIG_STRING, HUGE_STRING


class TestModel(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = False

    name = models.CharField(max_length=SMALL_STRING, blank=False, null=False)

    enumeration_value = TestField(blank=True, null=True)
    enumeration_other_value = models.CharField(max_length=HUGE_STRING, blank=True, null=True, default="hello world")

    def __unicode__(self):
        return self.name
