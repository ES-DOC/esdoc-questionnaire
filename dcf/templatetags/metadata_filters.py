from django import template

from dcf.models import *
from dcf.forms import *

register = template.Library()

#####################################
# gets rid of all spaces            #
# (shouldn't use spaces in HTML ids #
#####################################

import re

@register.filter
def stripSpaces(string):
    if string:
        return re.sub(r'\s+',"",string).strip()

#######################################
# returns the title of a MetdataModel #
#######################################

@register.filter
def getModelTitle(form):
    modelInstance = form.getModelInstance()
    if issubclass(type(modelInstance),ModelCustomizer):
        return modelInstance.getModelClass().getTitle()
    return modelInstance.getTitle()


##########################################################
# checks whether a field should be rendered as a subform #
##########################################################

@register.filter
def isInSubForms(field,form):
    subForms = form.getAllSubForms()    # this gets _all_ subforms, including those used by all ancestor forms
    if subForms.has_key(field.name):
        return True
    return False

##############################################################
# gets the actual subform associated with a particular field #
##############################################################

@register.filter
def getSubForm(form,field):
    subForms = form.getAllSubForms()            # note that I'm checking the full class hierarchy
    subFormDescription = subForms[field.name]   # subFormDescription[0] is the type, [1] is the class, [2] is the (current) instance
    return subFormDescription[2]

####################################
# gets the verbose name of a field #
####################################

@register.filter
def verbose_name(field,form):
    modelInstance = form.getModelInstance()
    modelField = modelInstance.getField(field.name)
    try:
        return modelField.verbose_name
    except AttributeError:
        return pretty_string(field.label) #(field.name)

############################################################
# given a list of forms (from a formset),                  #
# return that list sorted by the value of a specific field #
############################################################

@register.filter
def sort_forms_by_field(forms,fieldName):
    #    forms.sort(key = lambda x: x.cleaned_data[fieldName] if not x.cleaned_data else x.cleaned_data[fieldName])
    # sort the forms based on the value of the field from the form (cleaned_data)
    # if the form's data hasn't been set yet, then use the value of the field from the model (initial)
    try:
        forms.sort(key = lambda x: x.cleaned_data[fieldName])
    except AttributeError:
        forms.sort(key = lambda x: x.initial[fieldName])

    return forms

#ordering = ['order']    # not sure why this isn't working; wrote a custom templatetag to accomplish the same thing


#####
#
#####

@register.filter
def getFieldCategoryByName(fieldCategoryName):
    fieldCategory = FieldCategories.objects.filter(key=fieldCategoryName.replace(" ",""))
    print fieldCategory
#    I AM HERE
    return fieldCategory

###################################################################
# works out if the model behind this form has child models        #
# (and therefore needs to display the navigation tree / splitter) #
###################################################################

@register.filter
def isNested(form):
    #return False
    return True