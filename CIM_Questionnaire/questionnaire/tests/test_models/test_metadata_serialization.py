####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

import os
import urllib2

from lxml import etree as et

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase

from CIM_Questionnaire.questionnaire.models.metadata_project import MetadataProject
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary, UPLOAD_PATH as VOCABULARY_UPLOAD_PATH
from CIM_Questionnaire.questionnaire.models.metadata_version import MetadataVersion, UPLOAD_PATH as VERSION_UPLOAD_PATH
from CIM_Questionnaire.questionnaire.models.metadata_categorization import MetadataCategorization, UPLOAD_PATH as CATEGORIZATION_UPLOAD_PATH
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy
from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
from CIM_Questionnaire.questionnaire.models.metadata_serialization import MetadataModelSerialization

from CIM_Questionnaire.questionnaire.utils import get_joined_keys_dict

class TestMetadataSerialization(TestQuestionnaireBase):

    def setUp(self):

        super(TestMetadataSerialization, self).setUp()

        cim_document_type = "modelcomponent"

        # have _real_ version 1.8.1 of the CIM handy for these tests
        cim_project = MetadataProject(name="test_cim", title="CIM Project", active=True, authenticated=False)
        cim_project.save()
        project_qs = MetadataProject.objects.all()
        self.assertEqual(len(project_qs), 2)

        cim_vocabulary_path = os.path.join(VOCABULARY_UPLOAD_PATH, "test_atmosphere_bdl.xml")
        cim_vocabulary = MetadataVocabulary(name="cim", file=cim_vocabulary_path, document_type=cim_document_type)
        cim_vocabulary.save()
        vocabulary_qs = MetadataVocabulary.objects.all()
        self.assertEqual(len(vocabulary_qs), 2)

        cim_version_path = os.path.join(VERSION_UPLOAD_PATH, "test_cim_1_8_1.xml")
        cim_version = MetadataVersion(name="cim", file=cim_version_path, url="http://www.purl.org/org/esmetadata/cim/1.8.1/schemas/cim.xsd")
        cim_version.save()
        version_qs = MetadataVersion.objects.all()
        self.assertEqual(len(version_qs), 2)

        cim_categorization_path = os.path.join(CATEGORIZATION_UPLOAD_PATH, "test_esdoc_categorization.xml")
        cim_categorization = MetadataCategorization(name="cim", file=cim_categorization_path)
        cim_categorization.save()
        categorization_qs = MetadataCategorization.objects.all()
        self.assertEqual(len(categorization_qs), 2)

        cim_version.categorization = cim_categorization
        cim_version.save()
        cim_project.vocabularies.add(cim_vocabulary)
        cim_project.save()
        cim_version.register()
        cim_version.save()
        cim_categorization.register()
        cim_categorization.save()
        cim_vocabulary.register()
        cim_vocabulary.save()

        cim_proxy_to_test = MetadataModelProxy.objects.get(version=cim_version, name__iexact=cim_document_type)
        cim_vocabularies_to_test = [cim_vocabulary]

        # setup customizers & realizations...
        (cim_model_customizer, cim_standard_category_customizers, cim_standard_property_customizers, cim_scientific_category_customizers, cim_scientific_property_customizers) = \
            MetadataCustomizer.get_new_customizer_set(cim_project, cim_version, cim_proxy_to_test, cim_vocabularies_to_test)
        # add some one-off customizations as if this had been filled out in the form...
        cim_model_customizer.name = "cim_customizer"
        cim_model_customizer.default = True
        for standard_property_customizer in cim_standard_property_customizers:
            if standard_property_customizer.category is None:
                # TODO: REMOVE THIS AS SOON AS I'VE FIXED ISSUE #71
                standard_property_customizer.displayed = False
        MetadataCustomizer.save_customizer_set(cim_model_customizer, cim_standard_category_customizers, cim_standard_property_customizers, cim_scientific_category_customizers, cim_scientific_property_customizers)
        self.cim_model_customizer = cim_model_customizer

        reordered_cim_standard_property_proxies = [standard_property_customizer.proxy for standard_property_customizer in cim_standard_property_customizers]
        reordered_cim_scientific_property_customizers = get_joined_keys_dict(cim_scientific_property_customizers)
        reordered_cim_scientific_property_proxies = { key : [spc.proxy for spc in value] for key,value in reordered_cim_scientific_property_customizers.items() }

        (cim_models, cim_standard_properties, cim_scientific_properties) = \
            MetadataModel.get_new_realization_set(cim_project, cim_version, cim_proxy_to_test, reordered_cim_standard_property_proxies, reordered_cim_scientific_property_proxies, cim_model_customizer, cim_vocabularies_to_test)
        MetadataModel.save_realization_set(cim_models, cim_standard_properties, cim_scientific_properties)
        self.cim_model_realization = cim_models[0].get_root()

        serialization_qs = MetadataModelSerialization.objects.all()
        self.assertEqual(len(serialization_qs), 0)

        self.cim_model_realization.publish(force_save=True)

        serialization_qs = MetadataModelSerialization.objects.all()
        self.assertEqual(len(serialization_qs), 1)

        self.cim_model_serialization = serialization_qs[0]


    # def test_validate(self):
    #
    #     # TODO: MOVE THIS CODE TO A VALIDATE FN
    #
    #     import ipdb; ipdb.set_trace()
    #     version_url = self.cim_model_realization.version.url
    #     response = urllib2.urlopen(version_url)
    #     content = response.read()
    #     schema = et.XMLSchema(et.XML(content))
    #     parser = et.XMLParser(schema=schema)
    #     serialized_model = et.fromstring(str(self.cim_model_serialization.content), parser)
    #
