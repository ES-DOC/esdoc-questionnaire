# module imports

from django.db import models, DatabaseError
from uuid import uuid4

# intra/inter-package imports

from django_cim_forms.helpers import *
from django_cim_forms.controlled_vocabulary import *

#############################################
# the types of fields that a model can have #
#############################################

class FieldType(EnumeratedType):
    pass

## THIS HAS BEEN MADE A CLASS VARIABLE
#
#FieldTypeList = EnumeratedTypeList([
#    FieldType("MODEL_DESCRIPTION","Component Description"),
#    FieldType("BASIC","Basic Properties"),
#    FieldType("SCIENTIFIC","Scientific Properties"),
#])


#################################################
# some custom relationships for metadata models #
#################################################

class MetadataManyToManyField(models.ManyToManyField):
    _fieldName  = ""

    def __init__(self,*args,**kwargs):
        # force this field to be blank and null; so that validation is essentially skipped
        kwargs["blank"] = True
        kwargs["null"] = True
        # require a related_name; so that I can have multiple relations to the same model
        # and so that I can work out exactly which app/model/field combination I should query when adding new subforms
        # TODO: I don't like this approach, but I can't figure out a better way to do it right now
        related_name=kwargs.pop('related_name',None)
        if not related_name:
            raise MetadataError("you must provide a related_name kwarg to a MetadataManyToManyField")
        kwargs["related_name"] = "%(app_label)s;%(class)s;" + related_name
        super(MetadataManyToManyField,self).__init__(*args,**kwargs)

class MetadataEnumerationField(models.ForeignKey):

    _open = False

    def isOpen(self):
        return self._open

    def __init__(self,*args,**kwargs):
        open = kwargs.pop('open',False)
        kwargs["blank"] = False
        kwargs["null"] = True
        super(MetadataEnumerationField,self).__init__(*args,**kwargs)
        self._open = open


########################################
# base classes for all Metadata Models #
########################################

class MetadataModel(models.Model):

    # ideally, MetadataModel should be an ABC
    # but Django Models already have a metaclass: django.db.models.base.ModelBase
    # see http://stackoverflow.com/questions/8723639/a-django-model-that-subclasses-an-abc-gives-a-metaclass-conflict for a description of the problem
    # and http://code.activestate.com/recipes/204197-solving-the-metaclass-conflict/ for a solution that just isn't worth the hassle
    #from abc import *
    #__metaclass__ = ABCMeta
    class Meta:
        abstract = True

    _name = ""  # the name of the model class
    _title = "" # the title (to display) of the model class
    
    guid = models.CharField(max_length=64,editable=False,blank=True,unique=True)

    # can overrwite / append to this list in child classes...
    FieldTypes = EnumeratedTypeList([
        FieldType("MODEL_DESCRIPTION","Component Description"),
        FieldType("BASIC","Basic Properties"),
        FieldType("SCIENTIFIC","Scientific Properties"),
    ])
    _fieldsByType = {}

    def getName(self):
        return self._name

    def getTitle(self):
        return self._title

    def getGuid(self):
        return self.guid

    @log_class_fn()
    def __init__(self,*args,**kwargs):
        super(MetadataModel,self).__init__(*args,**kwargs)
        if not self.guid:
            self.guid = str(uuid4())

    def registerFieldType(self,field_type,fields):
        fieldType = field_type.getType()
        if fieldType in self._fieldsByType:
            # append the fields to an existing set...
            self._fieldsByType[fieldType] += fields
        else:
            # or create a new set...
            self._fieldsByType[fieldType] = fields

    def getAllFieldTypes(self):
        return self.FieldTypes

    def getActiveFieldTypes(self):
        return [fieldType for fieldType in list(self.FieldTypes) if (fieldType.getType() in self._fieldsByType)]

    def addToFieldTypes(self,fieldType):
        if not fieldType in self.FieldTypes:
            self.FieldTypes.append(fieldType)

#######################################################################################
# base classes for all CIM Models                                                     #
# (CIM models are just MetdataModels w/ content that work w/ Controlled Vocabularies) #
#######################################################################################

class ResponsibleParty_Role_enumeration(MetadataEnumeration):
    _enum = []

try:
    ResponsibleParty_Role_enumeration.loadEnumerations(enum=['Author','Principle Investigator',])
except DatabaseError:
    pass


####################################################
# This is the CIMDocument Stereotype               #
# note that it doesn't inherit from MetadataModel  #
# it just adds some more fields to a MetadataModel #
####################################################

# here is a stereotype...
# it could have been written as a decorator...
# but in the interest of future auto-generation, I haven't...

class CimDocument(models.Model):

    class Meta:
        abstract = True

    documentID = models.CharField(max_length=36,blank=False,editable=False)
