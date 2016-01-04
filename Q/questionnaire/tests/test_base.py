####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

from django.db import models, connection, connections, DEFAULT_DB_ALIAS
from django.db.models.query import QuerySet
from django.core.management import call_command
from django.core.management.color import no_style
from django.core.cache import caches
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.test.client import RequestFactory
from django.test.utils import CaptureQueriesContext
from unittest.util import safe_repr
from difflib import ndiff
import os
import pprint

from Q.questionnaire.q_utils import rel
from Q.questionnaire.q_constants import *

#############
# constants #
#############

TEST_FIXTURE_PATH = rel("fixtures/q_testdata.json")

# for most tests, I will use "real" (fixture) data
# but for some tests, I want to actually go through the upload/(re)register/delete process
# hence these files...

TEST_FILE_PATH = rel("tests/samples")
TEST_FILES = [
    "test_categorization.xml",
    "test_ontology.xml",
    "test_vocabulary.xml",
]

###############################################
# models used for test-specific functionality #
###############################################

# TODO: THE LOW-LEVEL DETAILS INVOLVED IN THIS CODE MAY BREAK IN FUTURE VERSIONS OF DJANGO

class TestModel(models.Model):
    """
    The base class for test-specific models below;
    These classes are just used for testing, therefore they shouldn't be in the regular db
    hence I define them here rather than the "models" directory and they are unlisted in INSTALLED_APPLICATIONS
    in order to ensure that they get added and removed from the test db (which is loaded initially via fixtures),
    the create_table and delete_table methods are used in setUp and tearDown below
    (got the idea from http://datahackermd.com/2013/testing-django-fields/)
    """

    class Meta:
        # THIS IS IMPORTANT: since migrations have been incorporated into v1.7,
        # I can no longer use the app_label of a listed (and therefore migrated) application;
        # instead, I comment it out and let any subclasses use the local test application
        # app_label = APP_LABEL
        abstract = True

    create_fn_name = "create_table"
    delete_fn_name = "delete_table"

    @classmethod
    def create_table(cls):
        table_name = cls._meta.db_table
        raw_sql, refs = connection.creation.sql_create_model(cls, no_style(), [])
        sql = u'\n'.join(raw_sql).encode('utf-8')
        cls.delete_table()
        cursor = connection.cursor()
        try:
            cursor.execute(sql)
        finally:
            cursor.close()

    @classmethod
    def delete_table(cls):
        table_name = cls._meta.db_table
        cursor = connection.cursor()
        try:
            # cursor.execute('DROP TABLE IF EXISTS %s' % table_name)
            cursor.execute("DROP TABLE IF EXISTS {0}".format(table_name))
        except:
            # Catch anything backend-specific here.
            # (E.g., MySQL raises a warning if the table didn't exist.)
            pass
        finally:
            cursor.close()


##########################################
# a way of testing the number of queries #
# performed during an operation          #
##########################################

class QueryCounter(CaptureQueriesContext):
    """
    provides a context manager for me to keep track of the number of queries
    (not to be confused w/ assertNumQueries)

    usage is:
    >> test_query_counter = QueryCounter()
    >> with test_query_counter:
    >>     do_some_stuff()
    >>     test_query_count = test_query_counter.get_num_queries()
    """

    def __init__(self):
        conn = connections[DEFAULT_DB_ALIAS]
        super(QueryCounter, self).__init__(conn)

    def reset(self):
        self.initial_queries = 0
        self.final_queries = None

    def get_num_queries(self):
        try:
            num_queries = len(self.captured_queries)
            return num_queries
        except AttributeError:
            return 0


####################################
# a decorator for incomplete tests #
####################################

def incomplete_test(func):
    """
    decorator fn for incomplete tests
    :param func:
    :return:
    """
    def func_wrapper(self):
        msg = u'"{0}" is incomplete.'.format(func.__name__)
        raise NotImplementedError(msg)
    return func_wrapper


#########################
# the actual test class #
#########################

