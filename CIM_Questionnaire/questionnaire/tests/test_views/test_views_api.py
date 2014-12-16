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
.. module:: test_views_api

Tests the RESTful API views (for loading form sections)
"""

from os.path import split
from django.core.urlresolvers import reverse
from CIM_Questionnaire.questionnaire.tests.test_base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.views.views_api import validate_section_key, validate_edit_view_arguments, get_section_template_path
from CIM_Questionnaire.questionnaire.views.views_api import STANDARD_PROPERTY_TYPE, SCIENTIFIC_PROPERTY_TYPE
from CIM_Questionnaire.questionnaire.utils import find_in_sequence, add_parameters_to_url, FuzzyInt
from CIM_Questionnaire.questionnaire.utils import DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY


class Test(TestQuestionnaireBase):

    def setUp(self):

        super(Test, self).setUp()

    # section_key format is:
    # [ <version_key> |
    #   <model_key> |
    #   <vocabulary_key> |
    #   <component_key> |
    #   'standard_properties" or "scientific_properties"
    #   <category_key> |
    #   <property_key> |
    #
    # ]

        test_version = self.cim_1_8_1_version
        test_model = self.downscaling_model_component_proxy_set["model_proxy"]
        test_vocabulary = self.atmosphere_vocabulary
        test_component = test_vocabulary.component_proxies.get(name__iexact="atmoskeyproperties")
        test_standard_category = self.cim_1_8_1_categorization.categories.get(key="document-properties")
        test_scientific_category = test_component.categories.get(key="general-attributes")
        test_standard_property = find_in_sequence(lambda p: p.name.lower() == "documentauthor", self.downscaling_model_component_proxy_set["standard_property_proxies"])
        test_scientific_property = test_scientific_category.scientific_properties.get(name__iexact="modelfamily")

        self.assertIsNotNone(test_version)
        self.assertIsNotNone(test_model)
        self.assertIsNotNone(test_vocabulary)
        self.assertIsNotNone(test_component)
        self.assertIsNotNone(test_standard_category)
        self.assertIsNotNone(test_scientific_category)
        self.assertIsNotNone(test_standard_property)
        self.assertIsNotNone(test_scientific_property)
        # TODO: CATEGORY REVERSE RELATIONSHIPS SHOULD BE NAMED THE SAME WAY (ie: either "properties" or "scientific/standard_properties")
        self.assertTrue(test_standard_property in test_standard_category.properties.all())
        self.assertTrue(test_scientific_property in test_scientific_category.scientific_properties.all())

        self.test_version_key = test_version.get_key()
        self.invalid_version_key = "invalid_version"

        self.test_model_key = test_model.name.lower()
        self.invalid_model_key = "invalid_model"

        self.default_vocabulary_key = DEFAULT_VOCABULARY_KEY
        self.test_vocabulary_key = test_vocabulary.get_key()
        self.invalid_vocabulary_key = "invalid_vocabulary"

        self.default_component_key = DEFAULT_COMPONENT_KEY
        self.test_component_key = test_component.get_key()
        self.invalid_component_key = "invalid_component"

        self.test_standard_category_key = test_standard_category.key
        self.invalid_standard_category_key = "invalid_standard_category"

        self.test_scientific_category_key = test_scientific_category.key
        self.invalid_scientific_category_key = "invalid_scientific_category"

        self.test_standard_property_key = test_standard_property.name.lower()
        self.invalid_standard_property_key = "invalid_standard_property"

        self.test_scientific_property_key = test_scientific_property.name.lower()
        self.invalid_scientificproperty_key = "invalid_scientific_property"

    def test_validate_section_key(self):

        section_key = "|".join([
            self.test_version_key,
            self.test_model_key,
        ])

        # first try w/ an incomplete key to make sure it fails...
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg) = \
            validate_section_key(section_key)
        self.assertFalse(validity)

        # now complete the key
        section_key += u"|%s|%s" % (self.default_vocabulary_key, self.default_component_key)

        # try for the least-specific section...
        # (entire default component)
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg) = \
            validate_section_key(section_key)
        self.assertTrue(validity)

        # try again for an actual component in the CV...
        section_key = section_key.replace(self.default_vocabulary_key, self.test_vocabulary_key)
        section_key = section_key.replace(self.default_component_key, self.test_component_key)
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg) = \
            validate_section_key(section_key)
        self.assertTrue(validity)

        # now try w/ different property_types...
        standard_section_key = section_key + "|standard_properties"
        scientific_section_key = section_key + "|scientific_properties"
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg) = \
            validate_section_key(standard_section_key)
        self.assertTrue(validity)
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg) = \
            validate_section_key(scientific_section_key)
        self.assertTrue(validity)

        # now try w/ (standard & scientific) categories...
        standard_section_key = standard_section_key + "|" + self.test_standard_category_key
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg) = \
            validate_section_key(standard_section_key)
        self.assertTrue(validity)
        scientific_section_key = scientific_section_key + "|" + self.test_scientific_category_key
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg) = \
            validate_section_key(scientific_section_key)
        self.assertTrue(validity)

        # now try w/ (standard & scientific) properties...
        standard_section_key = standard_section_key + "|" + self.test_standard_property_key
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg) = \
            validate_section_key(standard_section_key)
        self.assertTrue(validity)
        scientific_section_key = scientific_section_key + "|" + self.test_scientific_property_key
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg) = \
            validate_section_key(scientific_section_key)
        self.assertTrue(validity)

        # try again w/ the same standard property but for the default (root) component this time...
        default_standard_section_key = standard_section_key.replace(self.test_vocabulary_key, self.default_vocabulary_key)
        default_standard_section_key = default_standard_section_key.replace(self.test_component_key, self.default_component_key)
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg) = \
            validate_section_key(default_standard_section_key)
        self.assertTrue(validity)

        # now start introducing invalid keys...
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg) = \
            validate_section_key(standard_section_key.replace(self.test_version_key, self.invalid_version_key))
        self.assertFalse(validity)

    def test_validate_edit_view_arguments(self):

        section_key = "|".join([
            self.test_version_key,
            self.test_model_key,
            self.test_vocabulary_key,
            self.test_component_key,
        ])

        valid_project_name = self.downscaling_project.name
        invalid_project_name = "invalid"

        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, model_customizer, vocabularies, msg) = \
            validate_edit_view_arguments(invalid_project_name, section_key)
        self.assertFalse(validity)

        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, model_customizer, vocabularies, msg) = \
            validate_edit_view_arguments(valid_project_name, section_key)
        self.assertTrue(validity)
        self.assertEqual(model_customizer, self.downscaling_model_component_customizer_set["model_customizer"])

    def test_get_section_template_path(self):

        # (I can get away w/ just using booleans here)
        category_proxy = None
        property_proxy = None

        # get an entire component...
        section_template_path = get_section_template_path(property_proxy, None, category_proxy)
        section_template_file = split(section_template_path)[-1]
        self.assertEqual(section_template_file, "_section_component.html")

        # get all standard properties...
        property_type = STANDARD_PROPERTY_TYPE
        section_template_path = get_section_template_path(property_proxy, property_type, category_proxy)
        section_template_file = split(section_template_path)[-1]
        self.assertEqual(section_template_file, "_section_all_standard_categories.html")

        # get an entire standard category...
        category_proxy = True
        section_template_path = get_section_template_path(property_proxy, property_type, category_proxy)
        section_template_file = split(section_template_path)[-1]
        self.assertEqual(section_template_file, "_section_standard_category.html")

        # get a single standard property...
        property_proxy = True
        section_template_path = get_section_template_path(property_proxy, property_type, category_proxy)
        section_template_file = split(section_template_path)[-1]
        self.assertEqual(section_template_file, "_section_standard_property.html")

        # reset arguments...
        category_proxy = None
        property_proxy = None

        # get all scientific properties...
        property_type = SCIENTIFIC_PROPERTY_TYPE
        section_template_path = get_section_template_path(property_proxy, property_type, category_proxy)
        section_template_file = split(section_template_path)[-1]
        self.assertEqual(section_template_file, "_section_all_scientific_categories.html")

        # get an entire standard category...
        category_proxy = True
        section_template_path = get_section_template_path(property_proxy, property_type, category_proxy)
        section_template_file = split(section_template_path)[-1]
        self.assertEqual(section_template_file, "_section_scientific_category.html")

        # get a single standard property...
        property_proxy = True
        section_template_path = get_section_template_path(property_proxy, property_type, category_proxy)
        section_template_file = split(section_template_path)[-1]
        self.assertEqual(section_template_file, "_section_scientific_property.html")

    def test_api_get_new_edit_form_section(self):

        # just test getting a complete component for now
        # (that's all I use anyway)
        section_key = "|".join([
            self.test_version_key,
            self.test_model_key,
            self.test_vocabulary_key,
            self.test_component_key,
        ])

        query_limit = FuzzyInt(0, 572)
        request_url = add_parameters_to_url(
            reverse("api_get_new_edit_form_section", kwargs={
                "project_name": self.downscaling_project.name,
                "section_key": section_key,
            }),
            **{"session_id": "test"}
        )

        with self.assertNumQueries(query_limit):
            response = self.client.get(request_url)

        # make sure that the view was successful...
        self.assertEqual(response.status_code, 200)

        # make sure that the correct section was returned...
        section_parameters = response.context["section_parameters"]
        self.assertTrue("model_form" in section_parameters)
        self.assertTrue("standard_property_formset" in section_parameters)
        self.assertTrue("scientific_property_formset" in section_parameters)
        self.assertTrue("active_standard_categories_and_properties" in section_parameters)
        self.assertTrue("active_scientific_categories_and_properties" in section_parameters)

        form_prefix = u"%s_%s" % (self.test_vocabulary_key, self.test_component_key)
        self.assertEqual(section_parameters["model_form"].prefix, form_prefix)
        self.assertEqual(section_parameters["standard_property_formset"].prefix, form_prefix + "_standard_properties")
        self.assertEqual(section_parameters["scientific_property_formset"].prefix, form_prefix + "_scientific_properties")

        self.assertIsNone(section_parameters["model_form"].instance.pk)

    def test_api_get_existing_edit_form_section(self):

        # just test getting a complete component for now
        # (that's all I use anyway)
        section_key = "|".join([
            self.test_version_key,
            self.test_model_key,
            self.test_vocabulary_key,
            self.test_component_key,
        ])

        model_id = self.downscaling_model_component_realization_set["models"][0].get_root().pk

        query_limit = FuzzyInt(0, 468)
        request_url = add_parameters_to_url(
            reverse("api_get_existing_edit_form_section", kwargs={
                "project_name": self.downscaling_project.name,
                "section_key": section_key,
                "model_id": model_id,
            }),
            **{"session_id": "test"}
        )

        with self.assertNumQueries(query_limit):
            response = self.client.get(request_url)

        # make sure that the view was successful...
        self.assertEqual(response.status_code, 200)

        # make sure that the correct section was returned...
        section_parameters = response.context["section_parameters"]
        self.assertTrue("model_form" in section_parameters)
        self.assertTrue("standard_property_formset" in section_parameters)
        self.assertTrue("scientific_property_formset" in section_parameters)
        self.assertTrue("active_standard_categories_and_properties" in section_parameters)
        self.assertTrue("active_scientific_categories_and_properties" in section_parameters)

        form_prefix = u"%s_%s" % (self.test_vocabulary_key, self.test_component_key)
        self.assertEqual(section_parameters["model_form"].prefix, form_prefix)
        self.assertEqual(section_parameters["standard_property_formset"].prefix, form_prefix + "_standard_properties")
        self.assertEqual(section_parameters["scientific_property_formset"].prefix, form_prefix + "_scientific_properties")

        self.assertIsNotNone(section_parameters["model_form"].instance.pk)
