
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
__date__ ="Feb 1, 2013 4:34:42 PM"

"""
.. module:: views_edit

Summary of module goes here

"""

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, FieldError, MultipleObjectsReturned
from django.http import *
from django.shortcuts import *

from dcf.utils import *
from dcf.models import *
from dcf.forms.forms_edit import *
from dcf.views.views_error import error as dcf_error

def edit_instructions(request):
    return render_to_response('dcf/dcf_edit_instructions.html', {}, context_instance=RequestContext(request))


def edit(request,version_name="",project_name="",model_name=""):

    msg = ""

    # try to get the requested project...
    try:
        project = MetadataProject.objects.get(name__iexact=project_name)
    except ObjectDoesNotExist:
        msg = "Cannot find the project '%s'.  Has it been registered?" % project_name
        #raise MetadataError(msg)
        #return HttpResponseBadRequest(msg)
        return dcf_error(request,msg)

    # try to get the requested version...
    if version_name:
        try:
            version = MetadataVersion.objects.get(name__iexact=METADATA_NAME,version=version_name)
        except ObjectDoesNotExist:
            msg = "Cannot find version '%s'.  Has it been registered?" % (version_name)
            #raise MetadataError(msg)
            #return HttpResponseBadRequest(msg)
            return dcf_error(request,msg)
    else:
        version = project.getDefaultVersion()
        if not version:
            msg = "please specify a %s version; the %s project has no default one." % (METADATA_NAME,project)
            #raise MetadataError(msg)
            #return HttpResponseBadRequest(msg)
            return dcf_error(request,msg)

    # get the default categorization and vocabulary (if any)
    categorization  = version.default_categorization
    vocabulary      = project.default_vocabulary

    # try to get the requested model (class)...
    model_class = version.getModel(model_name)
    if not model_class:
        msg = "Cannot find the model type '%s' in version '%s'.  Have all model types been loaded?" % (model_name, version)
        #raise MetadataError(msg)
        #return HttpResponseBadRequest(msg)
        return dcf_error(request,msg)

    # try to get the default customizer for this project/version/model...
    try:
        customizer = MetadataModelCustomizer.objects.get(project=project,version=version,model=model_name,default=1)
    except MetadataModelCustomizer.DoesNotExist:
        msg = "There is no default customization associated with '%s'" % (model_name)
        return dcf_error(request,msg)

    # filters (to get a _specific_ model) may have been passed in as HTTP parameters
    filterParameters = {}
    if request.GET:
        for (key,value) in request.GET.iteritems():
            #key = key + "__iexact"  # this ensures that the filter is case-insenstive
            # unfortunately, the filter has to be case-sensitive b/c get_or_create() below _is_ case-sensitive
            # see https://code.djangoproject.com/ticket/7789 for more info
            if value.lower()=="true":
                filterParameters[key] = 1
            elif value.lower()=="false":
                filterParameters[key] = 0
            else:
                filterParameters[key] = re.sub('[\"\']','',value) # strip out any quotes

    # now get the model...
    if len(filterParameters)>0:
        # a _specific_ model may have been requested
        try:
            model = model_class.objects.get(**filterParameters)
        except FieldError,TypeError:
            # raise an error if some of the filter parameters were invalid
            msg = "Unable to create a %s with the following parameters: %s" % (model_class.getTitle(), (", ").join([u'%s=%s'%(key,value) for (key,value) in filterParameters.iteritems()]))
            return dcf_error(request,msg)
        except MultipleObjectsReturned:
            # raise an error if those filter params weren't enough to uniquely identify a customizer
            msg = "Unable to find a <i>single</i> %s with the following parameters: %s" % (model_class.getTitle(), (", ").join([u'%s=%s'%(key,value) for (key,value) in filterParameters.iteritems()]))
            return dcf_error(request,msg)
        except model_class.DoesNotExist:
            # if there is nothing w/ those filter params, then create a new customizer
            # (note, it won't be saved until the user submits the form)
            model = model_class(**filterParameters)
    else:
        # otherwise, just return a new customizer
        model = model_class(**filterParameters)

    if not model.isCIMDocument():
        msg = "The model type %s is not an editable CIM class" % (model_class.getTitle())
        return dcf_error(request,msg)
    
    form_class = MetadataFormFactory(model_class,customizer)
    
    if request.method == "POST":
        pass
    else:
        form = form_class(instance=model,request=request)


    # gather all the extra information required by the template
    dict = {}
    dict["msg"]             = msg   # any msg to popup to the user
    dict["form"]            = form  # the form itself, obviously

    dict["global_vars"]     = {"version":version.version.lower(),"project":project.name.lower(),"model":model.getName().lower()}

    dict["project_name"]    = project.long_name
    dict["model_name"]      = customizer.model_title
    dict["version_name"]    = version.name
    dict["version_number"]  = version.version
    dict["vocabulary_path"] = vocabulary.file.url

    return render_to_response('dcf/dcf_edit.html', dict, context_instance=RequestContext(request))