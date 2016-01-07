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

from django.http import HttpResponseForbidden,HttpResponseBadRequest, JsonResponse
from django.contrib import messages

from Q.questionnaire.views.services.views_services_base import validate_request
# from Q.questionnaire.models.models_realizations import QModel
from Q.questionnaire.models.models_realizations_bak import MetadataModel


def q_document_publish(request):

    valid_request, msg = validate_request(request)
    if not valid_request:
        return HttpResponseForbidden(msg)

    model_id = request.POST.get("document_id")
    try:
        # model = QModel.objects.get(id=model_id)
        model = MetadataModel.objects.get(id=model_id)
    # except QModel.DoesNotExist:
    except MetadataModel.DoesNotExist:
        msg = u"Unable to locate model w/ id '%s'" % model_id
        return HttpResponseBadRequest(msg)

    # if not model.is_active:
    if not model.active:
        msg = u"This model has been disabled."
        return HttpResponseBadRequest(msg)
    if not model.is_document and model.is_root:
        msg = u"This model is not a root document."
        return HttpResponseBadRequest(msg)
    if not model.is_complete():
        msg = u"This model is incomplete."
        return HttpResponseBadRequest(msg)

    publication = model.publish(force_save=True)

    if publication:
        msg = "You have successfully published this document.  It should appear in the ES-DOC Archive within 3 hours."
        messages.add_message(request, messages.INFO, msg)

    else:
        msg = "Error publishing document."
        messages.add_message(request, messages.ERROR, msg)

    return JsonResponse({"msg": msg})
