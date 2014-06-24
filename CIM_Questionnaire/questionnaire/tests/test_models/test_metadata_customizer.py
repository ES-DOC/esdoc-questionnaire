from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.models import MetadataCustomizer, MetadataModelCustomizer, MetadataModelProxy
from django.db import transaction
from django.db.utils import IntegrityError
from django.forms import model_to_dict


class TestMetadataCustomizer(TestQuestionnaireBase):

    def test_get_new_customizer_set(self):
        """Test that customizer sets are created correctly"""

        test_model_name = "modelcomponent"
        model_proxy_to_be_customized = MetadataModelProxy.objects.get(version=self.version,name__iexact=test_model_name)
        vocabularies_to_be_customized = self.project.vocabularies.filter(document_type__iexact=test_model_name)
        (test_model_customizer,test_standard_category_customizers,test_standard_property_customizers,test_scientific_category_customizers,test_scientific_property_customizers) = \
            MetadataCustomizer.get_new_customizer_set(self.project, self.version, model_proxy_to_be_customized, vocabularies_to_be_customized)

        # test that the proxies match up
        for test_standard_category_customizer in test_standard_category_customizers:
            self.assertEqual(test_standard_category_customizer.name,test_standard_category_customizer.proxy.name)
        for test_standard_property_customizer in test_standard_property_customizers:
            self.assertEqual(test_standard_property_customizer.name,test_standard_property_customizer.proxy.name)
        for vocabulary_key,test_scientific_category_customizer_dict in test_scientific_category_customizers.iteritems():
            for component_key,test_scientific_category_customizer_list in test_scientific_category_customizer_dict.iteritems():
                for test_scientific_category_customizer in test_scientific_category_customizer_list:
                    self.assertEqual(test_scientific_category_customizer.name,test_scientific_category_customizer.proxy.name)
        for vocabulary_key,test_scientific_property_customizer_dict in test_scientific_property_customizers.iteritems():
            for component_key,test_scientific_property_customizer_list in test_scientific_property_customizer_dict.iteritems():
                for test_scientific_property_customizer in test_scientific_property_customizer_list:
                    self.assertEqual(test_scientific_property_customizer.name,test_scientific_property_customizer.proxy.name)


    def test_get_existing_customizer_set(self):
        """Tests that customizer sets are retrieved correctly"""

        test_model_name = "modelcomponent"
        model_proxy_to_be_customized = MetadataModelProxy.objects.get(version=self.version,name__iexact=test_model_name)
        vocabularies_to_be_customized = self.project.vocabularies.filter(document_type__iexact=test_model_name)
        (test_model_customizer,test_standard_category_customizers,test_standard_property_customizers,test_scientific_category_customizers,test_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(self.customizer, vocabularies_to_be_customized)

        # test that the customizers match up w/ the existing db models
        existing_model_customizer = self.customizer
        self.assertEqual(test_model_customizer,existing_model_customizer)

        for test_standard_property_customizer,existing_standard_property_customizer in zip(test_standard_property_customizers,existing_model_customizer.standard_property_customizers.all()):
            self.assertEqual(test_standard_property_customizer,existing_standard_property_customizer)

        # test that the proxies match up
        for test_standard_category_customizer in test_standard_category_customizers:
            self.assertEqual(test_standard_category_customizer.name,test_standard_category_customizer.proxy.name)
        for test_standard_property_customizer in test_standard_property_customizers:
            self.assertEqual(test_standard_property_customizer.name,test_standard_property_customizer.proxy.name)
        for vocabulary_key,test_scientific_category_customizer_dict in test_scientific_category_customizers.iteritems():
            for component_key,test_scientific_category_customizer_list in test_scientific_category_customizer_dict.iteritems():
                for test_scientific_category_customizer in test_scientific_category_customizer_list:
                    self.assertEqual(test_scientific_category_customizer.name,test_scientific_category_customizer.proxy.name)
        for vocabulary_key,test_scientific_property_customizer_dict in test_scientific_property_customizers.iteritems():
            for component_key,test_scientific_property_customizer_list in test_scientific_property_customizer_dict.iteritems():
                for test_scientific_property_customizer in test_scientific_property_customizer_list:
                    self.assertEqual(test_scientific_property_customizer.name,test_scientific_property_customizer.proxy.name)

    def test_save_customizer_set(self):

        test_model_name = "modelcomponent"
        model_proxy_to_be_customized = MetadataModelProxy.objects.get(version=self.version,name__iexact=test_model_name)
        vocabularies_to_be_customized = self.project.vocabularies.filter(document_type__iexact=test_model_name)
        (test_model_customizer,test_standard_category_customizers,test_standard_property_customizers,test_scientific_category_customizers,test_scientific_property_customizers) = \
            MetadataCustomizer.get_new_customizer_set(self.project, self.version, model_proxy_to_be_customized, vocabularies_to_be_customized)

        # test that saving fails on a customizer w/ a duplicate name
        try:
            test_model_customizer.name = self.customizer.name
            with transaction.atomic(): # ensure that exceptions do not prevent future transactions
                MetadataCustomizer.save_customizer_set(test_model_customizer,test_standard_category_customizers,test_standard_property_customizers,test_scientific_category_customizers,test_scientific_property_customizers)
            self.assertTrue(False,msg="failed to catch duplicate name of customizer")
        except IntegrityError:
            test_model_customizer.name = "my_test_customizer"
            test_model_customizer.save()
            pass

        # test that saving a new default model_customizer causes any other default model_customizer to no longer be default
        test_model_customizer.default = True
        with transaction.atomic(): # ensure that exceptions do not prevent future transactions
            MetadataCustomizer.save_customizer_set(test_model_customizer,test_standard_category_customizers,test_standard_property_customizers,test_scientific_category_customizers,test_scientific_property_customizers)
        self.assertEqual(test_model_customizer.refresh().default,True)
        self.assertEqual(self.customizer.refresh().default,False)
        self.customizer.default = True
        self.customizer.save()
        self.assertEqual(test_model_customizer.refresh().default,False)
        self.assertEqual(self.customizer.refresh().default,True)


# class TestMetadataModelCustomizer(TestQuestionnaireBase):
#
#     def test_create_model_customizer(self):
#
#         model_customizers = MetadataModelCustomizer.objects.all()
#
#         excluded_fields = ["id","vocabularies","project","version","proxy","vocabulary_order"]
#         serialized_model_customizers = [model_to_dict(model_customizer,exclude=excluded_fields) for model_customizer in model_customizers]
#
#         customizers_to_test = [
#             {'model_root_component': u'RootComponent', 'description': u'', 'model_show_hierarchy': True, 'default': True, 'model_title': u'modelcomponent', 'model_show_all_properties': True, 'model_show_all_categories': False, 'model_description': u'blah', 'model_hierarchy_name': u'Component Hierarchy', 'name': u'test'}
#         ]
#
#         # test that the projects have the expected standard fields
#         for s,t in zip(serialized_model_customizers,customizers_to_test):
#             self.assertDictEqual(s,t)
