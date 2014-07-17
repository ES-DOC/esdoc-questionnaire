import os

from django.test import RequestFactory, Client, TestCase

from django.contrib.auth.models import User

from CIM_Questionnaire.questionnaire.models.metadata_authentication import MetadataUser, get_metadata_user
from CIM_Questionnaire.questionnaire.models.metadata_project import MetadataProject
from CIM_Questionnaire.questionnaire.models.metadata_version import MetadataVersion
from CIM_Questionnaire.questionnaire.models.metadata_categorization import MetadataCategorization
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy, MetadataStandardCategoryProxy, MetadataScientificCategoryProxy, MetadataStandardPropertyProxy, MetadataScientificPropertyProxy, MetadataComponentProxy
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer, MetadataModelCustomizer, MetadataStandardCategoryCustomizer, MetadataScientificCategoryCustomizer, MetadataStandardPropertyCustomizer, MetadataScientificPropertyCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel, MetadataStandardProperty, MetadataScientificProperty

from CIM_Questionnaire.questionnaire.models.metadata_version import UPLOAD_PATH as VERSION_UPLOAD_PATH
from CIM_Questionnaire.questionnaire.models.metadata_categorization import UPLOAD_PATH as CATEGORIZATION_UPLOAD_PATH
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import UPLOAD_PATH as VOCABULARY_UPLOAD_PATH

from CIM_Questionnaire.questionnaire.views import *

from CIM_Questionnaire.questionnaire.utils import CIM_DOCUMENT_TYPES


