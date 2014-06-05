from django.forms import model_to_dict
from CIM_Questionnaire.questionnaire.models import MetadataProject, MetadataVocabulary
from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase


class TestMetadataProject(TestQuestionnaireBase):

    def test_create_project(self):

        projects = MetadataProject.objects.all()

        excluded_fields = ["id","providers","vocabularies"]
        serialized_projects = [model_to_dict(project,exclude=excluded_fields) for project in projects]

        projects_to_test = [
            {'authenticated': False, 'description': u'', 'title': u'Test', 'url': u'', 'active': True, 'email': None, 'name': u'test'}
        ]

        # test that the projects have the expected standard fields
        for s,t in zip(serialized_projects,projects_to_test):
            self.assertDictEqual(s,t)

        # test that they have the expected foreignkeys
        vocabularies = MetadataVocabulary.objects.all()
        for project in projects:
            self.assertQuerysetEqual(project.vocabularies.all(),vocabularies)
