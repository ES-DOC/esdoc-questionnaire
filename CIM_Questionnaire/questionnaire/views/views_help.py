
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

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.sites.models import get_current_site

from CIM_Questionnaire.questionnaire.models.metadata_authentication import is_user_of, is_admin_of
from CIM_Questionnaire.questionnaire.models.metadata_project import MetadataProject
from CIM_Questionnaire.questionnaire import get_version


def questionnaire_help(request):

    active_projects = MetadataProject.objects.filter(active=True)
    current_user = request.user
    can_edit = any([is_user_of(current_user, project) for project in active_projects])
    can_customize = any([is_admin_of(current_user, project) for project in active_projects])

    # gather all the extra information required by the template
    _dict = {
        "site": get_current_site(request),
        "can_edit": can_edit,
        "can_customize": can_customize,
        "questionnaire_version": get_version(),
    }

    return render_to_response('questionnaire/questionnaire_help.html', _dict, context_instance=RequestContext(request))
