from django.forms import model_to_dict
from CIM_Questionnaire.questionnaire.models import MetadataCategorization, MetadataModelProxy
from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase


class TestMetadataVersion(TestQuestionnaireBase):

    def test_setUp(self):
        qs = MetadataCategorization.objects.all()
        self.assertEqual(len(qs),1)

    def test_register_models(self):

        models = MetadataModelProxy.objects.all()

        excluded_fields = ["id","version"]
        serialized_models = [model_to_dict(model,exclude=excluded_fields) for model in models]

        to_test = [{'order': 0, 'documentation': u'blah', 'name': u'modelcomponent', 'stereotype': u'document', 'package': None}, {'order': 1, 'documentation': u'blah', 'name': u'gridspec', 'stereotype': u'document', 'package': None}]

        # test that the models have the expected standard fields
        for s,t in zip(serialized_models,to_test):
            self.assertDictEqual(s,t)

        # test that they have the expected foreignkeys
        for model in models:
            self.assertEqual(model.version,self.version)

    def test_register_standard_properties(self):

        models = MetadataModelProxy.objects.all()

        to_test = [
            [
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'shortName', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 0, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'TEXT'},
            ],
            [
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'shortName', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 0, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'DEFAULT'},
                {'field_type': u'ENUMERATION', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'type', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'one|two|three', 'documentation': u'', 'order': 1, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'TEXT'},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'longName', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 2, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'TEXT'},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'description', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 3, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'TEXT'},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'purpose', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 4, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'TEXT'},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'license', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 5, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'TEXT'},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'timing', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 6, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'TEXT'},
                {'field_type': u'RELATIONSHIP', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'grid', 'enumeration_multi': False, 'relationship_target_name': u'gridspec', 'enumeration_choices': u'', 'documentation': u'', 'order': 7, 'enumeration_open': False, 'relationship_cardinality': u'0|*', 'atomic_type': u'TEXT'}
            ]
        ]

        excluded_fields = ["id","model_proxy","relationship_target_model"]

        for model,standard_properties_to_test in zip(models,to_test):
            standard_properties = model.standard_properties.all()
            serialized_standard_properties = [model_to_dict(standard_property,exclude=excluded_fields) for standard_property in standard_properties]

            # test that the properties have the expected standard fields
            for serialized_standard_property,standard_property_to_test in zip(serialized_standard_properties,standard_properties_to_test):
                self.assertDictEqual(serialized_standard_property,standard_property_to_test)

            for standard_property in standard_properties:
                self.assertEqual(standard_property.model_proxy,model)

                if standard_property.relationship_target_model or standard_property.relationship_target_name:
                    self.assertEqual(standard_property.relationship_target_model.name,standard_property.relationship_target_name)
