####################
#   Django-CIM-Forms
#   Copyright (c) 2012 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Jun 10, 2013 5:49:37 PM"

"""
.. module:: questionnaire_filters

Summary of module goes here

"""

from django import template

from Q.questionnaire.models.models_sites import get_site_type
from Q.questionnaire.models.models_vocabularies import DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY
from Q.questionnaire.models.models_users import is_member_of as user_is_member_of, is_user_of as user_is_user_of, is_admin_of as user_is_admin_of
from Q.questionnaire.q_utils import pretty_string as pretty_string_fn
from Q.questionnaire.q_constants import QUESTIONNAIRE_CODE_URL, QUESTIONNAIRE_EMAIL
from Q.questionnaire import get_version

register = template.Library()

#####################
# get static things #
#####################

@register.simple_tag
def q_version():
    return get_version()

@register.simple_tag
def q_url():
    return QUESTIONNAIRE_CODE_URL

@register.simple_tag
def q_email():
    return QUESTIONNAIRE_EMAIL

@register.assignment_tag
def get_default_vocabulary_key():
    return DEFAULT_VOCABULARY_KEY


@register.assignment_tag
def get_default_component_key():
    return DEFAULT_COMPONENT_KEY

@register.filter
def a_or_an(string):
    """
    filter to return "a" or "an" depending on whether string starts with a vowel sound
    """
    # TODO: handle confusing things like "an hour" or "a unicycle"
    vowel_sounds = ["a","e","i","o","u"]
    if string[0].lower() in vowel_sounds:
        return "an"
    else:
        return "a"


@register.filter
def pretty_string(string):
    return pretty_string_fn(string)


@register.filter
def get_length_of_values(dict):
    length_of_values = 0
    values = dict.values()
    for value in values:
        length_of_values += len(value)
    return length_of_values


@register.filter
def get_value_from_key(dict,key):
    return dict.get(key)

@register.filter
def site_type(site):
    return get_site_type(site)

@register.filter
def is_member_of(user, project):
    return user_is_member_of(user, project)

@register.filter
def is_user_of(user, project):
    return user_is_user_of(user, project)

@register.filter
def is_admin_of(user, project):
    return user_is_admin_of(user, project)


@register.filter
def get_form_by_field(formset,field_tuple):
    # TODO: USE FNS IN UTILS FOR THIS
    # returns the 1st form in a fieldset whose specified field has the specified value
    (field_name,field_value) = field_tuple.split('|')
    for form in formset:
        if form.get_current_field_value(field_name) == field_value:
            return form
    return None


@register.filter
def get_forms_by_field(formset,field_tuple):
    # TODO: USE FNS IN UTILS FOR THIS
    # returns all forms in a fieldset whose specified field has the specified value
    (field_name,field_value) = field_tuple.split('|')
    forms = []
    for form in formset:
        if form.get_current_field_value(field_name) == field_value:
            forms.append(form)
    return forms

##############################
# not happy w/ these filters #
##############################

from Q.questionnaire.views.views_api_bak import get_active_standard_categories as get_active_standard_categories_fn
from Q.questionnaire.views.views_api_bak import get_active_standard_properties as get_active_standard_properties_fn
from Q.questionnaire.views.views_api_bak import get_active_standard_properties_for_category as get_active_standard_properties_for_category_fn
from Q.questionnaire.views.views_api_bak import get_active_standard_categories_and_properties as get_active_standard_categories_and_properties_fn
from Q.questionnaire.views.views_api_bak import get_active_scientific_categories_by_key as get_active_scientific_categories_by_key_fn
from Q.questionnaire.views.views_api_bak import get_active_scientific_properties_by_key as get_active_scientific_properties_by_key_fn
from Q.questionnaire.views.views_api_bak import get_active_scientific_categories_and_properties_by_key as get_active_scientific_categories_and_properties_by_key_fn


@register.filter
def get_active_standard_categories(model_customizer):
    return get_active_standard_categories_fn(model_customizer)


@register.filter
def get_active_standard_properties(model_customizer):
    return get_active_standard_properties_fn(model_customizer)


@register.filter
def get_active_standard_categories_and_properties(model_customizer):
    return get_active_standard_categories_and_properties_fn(model_customizer)


@register.filter
def get_active_scientific_categories_by_key(model_customizer, key):
    return get_active_scientific_categories_by_key_fn(model_customizer, key)


@register.filter
def get_active_scientific_properties_by_key(model_customizer, key):
    return get_active_scientific_properties_by_key_fn(model_customizer, key)


@register.filter
def get_active_scientific_categories_and_properties_by_key(model_customizer, key):
    return get_active_scientific_categories_and_properties_by_key_fn(model_customizer, key)

#########################
# check if still needed #
#########################

@register.filter
def index(sequence,index):
    try:
        return sequence[index]
    except IndexError:
        return ''


@register.filter
def get_number_of_properties_from_key(formsets,key):
    if formsets and key in formsets:
        return formsets[key].number_of_properties
    return 0


@register.filter
def get_field_by_name(form,field_name):
    return form[field_name]


@register.filter
def get_instance_pk(form):
    instance = form.instance
    if instance:
        return instance.pk
    return -1