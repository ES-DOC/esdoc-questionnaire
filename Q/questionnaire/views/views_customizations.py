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
from Q.questionnaire.forms.forms_customize_models import QModelCustomizationForm
from Q.questionnaire.models.models_customizations import get_new_customizations, get_existing_customizations, set_owner
from Q.questionnaire.views.views_legacy import redirect_legacy_projects
from Q.questionnaire.views.views_base import add_parameters_to_context, validate_view_arguments, get_key_from_request, get_or_create_cached_object
from Q.questionnaire.views.views_errors import q_error

MODEL_CUSTOMIZATION_FORM_MAP = {
    # map of various useful bits of info needed to (re)create forms
    # strictly speaking, this isn't needed for the top-level view...
    # but a similar method is used for the section views (see "views_services_load_section.py")...
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
            next_page = "/login/?next=%s" % request.path
            return HttpResponseRedirect(next_page)
        if not is_admin_of(current_user, project):
            next_page = "/%s/" % project_name
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
            "key": model_proxy.name,
        }
    )
    model_customization_key = model_customization.get_key()

    if current_user.is_authenticated():
        set_owner(model_customization, current_user)

    # I generate the model_customization_form at this top-level
    # all other forms are generated as needed via the "load_section" view
    # which is called by the "section" directive according to the load-on-demand paradigm
    model_customization_form_class = MODEL_CUSTOMIZATION_FORM_MAP["form_class"]
    model_customization_form = model_customization_form_class(
        instance=model_customization,
        form_name=MODEL_CUSTOMIZATION_FORM_MAP["form_name"].format(safe_key=model_customization_key.replace('-', '_')),
        # prefix=?!?
        scope_prefix=MODEL_CUSTOMIZATION_FORM_MAP["form_scope_prefix"],
    )

    # work out the various paths,
    # so that ng can reload things as needed
    view_url = request.path
    view_url_sections = [section for section in view_url.split('/') if section]
    view_url_dirname = '/'.join(view_url_sections[:])
    api_url = reverse("customization-list", kwargs={})
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
        "customization": model_customization,
        "form": model_customization_form,
    }

    return render_to_response('questionnaire/q_customize.html', _dict, context_instance=context)


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
            next_page = "/login/?next=%s" % request.path
            return HttpResponseRedirect(next_page)
        if not is_admin_of(current_user, project):
            next_page = "/%s/" % project_name
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
        msg = "Cannot find the customization '{0}' for that project/ontology/model combination.".format(customization_name)
        return q_error(request, msg)
    model_customization_key = model_customization.get_key()

    # I generate the model_customization_form at this top-level
    # all other forms are generated as needed via the "load_section" view
    # which is called by the "section" directive according to the load-on-demand paradigm
    model_customization_form_class = MODEL_CUSTOMIZATION_FORM_MAP["form_class"]
    model_customization_form = model_customization_form_class(
        instance=model_customization,
        form_name=MODEL_CUSTOMIZATION_FORM_MAP["form_name"].format(safe_key=model_customization_key.replace('-', '_')),
        # prefix=?!?
        scope_prefix=MODEL_CUSTOMIZATION_FORM_MAP["form_scope_prefix"],
    )

    # work out the various paths,
    # so that ng can reload things as needed
    # (notice these are slightly different than in "q_customize_new" above
    view_url = request.path
    view_url_sections = [section for section in view_url.split('/') if section]
    view_url_dirname = '/'.join(view_url_sections[:-1])
    api_url = reverse("customization-detail", kwargs={"pk": model_customization.pk})
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
        "customization": model_customization,
        "form": model_customization_form,
    }

    return render_to_response('questionnaire/q_customize.html', _dict, context_instance=context)

