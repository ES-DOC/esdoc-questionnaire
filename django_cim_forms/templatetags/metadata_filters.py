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
    fieldTypes = list(model.FieldTypes)
    return [fieldType for fieldType in fieldTypes if (fieldType.getType() in model._fieldsByType)]

##########################################################
# returns all field types available to a particular form #
##########################################################

@register.filter
def getAllFieldTypes(form):
    model = form.Meta.model
    return model.FieldTypes

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
    if form._subForms.has_key(field.name):
        return True
    return False

