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
.. module:: views_inheritance

manipulates session variable storing which data to inherit
"""

from django.core.cache import get_cache
from django.http import HttpResponse

from CIM_Questionnaire.questionnaire.views.views_base import get_key_from_request
from CIM_Questionnaire.questionnaire.utils import QuestionnaireError


def get_cached_inheritance_data(instance_key):

    cache = get_cache("default")
    cached_inheritance_data_key = u"inheritance_%s" % instance_key

    inheritance_data = cache.get(cached_inheritance_data_key)

    return inheritance_data


def set_cached_inheritance_data(inheritance_data):

    instance_key = inheritance_data["instance_key"]

    cache = get_cache("default")
    cached_inheritance_data_key = u"inheritance_%s" % instance_key

    cache.set(cached_inheritance_data_key, inheritance_data)


def api_add_inheritance_data(request, **kwargs):

    if request.method != "POST":
        raise QuestionnaireError("api_add_inheritance_data can only accept POST requests")

    instance_key = get_key_from_request(request)

    existing_inheritance_data = get_cached_inheritance_data(instance_key)

    inheritance_data = dict(request.POST)
    # TODO: I HAVE NO IDEA WHY VALUES IN THE POST DICTIONARY ARE ALL LISTS?!?
    for k, v in inheritance_data.iteritems():
        if isinstance(v, list):
            inheritance_data[k] = v[0]

    if not existing_inheritance_data:

        set_cached_inheritance_data(inheritance_data)

    else:

        existing_inheritance_data.update(inheritance_data)
        set_cached_inheritance_data(existing_inheritance_data)

    response = HttpResponse(status=200)
    return response
