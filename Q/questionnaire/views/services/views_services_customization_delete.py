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
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from Q.questionnaire.models.models_customizations import QModelCustomization
from Q.questionnaire.models.models_users import is_admin_of
from Q.questionnaire.views.services.views_services_base import validate_request


def q_customization_delete(request):

    # check the request was valid...
    valid_request, msg = validate_request(request)
    if not valid_request:
        return HttpResponseForbidden(msg)

    # check the requested customization exists...
    customization_id = request.POST.get("customization_id")
    try:
        customization = QModelCustomization.objects.get(id=customization_id)
        project = customization.project
    except QModelCustomization.DoesNotExist:
        msg = u"Unable to locate customization w/ id '%s'" % customization_id
        return HttpResponseBadRequest(msg)

    # check the user has permission to delete the customization...
    current_user = request.user
    if project.authenticated:
        if not current_user.is_authenticated() or not is_admin_of(current_user, project):
            msg = "{0} does not have permission to delete {1}".format(current_user, customization)
            return HttpResponseForbidden(msg)

    # check the customization can be deleted...
    if customization.is_default:
        msg = u"You cannot delete the default customization."
        return HttpResponseBadRequest(msg)

    # delete it!
    customization.delete()

    # make sure the customization no loner exists...
    try:
        customization.refresh_from_db()
        msg = "Error deleting customization"
        messages.add_message(request, messages.ERROR, msg)
    except QModelCustomization.DoesNotExist:
        msg = "You have successfully deleted this customization."
        messages.add_message(request, messages.INFO, msg)

    return JsonResponse({"msg": msg})
