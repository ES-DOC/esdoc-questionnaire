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
.. module:: q_tags_ng

defines template tags to use w/ ng
"""

from django import template
# from django.template.base import Context
# from django.template.defaulttags import VerbatimNode

register = template.Library()


# TODO: THIS TAG DOES NOT WORK PROPERLY
# TODO: SO I AM USING {% verbatim ng %} INSTEAD
# TODO: LOOK INTO OTHER METHODS SUCH AS RE-DEFINING THE DEFAULT ng TAG SYNTAX
# TODO: DELETE THIS FILE AS NEEDED
# @register.tag
# def ngcode(parser, token):
#     """
#     Functions exactly like the {% verbatim %} tag
#     but renamed to make it clear that the purpose of this tag is to isolate ng code
#     Usage::
#         {% ngcode %}
#             <don't process this w/ Django; process it w/ Angular>
#         {% endngcode %}
#     """
#     nodelist = parser.parse(('endngcode',))
#     parser.delete_first_token()
#     return VerbatimNode(nodelist.render(Context()))
