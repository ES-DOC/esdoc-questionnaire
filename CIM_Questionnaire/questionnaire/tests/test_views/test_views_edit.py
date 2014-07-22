import re

from django.core.urlresolvers import reverse
from django.contrib import messages

from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.views.views_edit import validate_view_arguments, questionnaire_edit_new, questionnaire_edit_existing, questionnaire_edit_help

from CIM_Questionnaire.questionnaire.forms.forms_edit import get_data_from_edit_forms

from CIM_Questionnaire.questionnaire.utils import FuzzyInt

class Test(TestQuestionnaireBase):

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

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"model_name":"responsibleparty"})    # valid classname, but not a document
        (validity,project,version,model_proxy,model_customizer,msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity,False)


    def test_questionnaire_edit_help_get(self):

        # wrap all view tests w/ a check for num db hits
        # (django testing framework adds ~15 hits of setup code)
        query_limit = FuzzyInt(0,20)
        with self.assertNumQueries(query_limit):
            request_url = reverse("edit_help")
            response = self.client.get(request_url)

        self.assertEqual(response.status_code,200)

    # def test_questionnaire_edit_new_get(self):
    #     project_name = "test"
    #     version_name = "test"
    #     model_name = "modelcomponent"
    #
    #     request_url = self.get_request_url(project_name=project_name,version_name=version_name,model_name=model_name)
    #     response = self.client.get(request_url,follow=True)
    #
    #
    #     # get the arguments passed to the context...
    #
    #     test_site = response.context["site"]
    #     test_project = response.context["project"]
    #     test_version = response.context["version"]
    #     test_model_proxy = response.context["model_proxy"]
    #     test_vocabularies = response.context["vocabularies"]
    #     test_site = response.context["model_customizer"]
    #     test_model_formset = response.context["model_formset"]
    #     test_standard_properties_formsets = response.context["standard_properties_formsets"]
    #     test_scientific_properties_formsets = response.context["scientific_properties_formsets"]
    #     test_questionnaire_version = response.context["questionnaire_version"]
    #     test_can_publish = response.context["can_publish"]
    #
    #     session_variables = self.client.session
    #     message_variables = [m for m in list(response.context["messages"])]
    #
    #     self.assertNotIn("root_model_id",session_variables)
    #     self.assertEqual(session_variables["checked_arguments"],True)
    #     self.assertEqual(response.status_code,200)
    #
    # def test_questionnaire_edit_new_POST(self):
    #
    #     project_name = self.project.name.lower()
    #     version_name = self.version.name.lower()
    #     model_name = self.model_realization.name.lower()
    #
    #     request_url = reverse("edit_new", kwargs = {
    #         "project_name" : project_name,
    #         "version_name" : version_name,
    #         "model_name" : model_name,
    #     })
    #
    #     edit_forms = self.get_new_edit_forms(project_name=project_name, version_name=version_name, model_name=model_name)
    #
    #     test_data = get_data_from_edit_forms(edit_forms["model_formset"], edit_forms["standard_properties_formsets"], edit_forms["scientific_properties_formsets"])
    #
    #     # ("follow=True" allows the context setup in the initial view to be retained in the redirected view [http://stackoverflow.com/questions/16143149/django-testing-check-messages-for-a-view-that-redirects])
    #     response = self.client.post(request_url, data=test_data, follow=True)
    #
    #     session_variables = self.client.session
    #     message_variables = [m for m in list(response.context["messages"])]
    #
    #     self.assertIn("root_model_id", session_variables)
    #     self.assertEqual(session_variables["checked_arguments"], True)
    #     self.assertEqual(len(message_variables),1)
    #     self.assertEqual(message_variables[0].tags,messages.DEFAULT_TAGS[messages.SUCCESS])
    #     self.assertEqual(response.status_code,200)
    #
    #     model_id = session_variables["root_model_id"]
    #     model = MetadataModel.objects.get(pk=model_id)
    #
