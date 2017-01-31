####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################


from django.core.exceptions import ValidationError
from django.db import IntegrityError
from jsonschema import validate as json_validate
import json

from Q.questionnaire.tests.test_base import TestQBase, create_ontology, remove_ontology, incomplete_test
from Q.questionnaire.q_utils import serialize_model_to_dict, sort_sequence_by_key
from Q.questionnaire.models.models_ontologies import *


TEST_SCHEMA_VALID = "test_ontology_schema.json"
TEST_SPECIALIZATION_VALID = "test_ontology_specialization.json"
TEST_ONTOLOGY_INVALID = "test_invalid_ontology.json"


class TestQOntology(TestQBase):

    def setUp(self):

        # don't do the base setUp (it would interfere w/ the ids of the proxies registered below)
        # super(TestQOntolgoy, self).setUp()

        # create some test ontologies...
        self.test_ontology_schema = create_ontology(
            filename=TEST_SCHEMA_VALID,
            name="test_schema",
            version="2",
            type=QOntologyTypes.SCHEMA.get_type(),
        )

        # TODO: SEE THE COMMENT IN "q_fields.py" ABOUT SETTING VERSION MANUALLY...
        self.test_ontology_schema.refresh_from_db()

    def tearDown(self):

        # don't do the base tearDown
        # super(TestQOntolgoy, self).tearDown()

        # delete the test ontologies
        remove_ontology(ontology=self.test_ontology_schema)

    def test_ontology_key(self):

        test_key = "test_schema_2.0.0"
        self.assertEqual(self.test_ontology_schema.key, test_key)

    def test_ontology_has_key(self):

        test_key = "test_schema_2"
        self.assertIn(self.test_ontology_schema, QOntology.objects.has_key(test_key))

        test_key = "test_schema_2.0"
        self.assertIn(self.test_ontology_schema, QOntology.objects.has_key(test_key))

        test_key = "test_schema_2.0.0"
        self.assertIn(self.test_ontology_schema, QOntology.objects.has_key(test_key))

        test_key = "test_schema_1.2.3"
        self.assertNotIn(self.test_ontology_schema, QOntology.objects.has_key(test_key))

    def test_ontology_get_name_and_version_from_key(self):

        with self.assertRaises(QError):
            get_name_and_version_from_key("invalid_key")

        name, version = get_name_and_version_from_key("test_schema_1")
        self.assertEqual(name, "test_schema")
        self.assertEqual(version, "1.0.0")

        name, version = get_name_and_version_from_key("test_schema_1.2")
        self.assertEqual(name, "test_schema")
        self.assertEqual(version, "1.2.0")

        name, version = get_name_and_version_from_key("test_schema_1.2.3")
        self.assertEqual(name, "test_schema")
        self.assertEqual(version, "1.2.3")

    def test_ontology_validity(self):
        invalid_ontology = create_ontology(
            filename=TEST_ONTOLOGY_INVALID,
            name="test_invalid_schema",
            version="2",
        )
        with self.assertRaises(ValidationError):
            invalid_ontology.full_clean()

    def test_ontology_unique_name(self):
        with self.assertRaises(IntegrityError):
            invalid_ontology = create_ontology(
                filename=TEST_SCHEMA_VALID,
                name=self.test_ontology_schema.name,
                version="2",
                type=QOntologyTypes.SCHEMA.get_type(),
            )
            invalid_ontology.full_clean()

    def test_ontology_register(self):

        self.assertFalse(self.test_ontology_schema.is_registered)
        self.assertIsNone(self.test_ontology_schema.last_registered_version)
        self.test_ontology_schema.register()
        self.assertTrue(self.test_ontology_schema.is_registered)
        self.assertEqual(self.test_ontology_schema.last_registered_version, self.test_ontology_schema.version)

        test_model_proxies = self.test_ontology_schema.model_proxies.all()
        test_category_proxies = QCategoryProxy.objects.filter(model_proxy__ontology=self.test_ontology_schema)
        test_property_proxies = QPropertyProxy.objects.filter(model_proxy__ontology=self.test_ontology_schema)

        actual_model_proxies_data = [
            serialize_model_to_dict(model_proxy, exclude=["id", "guid", "created", "modified"])
            for model_proxy in test_model_proxies
        ]

        test_model_proxies_data = sort_sequence_by_key(
            [
                {'name': u'model', 'package': u'test_package', 'cim_id': '1', 'documentation': u'this is a test model', 'label': None,
                 'is_document': True, 'ontology': self.test_ontology_schema.pk, 'order': 1, 'is_meta': False},
                {'name': u'recursive_thing', 'package': u'test_package', 'cim_id': '2', 'documentation': None, 'label': None,
                 'is_document': False, 'ontology': self.test_ontology_schema.pk, 'order': 2, 'is_meta': False},
                {'name': u'other_thing_one', 'package': u'test_package', 'cim_id': '3', 'documentation': None, 'label': None,
                 'is_document': False, 'ontology': self.test_ontology_schema.pk, 'order': 3, 'is_meta': False},
                {'name': u'other_thing_two', 'package': u'test_package', 'cim_id': '4', 'documentation': None, 'label': None,
                 'is_document': False, 'ontology': self.test_ontology_schema.pk, 'order': 4, 'is_meta': False},
            ],
            "order"
        )

        for actual_model_proxy_data, test_model_proxy_data in zip(actual_model_proxies_data, test_model_proxies_data):
            self.assertDictEqual(actual_model_proxy_data, test_model_proxy_data)

        actual_category_proxies_data = [
            serialize_model_to_dict(category_proxy, exclude=["id", "guid", "created", "modified"])
            for category_proxy in test_category_proxies
        ]

        test_category_proxies_data = sort_sequence_by_key(
            [
                {'name': UNCATEGORIZED_CATEGORY_PROXY_NAME, 'package': UNCATEGORIZED_CATEGORY_PROXY_PACKAGE, 'cim_id': None,
                 'documentation': None, 'order': 1, 'model_proxy': 1, 'is_meta': False},
                {'name': UNCATEGORIZED_CATEGORY_PROXY_NAME, 'package': UNCATEGORIZED_CATEGORY_PROXY_PACKAGE, 'cim_id': None,
                 'documentation': None, 'order': 1, 'model_proxy': 2, 'is_meta': False},
                {'name': UNCATEGORIZED_CATEGORY_PROXY_NAME, 'package': UNCATEGORIZED_CATEGORY_PROXY_PACKAGE, 'cim_id': None,
                 'documentation': None, 'order': 1, 'model_proxy': 3, 'is_meta': False},
                {'name': UNCATEGORIZED_CATEGORY_PROXY_NAME, 'package': UNCATEGORIZED_CATEGORY_PROXY_PACKAGE, 'cim_id': None,
                 'documentation': None, 'order': 1, 'model_proxy': 4, 'is_meta': False},
            ],
            "order"
        )

        for actual_category_proxy_data, test_category_proxy_data in zip(actual_category_proxies_data, test_category_proxies_data):
            self.assertDictEqual(actual_category_proxy_data, test_category_proxy_data, excluded_keys=["model_proxy"])
        self.assertEqual(test_model_proxies.count(), test_category_proxies.filter(package=UNCATEGORIZED_CATEGORY_PROXY_PACKAGE, name=UNCATEGORIZED_CATEGORY_PROXY_NAME).count())

        actual_property_proxies_data = [
            serialize_model_to_dict(property_proxy, exclude=["id", "guid", "created", "modified"])
            for property_proxy in test_property_proxies
        ]

        model_model_proxy = test_model_proxies.get(name__iexact="model")
        recursive_thing_model_proxy = test_model_proxies.get(name__iexact="recursive_thing")
        other_thing_one_model_proxy = test_model_proxies.get(name__iexact="other_thing_one")
        other_thing_two_model_proxy = test_model_proxies.get(name__iexact="other_thing_two")
        model_model_proxy_uncategorized_category_proxy = model_model_proxy.category_proxies.get(
            package=UNCATEGORIZED_CATEGORY_PROXY_PACKAGE, name=UNCATEGORIZED_CATEGORY_PROXY_NAME
        )
        recursive_thing_model_proxy_uncategorized_category_proxy = recursive_thing_model_proxy.category_proxies.get(
            package=UNCATEGORIZED_CATEGORY_PROXY_PACKAGE, name=UNCATEGORIZED_CATEGORY_PROXY_NAME
        )
        other_thing_one_model_proxy_uncategorized_category_proxy = other_thing_one_model_proxy.category_proxies.get(
            package=UNCATEGORIZED_CATEGORY_PROXY_PACKAGE, name=UNCATEGORIZED_CATEGORY_PROXY_NAME
        )
        other_thing_two_model_proxy_uncategorized_category_proxy = other_thing_two_model_proxy.category_proxies.get(
            package=UNCATEGORIZED_CATEGORY_PROXY_PACKAGE, name=UNCATEGORIZED_CATEGORY_PROXY_NAME
        )

        test_property_proxies_data = \
            [

                {'category_proxy': model_model_proxy_uncategorized_category_proxy.pk, 'is_nillable': True, 'relationship_target_models': [], 'name': 'name',
                 'package': 'test_package', 'enumeration_choices': None, 'documentation': None, 'atomic_type': 'DEFAULT', 'cim_id': "1.1",
                 'order': 1, 'enumeration_is_open': False, 'cardinality_max': '1', 'relationship_target_names': None,
                 'cardinality_min': '1', 'field_type': 'ATOMIC', 'model_proxy': model_model_proxy.pk, 'is_meta': False},
                {'category_proxy': model_model_proxy_uncategorized_category_proxy.pk, 'is_nillable': True, 'relationship_target_models': [], 'name': 'enumeration',
                 'package': 'test_package', 'cim_id': "1.2",
                 'enumeration_choices': [{u'documentation': u'documentation for one', u'order': 1, u'value': u'one'},
                                         {u'documentation': u'documentation for two', u'order': 2, u'value': u'two'},
                                         {u'documentation': u'documentation for three', u'order': 3, u'value': u'three'}],
                 'documentation': 'this is a test enumeration', 'atomic_type': None, 'order': 2, 'enumeration_is_open': True,
                 'cardinality_max': '1', 'relationship_target_names': None, 'cardinality_min': '0',
                 'field_type': 'ENUMERATION', 'model_proxy': model_model_proxy.pk, 'is_meta': False},
                {'category_proxy': model_model_proxy_uncategorized_category_proxy.pk, 'is_nillable': True, 'relationship_target_models': [2], 'name': 'thing',
                 'package': 'test_package', 'enumeration_choices': None, 'cim_id': '1.3',
                 'documentation': 'a relationship property; there are lots of spaces in this documentation',
                 'atomic_type': None, 'order': 3, 'enumeration_is_open': False, 'cardinality_max': '1',
                 'relationship_target_names': ['test_package.recursive_thing'], 'cardinality_min': '0',
                 'field_type': 'RELATIONSHIP', 'model_proxy': model_model_proxy.pk, 'is_meta': False},
                {'category_proxy': recursive_thing_model_proxy_uncategorized_category_proxy.pk, 'is_nillable': True, 'relationship_target_models': [], 'name': 'name',
                 'package': 'test_package', 'enumeration_choices': None, 'documentation': None, 'atomic_type': 'DEFAULT', 'cim_id': '2.1',
                 'order': 1, 'enumeration_is_open': False, 'cardinality_max': '1', 'relationship_target_names': None,
                 'cardinality_min': '1', 'field_type': 'ATOMIC', 'model_proxy': recursive_thing_model_proxy.pk, 'is_meta': False},
                {'category_proxy': recursive_thing_model_proxy_uncategorized_category_proxy.pk, 'is_nillable': True, 'relationship_target_models': [recursive_thing_model_proxy.pk], 'name': 'child',
                 'package': 'test_package', 'enumeration_choices': None, 'documentation': None, 'atomic_type': None, 'cim_id': '2.2',
                 'order': 2, 'enumeration_is_open': False, 'cardinality_max': 'N',
                 'relationship_target_names': ['test_package.recursive_thing'], 'cardinality_min': '0',
                 'field_type': 'RELATIONSHIP', 'model_proxy': recursive_thing_model_proxy.pk, 'is_meta': False},
                {'category_proxy': recursive_thing_model_proxy_uncategorized_category_proxy.pk, 'is_nillable': True, 'relationship_target_models': [other_thing_one_model_proxy.pk, other_thing_two_model_proxy.pk], 'name': 'multiple_targets',
                 'package': 'test_package', 'enumeration_choices': None, 'documentation': None, 'atomic_type': None, 'cim_id': '2.3',
                 'order': 3, 'enumeration_is_open': False, 'cardinality_max': '1',
                 'relationship_target_names': ['test_package.other_thing_one', 'test_package.other_thing_two'],
                 'cardinality_min': '0', 'field_type': 'RELATIONSHIP', 'model_proxy': recursive_thing_model_proxy.pk, 'is_meta': False},
                {'category_proxy': other_thing_one_model_proxy_uncategorized_category_proxy.pk, 'is_nillable': True, 'relationship_target_models': [], 'name': 'name',
                 'package': 'test_package', 'enumeration_choices': None, 'documentation': None, 'atomic_type': 'DEFAULT', 'cim_id': '3.1',
                 'order': 1, 'enumeration_is_open': False, 'cardinality_max': '1', 'relationship_target_names': None,
                 'cardinality_min': '1', 'field_type': 'ATOMIC', 'model_proxy': other_thing_one_model_proxy.pk, 'is_meta': False},
                {'category_proxy': other_thing_two_model_proxy_uncategorized_category_proxy.pk, 'is_nillable': True, 'relationship_target_models': [], 'name': 'name',
                 'package': 'test_package', 'enumeration_choices': None, 'documentation': None, 'atomic_type': 'DEFAULT', 'cim_id': '4.1',
                 'order': 1, 'enumeration_is_open': False, 'cardinality_max': '1', 'relationship_target_names': None,
                 'cardinality_min': '1', 'field_type': 'ATOMIC', 'model_proxy': other_thing_two_model_proxy.pk, 'is_meta': False},
            ]

        for actual_property_proxy_data, test_property_proxy_data in zip(actual_property_proxies_data, test_property_proxies_data):
            self.assertDictEqual(actual_property_proxy_data, test_property_proxy_data)

    @incomplete_test
    def test_ontology_reregister(self):
        pass

    def test_get_inherited_classes(self):
        ontology_content = json.load(self.test_ontology_schema.file)
        json_validate(ontology_content, QCONFIG_SCHEMA)
        actual_inherited_classes = get_inherited_classes(ontology_content)
        test_inherited_classes = []
        self.assertSetEqual(set(actual_inherited_classes), set(test_inherited_classes))

    def test_get_excluded_classes(self):
        ontology_content = json.load(self.test_ontology_schema.file)
        json_validate(ontology_content, QCONFIG_SCHEMA)
        actual_excluded_classes = get_excluded_classes(ontology_content)
        test_excluded_classes = []
        self.assertSetEqual(set(actual_excluded_classes), set(test_excluded_classes))

    def test_get_defined_classes(self):
        ontology_content = json.load(self.test_ontology_schema.file)
        json_validate(ontology_content, QCONFIG_SCHEMA)
        actual_defined_classes = get_defined_classes(ontology_content)
        test_defined_classes = [
            {
                u'name': u'model',
                u'package': u'test_package',
                u'id': u'1',
                u'documentation': u'this is a test model',
                u'is_document': True,
                u'is_meta': False,
                u'properties': {
                    u'excluded': [],
                    u'inherited': [],
                    u'defined': [
                        {
                            u'name': u'name',
                            u'package': u'test_package',
                            u'id': u'id.1.1',
                            u'cardinality': u'1.1',
                            u'is_meta': False,
                            u'is_nillable': True,
                            u'property_type': u'ATOMIC',
                            u'atomic_type': u'STRING'
                        },
                        {
                            u'name': u'enumeration',
                            u'package': u'test_package',
                            u'id': u'1.2',
                            u'documentation': u'this is a test enumeration',
                            u'cardinality': u'0.1',
                            u'is_meta': False,
                            u'is_nillable': True,
                            u'property_type': u'ENUMERATION',
                            u'enumeration_is_open': True,
                            u'enumeration_members': [
                                {u'documentation': u'documentation for one', u'order': 1, u'value': u'one'},
                                {u'documentation': u'documentation for two', u'order': 2, u'value': u'two'},
                                {u'documentation': u'documentation for three', u'order': 3, u'value': u'three'}
                            ]
                        },
                        {
                            u'name': u'thing',
                            u'package': u'test_package',
                            u'id': u'1.3',
                            u'documentation': u'a relationship property;            there are lots of spaces in this documentation',
                            u'cardinality': u'0.1',
                            u'is_meta': False,
                            u'is_nillable': True,
                            u'property_type': u'RELATIONSHIP',
                            u'relationship_targets': [
                                u'test_package.recursive_thing'
                            ],
                        }
                    ]
                }
            },
            {
                u'name': u'recursive_thing',
                u'package': u'test_package',
                u'id': u'2',
                u'is_document': False,
                u'is_meta': False,
                u'properties': {
                    u'excluded': [],
                    u'inherited': [],
                    u'defined': [
                        {
                            u'name': u'name',
                            u'package': u'test_package',
                            u'id': u'2.1',
                            u'cardinality': u'1.1',
                            u'is_nillable': True,
                            u'is_meta': False,
                            u'property_type': u'ATOMIC',
                            u'atomic_type': u'STRING',
                        },
                        {
                            u'name': u'child',
                            u'package': u'test_package',
                            u'id': u'2.2',
                            u'cardinality': u'0.N',
                            u'is_nillable': True,
                            u'is_meta': False,
                            u'property_type': u'RELATIONSHIP',
                            u'relationship_targets': [
                                u'test_package.recursive_thing'
                            ]
                        },
                        {
                            u'name': u'multiple_targets',
                            u'package': u'test_package',
                            u'id': u'2.3',
                            u'cardinality': u'0.1',
                            u'is_nillable': True,
                            u'is_meta': False,
                            u'property_type': u'RELATIONSHIP',
                            u'relationship_targets': [
                                u'test_package.other_thing_one',
                                u'test_package.other_thing_two'
                            ]
                        }
                    ]
                }
            },
            {
                u'name': u'other_thing_one',
                u'package': u'test_package',
                u'id': u'3',
                u'is_document': False,
                u'is_meta': False,
                u'properties': {
                    u'inherited': [],
                    u'excluded': [],
                    u'defined': [
                        {
                            u'name': u'name',
                            u'package': u'test_package',
                            u'id': u'3.1',
                            u'cardinality': u'1.1',
                            u'is_nillable': True,
                            u'is_meta': False,
                            u'property_type': u'ATOMIC',
                            u'atomic_type': u'STRING'
                        }
                    ]
                }
            },
            {
                u'name': u'other_thing_two',
                u'package': u'test_package',
                u'id': u'4',
                u'is_document': False,
                u'is_meta': False,
                u'properties': {
                    u'inherited': [],
                    u'excluded': [],
                    u'defined': [
                        {
                            u'name': u'name',
                            u'package': u'test_package',
                            u'id': u'4.1',
                            u'cardinality': u'1.1',
                            u'is_meta': False,
                            u'is_nillable': True,
                            u'property_type': u'ATOMIC',
                            u'atomic_type': u'STRING'
                        }
                    ]
                }
            }
        ]

        for actual_defined_class, test_defined_class in zip(actual_defined_classes, test_defined_classes):
            self.assertDictEqual(actual_defined_class, test_defined_class)

    def test_get_inherited_properties(self):
        ontology_content = json.load(self.test_ontology_schema.file)
        json_validate(ontology_content, QCONFIG_SCHEMA)
        actual_inherited_properties = get_inherited_properties(ontology_content, "test_package.model")
        test_inherited_properties = []
        self.assertSetEqual(set(actual_inherited_properties), set(test_inherited_properties))

    def test_get_excluded_properties(self):
        ontology_content = json.load(self.test_ontology_schema.file)
        json_validate(ontology_content, QCONFIG_SCHEMA)
        actual_excluded_properties = get_excluded_properties(ontology_content, "test_package.model")
        test_excluded_properties = []
        self.assertSetEqual(set(actual_excluded_properties), set(test_excluded_properties))


    @incomplete_test
    def test_get_defined_properties(self):
        pass
