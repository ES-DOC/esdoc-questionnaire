####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.http import HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages


from Q.questionnaire.models.models_projects import QProject
from Q.questionnaire.models.models_users import project_join, is_pending_of, is_admin_of
from Q.questionnaire.serializers.serializers_projects import QProjectUserSerializer
from Q.questionnaire.views.services.views_services_base import validate_request

def q_project_add_member(request, project_name=None):
    """
    approve a project join request
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

    if not is_admin_of(request.user, project):
        msg = u"This user has not requested to join this project"
        return HttpResponseBadRequest(msg)

    if not is_pending_of(user, project):
        msg = u"This user has not requested to join this project"
        return HttpResponseBadRequest(msg)

    if project_join(project, user, site=request.current_site):
        serialized_user = QProjectUserSerializer(user).data
        return JsonResponse(serialized_user)
    else:
        msg = "Error adding user to project."
        messages.add_message(request, messages.ERROR, msg)
        return JsonResponse({"msg": msg})
