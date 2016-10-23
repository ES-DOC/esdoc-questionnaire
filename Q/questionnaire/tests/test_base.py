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

from django.db import models, connection, connections, transaction, DEFAULT_DB_ALIAS
from django.db.models.query import QuerySet
from django.db.models.fields import FieldDoesNotExist
from django.conf import settings
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
import inspect
import os
import pprint

from Q.questionnaire.q_utils import rel
from Q.questionnaire.q_constants import *

#############
# constants #
#############

# most tests use registered ontologies, but the unregistered fixture is still there just in-case...

TEST_UNREGISTERED_FIXTURE_PATH = rel("fixtures/q_testdata_unregistered.json")
TEST_REGISTERED_FIXTURE_PATH = rel("fixtures/q_testdata_registered.json")

# for some tests, I will use "real" (fixture) data
# but for some tests, I want to actually go through the upload/(re)register/delete process
# hence these raw files in TEST_FILE_PATH...

TEST_FILE_PATH = rel("tests/media")

# allows me to "trick" the test runner into thinking the test client sent an AJAX request
TEST_AJAX_REQUEST = {
    "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
}

###############################################
# models used for test-specific functionality #
###############################################

# TODO: THE LOW-LEVEL DETAILS INVOLVED IN THIS CODE MAY BREAK IN FUTURE VERSIONS OF DJANGO

