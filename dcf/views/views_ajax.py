
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
__date__ ="Feb 1, 2013 5:04:50 PM"

"""
.. module:: views_ajax

Summary of module goes here

"""

from django.template import *
from django.shortcuts import *
from django.http import *

from django.utils import simplejson as json

import re

from dcf.models import *
from dcf.forms import *

def get_category(request, category_type=""):
    category_key    = request.GET.get('k',None)
    category_name   = request.GET.get('n',None)
    version_name    = request.GET.get('v',None)
    project_name    = request.GET.get('p',None)
    model_name      = request.GET.get('m',None)

    create_if_none  = request.GET.get('c',True) # unless otherwise specified, create the category if it's not in the db already

    if not (category_type and category_key and category_name and version_name and project_name and model_name):
        msg = "invalid HTPP parameters to get_category"
        return HttpResponseBadRequest(msg)

    # sanity checks on the version/project/model...
    try:
        version = MetadataVersion.objects.get(name__iexact=METADATA_NAME,version=version_name)
        project = MetadataProject.objects.get(name__iexact=project_name)
    except ObjectDoesNotExist:
        msg = "invalid HTTP parameters to get_category"
        return HttpResponseBadRequest(msg)
    model = version.getModel(model_name)
    if not model:
        msg = "invalid HTTP parameters to get_category"
        return HttpResponseBadRequest(msg)

    if category_type=="attribute":
        category_class = MetadataAttributeCategory
    elif category_type=="property":
        category_class = MetadataPropertyCategory
    else:
        msg = "invalid category_type: %s" % category_type
        return HttpResponseBadRequest(msg)

    try:
        category = category_class.objects.get(key=category_key)
    except ObjectDoesNotExist:
        if create_if_none:
            category = category_class.objects.create(key=category_key,name=category_name)
        else:
            msg = "invalid HTTP parameters to get_category"
            return HttpResponseBadRequest(msg)

    json_category = JSON_SERIALIZER.serialize([category])
    return HttpResponse(json_category[1:len(json_category)-1], mimetype='application/json');

def edit_category(request, category_type=""):
    
    category_key    = request.GET.get('k',None)
    category_name   = request.GET.get('n',None)
    version_name    = request.GET.get('v',None)
    project_name    = request.GET.get('p',None)
    model_name      = request.GET.get('m',None)

    if not (category_type and category_key and category_name and version_name and project_name and model_name):
        msg = "invalid HTPP parameters to delete_category"
        return HttpResponseBadRequest(msg)

    # sanity checks on the version/project/model...
    try:
        version = MetadataVersion.objects.get(name__iexact=METADATA_NAME,version=version_name)
        project = MetadataProject.objects.get(name__iexact=project_name)
    except ObjectDoesNotExist:
        msg = "invalid HTTP parameters to delete_category"
        return HttpResponseBadRequest(msg)
    model = version.getModel(model_name)
    if not model:
        msg = "invalid HTTP parameters to delete_category"
        return HttpResponseBadRequest(msg)

    if category_type=="attribute":
        category_class = MetadataAttributeCategory
    elif category_type=="property":
        category_class = MetadataPropertyCategory        
    else:
        msg = "invalid category_type: %s" % category_type
        return HttpResponseBadRequest(msg)

    try:
        category = category_class.objects.get(key=category_key)
    except ObjectDoesNotExist:
        msg = "invalid HTTP parameters to get_category"
        return HttpResponseBadRequest(msg)

    # override the existing category values with those from the javascript category dictionary (they are more current)
    for (key,value) in request.GET.iteritems():
        if key in ["description","order"]:
            # ACTUALLY, I ONLY WANT TO MODIFY CERTAIN FIELDS
            # ANYTHING ELSE IS DANGEROUS
            try:
                setattr(category, key, value);
            except:
                pass

    form = MetadataCategoryForm(instance=category)

    form_template = Template("\
      <!-- don't need to re-load JS/CSS b/c it's already loaded in the parent page -->\
      <div id='dcf'>\
        <div id='customize'>\
            <form>\
                <br/>\
                <div class='form'>\
                    <table>\
                        {% for field in form.visible_fields %}\
                            <tr class='{% cycle \"odd\" \"even\" %}'>\
                                <td class='field-label'>{{field.label}}:&nbsp;</td>\
                                <td class='field-value'>\
                                    <div class='field' name='{{field.name}}'>\
                                        {{field}}\
                                    </div>\
                                </td>\
                            </tr>\
                        {% endfor %} {# /field in form.visible_fields #}\
                    </table>\
                </div> <!-- /.form -->\
            </form>\
        </div> <!-- /#customize -->\
      </div> <!-- /#dcf -->\
    ")
    form_context  = Context({"STATIC_URL" : "/static/", "form" : form, })

    return HttpResponse(form_template.render(form_context))

def delete_category(request, category_type=""):
    category_key    = request.GET.get('k',None)
    category_name   = request.GET.get('n',None)
    version_name    = request.GET.get('v',None)
    project_name    = request.GET.get('p',None)
    model_name      = request.GET.get('m',None)

    if not (category_type and category_key and category_name and version_name and project_name and model_name):
        msg = "invalid HTPP parameters to delete_category"
        return HttpResponseBadRequest(msg)

    # sanity checks on the version/project/model...
    try:
        version = MetadataVersion.objects.get(name__iexact=METADATA_NAME,version=version_name)
        project = MetadataProject.objects.get(name__iexact=project_name)
    except ObjectDoesNotExist:
        msg = "invalid HTTP parameters to delete_category"
        return HttpResponseBadRequest(msg)
    model = version.getModel(model_name)
    if not model:
        msg = "invalid HTTP parameters to delete_category"
        return HttpResponseBadRequest(msg)

    if category_type=="attribute":
        category_class = MetadataAttributeCategory
    elif category_type=="property":
        category_class = MetadataPropertyCategory
    else:
        msg = "invalid category_type: %s" % category_type
        return HttpResponseBadRequest(msg)

    try:
        category = category_class.objects.get(key=category_key)
    except ObjectDoesNotExist:
            msg = "invalid HTTP parameters to get_category"
            return HttpResponseBadRequest(msg)

    id = category.id
    type = category.getType()
    
    if type == CategoryTypes.PROPERTY:
        category.delete()
        msg = "deleted %s category: %s" % (type,id)
    else:        
        msg = "uwilling to deleted %s category: %s" % (type,id)

    return HttpResponse(msg);
