####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

from django.conf import settings
from Q.questionnaire.tests.test_base import TestQBase
from Q.questionnaire.models.models_sites import *


class TestQSite(TestQBase):

    def setUp(self):

        # don't need all the questionnaire-specific stuff for these tests
        # super(TestQSite, self).setUp()

        # this is running outside of any views, so dynamic_sites middleware has yet to run,
        # so I am forced to use DEFAULT_SITE_ID (since SITE_ID won't have been re-set yet),
        # that is fine for the scope of these tests
        site_id = settings.DEFAULT_SITE_ID
        default_site = Site.objects.get(pk=site_id)
        default_q_site = default_site.q_site
        self.assertIsNotNone(default_q_site)

        test_site = Site(name="test_site", domain="www.test.com")
        test_site.save()
        test_q_site = test_site.q_site
        self.assertIsNotNone(test_q_site)
        test_q_site.type = QSiteTypes.TEST
        test_q_site.save()

        self.test_site = test_site

    def tearDown(self):

        # don't need all the questionnaire-specific stuff for these tests
        # super(TestQSite, self).tearDown()

        pass

    def test_create_site(self):

        test_site = Site(name="another_test_site", domain="www.another_test.com")
        test_site.save()
        test_q_site = test_site.q_site
        self.assertIsNotNone(test_q_site)

    def test_delete_site(self):

        test_q_site_pk = self.test_site.q_site.pk
        self.test_site.delete()
        with self.assertRaises(QSite.DoesNotExist):
            QSite.objects.get(pk=test_q_site_pk)

    def test_get_site_type(self):

        test_q_site = self.test_site.q_site

        test_q_site.type = QSiteTypes.LOCAL
        test_q_site.save()
        self.assertEqual(get_site_type(self.test_site), "LOCAL")

        test_q_site.type = QSiteTypes.DEV
        test_q_site.save()
        self.assertEqual(get_site_type(self.test_site), "DEV")

        test_q_site.type = QSiteTypes.TEST
        test_q_site.save()
        self.assertEqual(get_site_type(self.test_site), "TEST")

        test_q_site.type = QSiteTypes.PROD
        test_q_site.save()
        self.assertEqual(get_site_type(self.test_site), "PROD")
