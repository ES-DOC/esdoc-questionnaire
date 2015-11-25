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
# from Q.questionnaire.models.models_realizations import get_new_realization_set
from Q.questionnaire.models.models_customizations import QModelCustomization, get_existing_customization_set
from Q.questionnaire.views.views_base import add_parameters_to_context, get_key_from_request, get_or_create_cached_object, validate_view_arguments as validate_view_arguments_base
from Q.questionnaire.views.views_errors import q_error

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
            default=True,
        )
    except QModelCustomization.DoesNotExist:
        msg = "There is no default customization associated with this project/model/ontology."
        validity = False
        return validity, project, ontology, proxy, customization, msg

    return validity, project, ontology, proxy, customization, msg

def q_model_new(request, project_name=None, ontology_key=None, document_type=None):

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

    # get the set of vocabularies that apply to this project/ontology/proxy...
    vocabularies = customization.vocabularies.all()

    # get (or set) objects from the cache...
    session_key = get_key_from_request(request)
    cached_customization_set_key = "{0}_customization_set".format(session_key)
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
    # realization_set = get_or_create_cached_object(request.session, cached_realization_set_key,
    #     get_new_realization_set,
    #     **{
    #         "project": project,
    #         "ontology": ontology,
    #         "proxy": proxy,
    #         "vocabularies": vocabularies,
    #     }
    # )

    # gather all the extra information required by the template
    _dict = {
        "session_key": session_key,
        "ontology": ontology,
        "proxy": proxy,
        "project": project,
        "vocabularies": vocabularies,
    }

    return render_to_response('questionnaire/q_edit.html', _dict, context_instance=context)


