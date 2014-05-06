
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

        # ensure that there is no categorized metadata before a new one is loaded
        qs = MetadataCategorization.objects.all()
        self.assertEqual(len(qs),0)

        # create a categorization
        test_categorization_name = "test_categorization.xml"
        test_categorization = MetadataCategorization(name="test",file=os.path.join(CATEGORIZATION_UPLOAD_PATH,test_categorization_name))
        test_categorization.save()
        
        # ensure the categorization is saved to the database
        qs = MetadataCategorization.objects.all()
        self.assertEqual(len(qs),1)

        # create a version
        test_version_name = "test_version.xml"
        test_version = MetadataVersion(name="test",file=os.path.join(VERSION_UPLOAD_PATH,test_version_name))
        test_version.categorization = test_categorization   # associate the "test" categorization w/ the "test" version
        test_version.save()

        # register a version
        self.assertEqual(test_version.registered,False)
        test_version.register()
        self.assertEqual(test_version.registered,True)

        # register a categorization        
        self.assertEqual(test_categorization.registered,False)
        test_categorization.register()
        self.assertEqual(test_categorization.registered,True)

        self.version = test_version
        self.categorization = test_categorization

        print "THE NUMBER OF METADATAMODELPROXIES IS %s" % (len(MetadataModelProxy.objects.all()))

    def tearDown(self):
        pass
    
    def test_setUp(self):
        qs = MetadataCategorization.objects.all()
        self.assertEqual(len(qs),1)


class MetadataEditingViewTest(TestCase):

# TODO: fixtures not currently working
# (perhaps b/c of the order in which fixtures are loaded)
#    fixtures = ["questionnaire_test_all.json"]

    def setUp(self):
        super(MetadataEditingViewTest,self).setUp()
        self.factory = RequestFactory()

    def tearDown(self):
        pass

    def test_default(self):
        self.assertTrue(True)

    def test_questionnaire_edit_new_get(self):
        project_name = "downscaling"
        version_name = "flarble"
        model_name = "modelcomponent"
        request_url = "/%s/edit/%s/%s" % (project_name,version_name,model_name)
        #import ipdb; ipdb.set_trace()
        request = self.factory.get(request_url)
        response = edit_new(request)
        self.assertEqual(response.status_code,200)

class MetadataVersionTest(MetadataTest):

    def test_register_models(self):

        models = MetadataModelProxy.objects.filter(version=self.version)

        serialized_models = models.values()
        to_test = [{'name': u'gridspec', 'stereotype': u'document', 'package': None, 'documentation': u'blah', 'version_id': 1, u'id': 2, 'order': 1},
                   {'name': u'modelcomponent', 'stereotype': u'document', 'package': None, 'documentation': u'blah', 'version_id': 1, u'id': 1, 'order': 0}]

        
        for s,t in zip(serialized_models,to_test):            
            # don't care about db pks
            t.pop("id")
            s.pop("id")
            t.pop("version_id")
            s.pop("version_id")
            self.assertDictEqual(s,t)

    def test_register_standard_properties(self):

        models = MetadataModelProxy.objects.filter(version=self.version)
        
        to_test = [[{'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'shortName', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'atomic_type': u'DEFAULT', u'id': 18, 'model_proxy_id': 4, 'enumeration_open': False, 'relationship_cardinality': u'', 'relationship_target_model_id': None, 'order': 0}], [{'field_type': u'RELATIONSHIP', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'grid', 'enumeration_multi': False, 'relationship_target_name': u'gridspec', 'enumeration_choices': u'', 'documentation': u'', 'atomic_type': u"['TEXT']", u'id': 17, 'model_proxy_id': 3, 'enumeration_open': False, 'relationship_cardinality': u'0|*', 'relationship_target_model_id': 4, 'order': 7}, {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'timing', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'atomic_type': u"['TEXT']", u'id': 16, 'model_proxy_id': 3, 'enumeration_open': False, 'relationship_cardinality': u'', 'relationship_target_model_id': None, 'order': 6}, {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'license', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'atomic_type': u"['TEXT']", u'id': 15, 'model_proxy_id': 3, 'enumeration_open': False, 'relationship_cardinality': u'', 'relationship_target_model_id': None, 'order': 5}, {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'purpose', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'atomic_type': u"['TEXT']", u'id': 14, 'model_proxy_id': 3, 'enumeration_open': False, 'relationship_cardinality': u'', 'relationship_target_model_id': None, 'order': 4}, {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'description', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'atomic_type': u"['TEXT']", u'id': 13, 'model_proxy_id': 3, 'enumeration_open': False, 'relationship_cardinality': u'', 'relationship_target_model_id': None, 'order': 3}, {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'longName', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'atomic_type': u"['TEXT']", u'id': 12, 'model_proxy_id': 3, 'enumeration_open': False, 'relationship_cardinality': u'', 'relationship_target_model_id': None, 'order': 2}, {'field_type': u'ENUMERATION', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'type', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'one|two|three', 'documentation': u'', 'atomic_type': u"['TEXT']", u'id': 11, 'model_proxy_id': 3, 'enumeration_open': False, 'relationship_cardinality': u'', 'relationship_target_model_id': None, 'order': 1}, {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'shortName', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'atomic_type': u"['TEXT']", u'id': 10, 'model_proxy_id': 3, 'enumeration_open': False, 'relationship_cardinality': u'', 'relationship_target_model_id': None, 'order': 0}]]

        #import ipdb; ipdb.set_trace()

        for model,standard_properties_to_test in zip(models,to_test):
            import ipdb;ipdb.set_trace()
            standard_properties = model.standard_properties.all()
            serialized_standard_properties = standard_properties.values()
            for serialized_standard_property,standard_property_to_test in zip(serialized_standard_properties,standard_properties_to_test):
                # don't care about db pks
                
##                standard_property_to_test.pop("id")
##                serialized_standard_property.pop("id")
##                standard_property_to_test.pop("model_proxy_id")
##                serialized_standard_property.pop("model_proxy_id")
##                standard_property_to_test.pop("relationship_target_model_id")
##                serialized_standard_property.pop("relationship_target_model_id")
                self.assertDictEqual(serialized_standard_property,standard_property_to_test)

class MetadataCategorizationTest(MetadataTest):

    def test_register_categories(self):

        categories = MetadataStandardCategoryProxy.objects.filter(categorization=self.categorization)

        serialized_categories = categories.values()
        categories_to_test = [{'name': u'Component Description', u'id': 3, 'categorization_id': 1, 'key': u'component-description', 'order': 3, 'description': u''}, {'name': u'Basic Properties', u'id': 2, 'categorization_id': 1, 'key': u'basic-properties', 'order': 2, 'description': u''}, {'name': u'Document Properties', u'id': 1, 'categorization_id': 1, 'key': u'document-properties', 'order': 1, 'description': u''}]
        
#        for category,category_to_test in zip(categories,categories_to_test):
#            serialized_category = model_to_dict(category)
#            serialized_category.pop("properties")

        for serialized_category,category_to_test in zip(serialized_categories,categories_to_test):
            self.assertDictEqual(serialized_category,serialized_category)

        for category in categories:
            categorized_properties = category.properties.all()
            properties_to_test = MetadataStandardPropertyProxy.objects.filter(category=category)

        