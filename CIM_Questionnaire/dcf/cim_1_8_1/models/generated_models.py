# auto-generated: 3 June 2013, 19:07
# module: cim_1_8_1.models

from dcf.models import *
from dcf.cim_1_8_1.models import *


#########################################
# this registers this version w/ the db #
#########################################

MetadataVersion.factory(
    name   =   "CIM",
    number =   "1.8.1",
)



#############################
# here are the enumerations #
#############################

class ProcessorType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ProcessorType"
    _title       = "Processor Type"
    _description = "A list of known compilers."

    CHOICES = [
        "NEC",
        "Sparc",
        "Intel",
        "Intel IA-64",
        "Intel EM64T",
        "AMD X86_64",
        "Other Intel",
        "Other AMD",

    ]

    open     = True
    nullable = False
    multi    = False


class SpatialRegriddingDimensionType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "SpatialRegriddingDimensionType"
    _title       = "Spatial Regridding Dimension Type"
    _description = "Is the regridding 2D or 3D?"

    CHOICES = [
        "1D",
        "2D",
        "3D",

    ]

    open     = False
    nullable = False
    multi    = False


class MachineVendorType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "MachineVendorType"
    _title       = "Machine Vendor Type"
    _description = "A list of organisations that create machines."

    CHOICES = [
        "ACTION",
        "Appro International",
        "Bull SA",
        "ClusterVision/Dell",
        "ClusterVision/IBM",
        "Cray Inc",
        "DALCO AG Switzerland",
        "Dawning",
        "Dell",
        "DELL/ACS",
        "Dell/Sun/IBM",
        "Fujitsu",
        "Hewlett-Packard",
        "Hitachi",
        "IBM",
        "Intel",
        "Koi Computers",
        "Lenovo",
        "Linux Networx",
        "NEC",
        "NEC/Sun",
        "NUDT",
        "Pyramid Computer",
        "Raytheon-Aspen Systems/Appro",
        "Self-made",
        "SGI",
        "SKIF/T-Platforms",
        "Sun Microsystems",
        "T-Platforms",

    ]

    open     = True
    nullable = False
    multi    = False


class InterconnectType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "InterconnectType"
    _title       = "Interconnect Type"
    _description = "A list of known compilers."

    CHOICES = [
        "Myrinet",
        "Quadrics",
        "Gigabit Ethernet",
        "Infiniband",
        "Mixed",
        "NUMAlink",
        "SP Switch",
        "Cray Interconnect",
        "Fat Tree",

    ]

    open     = True
    nullable = False
    multi    = False


class UnitType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "UnitType"
    _title       = "Unit Type"
    _description = "A list of scientific units."

    CHOICES = [
        "meter",
        "hectopascal",
        "pascal",
        "sigma",
        "degrees_c",

    ]

    open     = True
    nullable = False
    multi    = False


class DocumentStatusType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "DocumentStatusType"
    _title       = "Document Status Type"
    _description = "The current state of the CIM document: complete, incomplete, or in-progress."

    CHOICES = [
        "complete",
        "incomplete",
        "in-progress",

    ]

    open     = False
    nullable = False
    multi    = False


