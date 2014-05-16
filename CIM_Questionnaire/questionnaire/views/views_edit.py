
####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Sep 30, 2013 3:04:42 PM"

"""
.. module:: views_edit

Summary of module goes here

"""

import time
from django.utils import timezone

from django.db.models import Q
import operator

from django.core.exceptions  import ObjectDoesNotExist, FieldError, MultipleObjectsReturned
from django.db.models.fields import *

from questionnaire.utils    import *
from questionnaire.models   import *
from questionnaire.forms    import *
from questionnaire.views    import *

from questionnaire.models.metadata_model import create_models_from_components

def create_model_formset(models,model_customizer,request):
    initial_model_formset_data = [
        get_initial_data(model,{
            # TODO: DOUBLE CHECK IF I REALLY HAVE TO EXPLICITLY PASS THESE PARAMETERS
            # IF NOT, I CAN REDUCE THE NUMBER OF DB HITS HERE
            "proxy"             : model.proxy,
            "project"           : model.project,
            "version"           : model.version,
            "parent"            : model.parent,
            "last_modified"     : timezone.now(),
        })
        for model in models
    ]
    model_formset = MetadataModelFormSetFactory(
        request     = request,
        initial     = initial_model_formset_data,
        prefixes    = [u"%s_%s"%(model.vocabulary_key,model.component_key) for model in models],
        customizer  = model_customizer
    )
    return model_formset


def create_standard_property_formset(standard_properties,standard_property_customizers,request):

    model = standard_properties[0].model
    model_key = u"%s_%s" % (model.vocabulary_key,model.component_key)

    initial_standard_property_formset_data = [
        get_initial_data(standard_property,{
            "proxy"             : standard_property.proxy,
            "last_modified"     : timezone.now(),
            })
        for standard_property in standard_properties
    ]
    
    standard_property_formset = MetadataStandardPropertyInlineFormSetFactory(
        instance    = model,
        prefix      = model_key,
        request     = request,
        initial     = initial_standard_property_formset_data,
        extra       = len(initial_standard_property_formset_data),
        customizers = standard_property_customizers
    )
    return standard_property_formset

