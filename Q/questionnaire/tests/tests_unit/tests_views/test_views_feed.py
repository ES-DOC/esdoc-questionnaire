####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

"""
.. module:: test_views_user
.. moduleauthor:: Allyn Treshansky <allyn.treshansky@colorado.edu>

Tests the views associated w/ feeds

"""

from django.core.urlresolvers import reverse
from lxml import etree as et
import StringIO

from Q.questionnaire.q_utils import FuzzyInt, xpath_fix, get_index
from Q.questionnaire.tests.test_base import TestQBase, create_realization, incomplete_test
from Q.questionnaire.views.views_feed import *


# don't need to call this fn, if I use 'et.HTMLParser' as below
# def unescape_html(text):
#     return text.replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", '"').replace("&gt;",">").replace("&lt;","<").replace("&nbsp;", " ")


class Test(TestQBase):

    def setUp(self):
        super(Test, self).setUp()
        self.test_project = QProject.objects.get(name__iexact="test_project")
        self.test_ontology = self.test_project.ontologies.get(name__iexact="test_ontology")
        self.test_proxy = self.test_ontology.model_proxies.get(name__iexact="model")
        self.test_realization = create_realization(
            ontology=self.test_ontology,
            model_proxy=self.test_proxy,
            project=self.test_project,
            owner=self.test_user,
        )
        self.test_realization.is_root = True
        # just pretend that the document is complete so that it can be published...
        # (I don't actually care about content for these tests)
        self.test_realization.is_complete = True
        self.publication_v1 = self.test_realization.publish()
        self.assertIsNotNone(self.publication_v1)
        self.publication_v2 = self.test_realization.publish()
        self.assertIsNotNone(self.publication_v2)

    def tearDown(self):
        super(Test, self).tearDown()

    def test_feed_view(self):
        parser = et.HTMLParser()
        query_limit = FuzzyInt(0, 20)
        with self.assertNumQueries(query_limit):
            request_url = reverse("feed", kwargs={})
            response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        tree_node = et.parse(StringIO.StringIO(response.content), parser)
        entries = xpath_fix(tree_node, "//entry")
        self.assertIsNotNone(entries)
        self.assertEqual(len(entries), 2)

    def test_feed_project_view(self):
        parser = et.HTMLParser()
        query_limit = FuzzyInt(0, 20)
        with self.assertNumQueries(query_limit):
            request_url = reverse("feed_project", kwargs={
                "project_name": self.test_project.name,
            })
            response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        tree_node = et.parse(StringIO.StringIO(response.content), parser)
        entries = xpath_fix(tree_node, "//entry")
        self.assertIsNotNone(entries)
        self.assertEqual(len(entries), 2)
        # now test that an invalid project fails...
        with self.assertNumQueries(query_limit):
            request_url = reverse("feed_project", kwargs={
                "project_name": "invalid",
            })
            response = self.client.get(request_url)
        self.assertEqual(response.status_code, 400)

    def test_feed_project_ontology_view(self):
        parser = et.HTMLParser()
        query_limit = FuzzyInt(0, 20)
        with self.assertNumQueries(query_limit):
            request_url = reverse("feed_project_ontology", kwargs={
                "project_name": self.test_project.name,
                "ontology_key": self.test_ontology.get_key(),
            })
            response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        tree_node = et.parse(StringIO.StringIO(response.content), parser)
        entries = xpath_fix(tree_node, "//entry")
        self.assertIsNotNone(entries)
        self.assertEqual(len(entries), 2)
        # now test that an invalid ontology fails...
        with self.assertNumQueries(query_limit):
            request_url = reverse("feed_project_ontology", kwargs={
                "project_name": self.test_project.name,
                "ontology_key": "invalid",

            })
            response = self.client.get(request_url)
        self.assertEqual(response.status_code, 400)

    def test_feed_project_ontology_proxy_view(self):
        parser = et.HTMLParser()
        query_limit = FuzzyInt(0, 20)
        with self.assertNumQueries(query_limit):
            request_url = reverse("feed_project_ontology_proxy", kwargs={
                "project_name": self.test_project.name,
                "ontology_key": self.test_ontology.get_key(),
                "document_type": self.test_proxy.name.lower(),
            })
            response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        tree_node = et.parse(StringIO.StringIO(response.content), parser)
        entries = xpath_fix(tree_node, "//entry")
        self.assertIsNotNone(entries)
        self.assertEqual(len(entries), 2)
        # now test that an invalid proxy fails...
        with self.assertNumQueries(query_limit):
            request_url = reverse("feed_project_ontology_proxy", kwargs={
                "project_name": self.test_project.name,
                "ontology_key": self.test_ontology.get_key(),
                "document_type": "invalid",
            })
            response = self.client.get(request_url)
        self.assertEqual(response.status_code, 400)

    def test_publication_latest_view(self):
        parser = et.HTMLParser()
        query_limit = FuzzyInt(0, 20)
        with self.assertNumQueries(query_limit):
            request_url = reverse("publication_latest", kwargs={
                "project_name": self.test_project.name,
                "ontology_key": self.test_ontology.get_key(),
                "document_type": self.test_proxy.name.lower(),
                "publication_name": self.test_realization.get_key(),
            })
            response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        tree_node = et.parse(StringIO.StringIO(response.content), parser)
        model = get_index(xpath_fix(tree_node, "//model"), 0)
        self.assertIsNotNone(model)
        self.assertEqual(response.content, self.publication_v2.content)
        # now test that an invalid publication name fails...
        with self.assertNumQueries(query_limit):
            request_url = reverse("publication_latest", kwargs={
                "project_name": self.test_project.name,
                "ontology_key": self.test_ontology.get_key(),
                "document_type": self.test_proxy.name.lower(),
                "publication_name": "invalid",
            })
            response = self.client.get(request_url)
        self.assertEqual(response.status_code, 400)

    def test_publication_version_view(self):
        parser = et.HTMLParser()
        query_limit = FuzzyInt(0, 20)
        with self.assertNumQueries(query_limit):
            request_url = reverse("publication_version", kwargs={
                "project_name": self.test_project.name,
                "ontology_key": self.test_ontology.get_key(),
                "document_type": self.test_proxy.name.lower(),
                "publication_name": self.test_realization.get_key(),
                "publication_version": "1.0.0",
            })
            response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        tree_node = et.parse(StringIO.StringIO(response.content), parser)
        model = get_index(xpath_fix(tree_node, "//model"), 0)
        self.assertIsNotNone(model)
        self.assertEqual(response.content, self.publication_v1.content)
        # now test that an invalid version fails...
        with self.assertNumQueries(query_limit):
            request_url = reverse("publication_version", kwargs={
                "project_name": self.test_project.name,
                "ontology_key": self.test_ontology.get_key(),
                "document_type": self.test_proxy.name.lower(),
                "publication_name": self.test_realization.get_key(),
                "publication_version": "invalid",
            })
            response = self.client.get(request_url)
        self.assertEqual(response.status_code, 400)

