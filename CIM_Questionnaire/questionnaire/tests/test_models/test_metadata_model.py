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

import os

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase

from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy, MetadataComponentProxy
from CIM_Questionnaire.questionnaire.models.metadata_version import MetadataVersion
from CIM_Questionnaire.questionnaire.models.metadata_categorization import MetadataCategorization
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary
from CIM_Questionnaire.questionnaire.models.metadata_project import MetadataProject

from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import UPLOAD_PATH as VOCABULARY_UPLOAD_PATH
from CIM_Questionnaire.questionnaire.models.metadata_version import UPLOAD_PATH as VERSION_UPLOAD_PATH
from CIM_Questionnaire.questionnaire.models.metadata_categorization import UPLOAD_PATH as CATEGORIZATION_UPLOAD_PATH

from CIM_Questionnaire.questionnaire.utils import DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY

class TestMetadataModel(TestQuestionnaireBase):

    def setUp(self):

        super(TestMetadataModel,self).setUp()

        cim_document_type = "modelcomponent"

        # have _real_ version 1.8.1 of the CIM handy for these tests
        cim_project = MetadataProject(name="test_cim", title="CIM Project", active=True, authenticated=False)
        cim_project.save()
        project_qs = MetadataProject.objects.all()
        self.assertEqual(len(project_qs), 2)

        cim_vocabulary_path = os.path.join(VOCABULARY_UPLOAD_PATH, "test_atmosphere_bdl.xml")
        cim_vocabulary = MetadataVocabulary(name="cim", file=cim_vocabulary_path, document_type=cim_document_type)
        cim_vocabulary.save()
        vocabulary_qs = MetadataVocabulary.objects.all()
        self.assertEqual(len(vocabulary_qs), 2)

        cim_version_path = os.path.join(VERSION_UPLOAD_PATH, "test_cim_1_8_1.xml")
        cim_version = MetadataVersion(name="cim", file=cim_version_path)
        cim_version.save()
        version_qs = MetadataVersion.objects.all()
        self.assertEqual(len(version_qs), 2)

        cim_categorization_path = os.path.join(CATEGORIZATION_UPLOAD_PATH, "test_esdoc_categorization.xml")
        cim_categorization = MetadataCategorization(name="cim", file=cim_categorization_path)
        cim_categorization.save()
        categorization_qs = MetadataCategorization.objects.all()
        self.assertEqual(len(categorization_qs), 2)

        cim_version.categorization = cim_categorization
        cim_version.save()
        cim_project.vocabularies.add(cim_vocabulary)
        cim_project.save()
        cim_version.register()
        cim_version.save()
        cim_categorization.register()
        cim_categorization.save()
        cim_vocabulary.register()
        cim_vocabulary.save()

        self.cim_proxy = MetadataModelProxy.objects.get(version=cim_version,name__iexact=cim_document_type)
        self.cim_document_type = cim_document_type
        self.cim_version = cim_version
        self.cim_project = cim_project
        self.cim_vocabulary = cim_vocabulary


    def test_get_new_realization_set_from_cim(self):

        test_vocabularies = self.cim_project.vocabularies.filter(document_type__iexact=self.cim_document_type)
        self.assertEqual(len(test_vocabularies), 1)
        test_vocabulary = test_vocabularies[0]

        test_customizer = self.create_customizer_set_with_subforms(self.cim_project, self.cim_version, self.cim_proxy, properties_with_subforms=["documentAuthor"])

        (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(self.cim_proxy, vocabularies=test_vocabularies)

        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)


        # cannot do as much in-depth testing w/ actual CIM data as below
        # but can still check basic stuff like number & names of models & properties

        self.assertEqual(len(models), 13)

        self.assertEqual(len(scientific_properties), 13)
        for standard_property_list in standard_properties.values():
            self.assertEqual(len(standard_property_list), 23)

        cim_component_names = [
            u"%s_%s" % (DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY),
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='atmosphere').get_key()),
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='atmoskeyproperties').get_key()),
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='atmoscloudscheme').get_key()),
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='atmosradiation').get_key()),
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='atmosadvection').get_key()),
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='atmosconvectturbulcloud').get_key()),
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='topofatmosinsolation').get_key()),
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='atmosdynamicalcore').get_key()),
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='atmosorographyandwaves').get_key()),
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='atmosspaceconfiguration').get_key()),
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='atmoshorizontaldomain').get_key()),
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='cloudsimulator').get_key()),
        ]
        self.assertSetEqual(set(cim_component_names), set(scientific_properties.keys()))
        self.assertEqual(len(scientific_properties[cim_component_names[0]]), 0)
        self.assertEqual(len(scientific_properties[cim_component_names[1]]), 0)
        self.assertEqual(len(scientific_properties[cim_component_names[2]]), 3)
        self.assertEqual(len(scientific_properties[cim_component_names[3]]), 7)
        self.assertEqual(len(scientific_properties[cim_component_names[4]]), 10)
        self.assertEqual(len(scientific_properties[cim_component_names[5]]), 8)
        self.assertEqual(len(scientific_properties[cim_component_names[6]]), 13)
        self.assertEqual(len(scientific_properties[cim_component_names[7]]), 4)
        self.assertEqual(len(scientific_properties[cim_component_names[8]]), 10)
        self.assertEqual(len(scientific_properties[cim_component_names[9]]), 13)
        self.assertEqual(len(scientific_properties[cim_component_names[10]]), 6)
        self.assertEqual(len(scientific_properties[cim_component_names[11]]), 10)
        self.assertEqual(len(scientific_properties[cim_component_names[12]]), 12)


    def test_get_new_realization_set(self):

        test_document_type = "modelcomponent"

        test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)

        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
        self.assertEqual(len(test_vocabularies), 1)
        test_vocabulary = test_vocabularies[0]

        test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])

        (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)

        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)

        root_model_key = u"%s_%s" % (DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY)

        n_components = 1
        for vocabulary in test_vocabularies:
            n_components += len(vocabulary.component_proxies.all())
        self.assertEqual(len(models), n_components)
        self.assertEqual(n_components, 6)

        n_scientific_properties = sum([len(sp_list) for sp_list in scientific_properties.values()])
        self.assertEqual(n_scientific_properties, 9)

        excluded_fields = ["tree_id", "lft", "rght", "level", "parent",] # ignore mptt fields
        serialized_models = [self.fully_serialize_model(model,exclude=excluded_fields) for model in models]
        test_models_data = [
            {'is_root': True,  'version': self.version, 'created': None, 'component_key': DEFAULT_COMPONENT_KEY,                                                                                           'description': u'A ModelCompnent is nice.', 'title': u'RootComponent',                       'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': DEFAULT_VOCABULARY_KEY,    'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            {'is_root': False, 'version': self.version, 'created': None, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='testmodel').get_key(),              'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : testmodel',              'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            {'is_root': False, 'version': self.version, 'created': None, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='testmodelkeyproperties').get_key(), 'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : testmodelkeyproperties', 'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            {'is_root': False, 'version': self.version, 'created': None, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='pretendsubmodel').get_key(),        'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : pretendsubmodel',        'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            {'is_root': False, 'version': self.version, 'created': None, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='submodel').get_key(),               'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : submodel',               'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            {'is_root': False, 'version': self.version, 'created': None, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='subsubmodel').get_key(),            'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : subsubmodel',            'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
        ]

        test_scientific_properties_data = {
            u"%s_%s" % (DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY) : [],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="testmodelkeyproperties").get_key()) : [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',   'category_key': u'general-attributes',  'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'number', 'category_key': u'general-attributes',  'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 1, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'choice1', 'category_key': u'general-attributes', 'is_enumeration': True, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 2, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'choice2', 'category_key': u'general-attributes', 'is_enumeration': True, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 3, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',   'category_key': u'categoryone',         'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',   'category_key': u'categorytwo',         'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None},
            ],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="pretendsubmodel").get_key()) : [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name', 'category_key': u'categoryone', 'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="testmodel").get_key()) : [],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="submodel").get_key()) : [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name', 'category_key': u'categoryone', 'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="subsubmodel").get_key()) : [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name', 'category_key': u'categoryone', 'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
        }

        for actual_model_data,test_model_data in zip(serialized_models,test_models_data):
            self.assertDictEqual(actual_model_data,test_model_data)

        test_scientific_property_data = {}
        for model in models:
            model_key = model.get_model_key()
            for standard_property, standard_property_proxy in zip(standard_properties[model_key], standard_property_proxies):
                self.assertEqual(standard_property.model, model)
                self.assertEqual(standard_property.proxy, standard_property_proxy)
                self.assertEqual(standard_property.name, standard_property_proxy.name)
                self.assertEqual(standard_property.order, standard_property_proxy.order)
                self.assertEqual(standard_property.is_label, standard_property_proxy.is_label)
                self.assertEqual(standard_property.field_type, standard_property_proxy.field_type)
                self.assertIsNone(standard_property.atomic_value)
                self.assertIsNone(standard_property.enumeration_value)
                self.assertEqual(standard_property.enumeration_other_value, "Please enter a custom value")
                # no need to test relationship_value, since m2m fields cannot be set before save()

            excluded_fields = ["model", "proxy"]
            serialized_scientific_properties = [self.fully_serialize_model(sp, exclude=excluded_fields) for sp in scientific_properties[model_key]]
            for actual_scientific_property_data, test_scientific_property_data in zip(serialized_scientific_properties, test_scientific_properties_data[model_key]):
                self.assertDictEqual(actual_scientific_property_data, test_scientific_property_data)

            try:
                for scientific_property, scientific_property_proxy in zip(scientific_properties[model_key], scientific_property_proxies[model_key]):
                    self.assertEqual(scientific_property.model, model)
                    self.assertEqual(scientific_property.name, scientific_property_proxy.name)
            except KeyError:
                # the root model shouldn't have any scientific_properties
                self.assertEqual(model_key,root_model_key)


    def test_get_existing_realization_set(self):

        test_document_type = "modelcomponent"

        test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)

        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)
        self.assertEqual(len(test_vocabularies), 1)
        test_vocabulary = test_vocabularies[0]

        test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])

        models = self.model_realization.get_descendants(include_self=True)

        # TODO: RETURN THESE IN THE SAME ORDER AS get_new_realization_set !!!!!!!!!

        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_existing_realization_set(models, test_customizer, vocabularies=test_vocabularies)

        root_model_key = u"%s_%s" % (DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY)

        n_components = 1
        for vocabulary in test_vocabularies:
            n_components += len(vocabulary.component_proxies.all())
        self.assertEqual(len(models), n_components)
        self.assertEqual(n_components, 6)

        n_scientific_properties = sum([len(sp_list) for sp_list in scientific_properties.values()])
        self.assertEqual(n_scientific_properties, 9)

        excluded_fields = [ "tree_id", "lft", "rght", "level", "parent", "last_modified", "created", "id", ] # ignore mptt fields & datetime-specific fields & pk field
        serialized_models = [ self.fully_serialize_model(model, exclude=excluded_fields) for model in models ]
        test_models_data = [
            {'is_root': True,  'version': self.version, 'component_key': DEFAULT_COMPONENT_KEY,                                                                                           'description': u'A ModelCompnent is nice.', 'title': u'RootComponent',                       'order': 0, 'project': self.project,   'proxy': test_proxy, 'vocabulary_key': DEFAULT_VOCABULARY_KEY,    'is_document': True, 'active': True, 'name': u'modelComponent' },
            {'is_root': False, 'version': self.version, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='testmodel').get_key(),              'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : testmodel',              'order': 0, 'project': self.project,   'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, 'name': u'modelComponent' },
            {'is_root': False, 'version': self.version, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='testmodelkeyproperties').get_key(), 'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : testmodelkeyproperties', 'order': 0, 'project': self.project,   'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, 'name': u'modelComponent' },
            {'is_root': False, 'version': self.version, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='pretendsubmodel').get_key(),        'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : pretendsubmodel',        'order': 0, 'project': self.project,   'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, 'name': u'modelComponent' },
            {'is_root': False, 'version': self.version, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='submodel').get_key(),               'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : submodel',               'order': 0, 'project': self.project,   'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, 'name': u'modelComponent' },
            {'is_root': False, 'version': self.version, 'component_key': MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact='subsubmodel').get_key(),            'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : subsubmodel',            'order': 0, 'project': self.project,   'proxy': test_proxy, 'vocabulary_key': test_vocabulary.get_key(), 'is_document': True, 'active': True, 'name': u'modelComponent' },
        ]

        test_scientific_properties_data = {
            root_model_key : [],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="testmodelkeyproperties").get_key()) : [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',    'category_key': u'general-attributes',  'is_enumeration': False, 'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'number',  'category_key': u'general-attributes',  'is_enumeration': False, 'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 1, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'choice1', 'category_key': u'general-attributes',  'is_enumeration': True,  'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 2, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'choice2', 'category_key': u'general-attributes',  'is_enumeration': True,  'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 3, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',    'category_key': u'categoryone',         'is_enumeration': False, 'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',    'category_key': u'categorytwo',         'is_enumeration': False, 'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None},
            ],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="pretendsubmodel").get_key()) : [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name', 'category_key': u'categoryone', 'is_enumeration': False, 'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="testmodel").get_key()) : [],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="submodel").get_key()) : [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name', 'category_key': u'categoryone', 'is_enumeration': False, 'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
            u"%s_%s" % (test_vocabulary.get_key(), MetadataComponentProxy.objects.get(vocabulary=test_vocabulary, name__iexact="subsubmodel").get_key()) : [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name', 'category_key': u'categoryone', 'is_enumeration': False, 'extra_standard_name': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
        }

        for actual_model_data,test_model_data in zip(serialized_models,test_models_data):
            self.assertDictEqual(actual_model_data,test_model_data)

        test_scientific_property_data = {}
        for model in models:
            model_key = model.get_model_key()
            for standard_property, standard_property_proxy in zip(standard_properties[model_key], test_proxy.standard_properties.all()):
                self.assertEqual(standard_property.model, model)
                self.assertEqual(standard_property.proxy, standard_property_proxy)
                self.assertEqual(standard_property.name, standard_property_proxy.name)
                self.assertEqual(standard_property.order, standard_property_proxy.order)
                self.assertEqual(standard_property.is_label, standard_property_proxy.is_label)
                self.assertEqual(standard_property.field_type, standard_property_proxy.field_type)
                self.assertIsNone(standard_property.atomic_value)
                self.assertIsNone(standard_property.enumeration_value)
                self.assertEqual(standard_property.enumeration_other_value, "Please enter a custom value")
                # no need to test relationship_value, since m2m fields cannot be set before save()

            excluded_fields = ["model", "proxy", "id", ]
            serialized_scientific_properties = [self.fully_serialize_model(sp, exclude=excluded_fields) for sp in scientific_properties[model_key]]
            for actual_scientific_property_data, test_scientific_property_data in zip(serialized_scientific_properties, test_scientific_properties_data[model_key]):
                self.assertDictEqual(actual_scientific_property_data, test_scientific_property_data)


            # try:
            #     for scientific_property, scientific_property_proxy in zip(scientific_properties[model_key], scientific_property_proxies[model_key]):
            #         self.assertEqual(scientific_property.model, model)
            #         self.assertEqual(scientific_property.name, scientific_property_proxy.name)
            # except KeyError:
            #     # the root model shouldn't have any scientific_properties
            #     self.assertEqual(model_key,root_model_key)


