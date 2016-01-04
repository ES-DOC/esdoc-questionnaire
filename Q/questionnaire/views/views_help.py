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

from django.shortcuts import render_to_response

from Q.questionnaire.views.views_base import add_parameters_to_context

def q_help(request):

    # TODO: THIS SHOULD REDIRECT TO EXTERNAL DOCUMENTATION
    context = add_parameters_to_context(request)

    # gather all the extra information required by the template
    _dict = {
    }

    return render_to_response('questionnaire/q_help.html', _dict, context_instance=context)

