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

"""
.. module:: urls

All URL patterns for questionnaire app.
"""

from django.conf.urls import patterns, url, include
from django.conf import settings
from django.views.generic.base import RedirectView
from rest_framework.urlpatterns import format_suffix_patterns

from Q.questionnaire.views import *
from Q.questionnaire.views.api import *
from Q.questionnaire.views.services import *
from Q.questionnaire.views.views_feed import QFeed, q_publication

api_urls = patterns('',

    # list all pre-defined api urls...
    url(r'^$', api_root),

    # getting project info...
    url(r'^projects/$', QProjectList.as_view(), name="project-list"),
    url(r'^projects/(?P<pk>[0-9]+)/$', QProjectDetail.as_view(), name="project-detail"),

    # getting ontology info...
    url(r'^ontologies/$', QOntologyList.as_view(), name="ontology-list"),

    # just some lite serializations for populating the project page...
    url(r'^customizations_lite/$', QCustomizationLiteList.as_view(), name="customization_lite-list"),
    url(r'^realizations_lite/$', QRealizationLiteList.as_view(), name="realization_lite-list"),

    # customizations...
    url(r'^customizations/$', QModelCustomizationList.as_view(), name="customization-list"),
    url(r'^customizations/cache/$', get_cached_customizations, name="customization-cache"),
    url(r'^customizations/(?P<pk>[0-9]+)/$', QModelCustomizationDetail.as_view(), name="customization-detail"),

    # realizations...
    url(r'^realizations/$', QModelRealizationList.as_view(), name="realization-list"),
    url(r'^realizations/cache/$', get_cached_realizations, name="realization-cache"),
    url(r'^realizations/(?P<pk>[0-9]+)/$', QModelRealizationDetail.as_view(), name="realization-detail"),
)

# automatically add support for different serialization formats (JSON is default)...
api_urls = format_suffix_patterns(api_urls)

services_urls = patterns('',
    # getting pending messages...
    url(r'^messages/$', get_django_messages),
    # joining a project...
    url(r'^(?P<project_name>[^/]+)/project_join_request/$', q_project_join_request, name="project_join_request"),
    # publishing a document...
    url(r'^realization_publish/$', q_realization_publish, name="realization_publish"),
    # deleting a customization...
    url(r'^customization_delete/$', q_customization_delete, name="customization_delete"),
    # dealing w/ load-on-demand sections...
    url(r'^load_section/(?P<section_type>[^/]+)/$', q_load_section, name="load_section"),
    # adding & removing relationship properties...
    url(r'^realization_add_relationship_value/$', q_realization_add_relationship_value, name="realization_add_relationship_value"),
    url(r'^realization_remove_relationship_value/$', q_realization_remove_relationship_value, name="realization_remove_relationship_value"),
)

urlpatterns = patterns('',

    # RESTful API...
    url(r'^api/', include(api_urls)),

    # webservices (AJAX POST only) outside of RESTful API...
    url(r'^services/', include(services_urls)),

    # help...
    url(r'^help/$', RedirectView.as_view(url=settings.Q_HELP_URL, permanent=True), name="help"),

    # customizations...
    url(r'^(?P<project_name>[^/]+)/customize/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/$', q_customize_new, name="customize_new"),
    url(r'^(?P<project_name>[^/]+)/customize/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/(?P<customization_name>[^/]+)/$', q_customize_existing, name="customize_existing"),

    # # realizations...
    url(r'^(?P<project_name>[^/]+)/edit/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/$', q_edit_new, name="edit_new"),
    url(r'^(?P<project_name>[^/]+)/edit/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/(?P<realization_pk>[^/]+)/$', q_edit_existing, name="edit_existing"),
    url(r'^(?P<project_name>[^/]+)/view/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/$', q_view_new, name="view_new"),
    url(r'^(?P<project_name>[^/]+)/view/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/(?P<realization_pk>[^/]+)/$', q_view_existing, name="view_existing"),

    # users...
    url(r'^users/$', q_user),
    url(r'^users/(?P<user_name>[^/]+)/$', q_user, name="user"),
    url(r'^users/(?P<user_name>[^/]+)/password$', q_password, name="password"),
    url(r'^login/$', q_login, name="login"),
    url(r'^logout/$', q_logout, name="logout"),
    url(r'^register/$', q_register, name="register"),

    # # testing (obviously)...
    # url(r'^test/$', 'questionnaire.views.q_test', name="test"),
    # url(r'^test/(?P<pk>[0-9]+)/$', 'questionnaire.views.q_test', name="test"),

    # publications (ATOM feed)...
    url(r'^feed/$', QFeed(), name="feed"),
    url(r'^feed/(?P<project_name>[^/]+)/$', QFeed(), name="feed_project"),
    url(r'^feed/(?P<project_name>[^/]+)/(?P<ontology_key>[^/]+)/$', QFeed(), name="feed_project_ontology"),
    url(r'^feed/(?P<project_name>[^/]+)/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/$', QFeed(), name="feed_project_ontology_proxy"),
    url(r'^feed/(?P<project_name>[^/]+)/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/(?P<publication_name>[^/]+)/$', q_publication, name="publication_latest"),
    url(r'^feed/(?P<project_name>[^/]+)/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/(?P<publication_name>[^/]+)/(?P<publication_version>[^/]+)/$', q_publication, name="publication_version"),

    # projects...
    url(r'^(?P<project_name>[^/]+)/$', q_project, name="project"),

    # index...
    url(r'^$', 'questionnaire.views.q_index', name="index"),

)
