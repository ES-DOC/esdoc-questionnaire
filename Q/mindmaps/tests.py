import os

from django.test import TestCase, Client

from django.core.urlresolvers import reverse
from urlparse import urlparse

from Q.mindmaps.models import *
from Q.mindmaps.views import *

from Q.questionnaire.q_utils import FuzzyInt

class TestMindMaps(TestCase):

    """
     The base class for all CIM Questionnaire tests
     provides a reusable test client
     and a default user, project, version, categorization, vocabulary
     as well as default proxies, customizers, and realizations
     to play with in child classes
    """

    test_source_name = "test"
    test_domains = ["https://raw.githubusercontent.com/IWCCT/es-fdl", ]
    test_url = "https://raw.githubusercontent.com/IWCCT/es-fdl/postbarcelona20140630/coupled-system/Components.mm"

    def setUp(self):

        # client for all tests (this is better-suited for testing views b/c, among other things, it has sessions, cookies, etc.)
        self.client = Client()

        # SETUP DEFAULT MINDMAPSOURCES
        test_source = MindMapSource(name=self.test_source_name)
        test_source.save()
        for domain in self.test_domains:
            test_domain = MindMapDomain(source=test_source,domain=domain)
            test_domain.save()

        source_qs = MindMapSource.objects.all()
        self.assertEqual(len(source_qs), 1)
        domains_qs = test_source.domains.all()
        self.assertEqual(len(domains_qs), len(self.test_domains))

        self.mindmap_source = test_source

    def tearDown(self):
        # this is for resetting things that are not db-related (ie: files, etc.)
        # but it's not needed for the db since each test is run in its own transaction

        parsed_url = urlparse(self.test_url)
        absolute_path = os.path.join(settings.MEDIA_ROOT, "mindmaps", parsed_url.path[1:])
        path_root = os.path.join(settings.MEDIA_ROOT, "mindmaps", parsed_url.path[1:].split("/")[0])

        # remove the file...
        if os.path.exists(absolute_path):
            os.remove(absolute_path)
        # remove any empty directories in the path...
        for path, dirs, files in os.walk(path_root, topdown=False):
            try:
                os.rmdir(path)
            except OSError:
                # directory was not empty
                pass

    def assertQuerysetEqual(self, qs1, qs2):
        """Tests that two django querysets are equal"""
        # the built-in TestCase method takes a qs and a list, which is confusing
        # this is more intuitive (see https://djangosnippets.org/snippets/2013/)

        pk = lambda o: o.pk
        return self.assertEqual(
            list(sorted(qs1, key=pk)),
            list(sorted(qs2, key=pk))
        )

    def assertFileExists(self, file_path, **kwargs):
        """Tests that a file exists"""

        msg = kwargs.pop("msg",None)
        file_exists = os.path.exists(file_path)

        return self.assertEqual(file_exists, True, msg=msg)

    def assertFileDoesntExist(self, file_path, **kwargs):
        """Tests that a file doesn't exist"""

        msg = kwargs.pop("msg",None)
        file_exists = os.path.exists(file_path)

        return self.assertEqual(file_exists,False,msg=msg)

    def test_views_mindmaps_index(self):

        # wrap all view tests w/ a check for num db hits
        # (django testing framework adds ~15 hits of setup code)
        query_limit = FuzzyInt(0,20)
        with self.assertNumQueries(query_limit):
            request_url = reverse("index")
            response = self.client.get(request_url, follow=True)

        self.assertEqual(response.status_code,200)

    def test_views_mindmaps_view_GET(self):

        # wrap all view tests w/ a check for num db hits
        # (django testing framework adds ~15 hits of setup code)
        query_limit = FuzzyInt(0,20)
        with self.assertNumQueries(query_limit):
            request_url = reverse("view")
            request_url += "?url=%s" % (self.test_url)
            response = self.client.get(request_url,follow=True)

        self.assertEqual(response.status_code,200)

        parsed_url = urlparse(self.test_url)
        absolute_path = os.path.join(settings.MEDIA_ROOT, "mindmaps", parsed_url.path[1:])
        self.assertFileExists(absolute_path)

    def test_views_mindmaps_view_POST(self):

        # wrap all view tests w/ a check for num db hits
        # (django testing framework adds ~15 hits of setup code)
        query_limit = FuzzyInt(0,20)
        with self.assertNumQueries(query_limit):
            request_url = reverse("view")
            data = {
                "url" : self.test_url
            }
            response = self.client.post(request_url, data, follow=True)

        self.assertEqual(response.status_code,200)

        parsed_url = urlparse(self.test_url)
        absolute_path = os.path.join(settings.MEDIA_ROOT, "mindmaps", parsed_url.path[1:])
        self.assertFileExists(absolute_path)

    def test_views_mindmaps_view_invalid_url(self):

        # wrap all view tests w/ a check for num db hits
        # (django testing framework adds ~15 hits of setup code)
        query_limit = FuzzyInt(0,20)
        with self.assertNumQueries(query_limit):
            request_url = reverse("view")
            data = {
                "url": "http://my.invalid.url/file.mm",
            }
            response = self.client.post(request_url, data, follow=True)

        self.assertEqual(response.status_code,400)

    def test_views_mindmaps_view_disabled_source(self):

        self.mindmap_source.enabled = False
        self.mindmap_source.save()

        # wrap all view tests w/ a check for num db hits
        # (django testing framework adds ~15 hits of setup code)
        query_limit = FuzzyInt(0,20)
        with self.assertNumQueries(query_limit):
            request_url = reverse("view")
            data = {
                "url" : self.test_url
            }
            response = self.client.post(request_url, data, follow=True)

        self.assertEqual(response.status_code,400)

        parsed_url = urlparse(self.test_url)
        absolute_path = os.path.join(settings.MEDIA_ROOT, "mindmaps", parsed_url.path[1:])
        self.assertFileDoesntExist(absolute_path)
