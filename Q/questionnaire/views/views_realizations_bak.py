####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
import json

from Q.questionnaire.models.models_users import is_admin_of, is_user_of, is_member_of
from Q.questionnaire.models.models_realizations_bak import MetadataModel, MetadataScientificProperty, get_new_realization_set, get_existing_realization_set, get_model_parent_dictionary
from Q.questionnaire.models.models_customizations import QModelCustomization, get_existing_customization_set
from Q.questionnaire.models.models_proxies import get_existing_proxy_set
from Q.questionnaire.forms.bak.forms_edit_bak import create_new_edit_forms_from_models, create_existing_edit_forms_from_models, create_edit_forms_from_data, save_valid_forms
from Q.questionnaire.views.views_base import add_parameters_to_context, get_key_from_request, get_or_create_cached_object, validate_view_arguments as validate_view_arguments_base
from Q.questionnaire.views.views_inheritance_bak import get_cached_inheritance_data
from Q.questionnaire.views.views_errors import q_error
from Q.questionnaire.q_utils import get_joined_keys_dict


def validate_view_arguments(project_name=None, ontology_key=None, document_type=None):
    """
    extends the "validate_view_arguments" fn in "views_base"
    by adding a check that there is a default cutomization associated w/ this project/ontology/proxy
    :param project_name:
    :param ontology_key:
    :param document_type:
    :return:
    """

    customization = None

    validity, project, ontology, proxy, msg = validate_view_arguments_base(
        project_name=project_name,
        ontology_key=ontology_key,
        document_type=document_type
    )

    if not validity:
        return validity, project, ontology, proxy, customization, msg

    try:
        customization = QModelCustomization.objects.get(
            project=project,
            ontology=ontology,
            proxy=proxy,
            is_default=True,
        )
    except QModelCustomization.DoesNotExist:
        msg = "There is no default customization associated with this project/model/ontology."
        validity = False
        return validity, project, ontology, proxy, customization, msg

    return validity, project, ontology, proxy, customization, msg


def convert_customization_set(new_style_customization_set):
    """
    converts a customization_set from the new way of doing things to the old way of doing things
    :param new_style_customization_set: a post v0.15 customization_set
    :return: a pre v0.15 customization_set
    """

    old_style_customization_set = {}

    old_style_customization_set["model_customizer"] = new_style_customization_set["model_customization"]
    old_style_customization_set["standard_category_customizers"] = new_style_customization_set["standard_category_customizations"]
    old_style_customization_set["standard_property_customizers"] = new_style_customization_set["standard_property_customizations"]

    old_style_customization_set["scientific_category_customizers"] = {}
    for scientific_category_customization in new_style_customization_set["scientific_category_customizations"]:
        vocabulary_key = scientific_category_customization.vocabulary_key
        component_key = scientific_category_customization.component_key
        if vocabulary_key not in old_style_customization_set["scientific_category_customizers"]:
            old_style_customization_set["scientific_category_customizers"][vocabulary_key] = {}
        if component_key not in old_style_customization_set["scientific_category_customizers"][vocabulary_key]:
            old_style_customization_set["scientific_category_customizers"][vocabulary_key][component_key] = []
        old_style_customization_set["scientific_category_customizers"][vocabulary_key][component_key].append(scientific_category_customization)

    old_style_customization_set["scientific_property_customizers"] = {}
    for scientific_property_customization in new_style_customization_set["scientific_property_customizations"]:
        vocabulary_key = scientific_property_customization.vocabulary_key
        component_key = scientific_property_customization.component_key
        if vocabulary_key not in old_style_customization_set["scientific_property_customizers"]:
            old_style_customization_set["scientific_property_customizers"][vocabulary_key] = {}
        if component_key not in old_style_customization_set["scientific_property_customizers"][vocabulary_key]:
            old_style_customization_set["scientific_property_customizers"][vocabulary_key][component_key] = []
        old_style_customization_set["scientific_property_customizers"][vocabulary_key][component_key].append(scientific_property_customization)

    return old_style_customization_set