class TestQBase(TestCase):

    """
     The base class for all Questionnaire tests
     provides a reusable test client
     and some convenience fns for testing
    """

    maxDiff = None  # display full errors regardless of size
    # fixtures = ['q_testdata.json']  # using setUpTestData below instead of globally declaring fixtures here

    @classmethod
    def setUpTestData(cls):
        # load fixture data...
        call_command('loaddata', TEST_FIXTURE_PATH, verbosity=0)
        # setup other data...
        pass

    def setUp(self):

        self.cache = caches[CACHE_ALIAS]
        self.cache.clear()

        self.test_user = User.objects.create_user(
            username="test_user",
            email="allyn.treshansky@noaa.gov",
            password="password",
        )
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="allyn.treshansky@noaa.gov",
            password="password",
        )
        self.assertTrue(self.superuser.is_superuser)

        # factory is useful for creating simple requests
        self.factory = RequestFactory()
        # client is better-suited for most tests, though, b/c, among other things, it has sessions, cookies, etc.
        self.client = Client()  # enforce_csrf_checks=True)

        # self.cim_1_8_1_version = MetadataVersion.objects.get(name="cim", version="1.8.1")
        # self.cim_1_8_1_categorization = self.cim_1_8_1_version.categorization
        # self.cim_1_10_version = MetadataVersion.objects.get(name="cim", version="1.10")
        # self.cim_1_10_categorization = self.cim_1_10_version.categorization
        #
        # self.model_component_proxy = MetadataModelProxy.objects.get(version=self.cim_1_10_version, name__iexact="modelcomponent")
        #
        # self.atmosphere_vocabulary = MetadataVocabulary.objects.get(name__iexact="atmosphere")
        # self.landsurface_vocabulary = MetadataVocabulary.objects.get(name__iexact="landsurface")
        # self.statisticaldownscaling_vocabulary = MetadataVocabulary.objects.get(name__iexact="statisticaldownscaling")
        # self.modelinfrastructure_vocabulary = MetadataVocabulary.objects.get(name__iexact="modelinfrastructure")
        #
        # self.downscaling_project = MetadataProject.objects.get(name="downscaling")
        # downscaling_model_component_customizer = MetadataModelCustomizer.objects.get(project=self.downscaling_project, proxy=self.model_component_proxy, name="default")
        # downscaling_model_component_customizer_with_subforms = MetadataModelCustomizer.objects.get(project=self.downscaling_project, proxy=self.model_component_proxy, name="subforms")
        # self.downscaling_model_component_vocabularies = downscaling_model_component_customizer.get_sorted_vocabularies()
        #
        # (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
        #     MetadataCustomizer.get_existing_customizer_set(downscaling_model_component_customizer, self.downscaling_model_component_vocabularies)
        #
        # (model_customizer_with_subforms, standard_category_customizers_with_subforms, standard_property_customizers_with_subforms, nested_scientific_category_customizers_with_subforms, nested_scientific_property_customizers_with_subforms) = \
        #     MetadataCustomizer.get_existing_customizer_set(downscaling_model_component_customizer_with_subforms, self.downscaling_model_component_vocabularies)
        #
        # self.downscaling_model_component_customizer_set = {
        #     "model_customizer": model_customizer,
        #     "standard_category_customizers": standard_category_customizers,
        #     "standard_property_customizers": standard_property_customizers,
        #     "scientific_category_customizers": get_joined_keys_dict(nested_scientific_category_customizers),
        #     "scientific_property_customizers": get_joined_keys_dict(nested_scientific_property_customizers),
        # }
        #
        # self.downscaling_model_component_customizer_set_with_subforms = {
        #     "model_customizer": model_customizer_with_subforms,
        #     "standard_category_customizers": standard_category_customizers_with_subforms,
        #     "standard_property_customizers": standard_property_customizers_with_subforms,
        #     "scientific_category_customizers": get_joined_keys_dict(nested_scientific_category_customizers_with_subforms),
        #     "scientific_property_customizers": get_joined_keys_dict(nested_scientific_property_customizers_with_subforms),
        # }
        #
        # self.downscaling_model_component_proxy_set = {
        #     "model_proxy": self.model_component_proxy,
        #     "standard_property_proxies": [standard_property_customizer.proxy for standard_property_customizer in self.downscaling_model_component_customizer_set["standard_property_customizers"]],
        #     "scientific_property_proxies": {key: [spc.proxy for spc in value] for key, value in self.downscaling_model_component_customizer_set["scientific_property_customizers"].items()},
        # }
        #
        # downscaling_model_component_realizations = MetadataModel.objects.get(project=self.downscaling_project, pk=1).get_descendants(include_self=True)
        # (models, standard_properties, scientific_properties) = \
        #     MetadataModel.get_existing_realization_set(downscaling_model_component_realizations, self.downscaling_model_component_customizer_set["model_customizer"], vocabularies=self.downscaling_model_component_vocabularies)
        #
        # self.downscaling_model_component_realization_set = {
        #     "models": models,
        #     "standard_properties": standard_properties,
        #     "scientific_properties": scientific_properties,
        # }
        #
        # self.esfdl_project = MetadataProject.objects.get(name="es-fdl")
        # esfdl_model_component_customizer = MetadataModelCustomizer.objects.get(project=self.esfdl_project, proxy=self.model_component_proxy, name="default")
        # self.esfdl_model_component_vocabularies = esfdl_model_component_customizer.get_sorted_vocabularies()
        #
        # (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
        #     MetadataCustomizer.get_existing_customizer_set(esfdl_model_component_customizer, self.esfdl_model_component_vocabularies)
        #
        # self.esfdl_model_component_customizer_set = {
        #     "model_customizer": model_customizer,
        #     "standard_category_customizers": standard_category_customizers,
        #     "standard_property_customizers": standard_property_customizers,
        #     "scientific_category_customizers": get_joined_keys_dict(nested_scientific_category_customizers),
        #     "scientific_property_customizers": get_joined_keys_dict(nested_scientific_property_customizers),
        # }
        #
        # self.esfdl_model_component_proxy_set = {
        #     "model_proxy": self.model_component_proxy,
        #     "standard_property_proxies": [standard_property_customizer.proxy for standard_property_customizer in self.esfdl_model_component_customizer_set["standard_property_customizers"]],
        #     "scientific_property_proxies": {key: [spc.proxy for spc in value] for key, value in self.esfdl_model_component_customizer_set["scientific_property_customizers"].items()},
        # }
        #
        # esfdl_model_component_realizations = MetadataModel.objects.filter(project=self.esfdl_project)
        # (models, standard_properties, scientific_properties) = \
        #     MetadataModel.get_existing_realization_set(esfdl_model_component_realizations, self.esfdl_model_component_customizer_set["model_customizer"], vocabularies=self.esfdl_model_component_vocabularies)
        #
        # self.esfdl_model_component_realization_set = {
        #     "models": models,
        #     "standard_properties": standard_properties,
        #     "scientific_properties": scientific_properties,
        # }

    def tearDown(self):
        # this is for resetting things that are not db-related (ie: files, etc.)
        # but it's not needed for the db since each test is run in its own transaction
        pass

    ##############################
    # some additional assertions #
    ##############################

    def assertQuerysetEqual(self, qs1, qs2):
        """Tests that two django querysets are equal"""
        # the built-in TestCase method takes a qs and a list, which is confusing
        # this is more intuitive (see https://djangosnippets.org/snippets/2013/)

        pk = lambda o: o.pk
        return self.assertEqual(
            list(sorted(qs1, key=pk)),
            list(sorted(qs2, key=pk)),
        )

    def assertDictEqual(self, d1, d2, excluded_keys=[]):
        """
        Overrides super.assertDictEqual fn to remove certain keys from either list before the comparison
        """

        self.assertIsInstance(d1, dict, 'First argument is not a dictionary')
        self.assertIsInstance(d2, dict, 'Second argument is not a dictionary')

        d1_copy = d1.copy()
        d2_copy = d2.copy()
        for key_to_exclude in excluded_keys:
            d1_copy.pop(key_to_exclude, None)
            d2_copy.pop(key_to_exclude, None)

        msg = "{0} != {1}".format(safe_repr(d1_copy, True), safe_repr(d2_copy, True))
        diff = ('\n' + '\n'.join(ndiff(
            pprint.pformat(d1_copy).splitlines(),
            pprint.pformat(d2_copy).splitlines())))
        msg = self._truncateMessage(msg, diff)

        d1_keys = d1_copy.keys()
        d2_keys = d2_copy.keys()
        self.assertSetEqual(set(d1_keys), set(d2_keys), msg=msg)  # comparing as a set b/c order is irrelevant

        for key in d1_keys:
            d1_value = d1_copy[key]
            d2_value = d2_copy[key]
            # I am doing this instead of just calling super()
            # b/c Django doesn't consider querysets to be equal even if they point to the same thing
            # (see http://stackoverflow.com/questions/16058571/comparing-querysets-in-django-testcase)
            d1_type = type(d1_value)
            d2_type = type(d2_value)
            self.assertEqual(d1_type, d2_type)

            # try:
            #     self.assertEqual(d1_type, d2_type, msg=msg)
            # except AssertionError:
            #     # I need a quick check just in case I am comparing different types of strings
            #     string_types = [str, unicode, ]
            #     if not (d1_type in string_types and d2_type in string_types):
            #         raise AssertionError(msg)

            if d1_type == QuerySet:
                self.assertQuerysetEqual(d1_value, d2_value)
            else:
                self.assertEqual(d1_value, d2_value)

    def assertFileExists(self, file_path, **kwargs):
        """Tests that a file exists"""

        msg = kwargs.pop("msg", None)
        file_exists = os.path.exists(file_path)

        return self.assertTrue(file_exists, msg=msg)

    def assertFileDoesntExist(self, file_path, **kwargs):
        """Tests that a file doesn't exist"""

        msg = kwargs.pop("msg", None)
        file_exists = os.path.exists(file_path)

        return self.assertFalse(file_exists, msg=msg)


