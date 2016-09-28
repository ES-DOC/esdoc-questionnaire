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
        import ipdb; ipdb.set_trace()
        self.test_project = create_project(
            name="test_project",
            title="Test Project",
            email="allyn.treshansky@colorado.edu",
            description="A test project to use while testing recursions",
        )
        self.test_categorization = create_categorization(
            filename="categorization.xml",
            name="test_categorization",
            version="2.0",
        )
        self.test_ontology_schema = create_ontology(
            filename="ontology_schema.xml",
            name="test_ontology_schema",
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
            exclude=["id", "guid", "created", "modified"]
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
        }

        self.assertDictEqual(actual_model_customization_data, test_model_customization_data)

    def test_reset_property(self):

        import ipdb; ipdb.set_trace()
        model_proxy = self.test_ontology_schema.model_proxies.get(name="model")

        atomic_property_proxy = QPropertyProxy.objects.get(name__iexact="name", model_proxy=model_proxy)
        enumeration_property_proxy = QPropertyProxy.objects.get(name__iexact="enumeration", model_proxy=model_proxy)
        relationship_property_proxy = QPropertyProxy.objects.get(name__iexact="thing", model_proxy=model_proxy)

        uncategorized_category = QCategoryProxy.objects.get(name=UNCATEGORIZED_NAME)

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
            )

            test_atomic_property_customization_data = {
                #'category': None,
                'name': u'',
                'field_type': u'ATOMIC',
                'is_nillable': True,
                'documentation': u'',
                'relationship_show_subform': False,
                'atomic_type': u'DEFAULT',
                'enumeration_open': False,
                'relationship_target_customization_keys': None,
                'relationship_target_model_customizations': [],
                # 'model_customization': None,
                'proxy': atomic_property_proxy.pk,
                'inline_help': False,
                'is_hidden': False,
                'is_editable': True,
                'is_required': True,
                'atomic_default': None,
                'order': 1,
                'property_title': u'Name',
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
            )

            test_enumeration_property_customization_data = {
                #'category': None,
                'name': u'',
                'field_type': u'ENUMERATION',
                'is_nillable': True,
                'documentation': u'A test enumeration.',
                'relationship_show_subform': False,
                'atomic_type': 'DEFAULT',
                'enumeration_open': False,
                'relationship_target_customization_keys': None,
                'relationship_target_model_customizations': [],
                # 'model_customization': None,
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
            )

            test_relationship_property_customization_data = {
                #'category': None,
                'name': u'',
                'field_type': u'RELATIONSHIP',
                'is_nillable': True,
                'documentation': u'A relationship property; there are lots of spaces in this documentation.',
                'relationship_show_subform': True,
                'atomic_type': 'DEFAULT',
                'atomic_suggestions': None,
                'enumeration_open': False,
                'relationship_target_customization_keys': None,
                'relationship_target_model_customizations': [],
                # 'model_customization': None,
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

    def test_get_new_customizations_pt1(self):

        # model proxies...
        model_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="model")
        recursive_thing_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="recursive_thing")
        other_thing_one_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="other_thing_one")
        other_thing_two_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="other_thing_two")

        # category proxies...
        category_proxies = self.test_ontology_schema.categorization.category_proxies.all()

        # property_proxies...
        model_proxy_name_property_proxy = model_proxy.property_proxies.get(name__iexact="name")
        model_proxy_enumeration_property_proxy = model_proxy.property_proxies.get(name__iexact="enumeration")
        model_proxy_thing_property_proxy = model_proxy.property_proxies.get(name__iexact="thing")
        recursive_thing_proxy_name_property_proxy = recursive_thing_proxy.property_proxies.get(name__iexact="name")
        recursive_thing_proxy_child_property_proxy = recursive_thing_proxy.property_proxies.get(name__iexact="child")
        recursive_thing_proxy_multiple_targets_property_proxy = recursive_thing_proxy.property_proxies.get(name__iexact="multiple_targets")
        other_thing_one_proxy_name_property_proxy = other_thing_one_proxy.property_proxies.get(name__iexact="name")
        other_thing_two_proxy_name_property_proxy = other_thing_two_proxy.property_proxies.get(name__iexact="name")

        test_customizations = get_new_customizations_pt1(
            project=self.test_project,
            ontology=self.test_ontology_schema,
            model_proxy=model_proxy,
        )

        # get the top_level customizations...
        top_level_customizations = test_customizations
        top_level_model_customization = test_customizations["model_customization"]
        top_level_category_customizations = test_customizations["category_customizations"]
        top_level_property_customizations = sort_list_by_key(
            test_customizations["property_customizations"],
            "order"
        )
        # test the top_level customizations...
        self.assertEqual(len(top_level_customizations), 3)
        self.assertEqual(len(top_level_category_customizations), 4)
        self.assertEqual(len(top_level_property_customizations), 3)
        self.assertEqual(top_level_model_customization.proxy, model_proxy)
        self.assertSetEqual(
            set([c.proxy for c in top_level_category_customizations]),
            set(category_proxies)
        )
        self.assertEqual(top_level_property_customizations[0].proxy, model_proxy_name_property_proxy)
        self.assertEqual(top_level_property_customizations[1].proxy, model_proxy_enumeration_property_proxy)
        self.assertEqual(top_level_property_customizations[2].proxy, model_proxy_thing_property_proxy)
        self.assertEqual(len(top_level_property_customizations[2].unsaved_subform_customizations), 1)

        # get the model::thing subform customizations...
        model_thing_subform_customizations = top_level_property_customizations[2].unsaved_subform_customizations[0]
        model_thing_subform_model_customization = model_thing_subform_customizations["model_customization"]
        model_thing_subform_category_customizations = model_thing_subform_customizations["category_customizations"]
        model_thing_subform_property_customizations = sort_list_by_key(
            model_thing_subform_customizations["property_customizations"],
            "order"
        )

        # test the model::thing subform customizations...
        self.assertEqual(len(model_thing_subform_customizations), 3)
        self.assertEqual(len(model_thing_subform_category_customizations), 4)
        self.assertEqual(len(model_thing_subform_property_customizations), 3)
        self.assertEqual(model_thing_subform_model_customization.proxy, recursive_thing_proxy)
        self.assertSetEqual(
            set([c.proxy for c in model_thing_subform_category_customizations]),
            set(category_proxies)
        )
        self.assertEqual(model_thing_subform_property_customizations[0].proxy, recursive_thing_proxy_name_property_proxy)
        self.assertEqual(model_thing_subform_property_customizations[1].proxy, recursive_thing_proxy_child_property_proxy)
        self.assertEqual(model_thing_subform_property_customizations[2].proxy, recursive_thing_proxy_multiple_targets_property_proxy)
        self.assertEqual(len(model_thing_subform_property_customizations[1].unsaved_subform_customizations), 1)
        self.assertEqual(len(model_thing_subform_property_customizations[2].unsaved_subform_customizations), 2)

        # get the model::thing::child subform customizations...
        model_thing_child_subform_customizations = model_thing_subform_property_customizations[1].unsaved_subform_customizations[0]
        model_thing_child_subform_model_customization = model_thing_child_subform_customizations["model_customization"]
        model_thing_child_subform_category_customizations = model_thing_child_subform_customizations["category_customizations"]
        model_thing_child_subform_property_customizations = sort_list_by_key(
            model_thing_child_subform_customizations["property_customizations"],
            "order"
        )

        # test the model::thing::child subform customizations...
        self.assertEqual(len(model_thing_child_subform_customizations), 3)
        self.assertEqual(len(model_thing_child_subform_category_customizations), 4)
        self.assertEqual(len(model_thing_child_subform_property_customizations), 3)
        self.assertEqual(model_thing_child_subform_model_customization.proxy, recursive_thing_proxy)
        self.assertNotEqual(model_thing_child_subform_model_customization, model_thing_subform_model_customization)
        self.assertSetEqual(
            set([c.proxy for c in model_thing_child_subform_category_customizations]),
            set(category_proxies)
        )
        self.assertEqual(model_thing_child_subform_property_customizations[0].proxy, recursive_thing_proxy_name_property_proxy)
        self.assertNotEqual(model_thing_child_subform_property_customizations[0], model_thing_subform_property_customizations[0])
        self.assertEqual(model_thing_child_subform_property_customizations[1].proxy, recursive_thing_proxy_child_property_proxy)
        self.assertNotEqual(model_thing_child_subform_property_customizations[1], model_thing_subform_property_customizations[1])
        self.assertEqual(model_thing_child_subform_property_customizations[2].proxy, recursive_thing_proxy_multiple_targets_property_proxy)
        self.assertNotEqual(model_thing_child_subform_property_customizations[2], model_thing_subform_property_customizations[2])
        self.assertEqual(len(model_thing_child_subform_property_customizations[1].unsaved_subform_customizations), 1)
        self.assertEqual(len(model_thing_child_subform_property_customizations[2].unsaved_subform_customizations), 2)

        # get the model::thing::multiple_targets subform customizations...
        model_thing_multiple_targets_other_thing_one_subform_customizations = model_thing_subform_property_customizations[2].unsaved_subform_customizations[0]
        model_thing_multiple_targets_other_thing_one_subform_model_customization = model_thing_multiple_targets_other_thing_one_subform_customizations["model_customization"]
        model_thing_multiple_targets_other_thing_one_subform_category_customizations = model_thing_multiple_targets_other_thing_one_subform_customizations["category_customizations"]
        model_thing_multiple_targets_other_thing_one_subform_property_customizations = model_thing_multiple_targets_other_thing_one_subform_customizations["property_customizations"]
        model_thing_multiple_targets_other_thing_two_subform_customizations = model_thing_subform_property_customizations[2].unsaved_subform_customizations[1]
        model_thing_multiple_targets_other_thing_two_subform_model_customization = model_thing_multiple_targets_other_thing_two_subform_customizations["model_customization"]
        model_thing_multiple_targets_other_thing_two_subform_category_customizations = model_thing_multiple_targets_other_thing_two_subform_customizations["category_customizations"]
        model_thing_multiple_targets_other_thing_two_subform_property_customizations = model_thing_multiple_targets_other_thing_two_subform_customizations["property_customizations"]

        # test the model::thing::multiple_targets subform customizations...
        self.assertEqual(len(model_thing_multiple_targets_other_thing_one_subform_customizations), 3)
        self.assertEqual(model_thing_multiple_targets_other_thing_one_subform_model_customization.proxy, other_thing_one_proxy)
        self.assertIsNone(model_thing_multiple_targets_other_thing_one_subform_category_customizations)
        self.assertIsNone(model_thing_multiple_targets_other_thing_one_subform_property_customizations)
        self.assertEqual(len(model_thing_multiple_targets_other_thing_two_subform_customizations), 3)
        self.assertEqual(model_thing_multiple_targets_other_thing_two_subform_model_customization.proxy, other_thing_two_proxy)
        self.assertIsNone(model_thing_multiple_targets_other_thing_two_subform_category_customizations)
        self.assertIsNone(model_thing_multiple_targets_other_thing_two_subform_property_customizations)

        # get the model::thing::child::child subform customizations...
        model_thing_child_child_subform_customizations = model_thing_child_subform_property_customizations[1].unsaved_subform_customizations[0]
        model_thing_child_child_subform_model_customization = model_thing_child_child_subform_customizations["model_customization"]
        model_thing_child_child_subform_category_customizations = model_thing_child_child_subform_customizations["category_customizations"]
        model_thing_child_child_subform_property_customizations = model_thing_child_child_subform_customizations["property_customizations"]

        # test the model::thing::child::child subform customizations...
        self.assertEqual(len(model_thing_child_child_subform_customizations), 3)
        self.assertEqual(model_thing_child_child_subform_model_customization.proxy, recursive_thing_proxy)
        self.assertEqual(model_thing_child_child_subform_model_customization, model_thing_child_subform_model_customization)
        self.assertIsNone(model_thing_child_child_subform_category_customizations)
        self.assertIsNone(model_thing_child_child_subform_property_customizations)

        # get the model::thing::child::multiple_targets subform customizations...
        model_thing_child_multiple_targets_other_thing_one_subform_customizations = model_thing_child_subform_property_customizations[2].unsaved_subform_customizations[0]
        model_thing_child_multiple_targets_other_thing_one_subform_model_customization = model_thing_child_multiple_targets_other_thing_one_subform_customizations["model_customization"]
        model_thing_child_multiple_targets_other_thing_one_subform_category_customizations = model_thing_child_multiple_targets_other_thing_one_subform_customizations["category_customizations"]
        model_thing_child_multiple_targets_other_thing_one_subform_property_customizations = sort_list_by_key(
            model_thing_child_multiple_targets_other_thing_one_subform_customizations["property_customizations"],
            "order"
        )
        model_thing_child_multiple_targets_other_thing_two_subform_customizations = model_thing_child_subform_property_customizations[2].unsaved_subform_customizations[1]
        model_thing_child_multiple_targets_other_thing_two_subform_model_customization = model_thing_child_multiple_targets_other_thing_two_subform_customizations["model_customization"]
        model_thing_child_multiple_targets_other_thing_two_subform_category_customizations = model_thing_child_multiple_targets_other_thing_two_subform_customizations["category_customizations"]
        model_thing_child_multiple_targets_other_thing_two_subform_property_customizations = sort_list_by_key(
            model_thing_child_multiple_targets_other_thing_two_subform_customizations["property_customizations"],
            "order"
        )

        # test the model::thing::child::multiple_targets subform_customizations
        self.assertEqual(len(model_thing_child_multiple_targets_other_thing_one_subform_customizations), 3)
        self.assertEqual(len(model_thing_child_multiple_targets_other_thing_one_subform_category_customizations), 4)
        self.assertEqual(len(model_thing_child_multiple_targets_other_thing_one_subform_property_customizations), 1)
        self.assertEqual(model_thing_child_multiple_targets_other_thing_one_subform_model_customization.proxy, other_thing_one_proxy)
        self.assertEqual(model_thing_child_multiple_targets_other_thing_one_subform_model_customization, model_thing_multiple_targets_other_thing_one_subform_model_customization)
        self.assertSetEqual(
            set([c.proxy for c in model_thing_child_multiple_targets_other_thing_one_subform_category_customizations]),
            set(category_proxies)
        )
        self.assertEqual(model_thing_child_multiple_targets_other_thing_one_subform_property_customizations[0].proxy, other_thing_one_proxy_name_property_proxy)

        self.assertEqual(len(model_thing_child_multiple_targets_other_thing_two_subform_customizations), 3)
        self.assertEqual(len(model_thing_child_multiple_targets_other_thing_two_subform_category_customizations), 4)
        self.assertEqual(len(model_thing_child_multiple_targets_other_thing_two_subform_property_customizations), 1)
        self.assertEqual(model_thing_child_multiple_targets_other_thing_two_subform_model_customization.proxy, other_thing_two_proxy)
        self.assertEqual(model_thing_child_multiple_targets_other_thing_two_subform_model_customization, model_thing_multiple_targets_other_thing_two_subform_model_customization)
        self.assertSetEqual(
            set([c.proxy for c in model_thing_child_multiple_targets_other_thing_two_subform_category_customizations]),
            set(category_proxies)
        )
        self.assertEqual(model_thing_child_multiple_targets_other_thing_two_subform_property_customizations[0].proxy, other_thing_two_proxy_name_property_proxy)

    def test_get_new_customizations_pt2(self):

        # model proxies...
        model_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="model")
        recursive_thing_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="recursive_thing")
        other_thing_one_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="other_thing_one")
        other_thing_two_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="other_thing_two")

        # category proxies...
        category_proxies = self.test_ontology_schema.categorization.category_proxies.all()

        # property_proxies...
        model_proxy_name_property_proxy = model_proxy.property_proxies.get(name__iexact="name")
        model_proxy_enumeration_property_proxy = model_proxy.property_proxies.get(name__iexact="enumeration")
        model_proxy_thing_property_proxy = model_proxy.property_proxies.get(name__iexact="thing")
        recursive_thing_proxy_name_property_proxy = recursive_thing_proxy.property_proxies.get(name__iexact="name")
        recursive_thing_proxy_child_property_proxy = recursive_thing_proxy.property_proxies.get(name__iexact="child")
        recursive_thing_proxy_multiple_targets_property_proxy = recursive_thing_proxy.property_proxies.get(name__iexact="multiple_targets")
        other_thing_one_proxy_name_property_proxy = other_thing_one_proxy.property_proxies.get(name__iexact="name")
        other_thing_two_proxy_name_property_proxy = other_thing_two_proxy.property_proxies.get(name__iexact="name")

        test_created_customizations = {}
        test_customizations = get_new_customizations_pt1(
            project=self.test_project,
            ontology=self.test_ontology_schema,
            model_proxy=model_proxy,
            previously_created_customizations=test_created_customizations
        )
        get_new_customizations_pt2(
            test_customizations,
            previously_created_customizations=test_created_customizations
        )

        # I know most of test_customizations is set property based on 'test_get_new_customizations_pt1'
        # this just tests the bits of test_customizations that 'test_get_new_customizations_pt2' completes

        model_thing_subform_customizations = sort_list_by_key(
            test_customizations["property_customizations"],
            "order"
        )[2].unsaved_subform_customizations[0]
        model_thing_subform_category_customizations = sort_list_by_key(
            model_thing_subform_customizations["category_customizations"],
            "order"
        )
        model_thing_subform_property_customizations = sort_list_by_key(
            model_thing_subform_customizations["property_customizations"],
            "order"
        )

        model_thing_child_subform_customizations = model_thing_subform_property_customizations[1].unsaved_subform_customizations[0]
        model_thing_child_subform_category_customizations = sort_list_by_key(
            model_thing_child_subform_customizations["category_customizations"],
            "order"
        )
        model_thing_child_subform_property_customizations = sort_list_by_key(
            model_thing_child_subform_customizations["property_customizations"],
            "order"
        )

        model_thing_child_child_subform_customizations = model_thing_child_subform_property_customizations[1].unsaved_subform_customizations[0]
        model_thing_child_child_subform_category_customizations = sort_list_by_key(
            model_thing_child_child_subform_customizations["category_customizations"],
            "order"
        )
        model_thing_child_child_subform_property_customizations = sort_list_by_key(
            model_thing_child_child_subform_customizations["property_customizations"],
            "order"
        )

        model_thing_multiple_targets_subform_customizations = model_thing_subform_property_customizations[2].unsaved_subform_customizations
        model_thing_multiple_targets_other_thing_one_subform_customizations = model_thing_multiple_targets_subform_customizations[0]
        model_thing_multiple_targets_other_thing_two_subform_customizations = model_thing_multiple_targets_subform_customizations[1]
        model_thing_multiple_targets_other_thing_one_subform_category_customizations = sort_list_by_key(
            model_thing_multiple_targets_other_thing_one_subform_customizations["category_customizations"],
            "order"
        )
        model_thing_multiple_targets_other_thing_two_subform_category_customizations = sort_list_by_key(
            model_thing_multiple_targets_other_thing_two_subform_customizations["category_customizations"],
            "order"
        )
        model_thing_multiple_targets_other_thing_one_subform_property_customizations = sort_list_by_key(
            model_thing_multiple_targets_other_thing_one_subform_customizations["property_customizations"],
            "order"
        )
        model_thing_multiple_targets_other_thing_two_subform_property_customizations = sort_list_by_key(
            model_thing_multiple_targets_other_thing_two_subform_customizations["property_customizations"],
            "order"
        )

        model_thing_child_multiple_targets_subform_customizations = model_thing_child_subform_property_customizations[2].unsaved_subform_customizations
        model_thing_child_multiple_targets_other_thing_one_subform_customizations = model_thing_child_multiple_targets_subform_customizations[0]
        model_thing_child_multiple_targets_other_thing_two_subform_customizations = model_thing_child_multiple_targets_subform_customizations[1]
        model_thing_child_multiple_targets_other_thing_one_subform_category_customizations = sort_list_by_key(
            model_thing_child_multiple_targets_other_thing_one_subform_customizations["category_customizations"],
            "order"
        )
        model_thing_child_multiple_targets_other_thing_two_subform_category_customizations = sort_list_by_key(
            model_thing_child_multiple_targets_other_thing_two_subform_customizations["category_customizations"],
            "order"
        )
        model_thing_child_multiple_targets_other_thing_one_subform_property_customizations = sort_list_by_key(
            model_thing_child_multiple_targets_other_thing_one_subform_customizations["property_customizations"],
            "order"
        )
        model_thing_child_multiple_targets_other_thing_two_subform_property_customizations = sort_list_by_key(
            model_thing_child_multiple_targets_other_thing_two_subform_customizations["property_customizations"],
            "order"
        )

        # make sure _all_ category & property customizations are set
        # and that "model_thing_child_child_subform_customizations" points back to "model_thing_child_subform_customizations"
        self.assertEqual(len(model_thing_subform_category_customizations), 4)
        self.assertEqual(len(model_thing_child_subform_category_customizations), 4)
        self.assertEqual(len(model_thing_child_child_subform_category_customizations), 4)
        for i, category_proxy in enumerate(category_proxies):
            self.assertEqual(category_proxy, model_thing_subform_category_customizations[i].proxy)
            self.assertEqual(category_proxy, model_thing_child_subform_category_customizations[i].proxy)
            self.assertEqual(category_proxy, model_thing_child_child_subform_category_customizations[i].proxy)
            self.assertNotEqual(model_thing_subform_category_customizations[i], model_thing_child_subform_category_customizations[i])
            self.assertEqual(model_thing_child_subform_category_customizations[i], model_thing_child_child_subform_category_customizations[i])
        self.assertEqual(len(model_thing_subform_property_customizations), 3)
        self.assertEqual(len(model_thing_child_subform_property_customizations), 3)
        self.assertEqual(len(model_thing_child_child_subform_property_customizations), 3)
        for i, property_proxy in enumerate([recursive_thing_proxy_name_property_proxy, recursive_thing_proxy_child_property_proxy, recursive_thing_proxy_multiple_targets_property_proxy]):
            self.assertEqual(property_proxy, model_thing_subform_property_customizations[i].proxy)
            self.assertEqual(property_proxy, model_thing_child_subform_property_customizations[i].proxy)
            self.assertEqual(property_proxy, model_thing_child_child_subform_property_customizations[i].proxy)
            self.assertNotEqual(model_thing_subform_property_customizations[i], model_thing_child_child_subform_property_customizations[i])
            self.assertEqual(model_thing_child_child_subform_property_customizations[i], model_thing_child_subform_property_customizations[i])

        self.assertEqual(len(model_thing_multiple_targets_other_thing_one_subform_category_customizations), 4)
        self.assertEqual(len(model_thing_multiple_targets_other_thing_two_subform_category_customizations), 4)
        self.assertEqual(len(model_thing_child_multiple_targets_other_thing_one_subform_category_customizations), 4)
        self.assertEqual(len(model_thing_child_multiple_targets_other_thing_two_subform_category_customizations), 4)
        for i, category_proxy in enumerate(category_proxies):
            self.assertEqual(category_proxy, model_thing_multiple_targets_other_thing_one_subform_category_customizations[i].proxy)
            self.assertEqual(category_proxy, model_thing_multiple_targets_other_thing_two_subform_category_customizations[i].proxy)
            self.assertEqual(category_proxy, model_thing_child_multiple_targets_other_thing_one_subform_category_customizations[i].proxy)
            self.assertEqual(category_proxy, model_thing_child_multiple_targets_other_thing_two_subform_category_customizations[i].proxy)
            self.assertEqual(model_thing_multiple_targets_other_thing_one_subform_category_customizations[i], model_thing_child_multiple_targets_other_thing_one_subform_category_customizations[i])
            self.assertEqual(model_thing_multiple_targets_other_thing_two_subform_category_customizations[i], model_thing_child_multiple_targets_other_thing_two_subform_category_customizations[i])
        for i, property_proxy in enumerate([other_thing_one_proxy_name_property_proxy]):
            self.assertEqual(property_proxy, model_thing_multiple_targets_other_thing_one_subform_property_customizations[i].proxy)
            self.assertEqual(property_proxy, model_thing_child_multiple_targets_other_thing_one_subform_property_customizations[i].proxy)
            self.assertEqual(model_thing_multiple_targets_other_thing_one_subform_property_customizations, model_thing_child_multiple_targets_other_thing_one_subform_property_customizations)
        for i, property_proxy in enumerate([other_thing_two_proxy_name_property_proxy]):
            self.assertEqual(property_proxy, model_thing_multiple_targets_other_thing_two_subform_property_customizations[i].proxy)
            self.assertEqual(property_proxy, model_thing_child_multiple_targets_other_thing_two_subform_property_customizations[i].proxy)
            self.assertEqual(model_thing_multiple_targets_other_thing_two_subform_property_customizations, model_thing_child_multiple_targets_other_thing_two_subform_property_customizations)


    def test_get_new_customizations(self):

        model_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="model")
        recursive_thing_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="recursive_thing")

        test_customizations = get_new_customizations(
            project=self.test_project,
            ontology=self.test_ontology_schema,
            model_proxy=model_proxy,
        )

        self.assertEqual(len(test_customizations), 3)

        actual_model_customization_data = serialize_model_to_dict(
            test_customizations["model_customization"],
            exclude=["id", "guid", "created", "modified"]
        )
        test_model_customization_data = {
            'is_default': False,
            'name': u'',
            'model_title': u'Model',
            'project': self.test_project.pk,
            'synchronization': [],
            'proxy': model_proxy.pk,
            'model_show_all_categories': False,
            'model_description': u'',
            'ontology': self.test_ontology_schema.pk,
            'description': u'',
            'order': 1,
        }

        self.assertDictEqual(actual_model_customization_data, test_model_customization_data)

        actual_category_customizations_data = [
            serialize_model_to_dict(category_customization, exclude=["id", "guid", "created", "modified"])
            for category_customization in test_customizations["category_customizations"]
        ]
        test_category_customizations_data = sort_list_by_key(
            [
                {'name': u'', 'category_title': u'Category One', 'order': 1, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category One").pk, 'documentation': u'I am category one.'},
                {'name': u'', 'category_title': u'Category Two', 'order': 2, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category Two").pk, 'documentation': u'I am category two.'},
                {'name': u'', 'category_title': u'Category Three', 'order': 3, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category Three").pk, 'documentation': u'I am category three.'},
                {'name': u'', 'category_title': u'Uncategorized', 'order': 4, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Uncategorized").pk, 'documentation': u''},

            ],
            "order",
        )
        for actual_category_customization_data, test_category_customization_data in zip(actual_category_customizations_data, test_category_customizations_data):
            self.assertDictEqual(actual_category_customization_data, test_category_customization_data)

        actual_property_customizations_data = [
            serialize_model_to_dict(property_customization, exclude=["id", "guid", "created", "modified"])
            for property_customization in test_customizations["property_customizations"]
        ]
        test_property_customizations_data = sort_list_by_key(
            [
                {'name': u'', 'documentation': u'', 'is_hidden': False, 'is_nillable': True, 'relationship_target_customization_keys': None, 'relationship_target_model_customizations': [], 'field_type': u'ATOMIC', 'atomic_default': None, 'inline_help': False, 'property_title': u'Name', 'is_editable': True, 'proxy': model_proxy.property_proxies.get(name="name").pk, 'is_required': True, 'relationship_show_subform': False, 'order': 1, 'enumeration_open': False, 'atomic_type': u'DEFAULT', 'atomic_suggestions': ''},
                {'name': u'', 'documentation': u'A test enumeration.', 'is_hidden': False, 'is_nillable': True, 'relationship_target_customization_keys': None, 'relationship_target_model_customizations': [], 'field_type': u'ENUMERATION', 'atomic_default': None, 'inline_help': False, 'property_title': u'Enumeration', 'is_editable': True, 'proxy': model_proxy.property_proxies.get(name="enumeration").pk, 'is_required': False, 'relationship_show_subform': False, 'order': 2, 'enumeration_open': False, 'atomic_type': 'DEFAULT', 'atomic_suggestions': None},
                {'name': u'', 'documentation': u'A relationship property; there are lots of spaces in this documentation.', 'is_hidden': False, 'is_nillable': True, 'relationship_target_customization_keys': None, 'relationship_target_model_customizations': [], 'field_type': u'RELATIONSHIP', 'atomic_default': None, 'inline_help': False, 'property_title': u'Thing', 'is_editable': True, 'proxy': model_proxy.property_proxies.get(name="thing").pk, 'is_required': False, 'relationship_show_subform': True, 'order': 3, 'enumeration_open': False, 'atomic_type': 'DEFAULT', 'atomic_suggestions': None},
            ],
            "order",
        )
        for actual_property_customization_data, test_property_customization_data in zip(actual_property_customizations_data, test_property_customizations_data):
            self.assertDictEqual(actual_property_customization_data, test_property_customization_data, excluded_keys=["model_customization", "category"])

        # these tests really ought to be using a lambda fn that checks c.proxy.pk rather than c.property_title, but I'm lazy
        self.assertIn(
            find_in_sequence(lambda c: c.property_title == "Name", test_customizations["property_customizations"]).category,
            test_customizations["category_customizations"]
        )
        self.assertIn(
            find_in_sequence(lambda c: c.property_title == "Enumeration", test_customizations["property_customizations"]).category,
            test_customizations["category_customizations"]
        )
        self.assertIn(
            find_in_sequence(lambda c: c.property_title == "Thing", test_customizations["property_customizations"]).category,
            test_customizations["category_customizations"]
        )

        test_subform_customizations = find_in_sequence(lambda c: c.proxy.name == "thing", test_customizations["property_customizations"]).unsaved_subform_customizations

        self.assertEqual(len(test_subform_customizations), 1)
        test_subform_customizations = test_subform_customizations[0]
        self.assertEqual(len(test_subform_customizations), 3)

        actual_subform_model_customization_data = serialize_model_to_dict(
            test_subform_customizations["model_customization"],
            exclude=["id", "guid", "created", "modified"]
        )
        test_subform_model_customization_data = {
            'is_default': False,
            'name': u'',
            'model_title': u'Recursive Thing',
            'project': self.test_project.pk,
            'synchronization': [],
            'proxy': recursive_thing_proxy.pk,
            'model_show_all_categories': False,
            'model_description': u'',
            'ontology': self.test_ontology_schema.pk,
            'description': u'',
            'order': 2,

        }
        self.assertDictEqual(actual_subform_model_customization_data, test_subform_model_customization_data)

        actual_subform_category_customizations_data = [
            serialize_model_to_dict(category_customization, exclude=["id", "guid", "created", "modified"])
            for category_customization in test_subform_customizations["category_customizations"]
        ]
        test_subform_category_customizations_data = sort_list_by_key(
            [
                {'name': u'', 'category_title': u'Category One', 'order': 1, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category One").pk, 'documentation': u'I am category one.'},
                {'name': u'', 'category_title': u'Category Two', 'order': 2, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category Two").pk, 'documentation': u'I am category two.'},
                {'name': u'', 'category_title': u'Category Three', 'order': 3, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category Three").pk, 'documentation': u'I am category three.'},
                {'name': u'', 'category_title': u'Uncategorized', 'order': 4, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Uncategorized").pk, 'documentation': u''},
            ],
            "order",
        )
        for actual_subform_category_customization_data, test_subform_category_customization_data in zip(actual_subform_category_customizations_data, test_subform_category_customizations_data):
            self.assertDictEqual(actual_subform_category_customization_data, test_subform_category_customization_data)

        for subform_category_customization, category_customization in zip(test_subform_customizations["category_customizations"], test_customizations["category_customizations"]):
            # make sure that the subform categories use the same proxies but are in fact different instances
            self.assertEqual(subform_category_customization.proxy, category_customization.proxy)
            self.assertNotEqual(subform_category_customization.guid, category_customization.guid)

        actual_subform_property_customizations_data = [
            serialize_model_to_dict(property_customization, exclude=["id", "guid", "created", "modified"])
            for property_customization in test_subform_customizations["property_customizations"]
        ]
        test_subform_property_customizations_data = sort_list_by_key(
            [
                {'documentation': u'', 'relationship_target_customization_keys': None, 'relationship_target_model_customizations': [], 'is_hidden': False, 'field_type': u'ATOMIC', 'is_nillable': True, 'atomic_default': None, 'inline_help': False, 'property_title': u'Name', 'is_editable': True, 'proxy': recursive_thing_proxy.property_proxies.get(name="name").pk, 'name': u'', 'is_required': True, 'relationship_show_subform': False, 'order': 1, 'enumeration_open': False, 'atomic_type': u'DEFAULT', 'atomic_suggestions': ''},
                {'documentation': u'', 'relationship_target_customization_keys': None, 'relationship_target_model_customizations': [], 'is_hidden': False, 'field_type': u'RELATIONSHIP', 'is_nillable': True, 'atomic_default': None, 'inline_help': False, 'property_title': u'Child', 'is_editable': True, 'proxy': recursive_thing_proxy.property_proxies.get(name="child").pk, 'name': u'', 'is_required': False, 'relationship_show_subform': True, 'order': 2, 'enumeration_open': False, 'atomic_type': 'DEFAULT', 'atomic_suggestions': None},
            ],
            "order",
        )

        for actual_subform_property_customization_data, test_subform_property_customization_data in zip(actual_subform_property_customizations_data, test_subform_property_customizations_data):
            self.assertDictEqual(actual_subform_property_customization_data, test_subform_property_customization_data, excluded_keys=["model_customization", "category"])

        self.assertIn(
            find_in_sequence(lambda c: c.property_title == "Name", test_subform_customizations["property_customizations"]).category,
            test_subform_customizations["category_customizations"]
        )
        self.assertIn(
            find_in_sequence(lambda c: c.property_title == "Child", test_subform_customizations["property_customizations"]).category,
            test_subform_customizations["category_customizations"]
        )

        test_subform_subform_customizations = find_in_sequence(lambda c: c.proxy.name == "child", test_subform_customizations["property_customizations"]).unsaved_subform_customizations
        self.assertEqual(len(test_subform_subform_customizations), 1)
        test_subform_subform_customizations = test_subform_subform_customizations[0]
        self.assertEqual(len(test_subform_subform_customizations), 3)

        actual_subform_subform_model_customization_data = serialize_model_to_dict(
            test_subform_subform_customizations["model_customization"],
            exclude=["id", "guid", "created", "modified"]
        )
        test_subform_subform_model_customization_data = {
            'is_default': False, 'name': u'', 'model_title': u'Recursive Thing', 'project': self.test_project.pk, 'synchronization': [], 'proxy': recursive_thing_proxy.pk, 'model_show_all_categories': False, 'model_description': u'', 'ontology': self.test_ontology_schema.pk, 'description': u'', 'order': 2,
        }
        self.assertDictEqual(actual_subform_subform_model_customization_data, test_subform_subform_model_customization_data)
        self.assertNotEqual(test_subform_subform_customizations["model_customization"], test_subform_customizations["model_customization"])

        actual_subform_subform_category_customizations_data = [
            serialize_model_to_dict(category_customization, exclude=["id", "guid", "created", "modified"])
            for category_customization in test_subform_subform_customizations["category_customizations"]
        ]
        test_subform_subform_category_customizations_data = sort_list_by_key(
            [
                {'name': u'', 'category_title': u'Category One', 'order': 1, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category One").pk, 'documentation': u'I am category one.'},
                {'name': u'', 'category_title': u'Category Two', 'order': 2, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category Two").pk, 'documentation': u'I am category two.'},
                {'name': u'', 'category_title': u'Category Three', 'order': 3, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Category Three").pk, 'documentation': u'I am category three.'},
                {'name': u'', 'category_title': u'Uncategorized', 'order': 4, 'model_customization': None, 'proxy': self.test_ontology_schema.categorization.category_proxies.get(name="Uncategorized").pk, 'documentation': u''},
            ],
            "order",
        )
        for actual_subform_subform_category_customization_data, test_subform_subform_category_customization_data in zip(actual_subform_subform_category_customizations_data, test_subform_subform_category_customizations_data):
            self.assertDictEqual(actual_subform_subform_category_customization_data, test_subform_subform_category_customization_data, excluded_keys=["model_customization"])

        for subform_subform_category_customization, category_customization in zip(test_subform_subform_customizations["category_customizations"], test_customizations["category_customizations"]):
            self.assertEqual(subform_subform_category_customization.proxy, category_customization.proxy)
            self.assertNotEqual(subform_subform_category_customization, category_customization)

        actual_subform_subform_property_customizations_data = sort_list_by_key(
            [
                serialize_model_to_dict(property_customization, exclude=["id", "guid", "created", "modified"])
                for property_customization in test_subform_subform_customizations["property_customizations"]
            ],
            "order",
        )
        test_subform_subform_property_customizations_data = sort_list_by_key(
            [
                {'documentation': u'', 'is_hidden': False, 'field_type': u'ATOMIC', 'is_nillable': True, 'atomic_default': None, 'inline_help': False, 'property_title': u'Name', 'is_editable': True, 'proxy': recursive_thing_proxy.property_proxies.get(name="name").pk, 'relationship_target_customization_keys': None, 'relationship_target_model_customizations': [], 'name': u'', 'is_required': True, 'relationship_show_subform': False, 'order': 1, 'enumeration_open': False, 'atomic_type': u'DEFAULT', 'atomic_suggestions': ''},
                {'documentation': u'', 'is_hidden': False, 'field_type': u'RELATIONSHIP', 'is_nillable': True, 'atomic_default': None, 'inline_help': False, 'property_title': u'Child', 'is_editable': True, 'proxy': recursive_thing_proxy.property_proxies.get(name="child").pk, 'relationship_target_customization_keys': None, 'relationship_target_model_customizations': [], 'name': u'', 'is_required': False, 'relationship_show_subform': True, 'order': 2, 'enumeration_open': False, 'atomic_type': 'DEFAULT', 'atomic_suggestions': None},
                {'documentation': u'', 'is_hidden': False, 'field_type': u'RELATIONSHIP', 'is_nillable': True, 'atomic_default': None, 'inline_help': False, 'property_title': u'Multiple Targets', 'is_editable': True, 'proxy': recursive_thing_proxy.property_proxies.get(name="multiple_targets").pk, 'relationship_target_customization_keys': None, 'relationship_target_model_customizations': [], 'name': u'', 'is_required': False, 'relationship_show_subform': True, 'order': 3, 'enumeration_open': False, 'atomic_type': 'DEFAULT', 'atomic_suggestions': None},
            ],
            "order",
        )
        for actual_subform_subform_property_customization_data, test_subform_subform_property_customization_data in zip(actual_subform_subform_property_customizations_data, test_subform_subform_property_customizations_data):
            self.assertDictEqual(actual_subform_subform_property_customization_data, test_subform_subform_property_customization_data, excluded_keys=["model_customization", "category"])

        self.assertIn(
            find_in_sequence(lambda c: c.property_title == "Name", test_subform_subform_customizations["property_customizations"]).category,
            test_subform_subform_customizations["category_customizations"]
        )
        self.assertIn(
            find_in_sequence(lambda c: c.property_title == "Child", test_subform_subform_customizations["property_customizations"]).category,
            test_subform_subform_customizations["category_customizations"]
        )
        self.assertIn(
            find_in_sequence(lambda c: c.property_title == "Multiple Targets", test_subform_subform_customizations["property_customizations"]).category,
            test_subform_subform_customizations["category_customizations"]
        )

        test_subform_subform_subform_customizations = find_in_sequence(lambda c: c.proxy.name == "child", test_subform_subform_customizations["property_customizations"]).unsaved_subform_customizations
        self.assertEqual(len(test_subform_subform_subform_customizations), 1)
        test_subform_subform_subform_customizations = test_subform_subform_subform_customizations[0]
        self.assertEqual(len(test_subform_subform_subform_customizations), 3)

        # finally, at the lowest level of recursion, make sure the subforms point to the same customizations
        self.assertDictEqual(test_subform_subform_subform_customizations, test_subform_subform_customizations)

    def test_serialize_new_customizations(self):

        model_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="model")

        test_customizations = get_new_customizations(
            project=self.test_project,
            ontology=self.test_ontology_schema,
            model_proxy=model_proxy,
        )
        test_serialized_customizations = serialize_new_customizations(test_customizations)

        with open(get_test_file_path("serialization_customizations_default.json"), "r") as serialization_file:
            test_serialized_customizations_data = json.load(serialization_file)
        serialization_file.closed

        import ipdb; ipdb.set_trace()
        # not using built-in assertJSONEqual b/c I want to ignore keys
        self.assertJSONEqual(json.dumps(test_serialized_customizations), json.dumps(test_serialized_customizations_data))
        self.assertDictEqual(
            test_serialized_customizations,
            test_serialized_customizations_data,
            excluded_keys=["key", "category_key"]
        )

    def test_get_new_customizations2(self):

        # model proxies...
        model_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="model")
        recursive_thing_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="recursive_thing")
        other_thing_one_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="other_thing_one")
        other_thing_two_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="other_thing_two")

        # category proxies...
        category_proxies = self.test_ontology_schema.categorization.category_proxies.all()

        # property_proxies...
        model_proxy_property_proxies = model_proxy.property_proxies.all()
        recursive_thing_proxy_property_proxies = recursive_thing_proxy.property_proxies.all()
        other_thing_one_proxy_property_proxies = other_thing_one_proxy.property_proxies.all()
        other_thing_two_proxy_property_proxies = other_thing_two_proxy.property_proxies.all()

        test_created_customizations = {}
        test_model_customization = get_new_customizations(
            model_proxy.name,
            test_created_customizations,
            project=self.test_project,
            ontology=self.test_ontology_schema,
            model_proxy=model_proxy,
        )

        self.assertEqual(len(test_created_customizations), 36)

        model_customization = test_model_customization
        recursive_thing_customization = test_model_customization.property_customizations.all()[2].relationship_target_model_customizations(manager="allow_unsaved_relationship_target_model_customizations_manager").all()[0]
        recursive_thing_customization_2 = recursive_thing_customization.property_customizations.all()[1].relationship_target_model_customizations(manager="allow_unsaved_relationship_target_model_customizations_manager").all()[0]
        recursive_thing_customization_3 = recursive_thing_customization_2.property_customizations.all()[1].relationship_target_model_customizations(manager="allow_unsaved_relationship_target_model_customizations_manager").all()[0]
        other_thing_one_customization = recursive_thing_customization.property_customizations.all()[2].relationship_target_model_customizations(manager="allow_unsaved_relationship_target_model_customizations_manager").all()[0]
        other_thing_two_customization = recursive_thing_customization.property_customizations.all()[2].relationship_target_model_customizations(manager="allow_unsaved_relationship_target_model_customizations_manager").all()[1]

        self.assertEqual(model_customization.proxy, model_customization.proxy)
        self.assertEqual(recursive_thing_customization.proxy, recursive_thing_proxy)
        self.assertEqual(recursive_thing_customization_2.proxy, recursive_thing_proxy)
        self.assertEqual(other_thing_one_customization.proxy, other_thing_one_proxy)
        self.assertEqual(other_thing_two_customization.proxy, other_thing_two_proxy)

        self.assertNotEqual(recursive_thing_customization, recursive_thing_customization_2)
        self.assertEqual(recursive_thing_customization_2, recursive_thing_customization_3)

        for i, category_proxy in enumerate(category_proxies):
            self.assertEqual(category_proxy, model_customization.category_customizations.all()[i].proxy)
            self.assertEqual(category_proxy, recursive_thing_customization.category_customizations.all()[i].proxy)
            self.assertEqual(category_proxy, recursive_thing_customization_2.category_customizations.all()[i].proxy)
            self.assertEqual(category_proxy, other_thing_one_customization.category_customizations.all()[i].proxy)
            self.assertEqual(category_proxy, other_thing_two_customization.category_customizations.all()[i].proxy)
            self.assertNotEqual(model_customization.category_customizations.all()[i], recursive_thing_customization.category_customizations.all()[i])
            self.assertNotEqual(recursive_thing_customization.category_customizations.all()[i], recursive_thing_customization_2.category_customizations.all()[i])
            self.assertNotEqual(recursive_thing_customization_2.category_customizations.all()[i], other_thing_one_customization.category_customizations.all()[i])
            self.assertNotEqual(other_thing_one_customization.category_customizations.all()[i], other_thing_two_customization.category_customizations.all()[i])
            self.assertEqual(recursive_thing_customization_2.category_customizations.all()[i], recursive_thing_customization_3.category_customizations.all()[i])

        for i, property_proxy in enumerate(model_proxy_property_proxies):
            self.assertEqual(property_proxy, model_customization.property_customizations.all()[i].proxy)

        for i, property_proxy in enumerate(recursive_thing_proxy_property_proxies):
            self.assertEqual(property_proxy, recursive_thing_customization.property_customizations.all()[i].proxy)
            self.assertEqual(property_proxy, recursive_thing_customization_2.property_customizations.all()[i].proxy)
            self.assertEqual(property_proxy, recursive_thing_customization_3.property_customizations.all()[i].proxy)
            self.assertNotEqual(recursive_thing_customization.property_customizations.all()[i], recursive_thing_customization_2.property_customizations.all()[i])
            self.assertEqual(recursive_thing_customization_2.property_customizations.all()[i], recursive_thing_customization_3.property_customizations.all()[i])

        for i, property_proxy in enumerate(other_thing_one_proxy_property_proxies):
            self.assertEqual(property_proxy, other_thing_one_customization.property_customizations.all()[i].proxy)

        for i, property_proxy in enumerate(other_thing_two_proxy_property_proxies):
            self.assertEqual(property_proxy, other_thing_two_customization.property_customizations.all()[i].proxy)
