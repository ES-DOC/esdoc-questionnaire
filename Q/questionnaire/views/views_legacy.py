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

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from Q.questionnaire.models.models_projects import QProject
from Q.questionnaire.models.models_ontologies import QOntology
from Q.questionnaire.models.models_realizations_bak import MetadataModel
from Q.questionnaire.views.views_base import add_parameters_to_context
from Q.questionnaire.views.views_errors import q_error
from Q.questionnaire.q_utils import find_in_sequence

# I just use these views to map legacy urls from the dcmip-2012 project
# (which ran long before the ES-DOC Questionnaire was stable)
# to current urls

def q_legacy_view(request, realization_label=None):

    # TODO: IS THERE A WAY TO PASS "context" TO "HttpResponseRedirect"?
    context = add_parameters_to_context(request)

    project_name = "dycore"
    ontology_key = "cim_1.10.0"
    document_type = "modelcomponent"
    dycore_project = QProject.objects.get(name=project_name)
    cim_1_10_0_ontology = QOntology.objects.get(key=ontology_key)
    model_component_proxy = cim_1_10_0_ontology.model_proxies.get(name__iexact=document_type)
    realization_label = realization_label.lower()

    realizations = MetadataModel.objects.filter(
        project=dycore_project,
        version=cim_1_10_0_ontology,
        proxy=model_component_proxy,
    )
    realization = find_in_sequence(
        lambda r: r.get_label().lower() == realization_label,
        realizations
    )
    if not realization:
        msg = "Cannot find the specified model.  Please try again."
        return q_error(request, msg)

    view_existing_url = reverse("view_existing", kwargs={
        "project_name": project_name,
        "ontology_key": ontology_key,
        "document_type": document_type,
        "pk": realization.pk,
    })

    return HttpResponseRedirect(view_existing_url)

def q_legacy_feed(request):

    # TODO: IS THERE A WAY TO PASS "context" TO "HttpResponseRedirect"?
    context = add_parameters_to_context(request)

    feed_url = reverse("feed_project_ontology_proxy", kwargs={
        "project_name": "dycore",
        "ontology_key": "cim_1.10.0",
        "document_type": "modelcomponent",
    })

    return HttpResponseRedirect(feed_url)


def q_legacy_publication(request, id=None):

    # TODO: IS THERE A WAY TO PASS "context" TO "HttpResponseRedirect"?
    context = add_parameters_to_context(request)

    try:
        realization = MetadataModel.objects.get(pk=id)
        guid = realization.guid
    except MetadataModel.DoesNotExist:
        msg = "cannot find specified model"
        return q_error(request, msg)

    publication_url = reverse("publication_latest", kwargs={
        "project_name": "dycore",
        "ontology_key": "cim_1.10.0",
        "document_type": "modelcomponent",
        "guid": guid,
    })

    return HttpResponseRedirect(publication_url)
