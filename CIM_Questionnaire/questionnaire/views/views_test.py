
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
__date__ ="Dec 5, 2013 2:16:31 PM"

"""
.. module:: views_test

Summary of module goes here

"""

from django.contrib.sites.models import get_current_site
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.contrib import messages

from CIM_Questionnaire.questionnaire import get_version

def test(request):

    if request.method == "GET":
        pass
    else:
        pass

    # gather all the extra information required by the template
    dict = {
        "site" : get_current_site(request),
        "questionnaire_version" : get_version(),
        #"form" : form,
    }

    return render_to_response('questionnaire/questionnaire_test.html', dict, context_instance=RequestContext(request))
