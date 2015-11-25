####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'


from django.test import LiveServerTestCase
from django.core.exceptions import ImproperlyConfigured
import os

# test browser can be specified in environment variables
try:
    TEST_BROWSER = os.environ["TEST_BROWSER"].lower()
except KeyError:
    TEST_BROWSER = "firefox"  # use firefox by default
if TEST_BROWSER == "firefox":
    from selenium.webdriver.firefox.webdriver import WebDriver
elif TEST_BROWSER == "chrome" or TEST_BROWSER == "chromium":
    from selenium.webdriver.chrome.webdriver import WebDriver
elif TEST_BROWSER == "safari":
    from selenium.webdriver.safari.webdriver import WebDriver
elif TEST_BROWSER == "opera":
    from selenium.webdriver.opera.webdriver import WebDriver
else:
    msg = u"unknown test browser: '%s'" % TEST_BROWSER
    raise ImproperlyConfigured(msg)

TEST_TIMEOUT = 10  # seconds

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions


class TestFunctionalBase(LiveServerTestCase):
    """
    base class for functional tests; Uses selenium to drive a Firefox instance.
    By convention, some tests that are common to multiple pages
    are prefixed w/ "check" rather than "test"
    (so that they're not run automatically but can be called explicitly).
    """

    fixtures = ['questionnaire_testdata.json']

    @classmethod
    def setUpClass(cls):
        cls.webdriver = WebDriver()
        cls.webdriver.implicitly_wait(TEST_TIMEOUT)  # default wait (can explicitly wait using fns below)
        super(TestFunctionalBase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.webdriver.quit()
        super(TestFunctionalBase, cls).tearDownClass()

    ##############################
    # some additional assertions #
    ##############################

    def assertIn(self, member, container, msg=None):
        """
        performs a case-insensitive assertion
        (a lot of template code uses tags or filters that I want to be able to ignore)
        :param member:
        :param container:
        :param msg:
        :return:
        """

        member_lower = member.lower()
        container_lower = container.lower()

        if msg:
            return super(TestFunctionalBase, self).assertIn(member_lower, container_lower, msg=msg)
        else:
            return super(TestFunctionalBase, self).assertIn(member_lower, container_lower)

    #######################################################################
    # fns to hide details of whatever test domain LiveServerTestCase uses #
    #######################################################################

    def get_url(self, path=""):
        """
        returns a URL to use w/ tests
        :param path: path to append after the protocol+domain+port
        :return:
        """
        url = u"%s/%s" % (self.live_server_url, path.lstrip("/"))
        return url

    def set_url(self, path):
        """
        :param path: path to goto
        :return: None
        """
        if "//" in path:
            self.webdriver.get(path)
        else:
            self.webdriver.get(self.get_url(path))

    def assertURL(self, path):
        """
        :param path: asserts path matches the current url
        :return:
        """
        msg = "URLs do not match"

        current_url = self.webdriver.current_url.rstrip("/")

        if "//" in path:
            test_url = path.rstrip("/")
        else:
            test_url = self.get_url(path).rstrip("/")

        self.assertEqual(test_url, current_url, msg=msg)

    ###################################
    # checking generic custom widgets #
    ###################################

    def is_initialized(self, webelement):
        """
        checks if widget has been initialized via JS
        :param webelement: selenium webelement representing widget
        :return: boolean
        """
        widget_classes = webelement.get_attribute("class").split(" ")
        for widget_class in widget_classes:
            if widget_class.startswith("initialized_"):
                return True
        return False

    # ################################
    # # checking multiselect widgets #
    # ################################
    #
    # def is_multiselect_single(self, webelement):
    #     """
    #     :param webelement: selenium webelement representing multiselect widget
    #     :return: boolean
    #     """
    #     multiselect_classes = webelement.get_attribute("class").split(" ")
    #     return "single" in multiselect_classes
    #
    # def is_multiselect_multiple(self, webelement):
    #     """
    #     :param webelement: selenium webelement representing multiselect widget
    #     :return: boolean
    #     """
    #     multiselect_classes = webelement.get_attribute("class").split(" ")
    #     return "multiple" in multiselect_classes
    #
    # def is_multiselect_required(self, webelement):
    #     """
    #     :param webelement: selenium webelement representing multiselect widget
    #     :return: boolean
    #     """
    #     multiselect_classes = webelement.get_attribute("class").split(" ")
    #     return "selection_required" in multiselect_classes
    #
    # def get_multiselect_header(self, webelement):
    #     """
    #     :param webelement: selenium webelement representing multiselect widget
    #     :return: the header (button) of the widget
    #     """
    #     multiselect_header = webelement.find_element_by_css_selector(".multiselect_header")
    #     return multiselect_header
    #
    # def get_multiselect_content(self, webelement):
    #     """
    #     :param webelement: selenium webelement representing multiselect widget
    #     :return: the content (choices) of the widget
    #     """
    #     multiselect_content = webelement.find_element_by_css_selector(".multiselect_content")
    #     return multiselect_content
    #
    # def get_multiselect_options(self, webelement):
    #     """
    #     :param webelement: selenium webelement representing multiselect widget
    #     :return: the selected options of the widget
    #     """
    #     content = self.get_multiselect_content(webelement)
    #     options = content.find_elements_by_css_selector("ul li")
    #     return options
    #
    # def get_multiselect_values(self, webelement):
    #     """
    #     :param webelement: selenium webelement representing multiselect widget
    #     :return: the selected options of the widget
    #     """
    #     options = self.get_multiselect_options(webelement)
    #     selected_options = [option for option in options if option.get_attribute("selected")]
    #     return selected_options
    #
    # def set_multiselect_values(self, webelement, values):
    #     """
    #     :param webelement: selenium webelement representing multiselect widget
    #     :param values: string values to select
    #     :return: None
    #     """
    #     options = self.get_multiselect_options(webelement)
    #     for option in options:
    #         option_text = option.text
    #         option_input = option.find_element_by_tag_name("input")
    #         option_selected = option.get_attribute("selected")
    #         if option_text in values:
    #             if not option_selected:
    #                 option_input.click()
    #         else:
    #             if option_selected:
    #                 option_input.click()
    #
    # ######################
    # # checking help icons #
    # ######################
    #
    # def check_help_button(self, webelement):
    #     """
    #     tests that the help_button functions as expected
    #     :param webelement: selenium webelement representing field section
    #     :return:
    #     """
    #
    #     msg = "help_button does not function"
    #
    #     help_dialog = self.webdriver.find_element_by_id("help_dialog")
    #     help_button = webelement.find_element_by_css_selector("div.help_button")
    #
    #     self.assertFalse(help_dialog.is_displayed(), msg=msg)
    #     help_button.click()
    #     self.assertTrue(help_dialog.is_displayed(), msg=msg)
    #
    #     help_dialog_close_button = help_dialog.find_element_by_xpath("../div/button")
    #     help_dialog_close_button.click()
    #     self.assertFalse(help_dialog.is_displayed(), msg=msg)

    ###############################################
    # some stuff for dealing w/ JS loading delays #
    ###############################################

    # in general, these work by knowing that the JS code adds a class or element or whatever to the HTML
    # the selector argument targets the element _with_ that additional bit
    # it only returns once the element can be found

    def wait_by_css(self, selector):
        """
        pauses execution until an element w/ the specified css can be found
        :param selector:
        :return:
        """
        waiter = WebDriverWait(self.webdriver, TEST_TIMEOUT)
        locator = (By.CSS_SELECTOR, selector)
        element = waiter.until(expected_conditions.presence_of_element_located(locator))

        _msg = "Waited for %s seconds, but an element could not be found w/ the following css: '%s'" % (TEST_TIMEOUT, selector)
        self.assertIsNotNone(element, msg=_msg)

    def wait_by_xpath(self, selector):
        """
        pauses execution until an element w/ the specified xpath can be found
        :param selector:
        :return:
        """
        waiter = WebDriverWait(self.webdriver, TEST_TIMEOUT)
        locator = (By.XPATH, selector)
        element = waiter.until(expected_conditions.presence_of_element_located(locator))

        _msg = "Waited for %s seconds, but an element could not be found w/ the following xpath: '%s'" % (TEST_TIMEOUT, selector)
        self.assertIsNotNone(element, msg=_msg)