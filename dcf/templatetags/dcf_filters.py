
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
import os
import re

register = template.Library()


@register.filter
def stripSpaces(string):
    """
    filter to remove whitespace from string
    """
    if string:
        return re.sub(r'\s+',"",string).strip()
    
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
def sortFormsByField(forms,fieldName):
    """
    returns the set of forms sorted by a particular field
    """
    try:
        # use the value of the field from the form (cleaned_data)
        forms.sort(key = lambda x: x.cleaned_data[fieldName])
    except AttributeError:
        # if the form's data hasn't been set yet, then use the value of the field from the model (initial)
        forms.sort(key = lambda x: x.initial[fieldName])
    return forms
