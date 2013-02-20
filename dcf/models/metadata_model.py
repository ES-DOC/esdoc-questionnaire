
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
__date__ ="Jan 31, 2013 11:27:20 AM"

"""
.. module:: metadata_model

Summary of module goes here

"""

from django.db import models
import json

from dcf.fields import *
from dcf.utils import *

def CIMDocument(documentRestriction=""):
    """
    specifies that a MetadataModel is a "CIM Document"
    this means that it can form the root element of a CIM Document,
    and can therefore be edited as a top-level model
    """
    def decorator(obj):
        obj._isCIMDocument = True                           # specify this model as a CIM Document
        obj._cimDocumentRestriction = documentRestriction   # specify what permission (if any) is needed to edit this document
        return obj
    return decorator

@guid()
class MetadataModel(models.Model):
    # ideally, MetadataModel should be an ABC
    # but Django Models already have a metaclass: django.db.models.base.ModelBase
    # see http://stackoverflow.com/questions/8723639/a-django-model-that-subclasses-an-abc-gives-a-metaclass-conflict for a description of the problem
    # and http://code.activestate.com/recipes/204197-solving-the-metaclass-conflict/ for a solution that just isn't worth the hassle
    #from abc import *
    #__metaclass__ = ABCMeta
    class Meta:
        app_label = APP_LABEL
        abstract = True

    # every subclass needs to have its own instances of this next set of attributes:
    _name        = "MetadataModel"                      # the name of the model; required
    _title       = "Metadata Model"                     # a pretty title for the model for display purposes; optional
    _description = "The base class for a MetadataModel" # some descriptive text about the model; optional

    # if a model is a CIM Document, then these attributes get set using the @CIMDocument decorator
    _isCIMDocument          = False
    _cimDocumentRestriction = ""

    def __unicode__(self):
        if self._title != MetadataModel.getTitle():
            return u'%s' % self._title
        if self._name != MetadataModel.getName():
            return u'%s' % self._name

    def getName(self):
        return self._name

    @classmethod
    def getName(cls):
        return cls._name

    def getTitle(self):
        return self._title

    @classmethod
    def getTitle(cls):
        return cls._title

    def getDescription(self):
        return self._description

    @classmethod
    def getDescription(cls):
        return cls._description

    def isCIMDocument(self):
        return self._isCIMDocument

    def getCIMDocumentRestriction(self):
        return self._cimDocumentRestriction

    @classmethod
    def getAttributes(cls):
        fields = [field for field in cls._meta.fields if issubclass(type(field),MetadataField)]
        m2m_fields = [field for field in cls._meta.many_to_many if issubclass(type(field),MetadataField)]
        return fields + m2m_fields

@guid()
class MetadataAttribute(models.Model):
    class Meta:
        app_label = APP_LABEL

@guid()
class MetadataProperty(models.Model):
    class Meta:
        app_label = APP_LABEL

    short_name  = models.CharField(max_length=BIG_STRING,blank=False)
    long_name   = models.CharField(max_length=BIG_STRING,blank=False)
    open        = models.BooleanField(default=False)
    multi       = models.BooleanField(default=False)
    nullable    = models.BooleanField(default=False)
    model_name  = models.CharField(max_length=LIL_STRING,blank=False)
    
    values      = models.CharField(max_length=HUGE_STRING,blank=True)
    children    = models.ManyToManyField("self",symmetrical=False,related_name="parent",blank=True)


    def __unicode__(self):
        return u'MetadataProperty: %s' % self.short_name
    
    def setValues(self,values):
        self.values = json.dumps(values,separators=(',',':'))

    def getValues(self):
        try:
            return json.loads(self.values)
        except ValueError:
            # values is empty
            return []

    def save(self, *args, **kwargs):
        # TODO: TEST THIS LOGIC
        if self.pk and (self in self.children.all()):
            msg = "a property cannot be its own child."
            raise MetadataError(msg)

        super(MetadataProperty,self).save(*args,**kwargs)