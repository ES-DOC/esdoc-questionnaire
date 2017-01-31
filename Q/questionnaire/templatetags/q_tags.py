####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

"""
.. module:: q_tags

defines custom template tags
"""

from django import template
from django.conf import settings
from django.db.models.query import QuerySet
from django.core.serializers import serialize
from django.template.base import TemplateSyntaxError, render_value_in_context
from itertools import cycle as itertools_cycle
import json

from Q.questionnaire import get_version
from Q.questionnaire.models.models_sites import get_site_type
from Q.questionnaire.models.models_users import is_member_of as user_is_member_of, is_user_of as user_is_user_of, is_admin_of as user_is_admin_of, is_pending_of as user_is_pending_of
from Q.questionnaire.q_fields import ENUMERATION_OTHER_CHOICE
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
    return settings.Q_CODE_URL


@register.simple_tag
def q_email():
    return settings.Q_EMAIL


@register.simple_tag
def profanities():
    return PROFANITIES_LIST


@register.simple_tag
def reserved_words():
    return RESERVED_WORDS


@register.simple_tag
def enumeration_other_choice():
    return ENUMERATION_OTHER_CHOICE


@register.tag
def nil_reasons():
    return NIL_REASONS


# TODO: NOT SURE WHY THIS DIDN'T WORK W/ SIMPLE TAGS;
# TODO: USING AN INCLUSION TAG SEEMS LIKE OVERKILL
# TODO: (EVEN THOUGH ITS'S RECOMMENDED BY THE DOCS)
@register.inclusion_tag("questionnaire/_q_view_property_nillable.html", takes_context=True)
def nillable(context):
    return {
        'form': context.get("form"),
        'nil_reasons': NIL_REASONS,
    }

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

#################
# dynamic sites #
#################


@register.filter
def site_type(site):
    return get_site_type(site)

################
# utility tags #
################


@register.filter
def index(sequence, i):
    """
    returns the ith element in the sequence, otherwise returns an empty string
    :param sequence:
    :param i:
    :return:
    """
    try:
        return sequence[i]
    except IndexError:
        return u""


@register.filter
def jsonify(object):
    """
    returns a JSON representation of [a set of] object[s]
    :param object:
    :return:
    """
    # note: ng provides a "json" filter that can do this too
    # note: but Django doesn't [https://code.djangoproject.com/ticket/17419]
    if isinstance(object, QuerySet):
        return serialize('json', object)
    return json.dumps(object)


@register.filter
def a_or_an(value):
    """
    filter to return "a" or "an" depending on whether string starts with a vowel sound
    """
    # TODO: handle confusing things like "an hour" or "a unicycle"
    vowel_sounds = ["a", "e", "i", "o", "u"]
    if value[0].lower() in vowel_sounds:
        return "an"
    else:
        return "a"


@register.filter
def format(value, arg):
    """
    Alters default filter "stringformat" to not add the % at the front,
    so the variable can be placed anywhere in the string.
    """
    try:
        if value is not None:
            # return (str(arg)) % value
            return (str(value)) % arg
        else:
            return ""
    except (ValueError, TypeError):
        return ""

###########################################
# do some clever things w/ template loops #
###########################################


class ConditionalNode(template.Node):

    def __init__(self, conditional_operator, conditional_variable_name):
        self.conditional_operator = conditional_operator
        self.conditional_variable = template.Variable(conditional_variable_name)
        self.last_cycle_value = None

    # TODO: USING "nif" IS KIND OF HACKY... IS THERE A BETTER WAY TO HANDLE DIFFERENT SORTS OF CONDITIONALS
    def passes_condition(self, value):
        if self.conditional_operator == "if":
            return bool(value) is True
        elif self.conditional_operator == "nif":
            return bool(value) is False
        else:
            raise TemplateSyntaxError("unknown conditional_operator")

    def render(self, context):
        msg = "{0} must define a custom 'render' method.".format(self.__class__.__name__)
        raise NotImplementedError(msg)


# cycle through variables iff some condition is met...

