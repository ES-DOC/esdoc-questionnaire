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

from Q.questionnaire.models.models_realizations import get_property_realization_by_key
from Q.questionnaire.models.models_users import is_member_of
from Q.questionnaire.views.services.views_services_base import validate_request
from Q.questionnaire.views.views_base import get_key_from_request, get_cached_object


def q_realization_remove_relationship_value(request):

    # check the request was valid...
    valid_request, msg = validate_request(request)
    if not valid_request:
        return HttpResponseForbidden(msg)

    target_index = request.POST.get("target_index")
    target_key = request.POST.get("target_key")
    property_key = request.POST.get("key")

    session_key = get_key_from_request(request)
    cached_realizations_key = "{0}_realizations".format(session_key)

    cached_realizations = get_cached_object(request.session, cached_realizations_key)
    if not cached_realizations:
        msg = "unable to locate cached_realizations"
        return HttpResponseBadRequest(msg)

    # do some sanity checks...

    # check the realization to remove from exists...
    property_realization = get_property_realization_by_key(property_key, cached_realizations)
    if not property_realization:
        msg = "unable to find a QPropertyRealization with a key of '{0}'".format(property_key)
        return HttpResponseBadRequest(msg)

    # check that the target to remove exists...
    target_realizations = property_realization.relationship_values(manager="allow_unsaved_relationship_values_manager").filter_potentially_unsaved(key=target_key)
    if len(target_realizations) != 1:
        msg = "unable to find a QModelProxy with a key of '{0}'".format(target_key)
        return HttpResponseBadRequest(msg)
    target_realization = target_realizations[0]

    # check that it makes sense to remove this target...
    if property_realization.relationship_values(manager="allow_unsaved_relationship_values_manager").count() <= property_realization.cardinality_min:
        msg = "you have cannot remove this many QModelRealizations from this this QPropertyRealization"
        return HttpResponseBadRequest(msg)

    # check the user has permission to modify the realization...
    current_user = request.user
    project = cached_realizations.project
    if project.authenticated:
        if not current_user.is_authenticated() or not is_member_of(current_user, project):
            msg = "{0} does not have permission to modify a realization".format(current_user)
            return HttpResponseForbidden(msg)

    # ...okay, sanity checks are over

    # now remove the target...
    property_realization.relationship_values(manager="allow_unsaved_relationship_values_manager").remove_potentially_unsaved(target_realization)
    if target_realization.is_existing:
        target_realization.delete()
    request.session[cached_realizations_key] = cached_realizations

    # finally return a success msg...
    msg = "Successfully removed object"
    return JsonResponse({"msg": msg})
