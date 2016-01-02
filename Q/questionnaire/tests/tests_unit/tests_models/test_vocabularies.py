####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'


from Q.questionnaire.tests.test_base import TestQBase, create_vocabulary, remove_vocabulary, incomplete_test
from Q.questionnaire.models.models_vocabularies import *
from Q.questionnaire.q_utils import serialize_model_to_dict, sort_list_by_key
from Q.questionnaire.q_fields import MPTT_FIELDS



class TestQVocabulary(TestQBase):

    def setUp(self):

        super(TestQVocabulary, self).setUp()

        # create a test vocabulary
        self.test_vocabulary = create_vocabulary(
            name="test_vocabulary",
            version="1.0",
            document_type="modelcomponent",
        )

    def tearDown(self):

        super(TestQVocabulary, self).tearDown()

        # delete the test ontology
        remove_vocabulary(vocabulary=self.test_vocabulary)

    def test_vocabulary_register(self):

        self.assertFalse(self.test_vocabulary.is_registered)
        self.test_vocabulary.register()
        self.assertTrue(self.test_vocabulary.is_registered)

        test_component_proxies = self.test_vocabulary.component_proxies.all()
        test_category_proxies = QScientificCategoryProxy.objects.filter(component_proxy__vocabulary=self.test_vocabulary)
        test_property_proxies = QScientificPropertyProxy.objects.filter(component_proxy__vocabulary=self.test_vocabulary)

        component_excluded_fields = ["id", "guid", "created", "modified"] + MPTT_FIELDS
        component_excluded_fields.remove("parent")
        actual_component_proxies_data = [
            serialize_model_to_dict(component_proxy, exclude=component_excluded_fields)
            for component_proxy in test_component_proxies
        ]

        test_component_proxies_data = sort_list_by_key(
            [
                {'vocabulary': self.test_vocabulary.pk, 'documentation': None, 'name': u'TestModel', 'parent': None, 'order': 1},
                {'vocabulary': self.test_vocabulary.pk, 'documentation': None, 'name': u'TestModelKeyProperties', 'parent': QComponentProxy.objects.get(name="TestModel").pk, 'order': 2},
                {'vocabulary': self.test_vocabulary.pk, 'documentation': None, 'name': u'PretendSubModel', 'parent': QComponentProxy.objects.get(name="TestModel").pk, 'order': 3},
                {'vocabulary': self.test_vocabulary.pk, 'documentation': None, 'name': u'SubModel', 'parent': QComponentProxy.objects.get(name="TestModel").pk, 'order': 4},
                {'vocabulary': self.test_vocabulary.pk, 'documentation': None, 'name': u'SubSubModel', 'parent': QComponentProxy.objects.get(name="SubModel").pk, 'order': 5},
            ],
            "order"
        )

        for actual_component_proxy_data, test_component_proxy_data in zip(actual_component_proxies_data, test_component_proxies_data):
            self.assertDictEqual(actual_component_proxy_data, test_component_proxy_data)

        actual_category_proxies_data = [
            serialize_model_to_dict(category_proxy, exclude=["id", "guid", "created", "modified", ] + MPTT_FIELDS)
            for category_proxy in test_category_proxies
        ]

        test_category_proxies_data = sort_list_by_key(
            [
                {'documentation': None, 'component_proxy': test_component_proxies[0].pk, 'name': u'General Attributes', 'key': u'general-attributes', 'order': 1},
                {'documentation': None, 'component_proxy': test_component_proxies[1].pk, 'name': u'General Attributes', 'key': u'general-attributes', 'order': 1},
                {'documentation': None, 'component_proxy': test_component_proxies[1].pk, 'name': u'CategoryOne', 'key': u'categoryone', 'order': 2},
                {'documentation': None, 'component_proxy': test_component_proxies[1].pk, 'name': u'CategoryTwo', 'key': u'categorytwo', 'order': 3},
                {'documentation': None, 'component_proxy': test_component_proxies[2].pk, 'name': u'General Attributes', 'key': u'general-attributes', 'order': 1},
                {'documentation': None, 'component_proxy': test_component_proxies[2].pk, 'name': u'CategoryOne', 'key': u'categoryone', 'order': 2},
                {'documentation': None, 'component_proxy': test_component_proxies[3].pk, 'name': u'General Attributes', 'key': u'general-attributes', 'order': 1},
                {'documentation': None, 'component_proxy': test_component_proxies[3].pk, 'name': u'CategoryOne', 'key': u'categoryone', 'order': 2},
                {'documentation': None, 'component_proxy': test_component_proxies[4].pk, 'name': u'General Attributes', 'key': u'general-attributes', 'order': 1},
                {'documentation': None, 'component_proxy': test_component_proxies[4].pk, 'name': u'CategoryOne', 'key': u'categoryone', 'order': 2},
            ],
            "order"
        )

        for actual_category_proxy_data, test_category_proxy_data in zip(actual_category_proxies_data, test_category_proxies_data):
            self.assertDictEqual(actual_category_proxy_data, test_category_proxy_data)

        actual_property_proxies_data = [
            serialize_model_to_dict(property_proxy, exclude=["id", "guid", "created", "modified", ] + MPTT_FIELDS)
            for property_proxy in test_property_proxies
        ]

        test_property_proxies_data = sort_list_by_key(
            [
                {'category': test_category_proxies[1].pk, 'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'name1', 'enumeration_multi': False, 'choice': u'keyboard', 'documentation': u'I am free text.', 'atomic_type': u'DEFAULT', 'component_proxy': test_component_proxies[1].pk, 'enumeration_open': False, 'enumeration_choices': u'', 'cardinality': u'0|1', 'order': 1},
                {'category': test_category_proxies[1].pk, 'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'number', 'enumeration_multi': False, 'choice': u'keyboard', 'documentation': u'I am a number.', 'atomic_type': u'DEFAULT', 'component_proxy': test_component_proxies[1].pk, 'enumeration_open': False, 'enumeration_choices': u'', 'cardinality': u'0|1', 'order': 2},
                {'category': test_category_proxies[1].pk, 'field_type': u'ENUMERATION', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'choice1', 'enumeration_multi': True, 'choice': u'OR', 'documentation': u'I am an inclusive choice.', 'atomic_type': None, 'component_proxy': test_component_proxies[1].pk, 'enumeration_open': False, 'enumeration_choices': u'one|two|three|other|N/A', 'cardinality': u'0|1', 'order': 3},
                {'category': test_category_proxies[1].pk, 'field_type': u'ENUMERATION', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'choice2', 'enumeration_multi': False, 'choice': u'XOR', 'documentation': u'I am an exclusive choice.', 'atomic_type': None, 'component_proxy': test_component_proxies[1].pk, 'enumeration_open': False, 'enumeration_choices': u'yes|no', 'cardinality': u'0|1', 'order': 4},
                {'category': test_category_proxies[5].pk, 'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'name2', 'enumeration_multi': False, 'choice': u'keyboard', 'documentation': u'I am free text.', 'atomic_type': u'DEFAULT', 'component_proxy': test_component_proxies[1].pk, 'enumeration_open': False, 'enumeration_choices': u'', 'cardinality': u'0|1', 'order': 1},
                {'category': test_category_proxies[9].pk, 'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'name3', 'enumeration_multi': False, 'choice': u'keyboard', 'documentation': u'I am free text.', 'atomic_type': u'DEFAULT', 'component_proxy': test_component_proxies[1].pk, 'enumeration_open': False, 'enumeration_choices': u'', 'cardinality': u'0|1', 'order': 1},
                {'category': test_category_proxies[6].pk, 'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'name4', 'enumeration_multi': False, 'choice': u'keyboard', 'documentation': u'I am free text.', 'atomic_type': u'DEFAULT', 'component_proxy': test_component_proxies[2].pk, 'enumeration_open': False, 'enumeration_choices': u'', 'cardinality': u'0|1', 'order': 1},
                {'category': test_category_proxies[7].pk, 'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'name5', 'enumeration_multi': False, 'choice': u'keyboard', 'documentation': u'I am free text.', 'atomic_type': u'DEFAULT', 'component_proxy': test_component_proxies[3].pk, 'enumeration_open': False, 'enumeration_choices': u'', 'cardinality': u'0|1', 'order': 1},
                {'category': test_category_proxies[8].pk, 'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'name6', 'enumeration_multi': False, 'choice': u'keyboard', 'documentation': u'I am free text.', 'atomic_type': u'DEFAULT', 'component_proxy': test_component_proxies[4].pk, 'enumeration_open': False, 'enumeration_choices': u'', 'cardinality': u'0|1', 'order': 1},
            ],
            "order"
        )

        for actual_property_proxy_data, test_property_proxy_data in zip(actual_property_proxies_data, test_property_proxies_data):
            self.assertDictEqual(actual_property_proxy_data, test_property_proxy_data)

    @incomplete_test
    def test_vocabulary_reregister(self):
        pass
