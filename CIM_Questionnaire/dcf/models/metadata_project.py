
####################
#   Django-CIM-Forms
#   Copyright (c) 2012 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Jun 10, 2013 4:11:53 PM"

"""
.. module:: metadata_project

Summary of module goes here

"""

from django.db import models

from dcf.utils import *

class MetadataProject(models.Model):
    class Meta:
        app_label           = APP_LABEL
        abstract            = False
        # this is one of the few classes that I allow admin access to, so give it pretty names:
        verbose_name        = 'Metadata Project'
        verbose_name_plural = 'Metadata Projects'


    _guid = models.CharField(max_length=64,unique=True,editable=False,blank=False,default=lambda:str(uuid4()))

    name        = models.CharField(max_length=255,blank=False,unique=True,validators=[validate_no_spaces])
    title       = models.CharField(max_length=BIG_STRING,blank=False)
    description = models.TextField(blank=True)

    default_version     = models.ForeignKey("MetadataVersion",blank=True,null=True,related_name="project")

    restriction_customize   = models.CharField(max_length=64,blank=True,null=True)
    restriction_edit        = models.CharField(max_length=64,blank=True,null=True)

    def getGUID(self):
        return self._guid

    def __unicode__(self):
        if self.title:
            return u'%s' % self.title
        else:
            return u'%s' % self.name

    def getName(self):
        return self.name
    
    def getTitle(self):
        return self.title

    def getDefaultVersion(self):
        return self.default_version

