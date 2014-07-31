####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.conf import settings
from django.contrib.sites.models import Site

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase

from CIM_Questionnaire.questionnaire.models.metadata_site import MetadataSiteTypes, MetadataSite, get_metadata_site, get_metadata_site_type


class TestMetadataSite(TestQuestionnaireBase):


    def setUp(self):

        # don't need all the questionnaire-specific stuff for these tests
        #super(TestMetadataSite,self).setUp()

        site_id = settings.SITE_ID
        default_site = Site.objects.get(pk=site_id)
        default_metadata_site = get_metadata_site(default_site)
        self.assertIsNone(default_metadata_site)

        test_site = Site(name="test_site", domain="www.test.com")
        test_site.save()
        test_metadata_site = get_metadata_site(test_site)
        self.assertIsNotNone(test_metadata_site)

        self.test_site = test_site
        self.test_metadata_site = test_metadata_site

    # MetadataSite creation testing is happening implicitly in setUp above
    #def test_create_site(self):
    #    pass


    def test_delete_site(self):

        test_metadata_site_pk = self.test_metadata_site.pk
        self.test_site.delete()
        self.assertRaises(MetadataSite.DoesNotExist, MetadataSite.objects.get, pk=test_metadata_site_pk )

    def test_get_metadata_site_type(self):

        # in theory I could set type to any string
        # but in practice, it's restricted to choices in the admin form
        # and that's the only place it gets set
        # note that models don't automatically call clean on save

        self.test_metadata_site.type = MetadataSiteTypes.PROD
        self.test_metadata_site.save()
        self.assertEqual(get_metadata_site_type(self.test_site), "PROD")

        self.test_metadata_site.type = MetadataSiteTypes.TEST
        self.test_metadata_site.save()
        self.assertEqual(get_metadata_site_type(self.test_site), "TEST")

        self.test_metadata_site.type = MetadataSiteTypes.LOCAL
        self.test_metadata_site.save()
        self.assertEqual(get_metadata_site_type(self.test_site), "LOCAL")