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

#import os
from django.template.defaultfilters import slugify

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase

from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy

# from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
# from CIM_Questionnaire.questionnaire.models.metadata_version import MetadataVersion
# from CIM_Questionnaire.questionnaire.models.metadata_categorization import MetadataCategorization
# from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary
# from CIM_Questionnaire.questionnaire.models.metadata_project import MetadataProject
#
# from CIM_Questionnaire.questionnaire.utils import add_parameters_to_url
# from CIM_Questionnaire.questionnaire.utils import DEFAULT_VOCABULARY


class TestMetadataProxy(TestQuestionnaireBase):


    def check_property_order(self, property_list):
        """ Ensures that the lists returned by the fns below are ordered according to category then property """

        property_list_ordered = all(((property_list[i][0] <= property_list[i+1][0]) or property_list[i+1][0] == None) and ((property_list[i][1] < property_list[i+1][1]) or(property_list[i][0] != property_list[i+1][0])) for i in xrange(len(property_list)-1))
        return property_list_ordered

    def get_standard_proxy_order(self, property_proxy):
        """ Returns a list of tuples containing the category order and property order """

        try:
            property_category_proxy = property_proxy.category.all()[0]
            property_category_proxy_order = property_category_proxy.order
        except IndexError:
            property_category_proxy_order = None

        property_proxy_order = property_proxy.order

        return (property_category_proxy_order, property_proxy_order)


    def get_scientific_proxy_order(self, property_proxy):
        """ Returns a list of tuples containing the category order and property order """

        property_category_proxy = property_proxy.category
        if property_category_proxy:
            property_category_proxy_order = property_category_proxy.order
        else:
            property_category_proxy_order = None

        property_proxy_order = property_proxy.order

        return (property_category_proxy_order, property_proxy_order)

    def test_get_proxy_set(self):

        test_document_type = "modelcomponent"

        test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)

        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)

        (model_proxy, standard_property_proxies, scientific_property_proxies) = \
        MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)

        # test the right model proxy was returned...
        self.assertEqual(model_proxy, test_proxy)

        # test the right standard property proxies were returned...
        excluded_fields = [ "id", ]
        serialized_standard_property_proxies = [self.fully_serialize_model(spp,exclude=excluded_fields) for spp in standard_property_proxies]
        test_standard_property_proxies_data = [
            {'field_type': u'ATOMIC',       'atomic_default': u'', 'enumeration_nullable': False, 'name': u'string',        'enumeration_multi': False, 'relationship_target_model': None,                                                                                  'relationship_target_name': u'',                    'enumeration_choices': u'',                 'documentation': u'I am a string',                  'atomic_type': u'DEFAULT',  'is_label': True,   'enumeration_open': False, 'model_proxy': test_proxy, 'relationship_cardinality': u'',      'order': 0},
            {'field_type': u'ATOMIC',       'atomic_default': u'', 'enumeration_nullable': False, 'name': u'date',          'enumeration_multi': False, 'relationship_target_model': None,                                                                                  'relationship_target_name': u'',                    'enumeration_choices': u'',                 'documentation': u'I am a date',                    'atomic_type': u'DATE',     'is_label': False,  'enumeration_open': False, 'model_proxy': test_proxy, 'relationship_cardinality': u'',      'order': 2},
            {'field_type': u'RELATIONSHIP', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'author',        'enumeration_multi': False, 'relationship_target_model': MetadataModelProxy.objects.get(version=self.version, name__iexact="responsibleparty"), 'relationship_target_name': u'responsibleParty',    'enumeration_choices': u'',                 'documentation': u'I am a relationship',            'atomic_type': u'DEFAULT',  'is_label': False,  'enumeration_open': False, 'model_proxy': test_proxy, 'relationship_cardinality': u'0|1',   'order': 5},
            {'field_type': u'ATOMIC',       'atomic_default': u'', 'enumeration_nullable': False, 'name': u'boolean',       'enumeration_multi': False, 'relationship_target_model': None,                                                                                  'relationship_target_name': u'',                    'enumeration_choices': u'',                 'documentation': u'I am a boolean',                 'atomic_type': u'BOOLEAN',  'is_label': False,  'enumeration_open': False, 'model_proxy': test_proxy, 'relationship_cardinality': u'',      'order': 1},
            {'field_type': u'ENUMERATION',  'atomic_default': u'', 'enumeration_nullable': False, 'name': u'enumeration',   'enumeration_multi': False, 'relationship_target_model': None,                                                                                  'relationship_target_name': u'',                    'enumeration_choices': u'one|two|three',    'documentation': u'I am an enumreation',            'atomic_type': u'DEFAULT',  'is_label': False,  'enumeration_open': False, 'model_proxy': test_proxy, 'relationship_cardinality': u'',      'order': 4},
            {'field_type': u'RELATIONSHIP', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'contact',       'enumeration_multi': False, 'relationship_target_model': MetadataModelProxy.objects.get(version=self.version, name__iexact="responsibleparty"), 'relationship_target_name': u'responsibleParty',    'enumeration_choices': u'',                 'documentation': u'I am a relationship',            'atomic_type': u'DEFAULT',  'is_label': False,  'enumeration_open': False, 'model_proxy': test_proxy, 'relationship_cardinality': u'0|*',   'order': 6},
            {'field_type': u'ATOMIC',       'atomic_default': u'', 'enumeration_nullable': False, 'name': u'uncategorized', 'enumeration_multi': False, 'relationship_target_model': None,                                                                                  'relationship_target_name': u'',                    'enumeration_choices': u'',                 'documentation': u'I am an uncategorized string',   'atomic_type': u'DEFAULT',  'is_label': False,  'enumeration_open': False, 'model_proxy': test_proxy, 'relationship_cardinality': u'',      'order': 3},
        ]
        for actual_standard_property_proxy_data,test_standard_property_proxy_data in zip(serialized_standard_property_proxies,test_standard_property_proxies_data):
            self.assertDictEqual(actual_standard_property_proxy_data,test_standard_property_proxy_data)
        # in the right order...
        standard_property_proxies_order = [self.get_standard_proxy_order(spp) for spp in standard_property_proxies]
        standard_property_proxies_ordered = self.check_property_order(standard_property_proxies_order)
        self.assertEqual(standard_property_proxies_ordered, True)

        # test the right scientific property proxies were returned...
        model_keys = []
        for vocabulary in test_vocabularies:
            vocabulary_key = slugify(vocabulary.name)
            for component_proxy in vocabulary.component_proxies.all():
                component_key = slugify(component_proxy.name)
                model_keys.append(u"%s_%s" % (vocabulary_key, component_key))
        self.assertSetEqual(set(model_keys), set(scientific_property_proxies.keys()))
        # in the right order...
        for scientific_property_proxies_list in scientific_property_proxies.values():
            scientific_property_proxies_order = [self.get_scientific_proxy_order(spp) for spp in scientific_property_proxies_list]
            scientific_property_proxies_ordered = self.check_property_order(scientific_property_proxies_order)
            self.assertEqual(scientific_property_proxies_ordered, True)






