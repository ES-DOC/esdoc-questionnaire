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
from django.template.context import RequestContext

from Q.questionnaire.models.models_proxies import QModelProxy
from Q.questionnaire.models.models_realizations import QModel, get_new_realizations, get_model_realization_by_fn, get_property_realization_by_fn, serialize_new_realizations, recurse_through_realizations, RealizationTypes
from Q.questionnaire.models.models_realizations import get_realization_path, walk_realization_path
from Q.questionnaire.views.views_base import get_key_from_request, get_cached_object
from Q.questionnaire.views.services.views_services_base import validate_request
from Q.questionnaire.q_fields import allow_unsaved_fk
from Q.questionnaire.q_utils import QError

# the purpose of this service view is 2-fold...
# 1st it creates a new realization and adds it to the appropriate realizations already cached on the server
# 2nd it creates a JSON serialization of that realization to append to the JSON object already loaded on the client


def q_realization_add_relationship_value(request):
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
        raise QError(msg)

    property = get_property_realization_by_fn(
        lambda r: r.get_key() == property_key,
        cached_realizations
    )
    if not property:
        raise QError("unable to find property w/ key='{0}'".format(property_key))

    target_proxy = QModelProxy.objects.get(id=target_proxy_id)
    new_model_realization = get_new_realizations(
        project=cached_realizations.project,
        ontology=cached_realizations.ontology,
        model_proxy=target_proxy,
        key=target_proxy.name,
    )

    # double-check that adding this model to this property makes sense...
    assert target_proxy in property.proxy.relationship_target_models.all()
    assert property.get_cardinality_max() == '*' or property.relationship_values(manager="allow_unsaved_relationship_values_manager").count() < int(property.get_cardinality_max())

    # add the model...
    property.relationship_values(manager="allow_unsaved_relationship_values_manager").add_potentially_unsaved(new_model_realization)
    with allow_unsaved_fk(QModel, ["relationship_property"]):
        # in theory, Django doesn't store unsaved relationship
        # the custom manager above gets around this for the m2m relationship (property to model) and it is what I ought to use
        # however, in order to work my way up the realization hierarchy I need access to the reverse of that relationship
        # which is a fk relationship; hence this extra bit of code (which only exists so that "model_realizations.py#QRealization.get_parent_model_realization" works)
        new_model_realization.relationship_property = property

    # re-cache the changed realizations...
    request.session[cached_realizations_key] = cached_realizations

    # and return a serialized version of that model...
    new_model_realization_serialization = serialize_new_realizations(new_model_realization)
    return JsonResponse(new_model_realization_serialization)