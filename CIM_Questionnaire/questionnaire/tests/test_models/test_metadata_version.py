import os
import copy

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase

from CIM_Questionnaire.questionnaire.models.metadata_version import MetadataVersion
from CIM_Questionnaire.questionnaire.models.metadata_version import UPLOAD_PATH as VERSION_UPLOAD_PATH
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy, MetadataStandardPropertyProxy
from CIM_Questionnaire.questionnaire.utils import model_to_data

class TestMetadataVersion(TestQuestionnaireBase):

    def setUp(self):
        # don't call TestQuestionnaireBase.setUp() so that the version has not been registered
        pass


    def test_register(self):

        test_version_path = os.path.join(VERSION_UPLOAD_PATH, "test_version.xml")
        test_version = MetadataVersion(name="version", file=test_version_path, url="http://www.test.com/version.xsd")
        test_version.save()

        version_qs = MetadataVersion.objects.all()
        model_qs = MetadataModelProxy.objects.filter(version=test_version)
        property_qs = MetadataStandardPropertyProxy.objects.all()

        self.assertEqual(len(version_qs), 1)
        self.assertEqual(len(model_qs), 0)
        self.assertEqual(len(property_qs), 0)
        self.assertEqual(test_version.registered, False)

        test_version.register()
        test_version.save()

        self.assertEqual(test_version.registered, True)

        model_qs = MetadataModelProxy.objects.filter(version=test_version)
        property_qs = MetadataStandardPropertyProxy.objects.all()

        self.assertEqual(len(model_qs), 3)
        self.assertEqual(len(property_qs), 11)

        test_models_data = [
            {'name': u'modelComponent',     'stereotype': u'document',  'package': None, 'documentation': u'A ModelCompnent is nice.',                                          'namespace': None, 'order': 0, 'version': test_version.pk, },
            {'name': u'responsibleParty',   'stereotype': None,         'package': None, 'documentation': u'a stripped-down responsible party to use for testing purposes.',    'namespace': None, 'order': 1, 'version': test_version.pk, },
            {'name': u'contactType',        'stereotype': None,         'package': None, 'documentation': u'a stripped-down contactType just for testing purposes.',            'namespace': None, 'order': 2, 'version': test_version.pk, },
        ]
        models_data = [model_to_data(model) for model in model_qs]
        for actual_model_data, test_model_data in zip(models_data, test_models_data):
            self.assertDictEqual(actual_model_data, test_model_data, excluded_keys=["id"])

        test_properties_data = [
            {'field_type': u'ATOMIC',       'atomic_default': u'', 'enumeration_nullable': False, 'name': u'phone',             'stereotype': None, 'relationship_target_model': None,                                                                 'relationship_target_name': None,                   'enumeration_choices': u'',                     'documentation': u'',                               'atomic_type': u'DEFAULT',  'is_label': False, 'enumeration_open': False, 'model_proxy': MetadataModelProxy.objects.get(name__iexact="ContactType").pk,         'relationship_cardinality': u'',    'order': 0, 'enumeration_multi': False},
            {'field_type': u'ATOMIC',       'atomic_default': u'', 'enumeration_nullable': False, 'name': u'individualName',    'stereotype': None, 'relationship_target_model': None,                                                                 'relationship_target_name': None,                   'enumeration_choices': u'',                     'documentation': u'',                               'atomic_type': u'DEFAULT',  'is_label': True,  'enumeration_open': False, 'model_proxy': MetadataModelProxy.objects.get(name__iexact="ResponsibleParty").pk,    'relationship_cardinality': u'',    'order': 0, 'enumeration_multi': False},
            {'field_type': u'ATOMIC',       'atomic_default': u'', 'enumeration_nullable': False, 'name': u'string',            'stereotype': None, 'relationship_target_model': None,                                                                 'relationship_target_name': None,                   'enumeration_choices': u'',                     'documentation': u'I am a string',                  'atomic_type': u'DEFAULT',  'is_label': True,  'enumeration_open': False, 'model_proxy': MetadataModelProxy.objects.get(name__iexact="ModelComponent").pk,      'relationship_cardinality': u'',    'order': 0, 'enumeration_multi': False},
            {'field_type': u'ATOMIC',       'atomic_default': u'', 'enumeration_nullable': False, 'name': u'address',           'stereotype': None, 'relationship_target_model': None,                                                                 'relationship_target_name': None,                   'enumeration_choices': u'',                     'documentation': u'',                               'atomic_type': u'TEXT',     'is_label': False, 'enumeration_open': False, 'model_proxy': MetadataModelProxy.objects.get(name__iexact="ContactType").pk,         'relationship_cardinality': u'',    'order': 1, 'enumeration_multi': False},
            {'field_type': u'ATOMIC',       'atomic_default': u'', 'enumeration_nullable': False, 'name': u'boolean',           'stereotype': None, 'relationship_target_model': None,                                                                 'relationship_target_name': None,                   'enumeration_choices': u'',                     'documentation': u'I am a boolean',                 'atomic_type': u'BOOLEAN',  'is_label': False, 'enumeration_open': False, 'model_proxy': MetadataModelProxy.objects.get(name__iexact="ModelComponent").pk,      'relationship_cardinality': u'',    'order': 1, 'enumeration_multi': False},
            {'field_type': u'RELATIONSHIP', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'contactInfo',       'stereotype': None, 'relationship_target_model': MetadataModelProxy.objects.get(name__iexact="ContactType").pk,        'relationship_target_name': u'contactType',         'enumeration_choices': u'',                     'documentation': u'',                               'atomic_type': None,        'is_label': False, 'enumeration_open': False, 'model_proxy': MetadataModelProxy.objects.get(name__iexact="ResponsibleParty").pk,    'relationship_cardinality': u'1|1', 'order': 1, 'enumeration_multi': False},
            {'field_type': u'ATOMIC',       'atomic_default': u'', 'enumeration_nullable': False, 'name': u'date',              'stereotype': None, 'relationship_target_model': None,                                                                 'relationship_target_name': None,                   'enumeration_choices': u'',                     'documentation': u'I am a date',                    'atomic_type': u'DATE',     'is_label': False, 'enumeration_open': False, 'model_proxy': MetadataModelProxy.objects.get(name__iexact="ModelComponent").pk,      'relationship_cardinality': u'',    'order': 2, 'enumeration_multi': False},
            {'field_type': u'ATOMIC',       'atomic_default': u'', 'enumeration_nullable': False, 'name': u'uncategorized',     'stereotype': None, 'relationship_target_model': None,                                                                 'relationship_target_name': None,                   'enumeration_choices': u'',                     'documentation': u'I am an uncategorized string',   'atomic_type': u'DEFAULT',  'is_label': False, 'enumeration_open': False, 'model_proxy': MetadataModelProxy.objects.get(name__iexact="ModelComponent").pk,      'relationship_cardinality': u'',    'order': 3, 'enumeration_multi': False},
            {'field_type': u'ENUMERATION',  'atomic_default': u'', 'enumeration_nullable': False, 'name': u'enumeration',       'stereotype': None, 'relationship_target_model': None,                                                                 'relationship_target_name': None,                   'enumeration_choices': u'one|two|three',        'documentation': u'I am an enumreation',            'atomic_type': None,        'is_label': False, 'enumeration_open': False, 'model_proxy': MetadataModelProxy.objects.get(name__iexact="ModelComponent").pk,      'relationship_cardinality': u'',    'order': 4, 'enumeration_multi': False},
            {'field_type': u'RELATIONSHIP', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'author',            'stereotype': None, 'relationship_target_model': MetadataModelProxy.objects.get(name__iexact="ResponsibleParty").pk,   'relationship_target_name': u'responsibleParty',    'enumeration_choices': u'',                     'documentation': u'I am a relationship',            'atomic_type': None,        'is_label': False, 'enumeration_open': False, 'model_proxy': MetadataModelProxy.objects.get(name__iexact="ModelComponent").pk,      'relationship_cardinality': u'0|1', 'order': 5, 'enumeration_multi': False},
            {'field_type': u'RELATIONSHIP', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'contact',           'stereotype': None, 'relationship_target_model': MetadataModelProxy.objects.get(name__iexact="ResponsibleParty").pk,   'relationship_target_name': u'responsibleParty',    'enumeration_choices': u'',                     'documentation': u'I am a relationship',            'atomic_type': None,        'is_label': False, 'enumeration_open': False, 'model_proxy': MetadataModelProxy.objects.get(name__iexact="ModelComponent").pk,      'relationship_cardinality': u'0|*', 'order': 6, 'enumeration_multi': False},
        ]
        properties_data = [model_to_data(property) for property in property_qs]
        for actual_property_data, test_property_data in zip(properties_data, test_properties_data):
            self.assertDictEqual(actual_property_data, test_property_data, excluded_keys=["id",])

    def test_reregister(self):

        # this registers the "test" vocabulary by default
        super(TestMetadataVersion,self).setUp()
        test_version = self.version

        old_models = copy.deepcopy(list(MetadataModelProxy.objects.all()))
        old_properties = copy.deepcopy(list(MetadataStandardPropertyProxy.objects.all()))

        changed_vocabulary_path = os.path.join(VERSION_UPLOAD_PATH, "test_version_changed.xml")
        test_version.file = changed_vocabulary_path
        test_version.save()

        test_version.register()
        test_version.save()


        version_qs = MetadataVersion.objects.all()
        model_qs = MetadataModelProxy.objects.filter(version=test_version)
        property_qs = MetadataStandardPropertyProxy.objects.all()

        self.assertEqual(len(version_qs), 1)
        self.assertEqual(len(model_qs), 2)
        self.assertEqual(len(property_qs), 7)
        self.assertEqual(test_version.registered, True)

        test_models_data = [
            {'name': u'modelComponent',     'stereotype': u'document',  'package': None, 'documentation': u'A ModelCompnent is nice.',                                          'namespace': None, 'order': 0, 'version': test_version.pk, },
            {'name': u'responsibleParty',   'stereotype': None,         'package': None, 'documentation': u'a stripped-down responsible party to use for testing purposes.',    'namespace': None, 'order': 1, 'version': test_version.pk, },
        ]
        models_data = [model_to_data(model) for model in model_qs]
        for actual_model_data, test_model_data in zip(models_data, test_models_data):
            self.assertDictEqual(actual_model_data, test_model_data, excluded_keys=["id"])

        test_properties_data = [
            {'field_type': u'ATOMIC',       'atomic_default': u'', 'enumeration_nullable': False, 'name': u'individualName',    'stereotype': None, 'relationship_target_model': None,                                                                 'relationship_target_name': None,                   'enumeration_choices': u'',                     'documentation': u'',                               'atomic_type': u'DEFAULT',  'is_label': True,  'enumeration_open': False, 'model_proxy': MetadataModelProxy.objects.get(name__iexact="ResponsibleParty").pk,    'relationship_cardinality': u'',    'order': 0, 'enumeration_multi': False},
            {'field_type': u'ATOMIC',       'atomic_default': u'', 'enumeration_nullable': False, 'name': u'new_string',        'stereotype': None, 'relationship_target_model': None,                                                                 'relationship_target_name': None,                   'enumeration_choices': u'',                     'documentation': u'I am a new string',              'atomic_type': u'DEFAULT',  'is_label': True,  'enumeration_open': False, 'model_proxy': MetadataModelProxy.objects.get(name__iexact="ModelComponent").pk,      'relationship_cardinality': u'',    'order': 0, 'enumeration_multi': False},
            {'field_type': u'ATOMIC',       'atomic_default': u'', 'enumeration_nullable': False, 'name': u'date',              'stereotype': None, 'relationship_target_model': None,                                                                 'relationship_target_name': None,                   'enumeration_choices': u'',                     'documentation': u'I am a date',                    'atomic_type': u'DATE',     'is_label': False, 'enumeration_open': False, 'model_proxy': MetadataModelProxy.objects.get(name__iexact="ModelComponent").pk,      'relationship_cardinality': u'',    'order': 1, 'enumeration_multi': False},
            {'field_type': u'ATOMIC',       'atomic_default': u'', 'enumeration_nullable': False, 'name': u'uncategorized',     'stereotype': None, 'relationship_target_model': None,                                                                 'relationship_target_name': None,                   'enumeration_choices': u'',                     'documentation': u'I am an uncategorized string',   'atomic_type': u'DEFAULT',  'is_label': False, 'enumeration_open': False, 'model_proxy': MetadataModelProxy.objects.get(name__iexact="ModelComponent").pk,      'relationship_cardinality': u'',    'order': 2, 'enumeration_multi': False},
            {'field_type': u'ENUMERATION',  'atomic_default': u'', 'enumeration_nullable': False, 'name': u'enumeration',       'stereotype': None, 'relationship_target_model': None,                                                                 'relationship_target_name': None,                   'enumeration_choices': u'one|two|three',        'documentation': u'I am an enumreation',            'atomic_type': None,        'is_label': False, 'enumeration_open': False, 'model_proxy': MetadataModelProxy.objects.get(name__iexact="ModelComponent").pk,      'relationship_cardinality': u'',    'order': 3, 'enumeration_multi': False},
            {'field_type': u'RELATIONSHIP', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'author',            'stereotype': None, 'relationship_target_model': MetadataModelProxy.objects.get(name__iexact="ResponsibleParty").pk,   'relationship_target_name': u'responsibleParty',    'enumeration_choices': u'',                     'documentation': u'I am a relationship',            'atomic_type': None,        'is_label': False, 'enumeration_open': False, 'model_proxy': MetadataModelProxy.objects.get(name__iexact="ModelComponent").pk,      'relationship_cardinality': u'0|1', 'order': 4, 'enumeration_multi': False},
        ]
        properties_data = [model_to_data(property) for property in property_qs]
        for actual_property_data, test_property_data in zip(properties_data, test_properties_data):
            self.assertDictEqual(actual_property_data, test_property_data, excluded_keys=["id",])
