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

Tests the silly view used for testing
"""

from django.core.urlresolvers import reverse

from Q.questionnaire.tests.test_base import TestQBase
from Q.questionnaire.views.views_test import *

class Test(TestQBase):

    def test_q_test_get(self):

        request_url = reverse("test")
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
