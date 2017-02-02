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

from Q.questionnaire.forms.forms_customizations import QModelCustomizationForm
from Q.questionnaire.models.models_customizations import get_new_customizations, get_existing_customizations, set_owner
from Q.questionnaire.models.models_users import is_member_of, is_user_of, is_admin_of
from Q.questionnaire.views.views_base import validate_view_arguments, add_parameters_to_context, get_key_from_request, get_or_create_cached_object
from Q.questionnaire.views.views_errors import q_error
from Q.questionnaire.views.views_legacy import redirect_legacy_projects
from Q.questionnaire.q_utils import evaluate_lazy_object, add_parameters_to_url


MODEL_CUSTOMIZATION_FORM_MAP = {
    # map of various useful bits of info needed to (re)create forms;
    # strictly speaking, this isn't needed for the top-level view,
    # but a similar method is used for the section views (see "views_services_load_section.py"),
    # so I'm using this contrived map to keep the codebase similar in the 2 files.
    "form_class": QModelCustomizationForm,
    "form_name": _("model_customization_form_{safe_key}"),
    "form_scope_prefix": "current_model",
}


@redirect_legacy_projects
def q_customize_new(request, project_name=None, ontology_key=None, document_type=None):

    # save any request parameters...
    # (in case of redirection)
    context = add_parameters_to_context(request)

    # check the arguments...
    validity, project, ontology, model_proxy, msg = validate_view_arguments(
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
        if not is_admin_of(current_user, project):
            next_page = reverse("project", kwargs={"project_name": project_name})
            msg = "You have tried to view a restricted resource for this project.  Please consider joining."
            messages.add_message(request, messages.WARNING, msg)
            return HttpResponseRedirect(next_page)

    # get (or set) customization objects from the cache...
    session_key = get_key_from_request(request)
    cached_customizations_key = "{0}_customizations".format(session_key)
    model_customization = get_or_create_cached_object(request.session, cached_customizations_key,
        get_new_customizations,
        **{
            "project": project,
            "ontology": ontology,
            "model_proxy": model_proxy,
            # "key": model_proxy.name,
            "key": model_proxy.key,
        }
    )

    if current_user.is_authenticated():
        set_owner(model_customization, evaluate_lazy_object(current_user))

    # setup top-level form...
    # (subforms are handled by the load-on-demand paradigm)
    model_customization_form_class = MODEL_CUSTOMIZATION_FORM_MAP["form_class"]
    model_customization_form = model_customization_form_class(
        instance=model_customization,
        form_name=MODEL_CUSTOMIZATION_FORM_MAP["form_name"].format(safe_key=model_customization.key.replace('-', '_')),
        scope_prefix=MODEL_CUSTOMIZATION_FORM_MAP["form_scope_prefix"],
        # prefix=?!?
    )

    # work out various paths, so that ng can reload things as needed...
    view_url_dirname = request.path.rsplit('/', 1)[0]
    api_url_dirname = reverse("customization-list").rsplit('/', 1)[0]

    # gather all the extra information required by the template...
    template_context = {
        "project": project,
        "ontology": ontology,
        "proxy": model_proxy,
        "view_url_dirname": view_url_dirname,
        "api_url_dirname": api_url_dirname,
        "session_key": session_key,
        "customization": model_customization,
        "form": model_customization_form,
    }
    return render_to_response('questionnaire/q_customize.html', template_context, context_instance=context)


@redirect_legacy_projects
def q_customize_existing(request, project_name=None, ontology_key=None, document_type=None, customization_name=None):

    # save any request parameters...
    # (in case of redirection)
    context = add_parameters_to_context(request)

    # check the arguments...
    validity, project, ontology, model_proxy, msg = validate_view_arguments(
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
        if not is_admin_of(current_user, project):
            next_page = reverse("project", kwargs={"project_name": project_name})
            msg = "You have tried to view a restricted resource for this project.  Please consider joining."
            messages.add_message(request, messages.WARNING, msg)
            return HttpResponseRedirect(next_page)

    # get (or set) customization objects from the cache...
    # note that unlike in "q_customize_new" above, this bit is enclosed in a try/catch block
    # this is to deal w/ the possibility of an invalid customization_name
    try:
        session_key = get_key_from_request(request)
        cached_customizations_key = "{0}_customizations".format(session_key)
        model_customization = get_or_create_cached_object(request.session, cached_customizations_key,
            get_existing_customizations,
            **{
                "project": project,
                "ontology": ontology,
                "model_proxy": model_proxy,
                "customization_name": customization_name,
            }
        )
    except ObjectDoesNotExist:
        msg = "Cannot find the customization '{0}' for that project/ontology/model combination.".format(
            customization_name)
        return q_error(request, msg)

    # setup top-level form...
    # (subforms are handled by the load-on-demand paradigm)
    model_customization_form_class = MODEL_CUSTOMIZATION_FORM_MAP["form_class"]
    model_customization_form = model_customization_form_class(
        instance=model_customization,
        form_name=MODEL_CUSTOMIZATION_FORM_MAP["form_name"].format(safe_key=model_customization.key.replace('-', '_')),
        scope_prefix=MODEL_CUSTOMIZATION_FORM_MAP["form_scope_prefix"],
        # prefix=?!?
    )

    # work out various paths, so that ng can reload things as needed...
    view_url_dirname = request.path.rsplit('/', 2)[0]
    api_url_dirname = reverse("customization-detail", kwargs={"pk": model_customization.pk}).rsplit('/', 2)[0]

    # gather all the extra information required by the template...
    template_context = {
        "project": project,
        "ontology": ontology,
        "proxy": model_proxy,
        "view_url_dirname": view_url_dirname,
        "api_url_dirname": api_url_dirname,
        "session_key": session_key,
        "customization": model_customization,
        "form": model_customization_form,
    }
    return render_to_response('questionnaire/q_customize.html', template_context, context_instance=context)
