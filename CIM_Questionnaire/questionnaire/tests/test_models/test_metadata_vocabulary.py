import os

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase

from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import UPLOAD_PATH as VOCABULARY_UPLOAD_PATH

from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataScientificCategoryProxy, MetadataScientificPropertyProxy, MetadataComponentProxy

from CIM_Questionnaire.questionnaire.utils import CIM_DOCUMENT_TYPES

class TestMetadataVocabulary(TestQuestionnaireBase):

    def setUp(self):
        # don't call TestQuestionnaireBase.setUp() so that the db is empty

        test_document_type = "modelcomponent"
        self.assertIn(test_document_type, CIM_DOCUMENT_TYPES, msg="Unrecognized vocabulary document type: %s" % (test_document_type))
        test_vocabulary_path = os.path.join(VOCABULARY_UPLOAD_PATH, "test_vocabulary_bdl.xml")
        test_vocabulary = MetadataVocabulary(name="vocabulary", file=test_vocabulary_path, document_type=test_document_type)
        test_vocabulary.save()
        vocabulary_qs = MetadataVocabulary.objects.all()
        self.assertEqual(len(vocabulary_qs), 1)

    def test_register_components(self):

        components = MetadataComponentProxy.objects.all()

        excluded_fields = ["tree_id", "lft", "rght", "level", "parent",] # ignore mptt fields
        serialized_components = [self.fully_serialize_model(component,exclude=excluded_fields) for component in components]

        # I AM HERE
        #
        # test_components_data = [
        #     {'order': 1, 'documentation': u'Definition of component type Atmosphere required', 'name': u'atmosphere', "vocabulary" : test_vocabulary, },
        #     {'order': 2, 'documentation': u'Definition of component type AtmosKeyProperties required', 'name': u'atmoskeyproperties'},
        #     {'order': 3, 'documentation': u'Definition of component type TopOfAtmosInsolation required', 'name': u'topofatmosinsolation'},
        #     {'order': 4, 'documentation': u'Definition of component type AtmosSpaceConfiguration required', 'name': u'atmosspaceconfiguration'},
        #     {'order': 5, 'documentation': u'Definition of component type AtmosHorizontalDomain required', 'name': u'atmoshorizontaldomain'},
        #     {'order': 6, 'documentation': u'Definition of component type AtmosDynamicalCore required', 'name': u'atmosdynamicalcore'},
        #     {'order': 7, 'documentation': u'Definition of component type AtmosAdvection required', 'name': u'atmosadvection'},
        #     {'order': 8, 'documentation': u'Definition of component type AtmosRadiation required', 'name': u'atmosradiation'},
        #     {'order': 9, 'documentation': u'Definition of component type AtmosConvectTurbulCloud required', 'name': u'atmosconvectturbulcloud'},
        #     {'order': 10, 'documentation': u'Definition of component type AtmosCloudScheme required', 'name': u'atmoscloudscheme'},
        #     {'order': 11, 'documentation': u'Definition of component type CloudSimulator required', 'name': u'cloudsimulator'},
        #     {'order': 12, 'documentation': u'Definition of component type AtmosOrographyAndWaves required', 'name': u'atmosorographyandwaves'}
        # ]
        #
        # # test that the components have the expected standard fields
        # for s,t in zip(serialized_components,test_components_data):
        #     self.assertDictEqual(s,t)

