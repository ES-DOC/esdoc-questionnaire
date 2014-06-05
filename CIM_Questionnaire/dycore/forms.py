from django_cim_forms.forms import *

from dycore.models import *

#def setup_dycoreforms():
try:
#    print "setup_dycoreforms"
    DycoreScientificProperty_form = MetadataFormFactory(DycoreScientificProperty,name="DycoreScientificProperty_form",form=Property_form)
    DycoreScientificProperty_formset = MetadataFormSetFactory(DycoreScientificProperty,DycoreScientificProperty_form,name="DycoreScientificProperty_formset",extra=0)

    DycoreModel_form = MetadataFormFactory(DycoreModel,name="DycoreModel_form",subForms={"responsibleParties":"ResponsibleParty_formset","properties":"DycoreScientificProperty_formset","citations":"Citation_formset"})
    DycoreModel_formset = MetadataFormSetFactory(DycoreModel,DycoreModel_form,name="DycoreModel_formset")
#    print "success"
except DatabaseError:
 #   print "error"
    pass
