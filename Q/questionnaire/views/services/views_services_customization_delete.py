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

from Q.questionnaire.views.services.views_services_base import validate_request
from Q.questionnaire.models.models_customizations import QModelCustomization


def q_customization_delete(request):

    valid_request, msg = validate_request(request)
    if not valid_request:
        return HttpResponseForbidden(msg)

    customization_id = request.POST.get("customization_id")
    try:
        customization = QModelCustomization.objects.get(id=customization_id)
    except QModelCustomization.DoesNotExist:
        msg = u"Unable to locate customization w/ id '%s'" % customization_id
        return HttpResponseBadRequest(msg)

    if customization.is_default:
        msg = u"You cannot delete the default customization."
        return HttpResponseBadRequest(msg)

    customization.delete()

    try:
        customization.refresh_from_db()
        msg = "Error deleting customization"
        messages.add_message(request, messages.ERROR, msg)
    except QModelCustomization.DoesNotExist:
        msg = "You have successfully deleted this customization."
        messages.add_message(request, messages.INFO, msg)

    return JsonResponse({"msg": msg})