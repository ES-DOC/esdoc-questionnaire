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
from django.http import HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from uuid import uuid4

from Q.questionnaire.models.models_ontologies import QOntology
from Q.questionnaire.models.models_projects import QProject
from Q.questionnaire.models.models_proxies import QModelProxy
from Q.questionnaire.models.models_realizations import QModelRealization, get_new_realizations, serialize_realizations, import_realizations, set_owner
from Q.questionnaire.models.models_users import is_admin_of
from Q.questionnaire.serializers.serializers_realizations import QModelRealizationSerializer
from Q.questionnaire.views.services.views_services_base import validate_request
from Q.questionnaire.q_utils import QError

from pyesdoc.ontologies.cim.v2 import *
from pyesdoc import decode, encode


import json


def q_realization_import(request):

    valid_request, msg = validate_request(request)
    if not valid_request:
        return HttpResponseForbidden(msg)

    project_id = request.POST.get("project_id")
    document_content = request.POST.get("document_content")
    realization_type = request.POST.get("document_type")
    realization_copy = request.POST.get("document_copy") == "true"

    try:
        project = QProject.objects.get(pk=project_id)
    except QProject.DoesNotExist:
        msg = "Error importing document.  Cannot find an appropriate project."
        messages.add_message(request, messages.ERROR, msg)
        raise QError(msg)
    current_user = request.user
    assert is_admin_of(current_user, project), "User '{0}' does not have the authority to import a document to the '{1}' project".format(current_user, project)

    try:
        # originally I thought I would have to convert to pyesdoc and then QModelRealization
        # but I work directly via JSON instead
        document_json = json.loads(document_content)
    except Exception as e:
        msg = "Error importing document: {0}.".format(e.message)
        messages.add_message(request, messages.ERROR, msg)
        raise QError(e.message)

    document_info = document_json.get("meta")
    document_guid = document_info["id"]
    document_type = document_info["type"]
    # TODO: UN-COMMENT OUT THIS SECTION
    if document_type != realization_type:
        msg = "Error importing document.  It is not of type '{0}'.".format(realization_type.split('.')[-1])
        messages.add_message(request, messages.ERROR, msg)
        raise QError(msg)
    if realization_copy and QModelRealization.objects.filter(guid=document_guid).count():
        msg = "Error importing document.  Cannot copy document; There is already a document with the same id."
        messages.add_message(request, messages.ERROR, msg)
        raise QError(msg)

    document_type_ontology_name, document_type_ontology_version, document_type_proxy_package, document_type_proxy_name = document_type.split('.')
    document_ontology = QOntology.objects.has_key("{0}_{1}".format(document_type_ontology_name, document_type_ontology_version))
    if not document_ontology:
        msg = "Error importing document.  Cannot find a suitable ontology."
        messages.add_message(request, messages.ERROR, msg)
        raise QError(msg)
    try:
        document_proxy = QModelProxy.objects.get(
            is_document=True,
            ontology=document_ontology,
            package__iexact=document_type_proxy_package,
            name__iexact=document_type_proxy_name,
        )
    except QModelProxy.DoesNotExist:
        msg = "Error importing document.  Cannot find a suitable proxy."
        messages.add_message(request, messages.ERROR, msg)
        raise QError(msg)

    new_realizations = get_new_realizations(
        project=project,
        ontology=document_ontology,
        model_proxy=document_proxy,
    )
    new_realizations.is_root = True  # TODO: COME UP W/ A BETTER WAY OF DEALING W/ "is_root"
    set_owner(new_realizations, current_user)
    serialized_new_realization = serialize_realizations(new_realizations)
    import ipdb; ipdb.set_trace()
    realizations_to_import = import_realizations(
        source_realization=document_json,
        target_realization=serialized_new_realization,
        copy_realizations=realization_copy,
    )

    realizations_to_import_serializer = QModelRealizationSerializer(data=realizations_to_import)
    if realizations_to_import_serializer.is_valid():
        saved_realizations = realizations_to_import_serializer.save()
        msg = "Successfully imported document."
        messages.add_message(request, messages.SUCCESS, msg)
    else:
        msg = "Error importing document."
        messages.add_message(request, messages.ERROR, msg)

    return JsonResponse({"msg": msg})