############################################
# global fns to create static test content #
############################################

def create_categorization(**kwargs):

    from Q.questionnaire.models.models_categorizations import QCategorization

    file_path = kwargs.pop("file_path", os.path.join(TEST_FILE_PATH, "test_categorization.xml"))
    _name = kwargs.pop("name", "test_categorization")
    _version = kwargs.pop("version", None)
    _description = kwargs.pop("description", None)

    categorization_file = open(file_path)
    categorization = QCategorization(
        name=_name,
        version=_version,
        description=_description,
        file=SimpleUploadedFile(categorization_file.name, categorization_file.read())
    )
    categorization.save()
    return categorization


def remove_categorization(**kwargs):

    categorization = kwargs.pop("categorization")
    categorization.delete()


def create_ontology(**kwargs):

    from Q.questionnaire.models.models_ontologies import QOntology, CIMTypes

    file_path = kwargs.pop("file_path", os.path.join(TEST_FILE_PATH, "test_ontology.xml"))
    _name = kwargs.pop("name", "test_ontology")
    _version = kwargs.pop("version", 1)
    _description = kwargs.pop("description", None)
    _url = kwargs.pop("url", "http://www.test.com")
    _type = kwargs.pop("type", CIMTypes.CIM1.get_type())

    ontology_file = open(file_path)
    ontology = QOntology(
        name=_name,
        version=_version,
        description=_description,
        url=_url,
        type=_type,
        file=SimpleUploadedFile(ontology_file.name, ontology_file.read())
    )
    ontology.save()
    return ontology


def remove_ontology(**kwargs):

    ontology = kwargs.pop("ontology")
    ontology.delete()


def create_vocabulary(**kwargs):

    from Q.questionnaire.models.models_vocabularies import QVocabulary

    file_path = kwargs.pop("file_path", os.path.join(TEST_FILE_PATH, "test_vocabulary.xml"))
    _name = kwargs.pop("name", "test_vocabularyogy")
    _version = kwargs.pop("version", None)
    _description = kwargs.pop("description", None)
    _url = kwargs.pop("url", "http://www.test.com")
    _document_type = kwargs.pop("type", "modelcomponent")

    assert(_document_type in CIM_DOCUMENT_TYPES)

    vocabulary_file = open(file_path)
    vocabulary = QVocabulary(
        name=_name,
        version=_version,
        description=_description,
        url=_url,
        document_type=_document_type,
        file=SimpleUploadedFile(vocabulary_file.name, vocabulary_file.read())
    )
    vocabulary.save()
    return vocabulary


def remove_vocabulary(**kwargs):

    vocabulary = kwargs.pop("vocabulary")
    vocabulary.delete()