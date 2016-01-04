####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from Q.questionnaire.views.api.views_api_projects import QProjectList, QProjectDetail
from Q.questionnaire.views.api.views_api_ontologies import QOntologyList
from Q.questionnaire.views.api.views_api_lite import QModelLiteList, QCustomizationLiteList
from Q.questionnaire.views.api.views_api_customizations import QModelCustomizationList, QModelCustomizationDetail, get_cached_customization
from Q.questionnaire.views.api.views_api_realizations import QModelList, QModelDetail, QStandardPropertyList, QStandardPropertyDetail
from Q.questionnaire.views.api.views_api_user import UserViewSet

@api_view(('GET',))
def api_root(request, format=None):
    return Response({
        'users': reverse('user-list', request=request, format=format),
        'projects': reverse('project-list', request=request, format=format),
        'ontologies': reverse('ontology-list', request=request, format=format),
        'customizations': reverse('customization-list', request=request, format=format),
        'models_lite': reverse('model_lite-list', request=request, format=format),
        'customizations_lite': reverse('customization_lite-list', request=request, format=format),
    })
