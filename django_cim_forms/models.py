import django.forms.widgets
import django.forms.fields
# module imports

from django.db import models, DatabaseError
from django.utils.functional import curry
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

class MetadataCVField_bak(models.ManyToManyField):

    def __init__(self,*args,**kwargs):
        cvClass = kwargs.pop('cv',None)
        # TODO: again, not sure why I can't call this from here?
        #if cvClass:
        #    cvClass.loadCV()
        kwargs["blank"] = True
        kwargs["null"] = True
        super(MetadataCVField_bak,self).__init__(cvClass,**kwargs)

class _MetadataCVWidget(django.forms.widgets.MultiWidget):
    def __init__(self,*args,**kwargs):

        self.shortName = kwargs.pop("shortName",None)
        self.longName = kwargs.pop("longName",None)
        self.value_choices = kwargs.pop("values",[])
        widgets = (
            django.forms.fields.TextInput(attrs={'readonly':'readonly'}),
            django.forms.fields.TextInput(attrs={'readonly':'readonly'}),
            django.forms.fields.Select(choices=self.value_choices),
        )

        
        super(_MetadataCVWidget, self).__init__(widgets,*args,**kwargs)        

    # TODO: CHECK THIS
    def decompress(self, value):
        print "DECOMPRESS"
        print value
        if value:
            return [value,None,None]
        return [self.shortName,self.longName,None]


class _MetadataCVFormField(django.forms.fields.MultiValueField):
    widget = _MetadataCVWidget
    
    def __init__(self,*args,**kwargs):
        self.cv = kwargs.pop("cv",None)
        shortName = ""
        longName = ""
        value_choices = []
        try:
            self.cv_model=self.cv.objects.get(pk=18)
            shortName = self.cv_model.shortName
            longName = self.cv_model.longName
            value_choices = self.cv_model.values
        except DatabaseError:
            print "YOU MESSED UP!"

        fields = (
            django.forms.fields.CharField(label="short name",initial=shortName),    # CV property: shortName
            django.forms.fields.CharField(label="long name",initial=longName),      # CV property: longName
            django.forms.fields.ChoiceField(label="value",choices=value_choices),   # choices for CV Property: values
        )
        super(_MetadataCVFormField,self).__init__(fields,*args,**kwargs)
        # make sure the widget renders what this formfield contains...
        self.widget = _MetadataCVWidget(shortName=shortName,longName=longName,values=value_choices)

    # TODO: CHECK THIS
    def compress(self, data_list):
        print "COMPRESS"
        if data_list:
            data = { "shortName" : data_list[0], "longName" : data_list[1], "value" : data_list[2]}
            #return join data somehow into a string
            return data
        return { "shortName" : None, "longName" : None, "value" : None}

class MetadataCVField(models.Field):

    cv = None

    def __init__(self,*args,**kwargs):
        self.cv = kwargs.pop("cv",None)
        super(MetadataCVField,self).__init__(*args,**kwargs)

    def formfield(self,*args,**kwargs):

#        defaults = {'form_class': _MetadataCVFormField}
#        defaults.update(kwargs)
#        super(MetadataCVField,self).formfield(**defaults)
        return _MetadataCVFormField(cv=self.cv)

    def get_internal_type(self):
        return 'MetadataCVField'

class MetadataEnablerField(models.BooleanField):

    _fieldsToEnable = []
    _startEnabled = False

    def __init__(self,*args,**kwargs):
        fieldsToEnable = kwargs.pop("fields",None)
        startEnabled = kwargs.pop("startEnabled",False)
        super(MetadataEnablerField,self).__init__(*args,**kwargs)
        self._fieldsToEnable = fieldsToEnable
        self._startEnabled = startEnabled

    def getFieldsToEnable(self):
        return self._fieldsToEnable

    def getStartEnabled(self):
        return self._startEnabled
      