def convert_proxy_set(new_style_proxy_set):
    """
    converts a proxy_set from the new way of doing things to the old way of doing things
    :param new_style_proxy_set: a post v0.15 proxy_set
    :return: a pre v0.15 proxy_set
    """

    old_style_proxy_set = {}

    old_style_proxy_set["model_proxy"] = new_style_proxy_set["model_proxy"]
    old_style_proxy_set["standard_property_proxies"] = new_style_proxy_set["standard_property_proxies"]
    old_style_proxy_set["scientific_property_proxies"] = {}

    for scientific_property_proxy in new_style_proxy_set["scientific_property_proxies"]:
        model_key = "{0}_{1}".format(
            scientific_property_proxy.component_proxy.vocabulary.get_key(),
            scientific_property_proxy.component_proxy.get_key(),
        )
        if model_key not in old_style_proxy_set["scientific_property_proxies"]:
            old_style_proxy_set["scientific_property_proxies"][model_key] = []
        old_style_proxy_set["scientific_property_proxies"][model_key].append(scientific_property_proxy)

    return old_style_proxy_set


def get_rid_of_non_displayed_items(realization_set, proxy_set, customization_set):

    # clean it up a bit based on properties that have been customized not to be displayed
    standard_property_proxies_to_remove = []
    for standard_property_customizer in customization_set["standard_property_customizers"]:
        if not standard_property_customizer.displayed:
            standard_property_proxies_to_remove.append(standard_property_customizer.proxy.pk)
    for model in realization_set["models"]:
        model_key = model.get_model_key()
        realization_set["standard_properties"][model_key] = \
            realization_set["standard_properties"][model_key].exclude(proxy__id__in=standard_property_proxies_to_remove)
        customization_set["standard_property_customizers"] = \
            customization_set["standard_property_customizers"].exclude(proxy__id__in=standard_property_proxies_to_remove)
        scientific_property_proxies_to_remove = []
        for scientific_property_customizer in customization_set["scientific_property_customizers"][model_key]:
            if not scientific_property_customizer.displayed:
                scientific_property_proxies_to_remove.append(scientific_property_customizer.proxy.pk)
        if isinstance(realization_set["scientific_properties"][model_key], list):
            realization_set["scientific_properties"][model_key] = \
                [spr for spr in realization_set["scientific_properties"][model_key] if spr.proxy.pk not in scientific_property_proxies_to_remove]
        else:
            realization_set["scientific_properties"][model_key] = realization_set["scientific_properties"][model_key].exclude(proxy__id__in=scientific_property_proxies_to_remove)
        if isinstance(customization_set["scientific_property_customizers"][model_key], list):
            customization_set["scientific_property_customizers"][model_key] = \
                [spc for spc in customization_set["scientific_property_customizers"][model_key] if spc.proxy.pk not in scientific_property_proxies_to_remove]
        else:
            customization_set["scientific_property_customizers"][model_key] = customization_set["scientific_property_customizers"][model_key].exclude(proxy__id__in=scientific_property_proxies_to_remove)


def get_rid_of_non_displayed_subitems(subrealization_set, proxy_set, customization_set):
    # clean it up a bit based on properties that have been customized not to be displayed
    # (only deals w/ standard_properties in subforms)
    standard_property_proxies_to_remove = []
    for standard_property_customizer in customization_set["standard_property_customizers"]:
        if not standard_property_customizer.displayed:
            standard_property_proxies_to_remove.append(standard_property_customizer.proxy.pk)
    for key in subrealization_set["standard_properties"].keys():
        if isinstance(subrealization_set["standard_properties"][key], list):
            subrealization_set["standard_properties"][key] = \
                [spr for spr in subrealization_set["standard_properties"][key] if spr.proxy.pk not in standard_property_proxies_to_remove]
        else:
            subrealization_set["standard_properties"][key] = \
                subrealization_set["standard_properties"][key].exclude(proxy__id__in=standard_property_proxies_to_remove)
    customization_set["standard_property_customizers"] = \
        customization_set["standard_property_customizers"].exclude(proxy__id__in=standard_property_proxies_to_remove)


