from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase, QueryCounter

from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary
from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy, MetadataStandardPropertyProxy, MetadataScientificPropertyProxy
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer

from CIM_Questionnaire.questionnaire.forms.forms_edit import create_model_form_data, create_standard_property_form_data, create_scientific_property_form_data
from CIM_Questionnaire.questionnaire.forms.forms_edit import create_new_edit_forms_from_models, create_new_edit_subforms_from_models
from CIM_Questionnaire.questionnaire.forms.forms_edit import get_data_from_edit_forms
from CIM_Questionnaire.questionnaire.forms.forms_edit import MetadataModelFormSetFactory, MetadataStandardPropertyInlineFormSetFactory

from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes

from CIM_Questionnaire.questionnaire.utils import get_data_from_formset, get_data_from_form, get_joined_keys_dict

class Test(TestQuestionnaireBase):

    def test_create_model_form_data(self):

        test_document_type = "modelcomponent"

        test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)

        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)

        test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy)
        (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)

        (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)

        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)

        models_data = [create_model_form_data(model, model_customizer) for model in models]

        test_models_data = [
            {'is_root': True,  'version': self.version.pk, 'created': None, 'component_key': u'rootcomponent',           'description': u'A ModelCompnent is nice.', 'title': u'RootComponent',                        'order': 0, 'project': self.project.pk, 'proxy': test_proxy.pk, 'vocabulary_key': u'default_vocabulary',  'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            {'is_root': False, 'version': self.version.pk, 'created': None, 'component_key': u'testmodel',               'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : testmodel',               'order': 0, 'project': self.project.pk, 'proxy': test_proxy.pk, 'vocabulary_key': u'vocabulary',          'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            {'is_root': False, 'version': self.version.pk, 'created': None, 'component_key': u'testmodelkeyproperties',  'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : testmodelkeyproperties',  'order': 0, 'project': self.project.pk, 'proxy': test_proxy.pk, 'vocabulary_key': u'vocabulary',          'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            {'is_root': False, 'version': self.version.pk, 'created': None, 'component_key': u'pretendsubmodel',         'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : pretendsubmodel',         'order': 0, 'project': self.project.pk, 'proxy': test_proxy.pk, 'vocabulary_key': u'vocabulary',          'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            {'is_root': False, 'version': self.version.pk, 'created': None, 'component_key': u'submodel',                'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : submodel',                'order': 0, 'project': self.project.pk, 'proxy': test_proxy.pk, 'vocabulary_key': u'vocabulary',          'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
            {'is_root': False, 'version': self.version.pk, 'created': None, 'component_key': u'subsubmodel',             'description': u'A ModelCompnent is nice.', 'title': u'vocabulary : subsubmodel',             'order': 0, 'project': self.project.pk, 'proxy': test_proxy.pk, 'vocabulary_key': u'vocabulary',          'is_document': True, 'active': True, u'id': None, 'name': u'modelComponent'},
        ]

        for actual_model_data, test_model_data in zip(models_data, test_models_data):
            self.assertDictEqual(actual_model_data, test_model_data, excluded_keys=["last_modified", "created"]) # date models were created will be different each time this is run, so don't bother checking that field


    def test_create_standard_property_form_data(self):

        test_document_type = "modelcomponent"

        test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)

        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)

        test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy)
        (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)

        (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)

        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)

        test_standard_property_form_data = [
            {'field_type': u'ATOMIC',       'enumeration_other_value': 'Please enter a custom value', 'name': u'string',        'enumeration_value': None,  u'id': None, 'proxy': MetadataStandardPropertyProxy.objects.get(model_proxy=model_proxy, name="string").pk,        'is_label': True,  'order': 0, 'atomic_value': u'',  'relationship_value' : [],  },
            {'field_type': u'ATOMIC',       'enumeration_other_value': 'Please enter a custom value', 'name': u'date',          'enumeration_value': None,  u'id': None, 'proxy': MetadataStandardPropertyProxy.objects.get(model_proxy=model_proxy, name="date").pk,          'is_label': False, 'order': 2, 'atomic_value': u'',  'relationship_value' : [],  },
            {'field_type': u'RELATIONSHIP', 'enumeration_other_value': 'Please enter a custom value', 'name': u'author',        'enumeration_value': None,  u'id': None, 'proxy': MetadataStandardPropertyProxy.objects.get(model_proxy=model_proxy, name="author").pk,        'is_label': False, 'order': 5, 'atomic_value': None, 'relationship_value' : u'', },
            {'field_type': u'ATOMIC',       'enumeration_other_value': 'Please enter a custom value', 'name': u'boolean',       'enumeration_value': None,  u'id': None, 'proxy': MetadataStandardPropertyProxy.objects.get(model_proxy=model_proxy, name="boolean").pk,       'is_label': False, 'order': 1, 'atomic_value': u'',  'relationship_value' : [],  },
            {'field_type': u'ENUMERATION',  'enumeration_other_value': 'Please enter a custom value', 'name': u'enumeration',   'enumeration_value': u'',   u'id': None, 'proxy': MetadataStandardPropertyProxy.objects.get(model_proxy=model_proxy, name="enumeration").pk,   'is_label': False, 'order': 4, 'atomic_value': None, 'relationship_value' : [],  },
            {'field_type': u'RELATIONSHIP', 'enumeration_other_value': 'Please enter a custom value', 'name': u'contact',       'enumeration_value': None,  u'id': None, 'proxy': MetadataStandardPropertyProxy.objects.get(model_proxy=model_proxy, name="contact").pk,       'is_label': False, 'order': 6, 'atomic_value': None, 'relationship_value':  u'', },
        ]

        for model in models:
            model_key = model.get_model_key()

            # test that the customizer / realizations / proxies are all in the same order
            for standard_property, standard_property_customizer in zip(standard_properties[model_key], standard_property_customizers):
                self.assertEqual(standard_property.proxy, standard_property_customizer.proxy)

            standard_properties_data = [
                 create_standard_property_form_data(model, standard_property, standard_property_customizer)
                 for standard_property, standard_property_customizer in
                 zip(standard_properties[model_key], standard_property_customizers)
                 if standard_property_customizer.displayed
            ]

            for actual_standard_property_form_data, test_standard_property_data in zip(standard_properties_data, test_standard_property_form_data):
                self.assertDictEqual(actual_standard_property_form_data, test_standard_property_data, excluded_keys=["last_modified","model"])


    def test_create_scientific_property_form_data(self):

        test_document_type = "modelcomponent"

        test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)

        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)

        test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy)
        (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)

        # un-nest the scientific properties...
        scientific_property_customizers = {}
        for vocabulary_key,scientific_property_customizer_dict in nested_scientific_property_customizers.iteritems():
            for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
                model_key = u"%s_%s" % (vocabulary_key, component_key)
                scientific_property_customizers[model_key] = scientific_property_customizer_list


        (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)

        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)

        test_scientific_property_form_data = {
            u'vocabulary_testmodelkeyproperties': [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',    'category_key': u'general-attributes',  'is_enumeration': False,    'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'proxy': MetadataScientificPropertyProxy.objects.get(component__name="testmodelkeyproperties",category__key="general-attributes",name="name").pk,     'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'number',  'category_key': u'general-attributes',  'is_enumeration': False,    'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'proxy': MetadataScientificPropertyProxy.objects.get(component__name="testmodelkeyproperties",category__key="general-attributes",name="number").pk,   'is_label': False, 'extra_units': None, 'order': 1, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'choice1', 'category_key': u'general-attributes',  'is_enumeration': True,     'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'proxy': MetadataScientificPropertyProxy.objects.get(component__name="testmodelkeyproperties",category__key="general-attributes",name="choice1").pk,  'is_label': False, 'extra_units': None, 'order': 2, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'choice2', 'category_key': u'general-attributes',  'is_enumeration': True,     'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'proxy': MetadataScientificPropertyProxy.objects.get(component__name="testmodelkeyproperties",category__key="general-attributes",name="choice2").pk,  'is_label': False, 'extra_units': None, 'order': 3, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',    'category_key': u'categoryone',         'is_enumeration': False,    'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'proxy': MetadataScientificPropertyProxy.objects.get(component__name="testmodelkeyproperties",category__key="categoryone",name="name").pk,            'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None},
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',    'category_key': u'categorytwo',         'is_enumeration': False,    'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'proxy': MetadataScientificPropertyProxy.objects.get(component__name="testmodelkeyproperties",category__key="categorytwo",name="name").pk,            'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
            u'vocabulary_pretendsubmodel': [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',    'category_key': u'categoryone',         'is_enumeration': False,    'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'proxy': MetadataScientificPropertyProxy.objects.get(component__name="pretendsubmodel",category__key="categoryone",name="name").pk, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
            u'vocabulary_testmodel': [
            ],
            u'vocabulary_submodel': [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',    'category_key': u'categoryone',         'is_enumeration': False,    'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'proxy': MetadataScientificPropertyProxy.objects.get(component__name="submodel",category__key="categoryone",name="name").pk, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
            u'vocabulary_subsubmodel': [
                {'field_type': 'PROPERTY', 'enumeration_other_value': 'Please enter a custom value', 'extra_description': None, 'name': u'name',    'category_key': u'categoryone',         'is_enumeration': False,    'extra_standard_name': None, u'id': None, 'enumeration_value': None, 'proxy': MetadataScientificPropertyProxy.objects.get(component__name="subsubmodel",category__key="categoryone",name="name").pk, 'is_label': False, 'extra_units': None, 'order': 0, 'atomic_value': None}
            ],
            u'default_vocabulary_rootcomponent': [
            ]
        }

        for model in models:
            model_key = model.get_model_key()

            # THIS LOGIC IS REPEATED IN THE ACTUAL FN...
            # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
            if model_key not in scientific_property_customizers:
                scientific_property_customizers[model_key] = []

            # test that the customizer / realizations / proxies are all in the same order
            for scientific_property, scientific_property_customizer in zip(scientific_properties[model_key], scientific_property_customizers[model_key]):
                self.assertEqual(scientific_property.proxy, scientific_property_customizer.proxy)
                self.assertEqual(scientific_property.category_key, scientific_property_customizer.category.key)

            scientific_properties_data = [
                create_scientific_property_form_data(model, scientific_property, scientific_property_customizer)
                for scientific_property, scientific_property_customizer in
                zip(scientific_properties[model_key], scientific_property_customizers[model_key])
                if scientific_property_customizer.displayed
            ]
            for actual_scientific_property_form_data, test_scientific_property_data in zip(scientific_properties_data, test_scientific_property_form_data[model_key]):
                self.assertDictEqual(actual_scientific_property_form_data, test_scientific_property_data, excluded_keys=["last_modified","model"])


    def test_metadata_model_formset_factory(self):

        test_document_type = "modelcomponent"

        test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)

        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)

        test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy)
        (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)

        (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)

        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)

        models_data = [create_model_form_data(model, model_customizer) for model in models]

        model_keys = [model.get_model_key() for model in models]

        model_formset = MetadataModelFormSetFactory(
            initial = models_data,
            extra = len(models_data),
            prefixes = model_keys,
            customizer = model_customizer,
        )

        self.assertEqual(len(model_formset), 6)
        self.assertEqual(model_formset.number_of_models, 6)
        self.assertEqual(model_formset.prefix, "form")
        for model_key, model_form in zip(model_keys, model_formset):
            self.assertEqual(model_key, model_form.prefix)
            self.assertEqual(model_form.customizer, model_customizer)


    def test_metadata_standard_property_inline_formset_factory(self):

        test_document_type = "modelcomponent"

        test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)

        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)

        test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy)
        (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)

        (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)

        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)

        model_keys = [model.get_model_key() for model in models]

        standard_properties_formsets = {}
        for model_key, model in zip(model_keys, models):

            standard_properties_data = [
                create_standard_property_form_data(model, standard_property, standard_property_customizer)
                for standard_property, standard_property_customizer in
                zip(standard_properties[model_key], standard_property_customizers)
                if standard_property_customizer.displayed
            ]
            standard_properties_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
                instance = model,
                prefix = model_key,
                initial = standard_properties_data,
                extra = len(standard_properties_data),
                customizers = standard_property_customizers,
            )

        self.assertSetEqual(set(model_keys), set(standard_properties_formsets.keys()))

        for model_key, model in zip(model_keys, models):
            standard_properties_formset = standard_properties_formsets[model_key]

            standard_properties_formset_prefix = standard_properties_formset.prefix
            self.assertEqual(standard_properties_formset_prefix, u"%s_standard_properties"%(model_key))

            self.assertEqual(len(standard_properties_formset), 6)
            self.assertEqual(standard_properties_formset.number_of_properties, 6)
            for i, (standard_property_form, standard_property) in enumerate(zip(standard_properties_formset, standard_properties[model_key])):

                self.assertEqual(standard_property_form.prefix, u"%s-%s" % (standard_properties_formset_prefix, i))
                self.assertEqual(standard_property_form.customizer.proxy, standard_property.proxy)

                if standard_property.field_type == MetadataFieldTypes.RELATIONSHIP:
                    self.assertQuerysetEqual(standard_property_form.fields["relationship_value"].queryset, MetadataModel.objects.filter(proxy=standard_property.proxy.relationship_target_model))


    def test_metadata_standard_property_inline_formset_factory_with_subforms(self):

        test_document_type = "modelcomponent"

        test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)

        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)

        test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])
        (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)


        (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)

        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)

        model_keys = [model.get_model_key() for model in models]

        standard_properties_formsets = {}
        for model_key, model in zip(model_keys, models):

            standard_properties_data = [
                create_standard_property_form_data(model, standard_property, standard_property_customizer)
                for standard_property, standard_property_customizer in
                zip(standard_properties[model_key], standard_property_customizers)
                if standard_property_customizer.displayed
            ]
            standard_properties_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
                instance = model,
                prefix = model_key,
                initial = standard_properties_data,
                extra = len(standard_properties_data),
                customizers = standard_property_customizers,
            )

        self.assertSetEqual(set(model_keys), set(standard_properties_formsets.keys()))

        for model_key, model in zip(model_keys, models):
            standard_properties_formset = standard_properties_formsets[model_key]

            standard_properties_formset_prefix = standard_properties_formset.prefix
            self.assertEqual(standard_properties_formset_prefix, u"%s_standard_properties"%(model_key))

            self.assertEqual(len(standard_properties_formset), 6)
            self.assertEqual(standard_properties_formset.number_of_properties, 6)
            for i, (standard_property_form, standard_property) in enumerate(zip(standard_properties_formset, standard_properties[model_key])):

                self.assertEqual(standard_property_form.prefix, u"%s-%s" % (standard_properties_formset_prefix, i))
                self.assertEqual(standard_property_form.customizer.proxy, standard_property.proxy)

                if standard_property.field_type == MetadataFieldTypes.RELATIONSHIP:
                    self.assertQuerysetEqual(standard_property_form.fields["relationship_value"].queryset, MetadataModel.objects.filter(proxy=standard_property.proxy.relationship_target_model))
                    subform_customizer = standard_property_form.get_subform_customizer()
                    model_subformset = standard_property_form.get_model_subformset()
                    standard_properties_subformsets = standard_property_form.get_standard_properties_subformsets()
                    scientific_properties_subformsets = standard_property_form.get_scientific_properties_subformsets()

                    self.assertIsNotNone(subform_customizer)
                    self.assertIsNotNone(model_subformset)
                    self.assertIsNotNone(standard_properties_subformsets)
                    self.assertIsNotNone(scientific_properties_subformsets)

                    # further testing of the subform content is handled in test_create_new_edit_subforms_from_models below


                    # TODO
                    pass


    def test_create_new_edit_forms_from_models(self):

        test_document_type = "modelcomponent"

        test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)

        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)

        test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])
        (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
        scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)

        (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)

        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)

        (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_new_edit_forms_from_models(models,model_customizer,standard_properties,standard_property_customizers,scientific_properties,scientific_property_customizers)


    def test_create_new_edit_subforms_from_models(self):

        test_document_type = "modelcomponent"

        test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)

        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)

        test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])
        property_customizer = test_customizer.standard_property_customizers.get(name="author")
        subform_customizer = property_customizer.subform_customizer
        self.assertIsNotNone(subform_customizer)

        (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(subform_customizer, MetadataVocabulary.objects.none())
        scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)

        test_subform_prefix = "test_prefix"
        subform_min, subform_max = [int(val) if val != "*" else val for val in property_customizer.relationship_cardinality.split("|")]

        (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(model_customizer.proxy, vocabularies=MetadataVocabulary.objects.none())

        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_new_realization_set(subform_customizer.project, subform_customizer.version, subform_customizer.proxy, standard_property_proxies, scientific_property_proxies, model_customizer, MetadataVocabulary.objects.none())

        (model_subformset, standard_properties_subformsets, scientific_properties_subformsets) = \
            create_new_edit_subforms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix=test_subform_prefix, subform_min=subform_min, subform_max=subform_max)

        self.assertEqual(model_subformset.prefix, u"%s_subform" % (test_subform_prefix))
        for i, model_subform in enumerate(model_subformset.forms):
            self.assertEqual(model_subform.prefix, u"%s-%s" % (model_subformset.prefix, i))

            for standard_properties_subformset in standard_properties_subformsets.values():
                self.assertEqual(standard_properties_subformset.prefix, u"%s_standard_properties" % (model_subform.prefix))
                for i, standard_property_subform in enumerate(standard_properties_subformset.forms):
                    self.assertEqual(standard_property_subform.prefix, u"%s-%s" % (standard_properties_subformset.prefix, i))

            for scientific_properties_subformset in scientific_properties_subformsets.values():
                self.assertEqual(scientific_properties_subformset.prefix, u"%s_scientific_properties" % (model_subform.prefix))
                for i, scientific_property_subform in enumerate(scientific_properties_subformset.forms):
                    self.assertEqual(scientific_property_subform.prefix, u"%s-%s" % (scientific_properties_subformset.prefix, i))

        actual_model_subformset_data = get_data_from_formset(model_subformset)

        test_model_subformset_data = {
            u'%s-INITIAL_FORMS' % (model_subformset.prefix) : 0,
            u'%s-TOTAL_FORMS' % (model_subformset.prefix) : 1,
            u'%s-0-id' % (model_subformset.prefix) : None,
            u'%s-0-component_key' % (model_subformset.prefix) : u'rootcomponent',
            u'%s-0-is_root' % (model_subformset.prefix) : True,
            u'%s-0-title' % (model_subformset.prefix) : u'RootComponent',
            u'%s-0-active' % (model_subformset.prefix) : True,
            u'%s-0-version' % (model_subformset.prefix) : self.version.pk,
            u'%s-0-project' % (model_subformset.prefix) : self.project.pk,
            u'%s-0-proxy' % (model_subformset.prefix) : model_proxy.pk,
            u'%s-0-order' % (model_subformset.prefix) : 1,
            u'%s-0-vocabulary_key' % (model_subformset.prefix) : u'default_vocabulary',
            u'%s-0-DELETE' % (model_subformset.prefix) : False,
            u'%s-0-description' % (model_subformset.prefix) : u'a stripped-down responsible party to use for testing\n                purposes.',
            u'%s-0-name' % (model_subformset.prefix) : u'responsibleParty',
            u'%s-0-is_document' % (model_subformset.prefix) : True
        }

        test_standard_properties_subformset_data = {
            u'test_prefix_subform-0_standard_properties-INITIAL_FORMS': 0,
            u'test_prefix_subform-0_standard_properties-TOTAL_FORMS': 2,
            u'test_prefix_subform-0_standard_properties-0-relationship_value': [],
            u'test_prefix_subform-0_standard_properties-0-proxy': MetadataStandardPropertyProxy.objects.get(model_proxy=model_proxy, name__iexact="individualname").pk,
            u'test_prefix_subform-0_standard_properties-0-field_type': u'ATOMIC',
            u'test_prefix_subform-0_standard_properties-0-name': u'individualName',
            u'test_prefix_subform-0_standard_properties-0-is_label': True,
            u'test_prefix_subform-0_standard_properties-0-enumeration_value': None,
            u'test_prefix_subform-0_standard_properties-0-id': None,
            u'test_prefix_subform-0_standard_properties-0-enumeration_other_value': 'Please enter a custom value',
            u'test_prefix_subform-0_standard_properties-0-order': 0,
            u'test_prefix_subform-0_standard_properties-0-atomic_value': u'',
            u'test_prefix_subform-0_standard_properties-0-model': None,
            u'test_prefix_subform-0_standard_properties-0-DELETE': False,
            u'test_prefix_subform-0_standard_properties-1-proxy': MetadataStandardPropertyProxy.objects.get(model_proxy=model_proxy, name__iexact="contactinfo").pk,
            u'test_prefix_subform-0_standard_properties-1-order': 1,
            u'test_prefix_subform-0_standard_properties-1-id': None,
            u'test_prefix_subform-0_standard_properties-1-name': u'contactInfo',
            u'test_prefix_subform-0_standard_properties-1-enumeration_other_value': 'Please enter a custom value',
            u'test_prefix_subform-0_standard_properties-1-field_type': u'RELATIONSHIP',
            u'test_prefix_subform-0_standard_properties-1-model': None,
            u'test_prefix_subform-0_standard_properties-1-is_label': False,
            u'test_prefix_subform-0_standard_properties-1-relationship_value': u'',
            u'test_prefix_subform-0_standard_properties-1-atomic_value': None,
            u'test_prefix_subform-0_standard_properties-1-enumeration_value': None,
            u'test_prefix_subform-0_standard_properties-1-DELETE': False,
        }

        self.assertDictEqual(actual_model_subformset_data,test_model_subformset_data,excluded_keys=[u"%s-id"%(model_subformset.prefix)])

        for standard_properties_subformset in standard_properties_subformsets.values():
            actual_standard_properties_formset_data = get_data_from_formset(standard_properties_subformset)
            self.assertDictEqual(actual_standard_properties_formset_data,test_standard_properties_subformset_data,excluded_keys=[u"%s-id"%(standard_properties_subformset.prefix)])


        for scientific_properties_subformset in scientific_properties_subformsets.values():
           self.assertEqual(len(scientific_properties_subformset.forms), 0)


    def test_create_edit_forms_from_data(self):

        test_document_type = "modelcomponent"

        test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)

        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)

        test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])
        (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)
        scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)

        (model_proxy, standard_property_proxies, scientific_property_proxies) = MetadataModelProxy.get_proxy_set(test_proxy, vocabularies=test_vocabularies)

        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_new_realization_set(self.project, self.version, model_proxy, standard_property_proxies, scientific_property_proxies, test_customizer, test_vocabularies)

        (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_new_edit_forms_from_models(models,model_customizer,standard_properties,standard_property_customizers,scientific_properties,scientific_property_customizers)

        post_data = get_data_from_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets)


        import ipdb; ipdb.set_trace()
