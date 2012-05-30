from django import template

from django_cim_forms.models import *
from django_cim_forms.forms import *

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

#######################################################
# returns the app name of the model bound to a form #
#######################################################

@register.filter
def getAppName(form):
    # get the name of the model
    modelClass = form.getModelClass()
    return modelClass._meta.app_label.lower()

#######################################################
# returns the class name of the model bound to a form #
#######################################################

@register.filter
def getModelName(form):
    # get the name of the model
    modelClass = form.getModelClass()
    return modelClass.getName()

####################################
# returns a pretty name for a form #
####################################

@register.filter
def getModelTitle(form):
    # get the title of the model
    modelClass = form.getModelClass()
    return modelClass.getTitle()

###############################################
# returns the id of the model bound to a form #
###############################################

@register.filter
def getModelGuid(form):
    modelInstance = form.getModelInstance()
    return modelInstance.guid

###########################################################
# returns the field types being used by a particular form #
# (this takes into account the model's specified order)   #
###########################################################

@register.filter
def getActiveFieldTypes(form):
    modelInstance = form.getModelInstance()
    fieldTypes = modelInstance._fieldTypes.keys()
    if modelInstance._fieldTypeOrder:
        fieldTypes = [fieldType for fieldType in fieldTypes if (fieldType.getType() in modelInstance._fieldTypeOrder)]
        fieldTypes.sort(key=lambda fieldType: EnumeratedTypeList.comparator(fieldType,modelInstance._fieldTypeOrder))
    if modelInstance._fieldOrder:
        # only inlcude fieldTypes whose fields are specified in _fieldOrder
        fieldTypes = [fieldType for fieldType in fieldTypes if ([field for field in modelInstance._fieldTypes[fieldType] if field in modelInstance._fieldOrder])]
    return fieldTypes

###########################################################
# returns all registered field types of a particular form #
# (this takes into account the model's specified order)   #
###########################################################

@register.filter
def getAllFieldTypes(form):
    modelInstance = form.getModelInstance()
    fieldTypes = modelInstance._fieldTypes.keys()
    if modelInstance._fieldTypeOrder:
        fieldTypes = [fieldType for fieldType in fieldTypes if (fieldType.getType() in modelInstance._fieldTypeOrder)]
        fieldTypes.sort(key=lambda fieldType: EnumeratedTypeList.comparator(fieldType,modelInstance._fieldTypeOrder))

    return fieldTypes

##########################################################################
# returns the fields of a form belonging to a particular type            #
# (this takes into account the model's specified order)                  #
# (however, in practise, the fields are ordered in the form.__init__ fn) #
##########################################################################

@register.filter
def getFieldsOfType(form,fieldType):
    modelInstance = form.getModelInstance()
    fields = modelInstance._fieldTypes[fieldType]
    if modelInstance._fieldOrder:
        fields = [field for field in fields if field in modelInstance._fieldOrder]
        fields.sort(key=lambda fieldName: MetadataField.comparator(fieldName,modelInstance._fieldOrder))
        
    return fields

#############################################################
# returns all registered field types of a PropertyForm.     #
# w/ PropertyForms, field types are associated w/ the form, #
# not the model.                                            #
#############################################################

@register.filter
def getAllPropertyFieldTypes(form):
    fieldTypes = form._fieldTypes.keys()
    print fieldTypes
    if form._fieldTypeOrder:
        fieldTypes = [fieldType for fieldType in fieldTypes if (fieldType.getType() in form._fieldTypeOrder)]
        fieldTypes.sort(key=lambda fieldType: EnumeratedTypeList.comparator(fieldType,form._fieldTypeOrder))

    return fieldTypes

############################################
# another filter specific to PropertyForms #
# distinguishes between parents & children #
############################################

@register.filter
def hasSubItems(form):
    modelInstance = form.getModelInstance()
    return modelInstance.hasSubItems()

@register.filter
def hasValues(form):
    modelInstance = form.getModelInstance()
    return modelInstance.hasValues()

@register.filter
def haveSubItems(forms):
    for form in forms:
        modelInstance = form.getModelInstance()
        if modelInstance.hasSubItems():
            return True
    return False

@register.filter
def haveValues(forms):
    for form in forms:
        modelInstance = form.getModelInstance()
        if modelInstance.hasValues():
            return True
    return False

@register.filter
def isChildOf(childForm,parentForm):
    parentInstance = parentForm.getModelInstance()
    childInstance = childForm.getModelInstance()
    return childInstance.parentShortName == parentInstance.shortName

@register.filter
def nestProperties(formset):
    properties = [form.getModelInstance() for form in formset.forms]
    #return formset.nestPropertyForms(properties)
    return formset.nestPropertyForms({},None,properties)

@register.filter
def getForm(formset,shortName):
    for form in formset.forms:
        modelInstance = form.getModelInstance()
        if (modelInstance.shortName == shortName):
            return form

@register.filter
def getForms(formset,shortNames):
    forms = []
    for form in formset.forms:
        modelInstance = form.getModelInstance()
        if (modelInstance.shortName in shortNames):
            forms.append(form)
    return forms

@register.filter
def get_item(dict, key):
    # gets value from dict based on key
    # (just got too confusing to do this in the template)
    return dict.get(key)

###################################################################
# gets the value of a modelField (as opposed to a formField)      #
# useful for Property_forms (which have formFields added on init) #
###################################################################

@register.filter
def getModelFieldValue(form,fieldName):
    modelInstance = form.getModelInstance()
    #modelField = modelInstance.getField(fieldName)
    # TODO: does this work w/ lists?
    modelFieldValue = getattr(modelInstance,fieldName)
    return modelFieldValue

####################################
# gets the verbose name of a field #
####################################

@register.filter
def verbose_name(field,form):
    modelInstance = form.getModelInstance()
    modelField = modelInstance.getField(field.name)
    try:
        return modelField.getVerboseName()
    except AttributeError:
        return pretty_string(field.name)

#############################################################
# returns whether or not a field is required                #
# (some relationship fields have blank=True set internally; #
# this code ignores that                                    #
#############################################################

@register.filter
def required(field,form):
    modelInstance = form.getModelInstance()
    modelField = modelInstance.getField(field.name)
    try:
        return modelField.isRequired()
    except AttributeError:
        return False

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
    subForms = form.getAllSubForms() # note that I'm checking the full class hierarchy
    subFormDescription = subForms[field.name]   # subFormDescription[0] is the type, [1] is the class, [2] is the (current) instance
    return subFormDescription[2]

@register.filter
def test(form,field):
    subForms = form.getAllSubForms()
    subFormDescription = subForms[field.name]
    msg = "%s subform = %s" % (field,subFormDescription[2])
    return msg
#
#
#

@register.filter
def canAddRemote(field,form):
    modelInstance = form.getModelInstance()
    modelField = modelInstance.getField(field.name)
    return modelField.canAddRemote()

####################################################################################
# returns whether the form is based on a subclass of MetadataProperty              #
# these types of forms should be rendered slightly differently than standard forms #
####################################################################################

@register.filter
def isPropertyForm(form):
    return form.isPropertyForm()
