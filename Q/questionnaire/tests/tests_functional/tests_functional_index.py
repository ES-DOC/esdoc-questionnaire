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


"""
.. module:: test_functional_index

Functional tests for the index page
"""

from django.core.urlresolvers import reverse

from Q.questionnaire.tests.tests_functional.test_functional_base import TestFunctionalBase
from Q.questionnaire import get_version


class Test(TestFunctionalBase):

    def test_index_renders(self):
        """
        just test some basic top-level stuff on the index page
        :return:
        """

        index_url = reverse("index", kwargs={})
        self.set_url(index_url)

        # test it has the right title...
        title = self.webdriver.title
        test_title = "ES-DOC Questionnaire"
        self.assertEqual(title, test_title)

        # test it has the right version (in the footer)...
        footer = self.webdriver.find_element_by_css_selector("div.footer")
        version = get_version()
        self.assertIn(version, footer.text)

        # test it has the right site notice...
        site_section = self.webdriver.find_element_by_id("site")
        self.assertIsNotNone(site_section)

        # test the user block exists (and a user is not logged in)...
        user_section = self.webdriver.find_element_by_id("user")
        user_buttons = user_section.find_elements_by_css_selector("a.label")
        self.assertEqual(len(user_buttons), 2)
        self.assertEqual(user_buttons[0].text, "register")
        self.assertEqual(user_buttons[1].text, "login")

        # test that there are some projects...
        projects_section = self.webdriver.find_element_by_id("projects")
        projects = projects_section.find_elements_by_css_selector("a.project")
        self.assertGreater(len(projects), 0)
