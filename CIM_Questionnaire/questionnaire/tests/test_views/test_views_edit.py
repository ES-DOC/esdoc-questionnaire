import re

from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.views.views_edit import validate_view_arguments, questionnaire_edit_new, questionnaire_edit_existing, questionnaire_edit_help


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
            "project_name" : "test",
            "version_name" : "test",
            "model_name" : "modelcomponent",
        }

        request = self.factory.get("")    # just a "dummy" request for testing

        validate_view_arguments(request,**kwargs)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"project_name":"invalid"})
        invalid_response = validate_view_arguments(request, **invalid_kwargs)
        self.assertEqual(invalid_response.status_code,400)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"version_name":"invalid"})
        invalid_response = validate_view_arguments(request, **invalid_kwargs)
        self.assertEqual(invalid_response.status_code,400)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"model_name":"invalid"})
        invalid_response = validate_view_arguments(request, **invalid_kwargs)
        self.assertEqual(invalid_response.status_code,400)

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

        session_variables = self.client.session
        message_variables = [m for m in list(response.context["messages"])]

        self.assertNotIn("root_model_id",session_variables)
        self.assertEqual(session_variables["checked_arguments"],True)
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


