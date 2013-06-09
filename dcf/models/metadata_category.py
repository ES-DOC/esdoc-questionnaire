
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
__date__ ="May 31, 2013 11:04:27 AM"

"""
.. module:: metadata_category

Summary of module goes here

"""

from django.db import models
#from django.contrib.contenttypes.models import *
#from django.contrib.contenttypes import generic
import json

from dcf.utils import *
from dcf.models import *

class MetadataCategory(models.Model):
    class Meta:
        app_label = APP_LABEL
        abstract = True

    _type = None

    name        = models.CharField(max_length=64,blank=True,editable=True)
    description = models.TextField(blank=True,editable=True)
    order       = models.PositiveIntegerField(blank=True,null=True,editable=True)
    key         = models.CharField(max_length=64,blank=True,editable=True)

    def getType(self):
        return self._type

    def save(self,*args,**kwargs):
        if not self.order:
            # categories ought to have a default id
            self.order = self.id
        super(MetadataCategory,self).save(*args,**kwargs)


class MetadataAttributeCategory(MetadataCategory):
    class Meta:
        app_label = APP_LABEL
        unique_together = (("key", "categorization"))
        ordering = [ "order" ]
        
    mapping = models.CharField(max_length=HUGE_STRING,blank=True)
    categorization = models.ForeignKey("MetadataCategorization",blank=False,null=False,editable=False,related_name="categories")

    _type = CategoryTypes.ATTRIBUTE

    _guid = models.CharField(max_length=64,unique=True,editable=False,blank=False,default=lambda:str(uuid4()))

    def getGUID(self):
        return self._guid

    def getMapping(self):
        try:
            return json.loads(self.mapping)
        except ValueError:
            # mapping is empty
            return {}

    def setMapping(self,mapping):
        if isinstance(mapping,dict):
            self.mapping=json.dumps(mapping,separators=(',',':'))
        else:
            msg = "a category mapping must be a dictionary"
            raise MetadataError(msg)

    def __unicode__(self):
        return u'%s::%s' % (self.categorization,self.name)

#@guid()
class MetadataPropertyCategory(MetadataCategory):
    class Meta:
        app_label = APP_LABEL
        unique_together = (("key", "vocabulary", "component_name"))
        ordering = [ "order" ]

    mapping         = models.CharField(max_length=HUGE_STRING,blank=True)
    vocabulary      = models.ForeignKey("MetadataVocabulary",blank=False,null=False,editable=False,related_name="categories")
    component_name  = models.CharField(max_length=BIG_STRING,blank=False)
    
    _type = CategoryTypes.PROPERTY

    _guid = models.CharField(max_length=64,unique=True,editable=False,blank=False,default=lambda:str(uuid4()))

    def isCustom(self):
        if self.vocabulary:
            return True
        else:
            return False

    def isDefault(self):
        return not self.isCustom()
    
    def getGUID(self):
        return self._guid

    def getMapping(self):
        try:
            return json.loads(self.mapping)
        except ValueError:
            # mapping is empty
            return {}

    def setMapping(self,mapping):
        if isinstance(mapping,dict):
            self.mapping=json.dumps(mapping,separators=(',',':'))
        else:
            msg = "a category mapping must be a dictionary"
            raise MetadataError(msg)

    def __unicode__(self):
        return u'%s'%self.name
        #return u'%s::%s' % (self.vocabulary,self.name)

#_METADATA_CATEGORY_LIMITS = {'model_in':('metadataattributecategory','metadatapropertycategory')}
#
#class MetadataCategoryRelation(models.Model):
#    class Meta:
#        app_label = APP_LABEL
#
#    # this uses a generic foreign key to contenttypes
#    # (but the limit_choices_to kwarg ensures it only applies to attribute & property categories)
#    content_type    = models.ForeignKey(ContentType,limit_choices_to=_METADATA_CATEGORY_LIMITS)
#    object_id       = models.PositiveIntegerField()
#    category        = generic.GenericForeignKey("content_type","object_id")
#    categorization  = models.ForeignKey("MetadataCategorization")
#
#    def __unicode__(self):
#        return u'%s' % self.category
