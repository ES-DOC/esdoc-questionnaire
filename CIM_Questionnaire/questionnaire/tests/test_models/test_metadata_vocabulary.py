import os
import copy

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase

from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import UPLOAD_PATH as VOCABULARY_UPLOAD_PATH
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataScientificCategoryProxy, MetadataScientificPropertyProxy, MetadataComponentProxy, MetadataModelProxy

from CIM_Questionnaire.questionnaire.utils import CIM_DOCUMENT_TYPES
from CIM_Questionnaire.questionnaire.utils import model_to_data, get_joined_keys_dict, find_in_sequence

class TestMetadataVocabulary(TestQuestionnaireBase):

    def setUp(self):
        # don't call TestQuestionnaireBase.setUp() so that the vocabulary has not been registered
        pass


    def test_register(self):

        test_document_type = "modelcomponent"
        self.assertIn(test_document_type, CIM_DOCUMENT_TYPES, msg="Unrecognized vocabulary document type: %s" % (test_document_type))
        test_vocabulary_path = os.path.join(VOCABULARY_UPLOAD_PATH, "test_vocabulary_bdl.xml")
        test_vocabulary = MetadataVocabulary(name="vocabulary", file=test_vocabulary_path, document_type=test_document_type)
        test_vocabulary.save()

        vocabulary_qs = MetadataVocabulary.objects.all()
        component_qs = MetadataComponentProxy.objects.filter(vocabulary=test_vocabulary)
        category_qs = MetadataScientificCategoryProxy.objects.all()
        property_qs = MetadataScientificPropertyProxy.objects.all()

        self.assertEqual(len(vocabulary_qs), 1)
        self.assertEqual(len(category_qs), 0)
        self.assertEqual(len(component_qs), 0)
        self.assertEqual(len(property_qs), 0)
        self.assertEqual(test_vocabulary.registered, False)

        test_vocabulary.register()
        test_vocabulary.save()

        self.assertEqual(test_vocabulary.registered, True)

        component_qs = MetadataComponentProxy.objects.filter(vocabulary=test_vocabulary)
        category_qs = MetadataScientificCategoryProxy.objects.all()
        property_qs = MetadataScientificPropertyProxy.objects.all()

        self.assertEqual(len(component_qs), 5)
        self.assertEqual(len(category_qs), 10)
        self.assertEqual(len(property_qs), 9)

        test_vocabulary_data = {'registered': True, 'document_type': u'modelcomponent', 'name': u'vocabulary'}
        actual_vocabulary_data = model_to_data(test_vocabulary)
        self.assertDictEqual(actual_vocabulary_data, test_vocabulary_data, excluded_keys=["id", "file", "last_modified", "created",])

        test_components_data = [
            {'vocabulary': test_vocabulary.pk, 'documentation': u'', 'order': 1, 'name': u'TestModel'},
            {'vocabulary': test_vocabulary.pk, 'documentation': u'', 'order': 2, 'name': u'TestModelKeyProperties'},
            {'vocabulary': test_vocabulary.pk, 'documentation': u'', 'order': 3, 'name': u'PretendSubModel'},
            {'vocabulary': test_vocabulary.pk, 'documentation': u'', 'order': 4, 'name': u'SubModel'},
            {'vocabulary': test_vocabulary.pk, 'documentation': u'', 'order': 5, 'name': u'SubSubModel'},
        ]
        components_data = [model_to_data(component) for component in component_qs]
        for actual_component_data, test_component_data in zip(components_data, test_components_data):
            self.assertDictEqual(actual_component_data, test_component_data, excluded_keys=["id", "parent", "last_modified", "created",])

        component_testmodel = MetadataComponentProxy.objects.get(name__iexact="testmodel")
        component_testmodelkeyproperties = MetadataComponentProxy.objects.get(name__iexact="testmodelkeyproperties")
        component_pretendsubmodel = MetadataComponentProxy.objects.get(name__iexact="pretendsubmodel")
        component_submodel = MetadataComponentProxy.objects.get(name__iexact="submodel")
        component_subsubmodel = MetadataComponentProxy.objects.get(name__iexact="subsubmodel")

        test_categories_data = [
            {'name': u'General Attributes', 'component': component_testmodelkeyproperties.pk,   'key': u'general-attributes',   'order': 0, 'description': u''},
            {'name': u'General Attributes', 'component': component_submodel.pk,                 'key': u'general-attributes',   'order': 0, 'description': u''},
            {'name': u'General Attributes', 'component': component_testmodel.pk,                'key': u'general-attributes',   'order': 0, 'description': u''},
            {'name': u'General Attributes', 'component': component_subsubmodel.pk,              'key': u'general-attributes',   'order': 0, 'description': u''},
            {'name': u'General Attributes', 'component': component_pretendsubmodel.pk,          'key': u'general-attributes',   'order': 0, 'description': u''},
            {'name': u'CategoryOne',        'component': component_subsubmodel.pk,              'key': u'categoryone',          'order': 1, 'description': u''},
            {'name': u'CategoryOne',        'component': component_testmodelkeyproperties.pk,   'key': u'categoryone',          'order': 1, 'description': u''},
            {'name': u'CategoryOne',        'component': component_pretendsubmodel.pk,          'key': u'categoryone',          'order': 1, 'description': u''},
            {'name': u'CategoryOne',        'component': component_submodel.pk,                 'key': u'categoryone',          'order': 1, 'description': u''},
            {'name': u'CategoryTwo',        'component': component_testmodelkeyproperties.pk,   'key': u'categorytwo',          'order': 2, 'description': u''},
        ]
        categories_data = [model_to_data(category) for category in category_qs]
        for actual_category_data, test_category_data in zip(categories_data, test_categories_data):
            self.assertDictEqual(actual_category_data, test_category_data, excluded_keys=["id", "last_modified", "created","description"]) # description can be an empty string or None,
                                                                                                                                           # depending on whether this went through forms or not
                                                                                                                                           # for this test, I don't actually care

        category_testmodel_generalattributes = MetadataScientificCategoryProxy.objects.get(component=component_testmodel, name__iexact="general attributes")
        category_testmodelkeyproperties_generalattributes = MetadataScientificCategoryProxy.objects.get(component=component_testmodelkeyproperties, name__iexact="general attributes")
        category_testmodelkeyproperties_categoryone = MetadataScientificCategoryProxy.objects.get(component=component_testmodelkeyproperties, name__iexact="categoryone")
        category_testmodelkeyproperties_categorytwo = MetadataScientificCategoryProxy.objects.get(component=component_testmodelkeyproperties, name__iexact="categorytwo")
        category_pretendsubmodel_generalattributes = MetadataScientificCategoryProxy.objects.get(component=component_pretendsubmodel, name__iexact="general attributes")
        category_pretendsubmodel_categoryone = MetadataScientificCategoryProxy.objects.get(component=component_pretendsubmodel, name__iexact="categoryone")
        category_submodel_generalattributes = MetadataScientificCategoryProxy.objects.get(component=component_submodel, name__iexact="general attributes")
        category_submodel_categoryone = MetadataScientificCategoryProxy.objects.get(component=component_submodel, name__iexact="categoryone")
        category_subsubmodel_generalattributes = MetadataScientificCategoryProxy.objects.get(component=component_subsubmodel, name__iexact="general attributes")
        category_subsubmodel_categoryone = MetadataScientificCategoryProxy.objects.get(component=component_subsubmodel, name__iexact="categoryone")

        test_properties_data = [
            {'category': category_subsubmodel_categoryone.pk,                  'field_type': None, 'name': u'name',    'documentation': u'I am free text.',            'component': component_subsubmodel.pk,              'values': u'', 'is_label': False, 'choice': u'keyboard', 'order': 0},
            {'category': category_pretendsubmodel_categoryone.pk,              'field_type': None, 'name': u'name',    'documentation': u'I am free text.',            'component': component_pretendsubmodel.pk,          'values': u'', 'is_label': False, 'choice': u'keyboard', 'order': 0},
            {'category': category_submodel_categoryone.pk,                     'field_type': None, 'name': u'name',    'documentation': u'I am free text.',            'component': component_submodel.pk,                 'values': u'', 'is_label': False, 'choice': u'keyboard', 'order': 0},
            {'category': category_testmodelkeyproperties_generalattributes.pk, 'field_type': None, 'name': u'name',    'documentation': u'I am free text.',            'component': component_testmodelkeyproperties.pk,   'values': u'', 'is_label': False, 'choice': u'keyboard', 'order': 0},
            {'category': category_testmodelkeyproperties_categoryone.pk,       'field_type': None, 'name': u'name',    'documentation': u'I am free text.',            'component': component_testmodelkeyproperties.pk,   'values': u'', 'is_label': False, 'choice': u'keyboard', 'order': 0},
            {'category': category_testmodelkeyproperties_categorytwo.pk,       'field_type': None, 'name': u'name',    'documentation': u'I am free text.',            'component': component_testmodelkeyproperties.pk,   'values': u'', 'is_label': False, 'choice': u'keyboard', 'order': 0},
            {'category': category_testmodelkeyproperties_generalattributes.pk, 'field_type': None, 'name': u'number',  'documentation': u'I am a number.',             'component': component_testmodelkeyproperties.pk,   'values': u'', 'is_label': False, 'choice': u'keyboard', 'order': 1},
            {'category': category_testmodelkeyproperties_generalattributes.pk, 'field_type': None, 'name': u'choice1', 'documentation': u'I am an inclusive choice.',  'component': component_testmodelkeyproperties.pk,   'values': u'one|two|three|other|N/A', 'is_label': False, 'choice': u'OR', 'order': 2},
            {'category': category_testmodelkeyproperties_generalattributes.pk, 'field_type': None, 'name': u'choice2', 'documentation': u'I am an exclusive choice.',  'component': component_testmodelkeyproperties.pk,   'values': u'yes|no', 'is_label': False, 'choice': u'XOR', 'order': 3},
        ]
        properties_data = [model_to_data(property) for property in property_qs]
        for actual_property_data, test_property_data in zip(properties_data, test_properties_data):
            self.assertDictEqual(actual_property_data, test_property_data, excluded_keys=["id", "last_modified", "created",])

    def test_reregister(self):

        # this registers the "test" vocabulary by default
        super(TestMetadataVocabulary,self).setUp()
        test_vocabulary = self.vocabulary

        old_components = copy.deepcopy(list(MetadataComponentProxy.objects.all()))
        old_categories = copy.deepcopy(list(MetadataScientificCategoryProxy.objects.all()))
        old_properties = copy.deepcopy(list(MetadataScientificPropertyProxy.objects.all()))

        changed_vocabulary_path = os.path.join(VOCABULARY_UPLOAD_PATH, "test_vocabulary_changed_bdl.xml")
        test_vocabulary.file = changed_vocabulary_path
        test_vocabulary.save()

        test_vocabulary.register()
        test_vocabulary.save()

        component_testmodel = MetadataComponentProxy.objects.get(name__iexact="testmodel")
        component_testmodelkeyproperties = MetadataComponentProxy.objects.get(name__iexact="testmodelkeyproperties")
        component_pretendsubmodel = MetadataComponentProxy.objects.get(name__iexact="pretendsubmodel")
        component_submodel = MetadataComponentProxy.objects.get(name__iexact="submodel")
        component_subsubmodel = MetadataComponentProxy.objects.get(name__iexact="subsubmodel")

        category_testmodel_generalattributes = MetadataScientificCategoryProxy.objects.get(component=component_testmodel, name__iexact="general attributes")
        category_testmodelkeyproperties_generalattributes = MetadataScientificCategoryProxy.objects.get(component=component_testmodelkeyproperties, name__iexact="general attributes")
        category_testmodelkeyproperties_categoryone = MetadataScientificCategoryProxy.objects.get(component=component_testmodelkeyproperties, name__iexact="categoryone")
        category_testmodelkeyproperties_categorytwo = MetadataScientificCategoryProxy.objects.get(component=component_testmodelkeyproperties, name__iexact="categorytwo")
        category_pretendsubmodel_generalattributes = MetadataScientificCategoryProxy.objects.get(component=component_pretendsubmodel, name__iexact="general attributes")
        category_pretendsubmodel_categoryone = MetadataScientificCategoryProxy.objects.get(component=component_pretendsubmodel, name__iexact="categoryone")
        category_submodel_generalattributes = MetadataScientificCategoryProxy.objects.get(component=component_submodel, name__iexact="general attributes")
        category_submodel_categoryone = MetadataScientificCategoryProxy.objects.get(component=component_submodel, name__iexact="categoryone")
        category_subsubmodel_generalattributes = MetadataScientificCategoryProxy.objects.get(component=component_subsubmodel, name__iexact="general attributes")
        category_subsubmodel_categoryone = MetadataScientificCategoryProxy.objects.get(component=component_subsubmodel, name__iexact="categoryone")

        # CHANGES:
        # 1. removed testmodelkeyproperties->choice2
        # 2. added testmodelkeyproperties->choice3

        test_properties_data = [
            {'category': category_subsubmodel_categoryone.pk,                  'field_type': None, 'name': u'name',    'documentation': u'I am free text.',            'component': component_subsubmodel.pk,              'values': u'', 'is_label': False, 'choice': u'keyboard', 'order': 0},
            {'category': category_pretendsubmodel_categoryone.pk,              'field_type': None, 'name': u'name',    'documentation': u'I am free text.',            'component': component_pretendsubmodel.pk,          'values': u'', 'is_label': False, 'choice': u'keyboard', 'order': 0},
            {'category': category_submodel_categoryone.pk,                     'field_type': None, 'name': u'name',    'documentation': u'I am free text.',            'component': component_submodel.pk,                 'values': u'', 'is_label': False, 'choice': u'keyboard', 'order': 0},
            {'category': category_testmodelkeyproperties_generalattributes.pk, 'field_type': None, 'name': u'name',    'documentation': u'I am free text.',            'component': component_testmodelkeyproperties.pk,   'values': u'', 'is_label': False, 'choice': u'keyboard', 'order': 0},
            {'category': category_testmodelkeyproperties_categoryone.pk,       'field_type': None, 'name': u'name',    'documentation': u'I am free text.',            'component': component_testmodelkeyproperties.pk,   'values': u'', 'is_label': False, 'choice': u'keyboard', 'order': 0},
            {'category': category_testmodelkeyproperties_categorytwo.pk,       'field_type': None, 'name': u'name',    'documentation': u'I am free text.',            'component': component_testmodelkeyproperties.pk,   'values': u'', 'is_label': False, 'choice': u'keyboard', 'order': 0},
            {'category': category_testmodelkeyproperties_generalattributes.pk, 'field_type': None, 'name': u'number',  'documentation': u'I am a number.',             'component': component_testmodelkeyproperties.pk,   'values': u'', 'is_label': False, 'choice': u'keyboard', 'order': 1},
            {'category': category_testmodelkeyproperties_generalattributes.pk, 'field_type': None, 'name': u'choice1', 'documentation': u'I am an inclusive choice.',  'component': component_testmodelkeyproperties.pk,   'values': u'one|two|three|other|N/A', 'is_label': False, 'choice': u'OR', 'order': 2},
           #{'category': category_testmodelkeyproperties_generalattributes.pk, 'field_type': None, 'name': u'choice2', 'documentation': u'I am an exclusive choice.',  'component': component_testmodelkeyproperties.pk,   'values': u'yes|no'", 'is_label': False, 'choice': u'XOR', 'order': 3},
            {'category': category_testmodelkeyproperties_generalattributes.pk, 'field_type': None, 'name': u'choice3', 'documentation': u'I am an inclusive choice.',  'component': component_testmodelkeyproperties.pk,   'values': u'four|five|six|other|N/A', 'is_label': False, 'choice': u'OR', 'order': 3},
        ]
        property_qs = MetadataScientificPropertyProxy.objects.all()
        properties_data = [model_to_data(property) for property in property_qs]
        for actual_property_data, test_property_data in zip(properties_data, test_properties_data):
            self.assertDictEqual(actual_property_data, test_property_data, excluded_keys=["id", "last_modified", "created",])

    def test_reregister_with_existing_customizations(self):

        # this registers the "test" vocabulary by default
        super(TestMetadataVocabulary,self).setUp()

        old_component_proxies = copy.deepcopy(list(MetadataComponentProxy.objects.all()))
        old_scientific_category_proxies = copy.deepcopy(list(MetadataScientificCategoryProxy.objects.all()))
        old_scientific_property_proxies = copy.deepcopy(list(MetadataScientificPropertyProxy.objects.all()))

        test_document_type = "modelcomponent"
        test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)
        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
        self.assertEqual(len(test_vocabularies), 1)
        test_vocabulary = test_vocabularies[0]
        test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy)
        (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
        scientific_category_customizers = get_joined_keys_dict(nested_scientific_category_customizers)
        scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)

        old_model_customizer = copy.deepcopy(model_customizer)
        old_standard_category_customizers = copy.deepcopy(list(standard_category_customizers))
        old_standard_property_customizers = copy.deepcopy(list(standard_property_customizers))
        old_scientific_category_customizers = copy.deepcopy({ key : list(qs) for key, qs in scientific_category_customizers.items() })
        old_scientific_property_customizers = copy.deepcopy({ key : list(qs) for key, qs in scientific_property_customizers.items() })

        # CHANGES:
        # 1. removed testmodelkeyproperties->choice2
        # 2. added testmodelkeyproperties->choice3

        old_component_proxy = find_in_sequence(lambda cp: cp.name.lower() == "testmodelkeyproperties", old_component_proxies)
        old_scientific_category_proxy = find_in_sequence(lambda scp: scp.component==old_component_proxy and scp.name.lower() == "general attributes", old_scientific_category_proxies)
        old_scientific_property_proxy = find_in_sequence(lambda scp: scp.component==old_component_proxy and scp.category==old_scientific_category_proxy and scp.name.lower() == "choice2", old_scientific_property_proxies)

        self.assertEqual(len(old_model_customizer.scientific_property_customizers.filter(proxy=old_scientific_property_proxy)), 1)

        changed_vocabulary_path = os.path.join(VOCABULARY_UPLOAD_PATH, "test_vocabulary_changed_bdl.xml")
        test_vocabulary.file = changed_vocabulary_path
        test_vocabulary.save()
        test_vocabulary.register()
        test_vocabulary.save()

        new_component_proxies = list(MetadataComponentProxy.objects.all())
        new_scientific_category_proxies = list(MetadataScientificCategoryProxy.objects.all())
        new_scientific_property_proxies = list(MetadataScientificPropertyProxy.objects.all())

        (new_model_customizer, new_standard_category_customizers, new_standard_property_customizers, new_nested_scientific_category_customizers, new_nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
        new_scientific_category_customizers = get_joined_keys_dict(new_nested_scientific_category_customizers)
        new_scientific_property_customizers = get_joined_keys_dict(new_nested_scientific_property_customizers)

        new_component_proxy = find_in_sequence(lambda cp: cp.name.lower() == "testmodelkeyproperties", new_component_proxies)
        new_scientific_category_proxy = find_in_sequence(lambda scp: scp.component==new_component_proxy and scp.name.lower() == "general attributes", new_scientific_category_proxies)
        new_scientific_property_proxy = find_in_sequence(lambda scp: scp.component==new_component_proxy and scp.category==new_scientific_category_proxy and scp.name.lower() == "choice3", new_scientific_property_proxies)

        self.assertEqual(len(new_model_customizer.scientific_property_customizers.filter(proxy=old_scientific_property_proxy)), 0)
        self.assertEqual(len(new_model_customizer.scientific_property_customizers.filter(proxy=new_scientific_property_proxy)), 1)
