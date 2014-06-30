__author__ = 'allyn.treshansky'

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase

from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer, MetadataModelCustomizer, MetadataStandardPropertyCustomizer, MetadataScientificPropertyCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy
from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes

from CIM_Questionnaire.questionnaire.views.views_ajax import ajax_customize_subform

class Test(TestQuestionnaireBase):

    def test_ajax_customize_subform_new_get(self):

        test_model_name = "modelcomponent"
        model_proxy_to_customize = MetadataModelProxy.objects.get(version=self.version,name__iexact=test_model_name)
        vocabularies_to_customize = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(self.customizer,vocabularies_to_customize)

        self.assertEqual(model_customizer.proxy,model_proxy_to_customize)

        potential_properties_to_customize_subforms_for = model_customizer.standard_property_customizers.filter(field_type=MetadataFieldTypes.RELATIONSHIP)
        self.assertGreater(len(potential_properties_to_customize_subforms_for),0)
        property_to_customize_subform_for = potential_properties_to_customize_subforms_for[0]

        request_url = u"/ajax/customize_subform/?i=%s" % (property_to_customize_subform_for.pk)
        response = self.client.get(request_url,follow=True)

        self.assertEqual(response.status_code,200)
