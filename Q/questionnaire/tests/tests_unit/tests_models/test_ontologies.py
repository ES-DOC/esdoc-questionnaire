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


from Q.questionnaire.tests.test_base import TestQBase, create_ontology, remove_ontology, incomplete_test
from Q.questionnaire.q_utils import serialize_model_to_dict, sort_list_by_key
from Q.questionnaire.models.models_ontologies import *


class TestQOntolgoy(TestQBase):

    def setUp(self):

        # don't do the base setUp (it would interfere w/ the ids of the ontology created below)
        # super(TestQOntolgoy, self).setUp()

        # create some test ontologies...
        self.test_ontology_cim_1 = create_ontology(
            filename="test_ontology_1.xml",
            name="test_ontology",
            version="1.0",
            type=CIMTypes.CIM1.get_type(),
        )

        self.test_ontology_cim_2 = create_ontology(
            filename="test_ontology_2.xml",
            name="test_ontology",
            version="2.0",
            type=CIMTypes.CIM2.get_type(),
        )

    def tearDown(self):

        # don't do the base tearDown
        # super(TestQOntolgoy, self).tearDown()

        # delete the test ontologies
        remove_ontology(ontology=self.test_ontology_cim_1)
        remove_ontology(ontology=self.test_ontology_cim_2)

    def test_ontology_get_key(self):

        test_key = "test_ontology_1.0"
        self.assertEqual(self.test_ontology_cim_1.get_key(), test_key)
        self.assertEqual(QOntology.objects.get(key=test_key), self.test_ontology_cim_1)

        self.test_ontology_cim_1.version = "123"
        self.test_ontology_cim_1.save()

        test_key = "test_ontology_123"
        self.assertEqual(self.test_ontology_cim_1.get_key(), test_key)
        self.assertEqual(QOntology.objects.get(key=test_key), self.test_ontology_cim_1)

    def test_ontology_get_name_and_version_from_key(self):

        with self.assertRaises(QError):
            get_name_and_version_from_key("invalid_key")

        name, version = get_name_and_version_from_key("test_ontology_1")
        self.assertEqual(name, "test_ontology")
        self.assertEqual(version, "1.0.0")

        name, version = get_name_and_version_from_key("test_ontology_1.2")
        self.assertEqual(name, "test_ontology")
        self.assertEqual(version, "1.2.0")

        name, version = get_name_and_version_from_key("test_ontology_1.2.3")
        self.assertEqual(name, "test_ontology")
        self.assertEqual(version, "1.2.3")

    def test_ontology_validity_cim1(self):
        invalid_ontology = create_ontology(
            filename="test_ontology_2.xml",
            name="test_invalid_ontology",
            version="1.0",
            type=CIMTypes.CIM1.get_type(),
        )
        with self.assertRaises(ValidationError):
            # this is an invalid CIM1 file (it is a CIM2 file)
            invalid_ontology.full_clean()

    def test_ontology_register_cim1(self):

        self.assertFalse(self.test_ontology_cim_1.is_registered)
        self.test_ontology_cim_1.register()
        self.assertTrue(self.test_ontology_cim_1.is_registered)

        test_model_proxies = self.test_ontology_cim_1.model_proxies.all()
        test_property_proxies = QStandardPropertyProxy.objects.filter(model_proxy__ontology=self.test_ontology_cim_1)

        actual_model_proxies_data = [
            serialize_model_to_dict(model_proxy, exclude=["id", "guid", "created", "modified"])
            for model_proxy in test_model_proxies
        ]

        test_model_proxies_data = sort_list_by_key(
            [
                {'name': u'modelComponent', 'stereotype': u'document', 'package': None, 'documentation': u'A ModelCompnent is nice.', 'namespace': None, 'ontology': self.test_ontology_cim_1.pk, 'order': 1},
                {'name': u'responsibleParty', 'stereotype': None, 'package': None, 'documentation': u'a stripped-down responsible party to use for testing purposes.', 'namespace': None, 'ontology': self.test_ontology_cim_1.pk, 'order': 2},
                {'name': u'contactType', 'stereotype': None, 'package': None, 'documentation': u'a stripped-down contactType just for testing purposes.', 'namespace': None, 'ontology': self.test_ontology_cim_1.pk, 'order': 3},
            ],
            "order",
        )

        for actual_model_proxy_data, test_model_proxy_data in zip(actual_model_proxies_data, test_model_proxies_data):
            self.assertDictEqual(actual_model_proxy_data, test_model_proxy_data)

        actual_property_proxies_data = [
            serialize_model_to_dict(property_proxy, exclude=["id", "guid", "created", "modified"])
            for property_proxy in test_property_proxies
        ]

        test_property_proxies_data = sort_list_by_key(
            [
                {'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'string', 'stereotype': None, 'relationship_target_model': None, 'relationship_target_name': None, 'enumeration_choices': u'', 'documentation': u'I am a string', 'namespace': None, 'atomic_type': u'DEFAULT', 'order': 1, 'is_label': True, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[0].pk, 'enumeration_multi': False},
                {'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'individualName', 'stereotype': None, 'relationship_target_model': None, 'relationship_target_name': None, 'enumeration_choices': u'', 'documentation': u'', 'namespace': None, 'atomic_type': u'DEFAULT', 'order': 1, 'is_label': True, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[1].pk, 'enumeration_multi': False},
                {'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'phone', 'stereotype': None, 'relationship_target_model': None, 'relationship_target_name': None, 'enumeration_choices': u'', 'documentation': u'', 'namespace': None, 'atomic_type': u'DEFAULT', 'order': 1, 'is_label': False, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[2].pk, 'enumeration_multi': False},
                {'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'boolean', 'stereotype': None, 'relationship_target_model': None, 'relationship_target_name': None, 'enumeration_choices': u'', 'documentation': u'I am a boolean', 'namespace': None, 'atomic_type': u'BOOLEAN', 'order': 2, 'is_label': False, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[0].pk, 'enumeration_multi': False},
                {'field_type': u'RELATIONSHIP', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'contactInfo', 'stereotype': None, 'relationship_target_model': self.test_ontology_cim_1.model_proxies.get(name__iexact="contactType").pk, 'relationship_target_name': u'contactType', 'enumeration_choices': u'', 'documentation': u'', 'namespace': None, 'atomic_type': None, 'order': 2, 'is_label': False, 'enumeration_open': False, 'cardinality': u'1|1', 'model_proxy': test_model_proxies[1].pk, 'enumeration_multi': False},
                {'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'address', 'stereotype': None, 'relationship_target_model': None, 'relationship_target_name': None, 'enumeration_choices': u'', 'documentation': u'', 'namespace': None, 'atomic_type': u'TEXT', 'order': 2, 'is_label': False, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[2].pk, 'enumeration_multi': False},
                {'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'date', 'stereotype': None, 'relationship_target_model': None, 'relationship_target_name': None, 'enumeration_choices': u'', 'documentation': u'I am a date', 'namespace': None, 'atomic_type': u'DATE', 'order': 3, 'is_label': False, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[0].pk, 'enumeration_multi': False},
                {'field_type': u'ATOMIC', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'uncategorized', 'stereotype': None, 'relationship_target_model': None, 'relationship_target_name': None, 'enumeration_choices': u'', 'documentation': u'I am an uncategorized string', 'namespace': None, 'atomic_type': u'DEFAULT', 'order': 4, 'is_label': False, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[0].pk, 'enumeration_multi': False},
                {'field_type': u'ENUMERATION', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'enumeration', 'stereotype': None, 'relationship_target_model': None, 'relationship_target_name': None, 'enumeration_choices': u'one|two|three', 'documentation': u'I am an enumreation', 'namespace': None, 'atomic_type': None, 'order': 5, 'is_label': False, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[0].pk, 'enumeration_multi': False},
                {'field_type': u'RELATIONSHIP', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'author', 'stereotype': None, 'relationship_target_model': self.test_ontology_cim_1.model_proxies.get(name__iexact="responsibleParty").pk, 'relationship_target_name': u'responsibleParty', 'enumeration_choices': u'', 'documentation': u'I am a relationship', 'namespace': None, 'atomic_type': None, 'order': 6, 'is_label': False, 'enumeration_open': False, 'cardinality': u'0|1', 'model_proxy': test_model_proxies[0].pk, 'enumeration_multi': False},
                {'field_type': u'RELATIONSHIP', 'atomic_default': None, 'enumeration_nullable': False, 'name': u'contact', 'stereotype': None, 'relationship_target_model': self.test_ontology_cim_1.model_proxies.get(name__iexact="responsibleParty").pk, 'relationship_target_name': u'responsibleParty', 'enumeration_choices': u'', 'documentation': u'I am a relationship', 'namespace': None, 'atomic_type': None, 'order': 7, 'is_label': False, 'enumeration_open': False, 'cardinality': u'0|*', 'model_proxy': test_model_proxies[0].pk, 'enumeration_multi': False},
            ],
            "order",
        )

        for actual_property_proxy_data, test_property_proxy_data in zip(actual_property_proxies_data, test_property_proxies_data):
            self.assertDictEqual(actual_property_proxy_data, test_property_proxy_data)

    def test_ontology_validity_cim2(self):
        invalid_ontology = create_ontology(
            filename="test_ontology_1.xml",
            name="test_invalid_ontology",
            version="1.0",
            type=CIMTypes.CIM2.get_type(),
        )
        with self.assertRaises(ValidationError):
            # this is an invalid CIM2 file (it is a CIM1 file)
            invalid_ontology.full_clean()

    def test_ontology_register_cim2(self):

        import ipdb; ipdb.set_trace()
        self.assertFalse(self.test_ontology_cim_2.is_registered)
        self.test_ontology_cim_2.register()
        self.assertTrue(self.test_ontology_cim_2.is_registered)

    @incomplete_test
    def test_ontology_reregister(self):
        pass
