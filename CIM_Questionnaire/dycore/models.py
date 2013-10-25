from django.db import models
from django import forms
from django.utils.functional import curry

from django_cim_forms.cim_1_5.models import *
from django_cim_forms.models import *

class DataFormat_enumeration(MetadataEnumeration):
   _enum = ["ASCII","HDF (before version 5)","HDF5 (version 5 or higher)","GRIB1","GRIB2","NetCDF (before version 4)","NetCDF4 (version 4 or higher)",]

class Parallelization_enumeration(MetadataEnumeration):
   _enum = ["Message Passing Interface (MPI)","OpenMP","Hybrid: MPI and OpenMP","Hybrid: MPI, utilization of GPGPU accelerator hardware","Hybrid: OpenMP, utilization of GPGPU accelerator hardware","Hybrid: MPI, OpenMP, utilization of GPGPU accelerator hardware",]

class DycoreScientificProperties_cv(MetadataControlledVocabulary):
    _cv_name = "dycore_scientific_properties"
    _name = "DycoreScientificProperties_cv"
    pass

class DycoreScientificProperty(MetadataProperty):
    _name = "DycoreScientificProperty"
    _title = "Dycore Scientific Property"

    cvClass = DycoreScientificProperties_cv

    def __init__(self,*args,**kwargs):
        self.referencingModels.add("dycore.DycoreModel")
        super(DycoreScientificProperty,self).__init__(*args,**kwargs)

## NO LONGER SPECIFYING RESTRICTION BY PROJECT CLASS INSTANCE (WHICH WAS COG-SPECIFIC)
## NOW SPECIFYING THE ACTUAL PERMISSION STRING
##@CIMDocument("modelComponent","shortName","cog.models.project.Project(short_name__iexact=DCMIP-2012)")
@CIMDocument("modelComponent","shortName","cog.dcmip-2012_user_permission")
class DycoreModel(ModelComponent):
    _name = "DycoreModel"
    _title = "Atmospheric Dynamical Core Component"

    _fieldTypes = {}
    _fieldTypeOrder = None
    _fieldOrder = None
    _initialValues = {}

    project = MetadataEnumerationField(enumeration="cim_1_5.ActivityProject_enumeration",open=True)

    institution = MetadataAtomicField.Factory("charfield",max_length=BIG_STRING,blank=False)
    version = MetadataAtomicField.Factory("charfield",max_length=BIG_STRING,blank=True)

    parallelization = MetadataEnumerationField(enumeration="dycore.Parallelization_enumeration",open=True,blank=True)
    parallelization.verbose_name = "Parallelization Approach"

    dataFormat  = MetadataEnumerationField(enumeration="dycore.DataFormat_enumeration",open=True,blank=True)
    dataFormat.verbose_name = "Native Data Format of IO Data"

    properties = MetadataManyToManyField(sourceModel="dycore.DycoreModel",targetModel="dycore.DycoreScientificProperty")
    properties.verbose_name = "Scientific Properties"

    def __unicode__(self):
        return u'%s: %s' % (self.getName(), self.shortName)

    def __init__(self,*args,**kwargs):
        super(DycoreModel,self).__init__(*args,**kwargs)
        self.registerFieldType(FieldType("BASIC","Basic Properties"),["institution","version","parallelization","dataFormat"])
        self.registerFieldType(FieldType("MODEL_DESCRIPTION","Component Description"),["project"])
        self.registerFieldType(FieldType("PROPERTIES","Scientific Properties"),["properties"])
        self.setFieldTypeOrder(["MODEL_DESCRIPTION","BASIC","PROPERTIES"])
        self.setFieldOrder([
            "shortName","longName","type","project","description",
            "version","releaseDate","parallelization","dataFormat","componentLanguage","onlineResource","institution","fundingSource","responsibleParties","citations",
            "properties",
        ])
        self.setInitialValues({
            "embedded"          : False,
            "type"              : "AtmosDynamicalCore",
            "project"           : "DCMIP-2012",
#            "properties"        : DycoreScientificProperty.getProperties(filter="all"),
# curry this fn; it only gets called later on if initial=True
# (this way, I prevent creating unnecesary properties)
            "properties"        : curry(DycoreScientificProperty.getProperties,filter="all"),
            "componentLanguage" : "Fortran",
            "parallelization"   : "Hybrid: MPI and OpenMP",
            "dataFormat"        : "NetCDF4 (version 4 or higher)",
        })
        citations = self.getField("citations").getTargetModelClass()
        citations.setFieldOrder(["title","collectiveTitle"])
        citations.customizeFields({
            "title"             : {"verbose_name" : "Citation", "help_text" : "The common title of the publication.  For example, \"Smith et al. (1999)\"."},
            "collectiveTitle"   : {"verbose_name" : "Bibliographic entry", "help_text": "The complete bibliographic reference of this publication.", "_required" : True},
# I AM HERE
#            "horizontalGrid.discretizationType" : { "logically rectangular"}
        })
        
#def setup_dycoremodel():
try:
    DycoreModel.customizeFields({
        "shortName"     : {"_unique" : True, "verbose_name" : "Model Acronym", "help_text" : "The acronym commonly used to describe the model",},
        "longName"      : {"help_text" : "The full name of the model with all acronyms spelled out",},
        "type"          : {"_readonly" : True, "_required" : True,},
        "project"       : {"_readonly" : True,},
        "componentLanguage" : {"_open" : False},
        "responsibleParties" : {"verbose_name" : "Contact Information"},
        "description"   : {"help_text" : "A short characterization of the model, such as would appear in a published reference. For example, \"The HadGEM2-ES model was a two stage development from HadGEM1, representing improvements in the physical model (leading to HadGEM2-AO) and the addition of earth system components and coupling (leading to HadGEM2-ES)...\"",},
        "citations"     : {"verbose_name" : "Model Documentation", "help_text" : "List of technical reports, key journal papers for dynamical core and tracer advection scheme.",},
        "onlineResource": {"help_text" : "Web address for model download (if publicly released)"},
        "releaseDate"   : {"help_text" : "Release date of component (if applicable)."},
    })

    # customize the fields of related models...
    citations = DycoreModel._meta.get_field_by_name("citations")[0].getTargetModelClass()
    if citations:
        citations.customizeFields({
            "title"             : {"verbose_name" : "Citation", "help_text" : "The common title of the publication.  For example, <p>Staniforth and Wood (2008)</p> in case of two authors or <p>White et al. (2005)</p> in case of more than two authors.",},
            "collectiveTitle"   : {"verbose_name" : "Bibliographic entry", "help_text": "The complete bibliographic reference of this publication.  For example, <p>Staniforth A., and N. Wood, 2008: Aspects of the dynamical core of a nonhydrostatic, deep-atmosphere, unified weather and climate-prediciton model. J Comput. Phys., 227, 3445-3464</p> in the case of two authors or <p>White A. A., B. J. Hoskins, I. Roulstone, and A. Staniforth, 2005: Consistent approximate models of the global atmosphere: shallow, deep, hydrostatic, quasi-hydrostatic and non-hydrostatic. Quart. J. Roy. Meteorol. Soc., 131, 2081-2107</p> in the case of more than two authors.", "_required" : True,},
        })
except DatabaseError:
    # this will fail on syncdb; once I move to South, it won't matter
    pass

#def setup_dycorescientificproperties_cv():
try:
    DycoreScientificProperties_cv.loadCV()
except DatabaseError:
    # this will fail on syncdb; once I move to South, it won't matter
    pass
