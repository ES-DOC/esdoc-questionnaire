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

class MetadataCVField(models.ManyToManyField):

    cv_name = None

    def __init__(self,*args,**kwargs):
        kwargs["max_length"] = 123
        _cv_name = kwargs.pop("cv_name",None)

        if _cv_name:
            try:
                models = MetadataCV.objects.filter(cv_name=_cv_name)
                if not models:
                    # we haven't loaded the cv yet...
                    models = MetadataCV.loadCV(cv_name=_cv_name)                    
            except DatabaseError:
                pass
            
         # I AM HERE

        super(MetadataCVField,self).__init__(MetadataCV)
        self.cv_name = _cv_name

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
        FieldType("SIMULATION_DESCRIPTION", "Simulation Description"),
        FieldType("EXPERIMENT_DESCRIPTION", "Experiment Description"),
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

######
# CV #
######

class MetadataCV(MetadataModel):
    cv_name = models.CharField(max_length=BIG_STRING,blank=False,editable=False)
    shortName = models.CharField(max_length=BIG_STRING,blank=False)
    longName = models.CharField(max_length=BIG_STRING,blank=True)
    value = models.CharField(max_length=BIG_STRING,blank=False)

    @log_class_fn(LoggingTypes.FULL)
    def __init__(self,*args,**kwargs):
        super(MetadataCV,self).__init__(*args,**kwargs)



    @classmethod
    def loadCV(cls,*args,**kwargs):
        _cv_name = kwargs.pop("cv_name",None)
        if _cv_name:
            print _cv_name
            parser = et.XMLParser(remove_blank_text=True)
            cv = et.fromstring(get_cv(_cv_name),parser)
            xpath_item_expression = "//item"
            items = cv.xpath(xpath_item_expression)
            for item in items:
                shortName = item.xpath("shortName/text()")[0] or None
                longName = item.xpath("longName/text()")[0] or None
                model = MetadataCV()
                model.cv_name = _cv_name
                if shortName:
                    model.shortName = shortName
                if longName:
                    model.longName = longName
                # TODO: values / choices
                xpath_value_expression="//item[shortName/text()='%s']/values/value" % shortName
                values = cv.xpath(xpath_value_expression)
                value_choices = []
                for value in values:
                    valueShortName = item.xpath("shortName/text()")
                    valueLongName = item.xpath("longName/text()")
                    if not valueLongName:
                        value_choices.append((valueShortName[0],valueShortName[0]))
                    else:
                        value_choices.append((valueShortName[0],valueLongName[0]))
                model._meta.get_field_by_name("value")[0]._choices = value_choices
                model.fields["value"].choices = value_choices

                model.save()

    def __unicode__(self):
        name = u'%s' % "MetadataCV"
        if self.cv_name:
            name = u'%s' % self.cv_name
        if self.value:
            name = u'%s: %s' % (name, self.value)
        return name

########
# Enum #
########

class MetadataEnumeration(models.Model):

    name = models.CharField(max_length=25,blank=False)

    class Meta:
        abstract = True

    def __unicode__(self):
        return u'%s' % self.name

    @classmethod
    def add(cls,*args,**kwargs):
        name = kwargs.pop("name",None)
        if name:
            cls.objects.get_or_create(name=name)

    @classmethod
    def loadEnumerations(cls,*args,**kwargs):
        enum = kwargs.pop("enum",[])
        cls._enum = enum
        for name in enum:
            cls.add(name=name)

#######################################################################################
# base classes for all CIM Models                                                     #
# (CIM models are just MetdataModels w/ content that work w/ Controlled Vocabularies) #
#######################################################################################

class ResponsibleParty_Role_enumeration(MetadataEnumeration):
    _enum = []

class Activity_project_enumeration(MetadataEnumeration):
    _enum = []

try:
    ResponsibleParty_Role_enumeration.loadEnumerations(enum=['Author','Principle Investigator',])
    Activity_project_enumeration.loadEnumerations(enum=['CMIP5','AMIP','TAMIP'])
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
    
class Activity(MetadataModel):
    class Meta:
        abstract = True

    _name = "Activity"
    _fieldsByType = {}

    responsibleParties = MetadataManyToManyField('ResponsibleParty',related_name="responsibleParties")
    fundingSource = models.CharField(max_length=BIG_STRING,blank=True)
    rationale = models.TextField(blank=True)
    rationale.help_text = "For what purpose is this activity being performed?"
    project = MetadataEnumerationField("Activity_project_enumeration",open=True)

    def __init__(self, *args, **kwargs):
        super(Activity, self).__init__(*args, **kwargs)
        self.registerFieldType(self.FieldTypes.SIMULATION_DESCRIPTION, ["project","rationale",])
        self.registerFieldType(self.FieldTypes.BASIC, ['fundingSource','responsibleParties'])

class NumericalActivity(Activity):
    class Meta:
        abstract = True

    _name = "NumericalActivity"

    shortName = models.CharField(max_length=LIL_STRING,blank=False)
    longName = models.CharField(max_length=BIG_STRING,blank=False)
    description = models.TextField(blank=True)

    def __init__(self, *args, **kwargs):
        super(NumericalActivity, self).__init__(*args, **kwargs)
        self.registerFieldType(self.FieldTypes.SIMULATION_DESCRIPTION, ["shortName","longName","description"])

class Simulation(NumericalActivity):
    class Meta:
        abstract = True
        
    _name = "Simulation"
    _fieldsByType = {}

    simulationID = models.CharField(max_length=BIG_STRING,blank=True)
    calendar = models.DateField(blank=False)

    def __init__(self,*args,**kwargs):
        super(Simulation,self).__init__(*args,**kwargs)
        self.registerFieldType(self.FieldTypes.SIMULATION_DESCRIPTION, ["simulationID"])
        self.registerFieldType(self.FieldTypes.BASIC, ["calendar"])

class SimulationRun(Simulation,CimDocument):
    _name = "SimulationRun"

    pass

class Experiment(Activity):
    _name = "Experiment"
    _fieldsByType = {}

    
    def __init__(self,*args,**kwargs):
        super(Experiment,self).__init__(*args,**kwargs)

class NumericalExperiment(Experiment,CimDocument):
    _name = "NumericalExperiment"

    shortName = models.CharField(max_length=LIL_STRING,blank=False)
    longName = models.CharField(max_length=BIG_STRING,blank=False)
    description = models.TextField(blank=True)
    experimentID = models.CharField(max_length=LIL_STRING,blank=True)
    calendar = models.DateField(blank=False)

    def __init__(self,*args,**kwargs):
        super(NumericalExperiment,self).__init__(*args,**kwargs)
        self.registerFieldType(self.FieldTypes.EXPERIMENT_DESCRIPTION, ["shortName","longName","description","experimentID"])
        self.registerFieldType(self.FieldTypes.BASIC, ["calendar"])

class SoftwareComponent(MetadataModel):
    
    class Meta:
        abstract = True

    _name = "SoftwareComponent"

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

