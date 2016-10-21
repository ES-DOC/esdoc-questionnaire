####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"

"""
.. module:: test_api_projects

"""

from rest_framework.test import APIRequestFactory, APIClient
import json

from Q.questionnaire.tests.test_base import TestQBase
from Q.questionnaire.q_constants import *


class Test(TestQBase):

    def setUp(self):
        # no need to call the parent stuff
        # super(Test, self).setUp()

        # override some parent attributes w/ API-specific factory...
        self.factory = APIRequestFactory()
        self.client = APIClient()

    def tearDown(self):
        # no need to call the parent stuff...
        # super(Test, self).tearDown()
        pass

    #########
    # tests #
    #########

    def test_api_get_from_fixture(self):

        response = self.client.get(
            "/api/ontologies/"
        )
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content)

        cim_ontology_data = {
            "id": 2,
            "name": "cim",
            "version": 33554432,
            "url": "http://www.foo.com",
            "key": "cim_2.0.0",
            "description": "Metafor CIM ontology schema - version 2",
            "is_registered": True,
            "file": "http://localhost:8000/site_media/questionnaire/ontologies/cim_2.xml",
            "categorization": 1,
            "ontology_type": "SCHEMA",
            "title": "cim [2.0.0]",
            "document_types": [
                {
                    "title": "Downscaling",
                    "id": 9,
                    "name": "downscaling"
                },
                {
                    "title": "Ensemble",
                    "id": 3,
                    "name": "ensemble"
                },
                {
                    "title": "Model",
                    "id": 47,
                    "name": "model"
                },
                {
                    "title": "Party",
                    "id": 58,
                    "name": "party"
                },
                {
                    "title": "Simulation",
                    "id": 11,
                    "name": "simulation"
                }
            ]
        }

        test_ontology_data = {
            "id": 1,
            "name": "test_ontology",
            "version": 16777216,
            "url": "http://www.foo.com",
            "key": "test_ontology_1.0.0",
            "description": "This is a pretend CIM version used for testing purposes only. If you are seeing this in the production site, then something has gone horribly wrong.",
            "is_registered": True,
            "file": "http://localhost:8000/site_media/questionnaire/ontologies/ontology_schema.xml",
            "categorization": 2,
            "ontology_type": "SCHEMA",
            "title": "test_ontology [1.0.0]",
            "document_types": [
                {
                    "title": "Model",
                    "id": 72,
                    "name": "model"
                }
            ]
        }

        self.assertEqual(content["count"], 2)
        self.assertDictEqual(content["results"][0], cim_ontology_data, excluded_keys=["guid", "created", "modified", "file"])
        self.assertDictEqual(content["results"][1], test_ontology_data, excluded_keys=["guid", "created", "modified", "file"])
