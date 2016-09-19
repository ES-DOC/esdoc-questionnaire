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

class TestObject(object):

    def __init__(self, *args, **kwargs):
        name = kwargs.pop("name")
        count = kwargs.pop("count", 0)
        self.name = name
        self.count = count

    def __str__(self):
        return "{0} [{1}]".format(self.name, self.count)

def create_test_object(name=None, count=0):
    test_object = TestObject(name=name, count=count)
    return test_object

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

    def test_get_or_create_cached_object(self):

        test_key = "test_key"
        test_session = self.client.session

        with self.assertRaises(QError):
            test_object = get_cached_object(
                test_session,
                test_key
            )

        test_object = get_or_create_cached_object(
            test_session,
            test_key,
            create_test_object,
            **{
                "name": "test",
                "count": 1,
            }
        )

        import ipdb; ipdb.set_trace()

        self.assertEqual(test_object.count, 1)

        pass
