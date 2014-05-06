
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

__author__="allyn.treshansky"
__date__ ="Dec 9, 2013 4:33:11 PM"

"""
.. module:: tests

Summary of module goes here

"""

import os

from django.test import TestCase
from django.test.client import RequestFactory

from questionnaire.models import *
from questionnaire.views import *

from questionnaire.models.metadata_version import UPLOAD_PATH as VERSION_UPLOAD_PATH
from questionnaire.models.metadata_categorization import UPLOAD_PATH as CATEGORIZATION_UPLOAD_PATH
from questionnaire.models.metadata_vocabulary import UPLOAD_PATH as VOCABULARY_UPLOAD_PATH


class MetadataTest(TestCase):

    def setUp(self):
        # request factory for all tests
        self.factory = RequestFactory()

        #import ipdb; ipdb.set_trace()

        # create a categorization
        test_categorization_name = "test_categorization.xml"
        test_categorization = MetadataCategorization(name="test",file=os.path.join(CATEGORIZATION_UPLOAD_PATH,test_categorization_name))
        test_categorization.save()

        # create a version
        test_version_name = "test_version.xml"
        test_version = MetadataVersion(name="test",file=os.path.join(VERSION_UPLOAD_PATH,test_version_name))
        test_version.categorization = test_categorization   # associate the "test" categorization w/ the "test" version
        test_version.save()

        # create a vocabulary
        test_vocabulary_name = "test_vocabulary.xml"
        test_vocabulary = MetadataVocabulary(name="test",file=os.path.join(VOCABULARY_UPLOAD_PATH,test_vocabulary_name))
        test_vocabulary.document_type = "modelcomponent"
        test_vocabulary.save()

        # register a version
        self.assertEqual(test_version.registered,False)
        test_version.register()
        self.assertEqual(test_version.registered,True)

        # register a categorization        
        self.assertEqual(test_categorization.registered,False)
        test_categorization.register()
        self.assertEqual(test_categorization.registered,True)

        # register a vocabulary
        self.assertEqual(test_vocabulary.registered,False)
        test_vocabulary.register()
        self.assertEqual(test_vocabulary.registered,True)

        self.version = test_version
        self.categorization = test_categorization
        self.vocabulary = test_vocabulary
        
    def tearDown(self):
        pass

##class MetadataEditingViewTest(TestCase):
##
### TODO: fixtures not currently working
### (perhaps b/c of the order in which fixtures are loaded)
###    fixtures = ["questionnaire_test_all.json"]
##
##    def setUp(self):
##        super(MetadataEditingViewTest,self).setUp()
##        self.factory = RequestFactory()
##
##    def tearDown(self):
##        pass
##
##    def test_default(self):
##        self.assertTrue(True)
##
##    def test_questionnaire_edit_new_get(self):
##        project_name = "downscaling"
##        version_name = "flarble"
##        model_name = "modelcomponent"
##        request_url = "/%s/edit/%s/%s" % (project_name,version_name,model_name)
##        #import ipdb; ipdb.set_trace()
##        request = self.factory.get(request_url)
##        response = edit_new(request)
##        self.assertEqual(response.status_code,200)


class MetadataVersionTest(MetadataTest):

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
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'shortName', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 0, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u"['TEXT']"},
            ],
            [
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'shortName', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 0, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'DEFAULT'},
                {'field_type': u'ENUMERATION', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'type', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'one|two|three', 'documentation': u'', 'order': 1, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u"['TEXT']"},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'longName', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 2, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u"['TEXT']"},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'description', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 3, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u"['TEXT']"},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'purpose', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 4, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u"['TEXT']"},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'license', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 5, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u"['TEXT']"},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'timing', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 6, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u"['TEXT']"},
                {'field_type': u'RELATIONSHIP', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'grid', 'enumeration_multi': False, 'relationship_target_name': u'gridspec', 'enumeration_choices': u'', 'documentation': u'', 'order': 7, 'enumeration_open': False, 'relationship_cardinality': u'0|*', 'atomic_type': u"['TEXT']"}
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


class MetadataCategorizationTest(MetadataTest):

    def test_register_categories(self):

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

class MetadataVocabularyTest(MetadataTest):

    def test_register_components(self):
        components = MetadataComponentProxy.objects.all()

        import ipdb; ipdb.set_trace()
        
        pass

###        categories = MetadataStandardCategoryProxy.objects.all()
###
###        excluded_fields = ["id","categorization","properties"]
###        serialized_categories = [model_to_dict(category,exclude=excluded_fields) for category in categories]
###
###        categories_to_test = [
###            {'name': u'Document Properties', 'key': u'document-properties', 'order': 1, 'description': u''},
###            {'name': u'Basic Properties', 'key': u'basic-properties', 'order': 2, 'description': u''},
###            {'name': u'Component Description', 'key': u'component-description', 'order': 3, 'description': u''},
###        ]
###
###
###        # test that the categories have the expected standard fields
###        for s,t in zip(serialized_categories,categories_to_test):
###            self.assertDictEqual(s,t)
###
###        # test that they have the expected foreignkeys
###        for category in categories:
###            self.assertEqual(category.categorization,self.categorization)
###
###            # TODO: TEST THAT "PROPETIES" M2M FIELD IS AS EXPECTED
