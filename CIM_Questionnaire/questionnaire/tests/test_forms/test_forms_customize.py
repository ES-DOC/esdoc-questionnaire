from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer
from CIM_Questionnaire.questionnaire.forms.forms_customize import create_model_customizer_form_data, create_standard_property_customizer_form_data, create_scientific_property_customizer_form_data

class Test(TestQuestionnaireBase):

    def test_create_model_customizer_form_data(self):
        """Test creation of initial form data for model_customizer form."""

        vocabularies = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(self.customizer,vocabularies)

        model_customizer_data = create_model_customizer_form_data(model_customizer,standard_category_customizers,scientific_category_customizers)

        # TODO: ENSURE model_customizer_data CORRESPONDS TO EXPECTED VALUES

    def test_create_standard_property_customizer_form_data(self):
        """Test creation of initial form data for standard_customizer formset."""

        vocabularies = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(self.customizer,vocabularies)

        standard_property_customizers_data = [
            create_standard_property_customizer_form_data(model_customizer,standard_property_customizer)
            for standard_property_customizer in standard_property_customizers
        ]

        # TODO: ENSURE standard_property_customizers_data CORRESPONDS TO EXPECTED VALUES

    def test_create_scientific_property_customizer_form_data(self):
        """Test creation of initial form data for standard_customizer formset."""

        vocabularies = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(self.customizer,vocabularies)

        scientific_property_customizers_data = {}
        for vocabulary_key,scientific_property_customizer_dict in scientific_property_customizers.iteritems():
            scientific_property_customizers_data[vocabulary_key] = {}
            for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
                scientific_property_customizers_data[vocabulary_key][component_key] = [
                    create_scientific_property_customizer_form_data(model_customizer,scientific_property_customizer)
                    for scientific_property_customizer in scientific_property_customizers[vocabulary_key][component_key]
                ]
        # TODO: ENSURE scientific_property_customizers_data CORRESPONDS TO EXPECTED VALUES


