####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.db import models, transaction
from django.forms.models import modelform_factory, modelformset_factory
from django.test.client import RequestFactory
import tempfile

from Q.questionnaire.tests.test_base import TestQBase, TestModel, incomplete_test
from Q.questionnaire.q_utils import *

##########################
# some silly test models #
##########################


class TestUtilsModel(TestModel):

    name = models.CharField(blank=True, max_length=BIG_STRING, unique=True)
    other_name = models.CharField(blank=True, max_length=BIG_STRING, unique=False)

    def __str__(self):
        return self.name

TestUtilsForm = modelform_factory(TestUtilsModel, exclude=[])
TestUtilsFormSet = modelformset_factory(TestUtilsModel, TestUtilsForm)

TEST_MODELS = {
    "test_utils_model": TestUtilsModel,
}

####################################
# some silly test enumerated types #
####################################


class TestType(EnumeratedType):
    pass

TestTypes = EnumeratedTypeList([
    TestType("ONE", "one"),
    TestType("TWO", "two"),
    TestType("THREE", "three"),
])

#############################
# some silly test fn to use #
#############################


class TestFindInSequenceFunction(object):

    n = 0

    @classmethod
    def fn(cls, item, test_value):
        cls.n += 1
        return item == test_value


@legacy_code
def test_legacy_fn():
    return True

##############################################
# some silly validators to use w/ QValidator #
##############################################


class TestValidator1(QValidator):
    # has no msg; cannot be used
    name = "one"


class TestValidator2(QValidator):
    # has no __call_ method; cannot be used
    name = "two"
    msg = "invalid value"


class TestValidator3(QValidator):
    # has everything; can be used
    name = "three"
    msg = "this is invalid"

    def __call__(self, value):
        if value == "invalid":
            raise ValidationError(self.msg)

##############################
# the actual test base class #
##############################


