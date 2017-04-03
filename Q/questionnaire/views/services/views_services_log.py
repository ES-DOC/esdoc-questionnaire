####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
import json

from Q.questionnaire.views.services.views_services_base import validate_request
from Q.questionnaire.q_utils import q_logger


# this view takes an $http call from the client w/ some message to output in the log

def q_log(request):

    valid_request, msg = validate_request(request)
    if not valid_request:
        return HttpResponseForbidden(msg)

    msg = request.POST.get("msg")

    try:
        q_logger.info(msg)
        return HttpResponse(msg)
    except Exception as e:
        return HttpResponseBadRequest(e.message)
