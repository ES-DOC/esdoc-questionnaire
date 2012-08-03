#    Django-CIM-Forms
#    Copyright (c) 2012 CoG. All rights reserved.
#
#    Developed by: Earth System CoG
#    University of Colorado, Boulder
#    http://cires.colorado.edu/
#
#    This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].

from django.db import models, DatabaseError
from uuid import uuid4
import django.forms.models
import django.forms.widgets
import django.forms.fields

from django.core import serializers
from django.template.loader import render_to_string
from django.db.models import F

from importlib import import_module
import re

from django_cim_forms.helpers import *
from django_cim_forms.fields import *
from django_cim_forms.controlled_vocabulary import *


#######################################################
# decorator that identifies a class as a CIM document #
#######################################################

def CIMDocument(documentType,documentName,documentProjectRestriction=None):
    def decorator(obj):
        obj._isCIMDocument = True            # specify this model as a CIM Document
        obj._cimDocumentType = documentType  # identify the type of that Document
        obj._cimDocumentName = documentName  # identify how this model should be named in the CIM
        # optionally, identify for this Document a project whose users only should be able to access it
        if documentProjectRestriction:
            try:
                # documentProjectRestriction will be of the format <module>.<project_class>(<filter_string>)
                # <filter_string> will be of the format <field>=<val1>,<field2>=<val2>...
                pattern = re.compile("^(.*[\.])(.+)\((.+)\)$")
                match = pattern.match(documentProjectRestriction)
                documentProjectRestrictionModule = match.group(1).rstrip(".")
                documentProjectRestrictionClass = match.group(2)

                documentProjectRestrictionFilter = {}
                for filter_item in match.group(3).split(","):
                    key,val = filter_item.split("=")
                    if key.find("__") < 0:
                        key = key + "__iexact"
                    documentProjectRestrictionFilter[key] = val

                module = import_module(documentProjectRestrictionModule)
                cls = module.__dict__[documentProjectRestrictionClass]
                instance = cls.objects.get(**documentProjectRestrictionFilter)
            
                obj._cimDocumentProjectRestriction = instance
            except:
                print "error setting project restriction on %s" % obj
                pass

        return obj
    return decorator

############################################
# the base classes for all metadata models #
############################################

class MetadataModel(models.Model):
    # ideally, MetadataModel should be an ABC
    # but Django Models already have a metaclass: django.db.models.base.ModelBase
    # see http://stackoverflow.com/questions/8723639/a-django-model-that-subclasses-an-abc-gives-a-metaclass-conflict for a description of the problem
    # and http://code.activestate.com/recipes/204197-solving-the-metaclass-conflict/ for a solution that just isn't worth the hassle
    #from abc import *
    #__metaclass__ = ABCMeta
    class Meta:
        abstract = True

    # every subclass needs to have its own instances of this next set of attributes:
    _name = "MetadataModel"     # the name of the model; required
    _title = "Metadata Model"   # a pretty title for the model for display purposes
    _fieldTypes = {}            # a dictionary associating fieldTypes with lists of fields
    _fieldTypeOrder = None      # a list describing the order of fieldTypes (tabs); if a type is absent from this list it is not rendered
    _fieldOrder = None          # a list describing the order of fields; if a field is absent from this list it is not rendered
    _initialValues = {}         # a dictionary of initial values for the first time a model is created

    # if a model is a CIM Document, then these attributes get set using the @CIMDocument decorator
    _isCIMDocument = False
    _cimDocumentType = ""
    _cimDocumentName = ""
    _cimDocumentProjectRestriction = None
    

    # every model has a (gu)id & version
    # (but since 'editable=False', they won't show up in forms)
    _guid = models.CharField(max_length=64,editable=False,blank=True,unique=True)
    _version = models.IntegerField(max_length=64,editable=False,blank=True)

    # what application (project) is this model associated w/;
    # you can only have inter (not intra) application relationships
    app = models.CharField(max_length=64,editable=False,blank=True)

    CURRENT_APP = "django_cim_forms"    # default application

    # these fields work behind the scenes to track when models are created and updated
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __init__(self,*args,**kwargs):
        super(MetadataModel,self).__init__(*args,**kwargs)
   
        if not self._guid:
            self._guid = str(uuid4())

        if not self._version:
            self._version = 1
            
        if not self.app:
            self.app = self.CURRENT_APP
            
        ModelClass = type(self)
        ParentClass = ModelClass.__bases__[0]

        # MetadataModel instances must have unique names & titles
        name = ModelClass.getName()
        title = ModelClass.getTitle()
        if re.match(r'.*\s+', name):
            msg = "invalid MetadataModel: name ('%s') must not contain spaces" % name
            raise MetadataError(msg)
        if not name or (name == ParentClass.getName()):
            msg = "invalid MetadataModel: no unique name supplied for %s" % ModelClass
            raise MetadataError(msg)
        if not title: #or (title == ParentClass.getTitle()):
            msg = "invalid MetadataModel: no title supplied for %s" % ModelClass
            raise MetadataError(msg)

    def userCanAccess(self,user):
        if self._cimDocumentProjectRestriction:
            app_label = self._cimDocumentProjectRestriction._meta.app_label
            code_name = self._cimDocumentProjectRestriction.short_name.lower()
            permission_string = "%s.%s_user_permission" % (app_label,code_name)
            permission = user.has_perm(permission_string)
