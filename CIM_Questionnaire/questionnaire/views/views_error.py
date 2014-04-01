
####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Sep 30, 2013 3:04:42 PM"

"""
.. module:: views

Summary of module goes here

"""

from questionnaire.views import *
from questionnaire.utils import get_version

from django.template import *
from django.shortcuts import *
from django.http import *

def questionnaire_error(request,error_msg="",status_code=200):

    print error_msg

    # (note that error_msg can have embedded HTML tags)

    # gather all the extra information required by the template
    dict = {
        "site"                  : get_current_site(request),
        "error_msg"             : error_msg,
        "status_code"           : status_code,
        "questionnaire_version" : get_version(),
    }

    template    = loader.get_template('questionnaire/questionnaire_error.html')
    context     = RequestContext(request,dict)
    response    = HttpResponse(template.render(context),status=status_code)

    return response
