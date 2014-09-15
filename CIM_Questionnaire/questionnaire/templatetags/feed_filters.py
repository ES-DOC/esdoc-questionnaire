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