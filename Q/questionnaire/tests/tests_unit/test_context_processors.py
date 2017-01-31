####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"
"""
.. module:: test_context_processors

Tests for custom context_processors.  This includes debug.
"""

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import Client

from Q.questionnaire.context_processors.debug import debug as debug_context_processor
from Q.questionnaire.tests.test_base import TestQBase


class Test(TestQBase):

    def setUp(self):
        # no need for any questionnaire-specific stuff
        pass

    def tearDown(self):
        # no need for any questionnaire-specific stuff
        pass

    def test_debug(self):

        # just testing context_processors; don't need a _real_ request...
        client = Client()
        test_context = client.get(reverse("index")).context

        self.assertEqual(settings.DEBUG, debug_context_processor(test_context).get("debug"))

