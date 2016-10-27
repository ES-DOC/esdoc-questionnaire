####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages

from Q.questionnaire.models.models_users import is_admin_of, is_user_of, is_member_of
from Q.questionnaire.models.models_customizations import QModelCustomization, get_existing_customizations
from Q.questionnaire.models.models_realizations import get_new_realizations, get_existing_realizations, set_owner
from Q.questionnaire.views.views_base import add_parameters_to_context, get_key_from_request, get_or_create_cached_object, validate_view_arguments as validate_view_arguments_base
from Q.questionnaire.views.views_legacy import redirect_legacy_projects
from Q.questionnaire.q_utils import evaluate_lazy_object
from Q.questionnaire.views.views_errors import q_error

# MODEL_REALIZATION_FORM_MAP = {
#     # map of various useful bits of info needed to (re)create forms & formsets
#     # strictly speaking, this isn't needed for the top-level view...
#     # but a similar method is used for the section views (see "views_services_load_section.py")...
#     # so I'm using this contrived map to keep the codebase similar in the two files
#     "model": {
#         "form_class": QModelRealizationForm,
#         "form_name": _("model_form_{safe_key}"),
#         "form_scope_prefix": "current_model",
#     },
#     "properties": {
#     },
# }


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

    validity, project, ontology, model_proxy, msg = validate_view_arguments_base(
        project_name=project_name,
        ontology_key=ontology_key,
        document_type=document_type
    )

    if not validity:
        return validity, project, ontology, model_proxy, customization, msg

    try:
        customization = QModelCustomization.objects.get(
            project=project,
            ontology=ontology,
            proxy=model_proxy,
            is_default=True,
        )
    except ObjectDoesNotExist:
        msg = "There is no default customization associated with this project/ontology/model."
        validity = False
        return validity, project, ontology, model_proxy, customization, msg

    return validity, project, ontology, model_proxy, customization, msg


@redirect_legacy_projects
def q_edit_new(request, project_name=None, ontology_key=None, document_type=None):

    # save any request parameters...
    # (in case of redirection)
    context = add_parameters_to_context(request)

    # check the arguments...
    validity, project, ontology, model_proxy, model_customization, msg = validate_view_arguments(
        project_name=project_name,
        ontology_key=ontology_key,
        document_type=document_type
    )
    if not validity:
        return q_error(request, msg)

    # check authentication...
    # (not using "@login_required" b/c some projects ignore authentication)
    current_user = evaluate_lazy_object(request.user)
    if project.authenticated:
        if not current_user.is_authenticated():
            next_page = "/login/?next=%s" % request.path
            return HttpResponseRedirect(next_page)
        if not is_user_of(current_user, project):
            next_page = "/%s/" % project_name
            msg = "You have tried to view a restricted resource for this project.  Please consider joining."
            messages.add_message(request, messages.WARNING, msg)
            return HttpResponseRedirect(next_page)

    # get (or set) realization objects from the cache...
    session_key = get_key_from_request(request)
#    # no need to cache customizations; I access them as needed during form creation
#    # cached_customizations_key = "{0}_customizations".format(session_key)
#    # model_customization = get_or_create_cached_object(request.session, cached_customizations_key,
#    #     get_existing_customizations,
#    #     **{
#    #         "project": project,
#    #         "ontology": ontology,
#    #         "model_proxy": model_proxy,
#    #         "customization_id": customization.id,
#    #     }
#    # )
    cached_realizations_key = "{0}_realizations".format(session_key)
    model_realization = get_or_create_cached_object(request.session, cached_realizations_key,
        get_new_realizations,
        **{
            "project": project,
            "ontology": ontology,
            "model_proxy": model_proxy,
            "key": model_proxy.name,
            "customization": model_customization,
        }
    )
    if current_user.is_authenticated():
        set_owner(model_realization, current_user)

    # TODO: THIS IS A ONE-OFF TO GET ME THROUGH THE MEDIUM-TERM
    # TODO: IN THE LONG-TERM I OUGHT TO FIGURE OUT HOW TO AUTOMATICALLY WORK OUT HOW/WHEN TO SET "is_root"
    # TODO: (MOST LIKELY IT SHOULD BE IN "Q.questionnaire.models.models_realizations.QModel#reset")
    model_realization.is_root = True

    # no need to generate any forms or formsets; I do that all via the load-on-demand paradigm

    # work out the various paths,
    # so that ng can reload things as needed
    view_url = request.path
    view_url_sections = [section for section in view_url.split('/') if section]
    view_url_dirname = '/'.join(view_url_sections[:])
    api_url = reverse("realization-list", kwargs={})
    api_url_sections = [section for section in api_url.split('/') if section]
    api_url_dirname = '/'.join(api_url_sections[:])

    # gather all the extra information required by the template
    _dict = {
        "session_key": session_key,
        "view_url_dirname": "/{0}/".format(view_url_dirname),
        "api_url_dirname": "/{0}/".format(api_url_dirname),
        "project": project,
        "ontology": ontology,
        "proxy": model_proxy,
        "realization": model_realization,
        "customization": model_customization,
        "read_only": "false",
    }

    return render_to_response('questionnaire/q_edit.html', _dict, context_instance=context)


