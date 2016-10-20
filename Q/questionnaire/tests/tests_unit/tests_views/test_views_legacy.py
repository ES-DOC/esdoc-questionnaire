####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"

"""
.. module:: test_views_legacy

Tests the redirect_legacy_projects decorator
"""

from django.core.urlresolvers import reverse
from Q.questionnaire.tests.test_base import TestQBase
from Q.questionnaire.q_utils import add_parameters_to_url, FuzzyInt
from Q.questionnaire.views.views_legacy import *


class Test(TestQBase):

    def setUp(self):
        super(Test, self).setUp()

        # just setup some silly test projects
        # I don't care if they're valid or not
        # as long as 1 has 'is_legacy=True' it's good enough
        self.current_project = QProject(
            name="current_project",
            title="Current Project",
            email=self.test_user.email,
            is_legacy=False,
        )
        self.current_project.save()
        self.legacy_project = QProject(
            name="legacy_project",
            title="Legacy Project",
            email=self.test_user.email,
            is_legacy=True,
        )
        self.legacy_project.save()

    def tearDown(self):
        super(Test, self).tearDown()

    #####################
    # redirection tests #
    #####################

    # using the 'q_project' view as my test.
    # it doesn't really matter which one I use,
    # as long as it has the '@redirect_legacy_projects' decorator.
    # this decorator only applies to "GET" requests,
    # so I don't need to worry about any potential data passed in,
    # but I still check for explicit parameters in the URL just in-case.

    def test_redirect_legacy_projects(self):

        test_params = {
            "a": "a",
            "b": "b",
        }
        current_request_url = add_parameters_to_url(reverse("project", kwargs={
            "project_name": "current_project",
        }), **test_params)
        legacy_request_url = add_parameters_to_url(reverse("project", kwargs={
            "project_name": "legacy_project",
        }), **test_params)

        # check that a non-legacy view did not redirect and returned a normal status_code...
        response = self.client.get(current_request_url)
        with self.assertRaises(AssertionError):
            self.assertRedirects(response, expected_url=LEGACY_HOST+current_request_url)
        self.assertEqual(response.status_code, 200)

        import ipdb; ipdb.set_trace()
        # TODO: THIS ASSERTION FAILS
        # check that a legacy view did redirect and the status_code was either 301 or 302...
        response = self.client.get(legacy_request_url)
        self.assertRedirects(response, expected_url=LEGACY_HOST+legacy_request_url, status_code=FuzzyInt(301, 302), fetch_redirect_response=False)
