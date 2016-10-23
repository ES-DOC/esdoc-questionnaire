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

import json

from Q.questionnaire.tests.test_base import TestQBase, get_test_file_path, create_project, create_ontology, remove_ontology, create_categorization, remove_categorization
from Q.questionnaire.models.models_categorizations import UNCATEGORIZED_NAME
from Q.questionnaire.models.models_proxies import QModelProxy, QCategoryProxy, QPropertyProxy
from Q.questionnaire.models.models_customizations import *
from Q.questionnaire.q_utils import CIMTypes, serialize_model_to_dict, sort_list_by_key

class TestQCustomization(TestQBase):

    def setUp(self):

        # don't do the base setUp (it would interfere w/ the ids of the ontology created below)
        # super(TestQOntolgoy, self).setUp()
        self.test_project = create_project(
            name="project",
            title="Project",
            email="allyn.treshansky@colorado.edu",
            description="A test project to use while testing recursions",
        )
        self.test_categorization = create_categorization(
            filename="categorization.xml",
            name="categorization",
            version="2.0",
        )
        self.test_ontology_schema = create_ontology(
            filename="ontology_schema.xml",
            name="ontology",
            version="2.0",
        )
        self.test_ontology_schema.categorization = self.test_categorization
        self.test_ontology_schema.save()

        # TODO: SEE THE COMMENT IN "q_fields.py" ABOUT SETTING VERSION MANUALLY...
        self.test_ontology_schema.refresh_from_db()
        self.test_categorization.refresh_from_db()

        self.test_ontology_schema.register()
        self.test_categorization.register()

    def tearDown(self):

        # don't do the base tearDown
        # super(TestQOntolgoy, self).tearDown()

        remove_categorization(categorization=self.test_categorization)
        remove_ontology(ontology=self.test_ontology_schema)

    def test_reset_model(self):

        model_proxy = self.test_ontology_schema.model_proxies.get(name="model")

        model_customization = QModelCustomization(
            project=self.test_project,
            ontology=self.test_ontology_schema,
            proxy=model_proxy,
        )
        model_customization.reset()

        actual_model_customization_data = serialize_model_to_dict(
            model_customization,
            exclude=["id", "guid", "created", "modified", "relationship_source_property_customization"]  # note that I don't bother to check the 'relationship_source_property_customization' b/c I only ever access the reverse of that relationship (tested below)
        )

        test_model_customization_data = {
            'is_default': False,
            'description': u'',
            'model_title': u'Model',
            'project': self.test_project.pk,
            'synchronization': [],
            'ontology': self.test_ontology_schema.pk,
            'proxy': model_proxy.pk,
            'model_description': u'',
            'model_show_all_categories': False,
            'order': 1,
            'name': u'',
            'owner': None,
            'shared_owners': [],
        }

        self.assertDictEqual(actual_model_customization_data, test_model_customization_data)

    def test_reset_property(self):

        model_proxy = self.test_ontology_schema.model_proxies.get(name="model")

        atomic_property_proxy = QPropertyProxy.objects.get(name__iexact="name", model_proxy=model_proxy)
        enumeration_property_proxy = QPropertyProxy.objects.get(name__iexact="enumeration", model_proxy=model_proxy)
        relationship_property_proxy = QPropertyProxy.objects.get(name__iexact="thing", model_proxy=model_proxy)

        uncategorized_category = QCategoryProxy.objects.get(categorization=self.test_categorization, name=UNCATEGORIZED_NAME)

        test_model_customization = QModelCustomization(
            project=self.test_project,
            proxy=model_proxy,
        )
        test_model_customization.reset()

        with allow_unsaved_fk(QCategoryCustomization, ["model_customization"]):
            test_category_customization = QCategoryCustomization(
                proxy=QCategoryProxy.objects.get(pk=1),  # don't actually care which category I use for testing
                model_customization=test_model_customization,
            )
            test_category_customization.reset()

        with allow_unsaved_fk(QPropertyCustomization, ["model_customization", "category"]):

            # testing ATOMIC properties...

            atomic_property_customization = QPropertyCustomization(
                proxy=atomic_property_proxy,
                model_customization=test_model_customization,
                category=test_category_customization,
            )
            atomic_property_customization.reset()

            actual_atomic_property_customization_data = serialize_model_to_dict(
                atomic_property_customization,
                exclude=["id", "guid", "created", "modified"],
                include={
                    "relationship_target_model_customizations": atomic_property_customization.relationship_target_model_customizations.all(),
                }
            )

            test_atomic_property_customization_data = {
                'name': u'',
                'field_type': u'ATOMIC',
                'is_nillable': False,
                'documentation': u'',
                'relationship_show_subform': False,
                'atomic_type': u'DEFAULT',
                'enumeration_open': False,
                'relationship_target_model_customizations': [],
                # 'model_customization': ?!?,
                'proxy': atomic_property_proxy.pk,
                'inline_help': False,
                'is_hidden': False,
                'is_editable': True,
                'is_required': True,
                'atomic_default': None,
                'order': 1,
                'property_title': 'Name',
                'atomic_suggestions': ''
            }

            self.assertDictEqual(actual_atomic_property_customization_data, test_atomic_property_customization_data, excluded_keys=["category", "model_customization"])
            self.assertEqual(atomic_property_customization.model_customization, test_model_customization)
            self.assertEqual(atomic_property_customization.category, test_category_customization)

            # testing ENUMERATION properties...

            enumeration_property_customization = QPropertyCustomization(
                proxy=enumeration_property_proxy,
                model_customization=test_model_customization,
                category=test_category_customization,
            )
            enumeration_property_customization.reset()

            actual_enumeration_property_customization_data = serialize_model_to_dict(
                enumeration_property_customization,
                exclude=["id", "guid", "created", "modified"],
                include={
                    "relationship_target_model_customizations": atomic_property_customization.relationship_target_model_customizations.all()
                }
            )

            test_enumeration_property_customization_data = {
                'name': u'',
                'field_type': u'ENUMERATION',
                'is_nillable': True,
                'documentation': u'A test enumeration.',
                'relationship_show_subform': False,
                'atomic_type': 'DEFAULT',
                'enumeration_open': False,
                'relationship_target_model_customizations': [],
                # 'model_customization': ?!?,
                'proxy': enumeration_property_proxy.pk,
                'inline_help': False,
                'is_hidden': False,
                'is_editable': True,
                'is_required': False,
                'atomic_default': None,
                'order': 2,
                'property_title': u'Enumeration',
                'atomic_suggestions': None
            }

            self.assertDictEqual(actual_enumeration_property_customization_data, test_enumeration_property_customization_data, excluded_keys=["category", "model_customization"])
            self.assertEqual(enumeration_property_customization.model_customization, test_model_customization)
            self.assertEqual(enumeration_property_customization.category, test_category_customization)

            # testing RELATIONSHIP properties...

            relationship_property_customization = QPropertyCustomization(
                proxy=relationship_property_proxy,
                model_customization=test_model_customization,
                category=test_category_customization,
            )
            relationship_property_customization.reset()

            actual_relationship_property_customization_data = serialize_model_to_dict(
                relationship_property_customization,
                exclude=["id", "guid", "created", "modified"],
                include={
                    "relationship_target_model_customizations": atomic_property_customization.relationship_target_model_customizations.all(),
                }
            )

            test_relationship_property_customization_data = {
                'name': u'',
                'field_type': u'RELATIONSHIP',
                'is_nillable': True,
                'documentation': u'A relationship property; there are lots of spaces in this documentation.',
                'relationship_show_subform': True,
                'atomic_type': 'DEFAULT',
                'atomic_suggestions': None,
                'enumeration_open': False,
                'relationship_target_model_customizations': [],
                # 'model_customization': ?!?,
                'proxy': relationship_property_proxy.pk,
                'inline_help': False,
                'is_hidden': False,
                'is_editable': True,
                'is_required': False,
                'atomic_default': None,
                'order': 3,
                'property_title': u'Thing',
            }

            self.assertDictEqual(actual_relationship_property_customization_data, test_relationship_property_customization_data, excluded_keys=["category", "model_customization"])
            self.assertEqual(relationship_property_customization.model_customization, test_model_customization)
            self.assertEqual(relationship_property_customization.category, test_category_customization)

    # def test_get_new_customizations(self):
    #
    #     model_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="model")
    #     recursive_thing_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="recursive_thing")
    #
    #     test_customizations = get_new_customizations(
    #         project=self.test_project,
    #         ontology=self.test_ontology_schema,
    #         model_proxy=model_proxy,
    #         key=model_proxy.name,
    #     )
    #
    #     self.assertEqual(len(test_customizations), 3)
    #
    #     actual_model_customization_data = serialize_model_to_dict(
    #         test_customizations["model_customization"],
    #         exclude=["id", "guid", "created", "modified"]
    #     )
    #     test_model_customization_data = {
    #         'is_default': False,
    #         'name': u'',
    #         'model_title': u'Model',
    #         'project': self.test_project.pk,
    #         'synchronization': [],
    #         'proxy': model_proxy.pk,
    #         'model_show_all_categories': False,
    #         'model_description': u'',
    #         'ontology': self.test_ontology_schema.pk,
    #         'description': u'',
    #         'order': 1,
    #     }
    #
    #     self.assertDictEqual(actual_model_customization_data, test_model_customization_data)
    #
    #     actual_category_customizations_data = [
    #         serialize_model_to_dict(category_customization, exclude=["id", "guid", "created", "modified"])
    #         for category_customization in test_customizations["category_customizations"]
    #     ]
    #     test_category_customizations_data = sort_list_by_key(
    #         [
    #             {'name': u'', 'category_title': u'Category One', 'order': 1, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category One").pk, 'documentation': u'I am category one.'},
    #             {'name': u'', 'category_title': u'Category Two', 'order': 2, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category Two").pk, 'documentation': u'I am category two.'},
    #             {'name': u'', 'category_title': u'Category Three', 'order': 3, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category Three").pk, 'documentation': u'I am category three.'},
    #             {'name': u'', 'category_title': u'Uncategorized', 'order': 4, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Uncategorized").pk, 'documentation': u''},
    #
    #         ],
    #         "order",
    #     )
    #     for actual_category_customization_data, test_category_customization_data in zip(actual_category_customizations_data, test_category_customizations_data):
    #         self.assertDictEqual(actual_category_customization_data, test_category_customization_data)
    #
    #     actual_property_customizations_data = [
    #         serialize_model_to_dict(property_customization, exclude=["id", "guid", "created", "modified"])
    #         for property_customization in test_customizations["property_customizations"]
    #     ]
    #     test_property_customizations_data = sort_list_by_key(
    #         [
    #             {'name': u'', 'documentation': u'', 'is_hidden': False, 'is_nillable': True, 'relationship_target_customization_keys': None, 'relationship_target_model_customizations': [], 'field_type': u'ATOMIC', 'atomic_default': None, 'inline_help': False, 'property_title': u'Name', 'is_editable': True, 'proxy': model_proxy.property_proxies.get(name="name").pk, 'is_required': True, 'relationship_show_subform': False, 'order': 1, 'enumeration_open': False, 'atomic_type': u'DEFAULT', 'atomic_suggestions': ''},
    #             {'name': u'', 'documentation': u'A test enumeration.', 'is_hidden': False, 'is_nillable': True, 'relationship_target_customization_keys': None, 'relationship_target_model_customizations': [], 'field_type': u'ENUMERATION', 'atomic_default': None, 'inline_help': False, 'property_title': u'Enumeration', 'is_editable': True, 'proxy': model_proxy.property_proxies.get(name="enumeration").pk, 'is_required': False, 'relationship_show_subform': False, 'order': 2, 'enumeration_open': False, 'atomic_type': 'DEFAULT', 'atomic_suggestions': None},
    #             {'name': u'', 'documentation': u'A relationship property; there are lots of spaces in this documentation.', 'is_hidden': False, 'is_nillable': True, 'relationship_target_customization_keys': None, 'relationship_target_model_customizations': [], 'field_type': u'RELATIONSHIP', 'atomic_default': None, 'inline_help': False, 'property_title': u'Thing', 'is_editable': True, 'proxy': model_proxy.property_proxies.get(name="thing").pk, 'is_required': False, 'relationship_show_subform': True, 'order': 3, 'enumeration_open': False, 'atomic_type': 'DEFAULT', 'atomic_suggestions': None},
    #         ],
    #         "order",
    #     )
    #     for actual_property_customization_data, test_property_customization_data in zip(actual_property_customizations_data, test_property_customizations_data):
    #         self.assertDictEqual(actual_property_customization_data, test_property_customization_data, excluded_keys=["model_customization", "category"])
    #
    #     # these tests really ought to be using a lambda fn that checks c.proxy.pk rather than c.property_title, but I'm lazy
    #     self.assertIn(
    #         find_in_sequence(lambda c: c.property_title == "Name", test_customizations["property_customizations"]).category,
    #         test_customizations["category_customizations"]
    #     )
    #     self.assertIn(
    #         find_in_sequence(lambda c: c.property_title == "Enumeration", test_customizations["property_customizations"]).category,
    #         test_customizations["category_customizations"]
    #     )
    #     self.assertIn(
    #         find_in_sequence(lambda c: c.property_title == "Thing", test_customizations["property_customizations"]).category,
    #         test_customizations["category_customizations"]
    #     )
    #
    #     test_subform_customizations = find_in_sequence(lambda c: c.proxy.name == "thing", test_customizations["property_customizations"]).unsaved_subform_customizations
    #
    #     self.assertEqual(len(test_subform_customizations), 1)
    #     test_subform_customizations = test_subform_customizations[0]
    #     self.assertEqual(len(test_subform_customizations), 3)
    #
    #     actual_subform_model_customization_data = serialize_model_to_dict(
    #         test_subform_customizations["model_customization"],
    #         exclude=["id", "guid", "created", "modified"]
    #     )
    #     test_subform_model_customization_data = {
    #         'is_default': False,
    #         'name': u'',
    #         'model_title': u'Recursive Thing',
    #         'project': self.test_project.pk,
    #         'synchronization': [],
    #         'proxy': recursive_thing_proxy.pk,
    #         'model_show_all_categories': False,
    #         'model_description': u'',
    #         'ontology': self.test_ontology_schema.pk,
    #         'description': u'',
    #         'order': 2,
    #
    #     }
    #     self.assertDictEqual(actual_subform_model_customization_data, test_subform_model_customization_data)
    #
    #     actual_subform_category_customizations_data = [
    #         serialize_model_to_dict(category_customization, exclude=["id", "guid", "created", "modified"])
    #         for category_customization in test_subform_customizations["category_customizations"]
    #     ]
    #     test_subform_category_customizations_data = sort_list_by_key(
    #         [
    #             {'name': u'', 'category_title': u'Category One', 'order': 1, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category One").pk, 'documentation': u'I am category one.'},
    #             {'name': u'', 'category_title': u'Category Two', 'order': 2, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category Two").pk, 'documentation': u'I am category two.'},
    #             {'name': u'', 'category_title': u'Category Three', 'order': 3, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category Three").pk, 'documentation': u'I am category three.'},
    #             {'name': u'', 'category_title': u'Uncategorized', 'order': 4, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Uncategorized").pk, 'documentation': u''},
    #         ],
    #         "order",
    #     )
    #     for actual_subform_category_customization_data, test_subform_category_customization_data in zip(actual_subform_category_customizations_data, test_subform_category_customizations_data):
    #         self.assertDictEqual(actual_subform_category_customization_data, test_subform_category_customization_data)
    #
    #     for subform_category_customization, category_customization in zip(test_subform_customizations["category_customizations"], test_customizations["category_customizations"]):
    #         # make sure that the subform categories use the same proxies but are in fact different instances
    #         self.assertEqual(subform_category_customization.proxy, category_customization.proxy)
    #         self.assertNotEqual(subform_category_customization.guid, category_customization.guid)
    #
    #     actual_subform_property_customizations_data = [
    #         serialize_model_to_dict(property_customization, exclude=["id", "guid", "created", "modified"])
    #         for property_customization in test_subform_customizations["property_customizations"]
    #     ]
    #     test_subform_property_customizations_data = sort_list_by_key(
    #         [
    #             {'documentation': u'', 'relationship_target_customization_keys': None, 'relationship_target_model_customizations': [], 'is_hidden': False, 'field_type': u'ATOMIC', 'is_nillable': True, 'atomic_default': None, 'inline_help': False, 'property_title': u'Name', 'is_editable': True, 'proxy': recursive_thing_proxy.property_proxies.get(name="name").pk, 'name': u'', 'is_required': True, 'relationship_show_subform': False, 'order': 1, 'enumeration_open': False, 'atomic_type': u'DEFAULT', 'atomic_suggestions': ''},
    #             {'documentation': u'', 'relationship_target_customization_keys': None, 'relationship_target_model_customizations': [], 'is_hidden': False, 'field_type': u'RELATIONSHIP', 'is_nillable': True, 'atomic_default': None, 'inline_help': False, 'property_title': u'Child', 'is_editable': True, 'proxy': recursive_thing_proxy.property_proxies.get(name="child").pk, 'name': u'', 'is_required': False, 'relationship_show_subform': True, 'order': 2, 'enumeration_open': False, 'atomic_type': 'DEFAULT', 'atomic_suggestions': None},
    #         ],
    #         "order",
    #     )
    #
    #     for actual_subform_property_customization_data, test_subform_property_customization_data in zip(actual_subform_property_customizations_data, test_subform_property_customizations_data):
    #         self.assertDictEqual(actual_subform_property_customization_data, test_subform_property_customization_data, excluded_keys=["model_customization", "category"])
    #
    #     self.assertIn(
    #         find_in_sequence(lambda c: c.property_title == "Name", test_subform_customizations["property_customizations"]).category,
    #         test_subform_customizations["category_customizations"]
    #     )
    #     self.assertIn(
    #         find_in_sequence(lambda c: c.property_title == "Child", test_subform_customizations["property_customizations"]).category,
    #         test_subform_customizations["category_customizations"]
    #     )
    #
    #     test_subform_subform_customizations = find_in_sequence(lambda c: c.proxy.name == "child", test_subform_customizations["property_customizations"]).unsaved_subform_customizations
    #     self.assertEqual(len(test_subform_subform_customizations), 1)
    #     test_subform_subform_customizations = test_subform_subform_customizations[0]
    #     self.assertEqual(len(test_subform_subform_customizations), 3)
    #
    #     actual_subform_subform_model_customization_data = serialize_model_to_dict(
    #         test_subform_subform_customizations["model_customization"],
    #         exclude=["id", "guid", "created", "modified"]
    #     )
    #     test_subform_subform_model_customization_data = {
    #         'is_default': False, 'name': u'', 'model_title': u'Recursive Thing', 'project': self.test_project.pk, 'synchronization': [], 'proxy': recursive_thing_proxy.pk, 'model_show_all_categories': False, 'model_description': u'', 'ontology': self.test_ontology_schema.pk, 'description': u'', 'order': 2,
    #     }
    #     self.assertDictEqual(actual_subform_subform_model_customization_data, test_subform_subform_model_customization_data)
    #     self.assertNotEqual(test_subform_subform_customizations["model_customization"], test_subform_customizations["model_customization"])
    #
    #     actual_subform_subform_category_customizations_data = [
    #         serialize_model_to_dict(category_customization, exclude=["id", "guid", "created", "modified"])
    #         for category_customization in test_subform_subform_customizations["category_customizations"]
    #     ]
    #     test_subform_subform_category_customizations_data = sort_list_by_key(
    #         [
    #             {'name': u'', 'category_title': u'Category One', 'order': 1, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category One").pk, 'documentation': u'I am category one.'},
    #             {'name': u'', 'category_title': u'Category Two', 'order': 2, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category Two").pk, 'documentation': u'I am category two.'},
    #             {'name': u'', 'category_title': u'Category Three', 'order': 3, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category Three").pk, 'documentation': u'I am category three.'},
    #             {'name': u'', 'category_title': u'Uncategorized', 'order': 4, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Uncategorized").pk, 'documentation': u''},
    #         ],
    #         "order",
    #     )
    #     for actual_subform_subform_category_customization_data, test_subform_subform_category_customization_data in zip(actual_subform_subform_category_customizations_data, test_subform_subform_category_customizations_data):
    #         self.assertDictEqual(actual_subform_subform_category_customization_data, test_subform_subform_category_customization_data, excluded_keys=["model_customization"])
    #
    #     for subform_subform_category_customization, category_customization in zip(test_subform_subform_customizations["category_customizations"], test_customizations["category_customizations"]):
    #         self.assertEqual(subform_subform_category_customization.proxy, category_customization.proxy)
    #         self.assertNotEqual(subform_subform_category_customization, category_customization)
    #
    #     actual_subform_subform_property_customizations_data = sort_list_by_key(
    #         [
    #             serialize_model_to_dict(property_customization, exclude=["id", "guid", "created", "modified"])
    #             for property_customization in test_subform_subform_customizations["property_customizations"]
    #         ],
    #         "order",
    #     )
    #     test_subform_subform_property_customizations_data = sort_list_by_key(
    #         [
    #             {'documentation': u'', 'is_hidden': False, 'field_type': u'ATOMIC', 'is_nillable': True, 'atomic_default': None, 'inline_help': False, 'property_title': u'Name', 'is_editable': True, 'proxy': recursive_thing_proxy.property_proxies.get(name="name").pk, 'relationship_target_customization_keys': None, 'relationship_target_model_customizations': [], 'name': u'', 'is_required': True, 'relationship_show_subform': False, 'order': 1, 'enumeration_open': False, 'atomic_type': u'DEFAULT', 'atomic_suggestions': ''},
    #             {'documentation': u'', 'is_hidden': False, 'field_type': u'RELATIONSHIP', 'is_nillable': True, 'atomic_default': None, 'inline_help': False, 'property_title': u'Child', 'is_editable': True, 'proxy': recursive_thing_proxy.property_proxies.get(name="child").pk, 'relationship_target_customization_keys': None, 'relationship_target_model_customizations': [], 'name': u'', 'is_required': False, 'relationship_show_subform': True, 'order': 2, 'enumeration_open': False, 'atomic_type': 'DEFAULT', 'atomic_suggestions': None},
    #             {'documentation': u'', 'is_hidden': False, 'field_type': u'RELATIONSHIP', 'is_nillable': True, 'atomic_default': None, 'inline_help': False, 'property_title': u'Multiple Targets', 'is_editable': True, 'proxy': recursive_thing_proxy.property_proxies.get(name="multiple_targets").pk, 'relationship_target_customization_keys': None, 'relationship_target_model_customizations': [], 'name': u'', 'is_required': False, 'relationship_show_subform': True, 'order': 3, 'enumeration_open': False, 'atomic_type': 'DEFAULT', 'atomic_suggestions': None},
    #         ],
    #         "order",
    #     )
    #     for actual_subform_subform_property_customization_data, test_subform_subform_property_customization_data in zip(actual_subform_subform_property_customizations_data, test_subform_subform_property_customizations_data):
    #         self.assertDictEqual(actual_subform_subform_property_customization_data, test_subform_subform_property_customization_data, excluded_keys=["model_customization", "category"])
    #
    #     self.assertIn(
    #         find_in_sequence(lambda c: c.property_title == "Name", test_subform_subform_customizations["property_customizations"]).category,
    #         test_subform_subform_customizations["category_customizations"]
    #     )
    #     self.assertIn(
    #         find_in_sequence(lambda c: c.property_title == "Child", test_subform_subform_customizations["property_customizations"]).category,
    #         test_subform_subform_customizations["category_customizations"]
    #     )
    #     self.assertIn(
    #         find_in_sequence(lambda c: c.property_title == "Multiple Targets", test_subform_subform_customizations["property_customizations"]).category,
    #         test_subform_subform_customizations["category_customizations"]
    #     )
    #
    #     test_subform_subform_subform_customizations = find_in_sequence(lambda c: c.proxy.name == "child", test_subform_subform_customizations["property_customizations"]).unsaved_subform_customizations
    #     self.assertEqual(len(test_subform_subform_subform_customizations), 1)
    #     test_subform_subform_subform_customizations = test_subform_subform_subform_customizations[0]
    #     self.assertEqual(len(test_subform_subform_subform_customizations), 3)
    #
    #     # finally, at the lowest level of recursion, make sure the subforms point to the same customizations
    #     self.assertDictEqual(test_subform_subform_subform_customizations, test_subform_subform_customizations)
