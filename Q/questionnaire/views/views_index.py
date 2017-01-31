####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.shortcuts import render_to_response
from Q.questionnaire.views.views_base import add_parameters_to_context


def q_index(request):

    context = add_parameters_to_context(request)

    # gather all the extra information required by the template
    template_context = {}
    return render_to_response('questionnaire/q_index.html', template_context, context_instance=context)


def q_test(request):

    context = add_parameters_to_context(request)

    # gather all the extra information required by the template
    template_context = {}
    return render_to_response('questionnaire/q_test.html', template_context, context_instance=context)
