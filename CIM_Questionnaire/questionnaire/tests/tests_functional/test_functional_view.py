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
.. module:: test_functional_view

Functional tests for the view page
"""

import time

from django.core.urlresolvers import reverse
from selenium.common.exceptions import NoSuchElementException
from CIM_Questionnaire.questionnaire.tests.tests_functional.test_functional_base import TestFunctionalBase
from CIM_Questionnaire.questionnaire import get_version
from CIM_Questionnaire.questionnaire.models import *
from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes


class Test(TestFunctionalBase):

    def setUp(self):
        super(Test, self).setUp()

        # going to use downscaling / cim 1.10 / modelcomponent / "one" document for my tests...

        self.test_project = MetadataProject.objects.get(name="downscaling")
        self.test_ontology = MetadataVersion.objects.get(name="cim", version="1.10")
        self.test_proxy = MetadataModelProxy.objects.get(name__iexact="modelcomponent", version=self.test_ontology)
        self.test_customizer = MetadataModelCustomizer(default=True, proxy=self.test_proxy)

        existing_documents = MetadataModel.objects.filter(proxy=self.test_proxy, is_root=True)
        self.test_document = MetadataModel.get_models_with_label("one", existing_documents)[0]

    def load_edit_panes(self, n_list):
        """
        click on each item number in "n_list" in the component hierarchy
        :param n_list: a list of 0-based numbers of panes to load
        :return:
        """
        edit_panes = self.webdriver.find_elements_by_css_selector(".pane")
        for n in n_list:
            pane_id = edit_panes[n].get_attribute("id")
            self.load_edit_pane(n)
            self.wait_by_css("#%s.loaded" % pane_id)

    def load_edit_pane(self, n):
        """
        clicks on the nth item in the component hierarchy;
        this will load the corresponding pane
        :param n: the 0-based number of the pane to load
        :return:
        """
        component_tree = self.webdriver.find_element_by_id("component_tree")
        component_tree_nodes = component_tree.find_elements_by_css_selector("span.dynatree-node")
        self.assertGreaterEqual(len(component_tree_nodes), n, msg="Unable to locate node #%s in component_tree" % n)
        selected_component_tree_node = component_tree_nodes[n]
        selected_component_tree_node.click()

    def get_property_type(self, property_element):
        property_tag = property_element.tag_name.lower()
        if property_tag == "input" or property_tag == "textarea":
            return MetadataFieldTypes.ATOMIC
        elif property_tag == "div":
            return MetadataFieldTypes.ENUMERATION
        else:
            return MetadataFieldTypes.RELATIONSHIP

    def test_view_existing(self):
        """
        This tests that viewing an existing document
        renders as expected
        :return:
        """

        index_url = reverse("view_existing", kwargs={
            "project_name": self.test_project.name.lower(),
            "version_key": self.test_ontology.get_key(),
            "model_name": self.test_proxy.name.lower(),
            "model_id": self.test_document.pk,
        })
        self.set_url(index_url)

        # test it has the right title...
        title = self.webdriver.title
        test_title = "CIM Questionnaire Viewer"
        self.assertEqual(title, test_title)

        # test it has the right version (in the footer)...
        footer = self.webdriver.find_element_by_css_selector("div.footer")
        version = get_version()
        self.assertIn(version, footer.text)

        # test it has the right content_title...
        content_title = self.webdriver.find_element_by_css_selector("div.title")
        self.assertIn(self.test_project.title, content_title.text)
        self.assertIn(self.test_proxy.name, content_title.text)

        # test that the phrase "read-only" appears as expected...
        self.assertIn("read-only", content_title.text)
        content_documentation = self.webdriver.find_element_by_css_selector("div.documentation")
        self.assertIn("read-only", content_documentation.text)

        # test that editing buttons are not displayed...
        accordion_buttons = self.webdriver.find_elements_by_css_selector("button.replace, button.add, button.remove")
        self.assertEqual(len(accordion_buttons), 0)
        with self.assertRaises(NoSuchElementException):
            self.webdriver.find_element_by_css_selector("div.submit")

    def test_view_existing_is_read_only(self):
        """
        This tests that viewing an existing document
        contains only read-only fields
        :return:
        """

        index_url = reverse("view_existing", kwargs={
            "project_name": self.test_project.name.lower(),
            "version_key": self.test_ontology.get_key(),
            "model_name": self.test_proxy.name.lower(),
            "model_id": self.test_document.pk,
        })
        self.set_url(index_url)

        panes = self.webdriver.find_elements_by_css_selector(".pane")
        for i, pane in enumerate(panes[:3]):  # test at least 3 panes (so that the test includes scientific properties)
            self.load_edit_pane(i)
            self.wait_by_css("#%s.loaded" % pane.get_attribute("id"))
            # time.sleep(10)
            tab_links = pane.find_element_by_css_selector(".tabs>ul").find_elements_by_css_selector("li a")
            for tab_link in tab_links:
                tab_link.click()
                tab_id = tab_link.get_attribute("href").split('#')[1]
                tab_content = pane.find_element_by_id(tab_id)
                standard_properties = tab_content.find_elements_by_css_selector(".standard_property")
                # TODO: SCIENTIFIC_PROPERTIES = ...
                for standard_property in standard_properties:
                    # assert that the property renders as read-only...

                    property_classes = standard_property.get_attribute("class")
                    self.assertIn("ui-state-disabled", property_classes)
                    # assert that the property cannot be edited...
                    # (after clicking, make sure that the property does not have the focus;
                    # it should not be selected
                    # nor should it be active [see http://stackoverflow.com/a/11998624])
                    property_type = self.get_property_type(standard_property)
                    if property_type == MetadataFieldTypes.ATOMIC:
                        standard_property_is_selected = standard_property.is_selected()  # comparing before & after b/c in-case this is a checkbox, is_selected() might be True by virtue of being checked
                        standard_property.click()
                        self.assertEqual(standard_property_is_selected, standard_property.is_selected(), msg="read-only %s field (within tab '%s') is able to be selected" % (property_type.getType(), tab_id))
                        self.assertNotEqual(standard_property, self.webdriver.switch_to.active_element)
                    elif property_type == MetadataFieldTypes.ENUMERATION:
                        enumeration_header = standard_property.find_element_by_css_selector(".multiselect_header")
                        enumeration_content = standard_property.find_element_by_css_selector(".multiselect_content")
                        enumeration_header.click()
                        self.assertFalse(enumeration_content.is_displayed(), msg="read-only %s field content (within tab '%s') is able to be displayed" % (property_type.getType(), tab_id))
                        self.assertNotEqual(enumeration_header, self.webdriver.switch_to.active_element)
                    elif property_type == MetadataFieldTypes.RELATIONSHIP:
                        if standard_property.tag_name == "select":
                            try:
                                first_option = standard_property.find_element_by_css_selector("option")
                                first_option.click()
                                self.assertFalse((first_option.is_selected()), msg="read-only %s field option (within tab '%s') is able to be selected" % (property_type.getType(), tab_id))
                                self.assertNotEqual(first_option, self.webdriver.switch_to.active_element)
                            except NoSuchElementException:
                                pass  # if you are here, then there are no options to test

    def test_view_new(self):
        """
        This tests that trying to view a new document
        results in the Questionnaire Error page being rendered
        :return:
        """

        index_url = reverse("view_new", kwargs={
            "project_name": self.test_project.name.lower(),
            "version_key": self.test_ontology.get_key(),
            "model_name": self.test_proxy.name.lower(),
        })
        self.set_url(index_url)

        # this should goto a Questionnaire Error page
        # (b/c you can't view a new document)

        # test it has the right title...
        title = self.webdriver.title
        test_title = "CIM Questionnaire Error"
        self.assertEqual(title, test_title)

        # test it has the right version (in the footer)...
        footer = self.webdriver.find_element_by_css_selector("div.footer")
        version = get_version()
        self.assertIn(version, footer.text)

        # test it has the right content...
        msg = self.webdriver.find_element_by_css_selector("td.msg")
        test_msg = "The Questionnaire only supports viewing of existing instances."
        self.assertEqual(msg.text, test_msg)
