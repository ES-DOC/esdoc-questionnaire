
import os

from django.test import RequestFactory, Client, TestCase


from CIM_Questionnaire.questionnaire.models.metadata_authentication import MetadataUser
from CIM_Questionnaire.questionnaire.models.metadata_site import MetadataSite

from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import UPLOAD_PATH as VOCABULARY_UPLOAD_PATH
from CIM_Questionnaire.questionnaire.models.metadata_version import UPLOAD_PATH as VERSION_UPLOAD_PATH
from CIM_Questionnaire.questionnaire.models.metadata_categorization import UPLOAD_PATH as CATEGORIZATION_UPLOAD_PATH

class TestQuestionnaireBase(TestCase):
    """
     The base class for all CIM Questionnaire tests
     provides a reusable test client
     and a default user, site, version, categorization, vocabulary
     as well as default proxies, customizers, and models
     to play with in child classes
    """

    def setUp(self):

        # request factory for all tests
        self.factory = RequestFactory()
        # client for all tests (this is better-suited for testing views b/c, among other things, it has sessions, cookies, etc.)
        self.client = Client()#enforce_csrf_checks=True)

        #
        # # ensure that there are no categorizations before a new one is loaded
        # qs = MetadataCategorization.objects.all()
        # self.assertEqual(len(qs),0)
        #
        # # create a categorization
        # test_categorization_name = "test_categorization.xml"
        # test_categorization = MetadataCategorization(name="test",file=os.path.join(CATEGORIZATION_UPLOAD_PATH,test_categorization_name))
        # test_categorization.save()
        #
        # # ensure the categorization is saved to the database
        # qs = MetadataCategorization.objects.all()
        # self.assertEqual(len(qs),1)
        #
        # # ensure that there are no versions before a new one is loaded
        # qs = MetadataVersion.objects.all()
        # self.assertEqual(len(qs),0)
        #
        # # create a version
        # test_version_name = "test_version.xml"
        # test_version = MetadataVersion(name="test",file=os.path.join(VERSION_UPLOAD_PATH,test_version_name))
        # test_version.categorization = test_categorization   # associate the "test" categorization w/ the "test" version
        # test_version.save()
        #
        # # ensure the version is saved to the database
        # qs = MetadataVersion.objects.all()
        # self.assertEqual(len(qs),1)
        #
        # # ensure that there are no categorizations before a new one is loaded
        # qs = MetadataVocabulary.objects.all()
        # self.assertEqual(len(qs),0)
        #
        # # create a vocabulary
        # test_vocabulary_name = "test_vocabulary.xml"
        # test_vocabulary = MetadataVocabulary(name="test",file=os.path.join(VOCABULARY_UPLOAD_PATH,test_vocabulary_name))
        # test_vocabulary.document_type = "modelcomponent"
        # test_vocabulary.save()
        #
        # # ensure the version is saved to the database
        # qs = MetadataVocabulary.objects.all()
        # self.assertEqual(len(qs),1)
        #
        # # ensure that there are no projects before a new one is loaded
        # qs = MetadataProject.objects.all()
        # self.assertEqual(len(qs),0)
        #
        # # create a project
        # test_project = MetadataProject(name="test",title="Test")
        # test_project.save()
        #
        # # ensure the project is saved to the database
        # qs = MetadataProject.objects.all()
        # self.assertEqual(len(qs),1)
        #
        # # register a version
        # self.assertEqual(test_version.registered,False)
        # test_version.register()
        # test_version.save()
        # self.assertEqual(test_version.registered,True)
        #
        # # register a categorization
        # self.assertEqual(test_categorization.registered,False)
        # test_categorization.register()
        # test_categorization.save()
        # self.assertEqual(test_categorization.registered,True)
        #
        # # register a vocabulary
        # self.assertEqual(test_vocabulary.registered,False)
        # test_vocabulary.register()
        # test_vocabulary.save()
        # self.assertEqual(test_vocabulary.registered,True)
        #
        # # setup a project w/ a vocabulary
        # test_project.vocabularies.add(test_vocabulary)
        # test_project.save()
        #
        # # ensure that there are no customizers before a new one is loaded
        # qs = MetadataModelCustomizer.objects.all()
        # self.assertEqual(len(qs),0)
        #
        # # create a default customizer set
        # # (note, other customizers w/ other features will be used throughout the testing suite;
        # # this is just the default one where customizers need to exist for other functionallity to be tested)
        # test_model_name = "modelcomponent"
        # model_proxy_to_be_customized = MetadataModelProxy.objects.get(version=test_version,name__iexact=test_model_name)
        # vocabularies_to_be_customized = test_project.vocabularies.filter(document_type__iexact=test_model_name)
        # (test_model_customizer,test_standard_category_customizers,test_standard_property_customizers,test_scientific_category_customizers,test_scientific_property_customizers) = \
        #     MetadataCustomizer.get_new_customizer_set(test_project, test_version, model_proxy_to_be_customized, vocabularies_to_be_customized)
        # test_model_customizer.name = "test"
        # test_model_customizer.default = True
        # MetadataCustomizer.save_customizer_set(test_model_customizer,test_standard_category_customizers,test_standard_property_customizers,test_scientific_category_customizers,test_scientific_property_customizers)
        #
        # # ensure the customizer set is saved to the database
        # qs = MetadataModelCustomizer.objects.all()
        # self.assertEqual(len(qs),1)
        #
        # self.version        = test_version
        # self.categorization = test_categorization
        # self.vocabulary     = test_vocabulary
        # self.project        = test_project
        # self.customizer     = test_model_customizer


    def assertQuerysetEqual(self, qs1, qs2):
        """Tests that two django querysets are equal"""
        # the built-in TestCase method takes a qs and a list, which is confusing
        # this is more intuitive (see https://djangosnippets.org/snippets/2013/)

        pk = lambda o: o.pk
        return self.assertEqual(
            list(sorted(qs1, key=pk)),
            list(sorted(qs2, key=pk))
        )

