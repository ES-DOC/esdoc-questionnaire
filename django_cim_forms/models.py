# module imports

from django.db import models, DatabaseError
from uuid import uuid4

# intra/inter-package imports

from django_cim_forms.helpers import *
from django_cim_forms.controlled_vocabulary import *

############################################################
# the types of fields that a model can have                #
# (these are specified as needed in the models themselves) #
############################################################

class FieldType(EnumeratedType):
    pass

##############################
# custom fields for metadata #
##############################

class MetadataEnumerationField(models.ForeignKey):

    _open = False

    def isOpen(self):
        return self._open

    def __init__(self,*args,**kwargs):
        open = kwargs.pop('open',False)
        enumerationClass = kwargs.pop('enumeration',None)
        # TODO: why doesn't this work from here?
        #if enumerationClass:
        #   enumerationClass.loadEnumerations()
        kwargs["blank"] = open
        kwargs["null"] = True
        super(MetadataEnumerationField,self).__init__(enumerationClass,**kwargs)
        self._open = open

class MetadataCVField(models.ManyToManyField):

    def __init__(self,*args,**kwargs):
        cvClass = kwargs.pop('cv',None)
        # TODO: again, not sure why I can't call this from here?
        #if cvClass:
        #    cvClass.loadCV()
        kwargs["blank"] = True
        kwargs["null"] = True
        super(MetadataCVField,self).__init__(cvClass,**kwargs)

class MetadataManyToManyField(models.ManyToManyField):
    
    def __init__(self,*args,**kwargs):
        # force this field to be blank and null; so that validation is essentially skipped
        # (I do it manually in MetadataForm.clean)
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

class MetadataForeignKey(models.ForeignKey):

    def __init__(self,*args,**kwargs):
        # force this field to be blank and null; so that validation is essentially skipped
        # (I do it manually in MetadataForm.clean)
        kwargs["blank"] = True
        kwargs["null"] = True

        # require a related_name; so that I can have multiple relations to the same model
        # and so that I can work out exactly which app/model/field combination I should query when adding new subforms
        # TODO: I don't like this approach, but I can't figure out a better way to do it right now
        related_name=kwargs.pop('related_name',None)
        if not related_name:
            raise AttributeError("you must provide a related_name kwarg to a MetadataForeignKey")
        kwargs["related_name"] = "%(app_label)s;%(class)s;" + related_name
        super(MetadataForeignKey,self).__init__(*args,**kwargs)


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

    _fieldTypes = EnumeratedTypeList([])
    _fieldsByType = {}
    
    # every model has a guid
    guid = models.CharField(max_length=64,editable=False,blank=True,unique=True)

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

    def registerFieldType(self,fieldType,fields):
        # add to _fieldTypes if the fieldType is new
        if not fieldType in self._fieldTypes:
            self._fieldTypes.append(fieldType)

        if fieldType.getType() in self._fieldsByType:
            # append the fields to an existing set...
            self._fieldsByType[fieldType.getType()] += fields
        else:
            # or create a new set...
            self._fieldsByType[fieldType.getType()] = fields

    def getAllFieldTypes(self):
        return self._fieldTypes

    def getActiveFieldTypes(self):
        return [fieldType for fieldType in list(self._fieldTypes) if (fieldType.getType() in self._fieldsByType)]

    def serialize(self,format="JSON"):
        # sticking self in a list simulates a queryset
        qs = [self]
        if format.upper() == "JSON":
            data = json_serializer.serialize(qs)
            return data[1:len(data)-1]
        else:
            msg = "Unknown serialization format: %s" % format
            raise AttributeError(msg)

#######
# CVs #
#######

class MetadataCV(MetadataModel):
    _name = "MetadataCV"
    _cv = None
    _choices = []
    
    shortName = models.CharField(max_length=BIG_STRING,blank=False)
    longName = models.CharField(max_length=BIG_STRING,blank=True)
    value = models.CharField(max_length=BIG_STRING,blank=False)

    def getName(self):
        return self._name

    def __unicode__(self):
        name = u'%s' % self.getName()
        if self.longName:
            name = u'%s' % self.longName
        if self.value:
            name = u'%s: %s' % (name, self.value)
        return name

    @classmethod
    def loadCV(cls,*args,**kwargs):
        cv_name = kwargs.pop("cv_name",cls._cv_name)
        parser = et.XMLParser(remove_blank_text=True)
        cv = et.fromstring(get_cv(cv_name),parser)
        xpath_item_expression = "//item"
        items = cv.xpath(xpath_item_expression)
        for item in items:
            shortName = item.xpath("shortName/text()") or None
            longName = item.xpath("longName/text()") or None
            (model,created) = cls.objects.get_or_create(shortName=shortName[0],longName=longName[0])
