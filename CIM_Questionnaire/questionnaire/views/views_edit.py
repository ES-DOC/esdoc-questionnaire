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
from django.contrib import messages

from django.contrib.sites.models import get_current_site
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext


from CIM_Questionnaire.questionnaire.models.metadata_project import MetadataProject
from CIM_Questionnaire.questionnaire.models.metadata_version import MetadataVersion
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer, MetadataModelCustomizer, MetadataStandardPropertyCustomizer, MetadataScientificPropertyCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel, MetadataStandardProperty, MetadataScientificProperty

from CIM_Questionnaire.questionnaire.forms.forms_edit import create_new_edit_forms_from_models, create_existing_edit_forms_from_models, create_edit_forms_from_data, save_valid_forms

from CIM_Questionnaire.questionnaire.views.views_error import questionnaire_error
from CIM_Questionnaire.questionnaire.views import *

from CIM_Questionnaire.questionnaire.utils import DEFAULT_VOCABULARY

from CIM_Questionnaire.questionnaire import get_version

__author__ = "allyn.treshansky"
__date__ = "Sep 30, 2013 3:04:42 PM"


def validate_view_arguments(request, project_name="", model_name="", version_name=""):
    """Ensures that the arguments passed to an edit view are valid (ie: resolve to active projects, models, versions)"""

    # try to get the project...
    try:
        project = MetadataProject.objects.get(name__iexact=project_name)
    except MetadataProject.DoesNotExist:
        msg = "Cannot find the <u>project</u> '%s'.  Has it been registered?" % (project_name)
        return error(request,msg)

    if not project.active:
        msg = "Project '%s' is inactive." % (project_name)
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
    if not model_proxy.is_document():
        msg = "<u>%s</u> is not a recognized document type in the CIM." % model_name
        return error(request, msg)

    # try to get the default model customizer for this project/version/proxy combination...
    try:
        model_customizer = MetadataModelCustomizer.objects.get(project=project, version=version, proxy=model_proxy, default=True)
    except MetadataModelCustomizer.DoesNotExist:
        msg = "There is no default customization associated with this project/model/version."
        return error(request, msg)

    return (project,version,model_proxy,model_customizer)

