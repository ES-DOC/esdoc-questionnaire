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
.. module:: test_forms_base

Tests the base classes in forms_base
"""

from CIM_Questionnaire.questionnaire.forms.forms_base import *
from CIM_Questionnaire.questionnaire.forms.forms_edit import create_new_edit_forms_from_models
from CIM_Questionnaire.questionnaire.views.views_base import get_cached_new_realization_set

from CIM_Questionnaire.questionnaire.tests.test_base import TestQuestionnaireBase


class Test(TestQuestionnaireBase):

    def setUp(self):
        super(Test, self).setUp()

        # going to use Editing Forms for my tests...
        session_id = "test"
        new_realization_set = get_cached_new_realization_set(session_id, self.downscaling_model_component_customizer_set, self.downscaling_model_component_proxy_set, self.downscaling_model_component_vocabularies)

        models = new_realization_set["models"]
        model_customizer = self.downscaling_model_component_customizer_set["model_customizer"]
        standard_properties = new_realization_set["standard_properties"]
        standard_property_customizers = self.downscaling_model_component_customizer_set["standard_property_customizers"]
        scientific_properties = new_realization_set["scientific_properties"]
        scientific_property_customizers = self.downscaling_model_component_customizer_set["scientific_property_customizers"]

        (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_new_edit_forms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers)

        self.model_formset = model_formset
        self.standard_properties_formsets = standard_properties_formsets
        self.scientific_properties_formsets = scientific_properties_formsets

    def tearDown(self):
        super(Test, self).tearDown()

    def test_form_loading(self):

        # test MetadataForm.load()
        loaded_prefixes = []

        for model_form in self.model_formset.forms:
            self.assertFalse(model_form.is_loaded())

        for i, model_form in enumerate(self.model_formset.forms):
            if not i % 2:
                model_form.load()
                loaded_prefixes.append(model_form.prefix)

        # test MetadataForm.is_loaded()
        for i, model_form in enumerate(self.model_formset.forms):
            if not i % 2:
                self.assertTrue(model_form.is_loaded())
            else:
                self.assertFalse(model_form.is_loaded())

        # test MetadataForm.get_loaded_forms()
        loaded_forms = self.model_formset.get_loaded_forms()
        self.assertListEqual([form.prefix for form in loaded_forms], loaded_prefixes)

