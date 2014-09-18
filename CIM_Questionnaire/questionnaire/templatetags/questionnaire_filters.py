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
from django.template.defaultfilters import slugify

from django.contrib.sites.models import Site
from django.contrib.auth.models  import User

from CIM_Questionnaire.questionnaire.models.metadata_site import get_metadata_site_type
from CIM_Questionnaire.questionnaire.utils import DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY

register = template.Library()

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
    if isinstance(site,Site):
        return get_metadata_site_type(site)
    else:
        return None


@register.filter
def is_member_of(user,project):
    if isinstance(user,User):
        if user.is_superuser:
            # admin is a member of _all_ projects
            return True
        return user.metadata_user.is_member_of(project)
    return False


@register.filter
def is_user_of(user, project):
    if isinstance(user,User):
        if user.is_superuser:
            # admin has _all_ permisions
            return True
        return  user.metadata_user.is_user_of(project)
    return False


@register.filter
def is_admin_of(user, project):
    if isinstance(user,User):
        if user.is_superuser:
            # admin has _all_ permisions
            return True
        return  user.metadata_user.is_admin_of(project)
    return False


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

@register.filter
def get_active_scientific_categories_by_key(model_customizer,key):
    return model_customizer.get_active_scientific_categories_by_key(key)


@register.filter
def get_active_scientific_properties_by_key(model_customizer,key):
    return model_customizer.get_active_scientific_properties_by_key(key)


@register.filter
def get_active_scientific_categories_and_properties_by_key(model_customizer,key):
    return model_customizer.get_active_scientific_categories_and_properties_by_key(key)

#
# @register.filter
# def get_standard_properties_subformset_for_model(standard_property_form,model_form):
#
#     standard_properties_subformsets = standard_property_form.get_standard_properties_subformsets()
#
#     model_prefix = model_form.prefix
#
#     return standard_properties_subformsets[model_prefix]


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