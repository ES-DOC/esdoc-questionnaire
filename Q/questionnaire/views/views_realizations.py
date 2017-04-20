####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _

from Q.questionnaire.models.models_customizations import QModelCustomization
from Q.questionnaire.models.models_realizations import get_new_realizations, get_existing_realizations, set_owner
from Q.questionnaire.models.models_users import is_member_of, is_user_of
from Q.questionnaire.views.views_base import validate_view_arguments as validate_view_arguments_base, add_parameters_to_context, get_key_from_request, get_or_create_cached_object
from Q.questionnaire.views.views_errors import q_error
from Q.questionnaire.views.views_legacy import redirect_legacy_projects
from Q.questionnaire.q_utils import evaluate_lazy_object, add_parameters_to_url


def validate_view_arguments(project_name=None, ontology_key=None, document_type=None):
    """
    extends the "validate_view_arguments" fn in "views_base"
    by adding a check that there is a default customization associated w/ this project/ontology/proxy
    :param project_name:
    :param ontology_key:
    :param document_type:
    :return:
    """

    model_customization = None

    validity, project, ontology, model_proxy, msg = validate_view_arguments_base(
        project_name=project_name,
        ontology_key=ontology_key,
        document_type=document_type
    )

    if not validity:
        return validity, project, ontology, model_proxy, model_customization, msg

    try:
        model_customization = QModelCustomization.objects.get(
            project=project,
            proxy=model_proxy,
            is_default=True,
        )
    except ObjectDoesNotExist:
        msg = _(
            "There is no default customization associated with this document type for this project."
            "<br/>Please <a href='mailto:{0}'>contact</a> the project administrator for assistance."
        ).format(project.email)
        validity = False
        return validity, project, ontology, model_proxy, model_customization, msg

    return validity, project, ontology, model_proxy, model_customization, msg


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
    current_user = request.user
    if project.authenticated:
        if not current_user.is_authenticated():
            next_page = add_parameters_to_url(reverse("account_login"), next=request.path)
            return HttpResponseRedirect(next_page)
        if not is_user_of(current_user, project):
            next_page = reverse("project", kwargs={"project_name": project_name})
            msg = "You have tried to view a restricted resource for this project.  Please consider joining."
            messages.add_message(request, messages.WARNING, msg)
            return HttpResponseRedirect(next_page)

    # get (or set) realization objects from the cache...
    session_key = get_key_from_request(request)
    cached_realizations_key = "{0}_realizations".format(session_key)
    model_realization = get_or_create_cached_object(request.session, cached_realizations_key,
        get_new_realizations,
        **{
            "project": project,
            "ontology": ontology,
            "model_proxy": model_proxy,
            "key": model_proxy.name,
        }
    )

    if current_user.is_authenticated():
        set_owner(model_realization, evaluate_lazy_object(current_user))
    model_realization.is_root = True  # TODO: COME UP W/ A BETTER WAY OF DEALING W/ "is_root"

    # no forms are created here,
    # instead the load-on-demand paradigm is used,

    # work out various paths, so that ng can reload things as needed...
    view_url_dirname = request.path.rsplit('/', 1)[0]
    api_url_dirname = reverse("realization-list").rsplit('/', 1)[0]

    # gather all the extra information required by the template...
    template_context = {
        "project": project,
        "ontology": ontology,
        "proxy": model_proxy,
        "view_url_dirname": view_url_dirname,
        "api_url_dirname": api_url_dirname,
        "session_key": session_key,
        "customization": model_customization,
        "realization": model_realization,
        "read_only": "false",  # passing "false" instead of False b/c this is a JS variable
    }
    return render_to_response('questionnaire/q_edit.html', template_context, context_instance=context)


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
            next_page = add_parameters_to_url(reverse("account_login"), next=request.path)
            return HttpResponseRedirect(next_page)
        if not is_user_of(current_user, project):
            next_page = reverse("project", kwargs={"project_name": project_name})
            msg = "You have tried to view a restricted resource for this project.  Please consider joining."
            messages.add_message(request, messages.WARNING, msg)
            return HttpResponseRedirect(next_page)

    # get (or set) realization objects from the cache...
    # note that unlike in "q_edit_new" above, this bit is enclosed in a try/catch block
    try:
        session_key = get_key_from_request(request)
        cached_realizations_key = "{0}_realizations".format(session_key)
        model_realization = get_or_create_cached_object(request.session, cached_realizations_key,
            get_existing_realizations,
            **{
                "project": project,
                "ontology": ontology,
                "model_proxy": model_proxy,
                "model_id": realization_pk
            }
        )
    except ObjectDoesNotExist:
        msg = "Cannot find a document with an id of '{0}' for that project/ontology/document type combination.".format(realization_pk)
        return q_error(request, msg)

    # no forms are created here,
    # instead the load-on-demand paradigm is used,

    # work out various paths, so that ng can reload things as needed...
    # (notice these are slightly different than in "q_edit_new" above
    view_url_dirname = request.path.rsplit('/', 1)[0]
    api_url_dirname = reverse("realization-detail", kwargs={"pk": model_realization.pk}).rsplit('/', 2)[0]

    # gather all the extra information required by the template...
    template_context = {
        "project": project,
        "ontology": ontology,
        "proxy": model_proxy,
        "view_url_dirname": view_url_dirname,
        "api_url_dirname": api_url_dirname,
        "session_key": session_key,
        "customization": model_customization,
        "realization": model_realization,
        "read_only": "false",  # passing "false" instead of False b/c this is a JS variable
    }
    return render_to_response('questionnaire/q_edit.html', template_context, context_instance=context)


@redirect_legacy_projects
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


@redirect_legacy_projects
def q_view_existing(request, project_name=None, ontology_key=None, document_type=None, realization_pk=None):
    """
    this is exactly the same as "q_edit_existing" except:
    there are no authentication checks,
    the template_context & template are different.
    :param request:
    :param project_name:
    :param ontology_key:
    :param document_type:
    :param realization_pk:
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

    # no need to check authentication

    # get (or set) realization objects from the cache...
    # note that unlike in "q_edit_new" above, this bit is enclosed in a try/catch block
    try:
        session_key = get_key_from_request(request)
        cached_realizations_key = "{0}_realizations".format(session_key)
        model_realization = get_or_create_cached_object(request.session, cached_realizations_key,
            get_existing_realizations,
            **{
                "project": project,
                "ontology": ontology,
                "model_proxy": model_proxy,
                "model_id": realization_pk
            }
        )
    except ObjectDoesNotExist:
        msg = "Cannot find a document with an id of '{0}' for that project/ontology/document type combination.".format(realization_pk)
        return q_error(request, msg)

    # no forms are created here,
    # instead the load-on-demand paradigm is used,

    # work out various paths, so that ng can reload things as needed...
    # (notice these are slightly different than in "q_edit_new" above
    view_url_dirname = request.path.rsplit('/', 1)[0]
    api_url_dirname = reverse("realization-detail", kwargs={"pk": model_realization.pk}).rsplit('/', 2)[0]

    # gather all the extra information required by the template...
    template_context = {
        "project": project,
        "ontology": ontology,
        "proxy": model_proxy,
        "view_url_dirname": view_url_dirname,
        "api_url_dirname": api_url_dirname,
        "session_key": session_key,
        "customization": model_customization,
        "realization": model_realization,
        "read_only": "true",  # passing "true" instead of True b/c this is a JS variable
    }
    return render_to_response('questionnaire/q_view.html', template_context, context_instance=context)
