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

import json

from django.core.urlresolvers import reverse
from django.contrib import messages

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase

from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer, MetadataModelCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy

from CIM_Questionnaire.questionnaire.forms.forms_customize import get_data_from_customizer_forms

from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes

from CIM_Questionnaire.questionnaire.utils import add_parameters_to_url

class TestMetadataCustomizer(TestQuestionnaireBase):


    def setUp(self):

        super(TestMetadataCustomizer,self).setUp()

        # setup an additional customizer for testing purposes that uses subforms
        test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact="modelcomponent")
        test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=["author"])

        self.model_customizer.default = False
        self.model_customizer.save()
        test_customizer.default = True
        test_customizer.save()

        self.test_customizer = test_customizer

    def test_get_existing_customizer_set(self):

        test_customizer = self.test_customizer
        test_vocabularies = test_customizer.project.vocabularies.filter(document_type__iexact=test_customizer.proxy.name.lower())

        (model_customizer,standard_category_customizers, standard_property_customizers, scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(test_customizer, test_vocabularies)

        # make sure the model_customizer is as expected
        self.assertEqual(model_customizer,test_customizer)

        # make sure the standard category customizers are as expected
        self.assertQuerysetEqual(standard_category_customizers, test_customizer.standard_property_category_customizers.all())

        # make sure the standard property customizers are as expected
        self.assertQuerysetEqual(standard_property_customizers, test_customizer.standard_property_customizers.all())

        for vocabulary in test_vocabularies:
            vocabulary_key = vocabulary.get_key()
            for component_proxy in vocabulary.component_proxies.all():
                component_key = component_proxy.get_key()

                # make sure the scientific category customizers are as expected
                test_scientific_category_customizer_qs_from_model = test_customizer.scientific_property_category_customizers.filter(vocabulary_key=vocabulary_key, component_key=component_key)
                scientific_category_customizer_qs = scientific_category_customizers[vocabulary_key][component_key]
                self.assertQuerysetEqual(test_scientific_category_customizer_qs_from_model,scientific_category_customizer_qs)

                # make sure the scientific property customizers are as expected
                test_scientific_property_customizer_qs_from_model = test_customizer.scientific_property_customizers.filter(vocabulary_key=vocabulary_key, component_key=component_key)
                scientific_property_customizer_qs = scientific_property_customizers[vocabulary_key][component_key]
                self.assertQuerysetEqual(test_scientific_property_customizer_qs_from_model,scientific_property_customizer_qs)
