####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

"""
.. module:: q_tags

defines custom template tags
"""

from django import template
from django.db.models.query import QuerySet
from django.core.serializers import serialize
import json

from Q.questionnaire import get_version
from Q.questionnaire.models.models_sites import get_site_type
from Q.questionnaire.models.models_users import is_member_of as user_is_member_of, is_user_of as user_is_user_of, is_admin_of as user_is_admin_of, is_pending_of as user_is_pending_of
from Q.questionnaire.q_constants import *

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

@register.simple_tag
def profanities():
    return PROFANITIES_LIST

#################
# dynamic sites #
#################

@register.filter
def site_type(site):
    return get_site_type(site)

#######################
# authentication tags #
#######################

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
def is_pending_of(user, project):
    return user_is_pending_of(user, project)

################
# utility tags #
################

@register.filter
def index(sequence, i):
    """
    returns the ith element in the sequence, otherwise returns an empty string
    :param sequence:
    :param index:
    :return:
    """
    try:
        return sequence[i]
    except IndexError:
        return u""

@register.filter
def jsonify(object):
    """
    returns a JSON representation of a [set of] objects
    :param object:
    :return:
    """
    #  note - ng provides a "json" filter that can do this too
    if isinstance(object, QuerySet):
        return serialize('json', object)
    return json.dumps(object)


#############################
# form / field manipulation #
#############################

@register.filter
def get_form_by_field(formset, field_info):
    field_name, field_value = field_info.split('|')
    return formset.get_form_by_field(field_name, field_value)

@register.filter
def get_forms_by_field(formset, field_info):
    field_name, field_value = field_info.split('|')
    return formset.get_forms_by_field(field_name, field_value)