class ConditionalCycleNode(ConditionalNode):

    def __init__(self, cycle_values, conditional_operator, conditional_variable_name):
        super(ConditionalCycleNode, self).__init__(conditional_operator, conditional_variable_name)
        self.cycle_values = cycle_values
        self.last_cycle_value = None

    def render(self, context):
        if self not in context.render_context:
            context.render_context[self] = itertools_cycle(self.cycle_values)
        cycle_iter = context.render_context[self]

        try:
            conditional_variable_value = self.conditional_variable.resolve(context)
            if self.passes_condition(conditional_variable_value):
                value = next(cycle_iter).resolve(context)
                self.last_cycle_value = value
            else:
                if self.last_cycle_value is None:
                    self.last_cycle_value = next(cycle_iter).resolve(context)
                value = self.last_cycle_value
            return render_value_in_context(value, context)

        except template.VariableDoesNotExist:
            # fail silently...
            return


@register.tag
def conditional_cycle(parser, token):

    # a conditional cycle; only iterates when the 'if' clause is True or the 'nif' clause is False

    args = token.split_contents()

    if len(args) < 4:
        raise TemplateSyntaxError("invalid syntax for '{0}' tag".format(args[0]))
    if args[-2] not in ["if", "nif"]:
        raise TemplateSyntaxError("invalid syntax for '{0}' tag".format(args[0]))

    cycle_values = [parser.compile_filter(arg) for arg in args[1:-2]]
    conditional_operator = args[-2]
    conditional_variable_name = args[-1]
    node = ConditionalCycleNode(cycle_values, conditional_operator, conditional_variable_name)
    return node


# cycle through two variables iff some condition is met the first time...

class ConditionalSingletonNode(ConditionalNode):

    def __init__(self, conditional_outputs, conditional_operator, conditional_variable_name):
        super(ConditionalSingletonNode, self).__init__(conditional_operator, conditional_variable_name)
        self.conditional_outputs = conditional_outputs
        self.condition_met = False

    def render(self, context):
        if self not in context.render_context:
            context.render_context[self] = self.conditional_outputs
        conditional_outputs = context.render_context[self]

        try:
            conditional_variable_value = self.conditional_variable.resolve(context)
            if self.passes_condition(conditional_variable_value) and not self.condition_met:
                value = conditional_outputs[0].resolve(context)
                self.condition_met = True
            else:
                value = conditional_outputs[1].resolve(context)
            return render_value_in_context(value, context)

        except template.VariableDoesNotExist:
            # fail silently...
            return


@register.tag
def conditional_singleton(parser, token):

    # a conditional singleton; outputs one arg the first time the 'if' clause is True or the 'nif' clause is False and outputs another arg all other times

    args = token.split_contents()
    if len(args) != 5:
        raise TemplateSyntaxError("invalid syntax for '{0}' tag".format(args[0]))
    if args[-2] not in ["if", "nif"]:
        raise TemplateSyntaxError("invalid syntax for '{0}' tag".format(args[0]))

    conditional_outputs = [parser.compile_filter(arg) for arg in args[1:-2]]
    conditional_operator = args[-2]
    conditional_variable_name = args[-1]
    node = ConditionalSingletonNode(conditional_outputs, conditional_operator, conditional_variable_name)
    return node

#############################
# form / field manipulation #
#############################


@register.filter
def get_field_by_name(form, field_name):
    """
    gets a field from a form based on its name
    :param form:
    :param field_name:
    :return:
    """
    if field_name in form.fields:
        return form[field_name]
    return None


@register.filter
def get_fields_by_names(form, field_names):
    """
    gets a list of fields from a form based on their names
    :param form:
    :param field_names:
    :return:
    """
    fields = []
    for field_name in field_names.split(','):
        field = get_field_by_name(form, field_name)
        if field:
            fields.append(field)
    return fields


@register.filter
def get_form_by_field(formset, field_info):
    """
    gets a form from a formset based on a field_name/field_value pair
    :param formset:
    :param field_info:
    :return:
    """
    field_name, field_value = field_info.split('|')
    return formset.get_form_by_field(field_name, field_value)


@register.filter
def get_forms_by_field(formset, field_info):
    """
    gets a list of forms from a formset based on a field_name/field_value pair
    :param formset:
    :param field_info:
    :return:
    """
    field_name, field_value = field_info.split('|')
    return formset.get_forms_by_field(field_name, field_value)
