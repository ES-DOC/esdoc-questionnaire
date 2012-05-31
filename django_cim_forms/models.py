from django.db import models, DatabaseError
from uuid import uuid4
import django.forms.models
import django.forms.widgets
import django.forms.fields

from django_cim_forms.helpers import *
from django_cim_forms.fields import *
from django_cim_forms.controlled_vocabulary import *

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

    # every model has a guid
    # (but since 'editable=False', it won't show up in forms)
    guid = models.CharField(max_length=64,editable=False,blank=True,unique=True)

    def __init__(self,*args,**kwargs):
        super(MetadataModel,self).__init__(*args,**kwargs)
   
        if not self.guid:
            self.guid = str(uuid4())
   
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
                value = [value,""]#"%s|%s" & (value,"")

            # TODO: DO ANY OTHER FIELD TYPES NEED SPECIAL INITIALIZATION LOGIC?

            self._initialValues[key] = value


    def serialize(self,format="JSON"):
        # sticking self in a list simulates a queryset
        qs = [self]
        if format.upper() == "JSON":
            data = JSON_SERIALIZER.serialize(qs)
            return data[1:len(data)-1]
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

    def __unicode__(self):
        name = u'%s' % self.getTitle()
        if self.longName:
            name = u'%s' % self.longName
        elif self.shortName:
            name = u'%s' % self.shortName
        if self.value:
            name = u'%s: %s' % (name, self.value.strip().rstrip("|").rstrip("|"))
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
        return self.parentShortName != ""

    def hasValues(self):
        return self.valueChoices != None
        
    def hasSubItems(self):
        return not self.hasValues()

    def __init__(self,*args,**kwargs):
        cv = kwargs.pop("cv",None)
        
        super(MetadataProperty,self).__init__(*args,**kwargs)
        
 #       self.getField("value").widget = django.forms.Select()
        if cv:
            self.cvInstance = cv
            self.shortName = cv.shortName
            self.longName = cv.longName
            self.open = cv.open
            self.multi = cv.multi
            self.nullable = cv.nullable
            self.valueChoices = cv.values
            if cv.parent:
                self.parentShortName = cv.parent.shortName
                self.parentLongName = cv.parent.longName

            
