
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
__date__ ="Jun 8, 2013 12:27:08 PM"

"""
.. module:: metadata_property

Summary of module goes here

"""

from django.db import models
import json

from dcf.fields import *
from dcf.utils import *

PROPERTY_CHOICES = [
    ("XOR","XOR"),
    ("OR","OR"),
    ("keyboard","keyboard"),
]

PROPERTY_FORMAT = [
    ("string","string"),
    ("numerical","numerical")
]


class MetadataProperty(models.Model):
    class Meta:
        app_label = APP_LABEL
        unique_together = (("vocabulary", "name", "component_name", "default_category"))

    _guid = models.CharField(max_length=64,unique=True,editable=False,blank=False,default=lambda:str(uuid4()))
    
    vocabulary          = models.ForeignKey("MetadataVocabulary",blank=False,null=False,editable=False,related_name="default_properties")
    default_category    = models.ForeignKey("MetadataPropertyCategory",blank=True,null=True)

    component_name  = models.CharField(max_length=BIG_STRING,blank=False)

    name        = models.CharField(max_length=BIG_STRING,blank=False)
    choice      = models.CharField(max_length=LIL_STRING,blank=True,null=True,choices=PROPERTY_CHOICES)
    description = models.TextField(blank=True)

    open        = models.BooleanField(default=False)
    multi       = models.BooleanField(default=False)
    nullable    = models.BooleanField(default=False)

    
    def getGUID(self):
        return self._guid

    def __unicode__(self):
        return u'MetadataProperty: %s' % self.name

class MetadataPropertyValue(models.Model):
    class Meta:
        app_label = APP_LABEL

    _guid = models.CharField(max_length=64,unique=True,editable=False,blank=False,default=lambda:str(uuid4()))

    property = models.ForeignKey("MetadataProperty",blank=False,editable=False,related_name="values")

    format = models.CharField(max_length=LIL_STRING,blank=True,null=True,choices=PROPERTY_FORMAT)
    units  = models.CharField(max_length=LIL_STRING,blank=True,null=True)
    name   = models.CharField(max_length=BIG_STRING,blank=True,null=True)

    def getGUID(self):
        return self._guid

    def __unicode__(self):
        return u'MetadataPropertyValue: %s' % self.name
