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
.. module:: test_metadata_serialization

Tests the serialization process for MetadataModels
"""

# TODO: RIGHT NOW ONLY ES-DOC FORMAT IS SUPPORTED
# TODO: UPDATE TESTS TO SUPPORT METAFOR FORMAT TOO

from lxml import etree as et

from CIM_Questionnaire.questionnaire.tests.test_base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.models.metadata_serialization import MetadataModelSerialization
from CIM_Questionnaire.questionnaire.utils import xpath_fix, get_index

# import os
# import urllib2
#
# from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary, UPLOAD_PATH as VOCABULARY_UPLOAD_PATH
# from CIM_Questionnaire.questionnaire.models.metadata_version import MetadataVersion, UPLOAD_PATH as VERSION_UPLOAD_PATH
# from CIM_Questionnaire.questionnaire.models.metadata_categorization import MetadataCategorization, UPLOAD_PATH as CATEGORIZATION_UPLOAD_PATH
# from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer
# from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy
# from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel


class TestMetadataSerialization(TestQuestionnaireBase):

    def setUp(self):

        super(TestMetadataSerialization, self).setUp()

        metadata_serializations = MetadataModelSerialization.objects.all()
        self.assertEqual(len(metadata_serializations), 1)

        self.serialization = metadata_serializations[0]
        self.serialized_model = self.serialization.model

        self.assertEqual(self.serialized_model.project.name, "es-fdl")
        self.assertEqual(self.serialized_model.proxy.name, "modelComponent")

        # cim_document_type = "modelcomponent"
        #
        # # have _real_ version 1.8.1 of the CIM handy for these tests
        # cim_project = MetadataProject(name="test_cim", title="CIM Project", active=True, authenticated=False)
        # cim_project.save()
        # project_qs = MetadataProject.objects.all()
        # self.assertEqual(len(project_qs), 2)
        #
        # cim_vocabulary_path = os.path.join(VOCABULARY_UPLOAD_PATH, "test_atmosphere_bdl.xml")
        # cim_vocabulary = MetadataVocabulary(name="cim", file=cim_vocabulary_path, document_type=cim_document_type)
        # cim_vocabulary.save()
        # vocabulary_qs = MetadataVocabulary.objects.all()
        # self.assertEqual(len(vocabulary_qs), 2)
        #
        # cim_version_path = os.path.join(VERSION_UPLOAD_PATH, "test_cim_1_8_1.xml")
        # cim_version = MetadataVersion(name="cim", version="1.8.1", file=cim_version_path, url="http://www.purl.org/org/esmetadata/cim/1.8.1/schemas/cim.xsd")
        # cim_version.save()
        # version_qs = MetadataVersion.objects.all()
        # self.assertEqual(len(version_qs), 2)
        #
        # cim_categorization_path = os.path.join(CATEGORIZATION_UPLOAD_PATH, "test_esdoc_categorization.xml")
        # cim_categorization = MetadataCategorization(name="cim", file=cim_categorization_path)
        # cim_categorization.save()
        # categorization_qs = MetadataCategorization.objects.all()
        # self.assertEqual(len(categorization_qs), 2)
        #
        # cim_version.categorization = cim_categorization
        # cim_version.save()
        # cim_project.vocabularies.add(cim_vocabulary)
        # cim_project.save()
        # cim_version.register()
        # cim_version.save()
        # cim_categorization.register()
        # cim_categorization.save()
        # cim_vocabulary.register()
        # cim_vocabulary.save()
        #
        # cim_proxy_to_test = MetadataModelProxy.objects.get(version=cim_version, name__iexact=cim_document_type)
        # cim_vocabularies_to_test = [cim_vocabulary]
        #
        # # setup customizers & realizations...
        # (cim_model_customizer, cim_standard_category_customizers, cim_standard_property_customizers, cim_scientific_category_customizers, cim_scientific_property_customizers) = \
        #     MetadataCustomizer.get_new_customizer_set(cim_project, cim_version, cim_proxy_to_test, cim_vocabularies_to_test)
        # # add some one-off customizations as if this had been filled out in the form...
        # cim_model_customizer.name = "cim_customizer"
        # cim_model_customizer.default = True
        # for standard_property_customizer in cim_standard_property_customizers:
        #     if standard_property_customizer.category is None:
        #         # TODO: REMOVE THIS AS SOON AS I'VE FIXED ISSUE #71
        #         standard_property_customizer.displayed = False
        # MetadataCustomizer.save_customizer_set(cim_model_customizer, cim_standard_category_customizers, cim_standard_property_customizers, cim_scientific_category_customizers, cim_scientific_property_customizers)
        # self.cim_model_customizer = cim_model_customizer
        #
        # reordered_cim_standard_property_proxies = [standard_property_customizer.proxy for standard_property_customizer in cim_standard_property_customizers]
        # reordered_cim_scientific_property_customizers = get_joined_keys_dict(cim_scientific_property_customizers)
        # reordered_cim_scientific_property_proxies = { key : [spc.proxy for spc in value] for key,value in reordered_cim_scientific_property_customizers.items() }
        #
        # (cim_models, cim_standard_properties, cim_scientific_properties) = \
        #     MetadataModel.get_new_realization_set(cim_project, cim_version, cim_proxy_to_test, reordered_cim_standard_property_proxies, reordered_cim_scientific_property_proxies, cim_model_customizer, cim_vocabularies_to_test)
        # MetadataModel.save_realization_set(cim_models, cim_standard_properties, cim_scientific_properties)
        # self.cim_model_realization = cim_models[0].get_root()
        #
        # serialization_qs = MetadataModelSerialization.objects.all()
        # self.assertEqual(len(serialization_qs), 0)
        #
        # self.cim_model_realization.publish(force_save=True)
        #
        # serialization_qs = MetadataModelSerialization.objects.all()
        # self.assertEqual(len(serialization_qs), 1)
        #
        # self.cim_model_serialization = serialization_qs[0]

    def test_serialization_is_valid(self):

        # TODO: THIS DOES NOT ACTUALLY PERFORM XML VALIDATION
        # TODO: INSTEAD, IT JUST CHECKS THAT CERTAIN ELEMENTS/ATTRIBUTES ARE IN-PLACE

        serialization_content = et.fromstring(self.serialization.content)

        # test that I created the correct type of document...
        ontology_type = get_index(xpath_fix(serialization_content, "/modelComponent/@ontologyTypeKey"), 0)
        self.assertEqual(serialization_content.tag, "modelComponent")
        self.assertEqual(ontology_type, "cim.1.software.ModelComponent")

        # test that I included all sub-components correctly...
        components = self.serialized_model.get_descendants(include_self=True)
        component_ids = [component.get_id() for component in components]
        for i, component_section in enumerate(xpath_fix(serialization_content, "//meta")):
            _id = get_index(xpath_fix(component_section, "./id/text()"), 0)
            self.assertIn(_id, component_ids)
            _language = get_index(xpath_fix(component_section, "./language/text()"), 0)
            self.assertEqual(_language, "en")
            _project = get_index(xpath_fix(component_section, "./project/text()"), 0)
            self.assertEqual(_project, self.serialized_model.project.name)
            _source = get_index(xpath_fix(component_section, "./source/text()"), 0)
            self.assertEqual(_source, "CIM Questionnaire")
            _version = get_index(xpath_fix(component_section, "./version/text()"), 0)
            self.assertEqual(int(_version), self.serialization.version)

        # test various standard/scientific properties...

        # TODO: EXPAND THIS SECTION TO INCLUDE ALL COMBINATIONS OF PROPERTY VALUES

        # test that license (single/other/nullable) has a single value ["GNU General Public License"]
        _license = get_index(xpath_fix(serialization_content, "//property[shortName/text()='License']"), 0)
        self.assertIsNotNone(_license)
        _license_values = [value.text for value in xpath_fix(_license, ".//value")]
        self.assertEqual(len(_license_values), 1)
        self.assertIn("GNU General Public License", _license_values)

        # test that basiccapabilities (multi/other/nullable) has multiple values including OTHER ["transfer of field data between models", "unit conversion", "OTHER: something else"]
        _basic_capabilities = get_index(xpath_fix(serialization_content, "//property[shortName/text()='BasicCapabilities']"), 0)
        self.assertIsNotNone(_basic_capabilities)
        _basic_capabilities_values = [value.text for value in xpath_fix(_basic_capabilities, ".//value")]
        self.assertEqual(len(_basic_capabilities_values), 3)
        self.assertIn("transfer of field data between models", _basic_capabilities_values)
        self.assertIn("unit conversion", _basic_capabilities_values)
        self.assertIn("OTHER: something else", _basic_capabilities_values)

        # test that designintent (multi/other/nullable) has NONE value ["NONE"]
        _design_intent = get_index(xpath_fix(serialization_content, "//property[shortName/text()='DesignIntent']"), 0)
        self.assertIsNotNone(_design_intent)
        _design_intent_values = [value.text for value in xpath_fix(_design_intent, ".//value")]
        self.assertEqual(len(_design_intent_values), 1)
        self.assertIn("NONE", _design_intent_values)

        # test that mediationprovided (single/other/nullable) has OTHER value ["OTHER: another one"]
        _mediation_provided = get_index(xpath_fix(serialization_content, "//property[shortName/text()='MediationProvided']"), 0)
        self.assertIsNotNone(_mediation_provided)
        _mediation_provided_values = [value.text for value in xpath_fix(_mediation_provided, ".//value")]
        self.assertEqual(len(_mediation_provided_values), 1)
        self.assertIn("OTHER: another one", _mediation_provided_values)

        # test that controlregime (multi/other/nullable) is empty
        _control_regime = get_index(xpath_fix(serialization_content, "//property[shortName/text()='ControlRegime']"), 0)
        self.assertIsNotNone(_control_regime)
        _control_regime_values = [value.text for value in xpath_fix(_control_regime, ".//value")]
        self.assertEqual(len(_control_regime_values), 0)






        pass




    def test_serialize_model(self):
        pass

    def test_reserialize_model(self):
        pass

    def test_write_serialization(self):
        pass