def questionnaire_edit_new(request,project_name="",model_name="",version_name="",**kwargs):

    # try to get the project...
    try:
        project = MetadataProject.objects.get(name__iexact=project_name)
    except MetadataProject.DoesNotExist:
        msg = "Cannot find the <u>project</u> '%s'.  Has it been registered?" % (project_name)
        return error(request,msg)
    if not project.active:
        msg = "Project '%s' is inactive." % (project_name)
        return error(request,msg)
    
    # check authentication...
    # (not using "@login_required" b/c some projects ignore authentication)
    if project.authenticated:
        current_user = request.user
        if not current_user.is_authenticated():
            return redirect('/login/?next=%s'%(request.path))
        if not (request.user.is_superuser or request.user.metadata_user.is_user_of(project)):
            msg = "User '%s' does not have editing permission for project '%s'." % (request.user,project_name)
            if project.email:
                msg += "<br/>Please <a href='mailto:%s'>contact</a> the project for support." % (project.email)
            return error(request,msg)

    # try to get the version...
    try:
        version = MetadataVersion.objects.get(name__iexact=version_name,registered=True)
    except MetadataVersion.DoesNotExist:
        msg = "Cannot find the <u>version</u> '%s'.  Has it been registered?" % (version_name)
        return error(request,msg)

    # try to get the model (proxy)...
    try:
        model_proxy = MetadataModelProxy.objects.get(version=version,name__iexact=model_name)
    except MetadataModelProxy.DoesNotExist:
        msg = "Cannot find the <u>model</u> '%s' in the <u>version</u> '%s'." % (model_name,version_name)
        return error(request,msg)

    # try to get the default customizers for this project/version/proxy combination...
    try:
        model_customizer = MetadataModelCustomizer.objects.get(project=project,version=version,proxy=model_proxy,default=True)
    except MetadataModelCustomizer.DoesNotExist:
        msg = "There is no default customization associated with this project/model/version."
        return error(request,msg)
    standard_property_customizers   = model_customizer.standard_property_customizers.all()
    scientific_property_customizers = {} # this is filled in below, once I've created the component tree

    # getting the vocabularies into the right order is a 2-step process
    # b/c vocabularies do not have an "order" attribute (since they can be used by multiple projects/customizations),
    # but the model_customizer does record the desired order of active vocabularies (as a comma-separated list)
    vocabularies     = model_customizer.vocabularies.all()
    vocabulary_order = [int(order) for order in model_customizer.vocabulary_order.split(',')]
    vocabularies     = sorted(vocabularies,key=lambda vocabulary: vocabulary_order.index(vocabulary.pk))

    model_filter_parameters = {
        "project" : project,
        "version" : version,
        "proxy"   : model_proxy,
    }
    INITIAL_PARAMETER_LENGTH=len(model_filter_parameters)
    # TODO: check if the user added any parameters to the request; if so, pass those parameters to "questionnaire_edit_existing()"
    # TODO: HAVE TO DO THIS DIFFERENTLY THAN CUSTOMIZERS (see "views_customize.py"), SINCE FIELDS ARE FKS TO PROPERTIES

    # here is the "root" model
    model    = MetadataModel(**model_filter_parameters)

    # it has to go in a list in-case it is part of a hierarchy
    # (the formsets assume a hierarchy; if not, it will just be a formset w/ 1 form)
    models = []
    models.append(model)
    if model_customizer.model_show_hierarchy:
        model.title           = model_customizer.model_root_component
        model.vocabulary_key  = slugify(DEFAULT_VOCABULARY)
        model.component_key   = slugify(model_customizer.model_root_component)        
 
        for vocabulary in vocabularies:
            model_filter_parameters["vocabulary_key"] = slugify(vocabulary.name)
            components = vocabulary.component_proxies.all()
            if components:
                # recursively go through the components of each vocabulary
                # adding corresponding models to the list
                root_component = components[0].get_root()
                model_filter_parameters["parent"] = model
                model_filter_parameters["title"] = u"%s : %s" % (vocabulary.name,root_component.name)
                create_models_from_components(root_component,model_filter_parameters,models)
   
    # these need to be sorted according to the customizers (which are ordered by default),
    # so that when I pass an iterator of customizers to the formset, they will match the underlying form that is created for each property
    standard_property_proxies = sorted(model_proxy.standard_properties.all(),key=lambda proxy: standard_property_customizers.get(proxy=proxy).order)

    standard_properties     = {}
    standard_property_filter_parameters = {
        # in theory, constant kwargs would go here
        # it just so happens that standardproperties don't have any
    }
    scientific_properties   = {}
    scientific_property_filter_parameters = {
        # in theory, constant kwargs would go here
        # it just so happens that scientificproperties don't have any
    }
    for model in models:

        model.reset(True)

        vocabulary_key  = model.vocabulary_key
        component_key   = model.component_key
        model_key       = u"%s_%s"%(model.vocabulary_key,model.component_key)

        standard_properties[model_key] = []
        standard_property_filter_parameters["model"] = model
        for standard_property_proxy in standard_property_proxies:
            standard_property_filter_parameters["proxy"] = standard_property_proxy
            standard_property = MetadataStandardProperty(**standard_property_filter_parameters)
            standard_property.reset()
            standard_properties[model_key].append(standard_property)

        # here's where we can _finally_ get the scientific_customizers
        scientific_property_customizers[model_key] = MetadataScientificPropertyCustomizer.objects.filter(model_customizer=model_customizer,model_key=model_key)

        scientific_properties[model_key] = []
        try:
            # TODO: REWORK THIS TO COPE W/ SLUGIFY
            # (RIGHT NOW IT DEPENDS ON NAMES ALREADY BEING SLUFIGIED, AS IT WERE)
            vocabulary      = MetadataVocabulary.objects.get(name__iexact=vocabulary_key)
            component_proxy = MetadataComponentProxy.objects.get(vocabulary=vocabulary,name__iexact=component_key)
            # END TODO
            scientific_property_filter_parameters["model"] = model
            # again, I have to order the proxies (and hence the properties themselves) so that when I pass the iteration of customizers everything is in the right order 
            # (and the correct customizer gets matched up w/ the correct property)
            scientific_property_proxies = sorted(component_proxy.scientific_properties.all(),key=lambda proxy: scientific_property_customizers[model_key].get(proxy=proxy).order)
            for scientific_property_proxy in scientific_property_proxies:
                scientific_property_filter_parameters["proxy"] = scientific_property_proxy
                scientific_property = MetadataScientificProperty(**scientific_property_filter_parameters)
                scientific_property.reset()
                scientific_properties[model_key].append(scientific_property)
        except ObjectDoesNotExist:
            # there were no scientific properties associated w/ this component (or, rather, no components associated w/ this vocabulary)
            # that's okay
            pass
    
    # this final check has to be done after "model.reset()" has been called
    if not model.is_document:
        msg = "<u>%s</u> is not a recognized document type in the CIM." % (model_name)
        return error(request,msg)

    # right, all of the models, standardproperties, scientificproperties are setup
    # now we can setup the forms

    model_formset                   = None
    standard_property_formsets      = {}
    scientific_property_formsets    = {}

    
    if request.method == "GET":

        model_formset = create_model_formset(models,model_customizer,request)

        standard_property_formsets = {}
        for model in models:
            model_key = u"%s_%s" % (model.vocabulary_key,model.component_key)
            standard_property_formsets[model_key] = create_standard_property_formset(standard_properties[model_key],standard_property_customizers,request)

        for (i,model) in enumerate(models):
            model_key = u"%s_%s"%(model.vocabulary_key,model.component_key)

            initial_scientific_property_formset_data = [
                get_initial_data(scientific_property,{
                    "proxy"         : scientific_property.proxy,
                    "last_modified" : time.strftime("%c")
                })
                for scientific_property in scientific_properties[model_key]
            ]
            scientific_property_formsets[model_key] = MetadataScientificPropertyInlineFormSetFactory(
                instance    = model,
                prefix      = model_key,
                request     = request,
                initial     = initial_scientific_property_formset_data,
                extra       = len(initial_scientific_property_formset_data),
                customizers = scientific_property_customizers[model_key]
            )
            
    else: # request.method == "POST":

        validity = []

        model_formset = MetadataModelFormSetFactory(
            request     = request,
            customizer  = model_customizer,
            prefixes    = [u"%s_%s"%(model.vocabulary_key,model.component_key) for model in models],
        )

        validity += [model_formset.is_valid()]

        for (i,model) in enumerate(models):
            model_key = u"%s_%s"%(model.vocabulary_key,model.component_key)
            standard_property_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
                instance    = model,
                prefix      = model_key,
                request     = request,
                customizers = standard_property_customizers
            )

            validity += [standard_property_formsets[model_key].is_valid()]

            scientific_property_formsets[model_key] = MetadataScientificPropertyInlineFormSetFactory(
                instance    = model,
                prefix      = model_key,
                request     = request,
                customizers = scientific_property_customizers[model_key]
            )

        
            validity += [scientific_property_formsets[model_key].is_valid()]

        if all(validity):

            print "SUCCESS"

        else:

            model_form_errors = False
            if model_formset.non_form_errors():
                print "model_formset.non_form_errors: %s" % (model_formset.non_form_errors())
            else:
                print "no non_form_errors in model_formset"
            for model_form in model_formset:
                if model_form.errors:
                    model_form_errors = True
                    print "model_form.errors: %s" % (model_form.errors)
            if not model_form_errors:
                print "no form_errors in model_formset"
            for model in models:
                model_key = u"%s_%s" % (model.vocabulary_key,model.component_key)
                if standard_property_formsets[model_key].non_form_errors():
                    print "standard_property_formsets[%s].non_form_errors: %s" % (model_key,standard_property_formsets[model_key].non_form_errors())
                else:
                    print "no non_form_errors in standard_property_formsets[%s]" % (model_key)
                standard_property_form_errors = False
                for standard_property_form in standard_property_formsets[model_key]:
                    if standard_property_form.errors:
                        standard_property_form_errors = True
                        print "standard_property_formsets[%s].errors: %s" % (model_key,standard_property_form.errors)
                if not standard_property_form_errors:
                    print "no form_errors in standard_property_formsets[%s]" % (model_key)
            for model in models:
                model_key = u"%s_%s" % (model.vocabulary_key,model.component_key)
                if scientific_property_formsets[model_key].non_form_errors():
                    print "scientific_property_formsets[%s].non_form_errors: %s" % (model_key,scientific_property_formsets[model_key].non_form_errors())
                else:
                    print "no non_form_errors in scientific_property_formsets[%s]" % (model_key)
                scientific_property_form_errors = False
                for scientific_property_form in scientific_property_formsets[model_key]:
                    if scientific_property_form.errors:
                        scientific_property_form_errors = True
                        print "scientific_property_form.errors: %s" % (scientific_property_form.errors)
                if not scientific_property_form_errors:
                    print "no form_errors in scientific_property_formsets[%s]" % (model_key)

            messages.add_message(request, messages.ERROR, "Failed to save instance.")

    
    dict = {
        "site"                                    : get_current_site(request),
        "project"                                 : project,
        "version"                                 : version,
        "vocabularies"                            : vocabularies,
        "model_proxy"                             : model_proxy,
        "model_customizer"                        : model_customizer,
        "model_formset"                           : model_formset,
        "standard_property_formsets"              : standard_property_formsets,
        "scientific_property_formsets"            : scientific_property_formsets,
        "questionnaire_version"                   : get_version(),
    }

    return render_to_response('questionnaire/questionnaire_edit.html', dict, context_instance=RequestContext(request))


