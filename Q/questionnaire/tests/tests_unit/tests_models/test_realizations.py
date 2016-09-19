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

from Q.questionnaire.tests.test_base import TestQBase, get_test_file_path, create_project, create_ontology, remove_ontology, create_categorization, remove_categorization, create_customization, create_realization
from Q.questionnaire.models.models_proxies import QModelProxy, QCategoryProxy, QPropertyProxy
from Q.questionnaire.models.models_realizations import *

class TestQRealization(TestQBase):

    def setUp(self):

        # don't do the base setUp (it would interfere w/ the ids of the ontology created below)
        # super(TestQOntolgoy, self).setUp()

        self.test_user = User.objects.create_user(
            username="test_user",
            email="allyn.treshansky@noaa.gov",
            password="password",
        )
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="allyn.treshansky@noaa.gov",
            password="password",
        )

        self.test_project = create_project(
            name="test_project",
            title="Test Project",
            email="allyn.treshansky@noaa.gov",
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

    def test_get_new_realizations(self):

        model_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="model")

        test_realization = get_new_realizations(
            project=self.test_project,
            ontology=self.test_ontology_schema,
            model_proxy=model_proxy,
            key=model_proxy.name,
        )

        self.assertEqual(test_realization.proxy, model_proxy)

    def test_get_default_customization(self):

        model_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="model")

        create_customization(
            project=self.test_project,
            ontology=self.test_ontology_schema,
            model_proxy=model_proxy,
            owner=self.superuser,  # using superuser so I don't have to deal w/ project membership stuff
        )

        test_model_realization = get_new_realizations(
            project=self.test_project,
            ontology=self.test_ontology_schema,
            model_proxy=model_proxy,
            key=model_proxy.name,
        )
        default_model_customization = test_model_realization.get_default_customization()
        self.assertEqual(default_model_customization.proxy, test_model_realization.proxy)

        test_property_realization = test_model_realization.properties(manager="allow_unsaved_properties_manager").all()[0]
        default_property_customization = test_property_realization.get_default_customization()
        self.assertEqual(default_property_customization.proxy, test_property_realization.proxy)

        self.assertEqual(default_model_customization.name, default_property_customization.name)

    # def test_get_value(self):
    #
    #     model_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="model")
    #
    #     test_model_realization = get_new_realizations(
    #         project=self.test_project,
    #         ontology=self.test_ontology_schema,
    #         model_proxy=model_proxy,
    #         key=model_proxy.name,
    #     )
    #     test_property_realizations = test_model_realization.properties(manager="allow_unsaved_properties_manager").all()
    #     test_atomic_property = test_property_realizations[0]
    #     test_enumeration_property = test_property_realizations[1]
    #     test_relationship_property = test_property_realizations[2]
    #
    #     import ipdb; ipdb.set_trace()
    #
    #     self.assertEqual(test_atomic_property.get_value(), None)
    #     test_atomic_property.atomic_value = "test_value"
    #     self.assertEqual(test_atomic_property.get_value(), "test_value")
    #
    #     test_enumeration_property.get_value()
    #
    #     pass


    def test_update_completion(self):

        model_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="model")

        # temporarily changing the proxy (by making everything required) to better test all property types...
        property_proxies = model_proxy.property_proxies.all()
        for property_proxy in property_proxies:
            property_proxy.cardinality = "1|*"
            property_proxy.save()

        test_model_realization = create_realization(
            project=self.test_project,
            ontology=self.test_ontology_schema,
            model_proxy=model_proxy,
            owner=self.superuser,  # using superuser so I don't have to deal w/ project membership stuff
        )

        test_property_realizations = test_model_realization.properties(manager="allow_unsaved_properties_manager").all()
        test_atomic_property = test_property_realizations[0]
        test_enumeration_property = test_property_realizations[1]
        test_relationship_property = test_property_realizations[2]

        # a newly-created realization should be incomplete...
        update_completion(test_model_realization)
        self.assertFalse(test_model_realization.is_complete)

        test_atomic_property.is_nil = True
        test_atomic_property.save()
        test_enumeration_property.is_nil = True
        test_enumeration_property.save()
        test_relationship_property.is_nil = True
        test_relationship_property.save()
        test_model_realization.properties.update()  # force qs to be re-evaluated in light of the above changes

        # a realization w/ all properties set to nil should be complete...
        update_completion(test_model_realization)
        self.assertTrue(test_model_realization.is_complete)

        test_atomic_property.is_nil = False
        test_atomic_property.atomic_value = "test"
        test_atomic_property.save()
        test_enumeration_property.is_nil = False
        test_enumeration_property.enumeration_value = ['test']
        test_enumeration_property.save()
        test_relationship_property.is_nil = False
        # TODO: THIS BIT OF CODE OUGHT TO BE ISOLATED IN A FN (SEE "views_services_realization_add.py")
        target_test_model_realization = create_realization(
            project=self.test_project,
            ontology=self.test_ontology_schema,
            model_proxy=QModelProxy.objects.get(pk=test_relationship_property.get_possible_relationship_targets()[0]['pk']),
            owner=self.superuser,
        )
        test_relationship_property.relationship_values(manager="allow_unsaved_relationship_values_manager").add_potentially_unsaved(
            target_test_model_realization)
        with allow_unsaved_fk(QModel, ["relationship_property"]):
            target_test_model_realization.relationship_property = test_relationship_property
        target_test_atomic_property = target_test_model_realization.properties.all()[0]
        target_test_atomic_property.atomic_value = "test"
        target_test_atomic_property.save()
        target_test_model_realization.properties.update()
        test_relationship_property.save()
        test_model_realization.properties.update()  # force qs to be re-evaluated in light of the above changes

        # a realization w/ all complete properties should be complete...
        update_completion(test_model_realization)
        self.assertTrue(test_model_realization.is_complete)

        pass

    def test_recurse_through_realizations(self):

        model_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="model")

        test_model_realization = get_new_realizations(
            project=self.test_project,
            ontology=self.test_ontology_schema,
            model_proxy=model_proxy,
            key=model_proxy.name,
        )

        def _test_fn1(obj):
            # this fn changes obj but has no return value
            obj.test_field = "I am a test field"

        def _test_fn2(obj):
            # this fn changes obj and has a return value
            obj.test_field = "I am still a test field"
            return True

        import ipdb; ipdb.set_trace()
        output1 = recurse_through_realizations(_test_fn1, test_model_realization, [RealizationTypes.MODEL, RealizationTypes.CATEGORY, RealizationTypes.PROPERTY])
        self.assertEqual(test_model_realization.test_field, "I am a test field")
        output2 = recurse_through_realizations(_test_fn2, test_model_realization, [RealizationTypes.MODEL, RealizationTypes.CATEGORY, RealizationTypes.PROPERTY])
        self.assertEqual(test_model_realization.test_field, "I am still a test field")

        # I know this is fairly irrelevant code, but it's a pretty cool (and fast!) way of checking if a list contains all the same elements
        self.assertTrue(output1.count(output1[0]) == len(output1))
        self.assertTrue(output2.count(output2[0]) == len(output2))

        self.assertEqual(output1[0], None)
        self.assertEqual(output2[0], True)

        self.assertEqual(len(output1), 4)
        self.assertEqual(len(output2), 4)