class CalendarUnit(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "CalendarUnit"
    _title       = "Calendar Unit"
    _description = "Describes the units that a given calendar uses."

    CHOICES = [
        "days",
        "months",
        "years",

    ]

    open     = False
    nullable = False
    multi    = False


class RelationshipDirectionType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "RelationshipDirectionType"
    _title       = "Relationship Direction Type"
    _description = "The direction of a relationship: source to target, or target to source"

    CHOICES = [
        "toTarget",
        "fromTarget",

    ]

    open     = False
    nullable = False
    multi    = False

class OperatingSystemType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "OperatingSystemType"
    _title       = "Operating System Type"
    _description = "A list of common operating systems."

    CHOICES = [
        "Linux",
        "AIX",
        "Darwin",
        "Unicos",
        "Irix64",
        "SunOS",

    ]

    open     = True
    nullable = False
    multi    = False


class DataPurpose(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "DataPurpose"
    _title       = "Data Purpose"
    _description = "Describes what purpose a particular simulation input has: ancillary file, boundary condition, or initial condition."

    CHOICES = [
        "ancillaryFile",
        "boundaryCondition",
        "initialCondition",

    ]

    open     = False
    nullable = False
    multi    = False

class EntryPointType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "EntryPointType"
    _title       = "Entry Point Type"
    _description = "Describes the intended use of an EntryPoint (subroutine).  This is required for ESMF models."

    CHOICES = [
        "init",
        "run",
        "finalise",

    ]

    open     = False
    nullable = False
    multi    = False


class TimingUnits(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "TimingUnits"
    _title       = "Timing Units"
    _description = ""

    CHOICES = [
        "seconds",
        "minutes",
        "hours",
        "days",
        "months",
        "years",
        "decades",
        "centuries",

    ]

    open     = False
    nullable = False
    multi    = False

class LogicalRelationshipType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "LogicalRelationshipType"
    _title       = "Logical Relationship Type"
    _description = ""

    CHOICES = [
    "AND",
        "OR",
        "XOR",

    ]

    open     = False
    nullable = False
    multi    = False

class ComponentPropertyIntentType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ComponentPropertyIntentType"
    _title       = "Component Property Intent Type"
    _description = "Describes how a property is used by a component; either as an input argument, an output argument, or an inout argument."

    CHOICES = [
    "in",
        "out",
        "inout",

    ]

    open     = False
    nullable = False
    multi    = False

class DocumentRelationshipType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "DocumentRelationshipType"
    _title       = "Document Relationship Type"
    _description = "The types of relationships that can be specified within a document's genealogy."

    CHOICES = [
    "similarTo",
        "other",
        "laterVersionOf",
        "previousVersionOf",
        "fixedVersionOf",

    ]

    open     = False
    nullable = False
    multi    = False


class MachineType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "MachineType"
    _title       = "Machine Type"
    _description = ""

    CHOICES = [
    "Parallel",
        "Vector",
        "Beowulf",

    ]

    open     = False
    nullable = False
    multi    = False


class CompilerType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "CompilerType"
    _title       = "Compiler Type"
    _description = "A list of known compilers."

    CHOICES = [
    "Absoft",
        "Intel",
        "Lahey",
        "NAG",
        "Pathscale",
        "Portland PGI",
        "Silverfrost",

    ]

    open     = True
    nullable = False
    multi    = False

class QualityIssueType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "QualityIssueType"
    _title       = "Quality Issue Type"
    _description = ""

    CHOICES = [
    "metadata",
        "data_format",
        "data_content",
        "data_indexing",
        "science",

    ]

    open     = False
    nullable = False
    multi    = False


class QualitySeverityType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "QualitySeverityType"
    _title       = "Quality Severity Type"
    _description = ""

    CHOICES = [
    "cosmetic",
        "minor",
        "major",

    ]

    open     = False
    nullable = False
    multi    = False


class CIM_ResultType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "CIM_ResultType"
    _title       = "CIM Result Type"
    _description = ""

    CHOICES = [
    "plot",
        "document",
        "logfile",

    ]

    open     = False
    nullable = False
    multi    = False

class QualityStatusType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "QualityStatusType"
    _title       = "Quality Status Type"
    _description = ""

    CHOICES = [
    "reported",
        "confirmed",
        "partially_resolved",
        "resolved",

    ]

    open     = False
    nullable = False
    multi    = False


class CIM_ScopeCodeType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "CIM_ScopeCodeType"
    _title       = "CIM Scope Code Type"
    _description = "Relatively few of the scope codes defined in ISO19115 are relevant to CIM.  I have therefore added a number of additional scope types - these are indicated with a trailing asterisk."

    CHOICES = [
    "metadata",
        "dataset",
        "software",
        "service",
        "model",
        "modelComponent",
        "simulation",
        "experiment",
        "numericalRequirement",
        "ensemble",
        "file",

    ]

    open     = False
    nullable = False
    multi    = False


class CIM_FeatureType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "CIM_FeatureType"
    _title       = "CIM Feature Type"
    _description = ""

    CHOICES = [
    "file",
        "diagnostic",

    ]

    open     = False
    nullable = False
    multi    = False

class DataRestrictionScopeType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "DataRestrictionScopeType"
    _title       = "Data Restriction Scope Type"
    _description = "The method by which a data object is restricted."

    CHOICES = [
    "metadataAccessConstraint",
        "metadataUseConstraint",
        "dataAccessConstraint",
        "dataUseConstraint",

    ]

    open     = False
    nullable = False
    multi    = False

class DataAccessType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "DataAccessType"
    _title       = "Data Access Type"
    _description = "The  format that data is stored in."

    CHOICES = [
    "CD-ROM",
        "DiskDB",
        "DVD",
        "Microfiche",
        "OnlineFileHTTP",
        "OnlineFileFTP",

    ]

    open     = False
    nullable = False
    multi    = False

class TimeMappingType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "TimeMappingType"
    _title       = "Time Mapping Type"
    _description = "Enumerates the different ways that time can be mapped when transforming from one field to another."

    CHOICES = [
    "TimeAccumulation",
        "TimeAverage",
        "LastAvailable",
        "TimeInterpolation",
        "Exact",

    ]

    open     = True
    nullable = False
    multi    = False

class StatisticalModelComponentType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "StatisticalModelComponentType"
    _title       = "Statistical Model Component Type"
    _description = "An enumeration of types of StatisticalModelComponent.  This includes more than just statistical downscaling techniques; it can be used for forecast or impact models too."

    CHOICES = [
    "downscaling",
        "impact",
        "forecast",

    ]

    open     = True
    nullable = False
    multi    = False

class CouplingFrameworkType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "CouplingFrameworkType"
    _title       = "Coupling Framework Type"
    _description = "Is the regridding 2D or 3D?"

    CHOICES = [
    "BFG",
        "ESMF",
        "OASIS",

    ]

    open     = False
    nullable = False
    multi    = False

class ProcessorComponentType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ProcessorComponentType"
    _title       = "Processor Component Type"
    _description = "An enumeration of types of ProcessorComponent.  This includes things like transformers and post-processors."

    CHOICES = [
    "post_processor",
        "transformer",

    ]

    open     = True
    nullable = False
    multi    = False

class DataStatusType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "DataStatusType"
    _title       = "Data Status Type"
    _description = "The current status of a data object - complete, always updated, or available as a metadata description only (ie: the actual data is unavailable)."

    CHOICES = [
    "complete",
        "metadataOnly",
        "continuouslySupplemented",

    ]

    open     = False
    nullable = False
    multi    = False


class DataHierarchyType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "DataHierarchyType"
    _title       = "Data Hierarchy Type"
    _description = "The type of data object that is grouped together into a particular hierarchy.  Currently, this is made up of terms describing how the Met Office splits up archived data and how THREDDS categorises variables."

    CHOICES = [
    "run",
        "stream",
        "institute",
        "product",
        "model",
        "experiment",
        "frequency",
        "realm",
        "variable",
        "ensembleMember",

    ]

    open     = True
    nullable = False
    multi    = False

class SpatialRegriddingStandardMethodType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "SpatialRegriddingStandardMethodType"
    _title       = "Spatial Regridding Standard Method Type"
    _description = "Is the regridding 2D or 3D?"

    CHOICES = [
    "linear",
        "near-neighbour",
        "cubic",
        "conservative-first-order",
        "conservative-second-order",
        "conservative",
        "non-conservative",

    ]

    open     = False
    nullable = False
    multi    = False


class ConnectionType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ConnectionType"
    _title       = "Connection Type"
    _description = "The ConnectionType enumeration describes the mechanism of transport for a connection."

    CHOICES = [
    "CCSM Flux Coupler",
        "ESMF",
        "FMS",
        "Files",
        "MCT",
        "OASIS3",
        "OASIS4",
        "Shared Memory",
        "Embedded",

    ]

    open     = True
    nullable = False
    multi    = False


class ModelComponentType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ModelComponentType"
    _title       = "Model Component Type"
    _description = "An enumeration of types of ModelComponent.  This includes things like atmosphere &amp; ocean models, radiation schemes, etc.   CIM best-practice is to describe every component for which there is a named ComponentType as a separate component, even if it is not a separate unit of software (ie: even if it is embedded), instead of as a (set of) ModelParameters.  This codelist is synonomous with realm for the purposes of CMIP5."

    CHOICES = [
    "Advection",
        "Aerosol3D-Sources",
        "Aerosol2D-Sources",
        "AerolEmissionAndConc",
        "AerosolKeyProperties",
        "AerosolModel",
        "Aerosols",
        "AerosolSpaceConfig",
        "AerosolTransport",
        "AtmChem2D-Sources",
        "AtmChem3D-Sources",
        "AtmChemEmissionAndConc",
        "AtmChemKeyProperties",
        "AtmChemSpaceConfig",
        "AtmChemTransport",
        "AtmGasPhaseChemistry",
        "AtmHeterogeneousChemistry",
        "AtmosAdvection",
        "AtmosCloudScheme",
        "AtmosConvectTurbulCloud",
        "AtmosDynamicalCore",
        "AtmosHorizontalDomain",
        "AtmosKeyProperties",
        "AtmosOrographyAndWaves",
        "Atmosphere",
        "AtmosphericChemistry",
        "AtmosRadiation",
        "AtmosSpaceConfiguration",
        "Climate",
        "CloudSimulator",
        "IceSheetDynamics",
        "LandIce",
        "LandIceGlaciers",
        "LandIceKeyProperties",
        "LandIceSheet",
        "LandIceShelves",
        "LandIceShelvesDynamics",
        "LandSurface",
        "LandSurfaceAlbedo",
        "LandSurfaceCarbonCycle",
        "LandSurfaceEnergyBalance",
        "LandSurfaceKeyProperties",
        "LandSurfaceLakes",
        "LandSurfaceSnow",
        "LandSurfaceSoil",
        "LandSurfaceSpaceConfiguration",
        "LandSurfaceVegetation",
        "LandSurfSoilHeatTreatment",
        "LandSurfSoilHydrology",
        "Ocean",
        "OceanAdvection",
        "OceanBioBoundaryForcing",
        "OceanBioChemistry",
        "OceanBioGasExchange",
        "OceanBioGeoChemistry",
        "OceanBioKeyProperties",
        "OceanBioSpaceConfig",
        "OceanBioTimeStepFramework",
        "OceanBioTracers",
        "OceanBioTracersEcosystem",
        "OceanBoundaryForcing",
        "OceanBoundaryForcingTracers",
        "OceanHorizontalDomain",
        "OceanInteriorMixing",
        "OceanKeyProperties",
        "OceanLateralPhysics",
        "OceanLateralPhysMomentum",
        "OceanLateralPhysTracers",
        "OceanMixedLayer",
        "OceanNudging",
        "OceanSpaceConfiguration",
        "OceanUpAndLowBoundaries",
        "OceanVerticalPhysics",
        "PhotoChemistry",
        "RiverRouting",
        "SeaIce",
        "SeaIceDynamics",
        "SeaIceKeyProperties",
        "SeaIceSpaceConfiguration",
        "SeaIceThermodynamics",
        "StratosphericHeterChem",
        "TopOfAtmosInsolation",
        "ToposphericHeterChem",
        "VegetationCarbonCycle",

    ]

    open     = True
    nullable = False
    multi    = False

class SimulationRelationshipType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "SimulationRelationshipType"
    _title       = "Simulation Relationship Type"
    _description = "The types of relationships that can be described in a simulation's genealogy."

    CHOICES = [
    "extensionOf",
        "responseTo",
        "continuationOf",
        "previousSimulation",
        "higherResolutionVersionOf",
        "lowerResolutionVersionOf",
        "fixedVersionOf",
        "followingSimulation",

    ]

    open     = False
    nullable = False
    multi    = False


class DownscalingType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "DownscalingType"
    _title       = "Downscaling Type"
    _description = "The type of experiment relationship being recorded by an experiment's genealogy."

    CHOICES = [
    "statistical",
        "dynamic",

    ]

    open     = False
    nullable = False
    multi    = False


class ResolutionType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ResolutionType"
    _title       = "Resolution Type"
    _description = ""

    CHOICES = [

    ]

    open     = True
    nullable = False
    multi    = False

class DataFormatType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "DataFormatType"
    _title       = "Data Format Type"
    _description = "Describes the internal format of the dataset."

    CHOICES = [
    "Excel",
        "HDF",
        "NetCDF",
        "GRIB 1",
        "GRIB 2",
        "PP",
        "ASCII",
        "HDF EOS",
        "NCEP ON29",
        "NCEP ON129",
        "Binary",

    ]

    open     = True
    nullable = False
    multi    = False

class EnsembleType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "EnsembleType"
    _title       = "Ensemble Type"
    _description = ""

    CHOICES = [
    "Perturbed Boundary Conditions",
        "Cross Model",
        "Initial Condition",
        "Model Modification",
        "Staggered Start",
        "Perturbed Physics",
        "Experiment Driven",
        "Mixed",

    ]

    open     = True
    nullable = False
    multi    = False


class FixityType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "FixityType"
    _title       = "Fixity Type"
    _description = "Type of fixity for an observation station."

    CHOICES = [
    "stationary",
        "moving",

    ]

    open     = False
    nullable = False
    multi    = False


class FrequencyType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "FrequencyType"
    _title       = "Frequency Type"
    _description = "Measures of frequency."

    CHOICES = [
    "daily",
        "monthly",
        "yearly",
        "hourly",

    ]

    open     = True
    nullable = False
    multi    = False

class SimulationType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "SimulationType"
    _title       = "Simulation Type"
    _description = "The configuration type for a simulation.  Primarily this is for users of ESMF to describe their simulation case."

    CHOICES = [

    ]

    open     = True
    nullable = False
    multi    = False

class TemporalAveType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "TemporalAveType"
    _title       = "Temporal Ave Type"
    _description = ""

    CHOICES = [

    ]

    open     = True
    nullable = False
    multi    = False

class ExperimentRelationshipType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ExperimentRelationshipType"
    _title       = "Experiment Relationship Type"
    _description = "The type of experiment relationship being recorded by an experiment's genealogy."

    CHOICES = [
    "previousRealisation",
        "continuationOf",
        "controlExperiment",
        "higherResolutionVersionOf",
        "lowerResolutionVersionOf",
        "increaseEnsembleOf",
        "modifiedInputMethodOf",
        "shorterVersionOf",
        "extensionOf",

    ]

    open     = False
    nullable = False
    multi    = False

class ConformanceType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ConformanceType"
    _title       = "Conformance Type"
    _description = "Enumerates the different ways that a simulation can be conformant to an experimental requirement."

    CHOICES = [
    "not conformant",
        "standard config",
        "via inputs",
        "via model mods",
        "combination",

    ]

    open     = False
    nullable = False
    multi    = False

class ProjectType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ProjectType"
    _title       = "Project Type"
    _description = ""

    CHOICES = [
    "CMIP5",
        "AMIP",
        "TAMIP",

    ]

    open     = True
    nullable = False
    multi    = False

####################################
# and here are the actual classes  #
####################################


class DateRange(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False
    _abstract = True

    _name        = "DateRange"
    _title       = "Date Range"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(DateRange,self).__init__(*args,**kwargs)


    # UML Attribute
    duration = MetadataAtomicField.Factory("charfield",blank=True)


class DataSource(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False
    _abstract = True

    _name        = "DataSource"
    _title       = "Data Source"
    _description = "A DataSource can be realised by either a DataObject (file), a DataContent (variable), a Component (model), or a ComponentProperty (variable); all of those can supply data."

    def __init__(self,*args,**kwargs):
        super(DataSource,self).__init__(*args,**kwargs)


    # UML Attribute
    purpose = MetadataEnumerationField(enumeration='cim_1_8_1.DataPurpose',blank=True,)


class DataStorage(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False
    _abstract = True

    _name        = "DataStorage"
    _title       = "Data Storage"
    _description = "Describes the method that the DataObject is stored. An abstract class with specific child classes for each supported method."

    def __init__(self,*args,**kwargs):
        super(DataStorage,self).__init__(*args,**kwargs)


    # UML Attribute
    dataSize = MetadataAtomicField.Factory("integerfield",blank=True,)
# UML Attribute
    dataFormat = MetadataEnumerationField(enumeration='cim_1_8_1.DataFormatType',blank=True,)
# UML Attribute
    dataLocation = MetadataAtomicField.Factory("urlfield",blank=True,)
    dataLocation.help_text = "Points to the actual location of the data (used to be dataURI, a feature of DataObject)."
                # UML Attribute
    modificationDate = MetadataAtomicField.Factory("datefield",blank=True)
    modificationDate.help_text = "The date that the file (or other storage medium) has been updated"


class Activity(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False
    _abstract = True

    _name        = "Activity"
    _title       = "Activity"
    _description = "An abstract class used as the parent of MeasurementCampaigns, Projects, Experiments, and NumericalActivities."

    def __init__(self,*args,**kwargs):
        super(Activity,self).__init__(*args,**kwargs)


    # UML Attribute
    responsibleParty = MetadataManyToOneField(sourceModel='cim_1_8_1.Activity',targetModel='cim_1_8_1.ResponsibleParty',blank=True,)
    responsibleParty.help_text = "The point of contact(s) for this activity.This includes, among others, the principle investigator."
                # UML Attribute
    fundingSource = MetadataAtomicField.Factory("charfield",blank=True,)
    fundingSource.help_text = "The entities that funded this activity."
                # UML Attribute
    rationale = MetadataAtomicField.Factory("charfield",blank=True,)
    rationale.help_text = "For what purpose is this activity being performed?"
                # UML Attribute
    project = MetadataEnumerationField(enumeration='cim_1_8_1.ProjectType',blank=True,)
    project.help_text = "The project(s) that this activity is associated with (ie: CMIP5, AMIP, etc.)"


class Experiment(Activity):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Experiment"
    _title       = "Experiment"
    _description = "An experiment might be an activity which is both observational and numerical in focus, for example, a measurement campaign and numerical experiments for an alpine experiment.It is a place for the scientific description of the reason why an experiment was made."

    def __init__(self,*args,**kwargs):
        super(Experiment,self).__init__(*args,**kwargs)




class NumericalActivity(Activity):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False
    _abstract = True

    _name        = "NumericalActivity"
    _title       = "Numerical Activity"
    _description = "Numerical Activity is an abstract concept which in this world view is either an ensemble, a simulaiton or a DataProcessing activity."

    def __init__(self,*args,**kwargs):
        super(NumericalActivity,self).__init__(*args,**kwargs)


    # UML Attribute
    shortName = MetadataAtomicField.Factory("charfield",blank=False,)
# UML Attribute
    longName = MetadataAtomicField.Factory("charfield",blank=False,)
# UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)


class Simulation(NumericalActivity):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False
    _abstract = True

    _name        = "Simulation"
    _title       = "Simulation"
    _description = "A simulation is the implementation of a numerical experiment.  A simulation can be made up of child simulations aggregated together to form a simulation composite.  The parent simulation can be made up of whole or partial child simulations, the simulation attributes need to be able to capture this."

    def __init__(self,*args,**kwargs):
        super(Simulation,self).__init__(*args,**kwargs)


    # UML Attribute
    simulationID = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    simulationType = MetadataEnumerationField(enumeration='cim_1_8_1.SimulationType',blank=True,)
# UML Attribute
    calendar = MetadataManyToOneField(sourceModel='cim_1_8_1.Simulation',targetModel='cim_1_8_1.Calendar',blank=False,)
# UML Attribute
    input = MetadataManyToOneField(sourceModel='cim_1_8_1.Simulation',targetModel='cim_1_8_1.Coupling',blank=True,)
    input.help_text = "implemented as a mapping from a source to target; can be a forcing file, a boundary condition, etc."
                # UML Attribute
    output = MetadataManyToOneField(sourceModel='cim_1_8_1.Simulation',targetModel='cim_1_8_1.DataObject',blank=True,)
# UML Attribute
    restart = MetadataManyToOneField(sourceModel='cim_1_8_1.Simulation',targetModel='cim_1_8_1.DataObject',blank=True,)
# UML Attribute
    spinupDateRange = MetadataManyToOneField(sourceModel='cim_1_8_1.Simulation',targetModel='cim_1_8_1.ClosedDateRange',blank=True,)
    spinupDateRange.help_text = "The date range that a simulation is engaged in spinup."
                # UML Attribute
    spinupSimulation = MetadataManyToOneField(sourceModel='cim_1_8_1.Simulation',targetModel='cim_1_8_1.Simulation',blank=True,)
    spinupSimulation.help_text = "The (external) simulation used during spinup.  Note that this element can be used in conjuntion with spinupDateRange.  If a simulation has the latter but not the former, then one can assume that the simulation is performing its own spinup."
                # UML Attribute
    controlSimulation = MetadataManyToOneField(sourceModel='cim_1_8_1.Simulation',targetModel='cim_1_8_1.Simulation',blank=True,)
    controlSimulation.help_text = "Points to a simulation being used as the basis (control) run.  Note that only derived simulations can describe something as being control; a simulation should not know if it is being used itself as the control of some other run."
                # UML Attribute
    authorsList = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    simulationURL = MetadataAtomicField.Factory("urlfield",blank=True,)
    simulationURL.help_text = "Points to the URL where information about this simulation is maintained (primarily for CCSM)"


class NumericalRequirement(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False
    _abstract = True

    _name        = "NumericalRequirement"
    _title       = "Numerical Requirement"
    _description = "A description of the requirements of particular experiments.  Numerical Requirements can be initial conditions, boundary conditions, or physical modificiations."

    def __init__(self,*args,**kwargs):
        super(NumericalRequirement,self).__init__(*args,**kwargs)


    # UML Attribute
    _id = MetadataManyToOneField(sourceModel='cim_1_8_1.NumericalRequirement',targetModel='cim_1_8_1.Identifier',blank=True,)
# UML Attribute
    name = MetadataAtomicField.Factory("charfield",blank=False,)
# UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)




class Relationship(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False
    _abstract = True

    _name        = "Relationship"
    _title       = "Relationship"
    _description = "A record of a relationship between one document and another.  This class is abstract; specific document types must specialise this class for their relationshipTypes to be included in a document's genealogy."

    def __init__(self,*args,**kwargs):
        super(Relationship,self).__init__(*args,**kwargs)


    # UML Attribute
# type is unused
# UML Attribute
# target is unused
# UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    direction = MetadataEnumerationField(enumeration='cim_1_8_1.RelationshipDirectionType',blank=False,)


class ExperimentRelationship(Relationship):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ExperimentRelationship"
    _title       = "Experiment Relationship"
    _description = "Contains a set of relationship types specific to a simulation document that can be used to describe its genealogy."

    def __init__(self,*args,**kwargs):
        super(ExperimentRelationship,self).__init__(*args,**kwargs)


    # UML Attribute
    type = MetadataEnumerationField(enumeration='cim_1_8_1.ExperimentRelationshipType',blank=False,)
# UML Attribute
    target = MetadataManyToOneField(sourceModel='cim_1_8_1.ExperimentRelationship',targetModel='cim_1_8_1.NumericalExperiment',blank=False,)



class RequirementOption(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "RequirementOption"
    _title       = "Requirement Option"
    _description = "A NumericalRequirement that is being used as a set of related requirements; For example if a requirement is to use 1 of 3 boundary conditions, then that parent requirement would have three child RequirmentOptions (each of one with the XOR optionRelationship)."

    def __init__(self,*args,**kwargs):
        super(RequirementOption,self).__init__(*args,**kwargs)


    # UML Attribute
    requirement = MetadataManyToOneField(sourceModel='cim_1_8_1.RequirementOption',targetModel='cim_1_8_1.NumericalRequirement',blank=True,abstract=True)
    requirement.help_text = "The requirement being specified by this option"
                # UML Attribute
    optionRelationship = MetadataEnumerationField(enumeration='cim_1_8_1.LogicalRelationshipType',blank=False,)
    optionRelationship.help_text = "Describes how this optional (child) requirement is related to its sibling requirements.  For example, a NumericalRequirement could consist of a set of optional requirements each with an OR relationship meaning use this boundary condition _or_ that one."


class OutputRequirement(NumericalRequirement):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "OutputRequirement"
    _title       = "Output Requirement"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(OutputRequirement,self).__init__(*args,**kwargs)


    # UML Attribute
    outputFrequency = MetadataEnumerationField(enumeration='cim_1_8_1.FrequencyType',blank=True,)
# UML Attribute
    outputPeriod = MetadataManyToOneField(sourceModel='cim_1_8_1.OutputRequirement',targetModel='cim_1_8_1.DateRange',blank=True,)
# UML Attribute
    temporalAveraging = MetadataEnumerationField(enumeration='cim_1_8_1.TemporalAveType',blank=True,)


@MetadataDocument()
class SimulationRun(Simulation):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "SimulationRun"
    _title       = "Simulation Run"
    _description = "A SimulationRun is, as the name implies, one single model run.  A SimulationRun is a Simulation.There is a one to one association between SimulationRun and (a top-level) SoftwarePackage::ModelComponent. "

    def __init__(self,*args,**kwargs):
        super(SimulationRun,self).__init__(*args,**kwargs)


    # UML Attribute
    dateRange = MetadataManyToOneField(sourceModel='cim_1_8_1.SimulationRun',targetModel='cim_1_8_1.DateRange',blank=False,)
    dateRange.help_text = "A DateRange can be used to specify a startPoint, and optionally an endPoint, or an explicit duration."


class Project(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Project"
    _title       = "Project"
    _description = "A climate project."

    def __init__(self,*args,**kwargs):
        super(Project,self).__init__(*args,**kwargs)


    # UML Attribute
    experiment = MetadataManyToOneField(sourceModel='cim_1_8_1.Project',targetModel='cim_1_8_1.Experiment',blank=True,)


###class MeasurementCampaign(Activity):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "MeasurementCampaign"
###    _title       = "Measurement Campaign"
###    _description = ""
###
###    def __init__(self,*args,**kwargs):
###        super(MeasurementCampaign,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    duration = MetadataManyToOneField(sourceModel='cim_1_8_1.MeasurementCampaign',targetModel='cim_1_8_1.ClosedDateRange',blank=False,)


class LateralBoundaryCondition(NumericalRequirement):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "LateralBoundaryCondition"
    _title       = "Lateral Boundary Condition"
    _description = "A boundary condition is a numerical requirement which looks like a variable imposed on the model evolution (i.e. it might - or might not - evolve with time, but is seen by the model at various times during its evolution) as opposed to an initial condition (at model time zero)."

    def __init__(self,*args,**kwargs):
        super(LateralBoundaryCondition,self).__init__(*args,**kwargs)


    # UML Attribute
    source = MetadataManyToOneField(sourceModel='cim_1_8_1.LateralBoundaryCondition',targetModel='cim_1_8_1.DataSource',blank=True,)




class SimulationRelationship(Relationship):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "SimulationRelationship"
    _title       = "Simulation Relationship"
    _description = "Contains a set of relationship types specific to a simulation document that can be used to describe its genealogy."

    def __init__(self,*args,**kwargs):
        super(SimulationRelationship,self).__init__(*args,**kwargs)


    # UML Attribute
    type = MetadataEnumerationField(enumeration='cim_1_8_1.SimulationRelationshipType',blank=False,)
# UML Attribute
    target = MetadataManyToOneField(sourceModel='cim_1_8_1.SimulationRelationship',targetModel='cim_1_8_1.Simulation',blank=False,)



class Conformance(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Conformance"
    _title       = "Conformance"
    _description = "A conformance class maps how a configured model component met a specific numerical requirement.For example, for a double CO2 boundary condition, a model component might read a CO2 dataset in which CO2 has been doubled, or it might modify a parameterisation (presumably with a factor of two somewhere).So, the conformance links a requirement to a DataSource (which can be either an actual DataObject or a property of a model component).In some cases a model/simulation may _naturally_ conform to a requirement.  In this case there would be no reference to a DataSource but the conformant attribute would be true.If something is purpopsefully non-conformant then the conformant attribute would be false."

    def __init__(self,*args,**kwargs):
        super(Conformance,self).__init__(*args,**kwargs)


    # UML Attribute
    conformant = MetadataAtomicField.Factory("booleanfield",blank=False,)
    conformant.help_text = "Records whether or not this conformance satisfies the requirement.  A simulation should have at least one conformance mapping to every experimental requirement.  If a simulation satisfies the requirement - the usual case - then conformant should have a value of true.  If conformant is true but there is no reference to a source for the conformance, then we can assume that the simulation conforms to the requirement _naturally_, that is without having to modify code or inputs. If a simulation does not conform to a requirement then conformant should be set to false."
                # UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    frequency = MetadataEnumerationField(enumeration='cim_1_8_1.FrequencyType',blank=True,)
# UML Attribute
    requirement = MetadataManyToOneField(sourceModel='cim_1_8_1.Conformance',targetModel='cim_1_8_1.NumericalRequirement',blank=False,)
    requirement.help_text = "Points to the NumericalRequirement that the simulation in question is conforming to."
                # UML Attribute
    source = MetadataManyToOneField(sourceModel='cim_1_8_1.Conformance',targetModel='cim_1_8_1.DataSource',blank=True,)
    source.help_text = "Points to the DataSource used to conform to a particular Requirement.   This may be part of an activity::simulation or a software::component.  It can be either a DataObject or a SoftwareComponent or a ComponentProperty.  It could also be by using particular attributes of, say, a SoftwareComponent, but in that case the recommended practise is to reference the component and add appropriate text in the conformance description attribute."
                # UML Attribute
    type = MetadataEnumerationField(enumeration='cim_1_8_1.ConformanceType',blank=True,)
    type.help_text = "Describes the method that this simulation conforms to an experimental requirement (in case it is not specified by the change property of the reference to the source of this conformance)"


###@MetadataDocument()
###class Assimilation(Simulation):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "Assimilation"
###    _title       = "Assimilation"
###    _description = "An assimilation is a simulation that is constrained by observations. It is representative of an actual period in the past eg ERA-40. "
###
###    def __init__(self,*args,**kwargs):
###        super(Assimilation,self).__init__(*args,**kwargs)
###



class PhysicalModification(Conformance):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "PhysicalModification"
    _title       = "Physical Modification"
    _description = "Physical modification is the implementation of a boundary condition numerical requirement that is achieved within the model code rather than from some external source file. It  might include, for example,  a specific rate constant within a chemical reaction, or coefficient value(s) in a parameterisation. For example, one might require a numerical experiment where specific chemical reactions were turned off - e.g. no heterogeneous chemistry."

    def __init__(self,*args,**kwargs):
        super(PhysicalModification,self).__init__(*args,**kwargs)




@MetadataDocument()
class SimulationComposite(Simulation):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "SimulationComposite"
    _title       = "Simulation Composite"
    _description = "A SimulationComposite is an aggregation of Simulaitons.With the aggreation connector between Simulation and SimulationComposite(SC) the SC can be made up of both SimulationRuns and SCs.The SimulationComposite is the new name for the concept of SimulationCollection: A simulation can be made up of child simulations aggregated together to form a simulation composite.  The parent simulation can be made up of whole or partial child simulations and the SimulationComposite attributes need to be able to capture this."

    def __init__(self,*args,**kwargs):
        super(SimulationComposite,self).__init__(*args,**kwargs)


    # UML Attribute
    rank = MetadataAtomicField.Factory("integerfield",blank=False,)
    rank.help_text = "Position of a simulation in the SimulationComposite timeline. eg:  Is this the first (rank = 1) or second (rank = 2) simulation"
                # UML Attribute
    dateRange = MetadataManyToOneField(sourceModel='cim_1_8_1.SimulationComposite',targetModel='cim_1_8_1.DateRange',blank=False,)


###class ObservationStation(MetadataModel):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "ObservationStation"
###    _title       = "Observation Station"
###    _description = ""
###
###    def __init__(self,*args,**kwargs):
###        super(ObservationStation,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    fixity = MetadataEnumerationField(enumeration='cim_1_8_1.FixityType',blank=False,)


class BoundaryCondition(NumericalRequirement):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "BoundaryCondition"
    _title       = "Boundary Condition"
    _description = "A boundary condition is a numerical requirement which looks like a variable imposed on the model evolution (i.e. it might - or might not - evolve with time, but is seen by the model at various times during its evolution) as opposed to an initial condition (at model time zero)."

    def __init__(self,*args,**kwargs):
        super(BoundaryCondition,self).__init__(*args,**kwargs)


    # UML Attribute
    source = MetadataManyToOneField(sourceModel='cim_1_8_1.BoundaryCondition',targetModel='cim_1_8_1.DataSource',blank=True,)


class SpatioTemporalConstraint(NumericalRequirement):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "SpatioTemporalConstraint"
    _title       = "Spatio Temporal Constraint"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(SpatioTemporalConstraint,self).__init__(*args,**kwargs)


    # UML Attribute
    requiredDuration = MetadataManyToOneField(sourceModel='cim_1_8_1.SpatioTemporalConstraint',targetModel='cim_1_8_1.DateRange',blank=True,)
# UML Attribute
    spatialResolution = MetadataEnumerationField(enumeration='cim_1_8_1.ResolutionType',blank=True,)



@MetadataDocument()
class DownscalingSimulation(NumericalActivity):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "DownscalingSimulation"
    _title       = "Downscaling Simulation"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(DownscalingSimulation,self).__init__(*args,**kwargs)


    # UML Attribute
    downscalingID = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    downscalingType = MetadataEnumerationField(enumeration='cim_1_8_1.DownscalingType',blank=True,)
# UML Attribute
    calendar = MetadataManyToOneField(sourceModel='cim_1_8_1.DownscalingSimulation',targetModel='cim_1_8_1.Calendar',blank=False,)
# UML Attribute
    input = MetadataManyToOneField(sourceModel='cim_1_8_1.DownscalingSimulation',targetModel='cim_1_8_1.Coupling',blank=True,)
    input.help_text = "implemented as a mapping from a source to target; can be a forcing file, a boundary condition, etc."
                # UML Attribute
    output = MetadataManyToOneField(sourceModel='cim_1_8_1.DownscalingSimulation',targetModel='cim_1_8_1.DataObject',blank=True,)
# UML Attribute
    downscaledFrom = MetadataManyToOneField(sourceModel='cim_1_8_1.DownscalingSimulation',targetModel='cim_1_8_1.DataSource',blank=False,)


@MetadataDocument()
class NumericalExperiment(Experiment):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "NumericalExperiment"
    _title       = "Numerical Experiment"
    _description = "A numerical experiment may be generated by an experiment, in which case it is inSupportOf the experiment. But a numerical experiment may also exist as an activity in its own right (as it might be if it were needed for a MIP). Examples: AR4 individual experiments, AR5 individual experiments, RAPID THC experiments etc. "

    def __init__(self,*args,**kwargs):
        super(NumericalExperiment,self).__init__(*args,**kwargs)


    # UML Attribute
    shortName = MetadataAtomicField.Factory("charfield",blank=False,)
# UML Attribute
    longName = MetadataAtomicField.Factory("charfield",blank=False,)
# UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    experimentID = MetadataManyToOneField(sourceModel='cim_1_8_1.NumericalExperiment',targetModel='cim_1_8_1.Identifier',blank=True,)
    experimentID.help_text = "An experiment ID takes the form &lt;number&gt;.&lt;number&gt;[-&lt;letter&gt;]."
                # UML Attribute
    calendar = MetadataManyToOneField(sourceModel='cim_1_8_1.NumericalExperiment',targetModel='cim_1_8_1.Calendar',blank=False,)
    calendar.help_text = "Is the numerical experiment representative of real time, a 360 day year or a perpetual period?"


@MetadataDocument()
class DataProcessing(NumericalActivity):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "DataProcessing"
    _title       = "Data Processing"
    _description = "A DataProcessing activity refers to the processing of observation data or post processing of data from a simulation. It does not simulate scientific phenomena like a Simulation activity does.  It is associated with a ProcessorComponent as opposed to a ModelComponent."

    def __init__(self,*args,**kwargs):
        super(DataProcessing,self).__init__(*args,**kwargs)


    # UML Attribute
    inputs = MetadataManyToOneField(sourceModel='cim_1_8_1.DataProcessing',targetModel='cim_1_8_1.DataSource',blank=True,)
    inputs.help_text = "the data being processed."
                # UML Attribute
    outputs = MetadataManyToOneField(sourceModel='cim_1_8_1.DataProcessing',targetModel='cim_1_8_1.DataSource',blank=True,)
    outputs.help_text = "the data being generated."


###class EnsembleMember(MetadataModel):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "EnsembleMember"
###    _title       = "Ensemble Member"
###    _description = ""
###
###    def __init__(self,*args,**kwargs):
###        super(EnsembleMember,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    activity = MetadataManyToOneField(sourceModel='cim_1_8_1.EnsembleMember',targetModel='cim_1_8_1.NumericalActivity',blank=False,)
#### UML Attribute
###    ensembleMemberID = MetadataManyToOneField(sourceModel='cim_1_8_1.EnsembleMember',targetModel='cim_1_8_1.StandardName',blank=True,)


###class DataCollection(Project):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "DataCollection"
###    _title       = "Data Collection"
###    _description = "A DataCollection activity is one which is not aimed at supporting any specific experiment. "
###
###    def __init__(self,*args,**kwargs):
###        super(DataCollection,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    duration = MetadataManyToOneField(sourceModel='cim_1_8_1.DataCollection',targetModel='cim_1_8_1.DateRange',blank=False,)
###
###
###@MetadataDocument()
###class Ensemble(NumericalActivity):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "Ensemble"
###    _title       = "Ensemble"
###    _description = "An ensemble is made up of two or more simulations which are to be compared against each other to create ensemble statistics. Ensemble members can differ in terms of initial conditions, physical parameterisation and the model used.  An ensemble bundles together sets of ensembleMembers, all of which reference the same Simulation(Run) and include one or more changes."
###
###    def __init__(self,*args,**kwargs):
###        super(Ensemble,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    output = MetadataManyToOneField(sourceModel='cim_1_8_1.Ensemble',targetModel='cim_1_8_1.DataSource',blank=True,)
#### UML Attribute
###    ensembleType = MetadataEnumerationField(enumeration='cim_1_8_1.EnsembleType',blank=False,)
###
###
###

class InitialCondition(NumericalRequirement):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "InitialCondition"
    _title       = "Initial Condition"
    _description = "An initial condition is a numerical requirement on a model prognostic variable value at time zero."

    def __init__(self,*args,**kwargs):
        super(InitialCondition,self).__init__(*args,**kwargs)


    # UML Attribute
    source = MetadataManyToOneField(sourceModel='cim_1_8_1.InitialCondition',targetModel='cim_1_8_1.DataSource',blank=True,)




###class MIP(Project):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "MIP"
###    _title       = "MIP"
###    _description = "Model Intercomparison Project. Exmaple: CMIP5 and CCMVal. A MIP aggregates together many Numerical Experiments.  A MIP contains a reference to at least two experiments."
###
###    def __init__(self,*args,**kwargs):
###        super(MIP,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    numericalExperiment = MetadataManyToOneField(sourceModel='cim_1_8_1.MIP',targetModel='cim_1_8_1.NumericalExperiment',blank=False,)
###    numericalExperiment.help_text = "A NumericalExperiment to compare"
###
###
###class FileStorage(DataStorage):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "FileStorage"
###    _title       = "File Storage"
###    _description = "Contains attributes to describe a DataObject stored as a single file."
###
###    def __init__(self,*args,**kwargs):
###        super(FileStorage,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    fileSystem = MetadataAtomicField.Factory("charfield",blank=True,)
#### UML Attribute
###    path = MetadataAtomicField.Factory("charfield",blank=True,)
#### UML Attribute
###    fileName = MetadataAtomicField.Factory("charfield",blank=False,)




###class DataTopic(MetadataModel):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "DataTopic"
###    _title       = "Data Topic"
###    _description = "Describes the content  of a data object; the variable's name, units, etc."
###
###    def __init__(self,*args,**kwargs):
###        super(DataTopic,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    name = MetadataAtomicField.Factory("charfield",blank=False,)
#### UML Attribute
###    standardName = MetadataManyToOneField(sourceModel='cim_1_8_1.DataTopic',targetModel='cim_1_8_1.StandardName',blank=True,)
#### UML Attribute
###    description = MetadataAtomicField.Factory("charfield",blank=True,)
#### UML Attribute
###    unit = MetadataEnumerationField(enumeration='cim_1_8_1.UnitType',blank=True,)
###
###class gmd_MD_RestrictionCode_PropertyType(MetadataModel):
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###
###    _name        = "gmd_MD_RestrictionCode_PropertyType"
###    _title       = "gmd_MD_RestrictionCode_PropertyType"
###    _description = ""
###
###    def __init__(self,*args,**kwargs):
###        super(gmd_MD_RestrictionCode_PropertyType,self).__init__(*args,**kwargs)
###
###    name = MetadataAtomicField.Factory("charfield",blank=True,)
###
###class DataRestriction(MetadataModel):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "DataRestriction"
###    _title       = "Data Restriction"
###    _description = "An access or use restriction on some element of the DataObject's actual data."
###
###    def __init__(self,*args,**kwargs):
###        super(DataRestriction,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    restrictionScope = MetadataEnumerationField(enumeration='cim_1_8_1.DataRestrictionScopeType',blank=True,)
###    restrictionScope.help_text = "The thing (data or metadata, access or use) that this restriction is applied to."
###                # UML Attribute
###    restriction = MetadataManyToOneField(sourceModel='cim_1_8_1.DataRestriction',targetModel='cim_1_8_1.gmd_MD_RestrictionCode_PropertyType',blank=True,)
#### UML Attribute
###    license = MetadataManyToOneField(sourceModel='cim_1_8_1.DataRestriction',targetModel='cim_1_8_1.License',blank=True,)
###
###
###class DbStorage(DataStorage):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "DbStorage"
###    _title       = "Db Storage"
###    _description = "Contains attributes to describe a DataObject being stored in a database."
###
###    def __init__(self,*args,**kwargs):
###        super(DbStorage,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    dbAccessString = MetadataAtomicField.Factory("charfield",blank=True,)
#### UML Attribute
###    dbName = MetadataAtomicField.Factory("charfield",blank=False,)
#### UML Attribute
###    owner = MetadataAtomicField.Factory("charfield",blank=True,)
#### UML Attribute
###    dbTable = MetadataAtomicField.Factory("charfield",blank=True,)
###
###
###
###
###class DataDistribution(MetadataModel):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "DataDistribution"
###    _title       = "Data Distribution"
###    _description = "Describes how a DataObject is distributed."
###
###    def __init__(self,*args,**kwargs):
###        super(DataDistribution,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    distributionFee = MetadataAtomicField.Factory("charfield",blank=True,)
#### UML Attribute
###    distributionFormat = MetadataEnumerationField(enumeration='cim_1_8_1.DataFormatType',blank=True,)
#### UML Attribute
###    distributionAccess = MetadataEnumerationField(enumeration='cim_1_8_1.DataAccessType',blank=True,)
#### UML Attribute
###    responsibleParty = MetadataManyToOneField(sourceModel='cim_1_8_1.DataDistribution',targetModel='cim_1_8_1.ResponsibleParty',blank=True,)
###
###
@MetadataDocument()
class DataObject(DataSource):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "DataObject"
    _title       = "Data Object"
    _description = "A DataObject describes a unit of data.  DataObjects can be grouped hierarchically.  The attributes hierarchyLevelName and hierarchyLevelValue describe how objects are grouped.  "

    def __init__(self,*args,**kwargs):
        super(DataObject,self).__init__(*args,**kwargs)


    # UML Attribute
    dataStatus = MetadataEnumerationField(enumeration='cim_1_8_1.DataStatusType',blank=True,)
    dataStatus.help_text = "The current status of the data - is it complete, or is this metadata description all that is available, or is the data continuously supplemented."
                # UML Attribute
    acronym = MetadataAtomicField.Factory("charfield",blank=False,)
# UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    hierarchyLevelName = MetadataEnumerationField(enumeration='cim_1_8_1.DataHierarchyType',blank=True,)
    hierarchyLevelName.help_text = "What level in the data hierarchy (constructed by the self-referential parent/child aggregations) is this DataObject."
                # UML Attribute
    hierarchyLevelValue = MetadataManyToOneField(sourceModel='cim_1_8_1.DataObject',targetModel='cim_1_8_1.PropertyValue',blank=True,)
    hierarchyLevelValue.help_text = "What is the name of the specific HierarchyLevel this DataObject is being organised at (ie: if the HierarchyLevel is run then the name might be the runid)."
                # UML Attribute
    keyword = MetadataAtomicField.Factory("charfield",blank=True,)
    keyword.help_text = "Descriptive keyword used when searching for DataObjects (this is not the same as shortName / longName / description)."
                # UML Attribute
    geometryModel = MetadataManyToOneField(sourceModel='cim_1_8_1.DataObject',targetModel='cim_1_8_1.gml_AbstractGeometryType',blank=True,)
#### UML Attribute
###    dataProperty = MetadataManyToOneField(sourceModel='cim_1_8_1.DataObject',targetModel='cim_1_8_1.DataProperty',blank=True,)
###    dataProperty.help_text = "May not be used"
                # UML Attribute
    sourceSimulation = MetadataManyToOneField(sourceModel='cim_1_8_1.DataObject',targetModel='cim_1_8_1.Simulation',blank=True,)
    sourceSimulation.help_text = "Points to the simulation that generated this dataset."

class gmd_CI_Citation_Type(MetadataModel):

    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "gmd_CI_Citation_Type"
    _title       = "gmd_CI_Citation_Type"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(gmd_CI_Citation_Type,self).__init__(*args,**kwargs)

    name = MetadataAtomicField.Factory("charfield",blank=True,)

class DataCitation(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "DataCitation"
    _title       = "Data Citation"
    _description = "A description of references to this data from the scientific literature; like ISO: MD_ContentInformation"

    def __init__(self,*args,**kwargs):
        super(DataCitation,self).__init__(*args,**kwargs)


    # UML Attribute
    abstract = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    citation = MetadataManyToOneField(sourceModel='cim_1_8_1.DataCitation',targetModel='cim_1_8_1.gmd_CI_Citation_Type',blank=False,)


###class DataContent(DataSource):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "DataContent"
###    _title       = "Data Content"
###    _description = "The contents of the data object; like ISO: MD_ContentInformation."
###
###    def __init__(self,*args,**kwargs):
###        super(DataContent,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    topic = MetadataManyToOneField(sourceModel='cim_1_8_1.DataContent',targetModel='cim_1_8_1.DataTopic',blank=False,)
#### UML Attribute
###    aggregation = MetadataAtomicField.Factory("charfield",blank=True,)
###    aggregation.help_text = "Describes how the content has been aggregated together: sum, min, mean, max, ..."
###                # UML Attribute
###    frequency = MetadataEnumerationField(enumeration='cim_1_8_1.FrequencyType',blank=True,)
###    frequency.help_text = "Describes the frequency of the data content: daily, hourly, ..."
###
###
###
###
###class DataProperty(Property):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "DataProperty"
###    _title       = "Data Property"
###    _description = "A property of a DataObject.  Currently this is intended to be used to record CF specific information (like packing, scaling, etc.) for OASIS4."
###
###    def __init__(self,*args,**kwargs):
###        super(DataProperty,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    description = MetadataAtomicField.Factory("charfield",blank=True,)
###
###
###
###
###class DataExtent(MetadataModel):
###                # this is acutally an external dependency(gmd:EX_Extent_Type)
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "DataExtent"
###    _title       = "Data Extent"
###    _description = "Records the geographic (horizontal and vertical) and temporal extent of the DataObject.  "
###
###    def __init__(self,*args,**kwargs):
###        super(DataExtent,self).__init__(*args,**kwargs)
###
###
###
###
###class IpStorage(DataStorage):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "IpStorage"
###    _title       = "Ip Storage"
###    _description = ""
###
###    def __init__(self,*args,**kwargs):
###        super(IpStorage,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    protocol = MetadataAtomicField.Factory("charfield",blank=True,)
#### UML Attribute
###    host = MetadataAtomicField.Factory("charfield",blank=True,)
#### UML Attribute
###    path = MetadataAtomicField.Factory("charfield",blank=True,)
#### UML Attribute
###    fileName = MetadataAtomicField.Factory("charfield",blank=False,)
###
#### DELIBERATELY SKIPPING THE "GRIDS" PACKAGE B/C IT HAS TOO MANY EXTERNAL DEPENDENCIES
###
###
###
###class CIM_Result(MetadataModel):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "CIM_Result"
###    _title       = "CIM Result"
###    _description = ""
###
###    def __init__(self,*args,**kwargs):
###        super(CIM_Result,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    availableFrom = MetadataAtomicField.Factory("urlfield",blank=True)
#### UML Attribute
###    description = MetadataAtomicField.Factory("charfield",blank=True,)
#### UML Attribute
###    resultType = MetadataEnumerationField(enumeration='cim_1_8_1.CIM_ResultType',blank=False,)
###
###
###class CIM_Measure(MetadataModel):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "CIM_Measure"
###    _title       = "CIM Measure"
###    _description = ""
###
###    def __init__(self,*args,**kwargs):
###        super(CIM_Measure,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    evaluationMethodDescription = MetadataAtomicField.Factory("charfield",blank=True,)
#### UML Attribute
###    evaluationMethodType = MetadataAtomicField.Factory("charfield",blank=True,)
#### UML Attribute
###    evaluationProcedure =  MetadataAtomicField.Factory("charfield",blank=True,)
#### UML Attribute
###    measureDescription = MetadataAtomicField.Factory("charfield",blank=True,)
#### UML Attribute
###    measureIdentification =  MetadataAtomicField.Factory("charfield",blank=True,)
#### UML Attribute
###    nameOfMeasure = MetadataAtomicField.Factory("charfield",blank=True,)
###
###
###class CIM_Scope(MetadataModel):
###                # this is acutally an external dependency(gmd:DQ_Scope_Type)
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "CIM_Scope"
###    _title       = "CIM Scope"
###    _description = ""
###
###    def __init__(self,*args,**kwargs):
###        super(CIM_Scope,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    availableAt =  MetadataAtomicField.Factory("urlfield",blank=True,)
#### UML Attribute
###    target = MetadataManyToOneField(sourceModel='cim_1_8_1.CIM_Scope',targetModel='cim_1_8_1.Document',blank=True,)
###
###
###class CIM_ResultSet(MetadataModel):
###                # this is acutally an external dependency(gmd:DQ_Result_PropertyType)
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "CIM_ResultSet"
###    _title       = "CIM Result Set"
###    _description = ""
###
###    def __init__(self,*args,**kwargs):
###        super(CIM_ResultSet,self).__init__(*args,**kwargs)
###
###
###
###
###class CIM_DomainConsistency(MetadataModel):
###                # this is acutally an external dependency(gmd:DQ_DomainConsistency_Type)
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "CIM_DomainConsistency"
###    _title       = "CIM Domain Consistency"
###    _description = ""
###
###    def __init__(self,*args,**kwargs):
###        super(CIM_DomainConsistency,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
#### dateTime is unused
#### UML Attribute
###    evaluator = MetadataManyToOneField(sourceModel='cim_1_8_1.CIM_DomainConsistency',targetModel='cim_1_8_1.ResponsibleParty',blank=True,)
#### UML Attribute
#### result is unused
###
###
###
###
###class CIM_QualityDetail(MetadataModel):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "CIM_QualityDetail"
###    _title       = "CIM Quality Detail"
###    _description = "Locates the target of a CIM QualityIssue. "
###
###    def __init__(self,*args,**kwargs):
###        super(CIM_QualityDetail,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    detailDescription = MetadataAtomicField.Factory("charfield",blank=True,)
###    detailDescription.help_text = "a description of the quality issue with reference to this specific feature"
###                # UML Attribute
###    featureType = MetadataEnumerationField(enumeration='cim_1_8_1.CIM_FeatureType',blank=False,)
###    featureType.help_text = "the type of feature that the quality issue refers too (for METAFOR this could be simulation, file, boundary condition etc.)"
###                # UML Attribute
###    feature = MetadataManyToOneField(sourceModel='cim_1_8_1.CIM_QualityDetail',targetModel='cim_1_8_1.Document',blank=False,)
###    feature.help_text = "the reference to the specific feature (e.g. a URI to a file)"
###
###
###class CIM_QualityIssue(MetadataModel):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "CIM_QualityIssue"
###    _title       = "CIM Quality Issue"
###    _description = "Records an issue with an instance of the CIM.  The particular part of the instance being referred to is captured by the detail attribute(s).  A resolution can be added to a quality issue.  A single issue can have multiple subissues."
###
###    def __init__(self,*args,**kwargs):
###        super(CIM_QualityIssue,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    dateTime = MetadataAtomicField.Factory("datetimefield",blank=False,)
###    dateTime.help_text = "date (and time) issue was added to CIM"
###                # UML Attribute
###    issueDescription = MetadataAtomicField.Factory("charfield",blank=False,)
###    issueDescription.help_text = "summary description of quality issue"
###                # UML Attribute
###    issueIdentifiedBy = MetadataManyToOneField(sourceModel='cim_1_8_1.CIM_QualityIssue',targetModel='cim_1_8_1.ResponsibleParty',blank=False,)
###    issueIdentifiedBy.help_text = "person/organisation responsible for identifying this quality issue"
###                # UML Attribute
###    issueResponsibilityOf = MetadataManyToOneField(sourceModel='cim_1_8_1.CIM_QualityIssue',targetModel='cim_1_8_1.ResponsibleParty',blank=True,)
###    issueResponsibilityOf.help_text = "person/organisation allocated the responsibuility for addressing this issue"
###                # UML Attribute
###    issueSeverity = MetadataEnumerationField(enumeration='cim_1_8_1.QualitySeverityType',blank=False,)
###    issueSeverity.help_text = "severity of issue (e.g. potential, minor, major etc. - enumeration list will need to be defined for METAFOR"
###                # UML Attribute
###    issueStatus = MetadataEnumerationField(enumeration='cim_1_8_1.QualityStatusType',blank=False,)
###    issueStatus.help_text = "current status of this issue (e.g. open, investigation, closed, etc. - enumeration values to be defined for METAFOR)"
###                # UML Attribute
###    issueType = MetadataEnumerationField(enumeration='cim_1_8_1.QualityIssueType',blank=True,)
###    issueType.help_text = "type of quality issue (e.g. metadata, data etc. - enumeration list needs to be defined for METAFOR"
###
###
###class CIM_QualityResolution(MetadataModel):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "CIM_QualityResolution"
###    _title       = "CIM Quality Resolution"
###    _description = "A description of what action was taken because of a quality issue."
###
###    def __init__(self,*args,**kwargs):
###        super(CIM_QualityResolution,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    dateTime = MetadataAtomicField.Factory("datetimefield",blank=False,)
###    dateTime.help_text = "date of resolution information"
###                # UML Attribute
###    resolutionDescription = MetadataAtomicField.Factory("charfield",blank=False,)
###    resolutionDescription.help_text = "description of resolution of quality issues - including external references if required"
###                # UML Attribute
###    resolvedBy = MetadataManyToOneField(sourceModel='cim_1_8_1.CIM_QualityResolution',targetModel='cim_1_8_1.ResponsibleParty',blank=False,)
###    resolvedBy.help_text = "person/organisation responsible for resolution, or the person/organisation who should be contacted with any queries about the resolution of this quality issue"
###
###
###@MetadataDocument()
###class CIM_Quality(MetadataModel):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###
###    _name        = "CIM_Quality"
###    _title       = "CIM Quality"
###    _description = "The starting point for a quality record.  It can contain any number of issues and reports.  An issue is an open-ended description of some issue about a CIM instance.  A record is a prescribed description of some specific quantitative measure that has been applied to a CIM instance."
###
###    def __init__(self,*args,**kwargs):
###        super(CIM_Quality,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    scope = MetadataManyToOneField(sourceModel='cim_1_8_1.CIM_Quality',targetModel='cim_1_8_1.CIM_Scope',blank=False,)
###    scope.help_text = "the specific data to which the quality information applies"

# TODO: DO I WANT TO DO ANYTHING SPECIAL W/ THE "SHARED" PACKAGE?

class ClosedDateRange(DateRange):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ClosedDateRange"
    _title       = "Closed Date Range"
    _description = "A date range with specified start and end points."

    def __init__(self,*args,**kwargs):
        super(ClosedDateRange,self).__init__(*args,**kwargs)


    # UML Attribute
    endDate = MetadataAtomicField.Factory("datefield",blank=True,)
    endDate.help_text = "EndDate is optional becuase the length of a ClosedDateRange can be calculated from the StartDate plus the Duration element."
                # UML Attribute
    startDate = MetadataAtomicField.Factory("datefield",blank=False,)

class Standard(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Standard"
    _title       = "Standard"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(Standard,self).__init__(*args,**kwargs)


    # UML Attribute
    name = MetadataAtomicField.Factory("charfield",blank=False,)
    name.help_text = "The name of the standard"
                # UML Attribute
    version = MetadataAtomicField.Factory("charfield",blank=True,)
    version.help_text = "The version of the standard"
                # UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)



@MetadataDocument()
class Platform(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Platform"
    _title       = "Platform"
    _description = "A platform is a description of resources used to deploy a component/simulation.  A platform pairs a machine with a (set of) compilers.  There is also a point of contact for the platform. "

    def __init__(self,*args,**kwargs):
        super(Platform,self).__init__(*args,**kwargs)


    # UML Attribute
    shortName = MetadataAtomicField.Factory("charfield",blank=False,)
# UML Attribute
    longName = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    contact = MetadataManyToOneField(sourceModel='cim_1_8_1.Platform',targetModel='cim_1_8_1.ResponsibleParty',blank=True,)


class Compiler(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Compiler"
    _title       = "Compiler"
    _description = "A description of a compiler used on a particular platform."

    def __init__(self,*args,**kwargs):
        super(Compiler,self).__init__(*args,**kwargs)


    # UML Attribute
    compilerName = MetadataAtomicField.Factory("charfield",blank=False,)
# UML Attribute
    compilerVersion = MetadataAtomicField.Factory("charfield",blank=False,)
# UML Attribute
    compilerLanguage = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    compilerType = MetadataEnumerationField(enumeration='cim_1_8_1.CompilerType',blank=True,)
# UML Attribute
    compilerOptions = MetadataAtomicField.Factory("charfield",blank=True,)
    compilerOptions.help_text = "The set of options used during compilation (recorded here as a single string rather than separate elements)"
                # UML Attribute
    compilerEnvironmentVariables = MetadataAtomicField.Factory("charfield",blank=True,)
    compilerEnvironmentVariables.help_text = "The state of envrionment variables used during compilation (recorded here as a single string rather than separate elements)"


class License(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "License"
    _title       = "License"
    _description = "A description of a license restricting access to a unit of data or software."

    def __init__(self,*args,**kwargs):
        super(License,self).__init__(*args,**kwargs)


    # UML Attribute
    licenseName = MetadataAtomicField.Factory("charfield",blank=True,)
    licenseName.help_text = "The name that the license goes by (ie: GPL)"
                # UML Attribute
    licenseContact = MetadataAtomicField.Factory("charfield",blank=True,)
    licenseContact.help_text = "The point of contact for access to this artifact; may be either a person or an institution"
                # UML Attribute
    licenseDescription = MetadataAtomicField.Factory("charfield",blank=True,)
    licenseDescription.help_text = "A textual description of the license; might be the full text of the license, more likely to be a brief summary"
                # UML Attribute
    unrestricted = MetadataAtomicField.Factory("booleanfield",blank=False,)
    unrestricted.help_text = "If unrestricted=true then the artifact can be downloaded with no restrictions (ie: there are no administrative steps for the user to deal with; code or data can be downloaded and used directly)."


class DocumentRelationship(Relationship):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "DocumentRelationship"
    _title       = "Document Relationship"
    _description = "Contains the set of relationships supported by a Document."

    def __init__(self,*args,**kwargs):
        super(DocumentRelationship,self).__init__(*args,**kwargs)


    # UML Attribute
    type = MetadataEnumerationField(enumeration='cim_1_8_1.DocumentRelationshipType',blank=False,)
# UML Attribute
    target = MetadataManyToOneField(sourceModel='cim_1_8_1.DocumentRelationship',targetModel='cim_1_8_1.Document',blank=False,)


class Calendar(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False
    _abstract = True

    _name        = "Calendar"
    _title       = "Calendar"
    _description = "Describes a method of calculating a span of dates."

    def __init__(self,*args,**kwargs):
        super(Calendar,self).__init__(*args,**kwargs)


    # UML Attribute
    units = MetadataEnumerationField(enumeration='cim_1_8_1.CalendarUnit',blank=True,)
# UML Attribute
    length = MetadataAtomicField.Factory("integerfield",blank=True,)
# UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)
    description.help_text = "Describes the finer details of the calendar, in case they are not-obvious.  For example, if an experiment has changing conditions within it (ie: 1% CO2 increase until 2100, then hold fixed for the remaining period of the  experment)"


class MachineCompilerUnit(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "MachineCompilerUnit"
    _title       = "Machine Compiler Unit"
    _description = "Associates a machine with a [set of] compilers.  This is a separate class in case a platform needs to specify more than one machine/compiler pair."

    def __init__(self,*args,**kwargs):
        super(MachineCompilerUnit,self).__init__(*args,**kwargs)


    # UML Attribute
    machine = MetadataManyToOneField(sourceModel='cim_1_8_1.MachineCompilerUnit',targetModel='cim_1_8_1.Machine',blank=False,)
# UML Attribute
    compiler = MetadataManyToOneField(sourceModel='cim_1_8_1.MachineCompilerUnit',targetModel='cim_1_8_1.Compiler',blank=True,)


class ControlledVocabulary(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ControlledVocabulary"
    _title       = "Controlled Vocabulary"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(ControlledVocabulary,self).__init__(*args,**kwargs)


    # UML Attribute
    name = MetadataAtomicField.Factory("charfield",blank=False,)
    name.help_text = "The name of the CV"
                # UML Attribute
    version = MetadataAtomicField.Factory("charfield",blank=True,)
    version.help_text = "The version of the CV"
                # UML Attribute
    server = MetadataAtomicField.Factory("urlfield",blank=False,)
    server.help_text = "The location (URI) of the CV"
                # UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    details = MetadataAtomicField.Factory("charfield",blank=True,)
    details.help_text = "Details on how to access the CV"


class CodeList(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False
    _abstract = True

    _name        = "CodeList"
    _title       = "Code List"
    _description = "A placeholder for codelists (required for XSL generation)."

    def __init__(self,*args,**kwargs):
        super(CodeList,self).__init__(*args,**kwargs)


    # UML Attribute
    controlledVocabulary = MetadataManyToOneField(sourceModel='cim_1_8_1.CodeList',targetModel='cim_1_8_1.ControlledVocabulary',blank=True,)
# UML Attribute
    value = MetadataAtomicField.Factory("charfield",blank=False,)
    value.help_text = "The term being used for this CV (or standard)"


class OpenDateRange(DateRange):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "OpenDateRange"
    _title       = "Open Date Range"
    _description = "A date range without a specified start and/or end point."

    def __init__(self,*args,**kwargs):
        super(OpenDateRange,self).__init__(*args,**kwargs)


    # UML Attribute
    startDate = MetadataAtomicField.Factory("datefield",blank=True,)
# UML Attribute
    endDate = MetadataAtomicField.Factory("datefield",blank=True,)







class Machine(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Machine"
    _title       = "Machine"
    _description = "A description of a machine used by a particular platform."

    def __init__(self,*args,**kwargs):
        super(Machine,self).__init__(*args,**kwargs)


    # UML Attribute
    machineName = MetadataAtomicField.Factory("charfield",blank=False,)
# UML Attribute
    machineSystem = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    machineLibrary = MetadataAtomicField.Factory("charfield",blank=True,)
    machineLibrary.help_text = "A library residing on this machine."
                # UML Attribute
    machineDescription = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    machineLocation = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    machineOperatingSystem = MetadataEnumerationField(enumeration='cim_1_8_1.OperatingSystemType',blank=True,)
# UML Attribute
    machineType = MetadataEnumerationField(enumeration='cim_1_8_1.MachineType',blank=True,)
# UML Attribute
    machineVendor = MetadataEnumerationField(enumeration='cim_1_8_1.MachineVendorType',blank=True,)
# UML Attribute
    machineInterconnect = MetadataEnumerationField(enumeration='cim_1_8_1.InterconnectType',blank=True,)
# UML Attribute
    machineMaximumProcessors = MetadataAtomicField.Factory("integerfield",blank=True,)
# UML Attribute
    machineCoresPerProcessor = MetadataAtomicField.Factory("integerfield",blank=True,)
# UML Attribute
    machineProcessorType = MetadataEnumerationField(enumeration='cim_1_8_1.ProcessorType',blank=True,)



class StandardName(CodeList):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "StandardName"
    _title       = "Standard Name"
    _description = "Describes a name given to an entity from a recognised standard.  The CIM records the standard and the name.  For example, the standard might be CF and the name might be atmospheric_pressure."

    def __init__(self,*args,**kwargs):
        super(StandardName,self).__init__(*args,**kwargs)


    # UML Attribute
    standard = MetadataManyToOneField(sourceModel='cim_1_8_1.StandardName',targetModel='cim_1_8_1.Standard',blank=True,)
    standard.help_text = "Details of the standard being used."



class Daily_360(Calendar):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Daily_360"
    _title       = "Daily 360"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(Daily_360,self).__init__(*args,**kwargs)




class Genealogy(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Genealogy"
    _title       = "Genealogy"
    _description = "A record of a document's history.  A genealogy element contains a textual description and a set of relationships.  Each relationship has a type and a reference to some target.  There are different relationships for different document types."

    def __init__(self,*args,**kwargs):
        super(Genealogy,self).__init__(*args,**kwargs)




class ResponsibleParty(GMD_ResponsibleParty):

    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ResponsibleParty"
    _title       = "Responsible Party"
    _description = "A CIM-specific ResponsibleParty.  Sub-classes the gmd ResponsibleParty type and adds the attribute abbreviation."

    def __init__(self,*args,**kwargs):
        super(ResponsibleParty,self).__init__(*args,**kwargs)


    # UML Attribute
    abbreviation = MetadataAtomicField.Factory("charfield",blank=True,)




class PerpetualPeriod(Calendar):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "PerpetualPeriod"
    _title       = "Perpetual Period"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(PerpetualPeriod,self).__init__(*args,**kwargs)




class RealCalendar(Calendar):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "RealCalendar"
    _title       = "Real Calendar"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(RealCalendar,self).__init__(*args,**kwargs)



class SpatialRegridding(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "SpatialRegridding"
    _title       = "Spatial Regridding"
    _description = "Characteristics of the scheme used to interpolate a field from one grid (source grid) to another (target grid).Documents should use either the spatialRegriddingStandardMethod _or_ the spatialRegriddingUserMethod, but not both."

    def __init__(self,*args,**kwargs):
        super(SpatialRegridding,self).__init__(*args,**kwargs)


    # UML Attribute
    spatialRegriddingDimension = MetadataEnumerationField(enumeration='cim_1_8_1.SpatialRegriddingDimensionType',blank=True,)
# UML Attribute
    spatialRegriddingStandardMethod = MetadataEnumerationField(enumeration='cim_1_8_1.SpatialRegriddingStandardMethodType',blank=True,)
# UML Attribute
    spatialRegriddingUserMethod = MetadataManyToOneField(sourceModel='cim_1_8_1.SpatialRegridding',targetModel='cim_1_8_1.SpatialRegriddingUserMethod',blank=True,)


class ComponentLanguage(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ComponentLanguage"
    _title       = "Component Language"
    _description = "Details of the programming language a component is written in. There is an assumption that all EntryPoints use the same ComponentLanguage."

    def __init__(self,*args,**kwargs):
        super(ComponentLanguage,self).__init__(*args,**kwargs)


    # UML Attribute
    name = MetadataAtomicField.Factory("charfield",blank=False,)
    name.help_text = "The name of the language"


class Composition(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Composition"
    _title       = "Composition"
    _description = "The set of Couplings used by a Component.  Couplings can only occur between child components.  That is, a composition must belong to an ancestor component of the components whose fields are being connected."

    def __init__(self,*args,**kwargs):
        super(Composition,self).__init__(*args,**kwargs)


    # UML Attribute
    coupling = MetadataManyToOneField(sourceModel='cim_1_8_1.Composition',targetModel='cim_1_8_1.Coupling',blank=False,)
# UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=False,)


class ConnectionProperty(Property):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ConnectionProperty"
    _title       = "Connection Property"
    _description = "A ConnectionProperty is a name/value pair used to specify OASIS-specific properties."

    def __init__(self,*args,**kwargs):
        super(ConnectionProperty,self).__init__(*args,**kwargs)




class Connection(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Connection"
    _title       = "Connection"
    _description = "A Connection represents a link from a source DataSource to a target DataSource.  These can either be ComponentProperties (ie: the values come from an internal component) or DataObjects (ie: the values come from an external file).   It can be associated with another software component (a transformer).  If present, the rate, lag, timeTransformation, and spatialRegridding override that of the parent coupling.Note that there is the potential for multiple connectionSource &amp; connectionTarget and multiple couplingSources &amp; couplingTargets.  This may lead users to wonder how to match up a connection source (a ComponentProperty) with its coupling source (a SoftwareComponent). Clever logic is not required though; because the sources and targets are listed by reference, they can be found in a CIM document and the parent can be navigated to from there - there is no need to consult the source or target of the coupling."

    def __init__(self,*args,**kwargs):
        super(Connection,self).__init__(*args,**kwargs)


    # UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    type = MetadataEnumerationField(enumeration='cim_1_8_1.ConnectionType',blank=True,)
    type.help_text = "The type of Connection"
                # UML Attribute
    purpose = MetadataEnumerationField(enumeration='cim_1_8_1.DataPurpose',blank=True,)
    purpose.help_text = "Describes why this connection is being made.  Possible values include: boundaryCondition, initialCondition, Forcing."
                # UML Attribute
    timeProfile = MetadataManyToOneField(sourceModel='cim_1_8_1.Connection',targetModel='cim_1_8_1.Timing',blank=True,)
    timeProfile.help_text = "All information having to do with the rate of this connection; the times that it is active.  This overrides any rate of a Coupling."
                # UML Attribute
    timeLag = MetadataManyToOneField(sourceModel='cim_1_8_1.Connection',targetModel='cim_1_8_1.TimeLag',blank=True,)
    timeLag.help_text = " The coupling field used in the target at a given time corresponds to a field produced by the source at a previous time. "
                # UML Attribute
    spatialRegridding = MetadataManyToManyField(sourceModel='cim_1_8_1.Connection',targetModel='cim_1_8_1.SpatialRegridding',blank=True,)
    spatialRegridding.help_text = "Characteristics of the scheme used to interpolate a field from one grid (source grid) to another (target grid) "
                # UML Attribute
    timeTransformation = MetadataManyToOneField(sourceModel='cim_1_8_1.Connection',targetModel='cim_1_8_1.TimeTransformation',blank=True,)
    timeTransformation.help_text = "Temporal transformation performed on the coupling field before or after regridding onto the target grid. "
                # UML Attribute
    connectionSource = MetadataManyToOneField(sourceModel='cim_1_8_1.Connection',targetModel='cim_1_8_1.ConnectionEndPoint',blank=True,)
    connectionSource.help_text = "The source property being connected.  (note that there can be multiple sources)  This is optional; the file/component source may have already been specified by the couplingSource."
                # UML Attribute
    connectionTarget = MetadataManyToOneField(sourceModel='cim_1_8_1.Connection',targetModel='cim_1_8_1.ConnectionEndPoint',blank=True,)
    connectionTarget.help_text = "The target property being connected.  This is optional to support the way that input is handled in the CMIP5 questionnaire."
                # UML Attribute
    transformer = MetadataManyToOneField(sourceModel='cim_1_8_1.Connection',targetModel='cim_1_8_1.ProcessorComponent',blank=True,)
    transformer.help_text = "An in-line transformer.  This references a fully-described transformer (typically that forms part of the top-level composition) used in the context of this coupling.  It is used instead of separately specifying a spatialRegridding, timeTransformation, etc. here."
                # UML Attribute
    priming = MetadataManyToOneField(sourceModel='cim_1_8_1.Connection',targetModel='cim_1_8_1.DataSource',blank=True,)
    priming.help_text = "A priming source is one that is active on the first available timestep only (before proper coupling can ocurr).  It can either be described here explicitly, or else a separate coupling/connection with a timing profile that is active on only the first timestep can be created."
                # UML Attribute
    connectionProperty = MetadataManyToOneField(sourceModel='cim_1_8_1.Connection',targetModel='cim_1_8_1.ConnectionProperty',blank=True,)


class SoftwareComponent(DataSource):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False
    _abstract = True

    _name        = "SoftwareComponent"
    _title       = "Software Component"
    _description = "A SofwareCompnent is an abstract component from which all other components derive.  It represents an element that takes input data and generates output data.  A SoftwareCompnent can include nested child components.  Every component can have componentProperties which describe the scientific properties that a component simulates (for example, temperature, pressure, etc.) and the numerical properties that influence how a component performs its simulation (for example, the force of gravity). A SoftwareComponent can also have a Deployment, which describes how software is deployed onto computing resources.  And a SoftwareComponent can have a composition, which describes how ComponentProperties are coupled together either to/from other SoftwareComponents or external data files.  The properties specified by a component's composition must be owned by that component or a child of that component; child components cannot couple together their parents' properties."

    def __init__(self,*args,**kwargs):
        super(SoftwareComponent,self).__init__(*args,**kwargs)


    # UML Attribute
    shortName = MetadataAtomicField.Factory("charfield",blank=False,)
    shortName.help_text = "The name of the model (that is used internally)."
                # UML Attribute
    longName = MetadataAtomicField.Factory("charfield",blank=True,)
    longName.help_text = "The name of the model (that is recognized externally)."
                # UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)
    description.help_text = "A free-text description of the component."
                # UML Attribute
    license = MetadataAtomicField.Factory("charfield",blank=True)
    #license = MetadataManyToOneField(sourceModel='cim_1_8_1.SoftwareComponent',targetModel='cim_1_8_1.License',blank=True,)
    license.help_text = "The license held by this piece of software"
                # UML Attribute
    componentProperties = MetadataManyToOneField(sourceModel='cim_1_8_1.SoftwareComponent',targetModel='cim_1_8_1.ComponentProperties',blank=True,)
    componentProperties.help_text = "The properties that this model simulates and/or couples."
                # UML Attribute
    scientificProperties = MetadataManyToOneField(sourceModel='cim_1_8_1.SoftwareComponent',targetModel='cim_1_8_1.ScientificProperties',blank=True,)
    scientificProperties.help_text = "The properties that this model simulates and/or couples. ScientificProperties contain those properties that describe _how_ a model simulates.  (Although, the distinction between numerical and scientific may be unused - all properties can be stored under the generic ComponentProperties attribute)."
                # UML Attribute
    numericalProperties = MetadataManyToOneField(sourceModel='cim_1_8_1.SoftwareComponent',targetModel='cim_1_8_1.NumericalProperties',blank=True,)
    numericalProperties.help_text = "The properties that this model simulates and/or couples. NumericalProperties contain those properties that describe _what_ a model simulates.  (Although, the distinction between numerical and scientific may be unused - all properties can be stored under the generic ComponentProperties attribute)."
                # UML Attribute
    embedded = MetadataAtomicField.Factory("booleanfield",blank=True,)
    embedded.help_text = "An embedded component cannot exist on its own as an atomic piece of software; instead it is embedded within another (parent) component. When embedded equals true, the SoftwareComponent has a corresponding piece of software (otherwise it is acting as a virtual component which may be inexorably nested within a piece of software along with several other virtual components)."
                # UML Attribute
    responsibleParty = MetadataManyToManyField(sourceModel='cim_1_8_1.SoftwareComponent',targetModel='cim_1_8_1.ResponsibleParty',blank=True,)
# UML Attribute
    releaseDate = MetadataAtomicField.Factory("datefield",blank=True,null=True)
    releaseDate.help_text = "The date of publication of the software component code (as opposed to the date of publication of the metadata document, or the date of deployment of the model)"
                # UML Attribute
    previousVersion = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    fundingSource = MetadataAtomicField.Factory("charfield",blank=True,)
    fundingSource.help_text = "The entities that funded this software component."
                # UML Attribute
    citation = MetadataManyToOneField(sourceModel='cim_1_8_1.SoftwareComponent',targetModel='cim_1_8_1.gmd_CI_Citation_Type',blank=True,)
# UML Attribute
    onlineResource =  MetadataAtomicField.Factory("urlfield",blank=True,)
    onlineResource.help_text = "Provides a URL location for this model."
                # UML Attribute
    couplingFramework = MetadataEnumerationField(enumeration='cim_1_8_1.CouplingFrameworkType',blank=True,)
    couplingFramework.help_text = "The coupling framework that this entire component conforms to."
                # UML Attribute
    componentLanguage = MetadataManyToOneField(sourceModel='cim_1_8_1.SoftwareComponent',targetModel='cim_1_8_1.ComponentLanguage',blank=True,)
# UML Attribute
    grid = MetadataManyToOneField(sourceModel='cim_1_8_1.SoftwareComponent',targetModel='cim_1_8_1.gml_AbstractGeometryType',blank=True,)
    grid.help_text = "A reference to the grid that is used by this component."


class Rank(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Rank"
    _title       = "Rank"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(Rank,self).__init__(*args,**kwargs)


    # UML Attribute
    rankValue = MetadataAtomicField.Factory("integerfield",blank=True,)
# UML Attribute
    rankMin = MetadataAtomicField.Factory("integerfield",blank=True,)
# UML Attribute
    rankMax = MetadataAtomicField.Factory("integerfield",blank=True,)
# UML Attribute
    rankIncrement = MetadataAtomicField.Factory("integerfield",blank=True,)


class TimeLag(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "TimeLag"
    _title       = "Time Lag"
    _description = "The coupling field used in the target at a given time corresponds to a field produced by the source at a previous time. This lag specifies the difference in time."

    def __init__(self,*args,**kwargs):
        super(TimeLag,self).__init__(*args,**kwargs)


    # UML Attribute
    value = MetadataAtomicField.Factory("integerfield",blank=True,)
# UML Attribute
    units = MetadataEnumerationField(enumeration='cim_1_8_1.TimingUnits',blank=True,)



class SpatialRegriddingProperty(Property):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "SpatialRegriddingProperty"
    _title       = "Spatial Regridding Property"
    _description = "Used for OASIS-specific regridding information (ie: masked, order, normalisation, etc.)"

    def __init__(self,*args,**kwargs):
        super(SpatialRegriddingProperty,self).__init__(*args,**kwargs)



class ComponentProperties(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ComponentProperties"
    _title       = "Component Properties"
    _description = "Just acting as a container for multiple component properties."

    def __init__(self,*args,**kwargs):
        super(ComponentProperties,self).__init__(*args,**kwargs)




class TimeTransformation(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "TimeTransformation"
    _title       = "Time Transformation"
    _description = "Characteristics of the scheme used to interpolate a field from one grid (source grid) to another (target grid) "

    def __init__(self,*args,**kwargs):
        super(TimeTransformation,self).__init__(*args,**kwargs)


    # UML Attribute
    mappingType = MetadataEnumerationField(enumeration='cim_1_8_1.TimeMappingType',blank=False,)
# UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)


class Dependencies(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Dependencies"
    _title       = "Dependencies"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(Dependencies,self).__init__(*args,**kwargs)




@MetadataDocument()
class ProcessorComponent(SoftwareComponent):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ProcessorComponent"
    _title       = "Processor Component"
    _description = "A ProcessorComponent is a component which does not model some physical phenomena.  It still processes data, but it is not a scientific model in the strict sense.  Examples of ProcessorComponents include transformers and post-processors.  ProcessorComponents may be assocaited with a DataProcessing activity as opposed to a Simulation activity."

    def __init__(self,*args,**kwargs):
        super(ProcessorComponent,self).__init__(*args,**kwargs)


    # UML Attribute
    type = MetadataEnumerationField(enumeration='cim_1_8_1.ProcessorComponentType',blank=False,)
    type.help_text = "Describes the type of component.  There can be multiple types."
                # UML Attribute
    conservative = MetadataAtomicField.Factory("booleanfield",blank=False,)
    conservative.help_text = "A conservative component conserves fluxes across corresponding times and areas for different grids."
                # UML Attribute
    spatialRegridding = MetadataManyToManyField(sourceModel='cim_1_8_1.ProcessorComponent',targetModel='cim_1_8_1.SpatialRegridding',blank=True,)
    spatialRegridding.help_text = "Characteristics of the scheme used to interpolate a field from one grid (source grid) to another (target grid) "
                # UML Attribute
    timeTransformation = MetadataManyToOneField(sourceModel='cim_1_8_1.ProcessorComponent',targetModel='cim_1_8_1.TimeTransformation',blank=True,)
    timeTransformation.help_text = " Temporal transformation performed on the coupling field before or after regridding onto the target grid. "


class Coupling(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Coupling"
    _title       = "Coupling"
    _description = "A coupling represents a set of Connections between a source and target component.  Couplings can be complete or incomplete.  If they are complete then they must include all Connections between model properties.  If they are incomplete then the connections can be underspecified or not listed at all."

    def __init__(self,*args,**kwargs):
        super(Coupling,self).__init__(*args,**kwargs)


    # UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)
    description.help_text = "A free-text description of the coupling."
                # UML Attribute
    type = MetadataEnumerationField(enumeration='cim_1_8_1.ConnectionType',blank=True,)
    type.help_text = "Describes the method of coupling."
                # UML Attribute
    purpose = MetadataEnumerationField(enumeration='cim_1_8_1.DataPurpose',blank=False,)
# UML Attribute
    fullySpecified = MetadataAtomicField.Factory("booleanfield",blank=False,)
    fullySpecified.help_text = "If true then the coupling is fully-specified.  If false then not every Connection has been described within the coupling."
                # UML Attribute
    timeProfile = MetadataManyToOneField(sourceModel='cim_1_8_1.Coupling',targetModel='cim_1_8_1.Timing',blank=True,)
    timeProfile.help_text = "Describes how often the coupling takes place."
                # UML Attribute
    timeLag = MetadataManyToOneField(sourceModel='cim_1_8_1.Coupling',targetModel='cim_1_8_1.TimeLag',blank=True,)
    timeLag.help_text = " The coupling field used in the target at a given time corresponds to a field produced by the source at a previous time. "
                # UML Attribute
    spatialRegridding = MetadataManyToManyField(sourceModel='cim_1_8_1.Coupling',targetModel='cim_1_8_1.SpatialRegridding',blank=True,)
    spatialRegridding.help_text = "Characteristics of the scheme used to interpolate a field from one grid (source grid) to another (target grid) "
                # UML Attribute
    timeTransformation = MetadataManyToOneField(sourceModel='cim_1_8_1.Coupling',targetModel='cim_1_8_1.TimeTransformation',blank=True,)
    timeTransformation.help_text = "Temporal transformation performed on the coupling field before or after regridding onto the target grid. "
                # UML Attribute
    couplingSource = MetadataManyToOneField(sourceModel='cim_1_8_1.Coupling',targetModel='cim_1_8_1.CouplingEndPoint',blank=False,)
    couplingSource.help_text = "The source component of the coupling.  (note that there can be multiple sources)"
                # UML Attribute
    couplingTarget = MetadataManyToOneField(sourceModel='cim_1_8_1.Coupling',targetModel='cim_1_8_1.CouplingEndPoint',blank=False,)
    couplingTarget.help_text = "The target component of the coupling"
                # UML Attribute
    transformer = MetadataManyToOneField(sourceModel='cim_1_8_1.Coupling',targetModel='cim_1_8_1.ProcessorComponent',blank=True,)
    transformer.help_text = "An in-line transformer.  This references a fully-described transformer (typically that forms part of the top-level composition) used in the context of this coupling.  It is used instead of separately specifying a spatialRegridding, timeTransformation, etc. here."
                # UML Attribute
    priming = MetadataManyToOneField(sourceModel='cim_1_8_1.Coupling',targetModel='cim_1_8_1.DataSource',blank=True,)
    priming.help_text = "A priming source is one that is active on the first available timestep only (before proper coupling can ocurr).  It can either be described here explicitly, or else a separate coupling/connection with a timing profile that is active on only the first timestep can be created."
                # UML Attribute
    couplingProperty = MetadataManyToOneField(sourceModel='cim_1_8_1.Coupling',targetModel='cim_1_8_1.CouplingProperty',blank=True,)




class EntryPoint(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "EntryPoint"
    _title       = "Entry Point"
    _description = "Describes a function or subroutine of a SoftwareComponent.  BFG will use these EntryPoints to define a schedule of subroutine calls for a coupled model.  Currently, a very basic schedule can be approximated by using the proceeds and follows attributes, however a more complete system is required for full BFG compatibility.  Every EntryPoint can have a set of arguments associated with it.  These reference (previously defined) ComponentProperties."

    def __init__(self,*args,**kwargs):
        super(EntryPoint,self).__init__(*args,**kwargs)


    # UML Attribute
    name = MetadataAtomicField.Factory("charfield",blank=False,)
# UML Attribute
    type = MetadataEnumerationField(enumeration='cim_1_8_1.EntryPointType',blank=True,)
# UML Attribute
    proceeds = MetadataAtomicField.Factory("charfield",blank=True,)
    proceeds.help_text = "A list of the names of entryPoints that this entryPoint must poeceed"
                # UML Attribute
    follows = MetadataAtomicField.Factory("charfield",blank=True,)
    follows.help_text = "A list of the names of entryPoints that this entryPoint must follow"
                # UML Attribute
    argument = MetadataManyToOneField(sourceModel='cim_1_8_1.EntryPoint',targetModel='cim_1_8_1.ComponentProperty',blank=True,)
    argument.help_text = "A reference to an argument used by this EntryPoint"



@MetadataDocument()
class ModelComponent(SoftwareComponent):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ModelComponent"
    _title       = "Model Component"
    _description = "A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time."

    def __init__(self,*args,**kwargs):
        super(ModelComponent,self).__init__(*args,**kwargs)


    # UML Attribute
    type = MetadataEnumerationField(enumeration='cim_1_8_1.ModelComponentType',blank=False,)
    type.help_text = "Describes the type of component.  There can be multiple types."
                # UML Attribute
    timing = MetadataManyToOneField(sourceModel='cim_1_8_1.ModelComponent',targetModel='cim_1_8_1.Timing',blank=True,)
    timing.help_text = "Describes information about how this component simulates time."


class ComponentProperty(DataSource):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ComponentProperty"
    _title       = "Component Property"
    _description = "ComponentProperties include things that a component simulates (ie: pressure, humidity) and things that prescribe that simulation (ie: gravity, choice of advection scheme).  Note that this is a specialisation of shared::DataSource. data::DataObject is also a specialisation of shared::DataSource.  This allows software::Connections and/or activity::Conformance to refer to either ComponentProperties or DataObjects.  "

    def __init__(self,*args,**kwargs):
        super(ComponentProperty,self).__init__(*args,**kwargs)


    # UML Attribute
    shortName = MetadataAtomicField.Factory("charfield",blank=False,)
# UML Attribute
    longName = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    units = MetadataEnumerationField(enumeration='cim_1_8_1.UnitType',blank=True,)
# UML Attribute
    standardName = MetadataManyToOneField(sourceModel='cim_1_8_1.ComponentProperty',targetModel='cim_1_8_1.StandardName',blank=True,)
    standardName.help_text = "The standard name that this property is known as (for example, its CF name)"
                # UML Attribute
    value = MetadataManyToOneField(sourceModel='cim_1_8_1.ComponentProperty',targetModel='cim_1_8_1.PropertyValue',blank=True,)
    value.help_text = "The value of the property (not applicable to fields)"
                # UML Attribute
    citation = MetadataManyToOneField(sourceModel='cim_1_8_1.ComponentProperty',targetModel='cim_1_8_1.gmd_CI_Citation_Type',blank=True,)
# UML Attribute
    intent = MetadataEnumerationField(enumeration='cim_1_8_1.ComponentPropertyIntentType',blank=True,)
    intent.help_text = "The direction that this property is intended to be coupled: in, out, or inout."
                # UML Attribute
    represented = MetadataAtomicField.Factory("booleanfield",blank=False,)
    represented.help_text = "When set to false, means that this property is not used by the component. Covers the case when, for instance, a modeler chooses not to represent some property in their model.  (But still allows meaningful comparisons between components which _do_ model this property.)"
                # UML Attribute
    grid = MetadataManyToOneField(sourceModel='cim_1_8_1.ComponentProperty',targetModel='cim_1_8_1.gml_AbstractGeometryType',blank=True,)
    grid.help_text = "A reference to the grid that this property maps onto; may override the ModelComponent grid."



class ScientificProperties(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ScientificProperties"
    _title       = "Scientific Properties"
    _description = "This is just being used as a container for component properties."

    def __init__(self,*args,**kwargs):
        super(ScientificProperties,self).__init__(*args,**kwargs)




@MetadataDocument()
class StatisticalModelComponent(SoftwareComponent):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "StatisticalModelComponent"
    _title       = "Statistical Model Component"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(StatisticalModelComponent,self).__init__(*args,**kwargs)


    # UML Attribute
    type = MetadataEnumerationField(enumeration='cim_1_8_1.StatisticalModelComponentType',blank=False,)
    type.help_text = "Describes the type of component.  There can be multiple types."
                # UML Attribute
    timing = MetadataManyToOneField(sourceModel='cim_1_8_1.StatisticalModelComponent',targetModel='cim_1_8_1.Timing',blank=True,)


class Parallelisation(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Parallelisation"
    _title       = "Parallelisation"
    _description = "Describes how a deployment has been parallelised across a computing platform."

    def __init__(self,*args,**kwargs):
        super(Parallelisation,self).__init__(*args,**kwargs)


    # UML Attribute
    processes = MetadataAtomicField.Factory("integerfield",blank=False,)
# UML Attribute
    rank = MetadataManyToOneField(sourceModel='cim_1_8_1.Parallelisation',targetModel='cim_1_8_1.Rank',blank=True,)
# UML Attribute
# schedule is unused


class ConnectionEndPoint(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ConnectionEndPoint"
    _title       = "Connection End Point"
    _description = "The source/target of a connetion.  This is a DataSource (a ComponnetProperty or DataContent).  This is a separate class in order to associate an instanceID with the DataSource; this is used to identify which particular instance is being coupled in case the same DataSource is used more than once in a coupled model (this may be required for BFG).  Realistically, tihe instanceID is unlikely to be used for a connection, only for a coupling.  It is provided here for consistency."

    def __init__(self,*args,**kwargs):
        super(ConnectionEndPoint,self).__init__(*args,**kwargs)


    # UML Attribute
    dataSource = MetadataManyToOneField(sourceModel='cim_1_8_1.ConnectionEndPoint',targetModel='cim_1_8_1.DataSource',blank=False,)
# UML Attribute
    instanceID = MetadataManyToOneField(sourceModel='cim_1_8_1.ConnectionEndPoint',targetModel='cim_1_8_1.Identifier',blank=True,)
    instanceID.help_text = "If the same datasource is used more than once in a coupled model then a method for identifying which particular instance is being referenced is needed (for BFG)."
                # UML Attribute
    connectionProperty = MetadataManyToOneField(sourceModel='cim_1_8_1.ConnectionEndPoint',targetModel='cim_1_8_1.ConnectionProperty',blank=True,)
    connectionProperty.help_text = "The place to describe features specific to the source/target of a connection."


class CouplingEndPoint(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "CouplingEndPoint"
    _title       = "Coupling End Point"
    _description = "The source/target of a coupling.  This is a DataSource (a SoftwareComponent or DataObject).  This is a separate class in order to associate an instanceID with the DataSource; this is used to identify which particular instance is being coupled in case the same DataSource is used more than once in a coupled model (this may be required for BFG)."

    def __init__(self,*args,**kwargs):
        super(CouplingEndPoint,self).__init__(*args,**kwargs)


    # UML Attribute
    dataSource = MetadataManyToOneField(sourceModel='cim_1_8_1.CouplingEndPoint',targetModel='cim_1_8_1.DataSource',blank=False,)
# UML Attribute
    instanceID = MetadataManyToOneField(sourceModel='cim_1_8_1.CouplingEndPoint',targetModel='cim_1_8_1.Identifier',blank=True,)
    instanceID.help_text = "If the same datasource is used more than once in a coupled model then a method for identifying which particular instance is being referenced is needed (for BFG)."
                # UML Attribute
    couplingProperty = MetadataManyToOneField(sourceModel='cim_1_8_1.CouplingEndPoint',targetModel='cim_1_8_1.CouplingProperty',blank=True,)
    couplingProperty.help_text = "A place to describe features specific to the source/target of a coupling"


class CouplingProperty(Property):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "CouplingProperty"
    _title       = "Coupling Property"
    _description = "A CouplingProperty is a name/value pair used to specify OASIS-specific properties."

    def __init__(self,*args,**kwargs):
        super(CouplingProperty,self).__init__(*args,**kwargs)






class SpatialRegriddingUserMethod(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "SpatialRegriddingUserMethod"
    _title       = "Spatial Regridding User Method"
    _description = "Allows users to bypass the SpatialRegriddingStandardMethod and instead provide a set of weights and addresses for regridding via a file."

    def __init__(self,*args,**kwargs):
        super(SpatialRegriddingUserMethod,self).__init__(*args,**kwargs)


    # UML Attribute
    name = MetadataAtomicField.Factory("charfield",blank=False,)
# UML Attribute
    file = MetadataManyToOneField(sourceModel='cim_1_8_1.SpatialRegriddingUserMethod',targetModel='cim_1_8_1.DataObject',blank=True,)


class NumericalProperties(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "NumericalProperties"
    _title       = "Numerical Properties"
    _description = "This is just being used as a container for component properties."

    def __init__(self,*args,**kwargs):
        super(NumericalProperties,self).__init__(*args,**kwargs)




class Deployment(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Deployment"
    _title       = "Deployment"
    _description = "Gives information about the technical properties of a component: what machine it was run on, which compilers were used, how it was parallised, etc.A deployment basically associates a deploymentDate with a Platform.  A deployment only exists if something has been deployed.  A platform, in contrast, can exist independently, waiting to be used in deployments."

    def __init__(self,*args,**kwargs):
        super(Deployment,self).__init__(*args,**kwargs)


    # UML Attribute
    deploymentDate = MetadataAtomicField.Factory("datetimefield",blank=True,)
# UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    parallelisation = MetadataManyToOneField(sourceModel='cim_1_8_1.Deployment',targetModel='cim_1_8_1.Parallelisation',blank=True,)
# UML Attribute
    platform = MetadataManyToOneField(sourceModel='cim_1_8_1.Deployment',targetModel='cim_1_8_1.Platform',blank=True,)
    platform.help_text = "The platform that this deployment has been run on.  It is optional to allow for unconfigured models, that nonetheless specify their parallelisation constraints (a feature needed by OASIS)."
                # UML Attribute
    executableName = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    executableArgument = MetadataAtomicField.Factory("charfield",blank=True,)


class ComponentLanguageProperty(Property):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ComponentLanguageProperty"
    _title       = "Component Language Property"
    _description = "This provides a place to include language-specific information.  Every property is basically a name/value pair, where the names are things like: moduleName, reservedUnits, reservedNames (these are all examples of Fortran-specific properties). "

    def __init__(self,*args,**kwargs):
        super(ComponentLanguageProperty,self).__init__(*args,**kwargs)




class Timing(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Timing"
    _title       = "Timing"
    _description = "Provides information about the rate of couplings and connections and/or the timing characteristics of individual components - for example, the start and stop times that the component was run for or the units of time that a component is able to model (in a single timestep)."

    def __init__(self,*args,**kwargs):
        super(Timing,self).__init__(*args,**kwargs)


    # UML Attribute
    start = MetadataAtomicField.Factory("datetimefield",blank=True,)
# UML Attribute
    end = MetadataAtomicField.Factory("datetimefield",blank=True,)
# UML Attribute
    rate = MetadataAtomicField.Factory("integerfield",blank=True,)
# UML Attribute
    units = MetadataEnumerationField(enumeration='cim_1_8_1.TimingUnits',blank=False,)
# UML Attribute
    variableRate = MetadataAtomicField.Factory("booleanfield",blank=True,)
    variableRate.help_text = "Describes whether or not the model supports a variable timestep.  If set to true, then rate should not be specified."

