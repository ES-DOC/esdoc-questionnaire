from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase

from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel

from CIM_Questionnaire.questionnaire.forms.forms_edit import create_existing_edit_forms_from_models, get_data_from_edit_forms

from CIM_Questionnaire.questionnaire.utils import get_data_from_formset, get_data_from_form

# from django.template.defaultfilters import slugify
# from CIM_Questionnaire.questionnaire.forms.forms_edit import create_model_form_data, create_standard_property_form_data, \
#     create_scientific_property_form_data, MetadataModelFormSetFactory, MetadataStandardPropertyInlineFormSetFactory, \
#     MetadataScientificPropertyInlineFormSetFactory
# from CIM_Questionnaire.questionnaire.models import MetadataProject, MetadataVersion, MetadataModelProxy, \
#     MetadataModelCustomizer, MetadataScientificPropertyCustomizer, MetadataModel, MetadataStandardProperty, \
#     MetadataScientificProperty
# from CIM_Questionnaire.questionnaire.models.metadata_model import create_models_from_components


class Test(TestQuestionnaireBase):

    def test_create_existing_edit_forms_from_models(self):

        test_models = self.model_realization.get_descendants(include_self=True)
        test_document_type = self.model_realization.name.lower()
        vocabularies_to_test = self.project.vocabularies.filter(document_type__iexact=test_document_type)

        # get the realization set...
        (test_models, test_standard_properties, test_scientific_properties) = \
            MetadataModel.get_existing_realization_set(test_models)

        # get the customization set...
        (test_model_customizer, test_standard_category_customizers, test_standard_property_customizers, test_scientific_category_customizers, test_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(self.model_customizer, vocabularies_to_test)

        # reorder the customizers a bit...
        flattened_test_scientific_property_customizers = {}
        for vocabulary_key, scientific_property_customizer_dict in test_scientific_property_customizers.iteritems():
            for component_key, scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
                model_key = u"%s_%s" % (vocabulary_key, component_key)
                flattened_test_scientific_property_customizers[model_key] = scientific_property_customizer_list

        # create the forms...
        (test_model_formset, test_standard_properties_formsets, test_scientific_properties_formsets) = \
            create_existing_edit_forms_from_models(test_models, test_model_customizer, test_standard_properties, test_standard_property_customizers, test_scientific_properties, flattened_test_scientific_property_customizers)

        # now check the form content...

        test_data = get_data_from_edit_forms(test_model_formset,test_standard_properties_formsets,test_scientific_properties_formsets)


        test_model_formset_data = get_data_from_formset(test_model_formset)
        test_data.update(test_model_formset_data)

    def test_save_valid_forms(self):

        (test_model_formset, test_standard_properties_formsets, test_scientific_properties_formsets) = self.get_new_edit_forms()

        import ipdb; ipdb.set_trace()