class MetadataDocumentField(models.ManyToManyField):

    _app_name = ""
    _model_name = ""

    def __init__(self,*args,**kwargs):
        appName = kwargs.pop("appName","django_cim_forms")
        modelName = kwargs.pop("modelName",None)
        if not modelName:
            raise MetadataError("you must specify the appName and modelName for a MetadataDocumentField")
        super(MetadataDocumentField,self).__init__(*args,**kwargs)
        self._app_name = appName.lower()
        self._model_name = modelName.lower()

    def getAppName(self):
        return self._app_name

    def getModelName(self):
        return self._model_name
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
        self.help_text = None # this is the default setting; it can be overridden in the class definitions below

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
        self.help_text = None # this is the default setting; it can be overridden in the class definitions below

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


    _name = ""  # the name of the model class; THIS MUST BE UNIQUE!
    _title = "" # the title (to display) of the model class

    _fieldTypes = EnumeratedTypeList([])
    _fieldTypeOrder = None
    _fieldsByType = {}

    # every model has a guid
    guid = models.CharField(max_length=64,editable=False,blank=True,unique=True)

    def getName(self):
        return self._name

    def getTitle(self):
        return self._title

    def getGuid(self):
        return self.guid

    def setFieldTypeOrder(self,order):
        self._fieldTypeOrder = order
        
    def __init__(self,*args,**kwargs):
        super(MetadataModel,self).__init__(*args,**kwargs)
        if not self.guid:
            self.guid = str(uuid4())

    def registerFieldType(self,fieldType,fields):
##        # first make sure the fields exist...
##        if not all(f in [field.name for field in self._meta.fields] for f in fields):
##            msg = "'%s' is an invalid set of fields for %s" % (fields,self.getName())
##            raise MetadataError(msg)
        
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
        if self._fieldTypeOrder:
            # if an order is defined, return _fieldTypes according to that order
            return self._fieldTypes.sort(key=lambda fieldType: EnumeratedTypeList.comparator(fieldType,self._fieldTypeOrder))
        return self._fieldTypes

    def getActiveFieldTypes(self):
        orderedFieldTypes = self.getActiveFieldTypes()
        #return [fieldType for fieldType in list(self._fieldTypes) if (fieldType.getType() in self._fieldsByType)]
        return [fieldType for fieldType in orderedFieldTypes if (fieldType.getType() in self._fieldsByType)]

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
    _enum = ['CMIP5','AMIP','TAMIP', 'CASCADE', "DCMIP"]

class CalendarUnitType_enumeration(MetadataEnumeration):
    _enum = ['days','months','years']
    
class NumericalRequirementType_enumeration(MetadataEnumeration):
    _enum = ['Initial Condition','Boundary Condition','Output Requirement','SpatioTemporal Constraint']

class ConnectionType_enumeration(MetadataEnumeration):
    _enum = ['CCSM Flux Coupler','ESMF','FMS','Files','MCT','OASIS3','OASIS4','Shared Memory','Embedded']

class SpatialRegriddingDimensionType_enumeration(MetadataEnumeration):
    _enum = ['1D','2D','3D']

class SpatialRegriddingStandardMethodType_enumeration(MetadataEnumeration):
    _enum = ['linear','near-neighbour','cubic','conservative-first-order','conservative-second-order','conservative','non-conservative']

class TimeMappingType_enumeration(MetadataEnumeration):
    _enum = ['TimeAccumulation','TimeAverage','LastAvailable','TimeInterpolation','Exact']

class ConformanceType_enumeration(MetadataEnumeration):
    _enum = ['not conformant','standard config','via inputs','via model mods','combination']

class FrequencyType_enumeration(MetadataEnumeration):
    _enum = ['daily','monthly','yearly','hourly']

class LogicalRelationshipType_enumeration(MetadataEnumeration):
    _enum = ['AND','OR','XOR']

class DataStatusType_enumeration(MetadataEnumeration):
    _enum = ['complete','metadataOnly','continuouslySupplemented']
    
