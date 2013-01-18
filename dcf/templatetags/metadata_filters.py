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

#I AM HERE
#USE THESE IN EDIT LIKE CUSTOM!

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

#####################################################
# checks if the field's widget has a specific class #
#####################################################


@register.filter
def hasClass(field,className):
    attrs = field.field.widget.attrs
    try:
        classes = attrs["class"]
        for cls in classes.split(" "):
            if cls==className:
                return True
    except KeyError:
        pass
    return False

#####################################################################
# determines if the model behind this form already exists in the db #
#####################################################################

@register.filter
def isSaved(form):
    modelInstance = form.getModelInstance()
    return modelInstance.pk != None

##########
#
##########

@register.filter
def get_active_field_categories(form):
    modelInstance = form.getModelInstance()
    return modelInstance.getActiveFieldCategories()

######
#
#

@register.filter
def get_fields_of_category(form,category):
    modelInstance = form.getModelInstance()
    allFields = modelInstance.getAllFields()
    return [field.name for field in allFields if field.get_custom_category()==category]

@register.filter
def get_uncategorized_fields(form):
    modelInstance = form.getModelInstance()
    allFields = modelInstance.getAllFields()
    return [field.name for field in allFields if field.get_custom_category()==None]


############################################
# returns a pretty title for the subform   #
# (used in accordion headers for formsets) #
############################################

@register.filter
def get_subform_title(subform):
    modelInstance = subform.instance
    if modelInstance.pk != None:
        # if the underlying model already has values
        # then just use the unicode method to get a pretty title
        return u'%s' % modelInstance
    else:
        # otherwise do something else
        return u'[New %s]' % modelInstance.getTitle()


###################################################################################
# these next several filters replace the standard attribute fns for fields;       #
# they check to see if that attribute has been customized and return that instead #
###################################################################################

@register.filter
def custom_visible_fields(form):
    modelInstance = form.getModelInstance()
    currentVisibleFields = [visible_field for visible_field in form.visible_fields() if modelInstance.getField(visible_field.name).is_custom_visible()]
    currentVisibleFields.sort(key = lambda x: modelInstance.getField(x.name).custom_order)
    return currentVisibleFields

@register.filter
def custom_help_text(field,form):
    modelInstance = form.getModelInstance()
    modelField = modelInstance.getField(field.name)
    return modelField.get_custom_help_text()

@register.filter
def custom_verbose_name(field,form):
    modelInstance = form.getModelInstance()
    modelField = modelInstance.getField(field.name)
    return modelField.get_custom_verbose_name()

@register.filter
def custom_required(field,form):
    modelInstance = form.getModelInstance()
    modelField = modelInstance.getField(field.name)
    return modelField.get_custom_required()

@register.filter
def custom_subform(field,form):
    modelInstance = form.getModelInstance()
    modelField = modelInstance.getField(field.name)
    return modelField.is_custom_subform()

###############################################################
# returns the subform from the dictionary stored in the model #
###############################################################

@register.filter
def get_subform(field,form):
    subFormDescription = form._subForms[field.name]   # subFormDescription[0] is the type, [1] is the class, [2] is the (current) instance
    try:
        return subFormDescription[2]
    except:
        return None


######
#
######

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
