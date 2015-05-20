####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2014 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'ben.koziol'
__date__ = "Dec 01, 2014 3:00:00 PM"

"""
.. module:: test_utils

Tests all the utility fns
"""

from django.db import models
from django.forms.models import modelformset_factory

from django.core.urlresolvers import reverse

from CIM_Questionnaire.questionnaire.forms.forms_base import MetadataForm, MetadataFormSet
from CIM_Questionnaire.questionnaire.tests.test_base import TestQuestionnaireBase, TestModel
from CIM_Questionnaire.questionnaire.utils import *


#################################################################
# a silly set of models and forms to use w/ form-specific tests #
#################################################################

class TestUtilsModel(TestModel):

    name = models.CharField(blank=True, null=True, max_length=BIG_STRING, unique=True)
    other_name = models.CharField(blank=True, null=True, max_length=BIG_STRING, unique=False)

    def __unicode__(self):
        return u"%s" % self.name

TEST_MODELS = {
    "test_utils_model": TestUtilsModel,
}


class TestUtilsForm(MetadataForm):

    class Meta:
        model = TestUtilsModel

    def __init__(self, *args, **kwargs):
        super(TestUtilsForm, self).__init__(*args, **kwargs)
        # just a silly bit of CSS to test later on w/ some utility fns
        set_field_widget_attributes(self.fields["name"], {"class": "test_class", })

    def render(self):
        """
        allows me to return what a template would render for a form
        """
        return self.as_table()


class TestUtilsFormSet(MetadataFormSet):

    """
    A basic modelformset, w/ one special feature:
    individual forms can have unique prefixes
    (this is just like the MetadataModelFormSet)
    """
    def add_prefix(self, index):
        if self.form_prefixes_list:
            return "%s" % self.form_prefixes_list[index]
        else:
            return super(TestUtilsFormSet, self).add_prefix(index)


def TestUtilsFormSetFactory(*args, **kwargs):

    _prefixes = kwargs.pop("prefixes", [])
    _data = kwargs.pop("data", None)
    _initial = kwargs.pop("initial", [])
    _queryset = kwargs.pop("queryset", TestUtilsModel.objects.none())
    new_kwargs = {
        "extra": kwargs.pop("extra", 0),
        "formset": TestUtilsFormSet,
        "form": TestUtilsForm,
    }
    new_kwargs.update(kwargs)

    prefix = "test_form"

    _formset = modelformset_factory(TestUtilsModel, *args, **new_kwargs)
    # can use curry() to pass arguments to the individual formsets
    #  _formset.form = staticmethod(curry(TestUtilsForm, arg=value))

    _formset.form_prefixes_list = _prefixes

    if _data:
        return _formset(_data, initial=_initial, prefix=prefix)

    return _formset(queryset=_queryset, initial=_initial, prefix=prefix)


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


##############################################
# a silly test fn to run w/ find_in_sequence #
##############################################


class TestFindInSequenceFunction(object):

    n = 0

    @classmethod
    def fn(cls, item, test_value):
        cls.n += 1
        return item == test_value


########################
# the utils test class #
########################

