
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

from django.core.exceptions import ObjectDoesNotExist, FieldError, MultipleObjectsReturned
from django.db.models.fields import *
from django.contrib.sites.models    import get_current_site

from django.core.urlresolvers import reverse
from itertools import chain
from django.http import *
from django.shortcuts import *

from dcf.utils  import *
from dcf.models import *
from dcf.forms  import *
from dcf.views.views_error import error as dcf_error



def customize_instructions(request):
    return render_to_response('dcf/dcf_customize_instructions.html', {}, context_instance=RequestContext(request))


def customize_existing(request,version_number="",project_name="",model_name="",customizer_id="",**kwargs):

    msg = ""

    # try to get the requested customizer...
    try:
        model_customizer_instance = MetadataModelCustomizer.objects.get(pk=customizer_id)
    except ObjectDoesNotExist:
        msg = "Cannot find the specified Customizer.  Please try again."
        return dcf_error(request,msg)

#    standard_properties     = model_customizer_instance.getStandardPropertyCustomizers()
#    scientific_properties   = model_customizer_instance.getScientificPropertyCustomizers()
    
    project     = model_customizer_instance.getProject()
    version     = model_customizer_instance.getVersion()
    model_class = model_customizer_instance.getModel()

    # get the default categorization and vocabulary...
    categorizations = version.categorizations.all()
    vocabularies = project.vocabularies.all().filter(document_type__iexact=model_name)
    categorization  = categorizations[0] if categorizations else None
    if not categorization:
        msg = "There is no default categorization associated with version %s." % version
        return dcf_error(request,msg)
    if not vocabularies:
        msg = "There are no default vocabularies associated with project %s (for model %s)." % (project,model_name)
        return dcf_error(request,msg)

    component_list = []
    for vocabulary in vocabularies:
        try:
            component_list += vocabulary.getComponentList()
            if not any(component_list):
                msg = "There is no component hierarchy defined in this vocabulary.  Has it been registered?"
                return dcf_error(request,msg)
        except:
            msg = "There is no component hierarchy defined in this vocabulary.  Has it been registered?"
            return dcf_error(request,msg)

    standard_categories     = categorization.categories.all().order_by("order")

    scientific_categories   = project.categories.all().order_by("order")
    for vocabulary in vocabularies:
        scientific_categories = scientific_categories | vocabulary.categories.all().order_by("order")


#    # check that the user has permission for this view
#    if not request.user.is_authenticated():
#        return HttpResponseRedirect('%s/?next=%s' % (settings.LOGIN_URL,request.path))
#    else:
#        if not user_has_permission(request.user,project.restriction_customize):
#            msg = "You do not have permission to access this resource."
#            return dcf_error(request,msg)



    if request.method == "POST":
                    
        validity = []

        model_customizer_form = MetadataModelCustomizerForm( \
            request.POST,
            instance=model_customizer_instance,
            component_list = component_list,
            initial = {
                "categorization"                : categorization,
#                "vocabularies"                  : vocabularies,
                "standard_categories_content"   : JSON_SERIALIZER.serialize(standard_categories),
                "scientific_categories_content" : JSON_SERIALIZER.serialize(scientific_categories),
            }
        )

        standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance    = model_customizer_instance,
            prefix      = "standard_property",
            request     = request
        )

        scientific_property_customizer_formset = MetadataScientificPropertyCustomizerInlineFormSetFactory(
            instance    = model_customizer_instance,
            prefix      = "scientific_property",
            request     = request
        )

        validity += [model_customizer_form.is_valid()]
        validity += [standard_property_customizer_formset.is_valid()]
        validity += [scientific_property_customizer_formset.is_valid()]

        if all(validity):
       
