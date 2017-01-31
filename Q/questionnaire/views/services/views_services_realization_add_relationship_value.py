####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse

from Q.questionnaire.q_fields import allow_unsaved_fk
from Q.questionnaire.models.models_proxies import QModelProxy
from Q.questionnaire.models.models_realizations import QModelRealization, get_new_realizations, serialize_realizations, get_property_realization_by_key
from Q.questionnaire.models.models_users import is_member_of
from Q.questionnaire.views.services.views_services_base import validate_request
from Q.questionnaire.views.views_base import get_key_from_request, get_cached_object


def q_realization_add_relationship_value(request):

    # check the request was valid...
    valid_request, msg = validate_request(request)
    if not valid_request:
        return HttpResponseForbidden(msg)

    target_proxy_id = request.POST.get("target_proxy_id")
    property_key = request.POST.get("key")

    session_key = get_key_from_request(request)
    cached_realizations_key = "{0}_realizations".format(session_key)

    cached_realizations = get_cached_object(request.session, cached_realizations_key)
    if not cached_realizations:
        msg = "unable to locate cached_realizations"
        return HttpResponseBadRequest(msg)

    # do some sanity checks...

    # check the realization to add to exists...
    property_realization = get_property_realization_by_key(property_key, cached_realizations)
    if not property_realization:
        msg = "unable to find a QPropertyRealization with a key of '{0}'".format(property_key)
        return HttpResponseBadRequest(msg)

    # check that the target to add exists...
    try:
        target_proxy = QModelProxy.objects.get(id=target_proxy_id)
    except QModelProxy.DoesNotExist:
        msg = "unable to find a QModelProxy with an id of '{0}'".format(target_proxy_id)
        return HttpResponseBadRequest(msg)

    # check that it makes sense to add this target...
    if target_proxy not in property_realization.proxy.relationship_target_models.all():
        msg = "you are trying to add the wrong type of QModelRealization to this QPropertyRealization"
        return HttpResponseBadRequest(msg)
    if (not property_realization.is_infinite) and (property_realization.relationship_values(manager="allow_unsaved_relationship_values_manager").count() >= property_realization.cardinality_max):
        msg = "you have already added the maximum amount of QModelRealizations to this QPropertyRealization"
        return HttpResponseBadRequest(msg)

    # check the user has permission to modify the realization...
    current_user = request.user
    project = cached_realizations.project
    if project.authenticated:
        if not current_user.is_authenticated() or not is_member_of(current_user, project):
            msg = "{0} does not have permission to modify a realization".format(current_user)
            return HttpResponseForbidden(msg)

    # ...okay, sanity checks are over

    # now create the model...
    new_model_realization = get_new_realizations(
        project=project,
        ontology=target_proxy.ontology,
        model_proxy=target_proxy,
        key=target_proxy.name,
    )
    # now add the model...
    property_realization.relationship_values(manager="allow_unsaved_relationship_values_manager").add_potentially_unsaved(new_model_realization)
    with allow_unsaved_fk(QModelRealization, ["relationship_property"]):
        # the custom manager above ("allow_unsaved_relationship_values_manager") lets me cope w/ an unsaved m2m relationship - it is what I ought to use
        # however, some fns ("QRealization.get_root_realization") needs access to the reverse of that relationship; hence this extra bit of code
        new_model_realization.relationship_property = property_realization
    request.session[cached_realizations_key] = cached_realizations

    # finally return a serialized version of that model...
    new_model_realization_serialization = serialize_realizations(new_model_realization)
    return JsonResponse(new_model_realization_serialization)
