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


from Q.questionnaire.models.models_projects import QProject
from Q.questionnaire.models.models_users import is_pending_of, is_member_of, is_user_of, is_admin_of

def q_test(request):

    context = add_parameters_to_context(request)

    project = QProject.objects.get(pk=1)

    # work out user roles...
    project_authenticated = project.authenticated
    current_user = request.user
    is_admin = is_admin_of(current_user, project)
    is_user = is_user_of(current_user, project)
    is_member = is_member_of(current_user, project)
    is_pending = is_pending_of(current_user, project)
    can_view = True
    can_edit = not project_authenticated or (is_user or is_admin)
    can_customize = not project_authenticated or is_admin
    can_join = current_user.is_authenticated() and not (is_member or is_user or is_admin)
    can_delete = is_admin
    can_manage = is_admin
    can_publish = is_user or is_admin

    # gather all the extra information required by the template
    template_context = {
        "project": project,
        "can_customize": can_customize,
        "can_edit": can_edit,
        "can_view": can_view,
        "can_join": can_join,
        "can_delete": can_delete,
        "can_manage": can_manage,
        "can_publish": can_publish,
    }

    return render_to_response('questionnaire/q_test.html', template_context, context_instance=context)
