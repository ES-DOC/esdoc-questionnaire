
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
__date__ ="Jun 10, 2013 4:10:30 PM"

"""
.. module:: metadata_model

Summary of module goes here

"""

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from dcf.utils import *
from dcf.fields import *

def MetadataDocument(document_restriction=""):
    """
    specifies that a MetadataModel is a "CIM Document"
    this means that it can form the root element of a CIM Document,
    and can therefore be edited as a top-level model
    """
    def decorator(obj):
        obj._is_metadata_document          = True                   # specify this model as a CIM Document
        obj._metadata_document_restriction = document_restriction   # specify what permission (if any) is needed to edit this document

        # add some fields to obj...
        documentID = MetadataAtomicField.Factory("charfield",blank=True,)
        documentID.help_text = "a unique indentifier for this document"
        documentID.contribute_to_class(obj,"documentID")

        documentVersion = MetadataAtomicField.Factory("charfield",blank=True,)
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

        documentCreationDate = MetadataAtomicField.Factory("datefield",blank=True,)
        documentCreationDate.help_text = "The date the document was created."
        documentCreationDate.contribute_to_class(obj,"documentCreationDate")

        return obj
    return decorator

class MetadataModel(models.Model):
    # ideally, MetadataModel should be an ABC
    # but Django Models already have a metaclass: django.db.models.base.ModelBase
    # see http://stackoverflow.com/questions/8723639/a-django-model-that-subclasses-an-abc-gives-a-metaclass-conflict for a description of the problem
    # and http://code.activestate.com/recipes/204197-solving-the-metaclass-conflict/ for a solution that just isn't worth the hassle
    #from abc import *
    #__metaclass__ = ABCMeta
    class Meta:
        app_label   = APP_LABEL
        abstract    = True

    _name         = ""
    _title        = ""
    _description  = ""
    _type         = ""

    # if a model is a CIM Document, then these attributes get set using the @Document decorator above
    _is_metadata_document          = False
    _metadata_document_restriction = ""

    _guid = models.CharField(max_length=64,unique=True,editable=False,blank=False,default=lambda:str(uuid4()))

    metadata_project = models.ForeignKey("MetadataProject",blank=True,null=True,editable=False)
    component_name   = models.CharField(max_length=BIG_STRING,blank=True,null=True,)
    published        = models.BooleanField(default=False,)
    active           = models.BooleanField(default=True,)



    parent_content_type     = models.ForeignKey(ContentType,blank=True,null=True)
    parent_id               = models.PositiveIntegerField(blank=True,null=True)
    parent_object           = generic.GenericForeignKey('parent_content_type','parent_id')
    # can't have a reverse generic relation b/c this is an abstract class
    # so I do this manually in the getChildren fn below
    #children                = generic.GenericRelation("MetadataModel",content_type_field="parent_content_type",object_id_field="parent_id")


    scientific_properties   = generic.GenericRelation("MetadataProperty",content_type_field="model_content_type",object_id_field="model_id")

    # order of using this confusing stuff:
    # 1. save the parent
    # 2. call addParent from the child
    # 3. save the child
    # 4. call getChildren from the parent

    def getParent(self):
        return self.parent_object
    
    def setParent(self,parent):
        if not isinstance(parent,self.__class__):
            msg = "unable to assign a parent of a different class"
            raise MetadataError(msg)
        self.parent_object = parent

    def getChildren(self):
        model_type = ContentType.objects.get_for_model(self)
        model_class = model_type.model_class()
        children = model_class.objects.filter(
            parent_content_type__pk = model_type.id,
            parent_id = self.id
        )
        return children

    def getAllChildren(self):
        children = []
        self.getAllChildrenAux(children)
        return children

    def getAllChildrenAux(self,children):
        for child in self.getChildren():
            children.append(child)
            child.getAllChildrenAux(children)

    def addScientificProperty(self,property):
        property.model_object = self

    def addScientificProperties(self,properties):
        for property in properties:         
            self.addScientificProperty(property)

    def getScientificProperties(self):
        return self.scientific_properties.all()

    def getGUID(self):
        return self._guid

    def __unicode__(self):
        return u'%s' % (self._name)

    def setName(self,name):
        self._name = name

    def getName(self):
        return self._name

    @classmethod
    def getName(cls):
        return cls._name

    def setDescription(self,description):
        self._description = description

    def getDescription(self):
        return self._description

    @classmethod
    def getDescription(cls):
        return cls._description

    def setTitle(self,title):
        self._title = title
        
    def getTitle(self):
        return self._title
    
    @classmethod
    def getTitle(cls):
        return cls._title

    def setType(self,type):
        self._type = type

    def getType(self):
        return self._type

    @classmethod
    def getType(cls):
        return cls._type

    @classmethod
    def getFields(cls):
        fields      = [field for field in cls._meta.fields if issubclass(type(field),MetadataField)]
        m2m_fields  = [field for field in cls._meta.many_to_many if issubclass(type(field),MetadataField)]
        return fields + m2m_fields

    def getField(self,fieldName):
        # return the actual field (not the db representation of the field)
        try:
            return self._meta.get_field_by_name(fieldName)[0]
        except models.fields.FieldDoesNotExist:
            return None
        
    @classmethod
    def getField(cls,fieldName):
        # return the actual field (not the db representation of the field)
        try:
            return cls._meta.get_field_by_name(fieldName)[0]
        except models.fields.FieldDoesNotExist:
            return None

    @classmethod
    def isDocument(self):
        return self._is_metadata_document

    def isDocument(self):
        return self._is_metadata_document

    @classmethod
    def getDocumentRestriction(self):
        return self._metadata_document_restriction
    
    def getDocumentRestriction(self):
        return self._metadata_document_restriction

    def isPublished(self):
        return self.published

    def __unicode__(self):
        if hasattr(self,"name"):
            return u'%s' % (self.name)
        if hasattr(self,"longName"):
            return u'%s' % (self.longName)
        if hasattr(self,"shortName"):
            return u'%s' % (self.shortName)
        if hasattr(self,"individualName"):
            return u'%s' % (self.individualName)
        return u'%s' % self.getTitle()

