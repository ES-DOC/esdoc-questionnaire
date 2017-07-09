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
TEST_ONTOLOGY_HIERARCHICAL_SCHEMA = "test_ontology_hierarchical_schema.json"
TEST_ONTOLOGY_HIERARCHICAL_SPECIALIZATION = "test_ontology_hierarchical_specialization.json"


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
        self.test_ontology_specialization = create_ontology(
            filename=TEST_SPECIALIZATION_VALID,
            name="test_specialization",
            version="1",
            type=QOntologyTypes.SPECIALIZATION.get_type(),
            parent=self.test_ontology_schema,
        )

        # TODO: SEE THE COMMENT IN "q_fields.py" ABOUT SETTING VERSION MANUALLY...
        self.test_ontology_schema.refresh_from_db()
        self.test_ontology_specialization.refresh_from_db()

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

    def test_ontology_register_schema(self):

        ontology_key = self.test_ontology_schema.key

        self.assertFalse(self.test_ontology_schema.is_registered)
        self.assertIsNone(self.test_ontology_schema.last_registered_version)
        self.test_ontology_schema.register()
        self.assertTrue(self.test_ontology_schema.is_registered)
        self.assertEqual(self.test_ontology_schema.last_registered_version, self.test_ontology_schema.version)

        test_model_proxies = self.test_ontology_schema.model_proxies.all()
        test_category_proxies = QCategoryProxy.objects.filter(ontology=self.test_ontology_schema)
        test_property_proxies = QPropertyProxy.objects.filter(ontology=self.test_ontology_schema)

        actual_model_proxies_data = [
            serialize_model_to_dict(model_proxy, exclude=["id", "guid", "created", "modified", "property_proxies", "category_proxies"])
            for model_proxy in test_model_proxies
        ]

        test_model_proxies_data = sort_sequence_by_key(
            [
                {'name': u'model', 'package': u'test_package', 'cim_id': '{0}.test_package.model'.format(ontology_key), 'documentation': u'this is a test model',
                 'label': {u'fields': [u'name'], u'text': u'model name: {}'},
                 'is_document': True, 'ontology': self.test_ontology_schema.pk, 'order': 1, 'is_meta': False},
                {'name': u'recursive_thing', 'package': u'test_package', 'cim_id': '{0}.test_package.recursive_thing'.format(ontology_key), 'documentation': None, 'label': None,
                 'is_document': False, 'ontology': self.test_ontology_schema.pk, 'order': 2, 'is_meta': False},
                {'name': u'other_thing_one', 'package': u'test_package', 'cim_id': '{0}.test_package.other_thing_one'.format(ontology_key), 'documentation': None, 'label': None,
                 'is_document': False, 'ontology': self.test_ontology_schema.pk, 'order': 3, 'is_meta': False},
                {'name': u'other_thing_two', 'package': u'test_package', 'cim_id': '{0}.test_package.other_thing_two'.format(ontology_key), 'documentation': None, 'label': None,
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
                {'name': UNCATEGORIZED_CATEGORY_PROXY_NAME, 'is_uncategorized': True, 'cim_id': "{0}.{1}.{2}".format(test_model_proxies[0].cim_id, UNCATEGORIZED_CATEGORY_PROXY_PACKAGE, UNCATEGORIZED_CATEGORY_PROXY_NAME),
                 'documentation': None, 'order': 1, 'is_meta': None, 'ontology': self.test_ontology_schema.pk},
                {'name': UNCATEGORIZED_CATEGORY_PROXY_NAME, 'is_uncategorized': True, 'cim_id': "{0}.{1}.{2}".format(test_model_proxies[1].cim_id, UNCATEGORIZED_CATEGORY_PROXY_PACKAGE, UNCATEGORIZED_CATEGORY_PROXY_NAME),
                 'documentation': None, 'order': 1, 'is_meta': None, 'ontology': self.test_ontology_schema.pk},
                {'name': UNCATEGORIZED_CATEGORY_PROXY_NAME, 'is_uncategorized': True, 'cim_id': "{0}.{1}.{2}".format(test_model_proxies[2].cim_id, UNCATEGORIZED_CATEGORY_PROXY_PACKAGE, UNCATEGORIZED_CATEGORY_PROXY_NAME),
                 'documentation': None, 'order': 1, 'is_meta': None, 'ontology': self.test_ontology_schema.pk},
                {'name': UNCATEGORIZED_CATEGORY_PROXY_NAME, 'is_uncategorized': True, 'cim_id': "{0}.{1}.{2}".format(test_model_proxies[3].cim_id, UNCATEGORIZED_CATEGORY_PROXY_PACKAGE, UNCATEGORIZED_CATEGORY_PROXY_NAME),
                 'documentation': None, 'order': 1, 'is_meta': None, 'ontology': self.test_ontology_schema.pk},
            ],
            "order"
        )

        for actual_category_proxy_data, test_category_proxy_data in zip(actual_category_proxies_data, test_category_proxies_data):
            self.assertDictEqual(actual_category_proxy_data, test_category_proxy_data, excluded_keys=["model_proxy"])
        self.assertEqual(test_model_proxies.count(), test_category_proxies.filter(name=UNCATEGORIZED_CATEGORY_PROXY_NAME).count())

        actual_property_proxies_data = [
            serialize_model_to_dict(property_proxy, exclude=["id", "guid", "created", "modified"])
            for property_proxy in test_property_proxies
        ]

        model_model_proxy = test_model_proxies.get(name__iexact="model")
        recursive_thing_model_proxy = test_model_proxies.get(name__iexact="recursive_thing")
        other_thing_one_model_proxy = test_model_proxies.get(name__iexact="other_thing_one")
        other_thing_two_model_proxy = test_model_proxies.get(name__iexact="other_thing_two")
        model_model_proxy_uncategorized_category_proxy = model_model_proxy.category_proxies.get(is_uncategorized=True)
        recursive_thing_model_proxy_uncategorized_category_proxy = recursive_thing_model_proxy.category_proxies.get(is_uncategorized=True)
        other_thing_one_model_proxy_uncategorized_category_proxy = other_thing_one_model_proxy.category_proxies.get(is_uncategorized=True)
        other_thing_two_model_proxy_uncategorized_category_proxy = other_thing_two_model_proxy.category_proxies.get(is_uncategorized=True)

        test_property_proxies_data = sort_sequence_by_key(
            [

                {'category_proxy': model_model_proxy_uncategorized_category_proxy.pk, 'is_nillable': True, 'relationship_target_models': [], 'name': 'name',
                 'category_id': None, 'enumeration_choices': None, 'documentation': None, 'atomic_type': 'DEFAULT', 'cim_id': "test_schema_2.0.0.test_package.model.name", 'ontology': self.test_ontology_schema.pk,
                 'order': 1, 'enumeration_is_open': False, 'cardinality_max': '1', 'relationship_target_names': None, 'is_hierarchical': False,
                 'cardinality_min': '1', 'field_type': 'ATOMIC', 'is_meta': False},
                {'category_proxy': model_model_proxy_uncategorized_category_proxy.pk, 'is_nillable': True, 'relationship_target_models': [], 'name': 'enumeration',
                 'category_id': None, 'cim_id': 'test_schema_2.0.0.test_package.model.enumeration', 'is_hierarchical': False, 'ontology': self.test_ontology_schema.pk,
                 'enumeration_choices': [{u'documentation': u'documentation for one', u'order': 1, u'value': u'one'},
                                         {u'documentation': u'documentation for two', u'order': 2, u'value': u'two'},
                                         {u'documentation': u'documentation for three', u'order': 3, u'value': u'three'}],
                 'documentation': 'this is a test enumeration', 'atomic_type': None, 'order': 2, 'enumeration_is_open': True,
                 'cardinality_max': '1', 'relationship_target_names': None, 'cardinality_min': '0',
                 'field_type': 'ENUMERATION', 'is_meta': False},
                {'category_proxy': model_model_proxy_uncategorized_category_proxy.pk, 'is_nillable': True, 'relationship_target_models': [2], 'name': 'thing',
                 'category_id': None, 'enumeration_choices': None, 'cim_id': 'test_schema_2.0.0.test_package.model.relationship', 'is_hierarchical': False, 'ontology': self.test_ontology_schema.pk,
                 'documentation': 'a relationship property; there are lots of spaces in this documentation',
                 'atomic_type': None, 'order': 3, 'enumeration_is_open': False, 'cardinality_max': '1',
                 'relationship_target_names': ['test_schema_2.0.0.test_package.recursive_thing'], 'cardinality_min': '0',
                 'field_type': 'RELATIONSHIP', 'is_meta': False},
                {'category_proxy': recursive_thing_model_proxy_uncategorized_category_proxy.pk, 'is_nillable': True, 'relationship_target_models': [], 'name': 'name',
                 'category_id': None, 'enumeration_choices': None, 'documentation': None, 'atomic_type': 'DEFAULT', 'cim_id': 'test_schema_2.0.0.test_package.recursive_thing.name', 'ontology': self.test_ontology_schema.pk,
                 'order': 1, 'enumeration_is_open': False, 'cardinality_max': '1', 'relationship_target_names': None, 'is_hierarchical': False,
                 'cardinality_min': '1', 'field_type': 'ATOMIC', 'is_meta': False},
                {'category_proxy': recursive_thing_model_proxy_uncategorized_category_proxy.pk, 'is_nillable': True, 'relationship_target_models': [recursive_thing_model_proxy.pk], 'name': 'child',
                 'category_id': None, 'enumeration_choices': None, 'documentation': None, 'atomic_type': None, 'cim_id': 'test_schema_2.0.0.test_package.recursive_thing.child',
                 'order': 2, 'enumeration_is_open': False, 'cardinality_max': 'N', 'ontology': self.test_ontology_schema.pk,
                 'relationship_target_names': ['test_schema_2.0.0.test_package.recursive_thing'], 'is_hierarchical': False, 'cardinality_min': '0',
                 'field_type': 'RELATIONSHIP', 'is_meta': False},
                {'category_proxy': recursive_thing_model_proxy_uncategorized_category_proxy.pk, 'is_nillable': True, 'relationship_target_models': [other_thing_one_model_proxy.pk, other_thing_two_model_proxy.pk], 'name': 'multiple_targets',
                 'category_id': None, 'enumeration_choices': None, 'documentation': None, 'atomic_type': None, 'cim_id': 'test_schema_2.0.0.test_package.recursive_thing.multiple_targets',
                 'order': 3, 'enumeration_is_open': False, 'cardinality_max': '1', 'is_hierarchical': False, 'ontology': self.test_ontology_schema.pk,
                 'relationship_target_names': ['test_schema_2.0.0.test_package.other_thing_one', 'test_schema_2.0.0.test_package.other_thing_two'],
                 'cardinality_min': '0', 'field_type': 'RELATIONSHIP', 'is_meta': False},
                {'category_proxy': other_thing_one_model_proxy_uncategorized_category_proxy.pk, 'is_nillable': True, 'relationship_target_models': [], 'name': 'name',
                 'category_id': None, 'enumeration_choices': None, 'documentation': None, 'atomic_type': 'DEFAULT', 'cim_id': 'test_schema_2.0.0.test_package.other_thing_one.name', 'ontology': self.test_ontology_schema.pk,
                 'order': 1, 'enumeration_is_open': False, 'cardinality_max': '1', 'relationship_target_names': None, 'is_hierarchical': False,
                 'cardinality_min': '1', 'field_type': 'ATOMIC', 'is_meta': False},
                {'category_proxy': other_thing_two_model_proxy_uncategorized_category_proxy.pk, 'is_nillable': True, 'relationship_target_models': [], 'name': 'name',
                 'category_id': None, 'enumeration_choices': None, 'documentation': None, 'atomic_type': 'DEFAULT', 'cim_id': 'test_schema_2.0.0.test_package.other_thing_two.name', 'ontology': self.test_ontology_schema.pk,
                 'order': 1, 'enumeration_is_open': False, 'cardinality_max': '1', 'relationship_target_names': None, 'is_hierarchical': False,
                 'cardinality_min': '1', 'field_type': 'ATOMIC', 'is_meta': False},
            ],
            "order"
        )

        for actual_property_proxy_data, test_property_proxy_data in zip(actual_property_proxies_data, test_property_proxies_data):
            # no need to test "values" field b/c a schema (as opposed to a specialization) shouldn't have any
            self.assertDictEqual(actual_property_proxy_data, test_property_proxy_data, excluded_keys=["values"])

    def test_ontology_register_specialization(self):

        # all schema stuff has already been tested in "test_ontology_register_schema" above
        self.test_ontology_schema.register()

        schema_key = self.test_ontology_schema.key
        specialization_key = self.test_ontology_specialization.key

        self.assertFalse(self.test_ontology_specialization.is_registered)
        self.assertIsNone(self.test_ontology_specialization.last_registered_version)

        self.test_ontology_specialization.register()

        self.assertTrue(self.test_ontology_specialization.is_registered)
        self.assertEqual(self.test_ontology_specialization.last_registered_version, self.test_ontology_specialization.version)

        # test_model_proxies = self.test_ontology_specialization.model_proxies.all()
        # test_category_proxies = QCategoryProxy.objects.filter(model_proxies__in=test_model_proxies)
        # test_property_proxies = QPropertyProxy.objects.filter(model_proxies__in=test_model_proxies)

        test_proxies = self.test_ontology_specialization.get_all_proxies()
        test_model_proxies = list(filter(lambda p: isinstance(p, QModelProxy), test_proxies))
        test_category_proxies = list(filter(lambda p: isinstance(p, QCategoryProxy), test_proxies))
        test_property_proxies = list(filter(lambda p: isinstance(p, QPropertyProxy), test_proxies))

        actual_model_proxies_data = sort_sequence_by_key(
            [
                serialize_model_to_dict(model_proxy, exclude=["id", "guid", "created", "modified", "category_proxies", "property_proxies"])
                for model_proxy in test_model_proxies
            ],
            "order"
        )

        test_model_proxies_data = sort_sequence_by_key(
            [
                {'cim_id': u'test_specialization_1.0.0.test_package.specialized_model', 'name': u'model',
                  'package': u'test_package', 'documentation': u'this is a specialized test model',
                  'label': {u'fields': [u'name'], u'text': u'model name: {}'},
                  'is_document': True, 'ontology': self.test_ontology_specialization.pk, 'order': 1, 'is_meta': False},
                {'cim_id': u'test_schema_2.0.0.test_package.recursive_thing', 'name': u'recursive_thing',
                  'package': u'test_package', 'documentation': None, 'label': None, 'is_document': False, 'ontology': self.test_ontology_schema.pk,
                  'order': 2, 'is_meta': False},
                {'cim_id': u'test_schema_2.0.0.test_package.other_thing_one', 'name': u'other_thing_one',
                  'package': u'test_package', 'documentation': None, 'label': None, 'is_document': False, 'ontology': self.test_ontology_schema.pk,
                  'order': 3, 'is_meta': False},
                {'cim_id': u'test_schema_2.0.0.test_package.other_thing_two', 'name': u'other_thing_two',
                  'package': u'test_package', 'documentation': None, 'label': None, 'is_document': False, 'ontology': self.test_ontology_schema.pk,
                  'order': 4, 'is_meta': False},
            ],
            "order"
        )

        for actual_model_proxy_data, test_model_proxy_data in zip(actual_model_proxies_data, test_model_proxies_data):
            self.assertDictEqual(actual_model_proxy_data, test_model_proxy_data)

        actual_category_proxies_data = sort_sequence_by_key(
            [
                serialize_model_to_dict(category_proxy, exclude=["id", "guid", "created", "modified"])
                for category_proxy in test_category_proxies
            ],
            "order"
        )

        recursive_thing_proxy = QModelProxy.objects.get(cim_id="{0}.test_package.recursive_thing".format(schema_key))
        other_thing_one_proxy = QModelProxy.objects.get(cim_id="{0}.test_package.other_thing_one".format(schema_key))
        other_thing_two_proxy = QModelProxy.objects.get(cim_id="{0}.test_package.other_thing_two".format(schema_key))
        schema_model_proxy  = QModelProxy.objects.get(cim_id="{0}.test_package.model".format(schema_key))
        specialization_model_proxy = QModelProxy.objects.get(cim_id="{0}.test_package.specialized_model".format(specialization_key))

        test_category_proxies_data = sort_sequence_by_key(
            [
                {'cim_id': 'test_schema_2.0.0.test_package.recursive_thing.uncategorized.uncategorized', 'is_uncategorized': True, 'name': u'uncategorized', 'documentation': None,
                  'ontology': self.test_ontology_schema.pk, 'order': 1, 'is_meta': None},
                {'cim_id': 'test_schema_2.0.0.test_package.other_thing_two.uncategorized.uncategorized', 'is_uncategorized': True, 'name': u'uncategorized', 'documentation': None,
                 'ontology': self.test_ontology_schema.pk, 'order': 1, 'is_meta': None},
                {'cim_id': 'test_specialization_1.0.0.test_package.specialized_model.category_one',
                 'is_uncategorized': False, 'name': u'category_one', 'documentation': None,
                 'ontology': self.test_ontology_specialization.pk, 'order': 1, 'is_meta': None},
                {'cim_id': 'test_schema_2.0.0.test_package.other_thing_one.uncategorized.uncategorized', 'is_uncategorized': True, 'name': u'uncategorized', 'documentation': None,
                 'ontology': self.test_ontology_schema.pk, 'order': 1, 'is_meta': None},
                {'cim_id': 'test_specialization_1.0.0.test_package.specialized_model.uncategorized.uncategorized', 'is_uncategorized': True, 'name': u'uncategorized', 'documentation': None,
                  'ontology': self.test_ontology_specialization.pk, 'order': 2, 'is_meta': None},
            ],
            "order"
        )

        for actual_category_proxy_data, test_category_proxy_data in zip(actual_category_proxies_data, test_category_proxies_data):
            self.assertDictEqual(actual_category_proxy_data, test_category_proxy_data)

        uncategoriezed_category_recursive_thing_proxy = recursive_thing_proxy.category_proxies.get(name__iexact=UNCATEGORIZED_CATEGORY_PROXY_NAME)
        uncategorized_category_other_thing_one_proxy = other_thing_one_proxy.category_proxies.get(name__iexact=UNCATEGORIZED_CATEGORY_PROXY_NAME)
        uncategorized_category_other_thing_two_proxy = other_thing_two_proxy.category_proxies.get(name__iexact=UNCATEGORIZED_CATEGORY_PROXY_NAME)
        uncategorized_category_schema_model_proxy  = schema_model_proxy.category_proxies.get(name__iexact=UNCATEGORIZED_CATEGORY_PROXY_NAME)
        uncategorized_category_specialization_model_proxy = specialization_model_proxy.category_proxies.get(name__iexact=UNCATEGORIZED_CATEGORY_PROXY_NAME)
        category_one_category_specialization_model_proxy = specialization_model_proxy.category_proxies.get(name__iexact="category_one")

        actual_property_proxies_data = sort_sequence_by_key(
            [
                serialize_model_to_dict(property_proxy, exclude=["id", "guid", "created", "modified"])
                for property_proxy in test_property_proxies
            ],
            "order"
        )

        test_property_proxies_data = sort_sequence_by_key(
            [
                {'cim_id': None, 'category_id': None, 'relationship_target_models': [], 'name': u'name',
                  'category_proxy': uncategorized_category_schema_model_proxy.pk, 'enumeration_choices': None, 'documentation': None, 'is_hierarchical': False,
                  'atomic_type': u'DEFAULT', 'model_proxy': specialization_model_proxy.pk, 'enumeration_is_open': False, 'is_nillable': True,
                  'cardinality_max': u'1', 'relationship_target_names': None, 'values': None, 'cardinality_min': u'1',
                  'ontology': self.test_ontology_schema.pk, 'field_type': u'ATOMIC', 'order': 1, 'is_meta': False},
                 {'cim_id': None, 'category_id': None, 'relationship_target_models': [], 'name': u'name',
                  'category_proxy': uncategoriezed_category_recursive_thing_proxy.pk, 'enumeration_choices': None, 'documentation': None, 'is_hierarchical': False,
                  'atomic_type': u'DEFAULT', 'model_proxy': recursive_thing_proxy.pk, 'enumeration_is_open': False, 'is_nillable': True,
                  'cardinality_max': u'1', 'relationship_target_names': None, 'values': None, 'cardinality_min': u'1',
                  'ontology': self.test_ontology_schema.pk, 'field_type': u'ATOMIC', 'order': 1, 'is_meta': False},
                 {'cim_id': None, 'category_id': None, 'relationship_target_models': [], 'name': u'name',
                  'category_proxy': uncategorized_category_other_thing_one_proxy.pk, 'enumeration_choices': None, 'documentation': None, 'is_hierarchical': False,
                  'atomic_type': u'DEFAULT', 'model_proxy': other_thing_one_proxy.pk, 'enumeration_is_open': False, 'is_nillable': True,
                  'cardinality_max': u'1', 'relationship_target_names': None, 'values': None, 'cardinality_min': u'1',
                  'ontology': self.test_ontology_schema.pk, 'field_type': u'ATOMIC', 'order': 1, 'is_meta': False},
                 {'cim_id': None, 'category_id': None, 'relationship_target_models': [], 'name': u'name',
                  'category_proxy': uncategorized_category_other_thing_two_proxy.pk, 'enumeration_choices': None, 'documentation': None, 'is_hierarchical': False,
                  'atomic_type': u'DEFAULT', 'model_proxy': other_thing_two_proxy.pk, 'enumeration_is_open': False, 'is_nillable': True,
                  'cardinality_max': u'1', 'relationship_target_names': None, 'values': None, 'cardinality_min': u'1',
                  'ontology': self.test_ontology_schema.pk, 'field_type': u'ATOMIC', 'order': 1, 'is_meta': False},
                 {'cim_id': None, 'category_id': None, 'relationship_target_models': [2], 'name': u'child',
                  'category_proxy': uncategoriezed_category_recursive_thing_proxy.pk, 'enumeration_choices': None, 'documentation': None, 'is_hierarchical': False,
                  'atomic_type': None, 'model_proxy': recursive_thing_proxy.pk, 'enumeration_is_open': False, 'is_nillable': True,
                  'cardinality_max': u'N',
                  'relationship_target_names': [u'test_schema_2.0.0.test_package.recursive_thing'], 'values': None,
                  'cardinality_min': u'0', 'ontology': self.test_ontology_schema.pk, 'field_type': u'RELATIONSHIP', 'order': 2, 'is_meta': False},
                 {'cim_id': None, 'category_id': None, 'relationship_target_models': [other_thing_one_proxy.pk, other_thing_two_proxy.pk],
                  'name': u'multiple_targets', 'category_proxy': uncategoriezed_category_recursive_thing_proxy.pk, 'enumeration_choices': None, 'documentation': None,
                  'is_hierarchical': False, 'atomic_type': None, 'model_proxy': recursive_thing_proxy.pk, 'enumeration_is_open': False,
                  'is_nillable': True, 'cardinality_max': u'1',
                  'relationship_target_names': [u'test_schema_2.0.0.test_package.other_thing_one',
                                                u'test_schema_2.0.0.test_package.other_thing_two'], 'values': None,
                  'cardinality_min': u'0', 'ontology': self.test_ontology_schema.pk, 'field_type': u'RELATIONSHIP', 'order': 3, 'is_meta': False},
                 {'cim_id': None,
                  'category_id': u'test_specialization_1.0.0.test_package.specialized_model.category_one',
                  'relationship_target_models': [], 'name': u'new_property', 'category_proxy': category_one_category_specialization_model_proxy.pk,
                  'enumeration_choices': None, 'documentation': None, 'is_hierarchical': False,
                  'atomic_type': u'DEFAULT', 'model_proxy': specialization_model_proxy.pk, 'enumeration_is_open': False, 'is_nillable': True,
                  'cardinality_max': u'1', 'relationship_target_names': None, 'values': [u'a predefined value'],
                  'cardinality_min': u'1', 'ontology': self.test_ontology_specialization.pk, 'field_type': u'ATOMIC', 'order': 3, 'is_meta': False},
                 {'cim_id': None, 'category_id': None, 'relationship_target_models': [recursive_thing_proxy.pk], 'name': u'thing',
                  'category_proxy': uncategorized_category_schema_model_proxy.pk, 'enumeration_choices': None,
                  'documentation': u'a relationship property; there are lots of spaces in this documentation',
                  'is_hierarchical': False, 'atomic_type': None, 'model_proxy': specialization_model_proxy.pk, 'enumeration_is_open': False,
                  'is_nillable': True, 'cardinality_max': u'1',
                  'relationship_target_names': [u'test_schema_2.0.0.test_package.recursive_thing'], 'values': None,
                  'cardinality_min': u'0', 'ontology': self.test_ontology_schema.pk, 'field_type': u'RELATIONSHIP', 'order': 3, 'is_meta': False},
            ],
            "order"
        )

        for actual_property_proxy_data, test_property_proxy_data in zip(actual_property_proxies_data, test_property_proxies_data):
            self.assertDictEqual(actual_property_proxy_data, actual_property_proxy_data)

    # @incomplete_test
    # def test_ontology_reregister(self):
    #     pass

    def test_ontology_register_specialization_doesnt_change_schema(self):
        self.test_ontology_schema.register()
        schema_model = self.test_ontology_schema.model_proxies.get(name="model")
        schema_model_name = schema_model.property_proxies.get(name="name")
        self.assertEqual(self.test_ontology_schema, schema_model_name.ontology)
        self.assertIn(schema_model, schema_model_name.model_proxies.all())
        self.assertEqual(1, schema_model_name.model_proxies.count())

        self.test_ontology_specialization.register()
        specialization_model = self.test_ontology_specialization.model_proxies.get(name="model")
        specialization_model_name = specialization_model.property_proxies.get(name="name")
        self.assertEqual(self.test_ontology_schema, specialization_model_name.ontology)
        self.assertIn(specialization_model, schema_model_name.model_proxies.all())
        self.assertEqual(2, schema_model_name.model_proxies.count())
