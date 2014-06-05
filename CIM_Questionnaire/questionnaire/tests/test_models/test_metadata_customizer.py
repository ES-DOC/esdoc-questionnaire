from django.forms import model_to_dict
from CIM_Questionnaire.questionnaire.models import MetadataModelCustomizer
from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase


class TestMetadataModelCustomizer(TestQuestionnaireBase):

    def test_customizer_proxy_join_from_database(self):
        """Test customizers and proxies are properly joined."""

        model_customizers = MetadataModelCustomizer.objects.all()
        for mc in model_customizers:
            pc_standard = mc.standard_property_customizers.all()
            pc_scientific = mc.scientific_property_customizers.all()
            for pc in [pc_standard, pc_scientific]:
                for row in pc:
                    self.assertEqual(row.name, row.proxy.name)

    def test_create_model_customizer(self):

        model_customizers = MetadataModelCustomizer.objects.all()

        excluded_fields = ["id","vocabularies","project","version","proxy","vocabulary_order"]
        serialized_model_customizers = [model_to_dict(model_customizer,exclude=excluded_fields) for model_customizer in model_customizers]

        customizers_to_test = [
            {'model_root_component': u'RootComponent', 'description': u'', 'model_show_hierarchy': True, 'default': True, 'model_title': u'modelcomponent', 'model_show_all_properties': True, 'model_show_all_categories': False, 'model_description': u'blah', 'model_hierarchy_name': u'Component Hierarchy', 'name': u'test'}
        ]

        # test that the projects have the expected standard fields
        for s,t in zip(serialized_model_customizers,customizers_to_test):
            self.assertDictEqual(s,t)
