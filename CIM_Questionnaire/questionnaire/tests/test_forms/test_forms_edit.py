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

from CIM_Questionnaire.questionnaire.forms.forms_edit import *
from CIM_Questionnaire.questionnaire.forms.forms_edit_model import *
from CIM_Questionnaire.questionnaire.forms.forms_edit_standard_properties import *
from CIM_Questionnaire.questionnaire.forms.forms_edit_scientific_properties import *

from CIM_Questionnaire.questionnaire.views.views_base import get_cached_existing_customization_set, get_cached_new_realization_set, get_cached_existing_realization_set
from CIM_Questionnaire.questionnaire.utils import remove_non_loaded_data, remove_null_data
from CIM_Questionnaire.questionnaire.tests.test_base import TestQuestionnaireBase


class Test(TestQuestionnaireBase):

    def test_create_new_edit_forms_from_models(self):

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

        self.assertEqual(len(models), len(model_formset.forms))
        self.assertEqual(len(models), len(standard_properties_formsets))
        self.assertEqual(len(models), len(scientific_properties_formsets))

        for model, model_form in zip(models, model_formset.forms):
            model_key = model.get_model_key()
            model_proxy = model.proxy
            self.assertEqual(model_key, model_form.prefix)
            self.assertEqual(model_proxy.pk, model_form.get_current_field_value("proxy"))
            self.assertEqual(model_proxy.pk, model_form.customizer.proxy.pk)
            self.assertIn(model_key, standard_properties_formsets)
            self.assertIn(model_key, scientific_properties_formsets)

            for standard_property, standard_property_form in zip(standard_properties[model_key], standard_properties_formsets[model_key]):
                property_proxy = standard_property.proxy
                self.assertEqual(property_proxy.pk, standard_property_form.get_current_field_value("proxy"))
                self.assertEqual(property_proxy.pk, standard_property_form.customizer.proxy.pk)

            for scientific_property, scientific_property_form in zip(scientific_properties[model_key], scientific_properties_formsets[model_key]):
                property_proxy = scientific_property.proxy
                self.assertEqual(property_proxy.pk, scientific_property_form.get_current_field_value("proxy"))
                self.assertEqual(property_proxy.pk, scientific_property_form.customizer.proxy.pk)

    def test_create_existing_edit_forms_from_models(self):

        models = self.downscaling_model_component_realization_set["models"]
        model_customizer = self.downscaling_model_component_customizer_set["model_customizer"]
        standard_properties = self.downscaling_model_component_realization_set["standard_properties"]
        standard_property_customizers = self.downscaling_model_component_customizer_set["standard_property_customizers"]
        scientific_properties = self.downscaling_model_component_realization_set["scientific_properties"]
        scientific_property_customizers = self.downscaling_model_component_customizer_set["scientific_property_customizers"]

        (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_existing_edit_forms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers)

        self.assertEqual(len(models), len(model_formset.forms))
        self.assertEqual(len(models), len(standard_properties_formsets))
        self.assertEqual(len(models), len(scientific_properties_formsets))

        for model, model_form in zip(models, model_formset.forms):
            model_key = model.get_model_key()
            model_proxy = model.proxy
            self.assertEqual(model, model_form.instance)
            self.assertEqual(model_key, model_form.prefix)
            self.assertEqual(model_proxy.pk, model_form.get_current_field_value("proxy"))
            self.assertEqual(model_proxy.pk, model_form.customizer.proxy.pk)
            self.assertIn(model_key, standard_properties_formsets)
            self.assertIn(model_key, scientific_properties_formsets)

            for standard_property, standard_property_form in zip(standard_properties[model_key], standard_properties_formsets[model_key]):
                property_proxy = standard_property.proxy
                self.assertEqual(standard_property, standard_property_form.instance)
                self.assertEqual(property_proxy.pk, standard_property_form.get_current_field_value("proxy"))
                self.assertEqual(property_proxy.pk, standard_property_form.customizer.proxy.pk)

            for scientific_property, scientific_property_form in zip(scientific_properties[model_key], scientific_properties_formsets[model_key]):
                property_proxy = scientific_property.proxy
                self.assertEqual(scientific_property, scientific_property_form.instance)
                self.assertEqual(property_proxy.pk, scientific_property_form.get_current_field_value("proxy"))
                self.assertEqual(property_proxy.pk, scientific_property_form.customizer.proxy.pk)

    def test_create_new_edit_forms_from_models_with_subforms(self):

        session_id = "test"

        test_customization_set = get_cached_existing_customization_set(session_id, self.downscaling_model_component_customizer_set_with_subforms["model_customizer"], self.downscaling_model_component_vocabularies)
        test_realization_set = get_cached_new_realization_set(session_id, self.downscaling_model_component_customizer_set_with_subforms, self.downscaling_model_component_proxy_set, self.downscaling_model_component_vocabularies)

        models = test_realization_set["models"]
        model_customizer = test_customization_set["model_customizer"]
        standard_properties = test_realization_set["standard_properties"]
        standard_property_customizers = test_customization_set["standard_property_customizers"]
        scientific_properties = test_realization_set["scientific_properties"]
        scientific_property_customizers = test_customization_set["scientific_property_customizers"]

        (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_new_edit_forms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers)

        for model in models:
            model_key = model.get_model_key()
            for standard_property, standard_property_form in zip(standard_properties[model_key], standard_properties_formsets[model_key]):
                form_prefix = standard_property_form.prefix
                self.assertEqual(standard_property.proxy.pk, standard_property_form.get_current_field_value("proxy"))
                standard_property_customizer = standard_property_form.customizer
                if standard_property_customizer.field_type == "RELATIONSHIP" and standard_property_customizer.relationship_show_subform:
                    (subform_customizer, model_subformset, standard_properties_subformsets, scientific_properties_subformsets) = \
                        standard_property_form.get_subform_tuple()
                    subform_prefix = u"%s_subform" % form_prefix
                    self.assertEqual(subform_customizer.proxy, standard_property.proxy.relationship_target_model)
                    self.assertEqual(len(model_subformset.forms), 1)
                    self.assertEqual(model_subformset.prefix, subform_prefix)
                    self.assertEqual(subform_customizer.proxy.pk, model_subformset.forms[0].get_current_field_value("proxy"))
                    for standard_properties_subformset in standard_properties_subformsets.values():
                        for standard_subproperty_proxy, standard_property_subform in zip(subform_customizer.proxy.standard_properties.all(), standard_properties_subformset.forms):
                            standard_subproperty_customizer = standard_property_subform.customizer
                            self.assertEqual(standard_subproperty_proxy.pk, standard_property_subform.get_current_field_value("proxy"))
                            self.assertEqual(standard_subproperty_proxy, standard_subproperty_customizer.proxy)
                            self.assertTrue(standard_property_subform.prefix.startswith(subform_prefix))
                    for scientific_properties_subformset in scientific_properties_subformsets.values():
                        self.assertEqual(len(scientific_properties_subformset.forms), 0)

    def test_create_existing_edit_forms_from_models_with_subforms(self):

        session_id = "test"

        test_customization_set = get_cached_existing_customization_set(session_id, self.downscaling_model_component_customizer_set_with_subforms["model_customizer"], self.downscaling_model_component_vocabularies)
        test_realization_set = get_cached_existing_realization_set(session_id, self.downscaling_model_component_realization_set["models"], self.downscaling_model_component_customizer_set_with_subforms, self.downscaling_model_component_proxy_set, self.downscaling_model_component_vocabularies)

        models = test_realization_set["models"]
        model_customizer = test_customization_set["model_customizer"]
        standard_properties = test_realization_set["standard_properties"]
        standard_property_customizers = test_customization_set["standard_property_customizers"]
        scientific_properties = test_realization_set["scientific_properties"]
        scientific_property_customizers = test_customization_set["scientific_property_customizers"]

        (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_existing_edit_forms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers)

        for model in models:
            model_key = model.get_model_key()
            for standard_property, standard_property_form in zip(standard_properties[model_key], standard_properties_formsets[model_key]):
                form_prefix = standard_property_form.prefix
                self.assertEqual(standard_property.proxy.pk, standard_property_form.get_current_field_value("proxy"))
                standard_property_customizer = standard_property_form.customizer
                if standard_property_customizer.field_type == "RELATIONSHIP" and standard_property_customizer.relationship_show_subform:
                    (subform_customizer, model_subformset, standard_properties_subformsets, scientific_properties_subformsets) = \
                        standard_property_form.get_subform_tuple()
                    subform_prefix = u"%s_subform" % form_prefix
                    self.assertEqual(subform_customizer.proxy, standard_property.proxy.relationship_target_model)
                    self.assertEqual(len(model_subformset.forms), 1)
                    self.assertEqual(model_subformset.prefix, subform_prefix)
                    self.assertEqual(subform_customizer.proxy.pk, model_subformset.forms[0].get_current_field_value("proxy"))
                    for standard_properties_subformset in standard_properties_subformsets.values():
                        for standard_subproperty_proxy, standard_property_subform in zip(subform_customizer.proxy.standard_properties.all(), standard_properties_subformset.forms):
                            standard_subproperty_customizer = standard_property_subform.customizer
                            self.assertEqual(standard_subproperty_proxy.pk, standard_property_subform.get_current_field_value("proxy"))
                            self.assertEqual(standard_subproperty_proxy, standard_subproperty_customizer.proxy)
                            self.assertTrue(standard_property_subform.prefix.startswith(subform_prefix))
                    for scientific_properties_subformset in scientific_properties_subformsets.values():
                        self.assertEqual(len(scientific_properties_subformset.forms), 0)

    def test_create_edit_forms_from_data(self):

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

        # simulate one of the forms being loaded...
        model_formset.forms[0].load()
        # loaded_key = model_formset.forms[0].prefix

        post_data = get_data_from_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, simulate_post=True)

        (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_edit_forms_from_data(post_data, models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers)

        self.assertEqual(all(validity), True)

    #
    # def test_metadata_model_formset_factory_from_models(self):
    #
    #     test_document_type = "modelcomponent"
    #
    #     test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
    #
    #     test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
    #
    #     test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy)
    #     (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
    #         MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
    #
    #     (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)
    #
    #     (models, standard_properties, scientific_properties) = \
    #         MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)
    #
    #     models_data = [create_model_form_data(model, model_customizer) for model in models]
    #
    #     model_keys = [model.get_model_key() for model in models]
    #
    #     model_formset = MetadataModelFormSetFactory(
    #         initial = models_data,
    #         extra = len(models_data),
    #         prefixes = model_keys,
    #         customizer = model_customizer,
    #     )
    #
    #     self.assertEqual(len(model_formset), 6)
    #     self.assertEqual(model_formset.number_of_models, 6)
    #     self.assertEqual(model_formset.prefix, "form")
    #     for model_key, model_form in zip(model_keys, model_formset):
    #         self.assertEqual(model_key, model_form.prefix)
    #         self.assertEqual(model_form.customizer, model_customizer)
    #
    #
    # def test_metadata_standard_property_inline_formset_factory_from_models(self):
    #
    #     test_document_type = "modelcomponent"
    #
    #     test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
    #
    #     test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
    #
    #     test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy)
    #     (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
    #         MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
    #
    #     (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)
    #
    #     (models, standard_properties, scientific_properties) = \
    #         MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)
    #
    #     model_keys = [model.get_model_key() for model in models]
    #
    #     standard_properties_formsets = {}
    #     for model_key, model in zip(model_keys, models):
    #
    #         standard_properties_data = [
    #             create_standard_property_form_data(model, standard_property, standard_property_customizer)
    #             for standard_property, standard_property_customizer in
    #             zip(standard_properties[model_key], standard_property_customizers)
    #             if standard_property_customizer.displayed
    #         ]
    #         standard_properties_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
    #             instance = model,
    #             prefix = model_key,
    #             initial = standard_properties_data,
    #             extra = len(standard_properties_data),
    #             customizers = standard_property_customizers,
    #         )
    #
    #     self.assertSetEqual(set(model_keys), set(standard_properties_formsets.keys()))
    #
    #     for model_key, model in zip(model_keys, models):
    #         standard_properties_formset = standard_properties_formsets[model_key]
    #
    #         standard_properties_formset_prefix = standard_properties_formset.prefix
    #         self.assertEqual(standard_properties_formset_prefix, u"%s_standard_properties"%(model_key))
    #
    #         self.assertEqual(len(standard_properties_formset), 6)
    #         self.assertEqual(standard_properties_formset.number_of_properties, 6)
    #         for i, (standard_property_form, standard_property) in enumerate(zip(standard_properties_formset, standard_properties[model_key])):
    #
    #             self.assertEqual(standard_property_form.prefix, u"%s-%s" % (standard_properties_formset_prefix, i))
    #             self.assertEqual(standard_property_form.customizer.proxy, standard_property.proxy)
    #
    #             if standard_property.field_type == MetadataFieldTypes.RELATIONSHIP:
    #                 self.assertQuerysetEqual(standard_property_form.fields["relationship_value"].queryset, MetadataModel.objects.filter(proxy=standard_property.proxy.relationship_target_model))
    #
    #
    # def test_metadata_standard_property_inline_formset_factory_from_models_with_subforms(self):
    #
    #     test_document_type = "modelcomponent"
    #
    #     test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
    #
    #     test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
    #
    #     properties_with_subforms = [ "author", ]
    #     test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=properties_with_subforms)
    #     (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
    #         MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
    #
    #
    #     (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)
    #
    #     (models, standard_properties, scientific_properties) = \
    #         MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)
    #
    #     model_keys = [model.get_model_key() for model in models]
    #
    #     standard_properties_formsets = {}
    #     for model_key, model in zip(model_keys, models):
    #
    #         standard_properties_data = [
    #             create_standard_property_form_data(model, standard_property, standard_property_customizer)
    #             for standard_property, standard_property_customizer in
    #             zip(standard_properties[model_key], standard_property_customizers)
    #             if standard_property_customizer.displayed
    #         ]
    #         standard_properties_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
    #             instance = model,
    #             prefix = model_key,
    #             initial = standard_properties_data,
    #             extra = len(standard_properties_data),
    #             customizers = standard_property_customizers,
    #         )
    #
    #     self.assertSetEqual(set(model_keys), set(standard_properties_formsets.keys()))
    #
    #     for model_key, model in zip(model_keys, models):
    #         standard_properties_formset = standard_properties_formsets[model_key]
    #
    #         standard_properties_formset_prefix = standard_properties_formset.prefix
    #         self.assertEqual(standard_properties_formset_prefix, u"%s_standard_properties"%(model_key))
    #
    #         self.assertEqual(len(standard_properties_formset), 6)
    #         self.assertEqual(standard_properties_formset.number_of_properties, 6)
    #         for i, (standard_property_form, standard_property) in enumerate(zip(standard_properties_formset, standard_properties[model_key])):
    #
    #             self.assertEqual(standard_property_form.prefix, u"%s-%s" % (standard_properties_formset_prefix, i))
    #             self.assertEqual(standard_property_form.customizer.proxy, standard_property.proxy)
    #
    #             if standard_property.field_type == MetadataFieldTypes.RELATIONSHIP:
    #                 self.assertQuerysetEqual(standard_property_form.fields["relationship_value"].queryset, MetadataModel.objects.filter(proxy=standard_property.proxy.relationship_target_model))
    #
    #                 if standard_property.name in properties_with_subforms:
    #                     subform_customizer = standard_property_form.get_subform_customizer()
    #                     model_subformset = standard_property_form.get_model_subformset()
    #                     standard_properties_subformsets = standard_property_form.get_standard_properties_subformsets()
    #                     scientific_properties_subformsets = standard_property_form.get_scientific_properties_subformsets()
    #
    #                     self.assertIsNotNone(subform_customizer)
    #                     self.assertIsNotNone(model_subformset)
    #                     self.assertIsNotNone(standard_properties_subformsets)
    #                     self.assertIsNotNone(scientific_properties_subformsets)
    #
    #                 # further testing of the subform content is handled in below
    #
    #
    # def test_create_new_edit_forms_from_models(self):
    #
    #     test_document_type = "modelcomponent"
    #
    #     test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
    #
    #     test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
    #
    #     test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])
    #     (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
    #         MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
    #     scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)
    #
    #     (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)
    #
    #     (models, standard_properties, scientific_properties) = \
    #         MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)
    #
    #     (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_new_edit_forms_from_models(models,model_customizer,standard_properties,standard_property_customizers,scientific_properties,scientific_property_customizers)
    #
    #
    # def test_create_new_edit_subforms_from_models(self):
    #
    #     test_document_type = "modelcomponent"
    #
    #     test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
    #
    #     test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
    #
    #     test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])
    #     property_customizer = test_customizer.standard_property_customizers.get(name="author")
    #     subform_customizer = property_customizer.subform_customizer
    #     self.assertIsNotNone(subform_customizer)
    #
    #     (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
    #         MetadataCustomizer.get_existing_customizer_set(subform_customizer, MetadataVocabulary.objects.none())
    #     scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)
    #
    #     test_subform_prefix = "test_prefix"
    #     subform_min, subform_max = [int(val) if val != "*" else val for val in property_customizer.relationship_cardinality.split("|")]
    #
    #     (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(model_customizer.proxy, vocabularies=MetadataVocabulary.objects.none())
    #
    #     # this is a contrived test b/c parent_vocabulary_key and parent_component_key are hard-coded
    #     (models, standard_properties, scientific_properties) = \
    #         MetadataModel.get_new_subrealization_set(subform_customizer.project, subform_customizer.version, subform_customizer.proxy, standard_property_proxies, scientific_property_proxies, model_customizer, MetadataVocabulary.objects.none(), DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY)
    #
    #     (model_subformset, standard_properties_subformsets, scientific_properties_subformsets) = \
    #         create_new_edit_subforms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix=test_subform_prefix, subform_min=subform_min, subform_max=subform_max)
    #
    #     self.assertEqual(model_subformset.prefix, u"%s_subform" % (test_subform_prefix))
    #     for i, model_subform in enumerate(model_subformset.forms):
    #         self.assertEqual(model_subform.prefix, u"%s-%s" % (model_subformset.prefix, i))
    #
    #         for standard_properties_subformset in standard_properties_subformsets.values():
    #             self.assertEqual(standard_properties_subformset.prefix, u"%s_standard_properties" % (model_subform.prefix))
    #             for i, standard_property_subform in enumerate(standard_properties_subformset.forms):
    #                 self.assertEqual(standard_property_subform.prefix, u"%s-%s" % (standard_properties_subformset.prefix, i))
    #
    #         for scientific_properties_subformset in scientific_properties_subformsets.values():
    #             self.assertEqual(scientific_properties_subformset.prefix, u"%s_scientific_properties" % (model_subform.prefix))
    #             for i, scientific_property_subform in enumerate(scientific_properties_subformset.forms):
    #                 self.assertEqual(scientific_property_subform.prefix, u"%s-%s" % (scientific_properties_subformset.prefix, i))
    #
    #     actual_model_subformset_data = get_data_from_formset(model_subformset)
    #
    #     test_model_subformset_data = {
    #         u'%s-INITIAL_FORMS' % (model_subformset.prefix) : 0,
    #         u'%s-TOTAL_FORMS' % (model_subformset.prefix) : 1,
    #         u'%s-0-id' % (model_subformset.prefix) : None,
    #         u'%s-0-component_key' % (model_subformset.prefix) : DEFAULT_COMPONENT_KEY,
    #         u'%s-0-is_root' % (model_subformset.prefix) : True,
    #         u'%s-0-title' % (model_subformset.prefix) : u'RootComponent',
    #         u'%s-0-active' % (model_subformset.prefix) : True,
    #         u'%s-0-version' % (model_subformset.prefix) : self.version.pk,
    #         u'%s-0-project' % (model_subformset.prefix) : self.project.pk,
    #         u'%s-0-proxy' % (model_subformset.prefix) : model_proxy.pk,
    #         u'%s-0-order' % (model_subformset.prefix) : 1,
    #         u'%s-0-vocabulary_key' % (model_subformset.prefix) : DEFAULT_VOCABULARY_KEY,
    #         u'%s-0-DELETE' % (model_subformset.prefix) : False,
    #         u'%s-0-description' % (model_subformset.prefix) : u'a stripped-down responsible party to use for testing purposes.',
    #         u'%s-0-name' % (model_subformset.prefix) : u'responsibleParty',
    #         u'%s-0-is_document' % (model_subformset.prefix) : False,
    #     }
    #
    #     test_standard_properties_subformset_data = {
    #         u'test_prefix_subform-0_standard_properties-INITIAL_FORMS': 0,
    #         u'test_prefix_subform-0_standard_properties-TOTAL_FORMS': 2,
    #         u'test_prefix_subform-0_standard_properties-0-relationship_value': [],
    #         u'test_prefix_subform-0_standard_properties-0-proxy': MetadataStandardPropertyProxy.objects.get(model_proxy=model_proxy, name__iexact="individualname").pk,
    #         u'test_prefix_subform-0_standard_properties-0-field_type': u'ATOMIC',
    #         u'test_prefix_subform-0_standard_properties-0-name': u'individualName',
    #         u'test_prefix_subform-0_standard_properties-0-is_label': True,
    #         u'test_prefix_subform-0_standard_properties-0-enumeration_value': None,
    #         u'test_prefix_subform-0_standard_properties-0-id': None,
    #         u'test_prefix_subform-0_standard_properties-0-enumeration_other_value': 'Please enter a custom value',
    #         u'test_prefix_subform-0_standard_properties-0-order': 0,
    #         u'test_prefix_subform-0_standard_properties-0-atomic_value': None,
    #         u'test_prefix_subform-0_standard_properties-0-model': None,
    #         #u'test_prefix_subform-0_standard_properties-0-DELETE': False,
    #         u'test_prefix_subform-0_standard_properties-1-proxy': MetadataStandardPropertyProxy.objects.get(model_proxy=model_proxy, name__iexact="contactinfo").pk,
    #         u'test_prefix_subform-0_standard_properties-1-order': 1,
    #         u'test_prefix_subform-0_standard_properties-1-id': None,
    #         u'test_prefix_subform-0_standard_properties-1-name': u'contactInfo',
    #         u'test_prefix_subform-0_standard_properties-1-enumeration_other_value': 'Please enter a custom value',
    #         u'test_prefix_subform-0_standard_properties-1-field_type': u'RELATIONSHIP',
    #         u'test_prefix_subform-0_standard_properties-1-model': None,
    #         u'test_prefix_subform-0_standard_properties-1-is_label': False,
    #         u'test_prefix_subform-0_standard_properties-1-relationship_value': [],
    #         u'test_prefix_subform-0_standard_properties-1-atomic_value': None,
    #         u'test_prefix_subform-0_standard_properties-1-enumeration_value': None,
    #         #u'test_prefix_subform-0_standard_properties-1-DELETE': False,
    #     }
    #
    #     self.assertDictEqual(actual_model_subformset_data,test_model_subformset_data,excluded_keys=[u"%s-id"%(model_subformset.prefix)])
    #
    #     for standard_properties_subformset in standard_properties_subformsets.values():
    #         actual_standard_properties_subformset_data = get_data_from_formset(standard_properties_subformset)
    #         self.assertDictEqual(actual_standard_properties_subformset_data,test_standard_properties_subformset_data,excluded_keys=[u"%s-id"%(standard_properties_subformset.prefix)])
    #
    #     for scientific_properties_subformset in scientific_properties_subformsets.values():
    #        self.assertEqual(len(scientific_properties_subformset.forms), 0)
    #
    #
    # def test_metadata_model_formset_factory_from_data(self):
    #
    #     test_document_type = "modelcomponent"
    #
    #     test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
    #
    #     test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
    #
    #     test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])
    #     (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
    #         MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
    #     scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)
    #
    #     (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)
    #
    #     (models, standard_properties, scientific_properties) = \
    #         MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)
    #
    #     (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_new_edit_forms_from_models(models,model_customizer,standard_properties,standard_property_customizers,scientific_properties,scientific_property_customizers)
    #
    #     data = get_data_from_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, simulate_post=False)
    #
    #     model_keys = [model.get_model_key() for model in models]
    #
    #     model_formset = MetadataModelFormSetFactory(
    #         data = data,
    #         prefixes = model_keys,
    #         customizer = model_customizer,
    #     )
    #
    #     self.assertEqual(len(model_formset), 6)
    #     self.assertEqual(model_formset.number_of_models, 6)
    #     self.assertEqual(model_formset.prefix, "form")
    #     for model_key, model_form in zip(model_keys, model_formset):
    #         self.assertEqual(model_key, model_form.prefix)
    #         self.assertEqual(model_form.customizer, model_customizer)
    #
    #
    #
    # def test_metadata_standard_property_inline_formset_factory_from_data(self):
    #
    #     test_document_type = "modelcomponent"
    #
    #     test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
    #
    #     test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
    #
    #     test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])
    #     (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
    #         MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
    #     scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)
    #
    #     (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)
    #
    #     (models, standard_properties, scientific_properties) = \
    #         MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)
    #
    #     (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_new_edit_forms_from_models(models,model_customizer,standard_properties,standard_property_customizers,scientific_properties,scientific_property_customizers)
    #
    #     data = get_data_from_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, simulate_post=False)
    #
    #     model_keys = [model.get_model_key() for model in models]
    #
    #     standard_properties_formsets = {}
    #     for model_key, model in zip(model_keys, models):
    #
    #         standard_properties_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
    #             instance = model,
    #             prefix = model_key,
    #             data = data,
    #             customizers = standard_property_customizers,
    #         )
    #
    #     self.assertSetEqual(set(model_keys), set(standard_properties_formsets.keys()))
    #
    #     for model_key, model in zip(model_keys, models):
    #         standard_properties_formset = standard_properties_formsets[model_key]
    #
    #         standard_properties_formset_prefix = standard_properties_formset.prefix
    #         self.assertEqual(standard_properties_formset_prefix, u"%s_standard_properties"%(model_key))
    #
    #         self.assertEqual(len(standard_properties_formset), 6)
    #         self.assertEqual(standard_properties_formset.number_of_properties, 6)
    #         for i, (standard_property_form, standard_property) in enumerate(zip(standard_properties_formset, standard_properties[model_key])):
    #
    #             self.assertEqual(standard_property_form.prefix, u"%s-%s" % (standard_properties_formset_prefix, i))
    #             self.assertEqual(standard_property_form.customizer.proxy, standard_property.proxy)
    #
    #             if standard_property.field_type == MetadataFieldTypes.RELATIONSHIP:
    #                 self.assertQuerysetEqual(standard_property_form.fields["relationship_value"].queryset, MetadataModel.objects.filter(proxy=standard_property.proxy.relationship_target_model))
    #
    #
    # def test_metadata_standard_property_inline_formset_factory_from_data_with_subforms(self):
    #
    #     test_document_type = "modelcomponent"
    #
    #     test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
    #
    #     test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
    #
    #     properties_with_subforms = [ "author", ]
    #     test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=properties_with_subforms)
    #     (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
    #         MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
    #     scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)
    #
    #     (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)
    #
    #     (models, standard_properties, scientific_properties) = \
    #         MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)
    #
    #     (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_new_edit_forms_from_models(models,model_customizer,standard_properties,standard_property_customizers,scientific_properties,scientific_property_customizers)
    #
    #     data = get_data_from_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, simulate_post=False)
    #
    #     model_keys = [model.get_model_key() for model in models]
    #
    #     standard_properties_formsets = {}
    #     for model_key, model in zip(model_keys, models):
    #
    #         standard_properties_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
    #             instance = model,
    #             prefix = model_key,
    #             data = data,
    #             customizers = standard_property_customizers,
    #         )
    #
    #
    #     self.assertSetEqual(set(model_keys), set(standard_properties_formsets.keys()))
    #
    #     for model_key, model in zip(model_keys, models):
    #         standard_properties_formset = standard_properties_formsets[model_key]
    #
    #         standard_properties_formset_prefix = standard_properties_formset.prefix
    #         self.assertEqual(standard_properties_formset_prefix, u"%s_standard_properties"%(model_key))
    #
    #         self.assertEqual(len(standard_properties_formset), 6)
    #         self.assertEqual(standard_properties_formset.number_of_properties, 6)
    #         for i, (standard_property_form, standard_property) in enumerate(zip(standard_properties_formset, standard_properties[model_key])):
    #
    #             self.assertEqual(standard_property_form.prefix, u"%s-%s" % (standard_properties_formset_prefix, i))
    #             self.assertEqual(standard_property_form.customizer.proxy, standard_property.proxy)
    #
    #             if standard_property.field_type == MetadataFieldTypes.RELATIONSHIP:
    #                 self.assertQuerysetEqual(standard_property_form.fields["relationship_value"].queryset, MetadataModel.objects.filter(proxy=standard_property.proxy.relationship_target_model))
    #
    #                 if standard_property.name in properties_with_subforms:
    #                     subform_customizer = standard_property_form.get_subform_customizer()
    #                     model_subformset = standard_property_form.get_model_subformset()
    #                     standard_properties_subformsets = standard_property_form.get_standard_properties_subformsets()
    #                     scientific_properties_subformsets = standard_property_form.get_scientific_properties_subformsets()
    #
    #                     self.assertIsNotNone(subform_customizer)
    #                     self.assertIsNotNone(model_subformset)
    #                     self.assertIsNotNone(standard_properties_subformsets)
    #                     self.assertIsNotNone(scientific_properties_subformsets)
    #
    #                     # further testing of the subform content is handled below
    #
    #
    # def test_model_formset_is_valid(self):
    #
    #     import ipdb; ipdb.set_trace()
    #
    #     test_document_type = "modelcomponent"
    #
    #     test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
    #
    #     test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
    #
    #     test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])
    #     (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
    #         MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
    #     scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)
    #
    #     (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)
    #
    #     (models, standard_properties, scientific_properties) = \
    #         MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)
    #
    #     (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_new_edit_forms_from_models(models,model_customizer,standard_properties,standard_property_customizers,scientific_properties,scientific_property_customizers)
    #
    #     data = get_data_from_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, simulate_post=False)
    #
    #     model_keys = [model.get_model_key() for model in models]
    #
    #     model_formset = MetadataModelFormSetFactory(
    #         data = data,
    #         prefixes = model_keys,
    #         customizer = model_customizer,
    #     )
    #
    #     for model_form in model_formset:
    #         model_form.load()
    #
    #     model_formset_validity = model_formset.is_valid()
    #
    #     self.assertEqual(model_formset_validity, True)
    #
    #
    # def test_standard_property_inline_formset_is_valid(self):
    #
    #     test_document_type = "modelcomponent"
    #
    #     test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
    #
    #     test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
    #
    #     test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])
    #     (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
    #         MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
    #     scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)
    #
    #     (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)
    #
    #     (models, standard_properties, scientific_properties) = \
    #         MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)
    #
    #     (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_new_edit_forms_from_models(models,model_customizer,standard_properties,standard_property_customizers,scientific_properties,scientific_property_customizers)
    #
    #     data = get_data_from_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, simulate_post=False)
    #
    #     model_keys = [model.get_model_key() for model in models]
    #
    #     model_formset = MetadataModelFormSetFactory(
    #         data = data,
    #         prefixes = model_keys,
    #         customizer = model_customizer,
    #     )
    #
    #     model_formset_validity = model_formset.is_valid()
    #     model_instances = [model_form.save(commit=False) for model_form in model_formset.forms]
    #
    #     standard_properties_formsets = {}
    #
    #     validity = []
    #     for i, model_key in enumerate(model_keys):
    #
    #         standard_properties_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
    #             instance = model_instances[i],
    #             prefix = model_key,
    #             data = data,
    #             customizers = standard_property_customizers,
    #         )
    #
    #         validity += [standard_properties_formsets[model_key].is_valid()]
    #
    #     self.assertEqual(all(validity), True)
    #
    #
    # def test_standard_property_inline_formset_with_subforms_is_valid(self):
    #
    #     test_document_type = "modelcomponent"
    #
    #     test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
    #
    #     test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
    #
    #     test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])
    #     (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
    #         MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
    #     scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)
    #
    #     (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)
    #
    #     (models, standard_properties, scientific_properties) = \
    #         MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)
    #
    #     (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_new_edit_forms_from_models(models,model_customizer,standard_properties,standard_property_customizers,scientific_properties,scientific_property_customizers)
    #
    #     data = get_data_from_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, simulate_post=False)
    #
    #     model_keys = [model.get_model_key() for model in models]
    #
    #     model_formset = MetadataModelFormSetFactory(
    #         data = data,
    #         prefixes = model_keys,
    #         customizer = model_customizer,
    #     )
    #
    #     model_formset_validity = model_formset.is_valid()
    #     model_instances = [model_form.save(commit=False) for model_form in model_formset.forms]
    #
    #     standard_properties_formsets = {}
    #
    #     validity = []
    #     for i, model_key in enumerate(model_keys):
    #
    #         standard_properties_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
    #             instance = model_instances[i],
    #             prefix = model_key,
    #             data = data,
    #             customizers = standard_property_customizers,
    #         )
    #
    #         validity += [standard_properties_formsets[model_key].is_valid()]
    #
    #         for form in standard_properties_formsets[model_key].forms:
    #             field_type = form.get_current_field_value("field_type")
    #             customizer = form.customizer
    #             if field_type == MetadataFieldTypes.RELATIONSHIP and customizer.relationship_show_subform:
    #                 self.assertEqual(form.subform_validity, True)
    #
    #     self.assertEqual(all(validity), True)
    #
    #
    # def test_create_edit_forms_from_data(self):
    #
    #     test_document_type = "modelcomponent"
    #
    #     test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
    #
    #     test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
    #
    #     test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])
    #     (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
    #         MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
    #     scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)
    #
    #     (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)
    #
    #     (models, standard_properties, scientific_properties) = \
    #         MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)
    #
    #     (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_new_edit_forms_from_models(models,model_customizer,standard_properties,standard_property_customizers,scientific_properties,scientific_property_customizers)
    #
    #     original_data = get_data_from_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, simulate_post=False)
    #
    #     (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_edit_forms_from_data(original_data, models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers)
    #
    #     new_data = get_data_from_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, simulate_post=False)
    #
    #     excluded_keys = [key for key in new_data.keys() if "-DELETE" in key]
    #
    #     self.assertEqual(all(validity), True)
    #     self.assertDictEqual(original_data,new_data,excluded_keys=excluded_keys)
    #
    #
    #
    # def test_save_valid_model_formset(self):
    #
    #     test_document_type = "modelcomponent"
    #
    #     test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
    #
    #     test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
    #     self.assertEqual(len(test_vocabularies), 1)
    #     test_vocabulary = test_vocabularies[0]
    #
    #     test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])
    #     (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
    #         MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
    #     scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)
    #
    #     (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)
    #
    #     (models, standard_properties, scientific_properties) = \
    #         MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)
    #     model_parent_dictionary = get_model_parent_dictionary(models)
    #
    #     (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_new_edit_forms_from_models(models,model_customizer,standard_properties,standard_property_customizers,scientific_properties,scientific_property_customizers)
    #
    #     data = get_data_from_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, simulate_post=False)
    #
    #     (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_edit_forms_from_data(data, models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers)
    #
    #     model_instances = save_valid_model_formset(model_formset, model_parent_dictionary=model_parent_dictionary)
    #
    #     models_data = [model_to_data(model) for model in model_instances]
    #
    #     test_models_data = [
    #         {'is_root': True,  'name': u'modelComponent', 'title': u'RootComponent',                        'component_key': DEFAULT_COMPONENT_KEY,                                                                                           'order': 0, 'project': self.project.pk, 'version': self.version.pk, 'proxy': MetadataModelProxy.objects.get(version=self.version,name__iexact=test_document_type).pk, 'vocabulary_key': DEFAULT_VOCABULARY_KEY,    'is_document': True, 'active': True, 'description': u'A ModelCompnent is nice.', "is_published" : False, },
    #         {'is_root': False, 'name': u'modelComponent', 'title': u'vocabulary : TestModel',               'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="testmodel").get_key(),              'order': 0, 'project': self.project.pk, 'version': self.version.pk, 'proxy': MetadataModelProxy.objects.get(version=self.version,name__iexact=test_document_type).pk, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, 'description': u'A ModelCompnent is nice.', "is_published" : False, },
    #         {'is_root': False, 'name': u'modelComponent', 'title': u'vocabulary : TestModelKeyProperties',  'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="testmodelkeyproperties").get_key(), 'order': 0, 'project': self.project.pk, 'version': self.version.pk, 'proxy': MetadataModelProxy.objects.get(version=self.version,name__iexact=test_document_type).pk, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, 'description': u'A ModelCompnent is nice.', "is_published" : False, },
    #         {'is_root': False, 'name': u'modelComponent', 'title': u'vocabulary : PretendSubModel',         'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="pretendsubmodel").get_key(),        'order': 0, 'project': self.project.pk, 'version': self.version.pk, 'proxy': MetadataModelProxy.objects.get(version=self.version,name__iexact=test_document_type).pk, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, 'description': u'A ModelCompnent is nice.', "is_published" : False, },
    #         {'is_root': False, 'name': u'modelComponent', 'title': u'vocabulary : SubModel',                'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="submodel").get_key(),               'order': 0, 'project': self.project.pk, 'version': self.version.pk, 'proxy': MetadataModelProxy.objects.get(version=self.version,name__iexact=test_document_type).pk, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, 'description': u'A ModelCompnent is nice.', "is_published" : False, },
    #         {'is_root': False, 'name': u'modelComponent', 'title': u'vocabulary : SubSubModel',             'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="subsubmodel").get_key(),            'order': 0, 'project': self.project.pk, 'version': self.version.pk, 'proxy': MetadataModelProxy.objects.get(version=self.version,name__iexact=test_document_type).pk, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, 'description': u'A ModelCompnent is nice.', "is_published" : False, },
    #     ]
    #
    #     self.assertEqual(len(model_instances), 6)
    #
    #     for actual_model_data, test_model_data in zip(models_data, test_models_data):
    #         self.assertDictEqual(actual_model_data, test_model_data, excluded_keys=["id", "parent", "last_modified", "created",])
    #
    #     for model_instance in model_instances:
    #         model_parent = find_in_sequence(lambda model: model.get_model_key() == model_parent_dictionary[model_instance.get_model_key()], model_instances)
    #         self.assertEqual(model_instance.parent, model_parent)
    #
    #
    # def test_save_valid_standard_properties_formset(self):
    #
    #     test_document_type = "modelcomponent"
    #
    #     test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
    #
    #     test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
    #
    #     test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, )#properties_with_subforms=["author",])
    #     (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
    #         MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
    #     scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)
    #
    #     (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)
    #
    #     (models, standard_properties, scientific_properties) = \
    #         MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)
    #     model_parent_dictionary = get_model_parent_dictionary(models)
    #
    #     (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_new_edit_forms_from_models(models,model_customizer,standard_properties,standard_property_customizers,scientific_properties,scientific_property_customizers)
    #
    #     data = get_data_from_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, simulate_post=False)
    #
    #     (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_edit_forms_from_data(data, models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers)
    #
    #     test_standard_properties_data = [
    #         {'field_type': u'ATOMIC',       'enumeration_other_value': u'Please enter a custom value', 'name': u'string',       'enumeration_value': [], 'relationship_value': [], 'is_label': True,  'model': None, 'order': 0, 'atomic_value': u''},
    #         {'field_type': u'ATOMIC',       'enumeration_other_value': u'Please enter a custom value', 'name': u'date',         'enumeration_value': [], 'relationship_value': [], 'is_label': False, 'model': None, 'order': 2, 'atomic_value': u''},
    #         {'field_type': u'RELATIONSHIP', 'enumeration_other_value': u'Please enter a custom value', 'name': u'author',       'enumeration_value': [], 'relationship_value': [], 'is_label': False, 'model': None, 'order': 5, 'atomic_value': u''},
    #         {'field_type': u'ATOMIC',       'enumeration_other_value': u'Please enter a custom value', 'name': u'boolean',      'enumeration_value': [], 'relationship_value': [], 'is_label': False, 'model': None, 'order': 1, 'atomic_value': u'False'},
    #         {'field_type': u'ENUMERATION',  'enumeration_other_value': u'Please enter a custom value', 'name': u'enumeration',  'enumeration_value': [], 'relationship_value': [], 'is_label': False, 'model': None, 'order': 4, 'atomic_value': u''},
    #         {'field_type': u'RELATIONSHIP', 'enumeration_other_value': u'Please enter a custom value', 'name': u'contact',      'enumeration_value': [], 'relationship_value': [], 'is_label': False, 'model': None, 'order': 6, 'atomic_value': u''},
    #     ]
    #
    #     for standard_properties_formset in standard_properties_formsets.values():
    #         n_old_standard_properties_qs = len(MetadataStandardProperty.objects.all())
    #         standard_property_instances = save_valid_standard_properties_formset(standard_properties_formset)
    #         n_new_standard_properties_qs = len(MetadataStandardProperty.objects.all())
    #
    #         self.assertEqual(len(standard_property_instances), 6)
    #         self.assertEqual(n_new_standard_properties_qs - n_old_standard_properties_qs, len(standard_property_instances))
    #
    #         standard_property_instances_data = [model_to_data(standard_property_instance) for standard_property_instance in standard_property_instances]
    #
    #         for actual_standard_property_data, test_standard_property_data_data in zip(standard_property_instances_data, test_standard_properties_data):
    #             self.assertDictEqual(actual_standard_property_data, test_standard_property_data_data, excluded_keys=["id", "proxy", "last_modified", "created",])
    #
    #
    # def test_save_valid_standard_properties_formset_with_subforms(self):
    #
    #     test_document_type = "modelcomponent"
    #
    #     test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
    #
    #     test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
    #
    #     properties_with_subforms=[ "author", "contact", ]
    #     test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=properties_with_subforms)
    #     (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
    #         MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
    #     scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)
    #
    #     (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)
    #
    #     (models, standard_properties, scientific_properties) = \
    #         MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)
    #     model_parent_dictionary = get_model_parent_dictionary(models)
    #
    #     (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_new_edit_forms_from_models(models,model_customizer,standard_properties,standard_property_customizers,scientific_properties,scientific_property_customizers)
    #
    #     data = get_data_from_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, simulate_post=False)
    #
    #     (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_edit_forms_from_data(data, models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers)
    #
    #     for standard_properties_formset in standard_properties_formsets.values():
    #
    #         standard_property_instances = save_valid_standard_properties_formset(standard_properties_formset)
    #
    #         self.assertEqual(len(standard_property_instances), 6)
    #
    #         for property_with_subform in properties_with_subforms:
    #             standard_property_instance = find_in_sequence(lambda property: property.name==property_with_subform, standard_property_instances)
    #             self.assertGreater(len(standard_property_instance.relationship_value.all()), 0)
    #
    #
    # def test_save_valid_standard_properties_formset_with_subforms_added_subforms(self):
    #
    #     test_document_type = "modelcomponent"
    #
    #     test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
    #
    #     test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
    #
    #     properties_with_subforms=[ "author", "contact", ]
    #     test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=properties_with_subforms)
    #     (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
    #         MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
    #     scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)
    #
    #     (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)
    #
    #     (models, standard_properties, scientific_properties) = \
    #         MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)
    #     model_parent_dictionary = get_model_parent_dictionary(models)
    #
    #     (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_new_edit_forms_from_models(models,model_customizer,standard_properties, standard_property_customizers,scientific_properties, scientific_property_customizers)
    #
    #     data = get_data_from_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, simulate_post=False)
    #
    #     properties_to_add_subforms_to = ["contact"]
    #     root_component_key = models[0].get_root().get_model_key()
    #     new_data = self.add_subform_to_post_data(data, standard_properties_formsets[root_component_key], properties_to_add_subform_to=properties_to_add_subforms_to)
    #
    #     (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_edit_forms_from_data(new_data, models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers)
    #
    #     self.assertTrue(all(validity))
    #
    #     test_standard_properties_subform_data = [
    #         {'field_type': u'ATOMIC',       'enumeration_other_value': u'Please enter a custom value', 'name': u'individualName',   'enumeration_value': u'', 'relationship_value': [], 'is_label': True,   'order': 0, 'atomic_value': u''},
    #         {'field_type': u'RELATIONSHIP', 'enumeration_other_value': u'Please enter a custom value', 'name': u'contactInfo',      'enumeration_value': u'', 'relationship_value': [], 'is_label': False,  'order': 1, 'atomic_value': u''},
    #     ]
    #
    #     for key, standard_properties_formset in standard_properties_formsets.iteritems():
    #
    #         standard_property_instances = save_valid_standard_properties_formset(standard_properties_formset)
    #
    #         self.assertEqual(len(standard_property_instances), 6)
    #
    #         for property_with_subform in properties_with_subforms:
    #             standard_property_instance = find_in_sequence(lambda property: property.name==property_with_subform, standard_property_instances)
    #
    #             if standard_property_instance.name in properties_to_add_subforms_to and key == root_component_key:
    #                 # this is the one we added a subform to
    #                 self.assertEqual(len(standard_property_instance.relationship_value.all()), 2)
    #             else:
    #                 self.assertEqual(len(standard_property_instance.relationship_value.all()), 1)
    #
    #             for model_subform_instance in standard_property_instance.relationship_value.all():
    #                 standard_properties_data = [model_to_data(sp) for sp in model_subform_instance.standard_properties.all()]
    #                 for actual_standard_property_subform_data, test_standard_property_subform_data in zip(standard_properties_data, test_standard_properties_subform_data):
    #                     self.assertDictEqual(actual_standard_property_subform_data, actual_standard_property_subform_data, excluded_keys=["id", "model", "proxy"])
    #
    #
    #
    # def test_standard_property_form_has_changed(self):
    #
    #     test_document_type = "modelcomponent"
    #
    #     test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
    #
    #     test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
    #
    #     properties_with_subforms = [ "author", ]
    #     test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=properties_with_subforms)
    #     (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
    #         MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
    #     scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)
    #
    #     (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)
    #
    #     (models, standard_properties, scientific_properties) = \
    #         MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)
    #
    #     (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_new_edit_forms_from_models(models,model_customizer,standard_properties,standard_property_customizers,scientific_properties,scientific_property_customizers)
    #
    #     data = get_data_from_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, simulate_post=False)
    #
    #     (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #         create_edit_forms_from_data(data, models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers)
    #
    #     for standard_properties_formset in standard_properties_formsets.values():
    #         self.assertTrue(all([form.has_changed() for form in standard_properties_formset.forms]))
    #
    #         for property_with_subform in properties_with_subforms:
    #             standard_property_form_with_subform = get_form_by_field(standard_properties_formset,"name",property_with_subform)
    #
    #             #standard_property_form_with_subform.get_subform_customizer()
    #             model_subformset = standard_property_form_with_subform.get_model_subformset()
    #             standard_properties_subformsets = standard_property_form_with_subform.get_standard_properties_subformsets()
    #             scientific_properties_subformsets = standard_property_form_with_subform.get_scientific_properties_subformsets()
    #
    #             self.assertIsInstance(model_subformset, MetadataModelSubFormSet)
    #             self.assertNotIsInstance(model_subformset, MetadataModelFormSet)
    #
    #             for standard_properties_subformset in standard_properties_subformsets.values():
    #                 for standard_property_subform in standard_properties_subformset.forms:
    #                     self.assertIsInstance(standard_property_subform,MetadataStandardPropertySubForm)
    #                     self.assertNotIsInstance(standard_property_subform,MetadataStandardPropertyForm)
    #
    #
    #                     standard_property_subform.has_changed()
