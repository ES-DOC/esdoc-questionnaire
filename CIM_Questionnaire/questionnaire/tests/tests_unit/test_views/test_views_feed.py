
from django.core.urlresolvers import reverse

from CIM_Questionnaire.questionnaire.tests.test_base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.views.views_feed import validate_view_arguments, questionnaire_serialize


class Test(TestQuestionnaireBase):

    def test_validate_view_arguments(self):

        model = self.downscaling_model_component_realization_set["models"][0].get_root()
        kwargs = {
            "project_name": self.downscaling_project.name,
            "version_key": self.cim_1_8_1_version.get_key(),
            "model_name": model.name,
            "model_guid": model.guid,
        }

        # 1st time this is run, model is not published
        (validity, project, version, model, msg) = validate_view_arguments(**kwargs)
        self.assertFalse(validity)

        model.publish(force_save=True)  # (the actual publish fn is tested elsewhere)

        # 2nd time this is run, model is published
        (validity, project, version, model, msg) = validate_view_arguments(**kwargs)
        self.assertTrue(validity)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({
            "project_name": "invalid",
        })
        (validity, project, version, model, msg) = validate_view_arguments(**invalid_kwargs)
        self.assertFalse(validity)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({
            "version_key": "invalid",
        })
        (validity, project, version, model, msg) = validate_view_arguments(**invalid_kwargs)
        self.assertFalse(validity)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({
            "model_name": "invalid",
        })
        (validity, project, version, model, msg) = validate_view_arguments(**invalid_kwargs)
        self.assertFalse(validity)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({
            "model_name": "responsibleparty",  # valid classname, but not a document
        })
        (validity, project, version, model, msg) = validate_view_arguments(**invalid_kwargs)
        self.assertFalse(validity)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({
            "model_guid": "invalid",
        })
        (validity, project, version, model, msg) = validate_view_arguments(**invalid_kwargs)
        self.assertFalse(validity)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({
            "model_version": -1,
        })
        (validity, project, version, model, msg) = validate_view_arguments(**invalid_kwargs)
        self.assertFalse(validity)

        valid_kwargs = kwargs.copy()
        valid_kwargs.update({
            "model_version": 1,
        })
        (validity, project, version, model, msg) = validate_view_arguments(**valid_kwargs)
        self.assertTrue(validity)

    # TODO: I KNOW THIS TEST FAILS
    # I DON'T KNOW HOW TO REDIRECT ATOM FEEDS [http://stackoverflow.com/questions/25817904/django-generate-error-on-atom-feed-request]
    def test_questionnaire_feed(self):

        # valid request
        request_url = reverse("feed", kwargs={})
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)

        # valid request
        request_url = reverse("feed_project", kwargs={
            "project_name": self.downscaling_project.name,
        })
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)

        # invalid request
        request_url = reverse("feed_project", kwargs={
            "project_name": "invalid",
        })
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 400)

        # valid request
        request_url = reverse("feed_project_version", kwargs={
            "project_name": self.downscaling_project.name,
            "version_key": self.cim_1_8_1_version.get_key(),
        })
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)

        # invalid request
        request_url = reverse("feed_project_version", kwargs={
            "project_name": self.downscaling_project.name,
            "version_key": "invalid",
        })
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 400)

        # valid request
        request_url = reverse("feed_project_version_proxy", kwargs={
            "project_name": self.downscaling_project.name,
            "version_key": self.cim_1_8_1_version.get_key(),
            "model_name": self.downscaling_model_component_proxy_set["model_proxy"].name,
        })
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)

        # invalid request
        request_url = reverse("feed_project_version_proxy", kwargs={
            "project_name": self.downscaling_project.name,
            "version_key": self.cim_1_8_1_version.get_key(),
            "model_name": "invalid"
        })
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 400)
