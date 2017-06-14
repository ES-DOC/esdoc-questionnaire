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

from Q.questionnaire.models.models_ontologies import QOntology
from Q.questionnaire.models.models_projects import QProject
from Q.questionnaire.models.models_proxies import QModelProxy
from Q.questionnaire.models.models_realizations import QModelRealization, import_realization
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
        # originally I thought I would have to convert to pyesdoc and then QModelRealization
        # but I work directly via JSON instead
        document_json = json.loads(document_content)
    except Exception as e:
        msg = "Error importing document: {0}.".format(e.message)
        messages.add_message(request, messages.ERROR, msg)
        raise QError(e.message)

    try:
        project = QProject.objects.get(pk=project_id)
    except QProject.DoesNotExist:
        msg = "Error importing document.  Cannot find an appropriate project."
        messages.add_message(request, messages.ERROR, msg)
        raise QError(msg)

    document_info = document_json.pop("meta")
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

    import ipdb; ipdb.set_trace()
    imported_realization = import_realization(document_proxy, document_json)
    # TODO: I AM HERE
    # TODO: TURN "pyesdoc JSON" INTO "QModelRealization"
    # TODO: CHANGE guids, owners, dates AS NEEDED
    # TODO: serialize to "djangorestframeework JSON"
    # TODO: save using djangorestframework methods

    msg = "hello world"
    messages.add_message(request, messages.INFO, msg)

    return JsonResponse({"msg": msg})
