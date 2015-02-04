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
.. module:: test_metadata_customizer

Tests the MetadataCustomizer models
"""

from CIM_Questionnaire.questionnaire.tests.test_base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.models.metadata_customizer import *
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy


class TestMetadataCustomizer(TestQuestionnaireBase):

    def test_get_existing_customizer_set(self):

        test_customizer = self.downscaling_model_component_customizer_set_with_subforms["model_customizer"]
        test_vocabularies = self.downscaling_model_component_vocabularies

        (model_customizer, standard_category_customizers, standard_property_customizers, scientific_category_customizers, scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)

        # make sure the model_customizer is as expected
        self.assertEqual(model_customizer, test_customizer)

        # make sure the standard category customizers are as expected
        self.assertQuerysetEqual(standard_category_customizers, test_customizer.standard_property_category_customizers.all())

        # make sure the standard property customizers are as expected
        self.assertQuerysetEqual(standard_property_customizers, test_customizer.standard_property_customizers.all())

        for vocabulary in test_vocabularies:
            vocabulary_key = vocabulary.get_key()
            for component_proxy in vocabulary.component_proxies.all():
                component_key = component_proxy.get_key()

                # make sure the scientific category customizers are as expected
                test_scientific_category_customizer_qs_from_model = test_customizer.scientific_property_category_customizers.filter(vocabulary_key=vocabulary_key, component_key=component_key)
                scientific_category_customizer_qs = scientific_category_customizers[vocabulary_key][component_key]
                self.assertQuerysetEqual(test_scientific_category_customizer_qs_from_model, scientific_category_customizer_qs)

                # make sure the scientific property customizers are as expected
                test_scientific_property_customizer_qs_from_model = test_customizer.scientific_property_customizers.filter(vocabulary_key=vocabulary_key, component_key=component_key)
                scientific_property_customizer_qs = scientific_property_customizers[vocabulary_key][component_key]
                self.assertQuerysetEqual(test_scientific_property_customizer_qs_from_model,scientific_property_customizer_qs)

    def test_rename_customizer_set(self):

        test_customizer = self.downscaling_model_component_customizer_set_with_subforms["model_customizer"]

        name_1 = "subforms"
        name_2 = "new_name"

        self.assertEqual(test_customizer.name, name_1)
        for standard_property_customizer in test_customizer.standard_property_customizers.all():
            subform_customizer = standard_property_customizer.subform_customizer
            if subform_customizer:
                self.assertEqual(subform_customizer.name, name_1)

        test_customizer.rename(name_2)

        self.assertEqual(test_customizer.name, name_2)
        for standard_property_customizer in test_customizer.standard_property_customizers.all():
            subform_customizer = standard_property_customizer.subform_customizer
            if subform_customizer:
                self.assertEqual(subform_customizer.name, name_2)





