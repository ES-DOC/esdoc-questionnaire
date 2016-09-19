####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

from Q.questionnaire.tests.test_base import TestQBase, create_ontology, remove_ontology, create_categorization, remove_categorization, incomplete_test
from Q.questionnaire.q_utils import serialize_model_to_dict, sort_list_by_key
from Q.questionnaire.models.models_categorizations import *

class TestQCategorization(TestQBase):

    def setUp(self):

        # don't do the base setUp (it would interfere w/ the ids of the ontology created below)
        # super(TestQOntolgoy, self).setUp()

        # create some test categorizations...
        self.test_categorization = create_categorization(
            filename="categorization.xml",
            name="test_categorization",
            version="1.0",
        )
        # create some test ontologies...
        self.test_ontology_schema = create_ontology(
            filename="ontology_schema.xml",
            name="test_ontology_schema",
            version="2.0",
        )

        self.test_ontology_schema.categorization = self.test_categorization
        self.test_ontology_schema.save()

        # TODO: SEE THE COMMENT IN "q_fields.py" ABOUT SETTING VERSION MANUALLY...
        self.test_categorization.refresh_from_db()
        self.test_ontology_schema.refresh_from_db()

    def tearDown(self):

        # don't do the base tearDown
        # super(TestQOntolgoy, self).tearDown()

        remove_categorization(categorization=self.test_categorization)
        remove_ontology(ontology=self.test_ontology_schema)

    def test_categorization_register(self):

        # (registering the ontology is tested elsewhere)
        self.test_ontology_schema.register()

        self.assertFalse(self.test_categorization.is_registered)
        self.assertEqual(self.test_categorization.category_proxies.count(), 0)
        self.test_categorization.register()
        self.assertTrue(self.test_categorization.is_registered)
        self.assertEqual(self.test_categorization.category_proxies.count(), 4)  # 3 defined in categorization, plus "uncategorized" category

        category_proxies = self.test_categorization.category_proxies.all()

        actual_category_proxies_data = [
            dict(
                serialize_model_to_dict(
                    category_proxy,
                    exclude=["id", "guid", "created", "modified"]
                ),
                property_proxies=category_proxy.property_proxies.values_list("pk", flat=True)
            )
            for category_proxy in category_proxies
        ]

        test_category_proxies_properties_data = [
            [QPropertyProxy.objects.get(name__iexact="name", model_proxy__name__iexact="model").pk, QPropertyProxy.objects.get(name__iexact="name", model_proxy__name__iexact="recursive_thing").pk],
            [QPropertyProxy.objects.get(name__iexact="enumeration", model_proxy__name__iexact="model").pk, QPropertyProxy.objects.get(name__iexact="child", model_proxy__name__iexact="recursive_thing").pk],
            [QPropertyProxy.objects.get(name__iexact="thing", model_proxy__name__iexact="model").pk, QPropertyProxy.objects.get(name__iexact="multiple_targets", model_proxy__name__iexact="recursive_thing").pk],
            [QPropertyProxy.objects.get(name__iexact="name", model_proxy__name__iexact="other_thing_one").pk, QPropertyProxy.objects.get(name__iexact="name", model_proxy__name__iexact="other_thing_two").pk],
        ]

        test_category_proxies_data = sort_list_by_key(
            [
                {'is_specialized': False, 'property_proxies': test_category_proxies_properties_data[0], 'categorization': self.test_categorization.pk, 'name': u'Category One', 'documentation': u'I am category one.', 'order': 1},
                {'is_specialized': False, 'property_proxies': test_category_proxies_properties_data[1], 'categorization': self.test_categorization.pk, 'name': u'Category Two', 'documentation': u'I am category two.', 'order': 2},
                {'is_specialized': False, 'property_proxies': test_category_proxies_properties_data[2], 'categorization': self.test_categorization.pk, 'name': u'Category Three', 'documentation': u'I am category three.', 'order': 3},
                {'is_specialized': False, 'property_proxies': test_category_proxies_properties_data[3], 'categorization': self.test_categorization.pk, 'name': UNCATEGORIZED_NAME, 'documentation': UNCATEGORIZED_DOCUMENTATION, 'order': 4},
            ],
            "order"
        )

        for actual_category_proxy_data, test_category_proxy_data in zip(actual_category_proxies_data, test_category_proxies_data):
            self.assertDictEqual(actual_category_proxy_data, test_category_proxy_data, excluded_keys=["property_proxies"])
            self.assertItemsEqual(actual_category_proxy_data["property_proxies"], test_category_proxy_data["property_proxies"])  # using "assertItemsEqual" instead of "assertListEqual" b/c I don't care about order
