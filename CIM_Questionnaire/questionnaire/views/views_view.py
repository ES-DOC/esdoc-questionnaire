####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2014 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"
__date__ = "Dec 01, 2014 3:00:00 PM"

"""
.. module:: views_view

views for viewing an existing CIM Document
"""

from django.contrib.sites.models import get_current_site
from django.shortcuts import render_to_response
from django.template import RequestContext

from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataModelCustomizer, MetadataScientificPropertyCustomizer
from CIM_Questionnaire.questionnaire.forms.forms_edit import create_existing_edit_forms_from_models
from CIM_Questionnaire.questionnaire.views.views_base import validate_view_arguments
from CIM_Questionnaire.questionnaire.views.views_base import get_cached_existing_customization_set, get_cached_proxy_set, get_cached_new_realization_set, get_cached_existing_realization_set
from CIM_Questionnaire.questionnaire.views.views_error import questionnaire_error
from CIM_Questionnaire.questionnaire import get_version


def validate_view_view_arguments(project_name="", model_name="", version_key=""):

    (validity, project, version, model_proxy, msg) = \
        validate_view_arguments(project_name=project_name, model_name=model_name, version_key=version_key)

    model_customizer = None

    if not validity:
        return (validity, project, version, model_proxy, model_customizer, msg)

    # try to get the default model customizer for this project/version/proxy combination...
    try:
        model_customizer = MetadataModelCustomizer.objects.prefetch_related("vocabularies").get(project=project, version=version, proxy=model_proxy, default=True)
    except MetadataModelCustomizer.DoesNotExist:
        msg = "There is no default customization associated with this project/model/version."
        validity = False
        return (validity, project, version, model_proxy, model_customizer, msg)

    return (validity, project, version, model_proxy, model_customizer, msg)


def questionnaire_view_new(request, project_name="", model_name="", version_key="", **kwargs):

    # validate the arguments...
    (validity, project, version, model_proxy, model_customizer, msg) = \
        validate_view_view_arguments(project_name=project_name, model_name=model_name, version_key=version_key)
    if not validity:
        return questionnaire_error(request, msg)

    # and then let the user know that you can't view a new document
    msg = "The Questionnaire only supports viewing of <i>existing</i> instances."
    return questionnaire_error(request, msg)


def questionnaire_view_existing(request, project_name="", model_name="", version_key="", model_id="", **kwargs):

    # validate the arguments...
    (validity, project, version, model_proxy, model_customizer, msg) = \
        validate_view_view_arguments(project_name=project_name, model_name=model_name, version_key=version_key)
    if not validity:
        return questionnaire_error(request, msg)
    request.session["checked_arguments"] = True

    # try to get the requested model(s)...
    try:
        model = MetadataModel.objects.get(pk=model_id, project=project, version=version, proxy=model_proxy)
    except MetadataModel.DoesNotExist:
        msg = "Cannot find the specified model.  Please try again."
        return questionnaire_error(request, msg)
    if not model.is_root:
        # TODO: DEAL W/ THIS USE-CASE
        msg = "Currently only root models can be viewed.  Please try again."
        return questionnaire_error(request, msg)
    # don't bother checking authentication; all users can view instances

    # # getting the vocabularies into the right order is a 2-step process
    # # b/c vocabularies do not have an "order" attribute (since they can be used by multiple projects/customizations),
    # # but the model_customizer does record the desired order of active vocabularies (as a comma-separated list)
    # vocabularies = model_customizer.vocabularies.all()
    # vocabulary_order = [int(order) for order in filter(None,model_customizer.vocabulary_order.split(','))]
    # vocabularies = sorted(vocabularies, key=lambda vocabulary: vocabulary_order.index(vocabulary.pk))
    vocabularies = model_customizer.get_active_sorted_vocabularies()

    # get (or set) items from the cache...
    session_id = request.session.session_key
    customizer_set = get_cached_existing_customization_set(session_id, model_customizer, vocabularies)
    proxy_set = get_cached_proxy_set(session_id, customizer_set)
    realization_set = get_cached_existing_realization_set(session_id, model.get_descendants(include_self=True), customizer_set, proxy_set, vocabularies)

    # this is used for other fns that might need to know what the view returns
    # (such as those in the testing framework)
    root_model_id = realization_set["models"][0].get_root().pk
    request.session["root_model_id"] = root_model_id

    # clean it up a bit based on properties that have been customized not to be displayed
    # TODO: THIS MUST BE THE PLACE THAT CECELIA'S ERROR IS HAPPENING
    # TODO: WHY DON'T I PASS THESE REDUCED LISTS TO THE FORM FNS?
    for model in realization_set["models"]:
        model_key = model.get_model_key()
        standard_property_list = realization_set["standard_properties"][model_key]
        standard_properties_to_remove = []
        for standard_property, standard_property_customizer in zip(standard_property_list, customizer_set["standard_property_customizers"]):
            if not standard_property_customizer.displayed:
                # this list is actually a queryset, so remove doesn't work
                # standard_property_list.remove(standard_property)
                # instead, I have to use exclude
                standard_properties_to_remove.append(standard_property.pk)
        standard_property_list.exclude(id__in=standard_properties_to_remove)
        # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
        if model_key not in customizer_set["scientific_property_customizers"]:
            customizer_set["scientific_property_customizers"][model_key] = MetadataScientificPropertyCustomizer.objects.none()
        scientific_property_list = customizer_set["scientific_property_customizers"][model_key]
        scientific_properties_to_remove = []
        for scientific_property, scientific_property_customizer in zip(scientific_property_list, customizer_set["scientific_property_customizers"][model_key]):
            if not scientific_property_customizer.displayed:
                # (as above) this list is actually a queryset, so remove doesn't work
                # scientific_property_list.remove(scientific_property)
                # instead, I have to use exclude
                scientific_properties_to_remove.append(scientific_property.pk)
        scientific_property_list.exclude(id__in=scientific_properties_to_remove)

    if request.method == "GET" or request.method == "POST":  # IN THE VIEW YOU CAN'T SEND A POST, SO JUST IGNORE IT

        (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_existing_edit_forms_from_models(realization_set["models"], customizer_set["model_customizer"], realization_set["standard_properties"], customizer_set["standard_property_customizers"], realization_set["scientific_properties"], customizer_set["scientific_property_customizers"])

    # gather all the extra information required by the template
    _dict = {
        "site": get_current_site(request),  # provide a special message if this is not the production site
        "project": project,  # used for generating URLs in the footer, and in the title
        "version": version,  # used for generating URLs in the footer
        "model_proxy": model_proxy,  # used for generating URLs in the footer
        "vocabularies": vocabularies,
        "model_customizer": customizer_set["model_customizer"],
        "model_formset": model_formset,
        "standard_properties_formsets": standard_properties_formsets,
        "scientific_properties_formsets": scientific_properties_formsets,
        "questionnaire_version": get_version(),  # used in the footer
        "session_id": session_id,
        "root_model_id": root_model_id,
        "can_publish": True,  # only models that have already been saved can be published
    }

    return render_to_response('questionnaire/questionnaire_view.html', _dict, context_instance=RequestContext(request))


def questionnaire_view_help(request):

    # gather all the extra information required by the template
    _dict = {
        "site": get_current_site(request),
        "questionnaire_version": get_version(),
    }

    return render_to_response('questionnaire/questionnaire_edit_instructions.html', _dict, context_instance=RequestContext(request))

