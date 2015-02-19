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


class TestMetadataSerialization(TestQuestionnaireBase):

    def setUp(self):

        super(TestMetadataSerialization, self).setUp()

        metadata_serializations = MetadataModelSerialization.objects.all()
        self.assertEqual(len(metadata_serializations), 1)

        self.serialization = metadata_serializations[0]
        self.serialized_model = self.serialization.model

        self.assertEqual(self.serialized_model.project.name, "es-fdl")
        self.assertEqual(self.serialized_model.proxy.name, "modelComponent")

        self.assertTrue(self.serialization_is_valid(self.serialization, self.serialized_model))

    def serialization_is_valid(self, serialization, serialized_model):

        # TODO: THIS DOES NOT ACTUALLY PERFORM XML VALIDATION
        # TODO: INSTEAD, IT JUST CHECKS THAT CERTAIN ELEMENTS/ATTRIBUTES ARE IN-PLACE

        serialization_content = et.fromstring(serialization.content)

        try:
            # test that I created the correct type of document...
            ontology_type = get_index(xpath_fix(serialization_content, "/modelComponent/@ontologyTypeKey"), 0)
            self.assertEqual(serialization_content.tag, "modelComponent")
            self.assertEqual(ontology_type, "cim.1.software.ModelComponent")

            # test that I included all sub-components correctly...
            components = serialized_model.get_descendants(include_self=True)
            component_ids = [component.get_id() for component in components]
            for i, component_section in enumerate(xpath_fix(serialization_content, "//meta")):
                _id = get_index(xpath_fix(component_section, "./id/text()"), 0)
                self.assertIn(_id, component_ids)
                _language = get_index(xpath_fix(component_section, "./language/text()"), 0)
                self.assertEqual(_language, "en")
                _project = get_index(xpath_fix(component_section, "./project/text()"), 0)
                self.assertEqual(_project, serialized_model.project.name)
                _source = get_index(xpath_fix(component_section, "./source/text()"), 0)
                self.assertEqual(_source, "CIM Questionnaire")
                _version = get_index(xpath_fix(component_section, "./version/text()"), 0)
                self.assertEqual(int(_version), serialization.version)

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

            return True

        except AssertionError:

            return False

    def test_serialize_model(self):

        old_minor_version = self.serialized_model.get_minor_version()
        old_major_version = self.serialized_model.get_major_version()

        old_serialization = self.serialization

        self.serialized_model.publish()

        new_minor_version = self.serialized_model.get_minor_version()
        new_major_version = self.serialized_model.get_major_version()

        new_serialization = MetadataModelSerialization.objects.get(model=self.serialized_model, version=new_major_version)

        self.assertEqual(int(old_major_version), 1)
        self.assertEqual(int(old_minor_version), 1)
        self.assertEqual(int(new_major_version), 2)
        self.assertEqual(int(new_minor_version), 1)
        self.assertNotEqual(old_serialization, new_serialization)
        self.assertEqual(old_serialization.name, new_serialization.name)
        self.assertEqual(old_serialization.version, 1)
        self.assertEqual(new_serialization.version, 2)
        self.assertTrue(new_serialization.publication_date > old_serialization.publication_date)

        self.assertTrue(self.serialization_is_valid(new_serialization, self.serialized_model))

        pass

    def test_reserialize_model(self):

        old_serialization = self.serialization
        old_serialization_version = old_serialization.version
        old_serialization_content = old_serialization.content

        self.serialized_model.publish()

        new_serialization = MetadataModelSerialization.objects.get(model=self.serialized_model, version=self.serialized_model.get_major_version())
        new_serialization_version = new_serialization.version
        self.assertNotEqual(old_serialization, new_serialization)

        self.serialized_model.serialize(serialization_version=old_serialization_version)

        self.assertEqual(len(MetadataModelSerialization.objects.all()), 2)

        re_serialization = MetadataModelSerialization.objects.filter(model=self.serialized_model).exclude(version=new_serialization_version)[0]
        re_serialization_version = self.serialization.version
        self.assertEqual(old_serialization_version, re_serialization_version)
        self.assertNotEqual(re_serialization_version, new_serialization_version)

        self.assertTrue(self.serialization_is_valid(re_serialization, self.serialized_model))

    def test_write_serialization(self):

        serialization = self.serialization
        serialization_path = serialization.get_file_path()

        self.serialization.write()

        self.assertFileExists(serialization_path)
        with open(serialization_path, "r") as file:
            serialization_content = file.read()
            self.assertEqual(serialization_content, self.serialization.content)
