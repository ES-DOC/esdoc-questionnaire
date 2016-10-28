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
from Q.questionnaire.views.views_legacy import redirect_legacy_projects
from Q.questionnaire.views.views_errors import q_error
from Q.questionnaire.models.models_users import is_pending_of, is_member_of, is_user_of, is_admin_of
from Q.questionnaire.models.models_projects import QProject


@redirect_legacy_projects
def q_project(request, project_name=None):

    context = add_parameters_to_context(request)

    try:
        project = QProject.objects.get(name=project_name)
    except QProject.DoesNotExist:
        if not project_name:
            msg = u"Please specify a project name."
        else:
            msg = u"Unable to locate project '%s'" % (project_name)
        return q_error(request, error_msg=msg)
    if not project.is_active:
        msg = u"This project has been disabled."
        return q_error(request, error_msg=msg)

    # work out user roles...
    project_authenticated = project.authenticated
    current_user = request.user
    can_view = True  # is_member_of(current_user, project) or not project_authenticated
    can_edit = not project_authenticated or (is_user_of(current_user, project) or is_admin_of(current_user, project))
    can_customize = not project_authenticated or is_admin_of(current_user, project)
    can_join = current_user.is_authenticated() and not (is_member_of(current_user, project) or is_user_of(current_user, project) or is_admin_of(current_user, project))
    can_delete = is_admin_of(current_user, project)

    # gather all the extra information required by the template
    _dict = {
        "project": project,
        "can_customize": can_customize,
        "can_edit": can_edit,
        "can_view": can_view,
        "can_join": can_join,
        "can_delete": can_delete,
    }

    return render_to_response('questionnaire/q_project.html', _dict, context_instance=context)