class TestQuestionnaireBase(TestCase):

    """
     The base class for all CIM Questionnaire tests
     provides a reusable test client
     and a default user, project, version, categorization, vocabulary
     as well as default proxies, customizers, and realizations
     to play with in child classes
    """

    def setUp(self):

        # request factory for all tests
        self.factory = RequestFactory()
        # client for all tests (this is better-suited for testing views b/c, among other things, it has sessions, cookies, etc.)
        self.client = Client()#enforce_csrf_checks=True)

        # SETUP DEFAULT TEST USER & SUPERUSER
        test_user = User.objects.create_user("test", "a@b.com", "test")
        test_superuser = User.objects.create_superuser("admin", "a@b.com", "admin")
        user_qs = User.objects.all()
        self.assertEqual(len(user_qs),2)
        self.assertIsNotNone(get_metadata_user(test_user), msg="MetadataUser not created after the User.objects.create_user() fn")
        self.user = test_user
        self.super_user = test_superuser

        # SETUP DEFAULT PROJECT
        test_project = MetadataProject(name="project", title="Test Project", active=True, authenticated=False)
        test_project.save()
        project_qs = MetadataProject.objects.all()
        self.assertEqual(len(project_qs), 1)
        self.project = test_project

        # SETUP DEFAULT VERSION
        test_version_path = os.path.join(VERSION_UPLOAD_PATH, "test_version.xml")
        test_version = MetadataVersion(name="version", file=test_version_path)
        test_version.save()
        version_qs = MetadataVersion.objects.all()
        self.assertEqual(len(version_qs), 1)
        self.version = test_version

        # SETUP DEFAULT CATEGORIZATION
        test_categorization_path = os.path.join(CATEGORIZATION_UPLOAD_PATH, "test_categorization.xml")
        test_categorization = MetadataCategorization(name="categorization", file=test_categorization_path)
        test_categorization.save()
        categorization_qs = MetadataCategorization.objects.all()
        self.assertEqual(len(categorization_qs), 1)
        self.categorization = test_categorization

        # SETUP DEFAULT VOCABULARY
        test_document_type = "modelcomponent"
        self.assertIn(test_document_type, CIM_DOCUMENT_TYPES, msg="Unrecognized vocabulary document type: %s" % (test_document_type))
        test_vocabulary_path = os.path.join(VOCABULARY_UPLOAD_PATH, "test_vocabulary_bdl.xml")
        test_vocabulary = MetadataVocabulary(name="vocabulary", file=test_vocabulary_path, document_type=test_document_type)
        test_vocabulary.save()
        vocabulary_qs = MetadataVocabulary.objects.all()
        self.assertEqual(len(vocabulary_qs), 1)
        self.vocabulary = test_vocabulary

        # SETUP RELATIONS AMONG THOSE DEFAULT OBJECTS
        test_version.categorization = test_categorization
        test_version.save()
        test_project.vocabularies.add(test_vocabulary)
        test_project.save()

        # REGISTER THE DEFAULT OBJECTS TO GET PROXIES
        test_version.register()
        test_version.save()
        test_categorization.register()
        test_categorization.save()
        test_vocabulary.register()
        test_vocabulary.save()
        model_proxy_qs = MetadataModelProxy.objects.all()
        standard_category_proxy_qs = MetadataStandardCategoryProxy.objects.all()
        scientific_category_proxy_qs = MetadataScientificCategoryProxy.objects.all()
        standard_property_proxy_qs = MetadataStandardPropertyProxy.objects.all()
        scientific_property_proxy_qs = MetadataScientificPropertyProxy.objects.all()
        component_proxy_qs = MetadataComponentProxy.objects.all()
        self.assertEqual(len(model_proxy_qs), 3, msg="Unexpected number of MetadataModelProxy.  Did you change %s" % (test_version.file.path))
        self.assertEqual(len(standard_category_proxy_qs), 3, msg="Unexpected number of MetadataStandardCategoryProxy.  Did you change %s" % (test_version.file.path))
        self.assertEqual(len(scientific_category_proxy_qs), 10, msg="Unexpected number of MetadataScientificCategoryProxy.  Did you change %s" % (test_vocabulary.file.path))
        self.assertEqual(len(standard_property_proxy_qs), 11, msg="Unexpected number of MetadataStandardPropertyProxy.  Did you change %s" % (test_version.file.path))
        self.assertEqual(len(scientific_property_proxy_qs), 9, msg="Unexpected number of MetadataScientificCategoryProxy.  Did you change %s" % (test_vocabulary.file.path))
        self.assertEqual(len(component_proxy_qs), 5, msg="Unexpected number of MetadataComponentProxy.  Did you change %s" % (test_vocabulary.file.path))

        proxy_to_test = test_version.model_proxies.get(name__iexact=test_document_type)
        vocabularies_to_test = test_project.vocabularies.filter(document_type__iexact=test_document_type)

        # SETUP DEFAULT CUSTOMIZERS
        (test_model_customizer, test_standard_category_customizers, test_standard_property_customizers, test_scientific_category_customizers, test_scientific_property_customizers) = \
            MetadataCustomizer.get_new_customizer_set(test_project, test_version, proxy_to_test, vocabularies_to_test)
        test_model_customizer.name = "customizer"
        test_model_customizer.default = True
        MetadataCustomizer.save_customizer_set(test_model_customizer, test_standard_category_customizers, test_standard_property_customizers, test_scientific_category_customizers, test_scientific_property_customizers)
        model_customizer_qs = MetadataModelCustomizer.objects.all()
        standard_category_customizer_qs = MetadataStandardCategoryCustomizer.objects.all()
        scientific_category_customizer_qs = MetadataScientificCategoryCustomizer.objects.all()
        standard_property_customizer_qs = MetadataStandardPropertyCustomizer.objects.all()
        scientific_property_customizer_qs = MetadataScientificPropertyCustomizer.objects.all()
        self.assertEqual(len(model_customizer_qs), 1)
        self.assertEqual(len(standard_category_customizer_qs), 3)
        self.assertEqual(len(scientific_category_customizer_qs), 10)
        self.assertEqual(len(standard_property_customizer_qs), 7)
        self.assertEqual(len(scientific_property_customizer_qs), 9)
        self.model_customizer = test_model_customizer

        # SETUP DEFAULT REALIZATIONS
        reordered_test_standard_property_proxies = [standard_property_customizer.proxy for standard_property_customizer in test_standard_property_customizers]
        reordered_test_scientific_property_proxies = {}
        for vocabulary_key,scientific_property_customizer_dict in test_scientific_property_customizers.iteritems():
            for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
                model_key = u"%s_%s" % (vocabulary_key, component_key)
                reordered_test_scientific_property_proxies[model_key] = [scientific_property_customizer.proxy for scientific_property_customizer in scientific_property_customizer_list]
        (test_models, test_standard_properties, test_scientific_properties) = \
            MetadataModel.get_new_realization_set(test_project, test_version, proxy_to_test, reordered_test_standard_property_proxies, reordered_test_scientific_property_proxies, test_model_customizer, vocabularies_to_test)
        MetadataModel.save_realization_set(test_models,test_standard_properties,test_scientific_properties)
        model_qs = MetadataModel.objects.all()
        standard_property_qs = MetadataStandardProperty.objects.all()
        scientific_property_qs = MetadataScientificProperty.objects.all()
        self.assertEqual(len(model_qs), 6)
        self.assertEqual(len(standard_property_qs), 42)
        self.assertEqual(len(scientific_property_qs), 9)
        self.model_realization = test_models[0].get_root()


    def assertQuerysetEqual(self, qs1, qs2):
        """Tests that two django querysets are equal"""
        # the built-in TestCase method takes a qs and a list, which is confusing
        # this is more intuitive (see https://djangosnippets.org/snippets/2013/)

        pk = lambda o: o.pk
        return self.assertEqual(
            list(sorted(qs1, key=pk)),
            list(sorted(qs2, key=pk))
        )

    def assertFileExists(self, file_path, **kwargs):
        """Tests that a file exists"""

        msg = kwargs.pop("msg",None)
        file_exists = os.path.exists(file_path)

        return self.assertEqual(file_exists,True,msg=msg)

    def get_new_edit_forms(self):

        project_name = self.project.name,
        version_name = self.version.name,
        model_name = self.model_realization.name,

        request_url = reverse("edit_new", kwargs = {
            "project_name" : "project",
            "version_name" : "version",
            "model_name" : "modelcomponent",
        })

        response = self.client.get(request_url, follow=True)
        context = response.context

        import ipdb; ipdb.set_trace()

        self.assertEqual(response.status_code,200)

        model_formset = response.context["model_formset"]
        standard_properties_formsets = response.context["standard_properties_formsets"]
        scientific_properties_formsets = response.context["scientific_properties_formsets"]

        return (model_formset, standard_properties_formsets, scientific_properties_formsets)
