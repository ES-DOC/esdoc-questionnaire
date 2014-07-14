from django.forms import model_to_dict
from CIM_Questionnaire.questionnaire.models import MetadataStandardCategoryProxy
from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase


class TestMetadataCategorization(TestQuestionnaireBase):

    def test_register_standard_categories(self):

        categories = MetadataStandardCategoryProxy.objects.all()

        excluded_fields = ["id","categorization","properties"]
        serialized_categories = [model_to_dict(category,exclude=excluded_fields) for category in categories]

        categories_to_test = [
            {'name': u'Document Properties', 'key': u'document-properties', 'order': 1, 'description': u''},
            {'name': u'Basic Properties', 'key': u'basic-properties', 'order': 2, 'description': u''},
            {'name': u'Component Description', 'key': u'component-description', 'order': 3, 'description': u''},
        ]

        # test that the categories have the expected standard fields
        for s,t in zip(serialized_categories,categories_to_test):
            self.assertDictEqual(s,t)

        # test that they have the expected foreignkeys
        for category in categories:
            self.assertEqual(category.categorization,self.categorization)
            # TODO: TEST THAT "PROPETIES" M2M FIELD IS AS EXPECTED
