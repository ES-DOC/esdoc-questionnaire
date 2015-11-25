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

from django.shortcuts import render_to_response, redirect
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.contrib import messages

from Q.questionnaire.models import QModelCustomization, QOntology, QModelProxy, QProject
from Q.questionnaire.forms.forms_customize_models import QModelCustomizationForm

def q_test(request, pk=None):
    """
    This is just a view for testing/development purposes;
    It renders the "q_test.html" template
    It changes all the time during development
    :param request:
    :return:
    """
    _dict = {}
    return render_to_response('questionnaire/q_test.html', _dict, context_instance=RequestContext(request))

    document_type = "modelcomponent"
    ontology = QOntology.objects.get(pk=1)
    proxy = QModelProxy.objects.get(pk=1)
    project = QProject.objects.get(pk=1)

    vocabularies = project.vocabularies.filter(document_type__iexact=document_type)

    customization = QModelCustomization(
        ontology=ontology,
        proxy=proxy,
        project=project,
    )

    customization_form = QModelCustomizationForm(
        instance=customization,
        # prefix="model_customization",  # this MUST match the model name used by ng
        scope_prefix="model_customization",  # ths MUST match the model name used by ng
        form_name="model_customization_form",
    )

    # work out the various paths,
    # so that angular can dynamically reset things (if the customization_name changes)
    view_url = request.path
    view_url_sections = [section for section in view_url.split('/') if section]
    view_url_dirname = '/'.join(view_url_sections[:])
    view_url_basename = ""
    api_url = reverse("customization-list", kwargs={})
    api_url_sections = [section for section in api_url.split('/') if section]
    api_url_dirname = '/'.join(api_url_sections[:])
    api_url_basename = ""

    # gather all the extra information required by the template
    _dict.updte({
        "view_url_dirname": "/{0}/".format(view_url_dirname),
        "view_url_basename": view_url_basename,
        "api_url_dirname": "/{0}/".format(api_url_dirname),
        "api_url_basename": api_url_basename,
        "ontology": ontology,
        "proxy": proxy,
        "project": project,
        "vocabularies": vocabularies,
        # "customization": customization,
        "form": customization_form,
        "is_default": customization.is_default,
    })

    return render_to_response('questionnaire/q_test.html', _dict, context_instance=RequestContext(request))