def q_edit_new(request, project_name=None, ontology_key=None, document_type=None):

    # save any request parameters...
    # (in case of redirection)
    context = add_parameters_to_context(request)

    # check the arguments...
    validity, project, ontology, proxy, customization, msg = validate_view_arguments(
        project_name=project_name,
        ontology_key=ontology_key,
        document_type=document_type
    )
    if not validity:
        return q_error(request, msg)

    # check authentication...
    # (not using "@login_required" b/c some projects ignore authentication)
    if project.authenticated:
        current_user = request.user
        if not current_user.is_authenticated():
            next_page = "/login/?next=%s" % request.path
            return HttpResponseRedirect(next_page)
        if not is_user_of(current_user, project):
            next_page = "/%s/" % project_name
            msg = "You have tried to view a restricted resource for this project.  Please consider joining."
            messages.add_message(request, messages.WARNING, msg)
            return HttpResponseRedirect(next_page)

    # get the set of vocabularies that apply to this project/ontology/proxy/customization...
    vocabularies = customization.get_active_vocabularies()

    # get (or set) objects from the cache...
    session_key = get_key_from_request(request)
    cached_customization_set_key = "{0}_customization_set".format(session_key)
    cached_proxy_set_key = "{0}_proxy_set".format(session_key)
    cached_realization_set_key = "{0}_realization_set".format(session_key)
    customization_set = get_or_create_cached_object(request.session, cached_customization_set_key,
        get_existing_customization_set,
        **{
            "project": project,
            "ontology": ontology,
            "proxy": proxy,
            "customization_name": customization.name,
        }
    )
    customization_set = convert_customization_set(customization_set)
    customization_set["scientific_category_customizers"] = get_joined_keys_dict(customization_set["scientific_category_customizers"])
    customization_set["scientific_property_customizers"] = get_joined_keys_dict(customization_set["scientific_property_customizers"])
    proxy_set = get_or_create_cached_object(request.session, cached_proxy_set_key,
        get_existing_proxy_set,
        **{
            "ontology": ontology,
            "proxy": proxy,
            "vocabularies": vocabularies,
        }
    )
    proxy_set = convert_proxy_set(proxy_set)
    realization_set = get_or_create_cached_object(request.session, cached_realization_set_key,
        get_new_realization_set,
        **{
            "project": project,
            "ontology": ontology,
            "model_proxy": proxy_set["model_proxy"],
            "standard_property_proxies": proxy_set["standard_property_proxies"],
            "scientific_property_proxies": proxy_set["scientific_property_proxies"],
            "model_customizer": customization_set["model_customizer"],
            "vocabularies": vocabularies,
        }
    )

    if request.method == "GET":

        (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_new_edit_forms_from_models(
                realization_set["models"], customization_set["model_customizer"],
                realization_set["standard_properties"], customization_set["standard_property_customizers"],
                realization_set["scientific_properties"], customization_set["scientific_property_customizers"],
            )

        initial_completion_status = {
            realization.get_model_key(): False
            for realization in realization_set["models"]
        }

    else:  # request.method == "POST":
        data = request.POST
        inheritance_data = get_cached_inheritance_data(session_key)

        (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_edit_forms_from_data(
                data,
                realization_set["models"], customization_set["model_customizer"],
                realization_set["standard_properties"], customization_set["standard_property_customizers"],
                realization_set["scientific_properties"], customization_set["scientific_property_customizers"],
                inheritance_data=inheritance_data,
            )

        if all(validity):
            model_parent_dictionary = get_model_parent_dictionary(realization_set["models"])
            model_instances = save_valid_forms(
                model_formset, standard_properties_formsets, scientific_properties_formsets,
                model_parent_dictionary=model_parent_dictionary
            )

            root_model = model_instances[0].get_root()
            root_model_id = root_model.pk

            # this is used for other fns that might need to know what the view returns
            # (such as those in the testing framework)
            request.session["root_model_id"] = root_model_id
            msg = "Successfully saved document (v%s)" % root_model.document_version
            messages.add_message(request, messages.SUCCESS, msg)
            edit_existing_url = reverse("edit_existing", kwargs={
                "project_name": project_name,
                "document_type": document_type,
                "ontology_key": ontology_key,
                "pk": root_model_id,
            })
            return HttpResponseRedirect(edit_existing_url)

        else:

            messages.add_message(request, messages.ERROR, "Error saving document")

    # gather all the extra information required by the template
    _dict = {
        "session_key": session_key,
        "version": ontology,
        "model_proxy": proxy,
        "project": project,
        "vocabularies": vocabularies,
        "model_customizer": customization_set["model_customizer"],
        "initial_completion_status": json.dumps(initial_completion_status),
        "model_formset": model_formset,
        "standard_properties_formsets": standard_properties_formsets,
        "scientific_properties_formsets": scientific_properties_formsets,
        "display_completion_status": False,
        "can_publish": False,  # only models that have already been saved can be published
    }

    return render_to_response('questionnaire/bak/q_edit_bak.html', _dict, context_instance=context)


def q_edit_existing(request, project_name=None, ontology_key=None, document_type=None, pk=None):

    # save any request parameters...
    # (in case of redirection)
    context = add_parameters_to_context(request)

    # check the arguments...
    validity, project, ontology, proxy, customization, msg = validate_view_arguments(
        project_name=project_name,
        ontology_key=ontology_key,
        document_type=document_type
    )
    if not validity:
        return q_error(request, msg)

    # and try to get the requested model(s)...
    try:
        model = MetadataModel.objects.get(pk=pk, project=project, version=ontology, proxy=proxy)
    except MetadataModel.DoesNotExist:
        msg = "Cannot find the specified model.  Please try again."
        return q_error(request, msg)
    except ValueError:
        msg = "Invalid search terms.  Please try again."
        return q_error(request, msg)
    if not model.is_root:
        # TODO: DEAL W/ THIS USE-CASE
        msg = "Currently only root models can be viewed.  Please try again."
        return q_error(request, msg)

    # check authentication...
    # (not using "@login_required" b/c some projects ignore authentication)
    if project.authenticated:
        current_user = request.user
        if not current_user.is_authenticated():
            next_page = "/login/?next=%s" % request.path
            return HttpResponseRedirect(next_page)
        if not is_user_of(current_user, project):
            next_page = "/%s/" % project_name
            msg = "You have tried to view a restricted resource for this project.  Please consider joining."
            messages.add_message(request, messages.WARNING, msg)
            return HttpResponseRedirect(next_page)

    # get the set of vocabularies that apply to this project/ontology/proxy...
    vocabularies = customization.get_active_vocabularies()

    # get (or set) objects from the cache...
    # get (or set) objects from the cache...
    session_key = get_key_from_request(request)
    cached_customization_set_key = "{0}_customization_set".format(session_key)
    cached_proxy_set_key = "{0}_proxy_set".format(session_key)
    cached_realization_set_key = "{0}_realization_set".format(session_key)
    customization_set = get_or_create_cached_object(request.session, cached_customization_set_key,
        get_existing_customization_set,
        **{
            "project": project,
            "ontology": ontology,
            "proxy": proxy,
            "customization_name": customization.name,
        }
    )
    customization_set = convert_customization_set(customization_set)
    customization_set["scientific_category_customizers"] = get_joined_keys_dict(customization_set["scientific_category_customizers"])
    customization_set["scientific_property_customizers"] = get_joined_keys_dict(customization_set["scientific_property_customizers"])
    proxy_set = get_or_create_cached_object(request.session, cached_proxy_set_key,
        get_existing_proxy_set,
        **{
            "ontology": ontology,
            "proxy": proxy,
            "vocabularies": vocabularies,
        }
    )
    proxy_set = convert_proxy_set(proxy_set)
    realization_set = get_or_create_cached_object(request.session, cached_realization_set_key,
        get_existing_realization_set,
        **{
            "models": model.get_descendants(include_self=True),
            "model_customizer": customization_set["model_customizer"],
            "vocabularies": vocabularies,
        }
    )

    # this is used for other fns that might need to know what the view returns
    # (such as those in the testing framework)
    root_model_id = realization_set["models"][0].get_root().pk
    request.session["root_model_id"] = root_model_id

    # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
    for model in realization_set["models"]:
        model_key = model.get_model_key()
        if model_key not in customization_set["scientific_property_customizers"]:
            customization_set["scientific_property_customizers"][model_key] = MetadataScientificProperty.objects.none()

    get_rid_of_non_displayed_items(realization_set, proxy_set, customization_set)

    # # clean it up a bit based on properties that have been customized not to be displayed
    # # TODO: THIS MUST BE THE PLACE THAT CECELIA'S ERROR IS HAPPENING
    # # TODO: WHY DON'T I PASS THESE REDUCED LISTS TO THE FORM FNS?
    # for model in realization_set["models"]:
    #     model_key = model.get_model_key()
    #     standard_property_list = realization_set["standard_properties"][model_key]
    #     standard_properties_to_remove = []
    #     for standard_property, standard_property_customizer in zip(standard_property_list, customization_set["standard_property_customizers"]):
    #         if not standard_property_customizer.displayed:
    #             # this list is actually a queryset, so remove doesn't work
    #             # standard_property_list.remove(standard_property)
    #             # instead, I have to use exclude
    #             standard_properties_to_remove.append(standard_property.pk)
    #     standard_property_list.exclude(id__in=standard_properties_to_remove)
    #     # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
    #     if model_key not in customization_set["scientific_property_customizers"]:
    #         customization_set["scientific_property_customizers"][model_key] = MetadataScientificProperty.objects.none()
    #     scientific_property_list = customization_set["scientific_property_customizers"][model_key]
    #     scientific_properties_to_remove = []
    #     for scientific_property, scientific_property_customizer in zip(scientific_property_list, customization_set["scientific_property_customizers"][model_key]):
    #         if not scientific_property_customizer.displayed:
    #             # (as above) this list is actually a queryset, so remove doesn't work
    #             # scientific_property_list.remove(scientific_property)
    #             # instead, I have to use exclude
    #             scientific_properties_to_remove.append(scientific_property.pk)
    #     scientific_property_list.exclude(id__in=scientific_properties_to_remove)

    # now build the forms...
    if request.method == "GET":

        (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_existing_edit_forms_from_models(
                realization_set["models"], customization_set["model_customizer"],
                realization_set["standard_properties"], customization_set["standard_property_customizers"],
                realization_set["scientific_properties"], customization_set["scientific_property_customizers"]
            )

        initial_completion_status = {
            realization.get_model_key(): realization.is_complete()
            for realization in realization_set["models"]
        }

        display_completion_status = False

    else:  # request.method == "POST":
        data = request.POST
        inheritance_data = get_cached_inheritance_data(session_key)
        (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_edit_forms_from_data(
                data,
                realization_set["models"],
                customization_set["model_customizer"],
                realization_set["standard_properties"],
                customization_set["standard_property_customizers"],
                realization_set["scientific_properties"],
                customization_set["scientific_property_customizers"],
                inheritance_data=inheritance_data,
            )

        try_to_publish = "_publish" in data
        display_completion_status = False

        if all(validity):
            model_parent_dictionary = get_model_parent_dictionary(realization_set["models"])
            model_instances = save_valid_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, model_parent_dictionary=model_parent_dictionary)
            root_model = model_instances[0].get_root()

            initial_completion_status = {
                realization.get_model_key(): realization.is_complete()
                for realization in model_instances
            }

            # this is used for other fns that might need to know what the view returns
            # (such as those in the testing framework)
            request.session["root_model_id"] = root_model.pk

            if try_to_publish:
                # the .is_complete() fn works on a single instance
                # this checks _all_ instances
                completion = [model_instance.is_complete() for model_instance in model_instances]
                if all(completion):
                    root_model.publish(force_save=True)

                    msg = "Successfully saved and published document (v%s)" % root_model.document_version
                    messages.add_message(request, messages.SUCCESS, msg)
                else:
                    msg = "Saved document (v%s), but unable to publish it because it is incomplete." % root_model.document_version
                    messages.add_message(request, messages.WARNING, msg)
                    display_completion_status = True
            else:
                msg = "Successfully saved document (v%s)" % root_model.document_version
                messages.add_message(request, messages.SUCCESS, msg)

        else:

            if try_to_publish:
                msg = "Eror saving document; did not attempt to publish it."
            else:
                msg = "Eror saving document."
            messages.add_message(request, messages.ERROR, msg)

            initial_completion_status = {
                realization.get_model_key(): realization.is_complete()
                for realization in realization_set["models"]
            }

    # gather all the extra information required by the template
    _dict = {
        "session_key": session_key,
        "root_model_id": root_model_id,
        "version": ontology,
        "model_proxy": proxy,
        "project": project,
        "vocabularies": vocabularies,
        "model_customizer": customization_set["model_customizer"],
        "initial_completion_status": json.dumps(initial_completion_status),
        "model_formset": model_formset,
        "standard_properties_formsets": standard_properties_formsets,
        "scientific_properties_formsets": scientific_properties_formsets,
        "display_completion_status": display_completion_status,
        "can_publish": True,  # only models that have already been saved can be published

    }

    return render_to_response('questionnaire/bak/q_edit_bak.html', _dict, context_instance=context)


def q_view_new(request, project_name=None, ontology_key=None, document_type=None):
    """
    this is never exposed by templates
    but a user might still try to navigate explicitly to this URL
    just return an error telling them not to try that
    :param request:
    :param project_name:
    :param ontology_key:
    :param document_type:
    :return:
    """
    # save any request parameters...
    # (in case of redirection)
    context = add_parameters_to_context(request)

    # check the arguments...
    validity, project, ontology, proxy, customization, msg = validate_view_arguments(
        project_name=project_name,
        ontology_key=ontology_key,
        document_type=document_type
    )
    if not validity:
        return q_error(request, msg)

    # and then let the user know that you can't view a new document
    msg = "The Questionnaire only supports viewing of <em>existing</em> instances."
    return q_error(request, msg)


def q_view_existing(request, project_name=None, ontology_key=None, document_type=None, pk=None):

    # save any request parameters...
    # (in case of redirection)
    context = add_parameters_to_context(request)

    # check the arguments...
    validity, project, ontology, proxy, customization, msg = validate_view_arguments(
        project_name=project_name,
        ontology_key=ontology_key,
        document_type=document_type
    )
    if not validity:
        return q_error(request, msg)

    # and try to get the requested model(s)...
    try:
        model = MetadataModel.objects.get(pk=pk, project=project, version=ontology, proxy=proxy)
    except MetadataModel.DoesNotExist:
        msg = "Cannot find the specified model.  Please try again."
        return q_error(request, msg)
    except ValueError:
        msg = "Invalid search terms.  Please try again."
        return q_error(request, msg)
    if not model.is_root:
        # TODO: DEAL W/ THIS USE-CASE
        msg = "Currently only root models can be viewed.  Please try again."
        return q_error(request, msg)

    # check authentication...
    # (not using "@login_required" b/c some projects ignore authentication)
    if project.authenticated:
        current_user = request.user
        if not current_user.is_authenticated():
            next_page = "/login/?next=%s" % request.path
            return HttpResponseRedirect(next_page)
        if not is_user_of(current_user, project):
            next_page = "/%s/" % project_name
            msg = "You have tried to view a restricted resource for this project.  Please consider joining."
            messages.add_message(request, messages.WARNING, msg)
            return HttpResponseRedirect(next_page)

    # get the set of vocabularies that apply to this project/ontology/proxy...
    vocabularies = customization.get_active_vocabularies()

    # get (or set) objects from the cache...
    # get (or set) objects from the cache...
    session_key = get_key_from_request(request)
    cached_customization_set_key = "{0}_customization_set".format(session_key)
    cached_proxy_set_key = "{0}_proxy_set".format(session_key)
    cached_realization_set_key = "{0}_realization_set".format(session_key)
    customization_set = get_or_create_cached_object(request.session, cached_customization_set_key,
        get_existing_customization_set,
        **{
            "project": project,
            "ontology": ontology,
            "proxy": proxy,
            "customization_name": customization.name,
        }
    )
    customization_set = convert_customization_set(customization_set)
    customization_set["scientific_category_customizers"] = get_joined_keys_dict(customization_set["scientific_category_customizers"])
    customization_set["scientific_property_customizers"] = get_joined_keys_dict(customization_set["scientific_property_customizers"])
    proxy_set = get_or_create_cached_object(request.session, cached_proxy_set_key,
        get_existing_proxy_set,
        **{
            "ontology": ontology,
            "proxy": proxy,
            "vocabularies": vocabularies,
        }
    )
    proxy_set = convert_proxy_set(proxy_set)
    realization_set = get_or_create_cached_object(request.session, cached_realization_set_key,
        get_existing_realization_set,
        **{
            "models": model.get_descendants(include_self=True),
            "model_customizer": customization_set["model_customizer"],
            "vocabularies": vocabularies,
        }
    )

    # this is used for other fns that might need to know what the view returns
    # (such as those in the testing framework)
    root_model_id = realization_set["models"][0].get_root().pk
    request.session["root_model_id"] = root_model_id

    # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
    for model in realization_set["models"]:
        model_key = model.get_model_key()
        if model_key not in customization_set["scientific_property_customizers"]:
            customization_set["scientific_property_customizers"][model_key] = MetadataScientificProperty.objects.none()

    get_rid_of_non_displayed_items(realization_set, proxy_set, customization_set)

    # now build the forms...
    if request.method == "GET":

        (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_existing_edit_forms_from_models(
                realization_set["models"], customization_set["model_customizer"],
                realization_set["standard_properties"], customization_set["standard_property_customizers"],
                realization_set["scientific_properties"], customization_set["scientific_property_customizers"]
            )

        initial_completion_status = {
            realization.get_model_key(): realization.is_complete()
            for realization in realization_set["models"]
        }

        display_completion_status = False

    else:  # request.method == "POST":
        data = request.POST
        inheritance_data = get_cached_inheritance_data(session_key)
        (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_edit_forms_from_data(
                data,
                realization_set["models"],
                customization_set["model_customizer"],
                realization_set["standard_properties"],
                customization_set["standard_property_customizers"],
                realization_set["scientific_properties"],
                customization_set["scientific_property_customizers"],
                inheritance_data=inheritance_data,
            )

        try_to_publish = "_publish" in data
        display_completion_status = False

        if all(validity):
            model_parent_dictionary = get_model_parent_dictionary(realization_set["models"])
            model_instances = save_valid_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, model_parent_dictionary=model_parent_dictionary)
            root_model = model_instances[0].get_root()

            initial_completion_status = {
                realization.get_model_key(): realization.is_complete()
                for realization in model_instances
            }

            # this is used for other fns that might need to know what the view returns
            # (such as those in the testing framework)
            request.session["root_model_id"] = root_model.pk

            if try_to_publish:
                # the .is_complete() fn works on a single instance
                # this checks _all_ instances
                completion = [model_instance.is_complete() for model_instance in model_instances]
                if all(completion):
                    root_model.publish(force_save=True)

                    msg = "Successfully saved and published document (v%s)" % root_model.document_version
                    messages.add_message(request, messages.SUCCESS, msg)
                else:
                    msg = "Saved document (v%s), but unable to publish it because it is incomplete." % root_model.document_version
                    messages.add_message(request, messages.WARNING, msg)
                    display_completion_status = True
            else:
                msg = "Successfully saved document (v%s)" % root_model.document_version
                messages.add_message(request, messages.SUCCESS, msg)

        else:

            if try_to_publish:
                msg = "Eror saving document; did not attempt to publish it."
            else:
                msg = "Eror saving document."
            messages.add_message(request, messages.ERROR, msg)

            initial_completion_status = {
                realization.get_model_key(): realization.is_complete()
                for realization in realization_set["models"]
            }

    # gather all the extra information required by the template
    _dict = {
        "session_key": session_key,
        "root_model_id": root_model_id,
        "version": ontology,
        "model_proxy": proxy,
        "project": project,
        "vocabularies": vocabularies,
        "model_customizer": customization_set["model_customizer"],
        "initial_completion_status": json.dumps(initial_completion_status),
        "model_formset": model_formset,
        "standard_properties_formsets": standard_properties_formsets,
        "scientific_properties_formsets": scientific_properties_formsets,
        "display_completion_status": display_completion_status,
        "can_publish": False,  # cannot publish things in the "view" forms

    }

    return render_to_response('questionnaire/bak/q_view_bak.html', _dict, context_instance=context)
