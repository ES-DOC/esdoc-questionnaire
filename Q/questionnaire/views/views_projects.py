####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response


from Q.questionnaire.forms.forms_projects import QProjectForm
from Q.questionnaire.models.models_projects import QProject
from Q.questionnaire.models.models_users import is_pending_of, is_member_of, is_user_of, is_admin_of
from Q.questionnaire.views.views_base import add_parameters_to_context
from Q.questionnaire.views.views_errors import q_error
from Q.questionnaire.views.views_legacy import redirect_legacy_projects


@redirect_legacy_projects
def q_project(request, project_name=None):

    context = add_parameters_to_context(request)

    try:
        project = QProject.objects.get(name=project_name)
    except QProject.DoesNotExist:
        if not project_name:
            msg = u"Please specify a project name."
        else:
            msg = u"Unable to locate project '{0}'".format(project_name)
        return q_error(request, error_msg=msg)
    if not project.is_active:
        msg = u"This project has been disabled."
        return q_error(request, error_msg=msg)

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

    # gather all the extra information required by the template
    template_context = {
        "project": project,
        "can_customize": can_customize,
        "can_edit": can_edit,
        "can_view": can_view,
        "can_join": can_join,
        "can_delete": can_delete,
        "can_manage": can_manage,
    }

    return render_to_response('questionnaire/q_project.html', template_context, context_instance=context)


def q_project_manage(request, project_name=None):

    context = add_parameters_to_context(request)

    try:
        project = QProject.objects.get(name=project_name)
    except QProject.DoesNotExist:
        if not project_name:
            msg = u"Please specify a project name."
        else:
            msg = u"Unable to locate project '{0}'".format(project_name)
        return q_error(request, error_msg=msg)
    if not project.is_active:
        msg = u"This project has been disabled."
        return q_error(request, error_msg=msg)

    # work out user roles...
    current_user = request.user
    if not is_admin_of(current_user, project):
        next_page = reverse("project", kwargs={"project_name": project_name})
        msg = "You do not have permission to modify this project's settings."
        messages.add_message(request, messages.WARNING, msg)
        # TODO: CAN HttpResponseRedirect TAKE "context" ?
        return HttpResponseRedirect(next_page)

    project_management_form = QProjectForm(
        instance=project,
        form_name="project_management_form",
        scope_prefix="project_controller.project",
    )

    # gather all the extra information required by the template
    template_context = {
        "project": project,
        "form": project_management_form,
    }

    return render_to_response('questionnaire/q_project_manage.html', template_context, context_instance=context)
