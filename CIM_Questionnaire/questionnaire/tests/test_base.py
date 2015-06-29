import os
import json
import pprint

from django.test.client import RequestFactory
from django.test import TestCase, Client
from django.test.utils import CaptureQueriesContext
from unittest.util import safe_repr
from difflib import ndiff

from django.core.cache import get_cache
from django.core.management.color import no_style
from django.db import models, connection, connections, DEFAULT_DB_ALIAS
from django.db.models.query import QuerySet
from django.forms.fields import MultiValueField
from django.forms.models import BaseInlineFormSet
from django.core.urlresolvers import reverse
from django.contrib import messages

from django.contrib.auth.models import User

from CIM_Questionnaire.questionnaire.views import *

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

from CIM_Questionnaire.questionnaire.forms.forms_customize import get_data_from_customizer_forms

from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes, EnumerationFormField, CardinalityFormField

from CIM_Questionnaire.questionnaire.utils import add_parameters_to_url, get_form_by_field, get_joined_keys_dict, model_to_data, get_forms_by_field, get_data_from_form, get_data_from_formset
from CIM_Questionnaire.questionnaire.utils import CIM_DOCUMENT_TYPES
from CIM_Questionnaire.questionnaire.utils import APP_LABEL


###########################################
# some utility fns to get data from forms #
# (even if they aren't MetadataForms)     #
###########################################

def get_data_from_form(form, existing_data={}):

    data = {}

    form_prefix = form.prefix
    for field_name, field in form.fields.iteritems():

        if form_prefix:
            field_key = u"%s-%s" % (form_prefix, field_name)
        else:
            field_key = field_name

        if field_name in existing_data:
            field_value = existing_data[field_name]

        else:
            try:
                field_value = form.data[field_key]
            except KeyError:
                field_value = field.initial
                # try:
                #     field_value = form.initial[field_name]
                # except KeyError:
                #     msg = "unable to find %s in %s" % (field_key, form)
                #     raise KeyError(msg)

        if isinstance(field, MultiValueField) and isinstance(field_value, list):
            for i, v in enumerate(field_value):
                data[u"%s_%s" % (field_key, i)] = v
        else:
            data[field_key] = field_value

    return data


def get_data_from_formset(formset, existing_data={}):

    data = {}
    current_data = {}

    for form in formset:
        current_data.clear()
        current_data.update(existing_data)

        # (the hidden pk & fk fields do not get passed in via the queryset for existing model formsets)
        pk_field_name = formset.model._meta.pk.name
        current_data[pk_field_name] = form.fields[pk_field_name].initial
        if isinstance(formset, BaseInlineFormSet):
            fk_field_name = formset.fk.name
            current_data[fk_field_name] = form.fields[fk_field_name].initial

        if formset.can_delete:
            current_data["DELETE"] = False

        form_data = get_data_from_form(form, current_data)
        data.update(form_data)

    formset_prefix = formset.prefix
    if formset_prefix:
        total_forms_key = u"%s-TOTAL_FORMS" % formset_prefix
        initial_forms_key = u"%s-INITIAL_FORMS" % formset_prefix
    else:
        total_forms_key = u"TOTAL_FORMS"
        initial_forms_key = u"INITIAL_FORMS"
    data[total_forms_key] = formset.total_form_count()
    data[initial_forms_key] = formset.initial_form_count()

    return data


###############################################
# models used for test-specific functionality #
###############################################

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
        app_label = APP_LABEL
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
            cursor.execute('DROP TABLE IF EXISTS %s' % table_name)
        except:
            # Catch anything backend-specific here.
            # (E.g., MySQLdb raises a warning if the table didn't exist.)
            pass
        finally:
            cursor.close()

    def get_form_data(self):
        form_data = model_to_data(
            self,
            exclude=[],
            include={
                "loaded": True,  # here is not the place to test loaded/unloaded forms
            }
        )
        return form_data


##########################################
# a way of testing the number of queries #
# performed during an operation          #
##########################################

