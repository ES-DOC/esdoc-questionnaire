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
.. module:: views_categories


"""

import json
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.template.context import RequestContext
from django.contrib.sites.models import get_current_site

from CIM_Questionnaire.questionnaire.forms.forms_customize_categories import TagTypes, MetadataStandardCategoryCustomizerForm, MetadataScientificCategoryCustomizerForm
from CIM_Questionnaire.questionnaire.utils import get_data_from_form, QuestionnaireError


def remove_prefixes(old_dict):
    """
    remove prefixes from a dictionary
    required b/c the incoming AJAX data comes from a form w/in a formset (and hence w/ a prefix)
    while the data required to create a single form w/out a prefix
    :param old_dict:
    :return:
    """
    new_dict = {}
    for key, value in old_dict.iteritems():
        new_dict[key.rsplit('-')[-1]] = value
    return new_dict


def api_customize_category(request, category_type, **kwargs):

    if category_type == TagTypes.STANDARD.getName():
        form_class = MetadataStandardCategoryCustomizerForm
    elif category_type == TagTypes.SCIENTIFIC.getName():
        form_class = MetadataScientificCategoryCustomizerForm
    else:
        msg = "unknown tag type: %s" % category_type
        raise QuestionnaireError(msg)

    if request.method == "GET":
        initial_data = remove_prefixes(request.GET.dict())
        form = form_class(initial=initial_data)

        status = 200
        msg = None

    else:  # request.method == "POST"
        data = request.POST.copy()
        form = form_class(data)
        if form.is_valid():

            status = 200
            msg = u"Successfully customized category."

            new_data = get_data_from_form(form, existing_data={
                "loaded": True,
                "key": form.cleaned_data["key"],  # cleaned_data["key"] would have been set by the clean fn which would have been called as part of is_valid above
            })

            json_data = json.dumps(new_data)
            response = HttpResponse(json_data, content_type="text/html", status=status)
            response["msg"] = msg
            return response

        else:

            # okay, I'm overloading things a bit here
            # the problem is that if I actually send a "400" code, then AJAX (correctly) interprets that as an error
            # and all sorts of problems ensure
            # instead I can still treat it as a success - albeit a "202" success where "The request has been accepted for processing, but the processing has not been completed." [http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html]
            # then in the success handler of the AJAX call, I can just check for status_code != 200
            status = 202
            msg = u"Error customizing category."

    _dict = {
        "form": form,
        "site": get_current_site(request),
    }

    # csrf ?

    rendered_form = render_to_string("questionnaire/questionnaire_category.html", dictionary=_dict, context_instance=RequestContext(request))
    response = HttpResponse(rendered_form, content_type="text/html", status=status)
    response["msg"] = msg
    return response
