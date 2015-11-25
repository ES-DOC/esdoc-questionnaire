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
.. module:: test_views_base

Tests the views fns common to all (non-api) views
"""

from django.core.urlresolvers import reverse

from Q.questionnaire.q_utils import add_parameters_to_url
from Q.questionnaire.tests.test_base import TestQBase, incomplete_test
from Q.questionnaire.views.views_base import *

class Test(TestQBase):

    def test_add_parameters_to_context(self):

        test_params = {
            "one": "one",
            "two": "two",
            "three": "three,"
        }
        request_url = add_parameters_to_url(reverse("test"), **test_params)
        request = self.factory.get(request_url)
        context = add_parameters_to_context(request)

        for key, value in test_params.iteritems():
            self.assertEqual(context[key], value)