@redirect_legacy_projects
def q_edit_existing(request, project_name=None, ontology_key=None, document_type=None, realization_pk=None):
    # save any request parameters...
    # (in case of redirection)
    context = add_parameters_to_context(request)

    # check the arguments...
    validity, project, ontology, model_proxy, model_customization, msg = validate_view_arguments(
        project_name=project_name,
        ontology_key=ontology_key,
        document_type=document_type
    )
    if not validity:
        return q_error(request, msg)

    # check authentication...
    # (not using "@login_required" b/c some projects ignore authentication)
    current_user = request.user
    if project.authenticated:
        if not current_user.is_authenticated():
            next_page = "/login/?next=%s" % request.path
            return HttpResponseRedirect(next_page)
        if not is_user_of(current_user, project):
            next_page = "/%s/" % project_name
            msg = "You have tried to view a restricted resource for this project.  Please consider joining."
            messages.add_message(request, messages.WARNING, msg)
            return HttpResponseRedirect(next_page)

    # get (or set) realization objects from the cache...
    # note that unlike in "q_edit_new" above, this bit is enclosed in a try/catch block
    # this is to deal w/ the possibility of an invalid realization_pk
    try:
        session_key = get_key_from_request(request)
        cached_realizations_key = "{0}_realizations".format(session_key)
        model_realization = get_or_create_cached_object(request.session, cached_realizations_key,
            get_existing_realizations,
            **{
                "project": project,
                "ontology": ontology,
                "model_proxy": model_proxy,
                "model_id": realization_pk,
            }
        )
    except ObjectDoesNotExist:
        msg = "Cannot find a document with an id of '{0}' for that project/ontology/model combination.".format(
            realization_pk)
        return q_error(request, msg)

    # no need to generate any forms or formsets; I do that all via the load-on-demand paradigm

    # work out the various paths,
    # so that ng can reload things as needed
    # (notice these are slightly different than in "q_edit_new" above
    view_url = request.path
    view_url_sections = [section for section in view_url.split('/') if section]
    view_url_dirname = '/'.join(view_url_sections[:-1])
    api_url = reverse("realization-detail", kwargs={"pk": model_realization.pk})
    api_url_sections = [section for section in api_url.split('/') if section]
    api_url_dirname = '/'.join(api_url_sections[:-1])

    # gather all the extra information required by the template
    _dict = {
        "session_key": session_key,
        "view_url_dirname": "/{0}/".format(view_url_dirname),
        "api_url_dirname": "/{0}/".format(api_url_dirname),
        "project": project,
        "ontology": ontology,
        "proxy": model_proxy,
        "realization": model_realization,
        "customization": model_customization,
        "read_only": "false",
    }

    return render_to_response('questionnaire/q_edit.html', _dict, context_instance=context)


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
    validity, project, ontology, model_proxy, model_customization, msg = validate_view_arguments(
        project_name=project_name,
        ontology_key=ontology_key,
        document_type=document_type
    )
    if not validity:
        return q_error(request, msg)

    # and then let the user know that they can't vew a _new_ document...
    msg = "The ES-DOC Questionnaire only supports viewing of <em>existing</em> documents."
    return q_error(request, msg)


def q_view_existing(request, project_name=None, ontology_key=None, document_type=None, realization_pk=None):
    # save any request parameters...
    # (in case of redirection)
    context = add_parameters_to_context(request)

    # check the arguments...
    validity, project, ontology, model_proxy, model_customization, msg = validate_view_arguments(
        project_name=project_name,
        ontology_key=ontology_key,
        document_type=document_type
    )
    if not validity:
        return q_error(request, msg)

    # no need to check authentication

    # get (or set) realization objects from the cache...
    # note that unlike in "q_edit_new" above, this bit is enclosed in a try/catch block
    # this is to deal w/ the possibility of an invalid realization_pk
    try:
        session_key = get_key_from_request(request)
        cached_realizations_key = "{0}_realizations".format(session_key)
        model_realization = get_or_create_cached_object(request.session, cached_realizations_key,
            get_existing_realizations,
            **{
                "project": project,
                "ontology": ontology,
                "model_proxy": model_proxy,
                "model_id": realization_pk,
            }
        )
    except ObjectDoesNotExist:
        msg = "Cannot find a document with an id of '{0}' for that project/ontology/model combination.".format(
            realization_pk)
        return q_error(request, msg)

    # no need to generate any forms or formsets; I do that all via the load-on-demand paradigm

    # work out the various paths,
    # so that ng can reload things as needed
    # (notice these are slightly different than in "q_edit_new" above
    view_url = request.path
    view_url_sections = [section for section in view_url.split('/') if section]
    view_url_dirname = '/'.join(view_url_sections[:-1])
    api_url = reverse("realization-detail", kwargs={"pk": model_realization.pk})
    api_url_sections = [section for section in api_url.split('/') if section]
    api_url_dirname = '/'.join(api_url_sections[:-1])

    # gather all the extra information required by the template
    _dict = {
        "session_key": session_key,
        "view_url_dirname": "/{0}/".format(view_url_dirname),
        "api_url_dirname": "/{0}/".format(api_url_dirname),
        "project": project,
        "ontology": ontology,
        "proxy": model_proxy,
        "realization": model_realization,
        "customization": model_customization,
        "read_only": "true",
    }

    return render_to_response('questionnaire/q_view.html', _dict, context_instance=context)
