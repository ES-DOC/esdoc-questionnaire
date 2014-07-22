from django_cim_forms.forms import *
from django_cim_forms.cim_1_5.models import *

##########################################
# all non-abstract forms used by the CIM #
##########################################

#def setup_cimforms():
try:
#    print "setup_cimforms"
    DataSource_form = MetadataFormFactory(DataSource,name="DataSource_form")
    DataSource_formset = MetadataFormSetFactory(DataSource,DataSource_form,name="DataSource_formset")

    DateRange_form = MetadataFormFactory(DateRange,name="DateRange_form")
    DateRange_formset = MetadataFormSetFactory(DateRange,DateRange_form,name="DateRange_formset")

    Calendar_form = MetadataFormFactory(Calendar,name="Calendar_form",subForms={"range":"DateRange_form"})
    Calendar_formset = MetadataFormSetFactory(Calendar,Calendar_form,name="Calendar_formset")

    NumericalRequirement_form = MetadataFormFactory(NumericalRequirement,name="NumericalRequirement_form")
    NumericalRequirement_formset = MetadataFormSetFactory(NumericalRequirement,NumericalRequirement_form,name="NumericalRequirement_formset")

    RequirementOption_form = MetadataFormFactory(RequirementOption,name="RequirementOption_form",subForms={"requirement":"NumericalRequirement_form"})
    RequirementOption_formset = MetadataFormSetFactory(RequirementOption,RequirementOption_form,name="RequirementOption_formset")

    CompositeNumericalRequirement_form = MetadataFormFactory(CompositeNumericalRequirement,name="CompositeNumericalRequirement_form",subForms={"requirementOptions":"RequirementOption_formset"})
    CompositeNumericalRequirement_formset = MetadataFormSetFactory(CompositeNumericalRequirement,CompositeNumericalRequirement_form,name="CompositeNumericalRequirement_formset")

    NumericalExperiment_form = MetadataFormFactory(NumericalExperiment,name="NumericalExperiment_form",subForms={"calendar":"Calendar_form","numericalRequirements":"CompositeNumericalRequirement_formset"})
    NumericalExperiment_formset = MetadataFormSetFactory(NumericalExperiment,NumericalExperiment_form,name="NumericalExperiment_formset")

    ResponsibleParty_form = MetadataFormFactory(ResponsibleParty,name="ResponsibleParty_form")
    ResponsibleParty_formset = MetadataFormSetFactory(ResponsibleParty,ResponsibleParty_form,name="ResponsibleParty_formset")

    Citation_form = MetadataFormFactory(Citation,name="Citation_form")
    Citation_formset = MetadataFormSetFactory(Citation,Citation_form,name="Citation_formset")

    HorizontalGrid_form = MetadataFormFactory(HorizontalGrid,name="HorizontalGrid_form")
    HorizontalGrid_formset = MetadataFormSetFactory(HorizontalGrid,HorizontalGrid_form,name="HorizontalGrid_formset")

    VerticalGrid_form = MetadataFormFactory(VerticalGrid,name="VerticalGrid_form")
    VerticalGrid_formset = MetadataFormSetFactory(VerticalGrid,VerticalGrid_form,name="VerticalGrid_formset")

    GridSpec_form = MetadataFormFactory(GridSpec,name="GridSpec_form",subForms={"horizontalGrid" : "HorizontalGrid_form", "verticalGrid" : "VerticalGrid_form"})
    GridSpec_formset = MetadataFormSetFactory(GridSpec,GridSpec_form,name="GridSpec_formset")

    Conformance_form = MetadataFormFactory(Conformance,name="Conformance_form")
    Conformance_formset = MetadataFormSetFactory(Conformance,Conformance_form,name="Conformance_formset")

    Timing_form = MetadataFormFactory(Timing,name="Timing_form")
    Timing_formset = MetadataFormSetFactory(Timing,Timing_form,name="Timing_formset")

    TimeLag_form = MetadataFormFactory(TimeLag,name="TimeLag_form")
    TimeLag_formset = MetadataFormSetFactory(TimeLag,TimeLag_form,name="TimeLag_formset")

    SpatialRegriddingUserMethod_form = MetadataFormFactory(SpatialRegriddingUserMethod,name="SpatialRegriddingUserMethod_form")
    SpatialRegriddingUserMethod_formset = MetadataFormSetFactory(SpatialRegriddingUserMethod,SpatialRegriddingUserMethod_form,name="SpatialRegriddingUserMethod_formset")

    SpatialRegridding_form = MetadataFormFactory(SpatialRegridding,name="SpatialRegridding_form",subForms={"spatialRegriddingUserMethod" : "SpatialRegriddingUserMethod_form"})
    SpatialRegridding_formset = MetadataFormSetFactory(SpatialRegridding,SpatialRegridding_form,name="SpatialRegridding_formset")

    TimeTransformation_form = MetadataFormFactory(TimeTransformation,name="TimeTransformation_form")
    TimeTransformation_formset = MetadataFormSetFactory(TimeTransformation,TimeTransformation_form,name="TimeTransformation_formset")

    Coupling_form = MetadataFormFactory(Coupling,name="Coupling_form",subForms={"timeProfile" : "Timing_form", "timeLag" : "TimeLag_form", "spatialRegridding" : "SpatialRegridding_formset", "timeTransformation" : "TimeTransformation_form",})
    Coupling_formset = MetadataFormSetFactory(Coupling,Coupling_form,name="Coupling_formset")

#    print "success"
except DatabaseError:
#    print "error"
    pass

