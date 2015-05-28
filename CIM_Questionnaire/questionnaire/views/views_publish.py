####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2014 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"
__date__ = "Dec 01, 2014 3:00:00 PM"

"""
.. module:: views_publish

tries to publish document
"""

from django.core.cache import get_cache
from django.http import HttpResponse

from CIM_Questionnaire.questionnaire.views.views_base import get_key_from_request
from CIM_Questionnaire.questionnaire.utils import QuestionnaireError


def api_publish(request, **kwargs):

    instance_key = get_key_from_request(request)

    cache = get_cache("default")
    cached_realization_set_key = u"%s_realization_set" % instance_key
    realization_set = cache.get(cached_realization_set_key)

    if not realization_set:
        raise QuestionnaireError("api_publish unable to find realization_set; are you running it outside of an existing session?")

    realizations = realization_set["models"]
    root_realization = realizations[0].get_root()

    if root_realization.is_complete():
        root_realization.publish(force_save=True)
        status = 200
        msg = "successfully published document"
    else:
        # okay, I'm overloading things a bit here...
        # the problem is that if I actually send a "400" code, then AJAX (correctly) interprets that as an error
        # and all sorts of problems ensure
        # instead I can still treat it as a success - albeit a "202" success where "The request has been accepted for processing, but the processing has not been completed." [http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html]
        # then in the success handler of the AJAX call, I can just check for status_code != 200
        status = 202
        msg = "unable to publish document"

    response = HttpResponse(status=status)
    response["msg"] = msg
    return response
