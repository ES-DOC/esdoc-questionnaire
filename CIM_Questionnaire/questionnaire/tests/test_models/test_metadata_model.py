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
from django.template.defaultfilters import slugify

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase

from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy
from CIM_Questionnaire.questionnaire.models.metadata_version import MetadataVersion
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary

from CIM_Questionnaire.questionnaire.models.metadata_version import UPLOAD_PATH as VERSION_UPLOAD_PATH

from CIM_Questionnaire.questionnaire.utils import add_parameters_to_url
from CIM_Questionnaire.questionnaire.utils import DEFAULT_VOCABULARY

# TODO: CHECK THAT ORDERING OF PROXIES/CUSTOMIZERS IS STILL NECESSARY

class TestMetadataModel(TestQuestionnaireBase):

    def setUp(self):
        super(TestMetadataModel,self).setUp()

        # have _real_ version 1.8.1 of the CIM handy for these tests

        cim_version_path = os.path.join(VERSION_UPLOAD_PATH, "cim_1_8_1.xml")

        cim_version = MetadataVersion(name="cim", file=cim_version_path)
        cim_version.save()
        version_qs = MetadataVersion.objects.all()
        self.assertEqual(len(version_qs), 2)
        self.cim_version = cim_version


    def get_proxy_set(self,model_proxy,vocabularies=MetadataVocabulary.objects.none()):

        standard_property_proxies = model_proxy.standard_properties.all()

        scientific_property_proxies = {}
        for vocabulary in vocabularies:
            vocabulary_key = slugify(vocabulary.name)
            for component_proxy in vocabulary.component_proxies.all():
                component_key = slugify(component_proxy.name)
                model_key = u"%s_%s" % (vocabulary_key, component_key)
                scientific_property_proxies[model_key] = component_proxy.scientific_properties.all()

        return (model_proxy, standard_property_proxies, scientific_property_proxies)

    def test_get_new_realization_set(self):

        test_proxy = MetadataModelProxy.objects.get(version=self.version,name__iexact="modelcomponent")
        test_customizer = self.create_customizer_set_with_subforms(test_proxy.name, properties_with_subforms=["author"])
        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_customizer.proxy.name.lower())

        (model_proxy, standard_property_proxies, scientific_property_proxies) = self.get_proxy_set(test_proxy, vocabularies=test_vocabularies)

        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)

        root_model_key = u"%s_%s" % (slugify(DEFAULT_VOCABULARY), slugify(test_customizer.model_root_component))

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
            {'is_root': True,  'version': self.version, 'created': None, 'component_key': u'rootcomponent',          'description': u'A ModelCompnent is nice.', 'title': u'RootComponent',                       'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': u'default_vocabulary', 'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            {'is_root': False, 'version': self.version, 'created': None, 'component_key': u'testmodel',              'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : testmodel',              'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': u'vocabulary',         'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            {'is_root': False, 'version': self.version, 'created': None, 'component_key': u'testmodelkeyproperties', 'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : testmodelkeyproperties', 'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': u'vocabulary',         'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            {'is_root': False, 'version': self.version, 'created': None, 'component_key': u'pretendsubmodel',        'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : pretendsubmodel',        'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': u'vocabulary',         'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            {'is_root': False, 'version': self.version, 'created': None, 'component_key': u'submodel',               'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : submodel',               'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': u'vocabulary',         'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            {'is_root': False, 'version': self.version, 'created': None, 'component_key': u'subsubmodel',            'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : subsubmodel',            'order': 0, 'project': self.project, 'last_modified': None, 'proxy': test_proxy, 'vocabulary_key': u'vocabulary',         'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
        ]


        test_scientific_properties_data = {
            root_model_key : [],
            u'vocabulary_testmodelkeyproperties': [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',   'category_key': u'general-attributes',  'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',   'category_key': u'categoryone',         'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',   'category_key': u'categorytwo',         'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'number', 'category_key': u'general-attributes',  'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 1, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'choice1', 'category_key': u'general-attributes', 'is_enumeration': True, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 2, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'choice2', 'category_key': u'general-attributes', 'is_enumeration': True, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 3, 'atomic_value': None}
            ],
            u'vocabulary_pretendsubmodel': [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name', 'category_key': u'categoryone', 'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
            u'vocabulary_testmodel': [],
            u'vocabulary_submodel': [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name', 'category_key': u'categoryone', 'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
            u'vocabulary_subsubmodel': [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name', 'category_key': u'categoryone', 'is_enumeration': False, 'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
            u'default_vocabulary_rootcomponent': [],
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

        test_proxy = MetadataModelProxy.objects.get(version=self.version,name__iexact="modelcomponent")
        test_customizer = self.create_customizer_set_with_subforms(test_proxy.name, properties_with_subforms=["author"])
        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_customizer.proxy.name.lower())

        models = self.model_realization.get_descendants(include_self=True)

        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_existing_realization_set(models, test_customizer, test_vocabularies)

        # I AM HERE


