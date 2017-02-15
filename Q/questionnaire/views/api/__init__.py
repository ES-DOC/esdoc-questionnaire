####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


from Q.questionnaire.views.api.views_api_customizations import QModelCustomizationList, QModelCustomizationDetail, get_cached_customizations
from Q.questionnaire.views.api.views_api_lite import QProjectLiteDetail, QProjectLiteList, QCustomizationLiteList, QRealizationLiteList
from Q.questionnaire.views.api.views_api_ontologies import QOntologyList
from Q.questionnaire.views.api.views_api_projects import QProjectList, QProjectDetail, QProjectTestDetail
from Q.questionnaire.views.api.views_api_realizations import QModelRealizationList, QModelRealizationDetail, get_cached_realizations


@api_view(('GET',))
def api_root(request, format=None):
    return Response({
        'ontologies': reverse('ontology-list', request=request, format=format),
        'projects': reverse('project-list', request=request, format=format),
        'customizations': reverse('customization-list', request=request, format=format),
        'realizations': reverse('realization-list', request=request, format=format),
        'projects_lite': reverse('project_lite-list', request=request, format=format),
        'customizations_lite': reverse('customization_lite-list', request=request, format=format),
        'realizations_lite': reverse('realization_lite-list', request=request, format=format),
    })
