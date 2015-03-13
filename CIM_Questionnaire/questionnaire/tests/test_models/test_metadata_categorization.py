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
.. module:: test_metadata_categorization

Tests the MetadataCategorization models
"""

import os
import shutil

from django.conf import settings

from CIM_Questionnaire.questionnaire.tests.test_base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.utils import model_to_data
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataStandardCategoryProxy, MetadataStandardPropertyProxy
from CIM_Questionnaire.questionnaire.models.metadata_version import MetadataVersion, UPLOAD_PATH as ONTOLOGY_UPLOAD_PATH
from CIM_Questionnaire.questionnaire.models.metadata_categorization import MetadataCategorization, UPLOAD_PATH as CATEGORIZATION_UPLOAD_PATH

###################
# local constants #
###################

TEST_ONTOLOGY_FILE = os.path.join(settings.MEDIA_ROOT, ONTOLOGY_UPLOAD_PATH, "test_version.xml")
TEST_CATEGORIZATION_FILE = os.path.join(settings.MEDIA_ROOT, CATEGORIZATION_UPLOAD_PATH, "test_categorization.xml")

#################################
# now for the actual test class #
#################################


class TestMetadataCategorization(TestQuestionnaireBase):

    def setUp(self):

        super(TestMetadataCategorization, self).setUp()

        test_ontology = MetadataVersion(
            name="test_ontology",
            version="1.0",
            file=TEST_ONTOLOGY_FILE,
        )
        test_ontology.save()
        test_ontology.register()

        self.test_ontology = test_ontology

        backup_categorization_file = u"%s.bak" % TEST_CATEGORIZATION_FILE
        backup_ontology_file = u"%s.bak" % TEST_ONTOLOGY_FILE
        shutil.copy2(TEST_CATEGORIZATION_FILE, backup_categorization_file)
        shutil.copy2(TEST_ONTOLOGY_FILE, backup_ontology_file)

    def tearDown(self):

        super(TestMetadataCategorization, self).tearDown()

        backup_categorization_file = u"%s.bak" % TEST_CATEGORIZATION_FILE
        backup_ontology_file = u"%s.bak" % TEST_ONTOLOGY_FILE
        shutil.copy2(backup_categorization_file, TEST_CATEGORIZATION_FILE)
        shutil.copy2(backup_ontology_file, TEST_ONTOLOGY_FILE)

    def test_create_categorization(self):

        n_categorizations = MetadataCategorization.objects.count()
        test_categorization = MetadataCategorization(
            name="test",
            file=TEST_CATEGORIZATION_FILE,
        )
        test_categorization.save()
        self.assertEqual(test_categorization.pk, n_categorizations+1)

    def test_delete_categorization(self):

        test_categorization = MetadataCategorization(
            name="test",
            file=TEST_CATEGORIZATION_FILE,
        )
        test_categorization.save()
        self.test_ontology.categorization = test_categorization
        self.test_ontology.save()
        test_categorization.register()

        test_categorization.delete()
        self.assertFalse(os.path.isfile(TEST_CATEGORIZATION_FILE))
        self.assertEqual(MetadataCategorization.objects.count(), 1)

    def test_register_categorization(self):
        test_categorization = MetadataCategorization(
            name="test",
            file=TEST_CATEGORIZATION_FILE,
        )
        test_categorization.save()
        self.test_ontology.categorization = test_categorization
        self.test_ontology.save()

        self.assertFalse(test_categorization.registered)
        self.assertEqual(test_categorization.categories.count(), 0)

        test_categorization.register()

        self.assertTrue(test_categorization.registered)
        self.assertEqual(test_categorization.categories.count(), 3)

        actual_standard_category_proxies_data = [
            model_to_data(standard_category_proxy)
            for standard_category_proxy in test_categorization.categories.all()
        ]

        standard_property_proxies = MetadataStandardPropertyProxy.objects.filter(model_proxy__version=self.test_ontology)

        test_standard_category_proxies_data = [
            {"categorization": test_categorization.pk, 'name': u'Category One',   'key': u'category-one',   'order': 1, 'description': u'I am category one.',
             'properties': [standard_property_proxies.get(name="string").pk, standard_property_proxies.get(name="individualName").pk, standard_property_proxies.get(name="phone").pk, standard_property_proxies.get(name="date").pk, standard_property_proxies.get(name="author").pk],
             },
            {"categorization": test_categorization.pk, 'name': u'Category Two',   'key': u'category-two',   'order': 2, 'description': u'I am category two.',
             'properties': [standard_property_proxies.get(name="boolean").pk, standard_property_proxies.get(name="contactInfo").pk, standard_property_proxies.get(name="address").pk, standard_property_proxies.get(name="enumeration").pk, standard_property_proxies.get(name="contact").pk],
             },
            {"categorization": test_categorization.pk, 'name': u'Category Three', 'key': u'category-three', 'order': 3, 'description': u'I am category three - I am unused.',
             'properties': [],
             }
        ]

        for actual_standard_category_proxy_data, test_standard_category_proxy_data in zip(actual_standard_category_proxies_data, test_standard_category_proxies_data):
            self.assertDictEqual(actual_standard_category_proxy_data, test_standard_category_proxy_data, excluded_keys=["id", ])

