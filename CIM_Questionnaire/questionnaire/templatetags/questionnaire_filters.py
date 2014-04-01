
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
import os
import re

from django.contrib.sites.models import Site
from django.contrib.auth.models  import User

from questionnaire.utils  import *
from questionnaire.models import *
from questionnaire.forms  import *

register = template.Library()

@register.filter
def a_or_an(string):
    """
    filter to return "a" or "an" depending on whether string starts with a vowel sound
    """
    # TODO: handle confusing things like "an hour" or "a unicycle"
    vowel_sounds = ["a","e","i","o","u"]
    if string[0] in vowel_sounds:
        return "an"
    else:
        return "a"

@register.filter
def get_value_from_key(dict,key):
    if key in dict:
        return dict[key]
    return None

@register.filter
def get_value_length_from_key(dict,key):
    if key in dict:
        return len(dict[key])
    return 0

@register.filter
def get_number_of_properties_from_key(formsets,key):
    if key in formsets:
        return formsets[key].number_of_properties
    return 0

@register.filter
def site_type(site):
    if isinstance(site,Site):
        return site.metadata_site.get_type()
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


###@register.filter
###def get_property_type(form):
###
###    try:
###        property = form.instance
###        return property.field_type
###    except AttributeError:
###        msg = "form instance has no field_type attribute; is it a property form?"
###        print msg
###        return None

@register.filter
def get_field_by_name(form,field_name):
    return form[field_name]

@register.filter
def get_instance_pk(form):
    instance = form.instance
    if instance:
        return instance.pk
    return -1