# TODO: REMOVE LOOPS HERE
            model_customizer_instance = model_customizer_form.save()
            standard_property_customizer_instances = standard_property_customizer_formset.save(commit=False)
            for standard_property_customizer_instance in standard_property_customizer_instances:
                standard_property_customizer_instance.save()
            scientific_property_customizer_instances = scientific_property_customizer_formset.save(commit=False)
            for scientific_property_customizer_instance in scientific_property_customizer_instances:
                scientific_property_customizer_instance.save()

            customize_existing_url = reverse("customize_existing",kwargs={
                "version_number" : version.number,
                "project_name"   : project,
                "model_name"     : model_name,
                "customizer_id"  : model_customizer_instance.pk,
            }) + "?success=true"
            return HttpResponseRedirect(customize_existing_url)

    else: # request.method == "GET"

        if request.GET.get("success",False):
            msg = "Successfully saved the customization: '%s'." % model_customizer_instance.name

        model_customizer_form = MetadataModelCustomizerForm( \
            instance=model_customizer_instance,
            component_list = component_list,
            initial = {
                "categorization"                : categorization,
 #               "vocabularies"                  : vocabularies,
                "standard_categories_content"   : JSON_SERIALIZER.serialize(standard_categories),
                "scientific_categories_content" : JSON_SERIALIZER.serialize(scientific_categories),
            }
        )

        standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance    = model_customizer_instance,
            prefix      = "standard_property",
            request     = request
        )

        scientific_property_customizer_formset = MetadataScientificPropertyCustomizerInlineFormSetFactory(
            instance    = model_customizer_instance,
            prefix      = "scientific_property",
            request     = request
        )



    # gather all the extra information required by the template
    dict = {
        "msg"                                         : msg,
        "model_customizer_form"                       : model_customizer_form,
        "standard_property_customizer_formset"        : standard_property_customizer_formset,
        "scientific_property_customizer_formset"      : scientific_property_customizer_formset,
        "project"                                     : project,
        "version"                                     : version,
        "categorization"                              : categorization,
        "vocabularies"                                : vocabularies,
        "model_class"                                 : model_class,
        "component_list"                              : component_list,
    }

    return render_to_response('dcf/dcf_customize.html', dict, context_instance=RequestContext(request))


def customize_new(request,version_number="",project_name="",model_name=""):

    msg = ""

    # try to get the requested project...
    try:
        project = MetadataProject.objects.get(name__iexact=project_name)
    except ObjectDoesNotExist:
        msg = "Cannot find the project '%s'.  Has it been registered?" % project_name
        return dcf_error(request,msg)

    # try to get the requested version...
    if version_number:
        try:
            version = MetadataVersion.objects.get(name__iexact=METADATA_NAME,number=version_number)
        except ObjectDoesNotExist:
            msg = "Cannot find version '%s_%s'.  Has it been registered?" % (METADATA_NAME,version_number)
            return dcf_error(request,msg)
    else:
        version = project.getDefaultVersion()
        if not version:
            msg = "please specify a version; the '%s' project has no default one." % project.getName()
            return dcf_error(request,msg)

    # try to get the requested model (class)...
    model_class = version.getModelClass(model_name)
    if not model_class:
        msg = "Cannot find the model type '%s' in version '%s'.  Have all model types been registered?" % (model_name, version)
        return dcf_error(request,msg)

    # get the default categorization and vocabulary...
    categorizations = version.categorizations.all()
    vocabularies = project.vocabularies.all().filter(document_type__iexact=model_name)
    
    # TODO: THIS IS CLEARLY DUMB,
    # BUT THE RELATEDOBJECTMANAGER IS BEING USED FOR THE TIME WHEN
    # THIS CODE CAN SUPPORT MULTPLE CATEGORIZATIONS
    categorization  = categorizations[0] if categorizations else None
    if not categorization:
        msg = "There is no default categorization associated with version %s." % version
        return dcf_error(request,msg)
    if not vocabularies:
        msg = "There are no default vocabularies associated with '%s' within the project '%s'." % (model_class.getTitle(),project)
        return dcf_error(request,msg)

    component_list = []
    for vocabulary in vocabularies:
        try:
            component_list += vocabulary.getComponentList()
            if not any(component_list):
                msg = "There is no component hierarchy defined in this vocabulary.  Has it been registered?"
                return dcf_error(request,msg)
        except:
            msg = "There is no component hierarchy defined in this vocabulary.  Has it been registered?"
            return dcf_error(request,msg)

    standard_categories     = categorization.categories.all().order_by("order")

    scientific_categories   = project.categories.all().order_by("order")
    for vocabulary in vocabularies:
        scientific_categories = scientific_categories | vocabulary.categories.all().order_by("order")

    # at this point I know the project, model, version, categorization, vocabularies, and categories

    customizer_filter_parameters = {
        "project"   : project,
        "version"   : version,
        "model"     : model_name,
    }
    if request.method == "GET":
        # check if the user added any parameters to the request
        for (key,value) in request.GET.iteritems():
            value = re.sub('[\"\']','',value) # strip out any quotes
            field_type = type(MetadataModelCustomizer.getField(key))
            if field_type == BooleanField:
                # special case for boolean fields
                if value.lower()=="true" or value=="1":
                    customizer_filter_parameters[key] = True
                elif value.lower()=="false" or value=="0":
                    customizer_filter_parameters[key] = False
                else:
                    customizer_filter_parameters[key] = value
            elif field_type == CharField or field_type == TextField:
                # this ensures that the filter is case-insenstive for strings
                key = key + "__iexact"
                # bear in mind that if I ever change to using get_or_create, the filter will have to be case-sensitive
                # see https://code.djangoproject.com/ticket/7789 for more info
                customizer_filter_parameters[key] = value
            else:
                customizer_filter_parameters[key] = value        
        if len(customizer_filter_parameters) > 3:
            # if there were (extra) filter parameters passed
            # then try to get the customizer w/ those parameters
            try:
                existing_model_customizer_instance = MetadataModelCustomizer.objects.get(**customizer_filter_parameters)
                
                customize_existing_url = reverse("customize_existing",kwargs={
                    "version_number" : version.number,
                    "project_name"   : project.name,
                    "model_name"     : model_name,
                    "customizer_id"  : existing_model_customizer_instance.pk,
                })
                return HttpResponseRedirect(customize_existing_url)

            except FieldError,TypeError:
                # raise an error if some of the filter parameters were invalid
                msg = "Unable to access a Customizer with the following parameters: %s" % (", ").join([u'%s=%s'%(key,value) for (key,value) in customizer_filter_parameters.iteritems()])
                return dcf_error(request,msg)
            except MultipleObjectsReturned:
                # raise an error if those filter params weren't enough to uniquely identify a customizer
                msg = "Unable to find a <i>single</i> Customizer with the following parameters: %s" % (", ").join([u'%s=%s'%(key,value) for (key,value) in customizer_filter_parameters.iteritems()])
                return dcf_error(request,msg)
            except MetadataModelCustomizer.DoesNotExist:
                # raise an error if there was no matching query
                msg = "Unable to find any Customizer with the following parameters: %s" % (", ").join([u'%s=%s'%(key,value) for (key,value) in customizer_filter_parameters.iteritems()])
                return dcf_error(request,msg)

