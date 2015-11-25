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

from Q.questionnaire.models.models_users import is_admin_of, is_user_of, is_member_of
from Q.questionnaire.forms.forms_customize_models import QModelCustomizationForm
from Q.questionnaire.models.models_customizations import get_new_customization_set, get_existing_customization_set
from Q.questionnaire.views.views_base import add_parameters_to_context, validate_view_arguments, get_key_from_request, get_or_create_cached_object
from Q.questionnaire.views.views_errors import q_error

def q_customize_new(request, project_name=None, ontology_key=None, document_type=None):

    # save any request parameters...
    # (in case of redirection)
    context = add_parameters_to_context(request)

    # check the arguments...
    validity, project, ontology, proxy, msg = validate_view_arguments(
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
        if not is_admin_of(current_user, project):
            next_page = "/%s/" % project_name
            msg = "You have tried to view a restricted resource for this project.  Please consider joining."
            messages.add_message(request, messages.WARNING, msg)
            return HttpResponseRedirect(next_page)

    # get the set of vocabularies that apply to this project/ontology/proxy...
    vocabularies = project.vocabularies.filter(document_type__iexact=document_type)

    # get (or set) customization objects from the cache...
    session_key = get_key_from_request(request)
    cached_customization_set_key = "{0}_customization_set".format(session_key)
    customization_set = get_or_create_cached_object(request.session, cached_customization_set_key,
        get_new_customization_set,
        **{
            "project": project,
            "ontology": ontology,
            "proxy": proxy,
            "vocabularies": vocabularies,
        }
    )

    model_customization = customization_set["model_customization"]

    # I am only generating the model_customization_form at this top-level
    # all other forms (and formsets) are genearted as needed via the "load_section" view
    # called by the "section" directive according to the load-on-demand paradigm
    model_customization_form = QModelCustomizationForm(
        instance=model_customization,
        form_name="model_customization_form",
        # prefix=?!?,
        scope_prefix="model_customization",
    )

    # else:  # request.method == "POST"
    #
    #     # IN THEORY, I NEVER ENTER THIS BRANCH B/C ALL FORM SUBMISSION IS DONE VIA REST / ANGULAR
    #     # BUT I'M KEEPING THIS CODE HERE IN-CASE I NEED TO REFER TO IT LATER
    #
    #     data = request.POST.copy()  # sometimes I need to alter the data for unloaded forms;
    #                                 # this cannot be done on the original (immutable) QueryDict
    #
    #     model_customization_form = QModelCustomizationForm(
    #         data,
    #         instance=customization_set["model_customization"],
    #         # prefix=?!?,
    #         scope_prefix="model_customization",
    #         form_name="model_customization_form",
    #     )
    #
    #     if model_customization_form.is_valid():
    #         customization = model_customization_form.save()
    #         messages.add_message(request, messages.SUCCESS, "Successfully saved customization '%s'." % customization.name)
    #         customize_existing_url = reverse("customize_existing", kwargs={
    #             "project_name": project_name,
    #             "ontology_key": ontology_key,
    #             "document_type": document_type,
    #             "customizer_name": customization.name,
    #         })
    #         return HttpResponseRedirect(customize_existing_url)
    #
    #     else:
    #
    #         messages.add_message(request, messages.ERROR, "Failed to save customization.")

    # work out the various paths,
    # so that angular can reload things as needed
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
        "ontology": ontology,
        "proxy": proxy,
        "project": project,
        "vocabularies": vocabularies,
        "customization": model_customization,
        "model_customization_form": model_customization_form,
    }

    return render_to_response('questionnaire/q_customize.html', _dict, context_instance=context)


def q_customize_existing(request, project_name=None, ontology_key=None, document_type=None, customization_name=None):

    # save any request parameters...
    # (in case of redirection)
    context = add_parameters_to_context(request)

    # check the arguments...
    validity, project, ontology, proxy, msg = validate_view_arguments(
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
        cached_customization_set_key = "{0}_customization_set".format(session_key)
        customization_set = get_or_create_cached_object(request.session, cached_customization_set_key,
            get_existing_customization_set,
            **{
                "project": project,
                "ontology": ontology,
                "proxy": proxy,
                "customization_name": customization_name,
            }
        )
    except ObjectDoesNotExist:
        msg = "Cannot find the customization '{0}' for that project/ontology/model combination.".format(customization_name)
        return q_error(request, msg)

    model_customization = customization_set["model_customization"]

    # I am only generating the model_customization_form at this top-level
    # all other forms (and formsets) are generated as needed via the "load_section" view
    # called by the "section" directive according to the load-on-demand paradigm
    model_customization_form = QModelCustomizationForm(
        instance=model_customization,
        form_name="model_customization_form",
        # prefix=?!?,
        scope_prefix="model_customization",
    )

    # work out the various paths,
    # so that angular can reload things as needed
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
        "ontology": ontology,
        "proxy": proxy,
        "project": project,
        "vocabularies": [v.vocabulary for v in customization_set["vocabulary_customizations"]],
        "customization": model_customization,
        "model_customization_form": model_customization_form,
    }

    return render_to_response('questionnaire/q_customize.html', _dict, context_instance=context)
