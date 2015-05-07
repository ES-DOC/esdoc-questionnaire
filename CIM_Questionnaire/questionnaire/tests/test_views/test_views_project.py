####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2014 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'ben.koziol'
__date__ = "Dec 01, 2014 3:00:00 PM"

"""
.. module:: test_views_project

Tests the Project Index view
"""

import json
from CIM_Questionnaire.questionnaire.tests.test_base import TestQuestionnaireBase, get_data_from_form, get_data_from_formset
from CIM_Questionnaire.questionnaire.utils import FuzzyInt
from CIM_Questionnaire.questionnaire.views.views_project import *


class Test(TestQuestionnaireBase):

    def get_context_dictionary(self, response):
        """
        returns the data dictionary that is passed to the context handler of the project view
        :param response:
        :return:
        """
        context_dictionary_keys = [
            # this is copied _exactly_ from the view
            "questionnaire_version",
            "site",
            "project",
            "can_join",
            "can_view",
            "can_edit",
            "can_customize",
            "document_options",
            "new_document_form",
            "existing_document_formset",
            "new_customization_form",
            "existing_customization_formset",
        ]

        context_dictionary = {}
        for key in context_dictionary_keys:
            context_dictionary[key] = response.context[key]

        return context_dictionary

    def setUp(self):

        super(Test, self).setUp()

        # create a brand-new project to use w/ some tests
        # (a brand-new project will have no existing customizations or documents)
        new_project = MetadataProject(
            name="new",
            title="new project",
            authenticated=False,
        )
        new_project.save()
        self.new_project = new_project

    def test_questionnaire_project_index_GET(self):

        query_limit = FuzzyInt(0, 25)

        request_url = reverse("project_index", kwargs={
            "project_name": self.downscaling_project.name,
        })
        with self.assertNumQueries(query_limit):
            response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)

        request_url = reverse("project_index", kwargs={
            "project_name": self.new_project.name,
        })
        with self.assertNumQueries(query_limit):
            response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)

    def test_questionnaire_project_index_POST_create_new_customization(self):

        request_url = reverse("project_index", kwargs={
            "project_name": self.downscaling_project.name,
        })
        response = self.client.get(request_url)
        context_dictionary = self.get_context_dictionary(response)

        new_customization_form = context_dictionary["new_customization_form"]
        new_document_form = context_dictionary["new_document_form"]
        existing_customization_formset = context_dictionary["existing_customization_formset"]
        existing_document_formset = context_dictionary["existing_document_formset"]
        document_options = json.loads(context_dictionary["document_options"])

        post_data = {}
        post_data.update(get_data_from_form(new_customization_form))
        post_data.update(get_data_from_form(new_document_form))
        post_data.update(get_data_from_formset(existing_customization_formset))
        post_data.update(get_data_from_formset(existing_document_formset))

        # manipulate post data as if user selected to create the 1st document type of the 1st ontology
        # and then check that the post redirects to the approriate new_url
        new_url_kwargs = {"project_name": self.downscaling_project.name, }
        post_data[u"%s-create" % new_customization_form.prefix] = True
        for ontology_id, documents in document_options.iteritems():
            post_data[u"%s-ontologies" % new_customization_form.prefix] = ontology_id
            new_url_kwargs["version_key"] = MetadataVersion.objects.get(pk=ontology_id).get_key()
            for document_id, document_name in documents.iteritems():
                post_data[u"%s-documents" % new_customization_form.prefix] = document_id
                new_url_kwargs["model_name"] = MetadataModelProxy.objects.get(pk=document_id).name.lower()
                break
            break
        new_url = reverse("customize_new", kwargs=new_url_kwargs)

        response = self.client.post(request_url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], new_url)

    def test_questionnaire_project_index_POST_create_new_document(self):

        request_url = reverse("project_index", kwargs={
            "project_name": self.downscaling_project.name,
        })
        response = self.client.get(request_url)
        context_dictionary = self.get_context_dictionary(response)

        new_customization_form = context_dictionary["new_customization_form"]
        new_document_form = context_dictionary["new_document_form"]
        existing_customization_formset = context_dictionary["existing_customization_formset"]
        existing_document_formset = context_dictionary["existing_document_formset"]
        document_options = json.loads(context_dictionary["document_options"])

        post_data = {}
        post_data.update(get_data_from_form(new_customization_form))
        post_data.update(get_data_from_form(new_document_form))
        post_data.update(get_data_from_formset(existing_customization_formset))
        post_data.update(get_data_from_formset(existing_document_formset))

        # manipulate post data as if user selected to create the 1st document type of the 1st ontology
        # and then check that the post redirects to the approriate new_url
        new_url_kwargs = {"project_name": self.downscaling_project.name, }
        post_data[u"%s-create" % new_document_form.prefix] = True
        for ontology_id, documents in document_options.iteritems():
            post_data[u"%s-ontologies" % new_document_form.prefix] = ontology_id
            new_url_kwargs["version_key"] = MetadataVersion.objects.get(pk=ontology_id).get_key()
            for document_id, document_name in documents.iteritems():
                post_data[u"%s-documents" % new_document_form.prefix] = document_id
                new_url_kwargs["model_name"] = MetadataModelProxy.objects.get(pk=document_id).name.lower()
                break
            break
        new_url = reverse("edit_new", kwargs=new_url_kwargs)

        response = self.client.post(request_url, data=post_data, follow=True)
        # don't bother checking the status_code; depending on which ontology/document combination is used,
        # the corresponding customization may not exist
        # self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], new_url)

    def test_questionnaire_project_index_POST_edit_existing_customization(self):

        request_url = reverse("project_index", kwargs={
            "project_name": self.downscaling_project.name,
        })
        response = self.client.get(request_url)
        context_dictionary = self.get_context_dictionary(response)

        new_customization_form = context_dictionary["new_customization_form"]
        new_document_form = context_dictionary["new_document_form"]
        existing_customization_formset = context_dictionary["existing_customization_formset"]
        existing_document_formset = context_dictionary["existing_document_formset"]

        post_data = {}
        post_data.update(get_data_from_form(new_customization_form))
        post_data.update(get_data_from_form(new_document_form))
        post_data.update(get_data_from_formset(existing_customization_formset))
        post_data.update(get_data_from_formset(existing_document_formset))

        # manipulate post data as if user selected to edit the 1st customization
        # and then check that the post redirects to the approriate new_url
        new_url_kwargs = {"project_name": self.downscaling_project.name, }
        post_data[u"%s-edit" % existing_customization_formset.prefix] = True
        for customization_form in existing_customization_formset:
            post_data[u"%s-selected" % customization_form.prefix] = True
            customization_id = customization_form.fields["id"].initial
            customization = MetadataModelCustomizer.objects.get(pk=customization_id)
            new_url_kwargs["version_key"] = customization.version.get_key()
            new_url_kwargs["model_name"] = customization.proxy.name.lower()
            new_url_kwargs["customizer_name"] = customization.name
            break
        new_url = reverse("customize_existing", kwargs=new_url_kwargs)

        response = self.client.post(request_url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], new_url)

    def test_questionnaire_project_index_POST_edit_existing_document(self):

        request_url = reverse("project_index", kwargs={
            "project_name": self.downscaling_project.name,
        })
        response = self.client.get(request_url)
        context_dictionary = self.get_context_dictionary(response)

        new_customization_form = context_dictionary["new_customization_form"]
        new_document_form = context_dictionary["new_document_form"]
        existing_customization_formset = context_dictionary["existing_customization_formset"]
        existing_document_formset = context_dictionary["existing_document_formset"]

        post_data = {}
        post_data.update(get_data_from_form(new_customization_form))
        post_data.update(get_data_from_form(new_document_form))
        post_data.update(get_data_from_formset(existing_customization_formset))
        post_data.update(get_data_from_formset(existing_document_formset))

        # manipulate post data as if user selected to edit the 1st document
        # and then check that the post redirects to the approriate new_url
        new_url_kwargs = {"project_name": self.downscaling_project.name, }
        post_data[u"%s-edit" % existing_document_formset.prefix] = True
        for document_form in existing_document_formset:
            post_data[u"%s-selected" % document_form.prefix] = True
            document_id = document_form.fields["id"].initial
            document = MetadataModel.objects.get(pk=document_id)
            new_url_kwargs["version_key"] = document.version.get_key()
            new_url_kwargs["model_name"] = document.proxy.name.lower()
            new_url_kwargs["model_id"] = document.pk
            break
        new_url = reverse("edit_existing", kwargs=new_url_kwargs)

        response = self.client.post(request_url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], new_url)

    def test_questionnaire_project_index_POST_view_existing_document(self):

        request_url = reverse("project_index", kwargs={
            "project_name": self.downscaling_project.name,
        })
        response = self.client.get(request_url)
        context_dictionary = self.get_context_dictionary(response)

        new_customization_form = context_dictionary["new_customization_form"]
        new_document_form = context_dictionary["new_document_form"]
        existing_customization_formset = context_dictionary["existing_customization_formset"]
        existing_document_formset = context_dictionary["existing_document_formset"]

        post_data = {}
        post_data.update(get_data_from_form(new_customization_form))
        post_data.update(get_data_from_form(new_document_form))
        post_data.update(get_data_from_formset(existing_customization_formset))
        post_data.update(get_data_from_formset(existing_document_formset))

        # manipulate post data as if user selected to view the 1st document
        # and then check that the post redirects to the approriate new_url
        new_url_kwargs = {"project_name": self.downscaling_project.name, }
        post_data[u"%s-view" % existing_document_formset.prefix] = True
        for document_form in existing_document_formset:
            post_data[u"%s-selected" % document_form.prefix] = True
            document_id = document_form.fields["id"].initial
            document = MetadataModel.objects.get(pk=document_id)
            new_url_kwargs["version_key"] = document.version.get_key()
            new_url_kwargs["model_name"] = document.proxy.name.lower()
            new_url_kwargs["model_id"] = document.pk
            break
        new_url = reverse("view_existing", kwargs=new_url_kwargs)

        response = self.client.post(request_url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], new_url)

    def test_questionnaire_project_index_POST_publish_existing_document(self):

        request_url = reverse("project_index", kwargs={
            "project_name": self.downscaling_project.name,
        })
        response = self.client.get(request_url)
        context_dictionary = self.get_context_dictionary(response)

        new_customization_form = context_dictionary["new_customization_form"]
        new_document_form = context_dictionary["new_document_form"]
        existing_customization_formset = context_dictionary["existing_customization_formset"]
        existing_document_formset = context_dictionary["existing_document_formset"]

        post_data = {}
        post_data.update(get_data_from_form(new_customization_form))
        post_data.update(get_data_from_form(new_document_form))
        post_data.update(get_data_from_formset(existing_customization_formset))
        post_data.update(get_data_from_formset(existing_document_formset))

        # manipulate post data as if user selected to publish the 1st document
        post_data[u"%s-publish" % existing_document_formset.prefix] = True
        for document_form in existing_document_formset:
            post_data[u"%s-selected" % document_form.prefix] = True
            document_id = document_form.fields["id"].initial
            break

        document = MetadataModel.objects.get(pk=document_id)
        self.assertEqual(document.is_published, False)
        self.assertEqual(int(document.get_major_version()), 0)

        response = self.client.post(request_url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        document = document.refresh()  # get the current state of the db
        self.assertEqual(document.is_published, True)
        self.assertEqual(int(document.get_major_version()), 1)

    def test_questionnaire_project_index_POST_join_project(self):

        request_url = reverse("project_index", kwargs={
            "project_name": self.downscaling_project.name,
        })
        response = self.client.get(request_url)
        context_dictionary = self.get_context_dictionary(response)

        new_customization_form = context_dictionary["new_customization_form"]
        new_document_form = context_dictionary["new_document_form"]
        existing_customization_formset = context_dictionary["existing_customization_formset"]
        existing_document_formset = context_dictionary["existing_document_formset"]

        post_data = {}
        post_data.update(get_data_from_form(new_customization_form))
        post_data.update(get_data_from_form(new_document_form))
        post_data.update(get_data_from_formset(existing_customization_formset))
        post_data.update(get_data_from_formset(existing_document_formset))

        # manipulate post data as if user selected to join this project
        post_data[u"project_join"] = True
        response = self.client.post(request_url, data=post_data)
        response_messages = [message for message in response.context["messages"]]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_messages), 1)
        self.assertEqual(response_messages[0].tags, messages.DEFAULT_TAGS[messages.SUCCESS])

    def test_questionnaire_project_index_POST_join_project(self):

        request_url = reverse("project_index", kwargs={
            "project_name": self.new_project.name,
        })
        response = self.client.get(request_url)
        context_dictionary = self.get_context_dictionary(response)

        new_customization_form = context_dictionary["new_customization_form"]
        new_document_form = context_dictionary["new_document_form"]
        existing_customization_formset = context_dictionary["existing_customization_formset"]
        existing_document_formset = context_dictionary["existing_document_formset"]

        post_data = {}
        post_data.update(get_data_from_form(new_customization_form))
        post_data.update(get_data_from_form(new_document_form))
        post_data.update(get_data_from_formset(existing_customization_formset))
        post_data.update(get_data_from_formset(existing_document_formset))

        # manipulate post data as if user selected to join this project
        post_data[u"project_join"] = True
        response = self.client.post(request_url, data=post_data)
        response_messages = [message for message in response.context["messages"]]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_messages), 1)
        self.assertEqual(response_messages[0].tags, messages.DEFAULT_TAGS[messages.SUCCESS])