def questionnaire_edit_new(request, project_name="", model_name="", version_name="", **kwargs):

    # validate the arguments...
    (project,version,model_proxy,model_customizer) = validate_view_arguments(request,project_name=project_name,model_name=model_name,version_name=version_name)
    request.session["checked_arguments"] = True

    # check authentication...
    # (not using "@login_required" b/c some projects ignore authentication)
    if project.authenticated:
        current_user = request.user
        if not current_user.is_authenticated():
            return redirect('/login/?next=%s' % (request.path))
        if not (request.user.is_superuser or request.user.metadata_user.is_user_of(project)):
            msg = "User '%s' does not have editing permission for project '%s'." % (request.user, project_name)
            if project.email:
                msg += "<br/>Please <a href='mailto:%s'>contact</a> the project for support." % (project.email)
            return error(request, msg)

    # getting the vocabularies into the right order is a 2-step process
    # b/c vocabularies do not have an "order" attribute (since they can be used by multiple projects/customizations),
    # but the model_customizer does record the desired order of active vocabularies (as a comma-separated list)
    vocabularies = model_customizer.vocabularies.all()
    vocabulary_order = [int(order) for order in model_customizer.vocabulary_order.split(',')]
    vocabularies = sorted(vocabularies, key=lambda vocabulary: vocabulary_order.index(vocabulary.pk))

    # now try to get the default customizer set for this project/version/proxy combination...

    (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(model_customizer,vocabularies)

    # (also get the proxies b/c I'll need them when setting up properties below)
    # note that the proxies need to be sorted according to the customizers (which are ordered by default),
    # so that when I pass an iterator of customizers to the formsets, they will match the underlying form that is created for each property
    standard_property_proxies = [standard_property_customizer.proxy for standard_property_customizer in standard_property_customizers]
    scientific_property_proxies = {}
    scientific_property_customizers = {}
    for vocabulary_key,scientific_property_customizer_dict in nested_scientific_property_customizers.iteritems():
        for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
            model_key = u"%s_%s" % (vocabulary_key, component_key)
            # I have to restructure this; in the customizer views it makes sense to store these as a dictionary of dictionary
            # but here, they should only be one level deep (hence the use of "nested_" above
            scientific_property_customizers[model_key] = scientific_property_customizer_list
            scientific_property_proxies[model_key] = [scientific_property_customizer.proxy for scientific_property_customizer in scientific_property_customizer_list]

    # TODO: remove assert statement
    for properties in [model_customizer.standard_property_customizers.all(), model_customizer.scientific_property_customizers.all()]:
        for property in properties:
            assert property.name == property.proxy.name

    # TODO: will have to include _all_ properties in the forms (and just hide them in the template) so that they are there when I save things

    model_parameters = {
        "project": project,
        "version": version,
        "proxy": model_proxy,
    }
    INITIAL_PARAMETER_LENGTH = len(model_parameters)

    # TODO: check if the user added any parameters to the request; if so, pass those parameters to "questionnaire_edit_existing()"
    # TODO: HAVE TO DO THIS DIFFERENTLY THAN CUSTOMIZERS (see "views_customize.py"), SINCE FIELDS ARE FKS TO PROPERTIES
    for (key,value) in request.GET.iteritems():
        pass
    if len(model_parameters) > INITIAL_PARAMETER_LENGTH:
        pass

    # create the realization set
    # TODO: DON'T LIKE HAVING TO PASS MODEL_CUSTOMIZER, SINCE I WANT ALL CUSTOMIZATION FUNCTIONALITY TO BE FORM-SPECIFIC
    # BUT I HAVE TO SET THE ROOT VOCAB & COMPONENT KEY IN THIS FN
    (models, standard_properties, scientific_properties) = \
        MetadataModel.get_new_realization_set(project, version, model_proxy, standard_property_proxies, scientific_property_proxies, model_customizer, vocabularies)

    model_parent_dictionary = {}
    for model in models:
        if model.parent:
            model_parent_dictionary[model.get_model_key()] = model.parent.get_model_key()
        else:
            model_parent_dictionary[model.get_model_key()] = None

    if request.method == "GET":

        (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_new_edit_forms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers)

    else: # request.method == "POST":

        data = request.POST

        (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_edit_forms_from_data(data,models,model_customizer,standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers)

        if all(validity):

            model_instances = save_valid_forms(model_formset,standard_properties_formsets,scientific_properties_formsets, model_parent_dictionary=model_parent_dictionary)
            assert(len(model_instances)>0)
            root_model_id = model_instances[0].get_root().pk
            # this is used for other fns that might need to know what the view returns
            # (such as those in the testing framework)
            request.session["root_model_id"] = root_model_id
            
            # using Django's built-in messaging framework to pass status messages (as per https://docs.djangoproject.com/en/dev/ref/contrib/messages/)
            messages.add_message(request, messages.SUCCESS, "Successfully saved model instances")
            edit_existing_url = reverse("edit_existing",kwargs={
                "project_name"      : project_name,
                "model_name"        : model_name,
                "version_name"      : version_name,
                "model_id"          : root_model_id,
            })
            return HttpResponseRedirect(edit_existing_url)

        else:

            # using Django's built-in messaging framework to pass status messages (as per https://docs.djangoproject.com/en/dev/ref/contrib/messages/)
            messages.add_message(request, messages.ERROR, "Error saving model instances")

    dict = {
        "site": get_current_site(request),  # provide a special message if this is not the production site
        "project": project,  # used for generating URLs in the footer, and in the title
        "version": version,  # used for generating URLs in the footer
        "model_proxy": model_proxy,  # used for generating URLs in the footer
        "vocabularies": vocabularies,
        "model_customizer": model_customizer,
        "model_formset": model_formset,
        "standard_properties_formsets": standard_properties_formsets,
        "scientific_properties_formsets": scientific_properties_formsets,
        "questionnaire_version": get_version(),  # used in the footer
        "can_publish": False,  # only models that have already been saved can be published
    }

    return render_to_response('questionnaire/questionnaire_edit.html', dict, context_instance=RequestContext(request))


def questionnaire_edit_existing(request, project_name="", model_name="", version_name="", model_id="", **kwargs):

    # validate the arguments...
    (project,version,model_proxy,model_customizer) = validate_view_arguments(request,project_name=project_name,model_name=model_name,version_name=version_name)
    request.session["checked_arguments"] = True

    # check authentication...
    # (not using "@login_required" b/c some projects ignore authentication)
    if project.authenticated:
        current_user = request.user
        if not current_user.is_authenticated():
            return redirect('/login/?next=%s' % (request.path))
        if not (request.user.is_superuser or request.user.metadata_user.is_user_of(project)):
            msg = "User '%s' does not have editing permission for project '%s'." % (request.user, project_name)
            if project.email:
                msg += "<br/>Please <a href='mailto:%s'>contact</a> the project for support." % (project.email)
            return error(request, msg)

    # try to get the requested model...
    try:
        model = MetadataModel.objects.get(pk=model_id,name__iexact=model_name,project=project,version=version,proxy=model_proxy)
    except MetadataModel.DoesNotExist:
        msg = "Cannot find the specified model.  Please try again."
        return questionnaire_error(request,msg)
    if not model.is_root:
        # TODO: DEAL W/ THIS USE-CASE
        msg = "Currently only root models can be viewed.  Please try again."
        return questionnaire_error(request,msg)
    models = model.get_descendants(include_self=True)

    # getting the vocabularies into the right order is a 2-step process
    # b/c vocabularies do not have an "order" attribute (since they can be used by multiple projects/customizations),
    # but the model_customizer does record the desired order of active vocabularies (as a comma-separated list)
    vocabularies = model_customizer.vocabularies.all()
    vocabulary_order = [int(order) for order in model_customizer.vocabulary_order.split(',')]
    vocabularies = sorted(vocabularies, key=lambda vocabulary: vocabulary_order.index(vocabulary.pk))

    # now try to get the default customizer set for this project/version/proxy combination...

    (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(model_customizer,vocabularies)

    scientific_property_customizers = {}
    for vocabulary_key,scientific_property_customizer_dict in nested_scientific_property_customizers.iteritems():
        for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
            model_key = u"%s_%s" % (vocabulary_key, component_key)
            # I have to restructure this; in the customizer views it makes sense to store these as a dictionary of dictionary
            # but here, they should only be one level deep (hence the use of "nested_" above
            scientific_property_customizers[model_key] = scientific_property_customizer_list

    # create the realization set
    (models, standard_properties, scientific_properties) = \
        MetadataModel.get_existing_realization_set(models, model_customizer, standard_property_customizers)
    #
    # # clean it up so that everything is in the correct order...
    # for i,standard_property_customizer in enumerate(standard_property_customizers):
    #     standard_properties
    # standard_properties = sorted(unsorted_standard_properties, key=lambda property: standard_property_customizers.index(standard_property_customizers.get(proxy=property.proxy)))

    # clean it up a bit based on properties that have been customized not to be displayed
    for model in models:
        model_key = model.get_model_key()
        standard_property_list = standard_properties[model_key]
        for standard_property, standard_property_customizer in zip(standard_property_list,standard_property_customizers):
            if not standard_property_customizer.displayed:
                standard_property_list.remove(standard_property)
        # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
        if model_key not in scientific_property_customizers:
            scientific_property_customizers[model_key] = []
        scientific_property_list = scientific_properties[model_key]
        for scientific_property, scientific_property_customizer in zip(scientific_property_list,scientific_property_customizers[model_key]):
            if not scientific_property_customizer.displayed:
                scientific_property_list.remove(scientific_property)

    model_parent_dictionary = {}
    for model in models:
        if model.parent:
            model_parent_dictionary[model.get_model_key()] = model.parent.get_model_key()
        else:
            model_parent_dictionary[model.get_model_key()] = None


    # this is used for other fns that might need to know what the view returns
    # (such as those in the testing framework)
    assert(len(models)>0)
    root_model_id = models[0].get_root().pk
    request.session["root_model_id"] = root_model_id

    if request.method == "GET":

        (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_existing_edit_forms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers)

    else: # request.method == "POST":

        data = request.POST

        (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_edit_forms_from_data(data,models,model_customizer,standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers)

        if all(validity):

            model_instances = save_valid_forms(model_formset,standard_properties_formsets,scientific_properties_formsets, model_parent_dictionary=model_parent_dictionary)
            assert(len(model_instances) > 0)
            assert(root_model_id == model_instances[0].get_root().pk)
            # already set this above, just double-check that it hasn't changed
            #root_model_id = model_instances[0].get_root().pk

            # this is used for other fns that might need to know what the view returns
            # (such as those in the testing framework)
            request.session["root_model_id"] = root_model_id

            # using Django's built-in messaging framework to pass status messages (as per https://docs.djangoproject.com/en/dev/ref/contrib/messages/)
            messages.add_message(request, messages.SUCCESS, "Successfully saved instances.")

        else:

            # using Django's built-in messaging framework to pass status messages (as per https://docs.djangoproject.com/en/dev/ref/contrib/messages/)
            messages.add_message(request, messages.ERROR, "Error saving model instances")

    # gather all the extra information required by the template
    dict = {
        "site": get_current_site(request),  # provide a special message if this is not the production site
        "project": project,  # used for generating URLs in the footer, and in the title
        "version": version,  # used for generating URLs in the footer
        "model_proxy": model_proxy,  # used for generating URLs in the footer
        "vocabularies": vocabularies,
        "model_customizer": model_customizer,
        "model_formset": model_formset,
        "standard_properties_formsets": standard_properties_formsets,
        "scientific_properties_formsets": scientific_properties_formsets,
        "questionnaire_version": get_version(),  # used in the footer
        "can_publish": True,  # only models that have already been saved can be published
    }

    return render_to_response('questionnaire/questionnaire_edit.html', dict, context_instance=RequestContext(request))


def questionnaire_edit_help(request):

    # gather all the extra information required by the template
    dict = {
        "site"                          : get_current_site(request),
        "questionnaire_version"         : get_version(),
    }

    return render_to_response('questionnaire/questionnaire_edit_instructions.html', dict, context_instance=RequestContext(request))

