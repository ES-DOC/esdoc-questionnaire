####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2014 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'
__date__ = "May 15, 2015 3:00:00 PM"

"""
.. module:: test_functional_index

Functional tests for the index page
"""

from django.core.urlresolvers import reverse

from CIM_Questionnaire.questionnaire.tests.tests_functional.test_functional_base import TestFunctionalBase
from CIM_Questionnaire.questionnaire.models import MetadataProject
from CIM_Questionnaire.questionnaire import get_version


class Test(TestFunctionalBase):

    def test_index_renders(self):
        """
        :return:
        """

        index_url = reverse("index", kwargs={})
        self.set_url(index_url)

        # test it has the right title...
        title = self.webdriver.title
        test_title = "CIM Questionnaire"
        self.assertEqual(title, test_title)

        # test it has the right version (in the footer)...
        footer = self.webdriver.find_element_by_css_selector("div.footer")
        version = get_version()
        self.assertIn(version, footer.text)

        # test it has a link to the Django Admin (in the footer)...
        link_text = "Django Admin Interface"
        self.assertIn(link_text, footer.text)

        # test it has the right site notice...
        site_section = self.webdriver.find_element_by_id("site")
        self.assertIsNotNone(site_section)

        # test the user block exists (and a user is not logged in)...
        user_section = self.webdriver.find_element_by_id("user")
        user_buttons = user_section.find_elements_by_css_selector("a.button")
        self.assertEqual(len(user_buttons), 2)
        self.assertEqual(user_buttons[0].text, "register")
        self.assertEqual(user_buttons[1].text, "login")

        ###########################
        # test the projects field #
        ###########################

        projects_section = self.webdriver.find_element_by_css_selector("tr.field[name='projects']")
        projects_widget = projects_section.find_element_by_css_selector("div.multiselect")

        # test it is initialized...
        self.is_initialized(projects_widget)

        # test it is required...
        self.is_multiselect_required(projects_widget)

        # test it has the right set of projects...
        projects_widget_options = self.get_multiselect_options(projects_widget)
        displayed_projects = [projects_widget_option.text for projects_widget_option in projects_widget_options]
        active_projects = [project.title for project in MetadataProject.objects.filter(active=True)]
        self.assertItemsEqual(displayed_projects, active_projects)

        # test the help dialog box works...
        self.check_help_button(projects_section)

    def test_index_select_valid_project(self):

        index_url = reverse("index", kwargs={})
        self.set_url(index_url)

        submit_button = self.webdriver.find_element_by_css_selector("div.submit input.button")

        # test it takes user to project page...
        project_to_test = MetadataProject.objects.get(name__iexact="downscaling")
        projects_section = self.webdriver.find_element_by_css_selector("tr.field[name='projects']")
        projects_widget = projects_section.find_element_by_css_selector("div.multiselect")
        self.set_multiselect_values(projects_widget, [project_to_test.title])

        submit_button.click()
        self.assertURL(project_to_test.name)

    def test_index_select_invalid_project(self):

        index_url = reverse("index", kwargs={})
        self.set_url(index_url)

        submit_button = self.webdriver.find_element_by_css_selector("div.submit input.button")

        old_url = self.webdriver.current_url
        submit_button.click()

        # test it's re-loaded the same page...
        self.assertURL(old_url)

        # test it returns w/ error...
        projects_section = self.webdriver.find_element_by_css_selector("tr.field[name='projects']")
        projects_error = projects_section.find_element_by_css_selector("div.error_wrapper")
        self.assertIsNotNone(projects_error)