# I AM HERE            print permission
            return permission
        # if no restriction (or an invalid restriction) was specified, just grant access by default
        return True

    # overriding save to work out when/how to update vs insert
    def save(self, *args, **kwargs):
        force_insert = kwargs.pop("force_insert",False)
        if force_insert:
##            # TODO: GET THIS WORKING!!!!!!!!!
##            kwargs['force_insert'] = True
##            kwargs['force_update'] = False
##            self.pk = None
            self._version = F('_version')+1

        return super(MetadataModel,self).save(*args,**kwargs)

    @classmethod
    def getName(cls):
        name = cls._name
        if name:
            return name.strip()
        return name

    @classmethod
    def getTitle(cls):
        title = cls._title
        if title:
            return title.strip()
        return title

    def isCIMDocument(self):
        return self._isCIMDocument
    
    def getCIMDocumentType(self):
        return self._cimDocumentType

    def getCIMDocumentName(self):
        fieldValue = getattr(self, self._cimDocumentName)
        return fieldValue
    
    def getGuid(self):
        return self._guid

    def getVersion(self):
        return self._version

    def updateVersion(self):
        #self._guid = str(uuid4) # guid stays the same for all time
        self._version = (self.getVersion()+1)


    def getField(self,fieldName):
        # return the actual field (not the db representation of the field)
        try:
            return self._meta.get_field_by_name(fieldName)[0]
        except models.fields.FieldDoesNotExist:
            return None

    @classmethod
    def customizeFields(cls,customizeDictionary):
        for (fieldToCustomize,propertiesToCustomize) in customizeDictionary.iteritems():

            field = cls._meta.get_field(fieldToCustomize)
            for (propertyName,propertyValue) in propertiesToCustomize.iteritems():
                setattr(field,propertyName,propertyValue)

        
    def registerFieldType(self,fieldType,fieldNames):
        for ft in self._fieldTypes:
            if fieldType == ft: # fieldType equality is based on .getType()
                                # therefore, even if a new FieldType instance is being registered
                                # a new key will only be added if it has a new type
                currentTypes = self._fieldTypes[ft]
                self._fieldTypes[ft] = list(set(currentTypes)|set(fieldNames)) # union of the new set of fields and the existing set
                return
        self._fieldTypes[fieldType] = fieldNames

    def setFieldTypeOrder(self,order):
        # this will override any parent orders
        self._fieldTypeOrder = order

    def setFieldOrder(self,order):
        # this will override any parent orders
        self._fieldOrder = order

    @classmethod
    def setFieldOrder(cls,order):
        cls._fieldOrder = order
        
    def getInitialValues(self):
        return self._initialValues

    def setInitialValues(self,initialValues):
        # this fn will overwrite existing initialValues
        # (this ensures that subclass's initialValues have precedence over superclasses)
        for (key,value) in initialValues.iteritems():
            field = self.getField(key)
            if not field:
                msg = "invalid field ('%s') specified in setInitialValues for '%s'" % (key,self._name)
                raise MetadataError(msg)
            if isinstance(field,MetadataEnumerationField):
                # if I'm initializing an enumeration, I have to deal w/ the peculiarities of MultiValueFields
                possibleChoices = field.getCustomChoices()
                if [choice for choice in possibleChoices if choice[0]==value]:
                    # value is a valid choice
                    value=[value,""]
                elif field.isOpen():# [choice for choice in possibleChoices if choice[0]=="OTHER"]:
                    # value is not a valid choice, but enumeration is open
                    value=["OTHER",value]
                else:
                    # value is not a valid choice, and enumeration is not open
                    msg = "%s is not a valid initialValue"
                    raise MetadataError(msg)

                field.setInitialEnumeratedValue(value)  # this lets me access the initial value later on (in case the field is marked as disabled)


            # TODO: DO ANY OTHER FIELD TYPES NEED SPECIAL INITIALIZATION LOGIC?

            self._initialValues[key] = value

# MOVED TO MetadataForm.initialize() B/C THE INITIAL PROPERTIES QUERYSET IS NOW A CURRIED FUNCTION
# AND WILL ONLY EXIST IF initial=true IN THE FORM CONSTRUCTOR (THAT TRIGGERS THE initialize() FN)
#            try:
#                # since this is the model doing the initialization of these properties
#                # I should add it to the set of models that can reference them
#                [v.addReferencingModel(self) for v in value if isinstance(v,MetadataProperty)]
#
#            except TypeError:
#                # this is not iterable
#                # therefore it can't be a queryset
#                # therefore it won't include properties
#                pass

    def serialize(self,format="json"):
        # sticking self in a list simulates a queryset
        qs = [self]
        if format.lower() == "json":
            data = JSON_SERIALIZER.serialize(qs)
            return data[1:len(data)-1]
        elif format.lower() == "xml":
            # I AM HERE
            #xml = render_to_string('model_template.xml', {'query_set': qs})
            data = serializers.serialize("xml",qs)
            return data
        else:
            msg = "Unknown serialization format: %s" % format
            raise MetadataError(msg)

