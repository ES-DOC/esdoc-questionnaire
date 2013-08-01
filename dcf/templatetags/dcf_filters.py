
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
.. module:: dcf_filters

Summary of module goes here

"""

from django import template
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
def camelCase(string):
    """
    turns a set of words into a camelCase string
    """
    camel_case_string = ""
    for i, word in enumerate(string.split(" ")):
        if i==0:
            camel_case_string += word[0].lower() + word[1:]
        else:
            camel_case_string += word[0].upper() + word[1:]
    return camel_case_string

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
def getValueFromKey(dict,key):
    if key in dict:
        return dict[key]
    return None


@register.filter
def getAllValues(dict):
    values = getElementsInCollection(dict)
    try:
        # on the assumption that this is a list of MetadataCustomizers,
        # try to sort and trim the list
        values.sort(key = lambda x: x.order)
        return [value for value in value if values.displayed]
    except:
        return values


def getElementsInCollectionAux(collection,elements=[]):
   if isinstance(collection,dict):
     for value in collection.itervalues():
       getElementsInCollectionAux(value,elements)
   elif isinstance(collection,list):
     for value in collection:
       getElementsInCollectionAux(value,elements)
   else:
       return elements.append(collection)

@register.filter
def getElementsInCollection(collection):
    elements = []
    getElementsInCollectionAux(collection,elements)
    return [e for e in elements if e]

@register.filter
def getFilename(filepath):
    """
    given a url or path, returns the filename
    """
    return os.path.basename(filepath)


@register.filter
def getFieldValue(form,field_name):
    """
    returns the actual value of the field
    rather than the formfield widget
    (has a clever little check to see if it's a relationship field
    """
    try:
        field = form[field_name]

        if type(field.field) == MetadataEnumerationFormField:
        
            value = field.value()
            if value:
                if isinstance(value,list):
                    multi = False
                    value_list = value
                    if isinstance(value[0],list):
                        multi = True
                        value_list = value
                elif "||" in value:
                    multi = True
                    value_list = [v.split("|") for v in value.split("||")]
                    value_list = [value_list[0],value_list[1][0]]
                elif "|" in value:
                    multi = False
                    value_list = value.split("|")

                if multi:
                    for i,v in enumerate(value_list[0]):
                        if v == OPEN_CHOICE[0][0]:
                            value_list[0][i] = "OTHER: %s" % value_list[1]
                    num_enumerations = len(value_list[0])
                    if num_enumerations > 0:
                        if num_enumerations > 1:
                            return "%s + %s more selections" % (value_list[0][0], (num_enumerations - 1))
                        else:
                            return value_list[0][0]
                    else:
                        return None
                else:
                    if value_list[0] == OPEN_CHOICE[0][0]:
                        return "OTHER: %s" % value_list[1]
                    else:
                        return value_list[0]                    
            else:
                return None
            
        elif type(field.field) == ModelChoiceField: # TODO: WHAT ABOUT MultipleChoiceField OR ModelMultipleChoiceField
            EMPTY_CHOICE = "---------"
            for (value,text) in field.field.choices:
                if unicode(value) == unicode(field.value()):
                    return text if (text != EMPTY_CHOICE) else None
        else:
            value = field.value()
            return value if value else None

    except KeyError:
        return None

#<span class="label" name="property_value">{{form|getFieldValue:form.property_value_field.name}}</span>


@register.filter
def getField(form,field_name):
    return form[field_name]


@register.filter
def getMetadataField(form,field_name):
    """
    returns the actual MetadataField instance (not the db/form representation of it)
    """
    return form.get_metadata_field(field_name)

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
def getSubFormByName(form,field_name):
    """
    returns the subform associated w/ a field, if any
    """
    subForms        = form.getAllSubForms()  # note that I'm checking the full class hierarchy
    subFormData     = subForms[field_name]   # subFormData[0] is the type, [1] is the class, [2] is the (current) instance
    return subFormData[2]


####
### UNCHECKED BELOW HERE
###

@register.filter
def getFormsByComponentName(formset,component_name):
    forms = []
    for form in formset:
        if form["component_name"].value() == component_name:
            forms.append(form)
    return sortFormsByField(forms,"order")


@register.filter
def getStandardPropertyCustomizers(form):
    #print form.customizer
    #print form.customizer.getStandardPropertyCustomizers()
    return None

@register.filter
def getNamedPropertyFormSet(form,component_name):
    #print form._propertyForms
    return form._propertyForms[component_name.lower()]

@register.filter
def hasCategory(form,category):
    print "checking if it has category %s" % category
    model = form.instance
    print "checking if %s has category %s" % (model,category)
    print "it's category is %s" % model.category
    return model.category == category
