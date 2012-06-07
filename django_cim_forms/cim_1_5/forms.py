from django_cim_forms.forms import *
from django_cim_forms.cim_1_5.models import *

##########################################
# all non-abstract forms used by the CIM #
##########################################

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

Timing_form = MetadataFormFactory(Timing,name="Timing_form")
Timing_formset = MetadataFormSetFactory(Timing,Timing_form,name="Timing_formset")

Coupling_form = MetadataFormFactory(Coupling,name="Coupling_form",subForms={"timeProfile" : "Timing_form"})
Coupling_formset = MetadataFormSetFactory(Coupling,Coupling_form,name="Coupling_formset")
