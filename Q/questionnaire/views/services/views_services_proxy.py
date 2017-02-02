####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.http import HttpResponseBadRequest, HttpResponseForbidden, HttpResponse, JsonResponse
from Q.questionnaire.views.services.views_services_base import validate_request
from urlparse import urlparse
import urllib2
import json

# list of domains the proxy will accept...
VALID_DOMAINS = [
    "api.es-doc.org",
]


# this view takes an $http call from the client and routes it through the server
# this bit of indirection is done to get around CORS issues
# TODO: IN THE LONG-TERM, THE ES-DOC DOMAINS SHOULD JUST BE OPENED UP TO THE QUESTIONNAIRE

def q_proxy(request):

    valid_request, msg = validate_request(request)
    if not valid_request:
        return HttpResponseForbidden(msg)

    url = request.POST.get("url")
    response_format = request.POST.get("response_format", "HTTP")

    if urlparse(url).netloc not in VALID_DOMAINS:
        return HttpResponseBadRequest("invalid proxy url '{0}'".format(url))

    try:
        response = urllib2.urlopen(url)
        content = response.read()
    except urllib2.URLError as e:
        return HttpResponseBadRequest("unable to reach url '{0}': {1}".format(url, e))

    if response_format.upper() == "HTTP":
        return HttpResponse(content)
    elif response_format.upper() == "JSON":
        json_content = json.loads(content)
        return JsonResponse(json_content)
    else:
        return HttpResponseBadRequest("unknown response_format: '{0}'".format(response_format))
