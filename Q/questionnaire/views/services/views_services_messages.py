####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"


from django.contrib.messages import get_messages
from django.http import HttpResponseForbidden, JsonResponse

def get_django_messages(request):
    """
    finds all pending Django messages and sticks them into a JSON array
    this in turn gets accessed by an Angular app which then uses
    JS (bootbox) to display them as pretty pop-up messages
    (see "check_msg" in "q_base.js")
    :param request:
    :return:
    """

    if not request.is_ajax():
        msg = "Attempt to call service view outside of AJAX."
        return HttpResponseForbidden(msg)

    # the very act of accessing these messages pops them off the message queue;
    # Yay Django!
    messages = get_messages(request)

    data = []
    for message in messages:
        data.append({
            "text": message.message,
            "status": message.tags,
        })

    return JsonResponse(data, safe=False)
