from django import template

from django_cim_forms.models import *
from django_cim_forms.forms import *
from django_cim_forms.helpers import *

register = template.Library()

######################################
# custom filters to use in templates #
######################################


####################################
# returns a pretty name for a form #
####################################

@register.filter
def getModelTitle(form):
    # get the title of the model
    # (the name is the name of of the instance, while the title is a pretty name that can be used in the form)
    model = form.Meta.model
    return model._title

###########################################################
# returns the field types being used by a particular form #
###########################################################

@register.filter
def getActiveFieldTypes(form):
    model = form.Meta.model
    fieldTypes = list(model._fieldTypes)
    return [fieldType for fieldType in fieldTypes if (fieldType.getType() in model._fieldsByType)]

##########################################################
# returns all field types available to a particular form #
##########################################################

@register.filter
def getAllFieldTypes(form):
    model = form.Meta.model
    return model._fieldTypes

################################################################
# return all fields of a form assigned to a specific fieldType #
################################################################

@register.filter
def getFieldsOfType(form,fieldType):
    model = form.Meta.model
    return model._fieldsByType[fieldType.getType()]

##########################################################
# checks whether a field should be rendered as a subform #
##########################################################

@register.filter
def isInSubForms(form,field):
    subForms = form.getAllSubForms()    # this gets all subforms used by all ancestor models as well
#    subForms = form.getSubForms()       # this only gets subforms used by the current model
    if subForms.has_key(field.name):
        return True
    return False


##############################################################
# gets the actual subform associated with a particular field #
##############################################################

@register.filter
def getSubForm(field,form):
    subForms = form.getAllSubForms() # not that I'm checking the full class hierarchy of the model associated w/ form
    subField = subForms[field.name]
    return subField[2]

#############################################
# gets the subform type of a given subform  #
#############################################

@register.filter
def getSubFormType(subForm):
    return subForm.getSubFormType().getType()

##############################################
# work out the app and model of a given form #
##############################################

@register.filter
def getAppName(form):
    # get the application_label of the model
    model = form.Meta.model
    return model._meta.app_label.lower()

@register.filter
def getModelName(form):
    # get the name of hte model
    model = form.Meta.model
    return model._name.lower()