class TestModel(models.Model):
    """
    The base class for test-specific models below;
    These classes are just used for testing, therefore they shouldn't be in the regular db
    hence I define them here rather than the "models" directory and they are unlisted in INSTALLED_APPLICATIONS
    (except that as of v0.16 they are added to INSTALLED_APPS if run in test mode)
    in order to ensure that they get added and removed from the test db (which is loaded initially via fixtures),
    the create_table and delete_table methods are used in setUp and tearDown below
    """

    class Meta:
        # THIS IS IMPORTANT: since migrations have been incorporated into v1.7,
        # I can no longer use the app_label of a listed (and therefore migrated) application;
        # instead, I comment it out and let any subclasses use the local test application
        # TODO: I AM GETTING DEPRECATION WARNINGS ABOUT THIS
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

    @classmethod
    def get_field(cls, field_name):
        """
        convenience fn for getting the Django Field instance from a model class
        note that this is a classmethod; when called from an instance it will just convert that instance to its class
        """
        try:
            field = cls._meta.get_field_by_name(field_name)
            return field[0]
        except FieldDoesNotExist:
            return None

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
        # clear the logfile..
        log_file_name = settings.LOGGING["handlers"]["file"]["filename"]
        open(log_file_name, 'w').close()
        # load fixture data...
        call_command('loaddata', TEST_REGISTERED_FIXTURE_PATH, verbosity=0)
        # setup other data...
        pass

    def setUp(self):

        self.cache = caches[CACHE_ALIAS]
        self.cache.clear()

        self.test_user = User.objects.create_user(
            username="test_user",
            email="allyn.treshansky@colorado.edu",
            password="password",
        )
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="allyn.treshansky@colorado.edu",
            password="password",
        )
        self.assertTrue(self.superuser.is_superuser)

        # factory is useful for creating simple requests
        self.factory = RequestFactory()
        # client is better-suited for most tests, though, b/c it has sessions, cookies, etc.
        self.client = Client()  # enforce_csrf_checks=True)

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

    def assertDictEqual(self, d1, d2, excluded_keys=[], **kwargs):
        """
        Overrides super.assertDictEqual fn to remove certain keys from either list before the comparison
        (uses "**kwargs" b/c sometimes this gets called by built-in Django fns)
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

            try:
                self.assertEqual(d1_type, d2_type, msg=msg)
            except AssertionError:
                # If I was checking strings & unicode objects or querysets & lists then the above assertion would have failed
                # so check those 2 special cases here...
                string_types = [str, unicode, ]
                if d1_type in string_types and d2_type in string_types:
                    self.assertEqual(str(d1_value), str(d2_value))
                elif QuerySet in inspect.getmro(d1_type) or QuerySet in inspect.getmro(d2_type): # lil bit of indirection here b/c custom managers acting as querysets might have been created dynamically
                    self.assertQuerysetEqual(d1_value, d2_value)
                else:
                    # ...and if it still fails, then go ahead and raise the original error
                    raise AssertionError(msg)

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


#################################################
# global fns to create static test content      #
# used when I just want to create these objects #
# w/out testing them                            #
#################################################

def get_test_file_path(file_path):
    """
    returns test-specific path to a given file
    :param file_path:
    :return:
    """
    return os.path.join(TEST_FILE_PATH, file_path)

def create_project(**kwargs):

    from Q.questionnaire.models.models_projects import QProject

    _project_name = kwargs.pop("name")
    _project_title = kwargs.pop("title")
    _project_email = kwargs.pop("email")
    _project_url = kwargs.pop("url", None)
    _project_description = kwargs.pop("description", None)
    _project_authenticated = kwargs.pop("authenticated", False)
    _project_ontologies = kwargs.pop("ontologies", [])

    with transaction.atomic():
        project = QProject(
            name=_project_name,
            title=_project_title,
            email=_project_email,
        )
        if _project_url:
            project.url = _project_url
        if _project_description:
            project.description = _project_description
        if _project_authenticated:
            project.authenticated = _project_authenticated
        project.save()

        for ontology in _project_ontologies:
            project.ontologies.add(ontology)
        project.save()

    return project


def create_categorization(**kwargs):

    from Q.questionnaire.models.models_categorizations import QCategorization

    _filename = kwargs.pop("filename")
    _name = kwargs.pop("name", "test_categorization")
    _version = kwargs.pop("version", 1)
    _description = kwargs.pop("description", None)

    categorization_file_path = kwargs.pop("file_path", os.path.join(TEST_FILE_PATH, _filename))

    with open(categorization_file_path, "r") as categorization_file:

        categorization = QCategorization(
            name=_name,
            version=_version,
            description=_description,
            file=SimpleUploadedFile(categorization_file.name, categorization_file.read())
        )
        categorization.save()

    categorization_file.closed

    return categorization


def remove_categorization(**kwargs):

    categorization = kwargs.pop("categorization")
    categorization.delete()


def create_ontology(**kwargs):

    from Q.questionnaire.models.models_ontologies import QOntology, QOntologyTypes

    _filename = kwargs.pop("filename")
    _type = kwargs.pop("type", QOntologyTypes.SCHEMA.get_type())
    _name = kwargs.pop("name", "test_ontology")
    _version = kwargs.pop("version", 1)
    _description = kwargs.pop("description", None)
    _url = kwargs.pop("url", "http://www.test.com")

    ontology_file_path = kwargs.pop("file_path", os.path.join(TEST_FILE_PATH, _filename))

    with open(ontology_file_path, "r") as ontology_file:

        with transaction.atomic():
            ontology = QOntology(
                name=_name,
                version=_version,
                description=_description,
                url=_url,
                ontology_type=_type,
                file=SimpleUploadedFile(ontology_file.name, ontology_file.read())
            )
            ontology.save()

    ontology_file.closed

    return ontology


def remove_ontology(**kwargs):

    ontology = kwargs.pop("ontology")
    ontology.delete()


# def create_vocabulary(**kwargs):
#
#     from Q.questionnaire.models.models_vocabularies import QVocabulary
#
#     file_path = kwargs.pop("file_path", os.path.join(TEST_FILE_PATH, "test_vocabulary.xml"))
#     _name = kwargs.pop("name", "test_vocabularyogy")
#     _version = kwargs.pop("version", None)
#     _description = kwargs.pop("description", None)
#     _url = kwargs.pop("url", "http://www.test.com")
#     _document_type = kwargs.pop("type", "modelcomponent")
#
#     assert(_document_type in CIM_DOCUMENT_TYPES)
#
#     vocabulary_file = open(file_path)
#     vocabulary = QVocabulary(
#         name=_name,
#         version=_version,
#         description=_description,
#         url=_url,
#         document_type=_document_type,
#         file=SimpleUploadedFile(vocabulary_file.name, vocabulary_file.read())
#     )
#     vocabulary.save()
#     return vocabulary
#
#
# def remove_vocabulary(**kwargs):
#
#     vocabulary = kwargs.pop("vocabulary")
#     vocabulary.delete()

def create_customization(**kwargs):

    # this uses indirection via serializations in order to cope w/ potentially unsaved relationship fields

    from Q.questionnaire.models.models_customizations import get_new_customizations, serialize_new_customizations, set_name, set_owner
    from Q.questionnaire.serializers.serializers_customizations_models import QModelCustomizationSerializer

    _ontology = kwargs.pop("ontology")
    _model_proxy = kwargs.pop("model_proxy")
    _project = kwargs.pop("project")
    _name = kwargs.pop("name", "test_customization")
    _description = kwargs.pop("description", "test description")
    _owner = kwargs.pop("owner")  #, User.objects.get(is_superuser=True))
    _is_default = kwargs.pop("default", True)

    with transaction.atomic():
        customization_model = get_new_customizations(
            project=_project,
            ontology=_ontology,
            model_proxy=_model_proxy,
            key=_model_proxy.name
        )
        customization_model.description = _description
        customization_model.is_default = _is_default

        # this copies the relevant info to all customizations in the hierarchy...
        # (outside of the testing framework, this would have been done automatically on the client)
        set_name(customization_model, _name)
        set_owner(customization_model, _owner)

        customization_data = serialize_new_customizations(customization_model)
        customization_serializer = QModelCustomizationSerializer(
            data=customization_data
        )

        assert customization_serializer.is_valid(), "Invalid QModelCustomizationSerializer (in create_customization)"

        return customization_serializer.save()


def create_realization(**kwargs):

    # this uses indirection via serializations in order to cope w/ potentially unsaved relationship fields

    from Q.questionnaire.models.models_realizations import get_new_realizations, serialize_new_realizations, set_owner
    from Q.questionnaire.serializers.serializers_realizations_models import QModelRealizationSerializer

    _ontology = kwargs.pop("ontology")
    _model_proxy = kwargs.pop("model_proxy")
    _project = kwargs.pop("project")
    _owner = kwargs.pop("owner")  #, User.objects.get(is_superuser=True))

    with transaction.atomic():
        realization_model = get_new_realizations(
            project=_project,
            ontology=_ontology,
            model_proxy=_model_proxy,
            key=_model_proxy.name
        )

        # this copies the relevant info to all realizations in the hierarchy...
        # (outside of the testing framework, this would have been done automatically on the client)
        set_owner(realization_model, _owner)

        realization_data = serialize_new_realizations(realization_model)
        realization_serializer = QModelRealizationSerializer(
            data=realization_data
        )

        assert realization_serializer.is_valid(), "Invalid QModelRealizationSerializer (in create_realization)"

        return realization_serializer.save()