# I am purposefully not making this inherit from django.db.models;
# (hopefully this will avoid the "bulk_create" error that sqlite3 gives for really large numbers of models)
# anyway, everything in an enumeration is static and I don't need to use db fields
class MetadataEnumeration(object):
    class Meta:
        app_label = APP_LABEL
        abstract  = True

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

class MetadataProperty(models.Model):
    class Meta:
        app_label = APP_LABEL
        abstract  = False

    category        = models.ForeignKey("MetadataScientificCategory",blank=True,null=True,on_delete=models.SET_NULL)
    customizer      = models.ForeignKey("MetadataScientificPropertyCustomizer",blank=True,null=True)
    component_name  = models.CharField(max_length=64,blank=True)

    property_enumeration  = MetadataEnumerationField(blank=True,null=True,verbose_name="value")
    property_freetext     = MetadataAtomicField.Factory("charfield",blank=True,verbose_name="value")

    choice                = MetadataAtomicField.Factory("charfield",blank=True)
    name                  = MetadataAtomicField.Factory("charfield",blank=True,verbose_name="short name")
    long_name             = MetadataAtomicField.Factory("charfield",blank=True,verbose_name="long name")
    standard_name         = MetadataAtomicField.Factory("charfield",blank=True,verbose_name="standard name")
    description           = MetadataAtomicField.Factory("textfield",blank=True,verbose_name="description")
    
    model_content_type      = models.ForeignKey(ContentType,blank=True,null=True)
    model_id                = models.PositiveIntegerField(blank=True,null=True)
    model_object            = generic.GenericForeignKey('model_content_type', 'model_id')

    def customize(self,property_customizer):
        self.customizer      = property_customizer
        self.category        = property_customizer.category
        self.component_name  = property_customizer.component_name
        self.choice          = property_customizer.choice
        self.name            = property_customizer.name

        self.long_name       = property_customizer.long_name
        self.standard_name   = property_customizer.standard_name
        self.description     = property_customizer.description


    

