
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
.. module:: views_customize

Summary of module goes here

"""

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, FieldError, MultipleObjectsReturned
from django.http import *
from django.shortcuts import *

from dcf.utils import *
from dcf.models import *
from dcf.forms.forms_customize import *
from dcf.views.views_error import error as dcf_error


def save_categories(categories_content,category_class):
    for category_content in categories_content.itervalues():
        category_id = category_content.pop("pk",None)
        if category_id:
            category_categorization = category_content.pop("categorization",None) # (don't worry about setting this; it's never going to change)
            try:
                category = category_class.objects.get(pk=category_id)
                for (field_name,field_value) in category_content.iteritems():
                    setattr(category,field_name,field_value)
                category.save()
            except:
                return False
    return True

def customize_instructions(request):
    return render_to_response('dcf/dcf_customize_instructions.html', {}, context_instance=RequestContext(request))
 

def customize(request,version_name="",project_name="",model_name=""):

    msg = ""

    # try to get the requested project...
    try:
        project = MetadataProject.objects.get(name__iexact=project_name)
    except ObjectDoesNotExist:
        msg = "Cannot find the project '%s'.  Has it been registered?" % project_name
        return dcf_error(request,msg)

    # try to get the requested version...
    if version_name:
        try:
            version = MetadataVersion.objects.get(name__iexact=METADATA_NAME,version=version_name)
        except ObjectDoesNotExist:
            msg = "Cannot find version '%s'.  Has it been registered?" % (version_name)
            return dcf_error(request,msg)
    else:
        version = project.getDefaultVersion()
        if not version:
            msg = "please specify a %s version; the %s project has no default one." % (METADATA_NAME,project)
            return dcf_error(request,msg)

    # try to get the requested model (class)...
    model = version.getModel(model_name)
    if not model:
        msg = "Cannot find the model type '%s' in version '%s'.  Have all model types been loaded?" % (model_name, version)
        return dcf_error(request,msg)

    # get the default categorization and vocabulary
    # TODO: (these are set in admin right now, and can't be changed in the customization form)
    categorization  = version.default_categorization
    vocabulary      = project.default_vocabulary
    if not categorization:
        msg = "There is no default categorization associated with version %s." % version
        return dcf_error(request,msg)
    if not vocabulary:
        msg = "There is no default vocabulary associated with project %s." % project
        return dcf_error(request,msg)
    
    # filters (to get a _specific_ customizer) may have been passed in as HTTP parameters
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
    filterParameters["project"] = project
    filterParameters["version"] = version
    filterParameters["model"]   = model_name

    if len(filterParameters) > 3:
        # if there were (extra) filter parameters passed
        # then try to get the customizer w/ those parameters
        try:
            customizer = MetadataModelCustomizer.objects.get(**filterParameters)
        except FieldError,TypeError:
            # raise an error if some of the filter parameters were invalid
            msg = "Unable to create a Customizer with the following parameters: %s" % (", ").join([u'%s=%s'%(key,value) for (key,value) in filterParameters.iteritems()])
            return dcf_error(request,msg)
        except MultipleObjectsReturned:
            # raise an error if those filter params weren't enough to uniquely identify a customizer
            msg = "Unable to find a <i>single</i> Customizer with the following parameters: %s" % (", ").join([u'%s=%s'%(key,value) for (key,value) in filterParameters.iteritems()])
            return dcf_error(request,msg)
        except MetadataModelCustomizer.DoesNotExist:
            # if there is nothing w/ those filter params, then create a new customizer
            # (note, it won't be saved until the user submits the form)
            customizer = MetadataModelCustomizer(**filterParameters)
    else:
        # otherwise, just return a new customizer
        customizer = MetadataModelCustomizer(**filterParameters)    


    if request.method == "POST":

        form = MetadataModelCustomizerForm(request.POST,instance=customizer,request=request)
        if form.is_valid():
            customizer_instance = form.save(commit=False)
            print "ONE %s" % len(customizer_instance.attributes.all())
            customizer_instance.save()
            print "TWO %s" % len(customizer_instance.attributes.all())
            form.save_subforms(commit=True)
            print "THREE %s" % len(customizer_instance.attributes.all())
            form.save_m2m()
            print "FOUR %s" % len(customizer_instance.attributes.all())

            # attributes & properties are saved automatically along w/ the model_form
            # but categories have to be explicitly saved separately
            # b/c they are manipulated via a JQuery tagging widget and therefore aren't bound to a form
            save_categories(json.loads(form.data["attribute_categories_content"]),MetadataAttributeCategory)
            save_categories(json.loads(form.data["property_categories_content"]),MetadataPropertyCategory)

            msg = "Successfully saved the customization: '%s'." % customizer_instance.name

        else:
            print form.errors
            print form.non_field_errors()
            msg = "Unable to save the customization.  Please review the form and try again."

    else:

        form = MetadataModelCustomizerForm(instance=customizer,request=request)
    
    # gather all the extra information required by the template
    dict = {}
    dict["msg"]             = msg   # any msg to popup to the user
    dict["form"]            = form  # the form, obviously
    dict["global_vars"]     = {
                                "version"   :   version.version.lower(),
                                "project"   :   project.name.lower(),
                                "model"     :   model.getName().lower(),
                                # TODO: HANG ON HERE, model IS A CLASS; WON'T THIS ALWAYS RETURN ""?
                                "id"        :   model.pk or ""
                              }

    dict["project_name"]    = project.long_name
    dict["model_name"]      = model.getTitle()
    dict["version_name"]    = version.name
    dict["version_number"]  = version.version
    dict["vocabulary_path"] = vocabulary.file.url
    
    return render_to_response('dcf/dcf_customize.html', dict, context_instance=RequestContext(request))