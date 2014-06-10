from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer
from CIM_Questionnaire.questionnaire.forms.forms_customize import create_model_customizer_form_data

class Test(TestQuestionnaireBase):

    def test_create_model_customizer_form_data(self):
        """Test creation of initial form data for model_customizer form."""

        vocabularies = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(self.customizer,vocabularies)

        model_customizer_data = create_model_customizer_form_data(model_customizer,standard_category_customizers,scientific_category_customizers)

        # TODO: ENSURE model_customizer_data CORRESPONDS TO EXPECTED VALUES