class Test(TestQBase):

    def setUp(self):
        # setup the test models into the test db...
        for model_name, model_class in TEST_MODELS.iteritems():
            create_fn_name = model_class.create_fn_name
            try:
                model_create_fn = getattr(model_class, create_fn_name)
            except AttributeError:
                msg = "{0} has no {1} method".format(model_name, create_fn_name)
                raise TypeError(msg)
            with transaction.atomic():
                model_create_fn()
        # don't need questionnaire infrastructure...
        # super(Test, self).setUp()

    def tearDown(self):
        # setup the test models into the test db...
        for model_name, model_class in TEST_MODELS.iteritems():
            delete_fn_name = model_class.delete_fn_name
            try:
                model_delete_fn = getattr(model_class, delete_fn_name)
            except AttributeError:
                msg = "{0} has no {1} method".format(model_name, delete_fn_name)
                raise TypeError(msg)
            with transaction.atomic():
                model_delete_fn()
        # don't need questionnaire infrastructure...
        # super(Test, self).tearDown()

    #######################
    # test error handling #
    #######################

    def test_q_error(self):
        error_msg = "this is a test message"
        try:
            raise (QError(error_msg))
        except QError as e:
            self.assertEqual(
                str(e),
                "QError: {0}".format(error_msg)
            )

    def test_legacy_code(self):
        with self.assertRaises(QError):
            test_legacy_fn()

    #########################
    # test enumerated types #
    #########################

    def test_enumerated_types(self):

        # test I can get the right values...
        self.assertEqual(TestTypes.ONE, "ONE")
        self.assertEqual(TestTypes.ONE.get_type(), "ONE")
        self.assertEqual(TestTypes.ONE.get_name(), "one")

        # test I can't get the wrong values...
        try:
            TestTypes.FOUR
            self.assertEqual(True, False, msg="failed to recognize invalid enumerated_type")
        except EnumeratedTypeError:
            pass

        # test comparisons work...
        self.assertTrue(TestTypes.ONE == "ONE")
        self.assertTrue(TestTypes.ONE != "TWO")

        # test getting types explicitly works...
        self.assertEqual(TestTypes.get("ONE"), TestTypes.ONE)
        self.assertIsNone(TestTypes.get("INVALID_KEY"))

        # although there is support for enumerated type ordering, I don't actually care
        # so there are no tests for that functionality here

    ####################
    # test obfuscation #
    ####################

    def test_obfuscation(self):
        test_string = "Hello World!"
        test_encoding = encode_parameter(test_string)
        test_decoding = decode_parameter(test_encoding)

        self.assertNotEqual(test_string, test_encoding)
        self.assertEqual(test_string, test_decoding)

    ############################
    # test string manipulation #
    ############################

    def test_remove_spaces_and_linebreaks(self):
        valid_string = "This is a valid string."
        string_with_spaces = "This  is      a valid    string."
        string_with_linebreaks = "This \n is \n a \n valid \n string."
        string_with_spaces_and_linebreaks = "This  is  \n    a valid    string."

        self.assertEqual(valid_string, remove_spaces_and_linebreaks(valid_string))
        self.assertEqual(valid_string, remove_spaces_and_linebreaks(string_with_spaces))
        self.assertEqual(valid_string, remove_spaces_and_linebreaks(string_with_linebreaks))
        self.assertEqual(valid_string, remove_spaces_and_linebreaks(string_with_spaces_and_linebreaks))

    def test_pretty_string(self):
        test_pretty_string = "I Am A Pretty String"
        test_ugly_string = "iAmAPrettyString"

        self.assertEqual(test_pretty_string, pretty_string(test_ugly_string))

    def test_convert_to_camelCase(self):
        valid_string = "thisIsAValidString"
        invalid_string = "This is_a valid STRING"
        self.assertEqual(valid_string, convert_to_camelCase(invalid_string))

    ##############################
    # test sequence manipulation #
    ##############################

    def test_find_in_sequence(self):

        test_sequence = [1, 2, 3, 4, 5, ]

        TestFindInSequenceFunction.n = 0
        test_item = find_in_sequence(lambda item: TestFindInSequenceFunction.fn(item, 2), test_sequence)
        self.assertEqual(test_item, 2)
        self.assertEqual(TestFindInSequenceFunction.n, 2)

        TestFindInSequenceFunction.n = 0
        test_item = find_in_sequence(lambda item: TestFindInSequenceFunction.fn(item, 6), test_sequence)
        self.assertIsNone(test_item)
        self.assertEqual(TestFindInSequenceFunction.n, len(test_sequence))

    def test_find_dict_in_sequence(self):

        test_model_names = ["one", "two", "three"]
        for test_model_name in test_model_names:
            test_model = TestUtilsModel(name=test_model_name)
            test_model.save()

        test_models = TestUtilsModel.objects.all()
        self.assertEqual(len(test_models), len(test_model_names))

        test_model = find_dict_in_sequence({
            "name": "one"
        }, test_models)
        self.assertEqual(test_model, TestUtilsModel.objects.get(name="one"))

        test_model = find_dict_in_sequence({
            "name": "invalid"
        }, test_models)
        self.assertIsNone(test_model)

        test_model = find_dict_in_sequence({
            "invalid": "invalid"
        }, test_models)
        self.assertIsNone(test_model)

    def test_sort_list_by_key(self):

        one = {"name": "one", "order": 3}
        two = {"name": "two", "order": 2}
        three = {"name": "three", "order": 1}

        test_list = [one, two, three, ]

        test_list_sorted_by_name = sort_sequence_by_key(test_list, "name")
        self.assertListEqual(test_list_sorted_by_name, [one, three, two, ])
        test_list_sorted_by_order = sort_sequence_by_key(test_list, "order")
        self.assertListEqual(test_list_sorted_by_order, [three, two, one, ])
        test_list_sorted_by_name_reverse = sort_sequence_by_key(test_list, "name", reverse=True)
        self.assertListEqual(test_list_sorted_by_name_reverse, [two, three, one, ])
        test_list_sorted_by_order_reverse = sort_sequence_by_key(test_list, "order", reverse=True)
        self.assertListEqual(test_list_sorted_by_order_reverse, [one, two, three, ])

    ################################
    # test form/field manipulation #
    ################################

    def test_set_field_widget_attributes(self):
        test_model = TestUtilsModel(name="my_name", other_name="my_other_name")
        test_form = TestUtilsForm(instance=test_model)
        test_field = test_form.fields["name"]

        set_field_widget_attributes(test_field, {"class": "one"})
        self.assertIn("one", test_field.widget.attrs.get("class"))
        self.assertNotIn("two", test_field.widget.attrs.get("class"))

        set_field_widget_attributes(test_field, {"class": "two"})
        self.assertNotIn("one", test_field.widget.attrs.get("class"))
        self.assertIn("two", test_field.widget.attrs.get("class"))

    def test_update_field_widget_attributes(self):

        test_model = TestUtilsModel(name="my_name", other_name="my_other_name")
        test_form = TestUtilsForm(instance=test_model)
        test_field = test_form.fields["name"]

        update_field_widget_attributes(test_field, {"class": "one"})
        self.assertIn("one", test_field.widget.attrs.get("class"))
        self.assertNotIn("two", test_field.widget.attrs.get("class"))

        update_field_widget_attributes(test_field, {"class": "two"})
        self.assertIn("one", test_field.widget.attrs.get("class"))
        self.assertIn("two", test_field.widget.attrs.get("class"))

    #########################
    # test url manipulation #
    #########################

    def test_add_parameters_to_url(self):
        test_parameters = {
            "one": "a",
            "two": 2,
            "three": True,
        }
        test_url = add_parameters_to_url("www.test.com", **test_parameters)
        factory = RequestFactory()
        test_request = factory.get(test_url)
        self.assertEqual(test_request.GET.get("one"), u"a")
        self.assertEqual(test_request.GET.get("two"), u"2")
        self.assertEqual(test_request.GET.get("three"), u"True")

    ############################
    # test object manipulation #
    ############################

    @incomplete_test
    def test_evaluate_lazy_object(self):
        pass

    ################################
    # test (non-DRF) serialization #
    ################################

    def test_serialize_model_to_dict(self):
        test_model = TestUtilsModel(name="my_name", other_name="my_other_name")

        test_data = {
            "id": test_model.pk,
            "name": test_model.name,
            "other_name": test_model.other_name,
        }
        self.assertDictEqual(test_data, serialize_model_to_dict(test_model))

        test_data = {
            "id": test_model.pk,
            "name": test_model.name,
        }
        self.assertDictEqual(test_data, serialize_model_to_dict(test_model, exclude=["other_name"]))

        test_data = {
            "id": test_model.pk,
            "name": test_model.name,
            "other_name": "test",
        }
        self.assertDictEqual(test_data, serialize_model_to_dict(test_model, include={"other_name": "test"}))

    #################
    # test versions #
    #################

    def test_version_increment(self):
        test_version = Version("1.2.3")
        test_version += "1.2.3"
        self.assertEqual(test_version.fully_specified(), "2.4.6")

    def test_version_decrement(self):
        test_version = Version("1.2.3")
        test_version -= "1.2.3"
        self.assertEqual(test_version.fully_specified(), "0.0.0")
        with self.assertRaises(AssertionError):
            test_version -= "1.2.3"

    ##################
    # test FuzzyInts #
    ##################

    def test_fuzzy_int(self):
        test_fuzz = FuzzyInt(0, 10)

        self.assertEqual(test_fuzz, 0)
        self.assertEqual(test_fuzz, 5)
        self.assertEqual(test_fuzz, 10)
        self.assertNotEqual(test_fuzz, -1)
        self.assertNotEqual(test_fuzz, 11)

    ###################
    # test validators #
    ###################

    def test_qvalidator_object(self):
        valid_value = "test"
        invalid_value = "invalid"

        with self.assertRaises(AssertionError):
            one = TestValidator1()

        two = TestValidator2()
        with self.assertRaises(AssertionError):
            two(valid_value)

        three = TestValidator3()
        three(valid_value)
        with self.assertRaises(ValidationError):
            three(invalid_value)

    def test_validate_no_bad_chars(self):
        valid_value = "test"
        invalid_value = "\ / < > % # % { } [ ] $ |"
        validate_no_bad_chars(valid_value)
        with self.assertRaises(ValidationError):
            validate_no_bad_chars(invalid_value)

    def test_validate_not_blank(self):
        valid_value = "test"
        invalid_value = "     "
        validate_not_blank(valid_value)
        with self.assertRaises(ValidationError):
            validate_not_blank(invalid_value)

    def test_validate_no_spaces(self):
        valid_value = "test"
        invalid_value = "hello world"
        validate_no_spaces(valid_value)
        with self.assertRaises(ValidationError):
            validate_no_spaces(invalid_value)

    def test_validate_no_reserved_words(self):
        for reserved_word in RESERVED_WORDS:
            with self.assertRaises(ValidationError):
                validate_no_reserved_words(reserved_word)
        unreserved_word = "hello"
        validate_no_reserved_words(unreserved_word)

    def test_validate_no_profanities(self):
        for profanity in PROFANITIES_LIST:
            with self.assertRaises(ValidationError):
                validate_no_profanities(profanity)
        non_profanity = "hello"
        validate_no_profanities(non_profanity)

    def test_validate_password(self):
        test_password = "x"
        self.assertLess(len(test_password), MIN_PASSWORD_LENGTH)
        with self.assertRaises(ValidationError):
            validate_password(test_password)

        test_password = "password without non letters"
        self.assertGreater(len(test_password), MIN_PASSWORD_LENGTH)
        with self.assertRaises(ValidationError):
            validate_password(test_password)

        test_password = "validpassword123"
        self.assertGreater(len(test_password), MIN_PASSWORD_LENGTH)
        validate_password(test_password)

    def test_validate_file_extension(self):
        test_file_extensions = ["txt"]

        with tempfile.NamedTemporaryFile(suffix=".foo") as invalid_file:
            with self.assertRaises(ValidationError):
                validate_file_extension(invalid_file, test_file_extensions)

        with tempfile.NamedTemporaryFile(suffix=".txt") as valid_file:
            validate_file_extension(valid_file, test_file_extensions)

    @incomplete_test
    def test_validate_file_schema(self):
        pass
