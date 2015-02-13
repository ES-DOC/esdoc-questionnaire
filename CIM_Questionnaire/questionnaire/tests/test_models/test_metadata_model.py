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
.. module:: test_metadata_model

Tests the MetadataModel models
"""

import os
from django.conf import settings
from lxml import etree as et
from CIM_Questionnaire.questionnaire.tests.test_base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.models.metadata_model import *
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy, MetadataComponentProxy
from CIM_Questionnaire.questionnaire.models.metadata_version import MetadataVersion
from CIM_Questionnaire.questionnaire.models.metadata_categorization import MetadataCategorization
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary
from CIM_Questionnaire.questionnaire.models.metadata_project import MetadataProject
from CIM_Questionnaire.questionnaire.models.metadata_serialization import MetadataModelSerialization, MetadataSerializationFormats
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import UPLOAD_PATH as VOCABULARY_UPLOAD_PATH
from CIM_Questionnaire.questionnaire.models.metadata_version import UPLOAD_PATH as VERSION_UPLOAD_PATH
from CIM_Questionnaire.questionnaire.models.metadata_categorization import UPLOAD_PATH as CATEGORIZATION_UPLOAD_PATH
from CIM_Questionnaire.questionnaire.utils import DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY, get_tag_without_namespace, get_attribute_without_namespace


def get_vocabulary_key(model_key):
    split_key = model_key.split('_')
    n_splits = len(split_key)
    return "_".join(split_key[:(n_splits/2)])


def get_component_key(model_key):
    split_key = model_key.split('_')
    n_splits = len(split_key)
    return "_".join(split_key[(n_splits/2):])


class TestMetadataModel(TestQuestionnaireBase):

    def test_get_new_realization_set(self):

        test_customizer = self.downscaling_model_component_customizer_set_with_subforms["model_customizer"]
        test_proxies = self.downscaling_model_component_proxy_set
        test_vocabularies = self.downscaling_model_component_vocabularies

        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_new_realization_set(self.downscaling_project, self.cim_1_8_1_version, test_proxies["model_proxy"], test_proxies["standard_property_proxies"], test_proxies["scientific_property_proxies"], test_customizer, test_vocabularies)

        self.assertEqual(len(models), 27)

        self.assertEqual(len(standard_properties), 27)
        for standard_property_list in standard_properties.values():
            self.assertEqual(len(standard_property_list), 23)

        test_model_keys = [u"%s_%s" % (DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY), ]
        for vocabulary in test_vocabularies:
            test_model_keys += \
                [u"%s_%s" % (vocabulary.get_key(), component.get_key()) for component in MetadataComponentProxy.objects.filter(vocabulary=vocabulary)]
        self.assertEqual(len(test_model_keys), 27)
        self.assertSetEqual(set(test_model_keys), set(scientific_properties.keys()))

        self.assertEqual(len(scientific_properties[test_model_keys[0]]), 0)
        self.assertEqual(len(scientific_properties[test_model_keys[1]]), 0)
        self.assertEqual(len(scientific_properties[test_model_keys[2]]), 3)
        self.assertEqual(len(scientific_properties[test_model_keys[3]]), 4)
        self.assertEqual(len(scientific_properties[test_model_keys[4]]), 6)
        self.assertEqual(len(scientific_properties[test_model_keys[5]]), 10)
        self.assertEqual(len(scientific_properties[test_model_keys[6]]), 10)
        self.assertEqual(len(scientific_properties[test_model_keys[7]]), 8)
        self.assertEqual(len(scientific_properties[test_model_keys[8]]), 10)
        self.assertEqual(len(scientific_properties[test_model_keys[9]]), 13)
        self.assertEqual(len(scientific_properties[test_model_keys[10]]), 7)
        self.assertEqual(len(scientific_properties[test_model_keys[11]]), 12)
        self.assertEqual(len(scientific_properties[test_model_keys[12]]), 13)
        self.assertEqual(len(scientific_properties[test_model_keys[13]]), 0)
        self.assertEqual(len(scientific_properties[test_model_keys[14]]), 7)
        self.assertEqual(len(scientific_properties[test_model_keys[15]]), 2)
        self.assertEqual(len(scientific_properties[test_model_keys[16]]), 4)
        self.assertEqual(len(scientific_properties[test_model_keys[17]]), 7)
        self.assertEqual(len(scientific_properties[test_model_keys[18]]), 4)
        self.assertEqual(len(scientific_properties[test_model_keys[19]]), 10)
        self.assertEqual(len(scientific_properties[test_model_keys[20]]), 9)
        self.assertEqual(len(scientific_properties[test_model_keys[21]]), 4)
        self.assertEqual(len(scientific_properties[test_model_keys[22]]), 3)
        self.assertEqual(len(scientific_properties[test_model_keys[23]]), 4)
        self.assertEqual(len(scientific_properties[test_model_keys[24]]), 7)
        self.assertEqual(len(scientific_properties[test_model_keys[25]]), 9)
        self.assertEqual(len(scientific_properties[test_model_keys[26]]), 6)

        excluded_model_fields = ["tree_id", "lft", "rght", "level", "parent", ]  # ignore mptt fields
        serialized_models = [self.fully_serialize_model(model, exclude=excluded_model_fields) for model in models]
        test_models_data = [
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': True,  'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[0]),  'document_version': u'0.0', 'title': u'RootComponent', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[0]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[1]),  'document_version': u'0.0', 'title': u'atmosphere : Atmosphere', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[1]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[2]),  'document_version': u'0.0', 'title': u'atmosphere : AtmosKeyProperties', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[2]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[3]),  'document_version': u'0.0', 'title': u'atmosphere : TopOfAtmosInsolation', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[3]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[4]),  'document_version': u'0.0', 'title': u'atmosphere : AtmosSpaceConfiguration', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[4]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[5]),  'document_version': u'0.0', 'title': u'atmosphere : AtmosHorizontalDomain', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[5]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[6]),  'document_version': u'0.0', 'title': u'atmosphere : AtmosDynamicalCore', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[6]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[7]),  'document_version': u'0.0', 'title': u'atmosphere : AtmosAdvection', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[7]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[8]),  'document_version': u'0.0', 'title': u'atmosphere : AtmosRadiation', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[8]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[9]),  'document_version': u'0.0', 'title': u'atmosphere : AtmosConvectTurbulCloud', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[9]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[10]), 'document_version': u'0.0', 'title': u'atmosphere : AtmosCloudScheme', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[10]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[11]), 'document_version': u'0.0', 'title': u'atmosphere : CloudSimulator', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[11]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[12]), 'document_version': u'0.0', 'title': u'atmosphere : AtmosOrographyAndWaves', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[12]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[13]), 'document_version': u'0.0', 'title': u'landsurface : LandSurface', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[13]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[14]), 'document_version': u'0.0', 'title': u'landsurface : LandSurfaceKeyProperties', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[14]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[15]), 'document_version': u'0.0', 'title': u'landsurface : LandSurfaceSpaceConfig', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[15]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[16]), 'document_version': u'0.0', 'title': u'landsurface : LandSurfaceSoil', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[16]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[17]), 'document_version': u'0.0', 'title': u'landsurface : LandSurfSoilHydrology', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[17]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[18]), 'document_version': u'0.0', 'title': u'landsurface : LandSurfSoilHeatTreatment', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[18]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[19]), 'document_version': u'0.0', 'title': u'landsurface : LandSurfaceSnow', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[19]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[20]), 'document_version': u'0.0', 'title': u'landsurface : LandSurfaceVegetation', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[20]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[21]), 'document_version': u'0.0', 'title': u'landsurface : LandSurfaceEnergyBalance', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[21]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[22]), 'document_version': u'0.0', 'title': u'landsurface : LandSurfaceAlbedo', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[22]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[23]), 'document_version': u'0.0', 'title': u'landsurface : LandSurfaceCarbonCycle', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[23]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[24]), 'document_version': u'0.0', 'title': u'landsurface : VegetationCarbonCycle', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[24]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[25]), 'document_version': u'0.0', 'title': u'landsurface : RiverRouting', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[25]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
            {'id': None, 'description': u'A ModelCompnent is a scientific model; it represents code which models some physical phenomena for a particular length of time.', 'is_root': False, 'version': self.cim_1_8_1_version, 'component_key': get_component_key(test_model_keys[26]), 'document_version': u'0.0', 'title': u'landsurface : LandSurfaceLakes', 'name': u'modelComponent', 'project': self.downscaling_project, 'proxy': self.downscaling_model_component_proxy_set["model_proxy"], 'vocabulary_key': u"%s" % get_vocabulary_key(test_model_keys[26]), 'is_document': True, 'active': True, 'order': 1, 'is_published': False, },
        ]

        atmosphere_component_proxies = self.atmosphere_vocabulary.component_proxies.all()
        landsurface_component_proxies = self.landsurface_vocabulary.component_proxies.all()
        test_scientific_properties_data = {
            u'DEFAULT_VOCABULARY_DEFAULT_COMPONENT': [
                # the root component has no scientific properties
            ],
            u'ce5755af-a244-4010-bef9-b5bd127a9c53_1f32c6ea-41da-455e-9780-ffcbfc500fc6': [
                # atmosphere_component_proxies[0] has no scientific properties
            ],
            u'ce5755af-a244-4010-bef9-b5bd127a9c53_3ae89284-303f-4901-988d-03bafaf0603a': [
                {"name": "ModelFamily", "model": models[2], "proxy": atmosphere_component_proxies[1].scientific_properties.all()[0], "field_type": u'PROPERTY', "enumeration_other_value": "Please enter a custom value", "extra_description": None, "category_key": "general-attributes", "is_enumeration": True, "extra_standard_name": None, "enumeration_value": None, "atomic_value": None, "is_label": False, "extra_units": None, "order": 0, },
                {"name": "BasicApproximations", "model": models[2], "proxy": atmosphere_component_proxies[1].scientific_properties.all()[1], "field_type": u'PROPERTY', "enumeration_other_value": "Please enter a custom value", "extra_description": None, "category_key": "general-attributes", "is_enumeration": True, "extra_standard_name": None, "enumeration_value": None, "atomic_value": None, "is_label": False, "extra_units": None, "order": 1, },
                {"name": "VolcanoesImplementation", "model": models[2], "proxy": atmosphere_component_proxies[1].scientific_properties.all()[2], "field_type": u'PROPERTY', "enumeration_other_value": "Please enter a custom value", "extra_description": None, "category_key": "general-attributes", "is_enumeration": True, "extra_standard_name": None, "enumeration_value": None, "atomic_value": None, "is_label": False, "extra_units": None, "order": 2, },
            ],
            u'ce5755af-a244-4010-bef9-b5bd127a9c53_f0476696-ec6f-4546-b903-a943faa01c1c': [
                {"name": "ImpactOnOzone", "model": models[3], "proxy": atmosphere_component_proxies[2].scientific_properties.all()[0], "field_type": u'PROPERTY', "enumeration_other_value": "Please enter a custom value", "extra_description": None, "category_key": "general-attributes", "is_enumeration": True, "extra_standard_name": None, "enumeration_value": None, "atomic_value": None, "is_label": False, "extra_units": None, "order": 0, },
                {"name": "BasicApproximations", "model": models[3], "proxy": atmosphere_component_proxies[2].scientific_properties.all()[1], "field_type": u'PROPERTY', "enumeration_other_value": "Please enter a custom value", "extra_description": None, "category_key": "general-attributes", "is_enumeration": True, "extra_standard_name": None, "enumeration_value": None, "atomic_value": None, "is_label": False, "extra_units": None, "order": 1, },
                {"name": "VolcanoesImplementation", "model": models[3], "proxy": atmosphere_component_proxies[2].scientific_properties.all()[2], "field_type": u'PROPERTY', "enumeration_other_value": "Please enter a custom value", "extra_description": None, "category_key": "general-attributes", "is_enumeration": True, "extra_standard_name": None, "enumeration_value": None, "atomic_value": None, "is_label": False, "extra_units": None, "order": 2, },
                {"name": "VolcanoesImplementation", "model": models[3], "proxy": atmosphere_component_proxies[2].scientific_properties.all()[3], "field_type": u'PROPERTY', "enumeration_other_value": "Please enter a custom value", "extra_description": None, "category_key": "general-attributes", "is_enumeration": True, "extra_standard_name": None, "enumeration_value": None, "atomic_value": None, "is_label": False, "extra_units": None, "order": 3, },
            ],
            u'ce5755af-a244-4010-bef9-b5bd127a9c53_01c2aac8-b31d-4515-878f-3e53174cd7ba': [
            ],
            u'ce5755af-a244-4010-bef9-b5bd127a9c53_db032a55-68bc-4f82-b97a-41520bf25f5a': [
            ],
            u'ce5755af-a244-4010-bef9-b5bd127a9c53_82adb43f-4974-43fb-93b2-74a5f9277655': [
            ],
            u'ce5755af-a244-4010-bef9-b5bd127a9c53_350d5713-2974-402b-b00b-026938c30ea0': [
            ],
            u'ce5755af-a244-4010-bef9-b5bd127a9c53_75cceb73-eb9a-4efc-b65c-705c745b0671': [
            ],
            u'ce5755af-a244-4010-bef9-b5bd127a9c53_ce7d9c7a-176a-46d4-b2a7-0dc171e17ae1': [
            ],
            u'ce5755af-a244-4010-bef9-b5bd127a9c53_b88d37c3-1e2a-4935-8628-1a56dafa6ca3': [
            ],
            u'ce5755af-a244-4010-bef9-b5bd127a9c53_796f552f-960e-412d-b2b6-45e947336896': [
            ],
            u'ce5755af-a244-4010-bef9-b5bd127a9c53_3b7b4ae0-b005-409e-aa14-595b10484d97': [
            ],
            u'c61c167c-8cea-49d1-97cc-d82d2ccefd6e_02ae0771-c2db-4b47-8fd2-2b9c42dcbf39': [
            ],
            u'c61c167c-8cea-49d1-97cc-d82d2ccefd6e_20f7e832-e8c4-454a-b38c-b3c2b87f9e04': [
            ],
            u'c61c167c-8cea-49d1-97cc-d82d2ccefd6e_4da76774-2978-4ce0-9515-4cbac33689af': [
            ],
            u'c61c167c-8cea-49d1-97cc-d82d2ccefd6e_0f5bc643-defe-4090-b45e-fd5378627fd4': [
            ],
            u'c61c167c-8cea-49d1-97cc-d82d2ccefd6e_d12f7060-a02f-454c-81d7-a60fc98a259b': [
            ],
            u'c61c167c-8cea-49d1-97cc-d82d2ccefd6e_6cf61c3c-eb01-4b8f-aa2a-a580f534f23c': [
            ],
            u'c61c167c-8cea-49d1-97cc-d82d2ccefd6e_ca6424d2-b142-45dc-918e-5ae10fcde422': [
            ],
            u'c61c167c-8cea-49d1-97cc-d82d2ccefd6e_45b6a292-14b8-454c-ab2a-51ac129f6d88': [
            ],
            u'c61c167c-8cea-49d1-97cc-d82d2ccefd6e_22c479de-fd1f-4e46-bc89-3e33c71a0898': [
            ],
            u'c61c167c-8cea-49d1-97cc-d82d2ccefd6e_8b83018b-e230-452a-8579-db236becc238': [
            ],
            u'c61c167c-8cea-49d1-97cc-d82d2ccefd6e_a4df24f5-3dd5-4663-be44-a2bafb093d1a': [
            ],
            u'c61c167c-8cea-49d1-97cc-d82d2ccefd6e_c89bc002-2c2b-459a-8c94-ba9d00580e40': [
            ],
            u'c61c167c-8cea-49d1-97cc-d82d2ccefd6e_6fa3dda4-08b5-4568-a08b-2cf015d823ac': [
            ],
            u'c61c167c-8cea-49d1-97cc-d82d2ccefd6e_c2d3eee5-c7c8-4967-91d3-7a1a12741311': [
            ],
        }
        for actual_model_data, test_model_data in zip(serialized_models, test_models_data):
            self.assertDictEqual(actual_model_data, test_model_data, excluded_keys=["id", "guid", "created", "last_modified"])

        excluded_standard_property_fields = []
        excluded_scientific_property_fields = ["id", ]
        for model in models:
            model_key = model.get_model_key()
            for standard_property, standard_property_proxy in zip(standard_properties[model_key], test_proxies["standard_property_proxies"]):
                self.assertEqual(standard_property.model, model)
                self.assertEqual(standard_property.proxy, standard_property_proxy)
                self.assertEqual(standard_property.name, standard_property_proxy.name)
                self.assertEqual(standard_property.order, standard_property_proxy.order)
                self.assertEqual(standard_property.is_label, standard_property_proxy.is_label)
                self.assertEqual(standard_property.field_type, standard_property_proxy.field_type)
                self.assertIsNone(standard_property.atomic_value)
                self.assertIsNone(standard_property.enumeration_value)
                self.assertEqual(standard_property.enumeration_other_value, "Please enter a custom value")
                # no need to test relationship_value, since m2m fields cannot be set before save()

            serialized_scientific_properties = [self.fully_serialize_model(sp, exclude=excluded_scientific_property_fields) for sp in scientific_properties[model_key]]
            import ipdb; ipdb.set_trace()
            for actual_scientific_property_data, test_scientific_property_data in zip(serialized_scientific_properties, test_scientific_properties_data[model_key]):
                self.assertDictEqual(actual_scientific_property_data, test_scientific_property_data)






    def test_get_new_realization_set2(self):

        test_document_type = "modelcomponent"

        test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)

        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
        self.assertEqual(len(test_vocabularies), 1)
        test_vocabulary = test_vocabularies[0]

        test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])

        (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)

        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)

        root_model_key = u"%s_%s" % (DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY)

        n_components = 1
        for vocabulary in test_vocabularies:
            n_components += len(vocabulary.component_proxies.all())
        self.assertEqual(len(models), n_components)
        self.assertEqual(n_components, 6)

        n_scientific_properties = sum([len(sp_list) for sp_list in scientific_properties.values()])
        self.assertEqual(n_scientific_properties, 9)

        excluded_fields = ["tree_id", "lft", "rght", "level", "parent",] # ignore mptt fields
        serialized_models = [self.fully_serialize_model(model,exclude=excluded_fields) for model in models]
        test_models_data = [
            { "document_version" : u"0.0", "is_published": False, 'is_root': True,  'version': self.version, 'created': None, 'component_key': DEFAULT_COMPONENT_KEY,                                                                                           'description': u'A ModelCompnent is nice.', 'title': u'RootComponent',                       'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': DEFAULT_VOCABULARY_KEY,    'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            { "document_version" : u"0.0", "is_published": False, 'is_root': False, 'version': self.version, 'created': None, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='testmodel').get_key(),              'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : TestModel',              'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            { "document_version" : u"0.0", "is_published": False, 'is_root': False, 'version': self.version, 'created': None, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='testmodelkeyproperties').get_key(), 'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : TestModelKeyProperties', 'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            { "document_version" : u"0.0", "is_published": False, 'is_root': False, 'version': self.version, 'created': None, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='pretendsubmodel').get_key(),        'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : PretendSubModel',        'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            { "document_version" : u"0.0", "is_published": False, 'is_root': False, 'version': self.version, 'created': None, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='submodel').get_key(),               'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : SubModel',               'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            { "document_version" : u"0.0", "is_published": False, 'is_root': False, 'version': self.version, 'created': None, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='subsubmodel').get_key(),            'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : SubSubModel',            'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
        ]

        test_scientific_properties_data = {
            u"%s_%s" % (DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY) : [],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="testmodelkeyproperties").get_key()) : [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',   'category_key': u'general-attributes',  'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'number', 'category_key': u'general-attributes',  'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 1, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'choice1', 'category_key': u'general-attributes', 'is_enumeration': True, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 2, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'choice2', 'category_key': u'general-attributes', 'is_enumeration': True, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 3, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',   'category_key': u'categoryone',         'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',   'category_key': u'categorytwo',         'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None},
            ],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="pretendsubmodel").get_key()) : [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name', 'category_key': u'categoryone', 'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="testmodel").get_key()) : [],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="submodel").get_key()) : [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name', 'category_key': u'categoryone', 'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="subsubmodel").get_key()) : [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name', 'category_key': u'categoryone', 'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
        }

        for actual_model_data,test_model_data in zip(serialized_models,test_models_data):
            self.assertDictEqual(actual_model_data, test_model_data, excluded_keys=["guid"])

        test_scientific_property_data = {}
        for model in models:
            model_key = model.get_model_key()
            for standard_property, standard_property_proxy in zip(standard_properties[model_key], standard_property_proxies):
                self.assertEqual(standard_property.model, model)
                self.assertEqual(standard_property.proxy, standard_property_proxy)
                self.assertEqual(standard_property.name, standard_property_proxy.name)
                self.assertEqual(standard_property.order, standard_property_proxy.order)
                self.assertEqual(standard_property.is_label, standard_property_proxy.is_label)
                self.assertEqual(standard_property.field_type, standard_property_proxy.field_type)
                self.assertIsNone(standard_property.atomic_value)
                self.assertIsNone(standard_property.enumeration_value)
                self.assertEqual(standard_property.enumeration_other_value, "Please enter a custom value")
                # no need to test relationship_value, since m2m fields cannot be set before save()

            excluded_fields = ["model", "proxy"]
            serialized_scientific_properties = [self.fully_serialize_model(sp, exclude=excluded_fields) for sp in scientific_properties[model_key]]
            for actual_scientific_property_data, test_scientific_property_data in zip(serialized_scientific_properties, test_scientific_properties_data[model_key]):
                self.assertDictEqual(actual_scientific_property_data, test_scientific_property_data)

            try:
                for scientific_property, scientific_property_proxy in zip(scientific_properties[model_key], scientific_property_proxies[model_key]):
                    self.assertEqual(scientific_property.model, model)
                    self.assertEqual(scientific_property.name, scientific_property_proxy.name)
            except KeyError:
                # the root model shouldn't have any scientific_properties
                self.assertEqual(model_key,root_model_key)


    def test_get_existing_realization_set(self):

        test_document_type = "modelcomponent"

        test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)

        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
        self.assertEqual(len(test_vocabularies), 1)
        test_vocabulary = test_vocabularies[0]

        test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])

        models = self.model_realization.get_descendants(include_self=True)

        # TODO: RETURN THESE IN THE SAME ORDER AS get_new_realization_set !!!!!!!!!

        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_existing_realization_set(models, test_customizer, vocabularies=test_vocabularies)

        root_model_key = u"%s_%s" % (DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY)

        n_components = 1
        for vocabulary in test_vocabularies:
            n_components += len(vocabulary.component_proxies.all())
        self.assertEqual(len(models), n_components)
        self.assertEqual(n_components, 6)

        n_scientific_properties = sum([len(sp_list) for sp_list in scientific_properties.values()])
        self.assertEqual(n_scientific_properties, 9)

        excluded_fields = [ "tree_id", "lft", "rght", "level", "parent", "last_modified", "created", "id", ] # ignore mptt fields & datetime-specific fields & pk field
        serialized_models = [ self.fully_serialize_model(model, exclude=excluded_fields) for model in models ]
        test_models_data = [
            { "document_version" : u"0.1", "is_published": False, 'is_root': True,  'version': self.version, 'component_key': DEFAULT_COMPONENT_KEY,                                                                                           'description': u'A ModelCompnent is nice.', 'title': u'RootComponent',                       'order': 0, 'project': self.project,   'proxy': test_proxy, 'vocabulary_key': DEFAULT_VOCABULARY_KEY,    'is_document': True, 'active': True, 'name': u'modelComponent' },
            { "document_version" : u"0.1", "is_published": False, 'is_root': False, 'version': self.version, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='testmodel').get_key(),              'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : TestModel',              'order': 0, 'project': self.project,   'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, 'name': u'modelComponent' },
            { "document_version" : u"0.1", "is_published": False, 'is_root': False, 'version': self.version, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='testmodelkeyproperties').get_key(), 'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : TestModelKeyProperties', 'order': 0, 'project': self.project,   'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, 'name': u'modelComponent' },
            { "document_version" : u"0.1", "is_published": False, 'is_root': False, 'version': self.version, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='pretendsubmodel').get_key(),        'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : PretendSubModel',        'order': 0, 'project': self.project,   'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, 'name': u'modelComponent' },
            { "document_version" : u"0.1", "is_published": False, 'is_root': False, 'version': self.version, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='submodel').get_key(),               'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : SubModel',               'order': 0, 'project': self.project,   'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, 'name': u'modelComponent' },
            { "document_version" : u"0.1", "is_published": False, 'is_root': False, 'version': self.version, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='subsubmodel').get_key(),            'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : SubSubModel',            'order': 0, 'project': self.project,   'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, 'name': u'modelComponent' },
        ]

        test_scientific_properties_data = {
            root_model_key : [],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="testmodelkeyproperties").get_key()) : [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',    'category_key': u'general-attributes',  'is_enumeration': False, 'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'number',  'category_key': u'general-attributes',  'is_enumeration': False, 'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 1, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'choice1', 'category_key': u'general-attributes',  'is_enumeration': True,  'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 2, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'choice2', 'category_key': u'general-attributes',  'is_enumeration': True,  'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 3, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',    'category_key': u'categoryone',         'is_enumeration': False, 'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',    'category_key': u'categorytwo',         'is_enumeration': False, 'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None},
            ],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="pretendsubmodel").get_key()) : [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name', 'category_key': u'categoryone', 'is_enumeration': False, 'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="testmodel").get_key()) : [],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="submodel").get_key()) : [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name', 'category_key': u'categoryone', 'is_enumeration': False, 'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="subsubmodel").get_key()) : [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name', 'category_key': u'categoryone', 'is_enumeration': False, 'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
        }

        for actual_model_data,test_model_data in zip(serialized_models,test_models_data):
            self.assertDictEqual(actual_model_data, test_model_data, excluded_keys=["guid"])

        test_scientific_property_data = {}
        for model in models:
            model_key = model.get_model_key()
            for standard_property, standard_property_proxy in zip(standard_properties[model_key], test_proxy.standard_properties.all()):
                self.assertEqual(standard_property.model, model)
                self.assertEqual(standard_property.proxy, standard_property_proxy)
                self.assertEqual(standard_property.name, standard_property_proxy.name)
                self.assertEqual(standard_property.order, standard_property_proxy.order)
                self.assertEqual(standard_property.is_label, standard_property_proxy.is_label)
                self.assertEqual(standard_property.field_type, standard_property_proxy.field_type)
                self.assertIsNone(standard_property.atomic_value)
                self.assertIsNone(standard_property.enumeration_value)
                self.assertEqual(standard_property.enumeration_other_value, "Please enter a custom value")
                # no need to test relationship_value, since m2m fields cannot be set before save()

            excluded_fields = ["model", "proxy", "id", ]
            serialized_scientific_properties = [self.fully_serialize_model(sp, exclude=excluded_fields) for sp in scientific_properties[model_key]]
            for actual_scientific_property_data, test_scientific_property_data in zip(serialized_scientific_properties, test_scientific_properties_data[model_key]):
                self.assertDictEqual(actual_scientific_property_data, test_scientific_property_data)


            # try:
            #     for scientific_property, scientific_property_proxy in zip(scientific_properties[model_key], scientific_property_proxies[model_key]):
            #         self.assertEqual(scientific_property.model, model)
            #         self.assertEqual(scientific_property.name, scientific_property_proxy.name)
            # except KeyError:
            #     # the root model shouldn't have any scientific_properties
            #     self.assertEqual(model_key,root_model_key)



    def test_publish_realization(self):

        model = self.model_realization

        self.assertEqual(model.is_published, False)
        self.assertEqual(model.document_version, "0.1")

        model.publish(force_save=False)

        self.assertEqual(model.document_version, "1.0")
        self.assertEqual(model.is_published, True)

        serializations_qs = MetadataModelSerialization.objects.filter(model=model)

        self.assertEqual(len(serializations_qs), 0)

        model.publish(force_save=True)

        serializations_qs = MetadataModelSerialization.objects.filter(model=model)

        self.assertEqual(len(serializations_qs), 1)


    def test_serialize_realization(self):

        model = self.model_realization

        model.publish(force_save=True)
        #model.serialize()  # serialization is done when force_save=True
                            # (doing it this way so version is appropriately updated)

        serialization = MetadataModelSerialization.objects.get(model=model)
        serialized_model = et.fromstring(str(serialization.content))

        self.assertEqual(get_tag_without_namespace(serialized_model), model.proxy.name)
        if serialization.format != MetadataSerializationFormats.ESDOC_XML:
            # ESDOC doesn't use schemas; only check this if another format is used
            self.assertEqual(get_attribute_without_namespace(serialized_model, "schemaLocation"), model.version.url)



