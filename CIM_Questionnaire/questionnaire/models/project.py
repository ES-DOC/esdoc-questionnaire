
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
__date__ ="Oct 14, 2013 4:59:13 PM"

"""
.. module:: project

Summary of module goes here

"""

from django.db import models

class Project(models.Model):
    class Meta:
        app_label           = APP_LABEL
        abstract            = False
        # this is one of the few classes that I allow admin access to, so give it pretty names:
        verbose_name        = 'Metadata Project'
        verbose_name_plural = 'Metadata Projects'

    name        = models.CharField(max_length=255,blank=False,unique=True,validators=[validate_no_spaces])
    title       = models.CharField(max_length=255,blank=False)
    description = models.TextField(blank=True)

    def __unicode__(self):
        if self.title:
            return u'%s' % self.title
        else:
            return u'%s' % self.name

