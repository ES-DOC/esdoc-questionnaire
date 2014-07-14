
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

def questionnaire_help(request):

    # gather all the extra information required by the template
    dict = {
        "site"                  : get_current_site(request),
        "questionnaire_version" : get_version(),
    }

    return render_to_response('questionnaire/questionnaire_help.html', dict, context_instance=RequestContext(request))
