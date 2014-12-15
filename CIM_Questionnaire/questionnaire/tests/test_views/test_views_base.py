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
.. module:: test_views_base

Tests the views fns common to all views
"""

from CIM_Questionnaire.questionnaire.utils import FuzzyInt
from CIM_Questionnaire.questionnaire.views.views_base import validate_view_arguments, get_cached_existing_customization_set, get_cached_proxy_set, get_cached_new_realization_set, get_cached_existing_realization_set
from CIM_Questionnaire.questionnaire.tests.test_base import TestQuestionnaireBase


class Test(TestQuestionnaireBase):

    def test_validate_view_arguments(self):

        kwargs = {
            "project_name": self.downscaling_project.name,
            "model_name": self.model_component_proxy.name.lower(),
            "version_key": self.cim_1_8_1_version.get_key(),
        }

        (validity, project, version, model_proxy, msg) = validate_view_arguments(**kwargs)
        self.assertEqual(validity, True)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"project_name": "invalid"})
        (validity, project, version, model_proxy, msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity, False)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"model_name": "invalid"})
        (validity, project, version, model_proxy, msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity, False)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"version_key": "invalid"})
        (validity, project, version, model_proxy, msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity, False)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"model_name": "responsibleparty"})    # valid classname, but not a document
        (validity, project, version, model_proxy, msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity, False)

##############################
# test the caching mechanism #
##############################

    def test_get_cached_existing_customization_set(self):

        query_limit_create_from_models = FuzzyInt(0, 140)
        query_limit_load_from_cache = FuzzyInt(0, 1)

        test_session_id_1 = "test"          # dummy session_id; should result in creating from models
        test_session_id_2 = "test"          # same dummy session_id; should result in loading from cache
        test_session_id_3 = "another_test"  # different session_id; should result in creating from models

        with self.assertNumQueries(query_limit_create_from_models):
            customization_set_1 = get_cached_existing_customization_set(test_session_id_1, self.downscaling_model_component_customizer_set["model_customizer"], self.downscaling_model_comopnent_vocabularies)

        with self.assertNumQueries(query_limit_load_from_cache):
            customization_set_2 = get_cached_existing_customization_set(test_session_id_2, self.downscaling_model_component_customizer_set["model_customizer"], self.downscaling_model_comopnent_vocabularies)

        with self.assertNumQueries(query_limit_create_from_models):
            customization_set_3 = get_cached_existing_customization_set(test_session_id_3, self.downscaling_model_component_customizer_set["model_customizer"], self.downscaling_model_comopnent_vocabularies)

        self.assertIsNotNone(customization_set_1)
        self.assertIsNotNone(customization_set_2)
        self.assertIsNotNone(customization_set_3)

        self.assertEqual(customization_set_1["model_customizer"], customization_set_2["model_customizer"])
        self.assertEqual(customization_set_2["model_customizer"], customization_set_3["model_customizer"])
        self.assertQuerysetEqual(customization_set_1["standard_property_customizers"], customization_set_2["standard_property_customizers"])
        self.assertQuerysetEqual(customization_set_2["standard_property_customizers"], customization_set_3["standard_property_customizers"])
        self.assertQuerysetEqual(customization_set_1["standard_category_customizers"], customization_set_2["standard_category_customizers"])
        self.assertQuerysetEqual(customization_set_2["standard_category_customizers"], customization_set_3["standard_category_customizers"])
        self.assertItemsEqual(customization_set_1["scientific_property_customizers"].keys(), customization_set_2["scientific_property_customizers"].keys())
        self.assertItemsEqual(customization_set_2["scientific_property_customizers"].keys(), customization_set_3["scientific_property_customizers"].keys())
        self.assertItemsEqual(customization_set_1["scientific_category_customizers"].keys(), customization_set_2["scientific_category_customizers"].keys())
        self.assertItemsEqual(customization_set_2["scientific_category_customizers"].keys(), customization_set_3["scientific_category_customizers"].keys())
        for k, v in customization_set_1["scientific_property_customizers"].iteritems():
            self.assertQuerysetEqual(v, customization_set_2["scientific_property_customizers"][k])
            self.assertQuerysetEqual(v, customization_set_3["scientific_property_customizers"][k])
        for k, v in customization_set_1["scientific_category_customizers"].iteritems():
            self.assertQuerysetEqual(v, customization_set_2["scientific_category_customizers"][k])
            self.assertQuerysetEqual(v, customization_set_3["scientific_category_customizers"][k])

    def test_get_cached_proxy_set(self):

        # get_proxy_set doesn't touch the db!
        query_limit_create_from_models = FuzzyInt(0, 1)
        query_limit_load_from_cache = FuzzyInt(0, 1)

        test_session_id_1 = "test"          # dummy session_id; should result in creating from models
        test_session_id_2 = "test"          # same dummy session_id; should result in loading from cache
        test_session_id_3 = "another_test"  # different session_id; should result in creating from models

        with self.assertNumQueries(query_limit_create_from_models):
            proxy_set_1 = get_cached_proxy_set(test_session_id_1, self.downscaling_model_component_customizer_set)

        with self.assertNumQueries(query_limit_load_from_cache):
            proxy_set_2 = get_cached_proxy_set(test_session_id_2, self.downscaling_model_component_customizer_set)

        with self.assertNumQueries(query_limit_create_from_models):
            proxy_set_3 = get_cached_proxy_set(test_session_id_3, self.downscaling_model_component_customizer_set)

        self.assertIsNotNone(proxy_set_1)
        self.assertIsNotNone(proxy_set_2)
        self.assertIsNotNone(proxy_set_3)

        self.assertEqual(proxy_set_1["model_proxy"], proxy_set_2["model_proxy"])
        self.assertEqual(proxy_set_2["model_proxy"], proxy_set_3["model_proxy"])
        self.assertListEqual(proxy_set_1["standard_property_proxies"], proxy_set_2["standard_property_proxies"])
        self.assertListEqual(proxy_set_2["standard_property_proxies"], proxy_set_3["standard_property_proxies"])
        self.assertDictEqual(proxy_set_1["scientific_property_proxies"], proxy_set_2["scientific_property_proxies"])
        self.assertDictEqual(proxy_set_2["scientific_property_proxies"], proxy_set_3["scientific_property_proxies"])

    def test_get_cached_new_realization_set(self):

        query_limit_create_from_models = FuzzyInt(0, 185)
        query_limit_load_from_cache = FuzzyInt(0, 1)

        test_session_id_1 = "test"          # dummy session_id; should result in creating from models
        test_session_id_2 = "test"          # same dummy session_id; should result in loading from cache
        test_session_id_3 = "another_test"  # different session_id; should result in creating from models

        with self.assertNumQueries(query_limit_create_from_models):
            realization_set_1 = get_cached_new_realization_set(test_session_id_1, self.downscaling_model_component_customizer_set, self.downscaling_model_component_proxy_set, self.downscaling_model_comopnent_vocabularies)

        with self.assertNumQueries(query_limit_load_from_cache):
            realization_set_2 = get_cached_new_realization_set(test_session_id_2, self.downscaling_model_component_customizer_set, self.downscaling_model_component_proxy_set, self.downscaling_model_comopnent_vocabularies)

        with self.assertNumQueries(query_limit_create_from_models):
            realization_set_3 = get_cached_new_realization_set(test_session_id_3, self.downscaling_model_component_customizer_set, self.downscaling_model_component_proxy_set, self.downscaling_model_comopnent_vocabularies)

        self.assertIsNotNone(realization_set_1)
        self.assertIsNotNone(realization_set_2)
        self.assertIsNotNone(realization_set_3)

        self.assertEqual(realization_set_1["models"], realization_set_2["models"])
        self.assertEqual(realization_set_2["models"], realization_set_3["models"])
        self.assertDictEqual(realization_set_1["standard_properties"], realization_set_2["standard_properties"])
        self.assertDictEqual(realization_set_2["standard_properties"], realization_set_3["standard_properties"])
        self.assertDictEqual(realization_set_1["scientific_properties"], realization_set_2["scientific_properties"])
        self.assertDictEqual(realization_set_2["scientific_properties"], realization_set_3["scientific_properties"])

    def test_get_cached_existing_realization_set(self):

        query_limit_create_from_models = FuzzyInt(0, 54)
        query_limit_load_from_cache = FuzzyInt(0, 1)

        test_session_id_1 = "test"          # dummy session_id; should result in creating from models
        test_session_id_2 = "test"          # same dummy session_id; should result in loading from cache
        test_session_id_3 = "another_test"  # different session_id; should result in creating from models

        realizations = self.downscaling_model_component_realization_set["models"]

        with self.assertNumQueries(query_limit_create_from_models):
            realization_set_1 = get_cached_existing_realization_set(test_session_id_1, realizations, self.downscaling_model_component_customizer_set, self.downscaling_model_component_proxy_set, self.downscaling_model_comopnent_vocabularies)

        with self.assertNumQueries(query_limit_load_from_cache):
            realization_set_2 = get_cached_existing_realization_set(test_session_id_2, realizations, self.downscaling_model_component_customizer_set, self.downscaling_model_component_proxy_set, self.downscaling_model_comopnent_vocabularies)

        with self.assertNumQueries(query_limit_create_from_models):
            realization_set_3 = get_cached_existing_realization_set(test_session_id_3, realizations, self.downscaling_model_component_customizer_set, self.downscaling_model_component_proxy_set, self.downscaling_model_comopnent_vocabularies)

        self.assertIsNotNone(realization_set_1)
        self.assertIsNotNone(realization_set_2)
        self.assertIsNotNone(realization_set_3)

        self.assertEqual(realization_set_1["models"], realization_set_2["models"])
        self.assertEqual(realization_set_2["models"], realization_set_3["models"])
        self.assertDictEqual(realization_set_1["standard_properties"], realization_set_2["standard_properties"])
        self.assertDictEqual(realization_set_2["standard_properties"], realization_set_3["standard_properties"])
        self.assertDictEqual(realization_set_1["scientific_properties"], realization_set_2["scientific_properties"])
        self.assertDictEqual(realization_set_2["scientific_properties"], realization_set_3["scientific_properties"])
