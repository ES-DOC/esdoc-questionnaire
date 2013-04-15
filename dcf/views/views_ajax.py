
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

from django.core.exceptions import ObjectDoesNotExist, FieldError, MultipleObjectsReturned
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

def customize_subform(request):

    attribute_name  = request.GET.get('a',None)
    model_name      = request.GET.get('m',None)
    project_name    = request.GET.get('p',None)
    version_name    = request.GET.get('v',None)

    # TODO: for now just get the default model customizer...
    # TODO: need to work out how to get the model customizer if it hasn't yet been saved

    msg = ""

    # try to get the requested project...
    try:
        project = MetadataProject.objects.get(name__iexact=project_name)
    except ObjectDoesNotExist:
        msg = "Cannot find the project '%s'.  Has it been registered?" % project_name
        return HttpResponseBadRequest(msg)

    # try to get the requested version...
    if version_name:
        try:
            version = MetadataVersion.objects.get(name__iexact=METADATA_NAME,version=version_name)
        except ObjectDoesNotExist:
            msg = "Cannot find version '%s'.  Has it been registered?" % (version_name)
            return HttpResponseBadRequest(msg)
    else:
        version = project.getDefaultVersion()
        if not version:
            msg = "please specify a %s version; the %s project has no default one." % (METADATA_NAME,project)
            return HttpResponseBadRequest(msg)

    # try to get the requested model (class)...
    model_class = version.getModel(model_name)
    if not model_class:
        msg = "Cannot find the model type '%s' in version '%s'.  Have all model types been loaded?" % (model_name, version)
        return HttpResponseBadRequest(msg)

    try:
        model_customizer = MetadataModelCustomizer.objects.get(project=project,version=version,model=model_name,default=1)
    except MetadataModelCustomizer.DoesNotExist:
        msg = "There is no default customization associated with '%s'" % (model_name)
        return HttpResponseBadRequest(msg)

    attribute = model_customizer.attributes.get(attribute_name__iexact=attribute_name)
    related_model_class = model_class._meta.get_field_by_name(attribute.attribute_name)[0].getTargetModelClass()

    # at this point:
    # project = the project being customized
    # version = the version being customized
    # attribute = the attribute being customized (this is a relationshipfield)
    # model_class = the model being customized
    # related_model_class = the target model of the relationship
    # model_customizer = the existing customizer for the model being customized

    # need to set related_model_customizer

    filterParameters = {}
    filterParameters["project"] = project
    filterParameters["version"] = version
    filterParameters["name"]    = model_customizer.name # this customizer should have the same name as the 'parent' customizer
    filterParameters["model"]   = related_model_class.getName()

    if attribute.subform_customizer:
        related_model_customizer = attribute.subform_customizer
    else:
        try:
            related_model_customizer = MetadataModelCustomizer.objects.get(**filterParameters)
        except MetadataModelCustomizer.DoesNotExist:
            related_model_customizer = MetadataModelCustomizer(**filterParameters)
    # the above code replaces the following line (it handles the case where there was a customizer created previously by the subform but never attached to a parent customizer)
    #related_model_customizer = attribute.subform_customizer or MetadataModelCustomizer(**filterParameters)

    if request.method == "POST":
        print request.POST
        form = MetadataModelCustomizerForm(request.POST,instance=related_model_customizer,request=request)
        if form.is_valid():
            related_model_customizer = form.save(commit=False)
            related_model_customizer.save()
            form.save_m2m()

            # outputting JSON w/ pk & name to add as option to formfield
            json_related_model_customizer = json.dumps({"pk":related_model_customizer.pk,"unicode":u'%s'%related_model_customizer})
            print "JSON:"
            print json_related_model_customizer
            return HttpResponse(json_related_model_customizer,mimetype='application/json')
        
        else:
            msg = "Unable to save.  Please review the form and try again."
            print form.errors
            
            
    else:
        form = MetadataModelCustomizerForm(instance=related_model_customizer,request=request)
        
    # gather all the extra information required by the template
    dict = {}
    dict["STATIC_URL"]      = "/static/"
    dict["msg"]             = msg   
    dict["form"]            = form  

    rendered_form = django.template.loader.render_to_string("dcf/dcf_customize_subform.html", dictionary=dict, context_instance=RequestContext(request))
    return HttpResponse(rendered_form,mimetype='text/html')