class QueryCounter(CaptureQueriesContext):
    """ provides a context manager for me to keep track of the number of queries
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


##############################
# the actual base test class #
##############################

class TestQuestionnaireBase(TestCase):

    """
     The base class for all CIM Questionnaire tests
     provides a reusable test client
     and a default user, project, version, categorization, vocabulary
     as well as default proxies, customizers, and realizations
     to play with in child classes
    """

    maxDiff = None  # display full errors regardless of size
    fixtures = ['questionnaire_testdata.json']

    def test_fixtures_loaded(self):

        # update fixtures by running
        # `python CIM_Questionnaire/manage.py dumpdata questionnaire --indent=4 > CIM_Questionnaire/questionnaire/questionnaire_testdata.json`
        # TODO: TEST THAT CONTENT IS AS EXPECTED
        # NOTE THAT LOADING THE FIXTURES RELIES ON MODELS BEING ENTERED IN THE CORRECT ORDER
        # IF I GET A DeserializationError THEN TRY CHECKING THE ORDER OF MODELS IN THE JSON FILE

        pass

    def setUp(self):

        self.cache = get_cache("default")
        self.cache.clear()

        # factory is useful for creating simple requests
        self.factory = RequestFactory()
        # client is better-suited for most tests, though, b/c, among other things, it has sessions, cookies, etc.
        self.client = Client()  # enforce_csrf_checks=True)

        self.cim_1_8_1_version = MetadataVersion.objects.get(name="cim", version="1.8.1")
        self.cim_1_8_1_categorization = self.cim_1_8_1_version.categorization
        self.cim_1_10_version = MetadataVersion.objects.get(name="cim", version="1.10")
        self.cim_1_10_categorization = self.cim_1_10_version.categorization

        self.model_component_proxy = MetadataModelProxy.objects.get(version=self.cim_1_10_version, name__iexact="modelcomponent")

        self.atmosphere_vocabulary = MetadataVocabulary.objects.get(name__iexact="atmosphere")
        self.landsurface_vocabulary = MetadataVocabulary.objects.get(name__iexact="landsurface")
        self.statisticaldownscaling_vocabulary = MetadataVocabulary.objects.get(name__iexact="statisticaldownscaling")
        self.modelinfrastructure_vocabulary = MetadataVocabulary.objects.get(name__iexact="modelinfrastructure")

        self.downscaling_project = MetadataProject.objects.get(name="downscaling")
        downscaling_model_component_customizer = MetadataModelCustomizer.objects.get(project=self.downscaling_project, proxy=self.model_component_proxy, name="default")
        downscaling_model_component_customizer_with_subforms = MetadataModelCustomizer.objects.get(project=self.downscaling_project, proxy=self.model_component_proxy, name="subforms")
        self.downscaling_model_component_vocabularies = downscaling_model_component_customizer.get_sorted_vocabularies()

        (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(downscaling_model_component_customizer, self.downscaling_model_component_vocabularies)

        (model_customizer_with_subforms, standard_category_customizers_with_subforms, standard_property_customizers_with_subforms, nested_scientific_category_customizers_with_subforms, nested_scientific_property_customizers_with_subforms) = \
            MetadataCustomizer.get_existing_customizer_set(downscaling_model_component_customizer_with_subforms, self.downscaling_model_component_vocabularies)

        self.downscaling_model_component_customizer_set = {
            "model_customizer": model_customizer,
            "standard_category_customizers": standard_category_customizers,
            "standard_property_customizers": standard_property_customizers,
            "scientific_category_customizers": get_joined_keys_dict(nested_scientific_category_customizers),
            "scientific_property_customizers": get_joined_keys_dict(nested_scientific_property_customizers),
        }

        self.downscaling_model_component_customizer_set_with_subforms = {
            "model_customizer": model_customizer_with_subforms,
            "standard_category_customizers": standard_category_customizers_with_subforms,
            "standard_property_customizers": standard_property_customizers_with_subforms,
            "scientific_category_customizers": get_joined_keys_dict(nested_scientific_category_customizers_with_subforms),
            "scientific_property_customizers": get_joined_keys_dict(nested_scientific_property_customizers_with_subforms),
        }

        self.downscaling_model_component_proxy_set = {
            "model_proxy": self.model_component_proxy,
            "standard_property_proxies": [standard_property_customizer.proxy for standard_property_customizer in self.downscaling_model_component_customizer_set["standard_property_customizers"]],
            "scientific_property_proxies": {key: [spc.proxy for spc in value] for key, value in self.downscaling_model_component_customizer_set["scientific_property_customizers"].items()},
        }

        downscaling_model_component_realizations = MetadataModel.objects.get(project=self.downscaling_project, pk=1).get_descendants(include_self=True)
        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_existing_realization_set(downscaling_model_component_realizations, self.downscaling_model_component_customizer_set["model_customizer"], vocabularies=self.downscaling_model_component_vocabularies)

        self.downscaling_model_component_realization_set = {
            "models": models,
            "standard_properties": standard_properties,
            "scientific_properties": scientific_properties,
        }

        self.esfdl_project = MetadataProject.objects.get(name="es-fdl")
        esfdl_model_component_customizer = MetadataModelCustomizer.objects.get(project=self.esfdl_project, proxy=self.model_component_proxy, name="default")
        self.esfdl_model_component_vocabularies = esfdl_model_component_customizer.get_sorted_vocabularies()

        (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(esfdl_model_component_customizer, self.esfdl_model_component_vocabularies)

        self.esfdl_model_component_customizer_set = {
            "model_customizer": model_customizer,
            "standard_category_customizers": standard_category_customizers,
            "standard_property_customizers": standard_property_customizers,
            "scientific_category_customizers": get_joined_keys_dict(nested_scientific_category_customizers),
            "scientific_property_customizers": get_joined_keys_dict(nested_scientific_property_customizers),
        }

        self.esfdl_model_component_proxy_set = {
            "model_proxy": self.model_component_proxy,
            "standard_property_proxies": [standard_property_customizer.proxy for standard_property_customizer in self.esfdl_model_component_customizer_set["standard_property_customizers"]],
            "scientific_property_proxies": {key: [spc.proxy for spc in value] for key, value in self.esfdl_model_component_customizer_set["scientific_property_customizers"].items()},
        }

        esfdl_model_component_realizations = MetadataModel.objects.filter(project=self.esfdl_project)
        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_existing_realization_set(esfdl_model_component_realizations, self.esfdl_model_component_customizer_set["model_customizer"], vocabularies=self.esfdl_model_component_vocabularies)

        self.esfdl_model_component_realization_set = {
            "models": models,
            "standard_properties": standard_properties,
            "scientific_properties": scientific_properties,
        }

        #
        # # SETUP DEFAULT TEST USER & SUPERUSER
        # test_user = User.objects.create_user("test", "a@b.com", "test")
        # test_superuser = User.objects.create_superuser("admin", "a@b.com", "admin")
        # user_qs = User.objects.all()
        # self.assertEqual(len(user_qs), 2)
        # self.assertIsNotNone(get_metadata_user(test_user), msg="MetadataUser not created after the User.objects.create_user() fn")
        # self.client.login(username=test_superuser.username, password=test_superuser.password)
        # self.user = test_user
        # self.super_user = test_superuser
        #
        # # REPLACED ALL OF THIS W/ create_static_x() FNS BELOW
        # self.create_static_content()
        #
        # test_document_type = "modelcomponent"
        #
        # proxy_to_test = self.version.model_proxies.get(name__iexact=test_document_type)
        # vocabularies_to_test = self.project.vocabularies.filter(document_type__iexact=test_document_type)
        #
        # # SETUP DEFAULT CUSTOMIZERS
        # (test_model_customizer, test_standard_category_customizers, test_standard_property_customizers, test_scientific_category_customizers, test_scientific_property_customizers) = \
        #     MetadataCustomizer.get_new_customizer_set(self.project, self.version, proxy_to_test, vocabularies_to_test)
        # # add some one-off customizations as if this had been filled out in the form...
        # test_model_customizer.name = "customizer"
        # test_model_customizer.default = True
        # for standard_property_customizer in test_standard_property_customizers:
        #     if standard_property_customizer.category is None:
        #         # TODO: REMOVE THIS AS SOON AS I'VE FIXED ISSUE #71
        #         standard_property_customizer.displayed = False
        # MetadataCustomizer.save_customizer_set(test_model_customizer, test_standard_category_customizers, test_standard_property_customizers, test_scientific_category_customizers, test_scientific_property_customizers)
        # model_customizer_qs = MetadataModelCustomizer.objects.all()
        # standard_category_customizer_qs = MetadataStandardCategoryCustomizer.objects.all()
        # scientific_category_customizer_qs = MetadataScientificCategoryCustomizer.objects.all()
        # standard_property_customizer_qs = MetadataStandardPropertyCustomizer.objects.all()
        # scientific_property_customizer_qs = MetadataScientificPropertyCustomizer.objects.all()
        # self.assertEqual(len(model_customizer_qs), 1)
        # self.assertEqual(len(standard_category_customizer_qs), 3)
        # self.assertEqual(len(scientific_category_customizer_qs), 10)
        # self.assertEqual(len(standard_property_customizer_qs), 7)
        # self.assertEqual(len(scientific_property_customizer_qs), 9)
        # self.model_customizer = test_model_customizer
        #
        # # SETUP DEFAULT REALIZATIONS
        # reordered_test_standard_property_proxies = [standard_property_customizer.proxy for standard_property_customizer in test_standard_property_customizers]
        # reordered_test_scientific_property_customizers = get_joined_keys_dict(test_scientific_property_customizers)
        # reordered_test_scientific_property_proxies = { key : [spc.proxy for spc in value] for key,value in reordered_test_scientific_property_customizers.items() }
        #
        # # reordered_test_standard_property_proxies = [standard_property_customizer.proxy for standard_property_customizer in test_standard_property_customizers]
        # # reordered_test_scientific_property_proxies = {}
        # # for vocabulary_key,scientific_property_customizer_dict in test_scientific_property_customizers.iteritems():
        # #     for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
        # #         model_key = u"%s_%s" % (vocabulary_key, component_key)
        # #         reordered_test_scientific_property_proxies[model_key] = [scientific_property_customizer.proxy for scientific_property_customizer in scientific_property_customizer_list]
        # (test_models, test_standard_properties, test_scientific_properties) = \
        #     MetadataModel.get_new_realization_set(self.project, self.version, proxy_to_test, reordered_test_standard_property_proxies, reordered_test_scientific_property_proxies, test_model_customizer, vocabularies_to_test)
        # MetadataModel.save_realization_set(test_models,test_standard_properties,test_scientific_properties)
        # model_qs = MetadataModel.objects.all()
        # standard_property_qs = MetadataStandardProperty.objects.all()
        # scientific_property_qs = MetadataScientificProperty.objects.all()
        # self.assertEqual(len(model_qs), 6)
        # self.assertEqual(len(standard_property_qs), 42)
        # self.assertEqual(len(scientific_property_qs), 9)
        # self.model_realization = test_models[0].get_root()

    def tearDown(self):
        # this is for resetting things that are not db-related (ie: files, etc.)
        # but it's not needed for the db since each test is run in its own transaction
        # TODO CLEAR CACHE
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
            list(sorted(qs2, key=pk))
        )

    def assertDictEqual(self, d1, d2, excluded_keys=[]):
        """Overrides super.assertDictEqual fn to remove certain keys from either list before the comparison"""

        self.assertIsInstance(d1, dict, 'First argument is not a dictionary')
        self.assertIsInstance(d2, dict, 'Second argument is not a dictionary')

        d1_copy = d1.copy()
        d2_copy = d2.copy()
        for key_to_exclude in excluded_keys:
            d1_copy.pop(key_to_exclude, None)
            d2_copy.pop(key_to_exclude, None)

        msg = '%s != %s' % (safe_repr(d1_copy, True), safe_repr(d2_copy, True))
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
                # I need a quick check just in case I am comparing different types of strings
                string_types = [str, unicode, ]
                if not (d1_type in string_types and d2_type in string_types):
                    raise AssertionError(msg)

            if d1_type == QuerySet:
                self.assertQuerysetEqual(d1_value, d2_value)
            else:
                self.assertEqual(d1_value, d2_value)

        #return super(TestQuestionnaireBase, self).assertDictEqual(d1_copy, d2_copy)


    def assertFileExists(self, file_path, **kwargs):
        """Tests that a file exists"""

        msg = kwargs.pop("msg",None)
        file_exists = os.path.exists(file_path)

        return self.assertEqual(file_exists, True, msg=msg)


    def assertFileDoesntExist(self, file_path, **kwargs):
        """Tests that a file doesn't exist"""

        msg = kwargs.pop("msg",None)
        file_exists = os.path.exists(file_path)

        return self.assertEqual(file_exists, False, msg=msg)


    #################################################################################
    # the fns below are used to setup static db content                             #
    # they should be used in conjunction w/ fixtures for customizers & realizations #
    #################################################################################

    def create_static_content(self):

        self.create_static_version()
        self.create_static_vocabulary()
        self.create_static_project()

    def create_static_version(self):

        test_categorization_path = os.path.join(CATEGORIZATION_UPLOAD_PATH, "test_categorization.xml")
        test_categorization = MetadataCategorization(name="categorization", file=test_categorization_path)
        test_categorization.save()

        test_version_path = os.path.join(VERSION_UPLOAD_PATH, "test_version.xml")
        test_version = MetadataVersion(name="version", version="1.0", file=test_version_path, categorization=test_categorization, url="www.namespace.com/test/cim.xsd")
        test_version.save()

        test_version.register()
        test_version.save()
        test_categorization.register()
        test_categorization.save()

        model_proxy_qs = MetadataModelProxy.objects.all()
        standard_category_proxy_qs = MetadataStandardCategoryProxy.objects.all()
        standard_property_proxy_qs = MetadataStandardPropertyProxy.objects.all()
        self.assertEqual(len(model_proxy_qs), 3, msg="Unexpected number of MetadataModelProxy.  Did you change %s" % (test_version.file.path))
        self.assertEqual(len(standard_category_proxy_qs), 3, msg="Unexpected number of MetadataStandardCategoryProxy.  Did you change %s" % (test_version.file.path))
        self.assertEqual(len(standard_property_proxy_qs), 11, msg="Unexpected number of MetadataStandardPropertyProxy.  Did you change %s" % (test_version.file.path))

        self.version = test_version
        self.categorization = test_categorization


    def create_static_vocabulary(self):

        test_document_type = "modelcomponent"
        self.assertIn(test_document_type, CIM_DOCUMENT_TYPES, msg="Unrecognized vocabulary document type: %s" % (test_document_type))
        test_vocabulary_path = os.path.join(VOCABULARY_UPLOAD_PATH, "test_vocabulary_bdl.xml")
        test_vocabulary = MetadataVocabulary(name="vocabulary", file=test_vocabulary_path, document_type=test_document_type)
        test_vocabulary.save()

        test_vocabulary.register()
        test_vocabulary.save()

        component_proxy_qs = MetadataComponentProxy.objects.all()
        scientific_category_proxy_qs = MetadataScientificCategoryProxy.objects.all()
        scientific_property_proxy_qs = MetadataScientificPropertyProxy.objects.all()
        self.assertEqual(len(component_proxy_qs), 5, msg="Unexpected number of MetadataComponentProxy.  Did you change %s" % (test_vocabulary.file.path))
        self.assertEqual(len(scientific_category_proxy_qs), 10, msg="Unexpected number of MetadataScientificCategoryProxy.  Did you change %s" % (test_vocabulary.file.path))
        self.assertEqual(len(scientific_property_proxy_qs), 9, msg="Unexpected number of MetadataScientificCategoryProxy.  Did you change %s" % (test_vocabulary.file.path))

        self.vocabulary = test_vocabulary


    def create_static_project(self,**kwargs):
        vocabularies = kwargs.pop("vocabularies", [self.vocabulary])
        test_project = MetadataProject(name="project", title="Test Project", active=True, authenticated=False)
        test_project.save()
        for vocabulary in vocabularies:
            test_project.add_vocabulary(vocabulary)
        self.project = test_project


    ##########################################################################
    # the fns below get forms exactly as they would have been setup by views #
    # other fns in other classes explicitly test the fns used in those views #
    ##########################################################################


    def get_new_customizer_forms(self,*args,**kwargs):

        project_name = kwargs.pop("project_name", self.project.name.lower())
        version_key = kwargs.pop("version_key", self.version.get_key())
        model_name = kwargs.pop("model_name", self.model_realization.name.lower())

        request_url = reverse("customize_new", kwargs = {
            "project_name" : project_name,
            "version_key" : version_key,
            "model_name" : model_name,
        })

        response = self.client.get(request_url, follow=True)
        context = response.context

        self.assertEqual(response.status_code,200)

        model_customizer_form = context["model_customizer_form"]
        standard_property_customizer_formset = context["standard_property_customizer_formset"]
        scientific_property_customizer_formsets = context["scientific_property_customizer_formsets"]

        for standard_property_customizer_form in standard_property_customizer_formset:
            if standard_property_customizer_form.get_current_field_value("category") is None:
                # TODO: REMOVE THIS AS SOON AS I'VE FIXED ISSUE #71
                standard_property_customizer_form.initial["displayed"] = False

        return (model_customizer_form, standard_property_customizer_formset, scientific_property_customizer_formsets)


    def get_new_customizer_subforms(self,*args,**kwargs):

        property_id  = kwargs.pop("property_id", None)

        self.assertIsNotNone(property_id, msg="cannot create a customize subform without specifying which property to customize")

        request_url = add_parameters_to_url(reverse("customize_subform"), i=property_id)

        response = self.client.get(request_url, follow=True)
        context = response.context

        self.assertEqual(response.status_code,200)

        model_customizer_form = context["model_customizer_form"]
        standard_property_customizer_formset = context["standard_property_customizer_formset"]
        # NOT NEEDED FOR SUBFORMS
        #scientific_property_customizer_formsets = context["scientific_property_customizer_formsets"]
        scientific_property_customizer_formsets = {}

        return (model_customizer_form, standard_property_customizer_formset, scientific_property_customizer_formsets)


    def get_new_edit_forms(self,*args,**kwargs):

        project_name = kwargs.pop("project_name", self.project.name.lower())
        version_key = kwargs.pop("version_key", self.version.get_key())
        model_name = kwargs.pop("model_name", self.model_realization.name.lower())

        request_url = reverse("edit_new", kwargs = {
            "project_name" : project_name,
            "version_key" : version_key,
            "model_name" : model_name,
        })

        response = self.client.get(request_url, follow=True)
        context = response.context

        self.assertEqual(response.status_code,200)

        edit_forms = {
            "model_formset" : context["model_formset"],
            "standard_properties_formsets" : context["standard_properties_formsets"],
            "scientific_properties_formsets" : context["scientific_properties_formsets"],
        }

        return edit_forms


    def fully_serialize_model(self,model,exclude=[]):
        """
        serializes model to dictionary (like model_to_dict) but follows foreign keys
        makes lots of db hits - good enough for tests but not ready for production
        """
        model_dictionary = {}
        for field in model._meta.fields:
            field_name = field.name
            if field_name not in exclude:
                model_dictionary[field.name] = getattr(model,field_name)

        # suspect that the new logic above is faster & cleaner than the old logic below
        # model_dictionary = model_to_dict(model,exclude=exclude)
        # model_dictionary_copy = model_dictionary.copy()
        # for key, value in model_dictionary_copy.iteritems():
        #     field = model._meta.get_field_by_name(key)[0]
        #     if isinstance(field,ForeignKey):
        #         model_dictionary[key] = field.rel.to.objects.get(pk=value)

        return model_dictionary


    #######################################################################################
    # the fns below create customizers & realizations exactly as they would have by views #
    # other fns in other classes explicitly test the fns used in those views              #
    #######################################################################################


    def create_customizer_set_with_subforms(self, project, version, proxy, properties_with_subforms=[]):

        # setup an additional customizer for testing purposes
        # this one uses subforms
        customizer_name = "customizer_with_subforms"

        project_name = project.name.lower()
        version_key = version.get_key()
        model_name = proxy.name.lower()

        (model_customizer_form, standard_property_customizer_formset, scientific_property_customizer_formsets) = \
            self.get_new_customizer_forms(project_name=project_name, version_key=version_key, model_name=model_name)

        customizer_forms_data = get_data_from_customizer_forms(model_customizer_form, standard_property_customizer_formset, scientific_property_customizer_formsets)

        if model_customizer_form.prefix:
            model_customizer_form_prefix = u"%s-" % (model_customizer_form.prefix)
        else:
            model_customizer_form_prefix = ""
        customizer_forms_data[u"%sname" % (model_customizer_form_prefix)] = customizer_name

        request_url = reverse("customize_new", kwargs = {
            "project_name" : project_name,
            "version_key" : version_key,
            "model_name" : model_name,
        })

        # ("follow=True" allows the context setup in the initial view to be retained in the redirected view [http://stackoverflow.com/questions/16143149/django-testing-check-messages-for-a-view-that-redirects])
        response = self.client.post(request_url, data=customizer_forms_data, follow=True)

        session_variables = self.client.session
        message_variables = [m for m in list(response.context["messages"])]

        self.assertIn("model_id", session_variables)
        self.assertEqual(session_variables["checked_arguments"], True)
        self.assertEqual(len(message_variables), 1)
        self.assertEqual(message_variables[0].tags, messages.DEFAULT_TAGS[messages.SUCCESS])
        self.assertEqual(response.status_code, 200)

        parent_customizer = MetadataModelCustomizer.objects.get(pk=session_variables["model_id"])

        for property_name in properties_with_subforms:

            property = parent_customizer.standard_property_customizers.get(name=property_name)
            self.assertEqual(property.field_type,MetadataFieldTypes.RELATIONSHIP)

            (model_customizer_subform, standard_property_customizer_subformset, scientific_property_customizer_subformsets) = \
                self.get_new_customizer_subforms(property_id=property.pk)

            customizer_subforms_data = get_data_from_customizer_forms(model_customizer_subform, standard_property_customizer_subformset, scientific_property_customizer_subformsets)

            request_url = add_parameters_to_url(reverse("customize_subform"), i=property.pk)
            response = self.client.post(request_url, data=customizer_subforms_data, follow=True) # (the saving is handled in the POST)

            json_response = json.loads(response.content)

            self.assertEqual(json_response["subform_customizer_name"],parent_customizer.name)
            self.assertEqual(json_response["subform_customizer_name"],customizer_name)
            self.assertEqual(response.status_code,200)

            child_customizer = MetadataModelCustomizer.objects.get(pk=json_response["subform_customizer_id"])

            property.relationship_show_subform = True
            property.subform_customizer = child_customizer

            property.save()

        return parent_customizer

    def add_subform_to_post_data(self, data, standard_properties_formset, properties_to_add_subform_to=[]):

        for property_name in properties_to_add_subform_to:

            standard_property_form = get_form_by_field(standard_properties_formset,"name",property_name)

            (subform_customizer, model_subformset, standard_properties_subformsets, scientific_properties_subformsets) = \
            standard_property_form.get_subform_tuple()

            subformset_prefix = model_subformset.prefix
            initial_subforms = model_subformset.initial_form_count()
            total_subforms = model_subformset.total_form_count()

            request_url = add_parameters_to_url(reverse("select_realization"),
                c = standard_property_form.customizer.pk,
                p = standard_property_form.prefix,
                n = total_subforms + 1 , # recall that in the interface, this view gets called _after_ a subform has been added by JS; hence the' + 1'
            )

            # this is adding a new _blank_ subform
            response = self.client.post(request_url, data={"realizations" : -1}, follow=True)

            json_response = json.loads(response.content)

            # actually, don't have to mess w/ prefixes b/c there was no old subform in the interface that was copied
            # old_prefix = subformset_prefix + "-0"
            # new_prefix = json_response.pop("prefix")
            # for key, value in json_response.iteritems():
            #     data[key.replace(old_prefix,new_prefix)] = value
            data.update(json_response)

            data[subformset_prefix + "-INITIAL_FORMS"] = initial_subforms
            data[subformset_prefix + "-TOTAL_FORMS"] = total_subforms + 1

            return data



