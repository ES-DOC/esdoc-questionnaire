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

from django.http import HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from django.contrib import messages

from Q.questionnaire.models.models_realizations import get_model_realization_by_fn, get_property_realization_by_fn
from Q.questionnaire.views.views_base import get_key_from_request, get_cached_object
from Q.questionnaire.views.services.views_services_base import validate_request
from Q.questionnaire.q_utils import QError

# this removes the specified realization [model] from the cached realization [property]
# strictly speaking, this isn't necessary b/c the JSON object on the client will replace that cache upon serialization
# however, this does provide an end point for "q_ng_editor.js#remove_relationship_value_aux", which has the effect of
# refreshing the display after "q_ng_editor.js#remove_relationship_value" has already removed the appropriate JSON bit
# and, anyway, it follows the same logic as "q_realization_add_relationship_value"


def q_realization_remove_relationship_value(request):
    valid_request, msg = validate_request(request)
    if not valid_request:
        return HttpResponseForbidden(msg)

    target_index = int(request.POST.get("target_index"))
    property_key = request.POST.get("key")

    session_key = get_key_from_request(request)
    cached_realizations_key = "{0}_realizations".format(session_key)

    cached_realizations = get_cached_object(request.session, cached_realizations_key)
    if not cached_realizations:
        msg = "unable to locate cached_realizations"
        raise QError(msg)

    property = get_property_realization_by_fn(
        lambda r: r.get_key() == property_key,
        cached_realizations
    )
    if not property:
        raise QError("unable to find property w/ key='{0}'".format(property_key))

    # remove the model...
    try:
        target_to_remove = property.relationship_values(manager="allow_unsaved_relationship_values_manager").all()[target_index]
        property.relationship_values(manager="allow_unsaved_relationship_values_manager").remove_potentially_unsaved(target_to_remove)
        if target_to_remove.is_existing():
            target_to_remove.delete()
    except IndexError:
        raise QError("unable to find target of {0} at index {1}".format(property, target_index))

    # re-cache the changed realizations...
    request.session[cached_realizations_key] = cached_realizations

    # and return a success msg...
    # TODO: WHY DOESN'T THIS MSG DISPLAY IMMEDIATELY?
    msg = "Successfully removed object"
    messages.add_message(request, messages.SUCCESS, msg)
    return JsonResponse({"msg": msg})