#    # check that the user has permission for this view
#    if not request.user.is_authenticated():
#        return HttpResponseRedirect('%s/?next=%s' % (settings.LOGIN_URL,request.path))
#    else:
#        if not user_has_permission(request.user,project.restriction_customize):
#            msg = "You do not have permission to access this resource."
#            return dcf_error(request,msg)



    # if I'm here then I will be working w/ new customizers...
    model_proxy                 = MetadataModelProxy.objects.get(version=version,model_name=model_name)
    model_customizer_instance   = MetadataModelCustomizer(**customizer_filter_parameters)
    model_customizer_instance.reset(model_proxy)

    # (I only need to create the property customizers in the GET)

    if request.method == "POST":

        validity = []

        model_customizer_form = MetadataModelCustomizerForm( \
            request.POST,
            component_list=component_list,
            instance=model_customizer_instance,
            initial = {
                "categorization"                : categorization,
  #              "vocabularies"                  : vocabularies,
                "standard_categories_content"   : JSON_SERIALIZER.serialize(standard_categories),
                "scientific_categories_content" : JSON_SERIALIZER.serialize(scientific_categories),
            }
        )

        standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance=model_customizer_instance,
            prefix="standard_property",
            request=request
        )

        scientific_property_customizer_formset = MetadataScientificPropertyCustomizerInlineFormSetFactory(
            instance=model_customizer_instance,
            prefix="scientific_property",
            request=request
        )

        validity += [model_customizer_form.is_valid()]
        validity += [standard_property_customizer_formset.is_valid()]
        validity += [scientific_property_customizer_formset.is_valid()]

        if all(validity):

