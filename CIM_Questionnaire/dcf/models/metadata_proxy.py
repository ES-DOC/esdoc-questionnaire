
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
__date__ ="Jun 12, 2013 12:29:04 AM"

"""
.. module:: metadata_property

Summary of module goes here

"""
from django.db import models

from dcf.utils import *
from dcf.fields import *

class MetadataModelProxy(models.Model):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        verbose_name        = 'Model Proxy'
        verbose_name_plural = 'Model Proxies'

    _guid = models.CharField(max_length=64,unique=True,editable=False,blank=False,default=lambda:str(uuid4()))

    version             = models.ForeignKey("MetadataVersion",blank=False)
    model_name          = models.CharField(max_length=64,blank=False)
    document_type       = models.CharField(max_length=64,blank=True,choices=CIM_DOCUMENT_TYPES)

    model_title         = models.CharField(max_length=BIG_STRING,blank=False)
    model_description   = models.TextField(blank=True)

    def getGUID(self):
        return self._guid

    def __unicode__(self):
        return u'%s' % self.model_name

    def getStandardPropertyProxies(self):
        return MetadataStandardPropertyProxy.objects.filter(model_name=self.model_name,version=self.version)

    def getScientificPropertyProxies(self,vocabulary):
        return MetadataScientificPropertyProxy.objects.filter(model_name=self.model_name,vocabulary=vocabulary)
    

class MetadataPropertyProxy(models.Model):
    class Meta:
        app_label   = APP_LABEL
        abstract    = True

    _guid = models.CharField(max_length=64,unique=True,editable=False,blank=False,default=lambda:str(uuid4()))

    model_name  = models.CharField(max_length=255,blank=False)
    name        = models.CharField(max_length=255,blank=False)
    type        = models.CharField(max_length=255,blank=True,choices=[(type.getType(),type.getName()) for type in MetadataFieldTypes])

    required            = models.BooleanField(default=True,blank=True)
    editable            = models.BooleanField(default=True,blank=True)
    unique              = models.BooleanField(default=False,blank=True)
    verbose_name        = models.CharField(max_length=255,blank=False)
    documentation       = models.TextField(blank=True)
    default_value       = models.CharField(max_length=255,blank=True,null=True)

    def getGUID(self):
        return self._guid

    def __unicode__(self):
        return u'%s::%s' % (self.model_name,self.name)

class MetadataStandardPropertyProxy(MetadataPropertyProxy):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        unique_together = ("version","model_name","name")
        verbose_name        = 'Standard Prop. Proxy'
        verbose_name_plural = 'Standard Prop. Proxies'
    
    version     = models.ForeignKey("MetadataVersion",blank=False)
    category    = models.ForeignKey("MetadataStandardCategory",blank=True,null=True,on_delete=models.SET_NULL)
    field_type  = models.CharField(max_length=64,blank=False)

    enumeration_choices  = models.TextField(blank=True,null=True)
    enumeration_open     = models.BooleanField(default=False,blank=True)
    enumeration_multi    = models.BooleanField(default=False,blank=True)
    enumeration_nullable = models.BooleanField(default=False,blank=True)

    relationship_target_model = models.CharField(max_length=64,blank=True)
    relationship_source_model = models.CharField(max_length=64,blank=True)
    
    def __init__(self,*args,**kwargs):
        super(MetadataStandardPropertyProxy,self).__init__(*args,**kwargs)
        if isAtomicField(self.field_type):
            self.type = MetadataFieldTypes.ATOMIC
        elif isRelationshipField(self.field_type):
            self.type = MetadataFieldTypes.RELATIONSHIP
        elif isEnumerationField(self.field_type):
            self.type = MetadataFieldTypes.ENUMERATION
        


    def getCategory(self):
        return self.category

SCIENTIFIC_PROPERTY_CHOICES = [
    ("XOR","XOR"),
    ("OR","OR"),
    ("keyboard","keyboard"),
]

SCIENTIFIC_PROPERTY_FORMAT = [
    ("string","string"),
    ("numerical","numerical")
]

class MetadataScientificPropertyProxy(MetadataPropertyProxy):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        unique_together = ("model_name","component_name","name","category")
        verbose_name        = 'Scientific Prop. Proxy'
        verbose_name_plural = 'Scientific Prop. Proxies'

    vocabulary      = models.ForeignKey("MetadataVocabulary",blank=True,null=True)
    category        = models.ForeignKey("MetadataScientificCategory",blank=True,null=True,on_delete=models.SET_NULL)
    component_name  = models.CharField(max_length=64,blank=True)
    choice          = models.CharField(max_length=64,blank=True,null=True,choices=SCIENTIFIC_PROPERTY_CHOICES)
    
    standard_name   = models.CharField(max_length=64,blank=True,null=True)
    long_name       = models.CharField(max_length=64,blank=True,null=True)
    description     = models.TextField(max_length=64,blank=True,null=True)


    def __init__(self,*args,**kwargs):
        super(MetadataScientificPropertyProxy,self).__init__(*args,**kwargs)

    def getCategory(self):
        return self.category

class MetadataScientificPropertyProxyValue(models.Model):
    class Meta:
        app_label = APP_LABEL
        abstract  = False
        verbose_name        = 'Sci. Prop. Val. Proxy'
        verbose_name_plural = 'Sci. Prop. Val. Proxies'

    property = models.ForeignKey("MetadataScientificPropertyProxy",blank=False,editable=False,related_name="values")

    format = models.CharField(max_length=LIL_STRING,blank=True,null=True,choices=SCIENTIFIC_PROPERTY_FORMAT)
    units  = models.CharField(max_length=LIL_STRING,blank=True,null=True)
    name   = models.CharField(max_length=BIG_STRING,blank=True,null=True)

    def __unicode__(self):
        return u'%s' % self.name
