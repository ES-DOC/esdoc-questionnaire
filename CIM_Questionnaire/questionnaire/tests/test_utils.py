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

from django.core.urlresolvers import reverse
from CIM_Questionnaire.questionnaire.tests.test_base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.forms.forms_edit import create_new_edit_forms_from_models
from CIM_Questionnaire.questionnaire.utils import *


##############################################
# a silly test fn to run w/ find_in_sequence #
##############################################

class TestFindInSequenceFunction(object):

    n = 0

    @classmethod
    def fn(cls, item, test_value):
        cls.n += 1
        return item == test_value


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


########################
# the utils test class #
########################

class Test(TestQuestionnaireBase):

    # def setUp(self):
    #     pass
    #
    # def tearDown(self):
    #     pass

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

    def test_remove_spaces_and_linebreaks(self):

        valid_string = "This is a valid string."
        string_with_spaces = "This  is      a valid    string."
        string_with_linebreaks = "This \n is \n a \n valid \n string."
        string_with_spaces_and_linebreaks = "This  is  \n    a valid    string."

        self.assertEqual(valid_string, remove_spaces_and_linebreaks(valid_string))
        self.assertEqual(valid_string, remove_spaces_and_linebreaks(string_with_spaces))
        self.assertEqual(valid_string, remove_spaces_and_linebreaks(string_with_linebreaks))
        self.assertEqual(valid_string, remove_spaces_and_linebreaks(string_with_spaces_and_linebreaks))

    def test_add_parameters_to_url(self):

        base_url = reverse("questionnaire_test")
        test_url = add_parameters_to_url(base_url, **{
            "one": 1,
            "two": "two",
        })
        test_request = self.factory.get(test_url)

        self.assertEqual(test_request.GET.get("one", None), u"1")
        self.assertEqual(test_request.GET.get("two", None), u"two")

####################################################
# some fns to access particular forms of a formset #
####################################################

    def get_form_by_field(self):
        # TODO
        pass

    def test_get_forms_by_field(self):
        # TODO
        pass

    def test_get_form_by_prefix(self):

        (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_new_edit_forms_from_models(
                self.downscaling_model_component_realization_set["models"],
                self.downscaling_model_component_customizer_set["model_customizer"],
                self.downscaling_model_component_realization_set["standard_properties"],
                self.downscaling_model_component_customizer_set["standard_property_customizers"],
                self.downscaling_model_component_realization_set["scientific_properties"],
                self.downscaling_model_component_customizer_set["scientific_property_customizers"],
            )

        model_keys = [model.get_model_key() for model in self.downscaling_model_component_realization_set["models"]]

        for model_key in model_keys:
            model_form = get_form_by_prefix(model_formset, model_key)
            self.assertIsNotNone(model_form)

        invalid_model_form = get_form_by_prefix(model_formset, "invalid_key")
        self.assertIsNone(invalid_model_form)