# TODO: REMOVE LOOPS HERE?
# TODO: REMOVE setParent HERE?
            model_customizer_instance = model_customizer_form.save()
            standard_property_customizer_instances = standard_property_customizer_formset.save(commit=False)
            for standard_property_customizer_instance in standard_property_customizer_instances:
                standard_property_customizer_instance.setParent(model_customizer_instance)
                standard_property_customizer_instance.save()
            scientific_property_customizer_instances = scientific_property_customizer_formset.save(commit=False)
            for scientific_property_customizer_instance in scientific_property_customizer_instances:
                scientific_property_customizer_instance.setParent(model_customizer_instance)
                scientific_property_customizer_instance.save()

            customize_existing_url = reverse("customize_existing",kwargs={
                "version_number" : version.number,
                "project_name"   : project,
                "model_name"     : model_name,
                "customizer_id"  : model_customizer_instance.pk,
            }) + "?success=true"
            return HttpResponseRedirect(customize_existing_url)

        else:

            msg = "Unable to save the customization.  Please review the form and try again."

    else: # request.method == "GET"

        # (I already created the model customizer outside of this POST/GET block)

        standard_property_customizers = []
        standard_property_proxies   = MetadataStandardPropertyProxy.objects.filter(version=version,model_name=model_name)
        for standard_property_proxy in standard_property_proxies:
            standard_property_customizer = MetadataStandardPropertyCustomizer(**customizer_filter_parameters)
            standard_property_customizer.reset(standard_property_proxy)
            standard_property_customizers.append(standard_property_customizer)

        scientific_property_customizers = []
        #scientific_property_proxies = MetadataScientificPropertyProxy.objects.filter(vocabulary=vocabulary)
        scientific_property_proxies = MetadataScientificPropertyProxy.objects.filter(vocabulary__in=vocabularies)
        for scientific_property_proxy in scientific_property_proxies:
            scientific_property_customizer = MetadataScientificPropertyCustomizer(**customizer_filter_parameters)
            scientific_property_customizer.reset(scientific_property_proxy)
            scientific_property_customizers.append(scientific_property_customizer)

        model_customizer_form = MetadataModelCustomizerForm( \
            instance=model_customizer_instance,
            component_list = component_list,
            initial = {
                "project"                       : project,
                "version"                       : version,
                "model"                         : model_name,
                "categorization"                : categorization,
   #             "vocabularies"                  : vocabularies,
                "standard_categories_content"   : JSON_SERIALIZER.serialize(standard_categories),
                "scientific_categories_content" : JSON_SERIALIZER.serialize(scientific_categories),
            }
        )

        initial_standard_property_customizer_data = [
            get_initial_data(standard_property_customizer,{
                "project"   : project,
                "version"   : version,
                "model"     : model_name,
                "category"  : standard_property_customizer.category,
                "proxy"     : standard_property_customizer.proxy,
            })
            for standard_property_customizer in standard_property_customizers
        ]
        standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance=model_customizer_instance,
            initial=initial_standard_property_customizer_data,
            extra=len(initial_standard_property_customizer_data),
            prefix="standard_property",
            request=request
        )

        initial_scientific_property_customizer_data = [
            get_initial_data(scientific_property_customizer,{
                "project"   : project,
                "version"   : version,
                "model"     : model_name,
                "category"  : scientific_property_customizer.category,
                "proxy"     : scientific_property_customizer.proxy,
            })
            for scientific_property_customizer in scientific_property_customizers
        ]
        scientific_property_customizer_formset = MetadataScientificPropertyCustomizerInlineFormSetFactory(
            instance=model_customizer_instance,
            initial=initial_scientific_property_customizer_data,
            extra=len(initial_scientific_property_customizer_data),
            prefix="scientific_property",
            request=request,
        )

    # gather all the extra information required by the template
    dict = {
        "msg"                                         : msg,
        "model_customizer_form"                       : model_customizer_form,
        "standard_property_customizer_formset"        : standard_property_customizer_formset,
        "scientific_property_customizer_formset"      : scientific_property_customizer_formset,
        "project"                                     : project,
        "version"                                     : version,
        "vocabularies"                                : vocabularies,
        "model_class"                                 : model_class,
        "component_list"                              : component_list,
    }

    return render_to_response('dcf/dcf_customize.html', dict, context_instance=RequestContext(request))