#            xpath_value_expression="//item[shortName/text()='%s']/values/value" % shortName[0]
#            values = cv.xpath(xpath_value_expression)
#            value_choices = []
#            for value in values:
#                valueShortName = value.xpath("shortName/text()")
#                valueLongName = value.xpath("longName/text()")
#                if not valueLongName:
#                    value_choices.append((valueShortName[0],valueShortName[0]))
#                else:
#                    value_choices.append((valueShortName[0],valueLongName[0]))
#            model._cv = cv
#            model._choices = value_choices
            model.save()

####################
# CIM v1.5 Content #
####################

#########
# Enums #
#########

class DataPurpose_enumeration(MetadataEnumeration):
   _enum = ["ancillaryFile","initialCondition","boundaryCondition"]

class CouplingFrameworkType_enumeration(MetadataEnumeration):
   _enum = ["BFG","ESMF","OASIS"]

class ResponsiblePartyRole_enumeration(MetadataEnumeration):
   _enum = ["Author","Principle Investigator",]

class ModelComponentType_enumeration(MetadataEnumeration):
    _enum = [ "Advection", "Aerosol3D", "Aerosol2D", "AerolEmissionAndConc", "AerosolKeyProperties", "AerosolModel", "Aerosols", "AerosolSpaceConfig", "AerosolTransport", "AtmChem2D", "AtmChem3D", "AtmChemEmissionAndConc", "AtmChemKeyProperties", "AtmChemSpaceConfig", "AtmChemTransport", "AtmGasPhaseChemistry", "AtmHeterogeneousChemistry", "AtmosAdvection", "AtmosCloudScheme", "AtmosConvectTurbulCloud", "AtmosDynamicalCore", "AtmosHorizontalDomain", "AtmosKeyProperties", "AtmosOrographyAndWaves", "Atmosphere", "AtmosphericChemistry", "AtmosRadiation", "AtmosSpaceConfiguration", "Climate", "CloudSimulator", "IceSheetDynamics", "LandIce", "LandIceGlaciers", "LandIceKeyProperties", "LandIceSheet", "LandIceShelves", "LandIceShelvesDynamics", "LandSurface", "LandSurfaceAlbedo", "LandSurfaceCarbonCycle", "LandSurfaceEnergyBalance", "LandSurfaceKeyProperties", "LandSurfaceLakes", "LandSurfaceSnow", "LandSurfaceSoil", "LandSurfaceSpaceConfiguration", "LandSurfaceVegetation", "LandSurfSoilHeatTreatment", "LandSurfSoilHydrology", "Ocean", "OceanAdvection", "OceanBioBoundaryForcing", "OceanBioChemistry", "OceanBioGasExchange", "OceanBioGeoChemistry", "OceanBioKeyProperties", "OceanBioSpaceConfig", "OceanBioTimeStepFramework", "OceanBioTracers", "OceanBioTracersEcosystem", "OceanBoundaryForcing", "OceanBoundaryForcingTracers", "OceanHorizontalDomain", "OceanInteriorMixing", "OceanKeyProperties", "OceanLateralPhysics", "OceanLateralPhysMomentum", "OceanLateralPhysTracers", "OceanMixedLayer", "OceanNudging", "OceanSpaceConfiguration", "OceanUpAndLowBoundaries", "OceanVerticalPhysics", "PhotoChemistry", "RiverRouting", "SeaIce", "SeaIceDynamics", "SeaIceKeyProperties", "SeaIceSpaceConfiguration", "SeaIceThermodynamics", "StratosphericHeterChem", "TopOfAtmosInsolation", "ToposphericHeterChem", "VegetationCarbonCycle",]

class TimingUnits_enumeration(MetadataEnumeration):
    _enum = ["seconds", "minutes", "hours", "days", "months", "years", "decades", "centuries"]
    
class Activity_Project_enumeration(MetadataEnumeration):
    _enum = ['CMIP5','AMIP','TAMIP']

class CalendarUnitType_enumeration(MetadataEnumeration):
    _enum = ['days','months','years']
    
class NumericalRequirementType_enumeration(MetadataEnumeration):
    _enum = ['Initial Condition','Boundary Condition','Output Requirement','SpatioTemporal Constraint']

#####


