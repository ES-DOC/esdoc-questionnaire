
from django.core.urlresolvers import reverse

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.views.views_feed import MetadataFeed, validate_view_arguments, questionnaire_serialize


from CIM_Questionnaire.questionnaire.utils import FuzzyInt

class Test(TestQuestionnaireBase):

    def test_validate_view_arguments(self):

        kwargs = {
            "project_name" : self.project.name.lower(),
            "version_key" : self.version.get_key(),
            "model_name" : self.model_realization.name.lower(),
            "model_guid" : self.model_realization.guid,
        }

        # 1st time this is run, model is not published
        (validity, project, version, model, msg) = validate_view_arguments(**kwargs)
        self.assertEqual(validity, False)

        self.model_realization.publish(force_save=True)

        # 2nd time this is run, model is published
        (validity, project, version, model, msg) = validate_view_arguments(**kwargs)
        self.assertEqual(validity, True)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update( {"project_name" : "invalid" } )
        (validity, project, version, model, msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity, False)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update( { "version_key" : "invalid" } )
        (validity, project, version, model, msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity, False)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update( { "model_name" : "invalid" } )
        (validity, project, version, model, msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity, False)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update( { "model_name" : "responsibleparty" } )    # valid classname, but not a document
        (validity, project, version, model, msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity, False)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update( { "model_guid" : "invalid" } )
        (validity, project, version, model, msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity, False)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update( { "model_version" : -1 } )
        (validity, project, version, model, msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity, False)

        valid_kwargs = kwargs.copy()
        valid_kwargs.update( { "model_version" : 1 } )
        (validity, project, version, model, msg) = validate_view_arguments(**valid_kwargs)
        self.assertEqual(validity, True)

    # TODO: I KNOW THIS TEST FAILS
    # I DON'T KNOW HOW TO REDIRECT ATOM FEEDS [http://stackoverflow.com/questions/25817904/django-generate-error-on-atom-feed-request]
    def test_questionnaire_feed(self):

        # valid request
        request_url = reverse("feed", kwargs={})
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)

        # valid request
        request_url = reverse("feed_project", kwargs={ "project_name" : self.project.name} )
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)

        # invalid request
        request_url = reverse("feed_project", kwargs={ "project_name" : "invalid"} )
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 400)

        # valid request
        request_url = reverse("feed_project_version", kwargs={ "project_name" : self.project.name, "version_key" : self.version.get_key() } )
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)

        # invalid request
        request_url = reverse("feed_project_version", kwargs={ "project_name" : self.project.name, "version_key" : "invalid" } )
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 400)

        # valid request
        request_url = reverse("feed_project_version_proxy", kwargs={ "project_name" : self.project.name, "version_key" : self.version.get_key(), "model_name" : self.model_realization.proxy.name })
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)

        # invalid request
        request_url = reverse("feed_project_version_proxy", kwargs={ "project_name" : self.project.name, "version_key" : self.version.get_key(), "model_name" : "invalid" })
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 400)