##########################################
# properties are a special type of model #
# that are bound to CVs                  #
##########################################

class MetadataProperty(MetadataModel):
    class Meta:
        abstract = True

    _name = "MetadataProperty"
    _title = "Metadata Property"

    _fieldTypes = {}
    _fieldTypeOrder = None
    _fieldOrder = None
    _initialValues = {}

    cvClass = None
    cvInstance = None
    loadedCV = False

    referencingModels = set() # set of models that can reference this property (set ensures no duplicates)

    shortName = MetadataAtomicField.Factory("charfield",max_length=HUGE_STRING,blank=False)
    longName  = MetadataAtomicField.Factory("charfield",max_length=HUGE_STRING,blank=False)

    #value = MetadataAtomicField.Factory("charfield",max_length=HUGE_STRING,blank=False)
    value = MetadataPropertyField(blank=True,null=True)
    valueChoices = MetadataControlledVocabularyValueField(blank=True,null=True)

    parentShortName = MetadataAtomicField.Factory("charfield",max_length=HUGE_STRING,blank=True)
    parentLongName = MetadataAtomicField.Factory("charfield",max_length=HUGE_STRING,blank=True)

    open = models.NullBooleanField()        # can a user override the bound values?
    multi = models.NullBooleanField()       # can a user select more than one bound value?
    nullable = models.NullBooleanField()    # can a user select no bound values?
    custom = models.NullBooleanField()      # must a user provide a custom value?

    def __unicode__(self):
        name = u'%s' % self.getTitle()
        if self.longName:
            name = u'%s' % self.longName
        elif self.shortName:
            name = u'%s' % self.shortName
        if self.value:
            #name = u'%s: %s' % (name, self.value.strip().rstrip("|").rstrip("|"))
            # this is similar logic as that used by serializing to CIM XML
            # except that rather than separating sub-values via <value> tags,
            # I am separating them with "|" characters
            if self.isCustom():
                values = self.value.split("|")
                name = u'%s: %s' % (name, values[1])
            else:
                if self.isMulti():
                    allValues = ""
                    values = self.value.split("||")
                    multiValues = values[0].split("|")
                    for multiValue in multiValues:
                        if multiValue == "OTHER":
                            allValues += "OTHER: %s | " % values[1]
                        else:
                            allValues += "%s | " % multiValue
                    name = u'%s: %s' % (name, allValues.rstrip("| "))
                else:
                    allValues = ""
                    values = self.value.split("|")
                    if values[0] == "OTHER":
                        allValues += "OTHER: %s" % values[1]
                    else:
                        allValues += "%s" % values[0]
                    name = u'%s: %s' % (name, allValues)
        return name
        

    @classmethod
    def getProperties(cls,*args,**kwargs):
        # returns the queryset sepecified by "filter"
        # this is generally used to work out which properties to assign to a model as its initial values
        filter = kwargs.pop("filter","ALL")

        # first, check if the cv has been loaded...
        cvObjects = cls.cvClass.objects.all()
        if not cvObjects:
            msg = "failed to load " % cvClass
            raise MetadataError(msg)

        # next create a new set of properties corresponding to the CV...
        newProperties = set()
        for cvInstance in cvObjects:            
            newPropertyInstance = cls(cv=cvInstance)
            newPropertyInstance.save()
            newProperties.add(newPropertyInstance.id)            
        

        # TODO: ADDRESS THIS ISSUE...
        if (filter.upper()!="ALL"):
            msg = "Error: custom filters are not yet supported for retrieving initial properties"
            raise MetadataError(msg)
        
        # finally, return a queryset assuming I want ALL of the newly created properties...
        return cls.objects.filter(pk__in=newProperties)

    def getValueChoices(self):
        # TODO: COORDINATE THIS W/ OPEN/NONE/MULTI
        return self.valueChoices

    def hasParent(self):
        return (self.parentShortName != "" and self.parentShortName != None)

    def isMulti(self):
        return self.multi
    
    def isCustom(self):
        return self.custom 

    def hasValues(self):
        return self.valueChoices != None
        
    def hasSubItems(self):
        return not self.hasValues() and not self.isCustom()

    def getReferencingModels(self):
        return self.referencingModels

    def addReferencingModel(self,model):
        modelString = "%s.%s" % (model.app,model.getName())
        self.referencingModels.add(modelString)
        
    def __init__(self,*args,**kwargs):
        cv = kwargs.pop("cv",None)
        
        super(MetadataProperty,self).__init__(*args,**kwargs)

        
#        if self.cvClass and not self.loadedCV:
#            self.cvClass.loadCV()
#            self.loadedCV = True
#        
        if cv:
            self.cvInstance = cv
            self.shortName = cv.shortName
            self.longName = cv.longName
            self.open = cv.open
            self.multi = cv.multi
            self.nullable = cv.nullable
            self.custom = cv.custom
            self.valueChoices = cv.values
            if cv.parent:
                self.parentShortName = cv.parent.shortName
                self.parentLongName = cv.parent.longName

            