class DataSource(MetadataModel):
    class Meta:
        abstract = True

    purpose = MetadataEnumerationField(enumeration=DataPurpose_enumeration,open=True)

    def __init__(self,*args,**kwargs):
        super(DataSource, self).__init__(*args, **kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"),["purpose"])


class Activity(MetadataModel):
    class Meta:
        abstract = True

    responsibleParties = MetadataManyToManyField('ResponsibleParty',related_name="responsibleParties")
    fundingSource = models.CharField(max_length=BIG_STRING,blank=True)
    rationale = models.TextField(blank=True)
    rationale.help_text = "For what purpose is this activity being performed?"
    project = MetadataEnumerationField(enumeration=Activity_Project_enumeration,open=True)
    project.help_text = "The project that this activity is associated with"

    def __init__(self, *args, **kwargs):
        super(Activity, self).__init__(*args, **kwargs)
        self.registerFieldType(FieldType("SIMULATION_DESCRIPTION","Simulation Description"), ["project","rationale",])
        self.registerFieldType(FieldType("BASIC","Basic Properties"),['fundingSource','responsibleParties'])

class DateRange(MetadataModel):
    _name = "DateRange"

    duration = models.CharField(max_length=BIG_STRING,blank=True)
    startDate = models.DateField(blank=True,null=True)
    endDate = models.DateField(blank=True,null=True)

    def __init__(self,*args,**kwargs):
        super(DateRange,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"),['duration','startDate','endDate'])

class Calendar(MetadataModel):
    _name = "Calendar"

    units = MetadataEnumerationField(enumeration=CalendarUnitType_enumeration,open=False)
    length = models.IntegerField(blank=True)
    description = models.TextField(blank=True)
    range = MetadataForeignKey("DateRange",related_name="range")

    def __init__(self, *args, **kwargs):
        super(Calendar, self).__init__(*args, **kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"),['units','length','description','range'])

class NumericalActivity(Activity):
    class Meta:
        abstract = True

    _name = "NumericalActivity"

    shortName = models.CharField(max_length=LIL_STRING,blank=False)
    longName = models.CharField(max_length=BIG_STRING,blank=False)
    description = models.TextField(blank=True)

    def __init__(self, *args, **kwargs):
        super(NumericalActivity, self).__init__(*args, **kwargs)
        self.registerFieldType(FieldType("SIMULATION_DESCRIPTION","Simulation Description"),["shortName","longName","description"])

class Experiment(Activity):
    class Meta:
        abstract = True

    _name = "Experiment"

    def __init__(self, *args, **kwargs):
        super(Experiment, self).__init__(*args, **kwargs)

class NumericalRequirement(MetadataModel):
    _name = "NumericalRequirement"

    name = models.CharField(max_length=BIG_STRING,blank=False)
    type = MetadataEnumerationField(enumeration=NumericalRequirementType_enumeration,open=False)
    description = models.TextField()

    def __init__(self,*args,**kwargs):
        super(NumericalRequirement,self).__init__(*args,**kwargs)

    def __unicode__(self):
        name = u'Requirement'
        if self.type:
            name = u'%s: %s' % (name, self.type)
        if self.name:
            name = u'%s: %s' % (name, self.name)
        return name

class NumericalExperiment(Experiment):
    _name = "NumericalExperiment"
    _title = "Numerical Experiment"

    shortName = models.CharField(max_length=LIL_STRING,blank=False)
    longName = models.CharField(max_length=BIG_STRING,blank=False)
    description = models.TextField(blank=True)
    experimentID = models.CharField(max_length=LIL_STRING,blank=True)
    calendar = MetadataForeignKey("Calendar",related_name="calendar")
    numericalRequirements = MetadataManyToManyField("NumericalRequirement",related_name="numericalRequirements")

    def __init__(self,*args,**kwargs):
        super(NumericalExperiment,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("EXPERIMENT_DESCRIPTION","Experiment Description"),["shortName","longName","description","experimentID"])
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["calendar"])
        self.registerFieldType(FieldType("REQUIREMENT","Experiment Requirements"), ["numericalRequirements"])


class Simulation(NumericalActivity):
    class Meta:
        abstract = True

    _name = "Simulation"

    simulationID = models.CharField(max_length=BIG_STRING,blank=True)
    calendar = MetadataForeignKey("Calendar",related_name="calendar")

    def __init__(self,*args,**kwargs):
        super(Simulation,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("SIMULATION_DESCRIPTION","Simulation Description"), ["simulationID"])
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["calendar"])

class SimulationRun(Simulation):
    _name = "SimulationRun"

    pass

    def __init__(self,*args,**kwargs):
        super(SimulationRun,self).__init__(*args,**kwargs)



class ComponentLanguage(MetadataModel):
    name = models.CharField(max_length=BIG_STRING,blank=False)
    # TODO: PROPERTIES
    #componentLanguageProperty = MetadataPropertyField(property=ComponentLanguage_property)

    def __init__(self,*args,**kwargs):
        super(ComponentLanguage, self).__init__(*args, **kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"),["name"])


class SoftwareComponent(DataSource):
    class Meta:
        abstract = True
        
    embedded = models.BooleanField(blank=True)
    embedded.help_text = "An embedded component cannot exist on its own as an atomic piece of software; instead it is embedded within another (parent) component. When embedded equals 'true', the SoftwareComponent has a corresponding piece of software (otherwise it is acting as a 'virtual' component which may be inexorably nested within a piece of software along with several other virtual components)."
    couplingFramework = MetadataEnumerationField(enumeration=CouplingFrameworkType_enumeration,open=True)
    couplingFramework.help_text = "The coupling framework that this entire component conforms to"
    shortName = models.CharField(max_length=LIL_STRING,blank=False)
    shortName.help_text = "the name of the model that is used internally"
    longName = models.CharField(max_length=BIG_STRING,blank=False)
    longName.help_text = "the name of the model that is used externally"
    description = models.TextField(blank=True)
    description.help_text = "a free-text description of the component"
    license = models.CharField(max_length=BIG_STRING,blank=True)
    license.help_text = "the license held by this piece of software"
    # TODO: PROPERTIES (componentProperties, scientificProperties, numericalProperties)
    responsibleParties = MetadataManyToManyField('ResponsibleParty',related_name="responsibleParties")
    releaseDate = models.DateField(null=True)
    releaseDate.help_text = "The date of publication of the software component code (as opposed to the date of publication of the metadata document, or the date of deployment of the model)"
    previousVersion = models.CharField(max_length=BIG_STRING,blank=True)
    fundingSource = models.CharField(max_length=BIG_STRING,blank=True)
    fundingSource.help_text = "The entities that funded this software component"
    citations = MetadataManyToManyField("Citation",related_name="citations")
    onlineResource = models.URLField(verify_exists=False)
    componentLanguage = MetadataForeignKey("ComponentLanguage",related_name="componentLanguage")

    def __init__(self,*args,**kwargs):
        super(SoftwareComponent, self).__init__(*args, **kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"),["embedded","couplingFramework","license","responsibleParties","releaseDate","componentLanguage","fundingSource","previousVersion"])
        self.registerFieldType(FieldType("MODEL_DESCRIPTION","Component Description"),["shortName","longName","description", "citations", "onlineResource"])


class ResponsibleParty(MetadataModel):
    _name = "ResponsibleParty"
    _title = "Responsible Party"

    individualName = models.CharField(max_length=LIL_STRING,blank=False)
    organizationName = models.CharField(max_length=LIL_STRING,blank=False)
    role = MetadataEnumerationField(enumeration=ResponsiblePartyRole_enumeration,open=True)

    positionName = models.CharField(max_length=LIL_STRING,blank=True)
    contactInfo = models.CharField(max_length=LIL_STRING,blank=True)

    def __init__(self,*args,**kwargs):
        super(ResponsibleParty,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["individualName","organizationName","role","positionName","contactInfo"])

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
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["title","alternateTitle","edition","editionDate","identifier","otherCitationDetails","collectiveTitle","isbn","issn"])

    def __unicode__(self):
        return u'%s: %s' % (self.getName(), self.title)

class Timing(MetadataModel):
    units = MetadataEnumerationField(enumeration=TimingUnits_enumeration,open=False)
    variableRate = models.BooleanField(blank=True)
    start = models.DateTimeField(blank=True,null=True)
    end = models.DateTimeField(blank=True,null=True)
    rate = models.IntegerField(blank=True,null=True)

    def __init__(self,*args,**kwargs):
        super(Timing,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["units","variableRate","start","end","rate"])

class ModelComponent(SoftwareComponent):
    type = MetadataEnumerationField(enumeration=ModelComponentType_enumeration,open=True)
    timing = MetadataForeignKey("Timing",related_name="timing")

    def __init__(self,*args,**kwargs):
        super(ModelComponent,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("MODEL_DESCRIPTION","Component Description"), ["type"])
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["timing"])

##############

# TODO: move these functions into the MetadataEnumerationField.__init__ fn
try:
    DataPurpose_enumeration.loadEnumerations()
    CouplingFrameworkType_enumeration.loadEnumerations()
    ResponsiblePartyRole_enumeration.loadEnumerations()
    ModelComponentType_enumeration.loadEnumerations()
    TimingUnits_enumeration.loadEnumerations()
    Activity_Project_enumeration.loadEnumerations()
    CalendarUnitType_enumeration.loadEnumerations()
    NumericalRequirementType_enumeration.loadEnumerations()
except:
    # this will fail on syncdb; once I move to South, it won't matter
    pass

