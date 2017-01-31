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
.. module:: q_tags_publications

defines custom template tags for use in publishing documents
"""

from django import template
from django.utils.safestring import mark_safe
from lxml import etree as et

from Q.questionnaire.models.models_publications import QPublicationFormats
from Q.questionnaire.q_fields import QPropertyTypes
from Q.questionnaire.q_constants import *
from Q.questionnaire.q_utils import convert_to_camelCase

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


PLURAL_MAP = {
    'cactus': 'cacti',
    'octopus': 'octopi',
    'child': 'children',
}
VOWELS = set('aeiou')


@register.filter
def plural(word):
    """
    returns the plural form of a word
    :param word:
    :return:
    """
    # TODO: IS THERE A NON-HARD-CODED WAY TO DO THIS?
    # TODO: DOES PYESDOC INCLUDE THIS INFORMATION DURING PARSING?
    if not word:
        return u""

    plural = PLURAL_MAP.get(word)
    if plural:
        return plural

    root = word
    try:
        if word[-1] == 'y' and word[-2] not in VOWELS:
            root = word[:-1]
            suffix = 'ies'
        elif word[-1] == 's':
            if word[-2] in VOWELS:
                if word[-3:] == 'ius':
                    root = word[:-2]
                    suffix = 'i'
                else:
                    root = word[:-1]
                    suffix = 'ses'
            else:
                suffix = 'es'
        elif word[-2:] in ('ch', 'sh'):
            suffix = 'es'
        else:
            suffix = 's'
    except IndexError:
        suffix = 's'

    plural = root + suffix
    return plural


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


@register.filter
def format_name_for_publication(name, publication_format):
    """

    :param string:
    :param publication_format:
    :return:
    """
    assert publication_format == QPublicationFormats.CIM2_XML, "invalid publication_format in 'q_tags_publications.py#get_property_publication_value`"

    # turns spaces and underscores into camelCase
    return convert_to_camelCase(name)


@register.filter
def get_value_for_publication(property_realization, publication_format):
    """
    returns a property value for a property, property formatted
    :param property_realization: the property to publish
    :param publication_format: the format to be published (XML, JSON, etc.)
    :return:
    """
    assert publication_format == QPublicationFormats.CIM2_XML, "invalid publication_format in 'q_tags_publications.py#get_property_publication_value`"

    property_node = et.Element(convert_to_camelCase(property_realization.proxy.name))

    field_type = property_realization.field_type
    if field_type == QPropertyTypes.ATOMIC:
        if property_realization.is_nil:
            property_node.text = "{0}:{1}".format(NIL_PREFIX, property_realization.nil_reason.lower())
        else:
            if property_realization.value is not None:
                property_node.text = str(property_realization.value)
    elif field_type == QPropertyTypes.ENUMERATION:
        if property_realization.is_nil:
            property_node.text = "{0}:{1}".format(NIL_PREFIX, property_realization.nil_reason.lower())
        else:
            for property_value in property_realization.value:
                property_value_node = et.Element("value")
                property_value_node.text = property_value
                property_node.append(property_value_node)
    else:  # field_type == QPropertyTypes.RELATIONSHIP
        raise NotImplementedError

    property_node_for_publication = et.tostring(property_node, method='xml')
    return mark_safe(property_node_for_publication)
