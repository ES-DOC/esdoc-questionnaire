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
.. module:: feed_filters

Summary of module goes here

"""

import os
from django import template

from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel, MetadataStandardProperty, MetadataScientificProperty

register = template.Library()

@register.filter
def get_standard_property_by_name(model, property_name):
    property_name_lower = property_name.lower()
    standard_properties = model.standard_properties.all()
    for standard_property in standard_properties:
        if standard_property.name.lower() == property_name_lower:
            return standard_property
    return None


@register.filter
def get_scientific_property_by_name(model, property_name):
    property_name_lower = property_name.lower()
    scientific_properties = model.scientific_properties.all()
    for scientific_property in scientific_properties:
        if scientific_property.name.lower() == property_name_lower:
            return scientific_property
    return None


@register.filter
def get_standard_properties_with_stereotypes(model, stereotype_names):
    stereotype_names_list = stereotype_names.split(',')
    standard_properties = model.standard_properties.filter(proxy__stereotype__in=stereotype_names_list)
    return standard_properties


@register.filter
def get_standard_properties_without_stereotypes(model, stereotype_names):
    stereotype_names_list = stereotype_names.split(',')
    standard_properties = model.standard_properties.exclude(proxy__stereotype__in=stereotype_names_list)
    return standard_properties

@register.filter
def get_url_path(url):
    return os.path.split(url)[0]


@register.filter
def get_vocabulary_from_property(scientific_property):
    try:
        return scientific_property.proxy.component.vocabulary
    except:
        return None


@register.filter
def get_fully_qualified_tagname(property):
    """
    concatenates a namespace onto the property name
    :param property:
    :return:
    """
    if property.proxy.namespace:
        return u"%s:%s" % (property.proxy.namespace, property.name)
    else:
        return u"%s" % (property.name)