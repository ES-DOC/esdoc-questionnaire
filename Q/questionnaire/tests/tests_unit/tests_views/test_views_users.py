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
.. module:: test_views_user

Tests the views associated w/ users (login, logout, register, etc.)
"""

from django.core.urlresolvers import reverse
from django.conf import settings
from uuid import uuid4

from Q.questionnaire.q_utils import FuzzyInt, add_parameters_to_url, get_data_from_form
from Q.questionnaire.tests.test_base import TestQBase, incomplete_test
from Q.questionnaire.views.views_users import *

class Test(TestQBase):

    ######################
    # registration tests #
    ######################

    def test_q_register_get(self):

        query_limit = FuzzyInt(0, 10)
        with self.assertNumQueries(query_limit):
            request_url = reverse("register", kwargs={})
            response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)

    def test_q_register_post(self):
        query_limit = FuzzyInt(0, 10)
        with self.assertNumQueries(query_limit):
            request_url = reverse("register", kwargs={})
            response = self.client.get(request_url)

        registration_form = response.context["form"]
        post_data = get_data_from_form(registration_form, include={
            settings.HONEYPOT_FIELD_NAME: u"",  # the honeypot field
        })
        post_data["username"] = "Binky"
        post_data["password1"] = "PaSsWoRd123!"
        post_data["password2"] = "PaSsWoRd123!"

        response = self.client.post(request_url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_q_register_post_honeypot(self):
        """
        just like test_q_register_post, but tries to fill out the "honeypot" field
        :return:
        """
        query_limit = FuzzyInt(0, 10)
        with self.assertNumQueries(query_limit):
            request_url = reverse("register", kwargs={})
            response = self.client.get(request_url)

        registration_form = response.context["form"]
        post_data = get_data_from_form(registration_form, include={
            settings.HONEYPOT_FIELD_NAME: str(uuid4()),  # the honeypot field
        })
        post_data["username"] = "Binky"
        post_data["password1"] = "PaSsWoRd123!"
        post_data["password2"] = "PaSsWoRd123!"

        response = self.client.post(request_url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 400)

    def test_q_register_redirect(self):

        redirect_to = "/test_project/"
        query_limit = FuzzyInt(0, 10)
        with self.assertNumQueries(query_limit):
            request_url = add_parameters_to_url(
                reverse("register"),
                next=redirect_to  # adding the redirection parameter here
            )
            response = self.client.get(request_url)

        registration_form = response.context["form"]
        post_data = get_data_from_form(registration_form, include={
            settings.HONEYPOT_FIELD_NAME: u"",  # the honeypot field
        })
        post_data["username"] = "Binky"
        post_data["password1"] = "PaSsWoRd123!"
        post_data["password2"] = "PaSsWoRd123!"

        response = self.client.post(request_url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], redirect_to)

    ########################
    # login / logout tests #
    ########################

    @incomplete_test
    def test_q_login_get(self):
        pass

    @incomplete_test
    def test_q_login_post(self):
        pass

    @incomplete_test
    def test_q_login_redirect(self):
        pass

    @incomplete_test
    def test_q_logout_get(self):
        pass

    @incomplete_test
    def test_q_login_post(self):
        pass

    @incomplete_test
    def test_q_logout_redirect(self):
        pass

    ##############
    # user tests #
    ##############