#    documentVersion
#    metadataId
#    metadataVersion
#    externalID
#    documentAuthor
#    documentCreationDate
#    documentGenealogy
#    quality
#    documentStatus

    def __init__(self, *args, **kwargs):
        super(CimDocument, self).__init__(*args, **kwargs)
        # these attributes aren't displayed on the forms (editable=False),
        # so I need to initialize some of them automatically.
        if not self.documentID:
           self.documentID = str(uuid4())
    

class SoftwareComponent(MetadataModel):
    
    class Meta:
        abstract = True

    _name = "ModelComponent"

    shortName = models.CharField(max_length=LIL_STRING,blank=False)
    shortName.help_text = "the name of the model that is used internally"
    longName = models.CharField(max_length=BIG_STRING,blank=False)
    longName.help_text = "the name of the model that is used externally"
    description = models.TextField(blank=True)
    description.help_text = "a free-text description of the component"
    license = models.CharField(max_length=BIG_STRING,blank=True)
    license.help_text = "the license held by this piece of software"
    embedded = models.BooleanField(blank=True)
    embedded.help_text = "An embedded component cannot exist on its own as an atomic piece of software; instead it is embedded within another (parent) component. When embedded equals 'true', the SoftwareComponent has a corresponding piece of software (otherwise it is acting as a 'virtual' component which may be inexorably nested within a piece of software along with several other virtual components)."
    # CHANGE TO THE CIM HERE
    # (using a container of responsibleParties instead of a series of them)
    responsibleParties = MetadataManyToManyField('ResponsibleParty',related_name="responsibleParties")
    releaseDate = models.DateField()
    releaseDate.help_text = "The date of publication of the software component code (as opposed to the date of publication of the metadata document, or the date of deployment of the model)"
    previousVersion = models.CharField(max_length=LIL_STRING,blank=True)
    fundingSource = models.CharField(max_length=BIG_STRING,blank=True)
    fundingSource.help_text = "The entities that funded this software component."
    citations = MetadataManyToManyField("Citation",related_name="citations")

    

    def __init__(self, *args, **kwargs):
        super(SoftwareComponent, self).__init__(*args, **kwargs)
        self.registerFieldType(self.FieldTypes.MODEL_DESCRIPTION, ["shortName","longName","description",])
        self.registerFieldType(self.FieldTypes.BASIC, ['releaseDate',"license",'agency','institution','responsibleParties','fundingSource','citations','references'])


class ModelComponent(SoftwareComponent,CimDocument):
#    type (enumeration)
#    timing

    def __init__(self, *args, **kwargs):
        super(ModelComponent, self).__init__(*args, **kwargs)
        

class ResponsibleParty(MetadataModel):
    _name = "ResponsibleParty"
    _title = "Responsible Party"
    
    individualName = models.CharField(max_length=LIL_STRING,blank=False)
    organizationName = models.CharField(max_length=LIL_STRING,blank=False)
    role = MetadataEnumerationField("ResponsibleParty_role_enumeration",open=True)

    positionName = models.CharField(max_length=LIL_STRING,blank=True)
    contactInfo = models.CharField(max_length=LIL_STRING,blank=True)

    def __init__(self,*args,**kwargs):
        super(ResponsibleParty,self).__init__(*args,**kwargs)
        self.registerFieldType(self.FieldTypes.BASIC,["individualName","organizationName","role","positionName","contactInfo"])

    def __unicode__(self):
        name = u'%s' % self.getName()
        if self.role:
            name = u'%s: %s' % (name, self.role)
        if self.individualName:
            name = u'%s: %s' % (name, self.individualName)
        return name


class Citation(MetadataModel):
    _name = "Citation"
    _title = "Citation"

    title = models.CharField(max_length=BIG_STRING,blank=False)
    alternateTitle = models.CharField(max_length=BIG_STRING,blank=True)
    edition = models.CharField(max_length=BIG_STRING,blank=True)
    editionDate = models.DateField(blank=True,null=True)
    identifier = models.CharField(max_length=BIG_STRING,blank=True)
  #  citedResponsibleParty = MetadataManyToManyField('ResponsibleParty',related_name="citedResponsibleParty")
    otherCitationDetails = models.TextField(blank=True)
    collectiveTitle = models.CharField(max_length=BIG_STRING,blank=True)
    isbn = models.CharField(max_length=LIL_STRING,blank=True)
    issn = models.CharField(max_length=LIL_STRING,blank=True)

    def __init__(self,*args,**kwargs):
        super(Citation,self).__init__(*args,**kwargs)
        self.registerFieldType(self.FieldTypes.BASIC,["title","alternateTitle","date","otherCitationDetails"])

    def __unicode__(self):
        return u'%s: %s' % (self.getName(), self.title)

