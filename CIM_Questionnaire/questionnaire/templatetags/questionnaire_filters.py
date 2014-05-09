
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
.. module:: questionnaire_filters

Summary of module goes here

"""

from django import template
import os
import re

from django.contrib.sites.models import Site
from django.contrib.auth.models  import User

from questionnaire.utils  import *
from questionnaire.models import *
from questionnaire.forms  import *

register = template.Library()

@register.filter
def a_or_an(string):
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
def get_number_of_values(dict):
    number_of_values = 0
    for value in dict.values():
        number_of_values += len(value)
    return number_of_values

@register.filter
def get_value_from_key(dict,key):
    if dict and key in dict:
        return dict[key]
    return None

@register.filter
def index(sequence,index):
    try:
        return sequence[index]
    except IndexError:
        return ''

@register.filter
def get_number_of_properties_from_key(formsets,key):
    if formsets and key in formsets:
        return formsets[key].number_of_properties
    return 0

@register.filter
def site_type(site):
    if isinstance(site,Site):
        return site.metadata_site.get_type()
    else:
        return None

@register.filter
def is_member_of(user,project):
    if isinstance(user,User):
        if user.is_superuser:
            # admin is a member of _all_ projects
            return True
        return user.metadata_user.is_member_of(project)
    return False

@register.filter
def is_user_of(user, project):
    if isinstance(user,User):
        if user.is_superuser:
            # admin has _all_ permisions
            return True
        return  user.metadata_user.is_user_of(project)
    return False

@register.filter
def is_admin_of(user, project):
    if isinstance(user,User):
        if user.is_superuser:
            # admin has _all_ permisions
            return True
        return  user.metadata_user.is_admin_of(project)
    return False


###@register.filter
###def get_property_type(form):
###
###    try:
###        property = form.instance
###        return property.field_type
###    except AttributeError:
###        msg = "form instance has no field_type attribute; is it a property form?"
###        print msg
###        return None

@register.filter
def get_field_by_name(form,field_name):
    return form[field_name]

@register.filter
def get_instance_pk(form):
    instance = form.instance
    if instance:
        return instance.pk
    return -1

@register.filter
def analyze(formsets):
#    print "these formsets are contained in a %s" % (type(formsets))
#    print "there are %s items: %s" % (len(formsets),formsets.keys())
#    print "and each item has the following statistics:"
#    for (key,formset) in formsets.iteritems():
#        print "%s has a %s with %s properties" % (key,type(formset),formset.number_of_properties)
#        print "and they are..."
#        for form in formset:
#            print form.current_values["name"]
#            try:
#                print u"%s: %s" %(form.prefix,form.data[form.prefix+"-name"])
#            except:
#                print u"no data for %s" % (form.prefix)        
    return "analyzed"

@register.filter
def get_form_by_field(formset,field_tuple):
    # returns the 1st form in a fieldset whose specified field has the specified value
    (field_name,field_value) = field_tuple.split('|')
#    print ""
#    print 'looking for %s=%s (in %s)' % (field_name,field_value,formset.prefix)
    for (i,form) in enumerate(formset):
#        print "%s: has %s" % (i,form.current_values)
#        print form.get_field_value_by_name(field_name)
        if form.get_field_value_by_name(field_name) == field_value:
            return form
    return None

####def get_field_value_by_name(self,field_name):
####        try:
####            return self.current_values[field_name]
####        except KeyError:
####            msg = "Unable to locate field '%s' in form." % (field_name)
####            raise QuestionnaireError(msg)


@register.filter
def get_forms_by_field(formset,field_tuple):
    # returns all forms in a fieldset whose specified field has the specified value
    (field_name,field_value) = field_tuple.split('|')
    forms = []
    for form in formset:
        if form.get_field_value_by_name(field_name) == field_value:
            forms.append(form)
    return forms

@register.filter
def get_active_scientific_categories_by_key(model_customizer,key):
    return model_customizer.get_active_scientific_categories_by_key(key)

@register.filter
def get_active_scientific_properties_by_key(model_customizer,key):
    return model_customizer.get_active_scientific_properties_by_key(key)

@register.filter
def get_active_scientific_categories_and_properties_by_key(model_customizer,key):
    return model_customizer.get_active_scientific_categories_and_properties_by_key(key)

@register.assignment_tag
def get_default_vocabulary_key():
    return slugify(DEFAULT_VOCABULARY)

