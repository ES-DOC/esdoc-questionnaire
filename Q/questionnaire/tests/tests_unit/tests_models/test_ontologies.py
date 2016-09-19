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

from django.core.exceptions import ValidationError

from Q.questionnaire.tests.test_base import TestQBase, create_ontology, remove_ontology, incomplete_test
from Q.questionnaire.q_utils import serialize_model_to_dict, sort_list_by_key
from Q.questionnaire.models.models_ontologies import *

class TestQOntology(TestQBase):

    def setUp(self):

        # don't do the base setUp (it would interfere w/ the ids of the ontology created below)
        # super(TestQOntolgoy, self).setUp()

        # create some test ontologies...
        self.test_ontology_schema = create_ontology(
            filename="ontology_schema.xml",
            name="test_ontology_schema",
            version="2.0",
            type=QOntologyTypes.SCHEMA.get_type(),
        )

        # TODO: SEE THE COMMENT IN "q_fields.py" ABOUT SETTING VERSION MANUALLY...
        self.test_ontology_schema.refresh_from_db()

    def tearDown(self):

        # don't do the base tearDown
        # super(TestQOntolgoy, self).tearDown()

        # delete the test ontologies
        remove_ontology(ontology=self.test_ontology_schema)

    def test_ontology_get_key(self):

        test_key = "test_ontology_schema_2.0.0"
        self.assertEqual(self.test_ontology_schema.get_key(), test_key)

    def test_ontology_filter_by_key(self):

        self.test_ontology_schema.version = "123"
        self.test_ontology_schema.save()

        test_key = "test_ontology_schema_123"

        test_ontology = QOntology.objects.filter_by_key(test_key)[0]
        self.assertEqual(test_ontology, self.test_ontology_schema)

    def test_ontology_get_name_and_version_from_key(self):

        with self.assertRaises(QError):
            get_name_and_version_from_key("invalid_key")

        name, version = get_name_and_version_from_key("test_ontology_schema_1")
        self.assertEqual(name, "test_ontology_schema")
        self.assertEqual(version, "1.0.0")

        name, version = get_name_and_version_from_key("test_ontology_schema_1.2")
        self.assertEqual(name, "test_ontology_schema")
        self.assertEqual(version, "1.2.0")

        name, version = get_name_and_version_from_key("test_ontology_schema_1.2.3")
        self.assertEqual(name, "test_ontology_schema")
        self.assertEqual(version, "1.2.3")

    def test_ontology_validity(self):
        invalid_ontology = create_ontology(
            filename="ontology_invalid.xml",
            name="test_invalid_ontology",
            version="2.0",
        )
        with self.assertRaises(ValidationError):
            # this is an invalid CIM1 file (it is a CIM2 file)
            invalid_ontology.full_clean()

    def test_ontology_unique_name(self):
        with self.assertRaises(Exception):
            invalid_ontology = self.test_ontology_schema = create_ontology(
                filename="ontology_schema.xml",
                name="test_ontology_schema",
                version="2.0",
                type=QOntologyTypes.SCHEMA.get_type(),
            )
            invalid_ontology.full_clean()

    def test_ontology_register(self):

        self.assertFalse(self.test_ontology_schema.is_registered)
        self.test_ontology_schema.register()
        self.assertTrue(self.test_ontology_schema.is_registered)

        test_model_proxies = self.test_ontology_schema.model_proxies.all()
        test_property_proxies = QPropertyProxy.objects.filter(model_proxy__ontology=self.test_ontology_schema)

        actual_model_proxies_data = [
            serialize_model_to_dict(model_proxy, exclude=["id", "guid", "created", "modified"])
            for model_proxy in test_model_proxies
        ]

        test_model_proxies_data = sort_list_by_key(
            [
                {'name': u'model', 'stereotype': u'document', 'package': u'science', 'documentation': u'', 'is_specialized': False, 'ontology': self.test_ontology_schema.pk, 'order': 1},
                {'name': u'recursive_thing', 'stereotype': None, 'package': u'shared', 'documentation': u'', 'is_specialized': False, 'ontology': self.test_ontology_schema.pk, 'order': 2},
                {'name': u'other_thing_one', 'stereotype': None, 'package': u'shared', 'documentation': u'', 'is_specialized': False, 'ontology': self.test_ontology_schema.pk, 'order': 3},
                {'name': u'other_thing_two', 'stereotype': None, 'package': u'shared', 'documentation': u'', 'is_specialized': False, 'ontology': self.test_ontology_schema.pk, 'order': 4},
            ],
            "order",
        )

        for actual_model_proxy_data, test_model_proxy_data in zip(actual_model_proxies_data, test_model_proxies_data):
            self.assertDictEqual(actual_model_proxy_data, test_model_proxy_data)

        actual_property_proxies_data = [
            serialize_model_to_dict(property_proxy, exclude=["id", "guid", "created", "modified"])
            for property_proxy in test_property_proxies
        ]

        test_property_proxies_data = sort_list_by_key(
            [
                {'category': None, 'field_type': u'ATOMIC', 'is_nillable': True, 'name': u'name', 'stereotype': None, 'relationship_target_models': [], 'documentation': u'', 'atomic_type': u'DEFAULT', 'order': 1, 'enumeration_open': False, 'enumeration': None, 'enumeration_multi': False, 'is_specialized': False, 'relationship_target_names': u'', 'cardinality': u'1|1', 'atomic_default': None, 'model_proxy': test_model_proxies[0].pk},
                {'category': None, 'field_type': u'ENUMERATION', 'is_nillable': True, 'name': u'enumeration', 'stereotype': None, 'relationship_target_models': [], 'documentation': u'A test enumeration.', 'atomic_type': u'DEFAULT', 'order': 2, 'enumeration_open': False, 'enumeration': [{u'documentation': u'documentation for one.', u'order': 1, u'value': u'one'}, {u'documentation': u'documentation for two.', u'order': 2, u'value': u'two'}, {u'documentation': u'documentation for three.', u'order': 3, u'value': u'three'}], 'enumeration_multi': False, 'is_specialized': False, 'relationship_target_names': u'', 'cardinality': u'0|1', 'atomic_default': None, 'model_proxy': test_model_proxies[0].pk},
                {'category': None, 'field_type': u'RELATIONSHIP', 'is_nillable': True, 'name': u'thing', 'stereotype': None, 'relationship_target_models': [test_model_proxies[1].pk], 'documentation': u'', 'atomic_type': u'DEFAULT', 'order': 3, 'enumeration_open': False, 'enumeration': None, 'enumeration_multi': False, 'is_specialized': False, 'relationship_target_names': u'shared.recursive_thing', 'cardinality': u'0|1', 'atomic_default': None, 'model_proxy': test_model_proxies[0].pk},
                {'category': None, 'field_type': u'ATOMIC', 'is_nillable': True, 'name': u'name', 'stereotype': None, 'relationship_target_models': [], 'documentation': u'', 'atomic_type': u'DEFAULT', 'order': 1, 'enumeration_open': False, 'enumeration': None, 'enumeration_multi': False, 'is_specialized': False, 'relationship_target_names': u'', 'cardinality': u'1|1', 'atomic_default': None, 'model_proxy': test_model_proxies[1].pk},
                {'category': None, 'field_type': u'RELATIONSHIP', 'is_nillable': True, 'name': u'child', 'stereotype': None, 'relationship_target_models': [test_model_proxies[1].pk], 'documentation': u'', 'atomic_type': u'DEFAULT', 'order': 2, 'enumeration_open': False, 'enumeration': None, 'enumeration_multi': False, 'is_specialized': False, 'relationship_target_names': u'shared.recursive_thing', 'cardinality': u'0|*', 'atomic_default': None, 'model_proxy': test_model_proxies[1].pk},
                {'category': None, 'field_type': u'RELATIONSHIP', 'is_nillable': True, 'name': u'multiple_targets', 'stereotype': None, 'relationship_target_models': [test_model_proxies[2].pk, test_model_proxies[3].pk], 'documentation': u'', 'atomic_type': u'DEFAULT', 'order': 3, 'enumeration_open': False, 'enumeration': None, 'enumeration_multi': False, 'is_specialized': False, 'relationship_target_names': u'shared.other_thing_one|shared.other_thing_two', 'cardinality': u'0|1', 'atomic_default': None, 'model_proxy': test_model_proxies[1].pk},
                {'category': None, 'field_type': u'ATOMIC', 'is_nillable': True, 'name': u'name', 'stereotype': None, 'relationship_target_models': [], 'documentation': u'', 'atomic_type': u'DEFAULT', 'order': 1, 'enumeration_open': False, 'enumeration': None, 'enumeration_multi': False, 'is_specialized': False, 'relationship_target_names': u'', 'cardinality': u'1|1', 'atomic_default': None, 'model_proxy': test_model_proxies[2].pk},
                {'category': None, 'field_type': u'ATOMIC', 'is_nillable': True, 'name': u'name', 'stereotype': None, 'relationship_target_models': [], 'documentation': u'', 'atomic_type': u'DEFAULT', 'order': 1, 'enumeration_open': False, 'enumeration': None, 'enumeration_multi': False, 'is_specialized': False, 'relationship_target_names': u'', 'cardinality': u'1|1', 'atomic_default': None, 'model_proxy': test_model_proxies[3].pk},
            ],
            "order",
        )

        for actual_property_proxy_data, test_property_proxy_data in zip(actual_property_proxies_data, test_property_proxies_data):
            self.assertDictEqual(actual_property_proxy_data, test_property_proxy_data)

    @incomplete_test
    def test_ontology_reregister(self):
        pass