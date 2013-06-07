
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

        # add some fields to obj...
        documentID = MetadataAtomicField.Factory("charfield",blank=False,)
        documentID.help_text = "a unique indentifier for this document"
        documentID.contribute_to_class(obj,"documentID")

        documentVersion = MetadataAtomicField.Factory("charfield",blank=False,)
        documentVersion.contribute_to_class(obj,"documentVersion")

        metadataID = MetadataAtomicField.Factory("charfield",blank=True,)
        metadataID.contribute_to_class(obj,"metadataID")

        metadataVersion = MetadataAtomicField.Factory("charfield",blank=True,)
        metadataVersion.contribute_to_class(obj,"metadataVersion")

        externalID = MetadataAtomicField.Factory("charfield",blank=True,)
        externalID.help_text = "The id of this document as referenced by an external body (ie: DOI, or even IPSL)"
        externalID.contribute_to_class(obj,"externalID")

        documentAuthor = MetadataAtomicField.Factory("charfield",blank=True,)
        documentAuthor.help_text = "A contact for the author of this document (as opposed to the author of the artifact being described by this document; ie: the simulation or component or whatever).This includes information about the authoring institution."
        documentAuthor.contribute_to_class(obj,"documentAuthor")

        documentCreationDate = MetadataAtomicField.Factory("datefield",blank=False,)
        documentCreationDate.help_text = "The date the document was created."
        documentCreationDate.contribute_to_class(obj,"documentCreationDate")

        return obj
    return decorator

#@guid()
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

    _guid = models.CharField(max_length=64,unique=True,editable=False,blank=False,default=lambda:str(uuid4()))
    def getGUID(self):
        return self._guid

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

    def getField(self,fieldName):
        # return the actual field (not the db representation of the field)
        try:
            return self._meta.get_field_by_name(fieldName)[0]
        except models.fields.FieldDoesNotExist:
            return None



#@guid()
class MetadataEnumeration(MetadataModel):
    class Meta:
        app_label = APP_LABEL

    # every subclass needs to have its own instances of this next set of attributes:
    _name        = "MetadataEnumeration"                      # the name of the model; required
    _title       = "Metadata Enumeration"                     # a pretty title for the model for display purposes; optional
    _description = "The base class for a MetadataEnumeration" # some descriptive text about the model; optional

    # if a model is a CIM Document, then these attributes get set using the @CIMDocument decorator
    _isCIMDocument          = False
    _cimDocumentRestriction = ""

    CHOICES     = []
    open        = False
    nullable    = False
    multi       = False

    def getChoices(self):
        return self.CHOICES

    @classmethod
    def getChoices(cls):
        return cls.CHOICES

    def isOpen(self):
        return self.open

    @classmethod
    def isOpen(cls):
        return cls.open

    def isNullable(self):
        return self.nullable

    @classmethod
    def isNullable(cls):
        return cls.nullable

    def isMulti(self):
        return self.multi

    @classmethod
    def isMulti(cls):
        return cls.multi
#@guid()
class MetadataAttribute(models.Model):
    class Meta:
        app_label = APP_LABEL

    _guid = models.CharField(max_length=64,unique=True,editable=False,blank=False,default=lambda:str(uuid4()))
    def getGUID(self):
        return self._guid

#@guid()
class MetadataProperty(models.Model):
    class Meta:
        app_label = APP_LABEL

    _guid = models.CharField(max_length=64,unique=True,editable=False,blank=False,default=lambda:str(uuid4()))
    def getGUID(self):
        return self._guid

    short_name  = models.CharField(max_length=BIG_STRING,blank=False)
    long_name   = models.CharField(max_length=BIG_STRING,blank=False)
    open        = models.BooleanField(default=False)
    multi       = models.BooleanField(default=False)
    nullable    = models.BooleanField(default=False)
    model_name  = models.CharField(max_length=LIL_STRING,blank=False)
    
    values      = models.TextField(blank=True)
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


@guid()
class TestModel(models.Model):
    class Meta:
        app_label = APP_LABEL

    name = models.CharField(max_length=LIL_STRING)
    loaded = models.BooleanField(default=False)    
    #subModels = models.ManyToManyField("TestSubModel")

    tmpSubModels = []

    def __init__(self,*args,**kwargs):
        
        super(TestModel,self).__init__(*args,**kwargs)

        if not self.loaded:
            self.tmpSubModels = []
            for name in ["a","b","c"]:
                self.tmpSubModels.append(TestSubModel(name=name))
            self.loaded = True
   
#    def getSubModels(self):
#        if self.pk:
#
#            return TestSubModel.objects.filter(parentGUID=self.getGUID())
#        else:
#            return self.tmpSubModels

###        if len(self.tmpSubModels):
###            return self.tmpSubModels
###        else:
###            return self.subModels.all()
###
####        if not self.guid:
### #           self.guid = str(uuid4())
###
###        print "INIT MODEL: %s" % self.getGUID()
###        print "loaded? %s" % self.loaded
###
###        if not self.loaded:
###            for name in ["a","b","c"]:
###                (subModel,created) = TestSubModel.objects.get_or_create(name=name,parentGUID=self.getGUID())
###                self.tmpSubModels.append(subModel)
###            self.loaded = True
###
###        print "loaded? %s" % self.loaded
###
    def save(self,*args,**kwargs):
        super(TestModel,self).save(*args,**kwargs)

        if len(self.tmpSubModels):

#            for subModel in self.tmpSubModels:
#                subModel.parent = self
#                subModel.save()
            self.tmpSubModels = []

###            #self.subModels = [subModel.update(guid=self.getGUID()) for subModel in self.tmpSubModels]
###            self.subModels = [subModel.update(parentGUID=self.getGUID()) for subModel in self.tmpSubModels]
###            self.tmpSubModels = []
###
###
    def __unicode__(self):
        return u"Model: '%s'"  % (self.name)

@guid()
class TestSubModel(models.Model):
    class Meta:
        app_label = APP_LABEL

    name = models.CharField(max_length=LIL_STRING)
    #parentGUID = models.CharField(max_length=64)
    parent = models.ForeignKey("TestModel",blank=True,null=True,related_name="subModels")
    
###
###    guid = models.CharField(max_length=64,unique=True,editable=False,blank=False,default=lambda:str(uuid4()))
###    def getGUID(self):
###        return self.guid
###
###    def __init__(self,*args,**kwargs):
###        super(TestSubModel,self).__init__(*args,**kwargs)
###        print "INIT SUBMODEL: %s" % self
###
###    def save(self,*args,**kwargs):
###        new_guid = kwargs.pop("new_guid",None)
###        if new_guid:
###            self.parentGUID = new_guid
###        super(TestSubModel,self).save(*args,**kwargs)
###
###    def update(self,*args,**kwargs):
###        for (key,value) in kwargs.iteritems():
###            setattr(self, key, value)
###        self.save()
###        return self.pk
###
    def __unicode__(self):
        if self.parent:
            return u"SubModel: '%s', parent=%s"  % (self.name, self.parent)
        else:
            return u"SubModel: '%s', no parent" % (self.name)