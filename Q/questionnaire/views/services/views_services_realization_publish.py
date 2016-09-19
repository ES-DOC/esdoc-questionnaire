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

from Q.questionnaire.models import QModel, QPublication
from Q.questionnaire.views.services.views_services_base import validate_request
from Q.questionnaire.q_utils import QError

def q_realization_publish(request):
    import ipdb; ipdb.set_trace()
    valid_request, msg = validate_request(request)
    if not valid_request:
        return HttpResponseForbidden(msg)

    realization_model_id = request.POST.get("document_id")
    try:
        realization = QModel.objects.get(pk=realization_model_id)
    except QModel.DoesNotExist:
        msg = "unable to locate document with id={0}".format(realization_model_id)
        return HttpResponseBadRequest(msg)
    # I AM HERE
    return JsonResponse({"hello": "world"})
