####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

from Q.questionnaire.tests.test_base import TestQBase, create_project, create_ontology, remove_ontology, create_categorization, remove_categorization
from Q.questionnaire.models.models_proxies import QModelProxy, QPropertyProxy
from Q.questionnaire.models.models_things import *
from Q.questionnaire.q_utils import serialize_model_to_dict, sort_list_by_key
from Q.questionnaire import q_logger

class TestQThing(TestQBase):

    def setUp(self):

        # don't do the base setUp (it would interfere w/ the ids of the ontology created below)
        # super(TestQOntolgoy, self).setUp()

        self.test_project = create_project(
            name="test_project",
            title="Test Project",
            email="allyn.treshansky@noaa.gov",
            description="A test project to use while testing recursions",
        )
        self.test_categorization = create_categorization(
            filename="categorization.xml",
            name="test_categorization",
            version="2.0",
        )
        self.test_ontology_schema = create_ontology(
            filename="ontology_schema.xml",
            name="test_ontology_schema",
            version="2.0",
        )
        self.test_ontology_schema.categorization = self.test_categorization
        self.test_ontology_schema.save()

        # TODO: SEE THE COMMENT IN "q_fields.py" ABOUT SETTING VERSION MANUALLY...
        self.test_ontology_schema.refresh_from_db()
        self.test_categorization.refresh_from_db()

        self.test_ontology_schema.register()
        self.test_categorization.register()

    def tearDown(self):

        # don't do the base tearDown
        # super(TestQOntolgoy, self).tearDown()

        remove_categorization(categorization=self.test_categorization)
        remove_ontology(ontology=self.test_ontology_schema)

    def test_get_new_things(self):

        import ipdb; ipdb.set_trace()
        model_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="model")
        recursive_thing_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="recursive_thing")

        test_model_thing = QModelThing(
            project=self.test_project,
            ontology=self.test_ontology_schema,
            proxy=model_proxy,
        )
        property_proxy=model_proxy.property_proxies.get(name__iexact="thing")
        test_property_thing = QPropertyThing(
            proxy=property_proxy,
        )


    def test_get_new_thing(self):

        model_proxy = self.test_ontology_schema.model_proxies.get(name__iexact="model")
        import ipdb; ipdb.set_trace()
        test_customizations = {}
        test_model_customization = get_new_customizations(
            model_proxy.name,
            test_customizations,
            project=self.test_project,
            ontology=self.test_ontology_schema,
            model_proxy=model_proxy,
        )

        self.assertEqual(len(test_customizations), 16)

