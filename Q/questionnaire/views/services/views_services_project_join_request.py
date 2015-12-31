####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"

from django.http import HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages

from Q.questionnaire.views.services.views_services_base import validate_request
from Q.questionnaire.models.models_projects import QProject
from Q.questionnaire.models.models_users import project_join_request, is_pending_of


def q_project_join_request(request, project_name=None):
    """
    processes a join request
    :param request:
    :param project_name:
    :return:
    """
    valid_request, msg = validate_request(request)
    if not valid_request:
        return HttpResponseForbidden(msg)

    try:
        project = QProject.objects.get(name=project_name)
    except QProject.DoesNotExist:
        msg = u"Unable to locate project '%s'" % project_name
        return HttpResponseBadRequest(msg)
    if not project.is_active:
        msg = u"This project has been disabled."
        return HttpResponseBadRequest(msg)

    user_id = request.POST.get("user_id")
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        msg = u"Unable to locate user"
        return HttpResponseBadRequest(msg)

    was_already_pending = False
    if is_pending_of(user, project):
        was_already_pending = True

    if project_join_request(project, user, site=request.current_site):
        msg = "Your request has been sent to the project administrator for review"
        if was_already_pending:
            msg += " again.<p><em>You have sent this request before.  Please contact the project administrator [<a href='mailto:{email}'>{email}</a>] if things are moving too slowly</em>.</p>".format(
                email=project.email
            )
        else:
            msg += "."
        messages.add_message(request, messages.INFO, msg)
    else:
        msg = "Error sending project join request."
        messages.add_message(request, messages.ERROR, msg)

    return JsonResponse({"msg": msg})
