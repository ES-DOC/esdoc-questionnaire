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

from Q.questionnaire.tests.test_base import TestQBase, create_project
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

        # self.test_project = create_project(
        #     name="test_project",
        #     title="Test Project",
        #     email="allyn.treshansky@noaa.gov",
        # )

        response = self.client.get(
            "/api/projects/?is_active=true&is_displayed=true&ordering=title"
        )
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content)

        cmip6_project_data = {
            'id': 2,
            'name': 'cmip6',
            'title': 'CMIP6',
            'description': 'A test project.',
            'email': 'allyn.treshansky@colorado.edu',
            'url': '',
            'is_active': True,
            'is_displayed': True,
            'is_legacy': False,
            'authenticated': True,
            'ontologies': [2],
        }

        esps_project_data = {
            'id': 3,
            'name': 'esps',
            'title': 'ESPS',
            'description': 'A test project.',
            'email': 'allyn.treshansky@colorado.edu',
            'url': '',
            'is_active': True,
            'is_displayed': True,
            'is_legacy': True,
            'authenticated': True,
            'ontologies': [],
        }

        test_project_data = {
            'id': 1,
            'name': 'test_project',
            'title': 'Test Project',
            'description': 'A test project.',
            'email': 'allyn.treshansky@colorado.edu',
            'url': '',
            'is_active': True,
            'is_displayed': True,
            'is_legacy': False,
            'authenticated': True,
            'ontologies': [1],
        }

        self.assertEqual(content["count"], 3)
        self.assertDictEqual(content["results"][0], cmip6_project_data)
        self.assertDictEqual(content["results"][1], esps_project_data)
        self.assertDictEqual(content["results"][2], test_project_data)