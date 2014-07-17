import re

from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.views.views_edit import validate_view_arguments, questionnaire_edit_new, questionnaire_edit_existing, questionnaire_edit_help

from CIM_Questionnaire.questionnaire.forms.forms_edit import get_data_from_edit_forms

class Test(TestQuestionnaireBase):

    def get_request_url(self,project_name="test",version_name="test",model_name="test",document_id=""):
        """Return a URL suitable for client and factory testing."""

        if document_id:
            request_url = u"/%s/edit/%s/%s/%s/" % (project_name,version_name,model_name,document_id)
        else:
            request_url = u"/%s/edit/%s/%s/" % (project_name,version_name,model_name)
        return request_url

    def test_validate_view_arguments(self):

        kwargs = {
            "project_name" : self.project.name.lower(),
            "version_name" : self.version.name.lower(),
            "model_name" : self.model_realization.name.lower(),
        }

        (validity,project,version,model_proxy,model_customizer,msg) = validate_view_arguments(**kwargs)
        self.assertEqual(validity,True)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"project_name":"invalid"})
        (validity,project,version,model_proxy,model_customizer,msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity,False)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"version_name":"invalid"})
        (validity,project,version,model_proxy,model_customizer,msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity,False)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"model_name":"invalid"})
        (validity,project,version,model_proxy,model_customizer,msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity,False)

    def test_questionnaire_edit_help_get(self):

        request_url = u"/edit/help"
        response = self.client.get(request_url)

        self.assertEqual(response.status_code,200)


    def test_questionnaire_edit_help_post(self):

        request_url = u"/edit/help"
        response = self.client.post(request_url,{})

        self.assertEqual(response.status_code,200)

    def test_questionnaire_edit_new_get(self):
        project_name = "test"
        version_name = "test"
        model_name = "modelcomponent"

        request_url = self.get_request_url(project_name=project_name,version_name=version_name,model_name=model_name)
        response = self.client.get(request_url,follow=True)


        # get the arguments passed to the context...

        test_site = response.context["site"]
        test_project = response.context["project"]
        test_version = response.context["version"]
        test_model_proxy = response.context["model_proxy"]
        test_vocabularies = response.context["vocabularies"]
        test_site = response.context["model_customizer"]
        test_model_formset = response.context["model_formset"]
        test_standard_properties_formsets = response.context["standard_properties_formsets"]
        test_scientific_properties_formsets = response.context["scientific_properties_formsets"]
        test_questionnaire_version = response.context["questionnaire_version"]
        test_can_publish = response.context["can_publish"]

        session_variables = self.client.session
        message_variables = [m for m in list(response.context["messages"])]

        self.assertNotIn("root_model_id",session_variables)
        self.assertEqual(session_variables["checked_arguments"],True)
        self.assertEqual(response.status_code,200)

    def test_questionnaire_edit_new_POST(self):

        project_name = self.project.name.lower(),
        version_name = self.version.name.lower(),
        model_name = self.model_realization.name.lower()

        request_url = self.get_request_url(project_name=project_name, version_name=version_name, model_name=model_name)
        request_url = "/project/edit/version/modelcomponent/"

        response = self.client.get(request_url, follow=True)
        context = response.context

        test_model_formset = response.context["model_formset"]
        test_standard_properties_formsets = response.context["standard_properties_formsets"]
        test_scientific_properties_formsets = response.context["scientific_properties_formsets"]

        test_data = get_data_from_edit_forms(test_model_formset,test_standard_properties_formsets,test_scientific_properties_formsets)

        response = self.client.post(request_url, data=test_data, follow=True)

        self.assertEqual(response.status_code,200)





    def test_questionnaire_edit_new_customize_display(self):

        project_name = "test"
        version_name = "test"
        model_name = "modelcomponent"

        model_proxy_to_be_customized = MetadataModelProxy.objects.get(version=self.version,name__iexact=model_name)
        vocabularies_to_be_customized = self.project.vocabularies.filter(document_type__iexact=model_name)
        (test_model_customizer,test_standard_category_customizers,test_standard_property_customizers,test_scientific_category_customizers,test_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(self.customizer, vocabularies_to_be_customized)

        self.assertEqual(test_model_customizer.default,True)

        standard_property_customizer_to_test = test_standard_property_customizers[0]

        self.assertEqual(standard_property_customizer_to_test.displayed,True)
        standard_property_customizer_to_test.displayed = False
        standard_property_customizer_to_test.save()

        request_url = self.get_request_url(project_name=project_name,version_name=version_name,model_name=model_name)
        response = self.client.get(request_url,follow=True)

        session_variables = self.client.session
        message_variables = [m for m in list(response.context["messages"])]

        self.assertNotIn("root_model_id",session_variables)
        self.assertEqual(session_variables["checked_arguments"],True)
        self.assertEqual(response.status_code,200)
