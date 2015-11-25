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


from Q.questionnaire.tests.test_base import TestQBase, create_categorization, remove_categorization, create_ontology, remove_ontology
from Q.questionnaire.q_utils import serialize_model_to_dict


class TestQCategorization(TestQBase):

    def setUp(self):

        super(TestQCategorization, self).setUp()

        # create a test categorization
        # (this requires a test ontology)
        self.test_categorization = create_categorization()
        self.test_ontology = create_ontology()
        self.test_ontology.categorization = self.test_categorization
        self.test_ontology.save()

    def tearDown(self):

        super(TestQCategorization, self).tearDown()

        # delete the test categorization & test ontology
        remove_categorization(categorization=self.test_categorization)
        remove_ontology(ontology=self.test_ontology)

    def test_categorization_register(self):

        # (registering the ontology is tested elsewhere)
        self.test_ontology.register()

        self.assertFalse(self.test_categorization.is_registered)
        self.assertEqual(self.test_categorization.category_proxies.count(), 0)
        self.test_categorization.register()
        self.assertTrue(self.test_categorization.is_registered)
        self.assertEqual(self.test_categorization.category_proxies.count(), 3)

        test_category_proxies = self.test_categorization.category_proxies.all()

        actual_standard_category_proxies_data = [
            serialize_model_to_dict(standard_category_proxy, exclude=["id", "guid", "created", "modified"])
            for standard_category_proxy in test_category_proxies
        ]

        test_category_proxies_properties = [
            test_category_proxy.properties.values_list("pk", flat=True)
            for test_category_proxy in test_category_proxies
        ]

        test_standard_category_proxies_data = [
            {'properties': test_category_proxies_properties[0], 'categorization': self.test_categorization.pk, 'name': u'Category One', 'documentation': u'I am category one.', 'key': u'category-one', 'order': 1},
            {'properties': test_category_proxies_properties[1], 'categorization': self.test_categorization.pk, 'name': u'Category Two', 'documentation': u'I am category two.', 'key': u'category-two', 'order': 2},
            {'properties': test_category_proxies_properties[2], 'categorization': self.test_categorization.pk, 'name': u'Category Three', 'documentation': u'I am category three - I am unused.', 'key': u'category-three', 'order': 3},
        ]

        for actual_standard_category_proxy_data, test_standard_category_proxy_data in zip(actual_standard_category_proxies_data, test_standard_category_proxies_data):
            self.assertDictEqual(actual_standard_category_proxy_data, test_standard_category_proxy_data, excluded_keys=["properties"])
            self.assertItemsEqual(actual_standard_category_proxy_data["properties"], test_standard_category_proxy_data["properties"])  # using "assertItemsEqual" instead of "assertListEqual" b/c I don't care about order
