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


from Q.questionnaire.tests.test_base import TestQBase, create_ontology, remove_ontology, incomplete_test
from Q.questionnaire.q_utils import serialize_model_to_dict
from Q.questionnaire.models.models_ontologies import *


class TestQOntolgoy(TestQBase):

    def setUp(self):

        super(TestQOntolgoy, self).setUp()

        # create a test ontology
        self.test_ontology = create_ontology(
            name="test_ontology",
            version="1.0",
        )

    def tearDown(self):

        super(TestQOntolgoy, self).tearDown()

        # delete the test ontology
        remove_ontology(ontology=self.test_ontology)

    def test_ontology_get_key(self):

        test_key = "test_ontology_1.0"
        self.assertEqual(self.test_ontology.get_key(), test_key)
        self.assertEqual(QOntology.objects.get(key=test_key), self.test_ontology)

        self.test_ontology.version = "123"
        self.test_ontology.save()

        test_key = "test_ontology_123"
        self.assertEqual(self.test_ontology.get_key(), test_key)
        self.assertEqual(QOntology.objects.get(key=test_key), self.test_ontology)

    def test_ontology_register(self):

        self.assertFalse(self.test_ontology.is_registered)
        self.test_ontology.register()
        self.assertTrue(self.test_ontology.is_registered)

        test_model_proxies = self.test_ontology.model_proxies.all()
        test_property_proxies = QStandardPropertyProxy.objects.filter(model_proxy__ontology=self.test_ontology)

        actual_model_proxies_data = [
            serialize_model_to_dict(model_proxy, exclude=["id", "guid", "created", "modified"])
            for model_proxy in test_model_proxies
        ]

        test_model_proxies_data = [
            {'name': u'modelComponent', 'stereotype': u'document', 'package': None, 'documentation': u'A ModelCompnent is nice.', 'namespace': None, 'ontology': self.test_ontology.pk, 'order': 0},
            {'name': u'responsibleParty', 'stereotype': None, 'package': None, 'documentation': u'a stripped-down responsible party to use for testing purposes.', 'namespace': None, 'ontology': self.test_ontology.pk, 'order': 1},
            {'name': u'contactType', 'stereotype': None, 'package': None, 'documentation': u'a stripped-down contactType just for testing purposes.', 'namespace': None, 'ontology': self.test_ontology.pk, 'order': 2},
        ]

        for actual_model_proxy_data, test_model_proxy_data in zip(actual_model_proxies_data, test_model_proxies_data):
            self.assertDictEqual(actual_model_proxy_data, test_model_proxy_data)

        actual_property_proxies_data = [
            serialize_model_to_dict(property_proxy, exclude=["id", "guid", "created", "modified"])
            for property_proxy in test_property_proxies
        ]

        test_property_proxies_data = [
            {'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'string', 'stereotype': None, 'relationship_target_model': None, 'relationship_target_name': None, 'enumeration_choices': u'', 'documentation': u'I am a string', 'namespace': None, 'atomic_type': u'DEFAULT', 'order': 0, 'is_label': True, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[0].pk, 'enumeration_multi': False},
            {'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'boolean', 'stereotype': None, 'relationship_target_model': None, 'relationship_target_name': None, 'enumeration_choices': u'', 'documentation': u'I am a boolean', 'namespace': None, 'atomic_type': u'BOOLEAN', 'order': 1, 'is_label': False, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[0].pk, 'enumeration_multi': False},
            {'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'date', 'stereotype': None, 'relationship_target_model': None, 'relationship_target_name': None, 'enumeration_choices': u'', 'documentation': u'I am a date', 'namespace': None, 'atomic_type': u'DATE', 'order': 2, 'is_label': False, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[0].pk, 'enumeration_multi': False},
            {'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'uncategorized', 'stereotype': None, 'relationship_target_model': None, 'relationship_target_name': None, 'enumeration_choices': u'', 'documentation': u'I am an uncategorized string', 'namespace': None, 'atomic_type': u'DEFAULT', 'order': 3, 'is_label': False, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[0].pk, 'enumeration_multi': False},
            {'field_type': u'ENUMERATION', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'enumeration', 'stereotype': None, 'relationship_target_model': None, 'relationship_target_name': None, 'enumeration_choices': u'one|two|three', 'documentation': u'I am an enumreation', 'namespace': None, 'atomic_type': None, 'order': 4, 'is_label': False, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[0].pk, 'enumeration_multi': False},
            {'field_type': u'RELATIONSHIP', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'author', 'stereotype': None, 'relationship_target_model': 2, 'relationship_target_name': u'responsibleParty', 'enumeration_choices': u'', 'documentation': u'I am a relationship', 'namespace': None, 'atomic_type': None, 'order': 5, 'is_label': False, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[0].pk, 'enumeration_multi': False},
            {'field_type': u'RELATIONSHIP', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'contact', 'stereotype': None, 'relationship_target_model': 2, 'relationship_target_name': u'responsibleParty', 'enumeration_choices': u'', 'documentation': u'I am a relationship', 'namespace': None, 'atomic_type': None, 'order': 6, 'is_label': False, 'enumeration_open': False, 'cardinality': u'0|*', 'model_proxy': test_model_proxies[0].pk, 'enumeration_multi': False},
            {'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'individualName', 'stereotype': None, 'relationship_target_model': None, 'relationship_target_name': None, 'enumeration_choices': u'', 'documentation': u'', 'namespace': None, 'atomic_type': u'DEFAULT', 'order': 0, 'is_label': True, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[1].pk, 'enumeration_multi': False},
            {'field_type': u'RELATIONSHIP', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'contactInfo', 'stereotype': None, 'relationship_target_model': 3, 'relationship_target_name': u'contactType', 'enumeration_choices': u'', 'documentation': u'', 'namespace': None, 'atomic_type': None, 'order': 1, 'is_label': False, 'enumeration_open': False, 'cardinality': u'1|1', 'model_proxy': test_model_proxies[1].pk, 'enumeration_multi': False},
            {'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'phone', 'stereotype': None, 'relationship_target_model': None, 'relationship_target_name': None, 'enumeration_choices': u'', 'documentation': u'', 'namespace': None, 'atomic_type': u'DEFAULT', 'order': 0, 'is_label': False, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[2].pk, 'enumeration_multi': False},
            {'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'address', 'stereotype': None, 'relationship_target_model': None, 'relationship_target_name': None, 'enumeration_choices': u'', 'documentation': u'', 'namespace': None, 'atomic_type': u'TEXT', 'order': 1, 'is_label': False, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[2].pk, 'enumeration_multi': False},
        ]

        for actual_property_proxy_data, test_property_proxy_data in zip(actual_property_proxies_data, test_property_proxies_data):
            self.assertDictEqual(actual_property_proxy_data, test_property_proxy_data)

    @incomplete_test
    def test_ontology_reregister(self):
        pass
