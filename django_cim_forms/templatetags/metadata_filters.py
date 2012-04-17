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
    fieldTypes = model._fieldTypes
    if model._fieldTypeOrder:
        fieldTypes.sort(key=lambda fieldType: EnumeratedTypeList.comparator(fieldType,model._fieldTypeOrder))
    return [fieldType for fieldType in fieldTypes if (fieldType.getType() in model._fieldsByType)]

##########################################################
# returns all field types available to a particular form #
##########################################################

@register.filter
def getAllFieldTypes(form):
    model = form.Meta.model
    if model._fieldTypeOrder:
        return model._fieldTypes.sort(key=lambda fieldType: EnumeratedTypeList.comparator(fieldType,model._fieldTypeOrder))
    return model._fieldTypes

################################################################
# return all fields of a form assigned to a specific fieldType #
################################################################

@register.filter
def getFieldsOfType(form,fieldType):
    model = form.Meta.model
    return model._fieldsByType[fieldType.getType()]

#############################################################################
# return whether or not this field is _really_ required                     #
# (some Metadata Relationship Fields always have blank=True set internally) #
#############################################################################

@register.filter
def required(form,field):
    #return field.isRequired
    model = form.Meta.model
    modelField = model._meta.get_field_by_name(field.name)[0]    
    try:
        return modelField.isRequired()
    except AttributeError:
        return None

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