def questionnaire_edit_existing(request,project_name="",model_name="",version_name="",document_name="",**kwargs):

    # try to get the project...
    try:
        project = MetadataProject.objects.get(name__iexact=project_name)
    except MetadataProject.DoesNotExist:
        msg = "Cannot find the <u>project</u> '%s'.  Has it been registered?" % (project_name)
        return error(request,msg)

    if not project.active:
        msg = "Project '%s' is inactive." % (project_name)
        return error(request,msg)

    # check authentication...
    # (not using @login_required b/c some projects ignore authentication)
    if project.authenticated:
        current_user = request.user
        if not current_user.is_authenticated():
            return redirect('/login/?next=%s'%(request.path))
        if not (request.user.is_superuser or request.user.metadata_user.is_user_of(project)):
            msg = "User '%s' does not have editing permission for project '%s'." % (request.user,project_name)
            if project.email:
                msg += "<br/>Please <a href='mailto:%s'>contact</a> the project for support." % (project.email)
            return error(request,msg)

    # try to get the version...
    try:
        version = MetadataVersion.objects.get(name__iexact=version_name,registered=True)
    except MetadataVersion.DoesNotExist:
        msg = "Cannot find the <u>version</u> '%s'.  Has it been registered?" % (version_name)
        return error(request,msg)


    # gather all the extra information required by the template
    dict = {
        "site"                                    : get_current_site(request),
        "project"                                 : project,
        "version"                                 : version,
        "questionnaire_version"                   : get_version(),
    }

    return render_to_response('questionnaire/questionnaire_edit.html', dict, context_instance=RequestContext(request))


def questionnaire_edit_help(request):

    # gather all the extra information required by the template
    dict = {
        "site"                          : get_current_site(request),
        "questionnaire_version"         : get_version(),
    }

    return render_to_response('questionnaire/questionnaire_edit_instructions.html', dict, context_instance=RequestContext(request))

