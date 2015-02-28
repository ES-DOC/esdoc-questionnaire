
####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Dec 5, 2013 2:16:31 PM"

"""
.. module:: views_test

Used for testing

"""

from django.contrib.sites.models import get_current_site
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.forms import ModelForm

# from CIM_Questionnaire.questionnaire.models.metadata_test import TestModel
# from CIM_Questionnaire.questionnaire.fields import NULL_CHOICE, EMPTY_CHOICE, OTHER_CHOICE
from CIM_Questionnaire.questionnaire.utils import set_field_widget_attributes, update_field_widget_attributes
from CIM_Questionnaire.questionnaire import get_version

# TEST_CHOICES = [("one", "ONE"), ("two", "TWO"), ("three", "THREE"), ]
#
#
# class TestForm(ModelForm):
#
#     class Meta:
#         model = TestModel
#         fields = ["name", "enumeration_value", "enumeration_other_value", ]
#
#     def __init__(self, *args, **kwargs):
#         super(TestForm, self).__init__(*args, **kwargs)
#
#         PRETEND_CUSTOMIZER = {
#             "choices": list(TEST_CHOICES),
#             "nullable": True,
#             "open": True,
#             "multi": False,
#         }
#
#         # this is mimicing "get_current_field_value()"
#         field_name = "enumeration_value"
#         try:
#             if self.prefix:
#                 field_value = self.data[u"%s-%s" % (self.prefix, field_name)]
#             else:
#                 field_value = self.data[field_name]
#         except KeyError:
#             field_value = self.initial[field_name]
#
#         if isinstance(field_value, basestring) and PRETEND_CUSTOMIZER["multi"]:
#             self.initial[field_name] = field_value.split("|")
#
#         self.pretend_customize(**PRETEND_CUSTOMIZER)
#
#     def pretend_customize(self, **kwargs):
#         # this is just pretending to do real customization
#         choices = kwargs.pop("choices", [])
#         is_nullable = kwargs.pop("nullable", False)
#         is_open = kwargs.pop("open", False)
#         is_multi = kwargs.pop("multi", True)
#
#         enumeration_value_field = self.fields["enumeration_value"]
#         enumeration_other_field = self.fields["enumeration_other_value"]
#
#         custom_widget_attributes = {"class": "multiselect enumeration"}
#         all_enumeration_choices = choices
#         if is_nullable:
#             all_enumeration_choices += NULL_CHOICE
#             custom_widget_attributes["class"] += " nullable"
#         if is_open:
#             all_enumeration_choices += OTHER_CHOICE
#             custom_widget_attributes["class"] += " open"
#         if is_multi:
#             custom_widget_attributes["class"] += " multiple"
#             enumeration_value_field.set_choices(all_enumeration_choices, multi=True)
#         else:
#             custom_widget_attributes["class"] += " single"
#             enumeration_value_field.set_choices(all_enumeration_choices, multi=False)
#
#         update_field_widget_attributes(enumeration_value_field, custom_widget_attributes)
#         update_field_widget_attributes(enumeration_other_field, {"class": "other"})


def test(request):

    # request_parameters = request.GET.copy()
    # test_params = {}
    # for (key, value) in request_parameters.iteritems():
    #     test_params[key] = value
    # if len(test_params) > 0:
    #     test_model = TestModel.objects.get(**test_params)
    # else:
    #     test_model = TestModel()
    #
    # if request.method == "GET":
    #     test_form = TestForm(instance=test_model)
    #
    # else:  # request.method == "POST"
    #     data = request.POST
    #     test_form = TestForm(data, instance=test_model)
    #
    #     if test_form.is_valid():
    #         test_form.save()

    # gather all the extra information required by the template
    _dict = {
        "site": get_current_site(request),
        "questionnaire_version": get_version(),
        # "form": test_form,
    }

    return render_to_response('questionnaire/questionnaire_test.html', _dict, context_instance=RequestContext(request))
