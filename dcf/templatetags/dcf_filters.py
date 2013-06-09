
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
__date__ ="Jan 31, 2013 12:45:47 PM"

"""
.. module:: views_index

Summary of module goes here

"""

from django import template
from twisted.python.htmlizer import filter
import os
import re

from dcf.fields import *
from dcf.models import *
from dcf.forms  import *

register = template.Library()


@register.filter
def stripSpaces(string):
    """
    filter to remove whitespace from string
    """
    if string:
        return re.sub(r'\s+',"",string).strip()

@register.filter
def aOrAn(string):
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
def getFilename(filepath):
    """
    given a url or path, returns the filename
    """
    return os.path.basename(filepath)

@register.filter
def getSubForm(form,field):
    """
    returns the subform associated w/ a field, if any
    """
    subForms            = form.getAllSubForms()  # note that I'm checking the full class hierarchy
    subFormDescription  = subForms[field.name]   # subFormDescription[0] is the type, [1] is the class, [2] is the (current) instance
    return subFormDescription[2]

@register.filter
def getNamedSubForm(form,subformName):
    """
    returns a specific subform
    (used by customizer form when I have some subforms w/ a constant name
    """
    subForms            = form.getAllSubForms()
    subFormDescription  = subForms[subformName]
    return subFormDescription[2]

@register.filter
def sortFormsByField(forms,fieldName):
    """
    returns the set of forms sorted by a particular field
    the try/catch ValueError statement deals w/ the case where I am sorting based on numbers
    (otherwise "1, 10, 2" would be returned instead of "1, 2, 10")
    the if/else in the lambda fn deals w/ the case where the form may or may not have passed validation
    (if it did, it will have "cleaned_data" if not it will just have "data")
    """
    try:
        # use the value of the field from the form (cleaned_data/data - depending on whether the form was valid or not)
        forms.sort(key = lambda x: float(x.cleaned_data[fieldName]) if hasattr(x,"cleaned_data") else float(x.data[x.prefix+"-"+fieldName]))
    except ValueError:
        forms.sort(key = lambda x: x.cleaned_data[fieldName] if hasattr(x,"cleaned_data") else x.data[x.prefix+"-"+fieldName])
    except (AttributeError, KeyError):
        # if the form's data hasn't been set yet, then use the value of the field from the model (initial)
        forms.sort(key = lambda x: x.initial[fieldName])

    return forms


@register.filter
def getAttributeCategories(form):
    customizer = form.getCustomizer()
    if customizer.model_show_all_categories:
        attribute_categories = [attribute.category for attribute in customizer.attributes.all() if attribute.category]
        attribute_categories = list(set(attribute_categories))  # remove duplicates
        attribute_categories.sort(key = lambda x: x.order)      # although categories are naturally sorted by "order",
        return attribute_categories                             # getting them in the list comprehension above ignores that
    else:
        return getActiveAttributeCategories(form)

@register.filter
def getActiveAttributeCategories(form):
    customizer = form.getCustomizer()
    active_attribute_categories = [attribute.category for attribute in customizer.attributes.all() if attribute.category and attribute.displayed]
    active_attribute_categories = list(set(active_attribute_categories))    # remove duplicates
    active_attribute_categories.sort(key = lambda x: x.order)               # although categories are naturally sorted by "order",
    return active_attribute_categories                                      # getting them in the list comprehension above ignores that

@register.filter
def getActiveAttributesOfCategory(form,category):
    customizer = form.getCustomizer()
    active_attributes = [attribute for attribute in customizer.attributes.all() if (attribute.category == category)]
    active_attributes.sort(key = lambda x: x.order)
    return active_attributes

@register.filter
def getActiveAttributesOfNoCategory(form):
    customizer = form.getCustomizer()
    active_attributes = [attribute for attribute in customizer.attributes.all() if not attribute.category]
    active_attributes.sort(key = lambda x: x.order)
    return active_attributes

@register.filter
def getAllActiveAttributes(form):
    customizer = form.getCustomizer()
    active_attributes = [attribute for attribute in customizer.attributes.all()]
    active_attributes.sort(key = lambda x: x.order)
    return active_attributes

@register.filter
def getFieldFromName(form,fieldName):
    """
    returns the actual MetadataField instance (not the db/form representation of it)
    """
    return form.instance.getField(fieldName)

@register.filter
def getFormFieldFromName(form,fieldName):
    """
    okay, this one returns the form representation
    """
    return form[fieldName]

@register.filter
def getAttributeFromCustomizer(form,customizer):
    """
    returns the form field (the one that can be rendered by the form)
    """
    return form.__getitem__(customizer.attribute_name)


@register.filter
def getComponentList(form):
    component_tree = getComponentTree(form)
    component_list = []
    component_list_generator = list_from_tree(component_tree)
    for component in component_list_generator:
        component_list += component
    return component_list


@register.filter
def getComponentTree(form):
    if type(form) == MetadataModelCustomizerForm:
        customizer = form.instance
    else:
        customizer = form.getCustomizer()
    component_hierarchy = customizer.getVocabulary().component_hierarchy
    return json.loads(component_hierarchy)