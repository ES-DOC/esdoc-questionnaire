__author__ = 'ben.koziol'

from django.core.urlresolvers import reverse

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase

from CIM_Questionnaire.questionnaire.views.views_api import validate_section_key, api_get_form_section

from CIM_Questionnaire.questionnaire.utils import DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY
from CIM_Questionnaire.questionnaire.utils import FuzzyInt

class Test(TestQuestionnaireBase):

    def setUp(self):

        super(Test,self).setUp()

    # section_key format is:
    # [ <version_key> |
    #   <model_key> |
    #   <vocabulary_key> |
    #   <component_key> |
    #   'standard_properties" or "scientific_properties"
    #   <category_key> |
    #   <property_key> |
    #
    # ]

        self.test_version_key = self.version.get_key()
        self.invalid_version_key = "invalid_version"

        self.test_model_key = "ModelComponent".lower()
        self.invalid_model_key = "invalid_model"

        self.default_vocabulary_key = DEFAULT_VOCABULARY_KEY
        self.test_vocabulary_key = self.vocabulary.guid
        self.invalid_vocabulary_key = "invalid_vocabulary"

        self.default_component_key = DEFAULT_COMPONENT_KEY
        self.test_component_key = self.vocabulary.component_proxies.get(name__iexact="testmodelkeyproperties").guid
        self.invalid_component_key = "invalid_component"

        self.test_standard_category_key = "category-one"
        self.invalid_standard_category_key = "invalid_standard_category"

        self.test_scientific_category_key = "categoryone"
        self.invalid_scientific_category_key = "invalid_scientific_category"

        self.test_standard_property_key = "author"  # might as well make this a complex relationship (this way I can check subforms)
        self.invalid_standard_property_key = "invalid_standard_property"

        self.test_scientific_property_key = "name"
        self.invalid_scientificproperty_key = "invalid_scientific_property"

        # TODO: ADD REAL CIM DATA TO THIS TEST

    def test_validate_section_key(self):

        section_key = "|".join([
            self.test_version_key,
            self.test_model_key,
        ])

        # first try w/ an incomplete key to make sure it fails...
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg ) = \
            validate_section_key(section_key)
        self.assertEqual(validity, False)

        # now complete the key
        section_key += u"|%s|%s" % (self.default_vocabulary_key, self.default_component_key)

        # try for the least-specific section...
        # (entire default component)
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg ) = \
            validate_section_key(section_key)
        self.assertEqual(validity, True)

        # try again for an actual component in the CV...
        section_key = section_key.replace(self.default_vocabulary_key, self.test_vocabulary_key)
        section_key = section_key.replace(self.default_component_key, self.test_component_key)
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg ) = \
            validate_section_key(section_key)
        self.assertEqual(validity, True)

        # now try w/ different property_types...
        standard_section_key = section_key + "|standard_properties"
        scientific_section_key = section_key + "|scientific_properties"
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg ) = \
            validate_section_key(standard_section_key)
        self.assertEqual(validity, True)
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg ) = \
            validate_section_key(scientific_section_key)
        self.assertEqual(validity, True)

        # now try w/ (standard & scientific) categories...
        standard_section_key = standard_section_key + "|" + self.test_standard_category_key
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg ) = \
            validate_section_key(standard_section_key)
        self.assertEqual(validity, True)
        scientific_section_key = scientific_section_key + "|" + self.test_scientific_category_key
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg ) = \
            validate_section_key(scientific_section_key)
        self.assertEqual(validity, True)

        # now try w/ (standard & scientific) properties...
        standard_section_key = standard_section_key + "|" + self.test_standard_property_key
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg ) = \
            validate_section_key(standard_section_key)
        self.assertEqual(validity, True)
        scientific_section_key = scientific_section_key + "|" + self.test_scientific_property_key
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg ) = \
            validate_section_key(scientific_section_key)
        self.assertEqual(validity, True)

        # try again w/ the same standard property but for the default (root) component this time...
        default_standard_section_key = standard_section_key.replace(self.test_vocabulary_key, self.default_vocabulary_key)
        default_standard_section_key = default_standard_section_key.replace(self.test_component_key, self.default_component_key)
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg ) = \
            validate_section_key(default_standard_section_key)
        self.assertEqual(validity, True)

        # now start introducing invalid keys...
        (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg ) = \
            validate_section_key(standard_section_key.replace(self.test_version_key,self.invalid_version_key))
        self.assertEqual(validity, False)


    # def test_api_get_form_section(self):
    #
    #
    #     section_key = "%s|%s|%s" % (self.test_version_key, test_vocabulary_key, self.test_component_key, self.test_category_key)
    #
    #     # wrap all view tests w/ a check for num db hits
    #     # (django testing framework adds ~15 hits of setup code)
    #     query_limit = FuzzyInt(0,20)
    #     with self.assertNumQueries(query_limit):
    #
    #
    #         request_url = reverse("api_get_form_section", kwargs = {
    #             "project" : self.project,
    #             "section_key" : section_key,
    #         })
    #
    #         import ipdb; ipdb.set_trace()
    #
    #         response = self.client.get(request_url)
    #
    #     self.assertEqual(response.status_code, 200)
    #
    #