class Test(TestQuestionnaireBase):

    def setUp(self):
        for model_name, model_class in TEST_MODELS.iteritems():
            create_fn_name = model_class.create_fn_name
            try:
                model_create_fn = getattr(model_class, create_fn_name)
                model_create_fn()
            except AttributeError:
                msg = "%s has no %s method" % (model_name, create_fn_name)
                raise TypeError(msg)
        super(Test, self).setUp()

    def tearDown(self):
        for model_name, model_class in TEST_MODELS.iteritems():
            delete_fn_name = model_class.delete_fn_name
            try:
                model_delete_fn = getattr(model_class, delete_fn_name)
                model_delete_fn()
            except AttributeError:
                msg = "%s has no %s method" % (model_name, delete_fn_name)
                raise TypeError(msg)
        super(Test, self).tearDown()

    ######################################
    # ...and now for the actual tests... #
    ######################################

    ###########################
    # form/field manipulation #
    ###########################

    def test_get_form_by_field(self):

        test_model_names = ["one", "two", "three"]
        for test_model_name in test_model_names:
            test_model = TestUtilsModel(name=test_model_name)
            test_model.save()

        test_models = TestUtilsModel.objects.all()
        test_formset = TestUtilsFormSetFactory(queryset=test_models)

        test_form = get_form_by_field(test_formset, "name", "one")
        self.assertIsNotNone(test_form)
        self.assertEqual(test_form.instance, TestUtilsModel.objects.get(name="one"))

        test_form = get_form_by_field(test_formset, "name", "invalid")
        self.assertIsNone(test_form)

    def test_get_forms_by_field(self):

        test_model_parameter_list = [
            {"name": "one", "other_name": "foo", },
            {"name": "two", "other_name": "foo", },
            {"name": "three", "other_name": "bar", },
        ]
        for test_model_parameters in test_model_parameter_list:
            test_model = TestUtilsModel(**test_model_parameters)
            test_model.save()

        test_models = TestUtilsModel.objects.all()
        test_formset = TestUtilsFormSetFactory(queryset=test_models)

        test_forms = get_forms_by_field(test_formset, "other_name", "foo")
        self.assertEqual(len(test_forms), 2)
        test_instances = TestUtilsModel.objects.filter(other_name="foo")
        for test_form in test_forms:
            test_instance = test_form.instance
            self.assertIn(test_instance.pk, [instance.pk for instance in test_instances])

        test_forms = get_form_by_field(test_formset, "other_name", "invalid")
        self.assertIsNone(test_forms)

    def test_get_form_by_prefix(self):

        test_model_names = ["one", "two", "three", ]
        for test_model_name in test_model_names:
            test_model = TestUtilsModel(name=test_model_name)
            test_model.save()

        test_models = TestUtilsModel.objects.all()
        test_formset = TestUtilsFormSetFactory(queryset=test_models, prefixes=test_model_names)

        for test_prefix in test_model_names:
            test_form = get_form_by_prefix(test_formset, test_prefix)
            self.assertIsNotNone(test_form)
            self.assertEqual(test_form.instance, TestUtilsModel.objects.get(name=test_prefix))

        invalid_test_form = get_form_by_prefix(test_formset, "invalid_prefix")
        self.assertIsNone(invalid_test_form)

    def test_set_field_widget_attributes(self):
        test_model = TestUtilsModel(name="one", other_name="foo")
        test_form = TestUtilsForm(instance=test_model)

        rendered_form = test_form.render()
        self.assertIn(u'<input class="test_class"', rendered_form)

        set_field_widget_attributes(test_form.fields["name"], {"class": "new_class"})
        rendered_form = test_form.render()
        self.assertNotIn(u'<input class="test_class"', rendered_form)
        self.assertIn(u'<input class="new_class"', rendered_form)

    def test_update_field_widget_attributes(self):
        test_model = TestUtilsModel(name="one", other_name="foo")
        test_form = TestUtilsForm(instance=test_model)

        rendered_form = test_form.render()
        self.assertIn(u'<input class="test_class"', rendered_form)

        update_field_widget_attributes(test_form.fields["name"], {"class": "new_class"})
        rendered_form = test_form.render()
        self.assertIn(u'<input class="test_class new_class"', rendered_form)

    def test_model_to_data(self):
        test_model = TestUtilsModel(name="one", other_name="foo")

        test_model_data = model_to_data(test_model)
        test_form = TestUtilsForm(test_model_data)
        if test_form.is_valid():
            self.assertEqual(test_form.cleaned_data["name"], "one")
            self.assertEqual(test_form.cleaned_data["other_name"], "foo")

        test_model_data = model_to_data(test_model, include={"other_name": "bar"})
        test_form = TestUtilsForm(test_model_data)
        if test_form.is_valid():
            self.assertEqual(test_form.cleaned_data["name"], "one")
            self.assertEqual(test_form.cleaned_data["other_name"], "bar")

        test_model_data = model_to_data(test_model, exclude=["other_name", ])
        test_form = TestUtilsForm(test_model_data)
        if test_form.is_valid():
            self.assertEqual(test_form.cleaned_data["name"], "one")
            self.assertEqual(test_form.cleaned_data["other_name"], u'')

    def test_get_data_from_form(self):
        test_model = TestUtilsModel(name="one", other_name="foo")
        test_model_data = model_to_data(test_model, include={"loaded": True, })

        test_unbound_form = TestUtilsForm(instance=test_model)
        test_unbound_form_data = get_data_from_form(test_unbound_form, existing_data={"loaded": True, })
        for k, v in test_unbound_form_data.iteritems():
            self.assertEqual(test_model_data[k], v)

        test_bound_form = TestUtilsForm(test_model_data)
        test_bound_form_data = get_data_from_form(test_bound_form, existing_data={"loaded": True, })
        for k, v in test_bound_form_data.iteritems():
            self.assertEqual(test_model_data[k], v)

    #######################
    # string manipulation #
    #######################

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

    ####################
    # url manipulation #
    ####################

    def test_add_parameters_to_url(self):
        test_parameters = {
            "one": "a",
            "two": 2,
            "three": True,
        }
        test_url = add_parameters_to_url("www.test.com", **test_parameters)
        test_request = self.factory.get(test_url)
        self.assertEqual(test_request.GET.get("one"), u"a")
        self.assertEqual(test_request.GET.get("two"), u"2")
        self.assertEqual(test_request.GET.get("three"), u"True")

    ####################
    # enumerated types #
    ####################

    def test_enumerated_types(self):

        # test I can get the right values...
        self.assertEqual(TestTypes.ONE, "ONE")
        self.assertEqual(TestTypes.ONE.getType(), "ONE")
        self.assertEqual(TestTypes.ONE.getName(), "one")

        # test I can't get the wrong values...
        try:
            TestTypes.FOUR
            self.assertEqual(True, False, msg="failed to recognize invalid enumerated_type")
        except EnumeratedTypeError:
            pass

        # test comparisons work...
        self.assertTrue(TestTypes.ONE == "ONE")
        self.assertTrue(TestTypes.ONE != "TWO")

        # although there is support for ordering, I don't actually care

    #############
    # FuzzyInts #
    #############

    def test_fuzzy_int(self):
        test_fuzz = FuzzyInt(0, 10)

        self.assertEqual(test_fuzz, 0)
        self.assertEqual(test_fuzz, 5)
        self.assertEqual(test_fuzz, 10)
        self.assertNotEqual(test_fuzz, -1)
        self.assertNotEqual(test_fuzz, 11)

    ############
    # list fns #
    ############

    def test_get_index(self):
        test_list = ["one", "two", "three", ]

        test_list_item = get_index(test_list, 0)
        self.assertEqual(test_list_item, "one")

        test_list_item = get_index(test_list, 3)
        self.assertIsNone(test_list_item)

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

    def test_get_joined_keys_dict(self):

        dct = {
            u'couplingtechnology_01': {
                u'couplingtechnology': [],
                u'implementation': [1, 2, 3, ],
                u'couplingtechnologykeyproperties': [1, 2, 3, ],
                u'architecture': [1, ],
                u'composition': [1, 2, 3, 4, 5, ]
            },
            u'couplingtechnology_02': {
                u'couplingtechnology': [99],
                u'implementation': [10, 20, 30, ],
                u'couplingtechnologykeyproperties': [10, 20, 30, ],
                u'architecture': [10, ],
                u'composition': [10, 20, 30, 40, 50, ]
            }
        }

        actual = {
            u'couplingtechnology_01_composition': [1, 2, 3, 4, 5],
            u'couplingtechnology_02_composition': [10, 20, 30, 40, 50],
            u'couplingtechnology_02_couplingtechnologykeyproperties': [10, 20, 30],
            u'couplingtechnology_01_architecture': [1],
            u'couplingtechnology_01_couplingtechnologykeyproperties': [1, 2, 3],
            u'couplingtechnology_01_couplingtechnology': [],
            u'couplingtechnology_02_architecture': [10],
            u'couplingtechnology_01_implementation': [1, 2, 3],
            u'couplingtechnology_02_implementation': [10, 20, 30],
            u'couplingtechnology_02_couplingtechnology': [99]
        }

        joined_keys_dict = get_joined_keys_dict(dct)

        # output is copied so the memory locations should stay the same
        self.assertEqual(id(joined_keys_dict['couplingtechnology_02_composition']), id(dct['couplingtechnology_02']['composition']))

        self.assertDictEqual(joined_keys_dict, actual)

        # unicode key types are wanted
        for key in joined_keys_dict.iterkeys():
            self.assertIsInstance(key, unicode)


