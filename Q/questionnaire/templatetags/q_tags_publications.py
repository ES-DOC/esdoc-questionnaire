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
.. module:: q_tags_publications

defines template tags to use w/ XML serializations of realizations
"""

from django import template
from Q.questionnaire.q_constants import *

register = template.Library()


@register.simple_tag
def publication_source():
    return PUBLICATION_SOURCE


@register.filter
def publication_institute(model):
    institute = model.owner.profile.institute
    if institute:
        return institute.name
    return None


@register.filter
def get_ontology_type_key(model_proxy):
    ontology = model_proxy.ontology
    ontology_type_key = "{0}.{1}.{2}.{3}".format(
        ontology.name.lower(),
        ontology.get_version_major(),
        model_proxy.package.lower(),
        model_proxy.name.title(),
    )
    return ontology_type_key