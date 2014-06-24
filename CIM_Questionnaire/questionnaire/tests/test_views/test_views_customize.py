__author__ = 'ben.koziol'

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase

from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy

from CIM_Questionnaire.questionnaire.forms.forms_customize import create_model_customizer_form_data, create_standard_property_customizer_form_data, create_scientific_property_customizer_form_data
from CIM_Questionnaire.questionnaire.forms.forms_customize import create_new_customizer_forms_from_models, create_existing_customizer_forms_from_models, create_customizer_forms_from_data, get_data_from_customizer_forms
from CIM_Questionnaire.questionnaire.forms.forms_customize import MetadataModelCustomizerForm, MetadataStandardPropertyCustomizerInlineFormSetFactory, MetadataScientificPropertyCustomizerInlineFormSetFactory
from CIM_Questionnaire.questionnaire.views.views_customize import questionnaire_customize_new, questionnaire_customize_existing, questionnaire_customize_help
from CIM_Questionnaire.questionnaire.views.views_customize import validate_view_arguments

class Test(TestQuestionnaireBase):

    def get_request_url(self,project_name="test",version_name="test",model_name="test"):
        """Return a URL suitable for client and factory testing."""

        request_url = u"/%s/customize/%s/%s/" % (project_name,version_name,model_name)
        return request_url

    def test_validate_view_arguments(self):

        kwargs = {
            "project_name" : "test",
            "version_name" : "test",
            "model_name" : "modelcomponent",
        }

        validate_view_arguments(**kwargs)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"project_name":"invalid"})
        invalid_response = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(invalid_response.status_code,400)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"version_name":"invalid"})
        invalid_response = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(invalid_response.status_code,400)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"model_name":"invalid"})
        invalid_response = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(invalid_response.status_code,400)


    def test_questionnaire_customize_help_get(self):

        request_url = u"/customize/help"
        response = self.client.get(request_url)

        self.assertEqual(response.status_code,200)


    def test_questionnaire_customize_help_post(self):

        request_url = u"/customize/help"
        response = self.client.post(request_url,{})

        self.assertEqual(response.status_code,200)

    def test_questionnaire_customize_new_get(self):

        project_name = "test"
        version_name = "test"
        model_name = "modelcomponent"

        request_url = self.get_request_url(project_name=project_name,version_name=version_name,model_name=model_name)
        response = self.client.get(request_url)

        self.assertEqual(response.status_code,200)

    def test_questionnaire_customize_new_post(self):

        test_model_name = "modelcomponent"
        model_proxy_to_customize = MetadataModelProxy.objects.get(version=self.version,name__iexact=test_model_name)
        vocabularies_to_customize = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_new_customizer_set(self.project,self.version,model_proxy_to_customize,vocabularies_to_customize)

        (model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets) = \
            create_new_customizer_forms_from_models(model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers,vocabularies_to_customize=vocabularies_to_customize)

        post_data = get_data_from_customizer_forms(model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets)
        # add some one-off entries that would normally be done in the interface...
        model_customizer_form_prefix = model_customizer_form.prefix
        if model_customizer_form_prefix:
            model_customizer_name_key = u"%s-name" % (model_customizer_form_prefix)
            model_customizer_vocabularies_key = u"%s-vocabularies" % (model_customizer_form_prefix)
        else:
            model_customizer_name_key = u"name"
            model_customizer_vocabularies_key = u"vocabularies"
        post_data[model_customizer_name_key] = "new_test_customizer"
        post_data[model_customizer_vocabularies_key] = [vocabulary.pk for vocabulary in model_customizer_form.get_current_field_value("vocabularies")]

        for (key, value) in post_data.iteritems():
            if value == u"None":
                post_data[key] = None

        request_url = self.get_request_url(project_name=self.project.name,version_name=self.version.name,model_name=test_model_name)
        response = self.client.post(request_url,post_data)

        import ipdb; ipdb.set_trace()
