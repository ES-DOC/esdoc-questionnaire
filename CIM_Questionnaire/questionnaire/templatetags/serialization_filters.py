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

from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataStandardProperty, MetadataScientificProperty
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy, MetadataScientificCategoryProxy, MetadataScientificPropertyProxy, MetadataStandardCategoryProxy, MetadataStandardPropertyProxy

register = template.Library()

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
def get_institute_code(model):
    """
    this is a one-off for pyesdoc serializations which require this
    :param model: the model whose institute code is being requested
    :return: the responsibleParty -> organisationName if available (otherwise None)
    """
    document_author_property = get_standard_property_by_name(model, "documentAuthor")
    if document_author_property:
        document_authors = document_author_property.relationship_value.all()
        if len(document_authors) != 0:
            institute = get_standard_property_by_name(document_authors[0], "organisationName")
            return institute.atomic_value
        else:
            return None
    else:
        parent_property_set = model.metadatastandardproperty_set.all()
        if parent_property_set:
            parent_model = parent_property_set[0].model
            return get_institute_code(parent_model)
        else:
            return None
    # try:
    #     document_author = get_standard_property_by_name(model, "documentAuthor").relationship_value.all()[0]
    #     institute = get_standard_property_by_name(document_author, "organisationName")
    #     return institute.atomic_value
    # except AttributeError:
    #     return None

@register.filter
def get_standard_property_by_name(model, property_name):
    """
    returns the standard_property w/ a matching property_name,
    if no matches are found, returns None
    :param model: model to check
    :param property_name: name to check (case-insensitive)
    :return:
    """
    try:
        standard_property = model.standard_properties.get(name__iexact=property_name)
        return standard_property
    except MetadataStandardProperty.DoesNotExist:
        return None


@register.filter
def get_scientific_property_by_name(model, property_name):
    """
    returns the scientific_property w/ a matching property_name,
    if no matches are found, returns None
    :param model: model to check
    :param property_name: name to check (case-insensitive)
    :return:
    """
    try:
        scientific_property = model.scientific_properties.get(name__iexact=property_name)
        return scientific_property
    except MetadataScientificProperty.DoesNotExist:
        return None


@register.filter
def get_scientific_categories_and_properties_dictionary(scientific_properties):
    scientific_categories_and_properties_dictionary = {}
    for scientific_property in scientific_properties:
        scientific_category_proxy = MetadataScientificCategoryProxy.objects.get(key=scientific_property.category_key, component=scientific_property.proxy.component)
        if scientific_category_proxy not in scientific_categories_and_properties_dictionary:
            scientific_categories_and_properties_dictionary[scientific_category_proxy] = []
        scientific_categories_and_properties_dictionary[scientific_category_proxy].append(scientific_property)
    return scientific_categories_and_properties_dictionary

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

@register.filter
def get_ontology_type_key(model):
    """
    returns the ES-DOC type for this proxy
    :param property:
    :return:
    """
    proxy = model.proxy
    ontology_type_key = "cim.1.%s.%s" % (proxy.package, proxy.name[0].upper()+proxy.name[1:])
    return ontology_type_key

PLURAL_MAP = {
    'cactus' : 'cacti',
}
VOWELS = set('aeiou')

@register.filter
def get_plural(word):

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

