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

        # override some parent attributes w/ API-specific factory...
        self.factory = APIRequestFactory()
        self.client = APIClient()

        # no need to call the parent stuff
        # super(Test, self).setUp()

    def tearDown(self):
        pass

        # no need to call the parent stuff...
        # super(Test, self).tearDown()

    #########
    # tests #
    #########

    def test_api_get(self):

        self.test_project = create_project(
            name="test_project",
            title="Test Project",
            email="allyn.treshansky@noaa.gov",
        )

        response = self.client.get(
            "/api/projects/?is_active=true&is_displayed=true&ordering=title"
        )
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content)
        self.assertDictEqual(
            content,
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 1,
                        "name": "test_project",
                        "title": "Test Project",
                        "description": "",
                        "email": "allyn.treshansky@noaa.gov",
                        "url": "",
                        "is_active": True,
                        "is_displayed": True,
                        "authenticated": True,
                        "ontologies": []
                    }
                ]
            }
        )


