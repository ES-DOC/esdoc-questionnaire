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


from Q.questionnaire.tests.test_base import TestQBase, create_categorization, remove_categorization, create_ontology, remove_ontology
from Q.questionnaire.models.models_ontologies import CIMTypes
from Q.questionnaire.q_utils import serialize_model_to_dict


class TestQCategorization(TestQBase):

    def setUp(self):

        super(TestQCategorization, self).setUp()

        # create some test categorizations
        # (these require test ontologies)

        self.test_categorization_1 = create_categorization(
            filename="test_categorization_1.xml",
            name="test_categorization_1",
            version="1.0",
            type=CIMTypes.CIM1.get_type(),
        )
        self.test_ontology_1 = create_ontology(
            filename="test_ontology_1.xml",
            name="test_ontology_1",
            version="1.0",
            type=CIMTypes.CIM1.get_type(),
        )
        self.test_ontology_1.categorization = self.test_categorization_1
        self.test_ontology_1.save()

        self.test_categorization_2 = create_categorization(
            filename="test_categorization_2.xml",
            name="test_categorization_2",
            version="2.0",
            type=CIMTypes.CIM2.get_type(),
        )
        self.test_ontology_2 = create_ontology(
            filename="test_ontology_2.xml",
            name="test_ontology_2",
            version="2.0",
            type=CIMTypes.CIM2.get_type(),
        )
        self.test_ontology_2.categorization = self.test_categorization_2
        self.test_ontology_2.save()

        # TODO: SEE THE COMMENT IN "q_fields.py" ABOUT SETTING VERSION MANUALLY...
        self.test_categorization_1.refresh_from_db()
        self.test_ontology_1.refresh_from_db()
        self.test_categorization_2.refresh_from_db()
        self.test_ontology_2.refresh_from_db()

    def tearDown(self):

        super(TestQCategorization, self).tearDown()

        # delete the test categorizations & test ontologies
        remove_categorization(categorization=self.test_categorization_1)
        remove_ontology(ontology=self.test_ontology_1)
        remove_categorization(categorization=self.test_categorization_2)
        remove_ontology(ontology=self.test_ontology_2)

    def test_categorization_register_cim1(self):

        # (registering the ontology is tested elsewhere)
        self.test_ontology_1.register()

        self.assertFalse(self.test_categorization_1.is_registered)
        self.assertEqual(self.test_categorization_1.category_proxies.count(), 0)
        self.test_categorization_1.register()
        self.assertTrue(self.test_categorization_1.is_registered)
        self.assertEqual(self.test_categorization_1.category_proxies.count(), 3)

        test_category_proxies = self.test_categorization_1.category_proxies.all()

        actual_standard_category_proxies_data = [
            serialize_model_to_dict(standard_category_proxy, exclude=["id", "guid", "created", "modified"])
            for standard_category_proxy in test_category_proxies
        ]

        test_category_proxies_properties = [
            test_category_proxy.properties.values_list("pk", flat=True)
            for test_category_proxy in test_category_proxies
        ]

        test_standard_category_proxies_data = [
            {'properties': test_category_proxies_properties[0], 'categorization': self.test_categorization_1.pk, 'name': u'Category One', 'documentation': u'I am category one.', 'key': u'category-one', 'order': 1},
            {'properties': test_category_proxies_properties[1], 'categorization': self.test_categorization_1.pk, 'name': u'Category Two', 'documentation': u'I am category two.', 'key': u'category-two', 'order': 2},
            {'properties': test_category_proxies_properties[2], 'categorization': self.test_categorization_1.pk, 'name': u'Category Three', 'documentation': u'I am category three - I am unused.', 'key': u'category-three', 'order': 3},
        ]

        for actual_standard_category_proxy_data, test_standard_category_proxy_data in zip(actual_standard_category_proxies_data, test_standard_category_proxies_data):
            self.assertDictEqual(actual_standard_category_proxy_data, test_standard_category_proxy_data, excluded_keys=["properties"])
            self.assertItemsEqual(actual_standard_category_proxy_data["properties"], test_standard_category_proxy_data["properties"])  # using "assertItemsEqual" instead of "assertListEqual" b/c I don't care about order

    def test_categorization_register_cim2(self):

        # (registering the ontology is tested elsewhere)
        self.test_ontology_2.register()

        self.assertFalse(self.test_categorization_2.is_registered)
        self.assertEqual(self.test_categorization_2.category_proxies.count(), 0)
        self.test_categorization_2.register()
        self.assertTrue(self.test_categorization_2.is_registered)
        self.assertEqual(self.test_categorization_2.category_proxies.count(), 3)

        test_category_proxies = self.test_categorization_2.category_proxies.all()

        actual_standard_category_proxies_data = [
            serialize_model_to_dict(standard_category_proxy, exclude=["id", "guid", "created", "modified"])
            for standard_category_proxy in test_category_proxies
        ]

        test_category_proxies_properties = [
            test_category_proxy.properties.values_list("pk", flat=True)
            for test_category_proxy in test_category_proxies
        ]

        test_standard_category_proxies_data = [
            {'properties': test_category_proxies_properties[0], 'categorization': self.test_categorization_2.pk, 'name': u'Category One', 'documentation': u'I am category one.', 'key': u'category-one', 'order': 1},
            {'properties': test_category_proxies_properties[1], 'categorization': self.test_categorization_2.pk, 'name': u'Category Two', 'documentation': u'I am category two.', 'key': u'category-two', 'order': 2},
            {'properties': test_category_proxies_properties[2], 'categorization': self.test_categorization_2.pk, 'name': u'Category Three', 'documentation': u'I am category three - I am unused.', 'key': u'category-three', 'order': 3},
        ]

        for actual_standard_category_proxy_data, test_standard_category_proxy_data in zip(actual_standard_category_proxies_data, test_standard_category_proxies_data):
            self.assertDictEqual(actual_standard_category_proxy_data, test_standard_category_proxy_data, excluded_keys=["properties"])
            self.assertItemsEqual(actual_standard_category_proxy_data["properties"], test_standard_category_proxy_data["properties"])  # using "assertItemsEqual" instead of "assertListEqual" b/c I don't care about order