class DataHierarchyType_enumeration(MetadataEnumeration):
    _enum = ['run','stream','institute','model','product','experiment','frequency','realm','variable','ensembleMember']
#####


class DataSource(MetadataModel):
    class Meta:
        abstract = False#True

    _fieldsByType = {}

    purpose = MetadataEnumerationField(enumeration=DataPurpose_enumeration,open=True)

    def __init__(self,*args,**kwargs):
        super(DataSource, self).__init__(*args, **kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"),["purpose"])

class ComponentProperty(MetadataModel):
    # a ComponentProperty is a special type of model
    # it is bound to a CV

    class Meta:
        abstract = True

    _name = "ComponentProperty"
    _title = "Component Property"

    _fieldsByType = {}

    cv = None

    shortName = models.CharField(max_length=BIG_STRING,blank=False)
    longName  = models.CharField(max_length=BIG_STRING,blank=True)
    value = models.CharField(max_length=BIG_STRING,blank=True,null=True)

    def __unicode__(self):
        name = u'%s' % self.getTitle()
        if self.longName:
            name = u'%s' % self.longName
        elif self.shortName:
            name = u'%s' % self.shortName
        if self.value:
            name = u'%s: %s' % (name,self.value)
        return name

    def __init__(self,*args,**kwargs):
        cv = kwargs.pop("cv",None)
        super(ComponentProperty, self).__init__(*args, **kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"),["shortName","longName","value"])

        self._meta.get_field_by_name("shortName")[0].default = cv.shortName
        self._meta.get_field_by_name("longName")[0].default = cv.longName
        self._meta.get_field_by_name("value")[0]._choices = cv.values
        self._meta.get_field_by_name("value")[0].widget = django.forms.Select()




    

class Activity(MetadataModel):
    class Meta:
        abstract = True

    _fieldsByType = {}

    responsibleParties = MetadataManyToManyField('ResponsibleParty',related_name="responsibleParties")
    responsibleParties.help_text = "The point of contact(s) for this activity.This includes, among others, the principle investigator."
    fundingSource = models.CharField(max_length=BIG_STRING,blank=True)
    fundingSource.help_text = "The entities that funded this activity."
    rationale = models.TextField(blank=True)
    rationale.help_text = "For what purpose is this activity being performed?"
    project = MetadataEnumerationField(enumeration=Activity_Project_enumeration,open=True)
    project.help_text = "The project that this activity is associated with"

    def __init__(self, *args, **kwargs):
        super(Activity, self).__init__(*args, **kwargs)
        
        self.registerFieldType(FieldType("BASIC","Basic Properties"),['fundingSource','responsibleParties'])

class DateRange(MetadataModel):
    _name = "DateRange"

    _fieldsByType = {}

    duration = models.CharField(max_length=BIG_STRING,blank=True)
    startDate = models.DateField(blank=True,null=True)
    endDate = models.DateField(blank=True,null=True)

    def __init__(self,*args,**kwargs):
        super(DateRange,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"),['duration','startDate','endDate'])

class Calendar(MetadataModel):
    _name = "Calendar"

    _fieldsByType = {}

    units = MetadataEnumerationField(enumeration=CalendarUnitType_enumeration,open=False)
    length = models.IntegerField(blank=True)
    description = models.TextField(blank=True)
    range = MetadataForeignKey("DateRange",related_name="range")

    def __init__(self, *args, **kwargs):
        super(Calendar, self).__init__(*args, **kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"),['units','length','description','range'])

class DataObject(DataSource):
    _name = "DataObject"
    _title = "Data Object"

    _fieldsByType = {}

    dataStatus = MetadataEnumerationField(enumeration=DataStatusType_enumeration,open=False,blank=True)
    dataStatus.help_text = "The current status of the data - is it complete, or is this metadata description all that is available, or is the data continuously supplemented."
    acronym = models.CharField(max_length=LIL_STRING,blank=False)
    description = models.TextField(blank=True)
    hierarchyLevelName = MetadataEnumerationField(enumeration=DataHierarchyType_enumeration,open=True,blank=True)
    hierarchyLevelName.help_text = "What level in the data hierarchy (constructed by the self-referential parent/child aggregations) is this DataObject."


    def __init__(self, *args, **kwargs):
        super(DataObject, self).__init__(*args, **kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"),["dataStatus","acronym","description","hierarchyLevelName"])

    def __unicode__(self):
        name = self.getName()
        if self.acronym:
            name = u'%s: %s' % (name, self.acronym)
        return name

class NumericalActivity(Activity):
    class Meta:
        abstract = True

    _name = "NumericalActivity"

    _fieldsByType = {}

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

    _fieldsByType = {}

    def __init__(self, *args, **kwargs):
        super(Experiment, self).__init__(*args, **kwargs)
        self.registerFieldType(FieldType("EXPERIMENT_DESCRIPTION","Experiment Description"), ["project","rationale",])

class NumericalRequirement(MetadataModel):
    _name = "NumericalRequirement"
    _title = "Numerical Requirement"
    
    _fieldsByType = {}

    requirementId = models.CharField(max_length=LIL_STRING,blank=False)
    name = models.CharField(max_length=BIG_STRING,blank=False)
    type = MetadataEnumerationField(enumeration=NumericalRequirementType_enumeration,open=False)
    description = models.TextField()
    sources = MetadataDocumentField("DataObject",modelName="dataobject",blank=True,null=True)
    sources.help_text = None

    def __init__(self,*args,**kwargs):
        super(NumericalRequirement,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["requirementId","name","type","description","sources"])

    def __unicode__(self):
        name = u'Requirement'
        if self.type:
            name = u'%s (%s)' % (name, self.type)
        if self.name:
            name = u'%s: "%s"' % (name, self.name)
        return name

class CompositeNumericalRequirement(NumericalRequirement):
    _name = "CompositeNumericalRequirement"
    _title = "Numerical Requirement"

    _fieldsByType = {}


    isComposite = MetadataEnablerField(fields=["requirementOptions","sources"])
    isComposite.help_text = "is this requirement composed of other child requirements?"

    requirementOptions = MetadataManyToManyField("RequirementOption",related_name="requirementOptions")
    #requirementOptions.verbose_name = "sub-requirements"

    def __init__(self,*args,**kwargs):
        super(NumericalRequirement,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["isComposite","requirementOptions"])


class RequirementOption(MetadataModel):
    _name = "RequirementOption"
    _title = "Requirement Option"

    _fieldsByType = {}

    optionRelationship = MetadataEnumerationField(enumeration=LogicalRelationshipType_enumeration,open=False)
    optionRelationship.help_text = "Describes how this optional (child) requirement is related to its sibling requirements.  For example, a NumericalRequirement could consist of a set of optional requirements each with an \"OR\" relationship meaning use this boundary condition _or_ that one."
    requirement = MetadataForeignKey("NumericalRequirement",related_name="requirement")
    requirement.help_text = "A NumericalRequirement that is being used as a set of related requirements; For example if a requirement is to use 1 of 3 boundary conditions, then that \"parent\" requirement would have three \"child\" RequirmentOptions (each of one with the XOR optionRelationship)."

    def __unicode__(self):
        name = u'Requirement Option'
        if self.optionRelationship:
            name = u'%s: %s' % (name, self.type)
        if self.requirement:
            name = u'%s: %s' % (name, self.requirement)
        return name

    def __init__(self,*args,**kwargs):
        super(RequirementOption,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["optionRelationship","requirement"])

class NumericalExperiment(Experiment):
    _name = "NumericalExperiment"
    _title = "Numerical Experiment"

    _fieldsByType = {}

    shortName = models.CharField(max_length=LIL_STRING,blank=False)
    longName = models.CharField(max_length=BIG_STRING,blank=False)
    description = models.TextField(blank=True)
    experimentID = models.CharField(max_length=LIL_STRING,blank=False)
    calendar = MetadataForeignKey("Calendar",related_name="calendar")
    numericalRequirements = MetadataManyToManyField("CompositeNumericalRequirement",related_name="numericalRequirements")

    def __init__(self,*args,**kwargs):
        super(NumericalExperiment,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("EXPERIMENT_DESCRIPTION","Experiment Description"),["shortName","longName","description","experimentID"])
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["calendar"])
        self.registerFieldType(FieldType("REQUIREMENT","Numerical Requirements"), ["numericalRequirements"])

class TimeTransformation(MetadataModel):
    _name = "TimeTransformation"
    _fieldsByType = {}

    mappingType = MetadataEnumerationField(enumeration=TimeMappingType_enumeration,open=True)
    mappingType.help_text = "Enumerates the different ways that time can be mapped when transforming from one field to another."
    description = models.TextField(blank=True)

    def __init__(self,*args,**kwargs):
        super(TimeTransformation,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["mappingType","description"])

class CouplingEndPoint(MetadataModel):
    _name = "CouplingEndPoint"

    _fieldsByType = {}

    dataSource = models.CharField(max_length=BIG_STRING,blank=False)
    # TODO: THIS SHOULD BE AN "IDENTIFIER" CLASS
    instanceID = models.CharField(max_length=LIL_STRING,blank=True)
    instanceID.help_text = "If the same datasource is used more than once in a coupled model then a method for identifying which particular instance is being referenced is needed (for BFG)."

    def __init__(self,*args,**kwargs):
        super(CouplingEndPoint,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["dataSource","instanceID"])
        
class Coupling(MetadataModel):
    _name = "Coupling"
    _title = "Coupling"

    _fieldsByType = {}

    purpose = MetadataEnumerationField(enumeration=DataPurpose_enumeration,open=True)
    fullySpecified = models.BooleanField()
    fullySpecified.help_text="If \"true\" then the coupling is fully-specified.  If \"false\" then not every Connection has been described within the coupling."
    description = models.TextField(blank=True)
    description.help_text="A free-text description of the coupling"
    connectionType = MetadataEnumerationField(enumeration=ConnectionType_enumeration,open=True)
    connectionType.help_text="Describes the method of coupling"
    timeProfile = MetadataForeignKey("Timing",related_name="timeProfile")
    timeProfile.help_text="Describes how often the coupling takes place."
    timeLag = MetadataForeignKey("TimeLag",related_name="timeLag")
    timeLag.help_text="The coupling field used in the target at a given time corresponds to a field produced by the source at a previous time."
    spatialRegridding = MetadataManyToManyField("SpatialRegridding",related_name="spatialRegridding")
    spatialRegridding.help_text="Characteristics of the scheme used to interpolate a field from one grid (source grid) to another (target grid)"
    timeTransformation = MetadataForeignKey("TimeTransformation",related_name="timeTransformation")
    timeTransformation.help_text="Temporal transformation performed on the coupling field before or after regridding onto the target grid. "
    couplingSource = MetadataForeignKey("CouplingEndPoint",related_name="couplingSource")
    couplingTarget = MetadataForeignKey("CouplingEndPoint",related_name="couplingTarget")
    priming = models.CharField(max_length=BIG_STRING,blank=False)
    priming.help_text = "A priming source is one that is active on the first available timestep only (before \"proper\" coupling can ocurr).  It can either be described here explicitly, or else a separate coupling/connection with a timing profile that is active on only the first timestep can be created."
    
    def __init__(self,*args,**kwargs):
        super(Coupling,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["purpose","fullySpecified","description","timeProfile","timeLag","spatialRegridding","timeTransformation","couplingSource","couplingTarget"])

    def __unicode__(self):
        name = u'%s' % self.getName()
        if self.connectionType:
            name = u'%s: %s' % (name, self.connectionType)
        return name

class Conformance(MetadataModel):
    _name = "Conformance"
    _title = "Conformance"

    _fieldsByType = {}

    conformant = models.BooleanField()
    conformant.help_text = "Records whether or not this conformance satisfies the requirement.  A simulation should have at least one conformance mapping to every experimental requirement.  If a simulation satisfies the requirement - the usual case - then conformant should have a value of \"true.\"  If conformant is true but there is no reference to a source for the conformance, then we can assume that the simulation conforms to the requirement _naturally_, that is without having to modify code or inputs. If a simulation does not conform to a requirement then conformant should be set to \"false.\""
    type = MetadataEnumerationField(enumeration=ConformanceType_enumeration,open=False)
    type.help_text = "Describes the method that this simulation conforms to an experimental requirement (in case it is not specified by the change property of the reference to the source of this conformance)"
    description = models.TextField(blank=True)
    frequency = MetadataEnumerationField(enumeration=FrequencyType_enumeration,open=True)
    # TODO: DOUBLE-CHECK THAT THIS WORKS W/ ABSTRACT CLASSES
    requirements = models.ManyToManyField("NumericalRequirement")
    requirements.help_text="Points to the NumericalRequirement that the simulation in question is conforming to."
    sources = models.ManyToManyField("DataSource")
    sources.help_text = "Points to the DataSource used to conform to a particular Requirement.   This may be part of an activity::simulation or a software::component.  It can be either a DataObject or a SoftwareComponent or a ComponentProperty.  It could also be by using particular attributes of, say, a SoftwareComponent, but in that case the recommended practise is to reference the component and add appropriate text in the conformance description attribute."
    
    def __init__(self,*args,**kwargs):
        super(Conformance,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["conformant","type","description","frequency"])
        self.registerFieldType(FieldType("REQUIREMENTS","Experimental Requirements"), ["requirements"])
        self.registerFieldType(FieldType("SOURCES","Conformant Methods"), ["sources"])

    def __unicode__(self):
        name = u'%s' % self.getName()
        # TODO: map requirements and sources to (truncated) lists
##        if self.requirements:
##            name = u'%s: %s' % (name, "requirements")
##        if self.sources:
##            name = u'%s: %s' % (name, "sources")
        return name


class Simulation(NumericalActivity):
    class Meta:
        abstract = True

    _name = "Simulation"

    _fieldsByType = {}

    simulationID = models.CharField(max_length=BIG_STRING,blank=False)
    calendar = MetadataForeignKey("Calendar",related_name="calendar")
    inputs = MetadataManyToManyField("Coupling",related_name="inputs")
    inputs.help_text="implemented as a mapping from a source to target; can be a forcing file, a boundary condition, etc."

    outputs = MetadataManyToManyField("DataObject",related_name="outputs")
    restarts = MetadataManyToManyField("DataObject",related_name="restarts")
    
    conformances = MetadataManyToManyField("Conformance",related_name="conformances")

    def __init__(self,*args,**kwargs):
        super(Simulation,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("SIMULATION_DESCRIPTION","Simulation Description"), ["simulationID","project","rationale"])        
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["calendar"])
        self.registerFieldType(FieldType("COUPLINGS","Inputs & Outputs"),["inputs","outputs","restarts"])
        self.registerFieldType(FieldType("CONFORMANCES","Conformances"), ["conformances"])

class SimulationRun(Simulation):
    _name = "SimulationRun"

    _fieldsByType = {}

    pass

    def __init__(self,*args,**kwargs):
        super(SimulationRun,self).__init__(*args,**kwargs)



class ComponentLanguage(MetadataModel):
    name = models.CharField(max_length=BIG_STRING,blank=False)
    # TODO: PROPERTIES
    #componentLanguageProperty = MetadataPropertyField(property=ComponentLanguage_property)

    _fieldsByType = {}

    def __init__(self,*args,**kwargs):
        super(ComponentLanguage, self).__init__(*args, **kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"),["name"])


class SoftwareComponent(DataSource):
    class Meta:
        abstract = True

    _fieldsByType = {}

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
        self.registerFieldType(FieldType("BASIC","Basic Properties"),["couplingFramework","license","releaseDate","componentLanguage","citations", "onlineResource","fundingSource","previousVersion","responsibleParties"])
        self.registerFieldType(FieldType("MODEL_DESCRIPTION","Component Description"),["shortName","longName","description", "embedded",])


class ResponsibleParty(MetadataModel):
    _name = "ResponsibleParty"
    _title = "Responsible Party"

    _fieldsByType = {}

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

    _fieldsByType = {}

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

    _fieldsByType = {}

    units = MetadataEnumerationField(enumeration=TimingUnits_enumeration,open=False)
    variableRate = models.BooleanField(blank=True)
    start = models.DateTimeField(blank=True,null=True)
    end = models.DateTimeField(blank=True,null=True)
    rate = models.IntegerField(blank=True,null=True)

    def __init__(self,*args,**kwargs):
        super(Timing,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["units","variableRate","start","end","rate"])

class TimeLag(MetadataModel):
    _fieldsByType = {}

    units = MetadataEnumerationField(enumeration=TimingUnits_enumeration,open=False)
    value = models.IntegerField()

    def __init__(self,*args,**kwargs):
        super(TimeLag,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["units","value"])

class SpatialRegriddingUserMethod(MetadataModel):
    _fieldsByType = {}

    name = models.CharField(max_length=BIG_STRING,blank=False)
    file = models.CharField(max_length=BIG_STRING,blank=True)

    def __init__(self,*args,**kwargs):
        super(SpatialRegriddingUserMethod,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["name","file"])


class SpatialRegridding(MetadataModel):

    _name = "SpatialRegridding"

    _fieldsByType = {}

    spatialRegriddingDimension = MetadataEnumerationField(enumeration=SpatialRegriddingDimensionType_enumeration,open=False,blank=True)
    spatialRegriddingStandardMethod = MetadataEnumerationField(enumeration=SpatialRegriddingStandardMethodType_enumeration,open=False)
    spatialRegriddingUserMethod = MetadataForeignKey("SpatialRegriddingUserMethod",related_name="spatialRegriddingUserMethod")
    spatialRegriddingUserMethod.help_text = "Allows users to bypass the SpatialRegriddingStandardMethod and instead provide a set of weights and addresses for regridding via a file."

    def __init__(self,*args,**kwargs):
        super(SpatialRegridding,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"), ["spatialRegriddingDimension","spatialRegriddingStandardMethod","spatialRegriddingUserMethod"])

    def __unicode__(self):
        name = u'%s' % self.getName()
        if self.spatialRegriddingDimension:
            name = u'%s: %s' % (name, self.spatialRegriddingDimension)
        if self.spatialRegriddingStandardMethod:
            name = u'%s: %s' % (name, self.spatialRegriddingStandardMethod)
        elif self.spatialRegriddingUserMethod:
            name = u'%s: %s' % (name, self.spatialRegriddingUserMethod)
        return name

class ModelComponent(SoftwareComponent):

    _fieldsByType = {}

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
    ConnectionType_enumeration.loadEnumerations()
    SpatialRegriddingDimensionType_enumeration.loadEnumerations()
    SpatialRegriddingStandardMethodType_enumeration.loadEnumerations()
    TimeMappingType_enumeration.loadEnumerations()
    ConformanceType_enumeration.loadEnumerations()
    FrequencyType_enumeration.loadEnumerations()
    LogicalRelationshipType_enumeration.loadEnumerations()
    DataStatusType_enumeration.loadEnumerations()
    DataHierarchyType_enumeration.loadEnumerations()
except:
    # this will fail on syncdb; once I move to South, it won't matter
    pass

