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

from django.template import RequestContext
from django.http import HttpResponse
from django.shortcuts import loader
from django.utils.translation import ugettext_lazy as _



def q_error(request, error_msg="", status_code=400):

    # (note that error_msg can have embedded HTML tags)
    #  print error_msg

    # gather all the extra information required by the template
    _dict = {
        "error_msg": error_msg,
        "status_code": status_code,
    }

    template = loader.get_template('questionnaire/q_error.html')
    context = RequestContext(request, _dict)
    response = HttpResponse(template.render(context), status=status_code)

    return response


# def q_400(request):
#     error_msg = "bad request"
#     response = q_error(request, error_msg=error_msg, status_code=400)
#     return response
#
# def q_403(request):
#     error_msg = "permission denied"
#     response = q_error(request, error_msg=error_msg, status_code=403)
#     return response

def q_404(request):

    template = loader.get_template('questionnaire/q_404.html')
    context = RequestContext(request)
    response = HttpResponse(template.render(context), status=404)

    return response

def q_500(request):

    template = loader.get_template('questionnaire/q_500.html')
    context = RequestContext(request)
    response = HttpResponse(template.render(context), status=500)

    return response


