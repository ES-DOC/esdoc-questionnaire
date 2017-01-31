####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.conf import settings
from django.conf.urls import patterns, url, include
from django.views.generic.base import RedirectView
from rest_framework.urlpatterns import format_suffix_patterns

from Q.questionnaire.views import *
from Q.questionnaire.views.api import *
from Q.questionnaire.views.services import *
from Q.questionnaire.views.views_feed import QFeed, q_publication

api_urls = patterns('',

    # getting project info...
    url(r'^projects/$', QProjectList.as_view(), name="project-list"),
    url(r'^projects/(?P<pk>[0-9]+)/$', QProjectDetail.as_view(), name="project-detail"),

    # just some lite serializations for populating the project page...
    url(r'^customizations_lite/$', QCustomizationLiteList.as_view(), name="customization_lite-list"),
    url(r'^realizations_lite/$', QRealizationLiteList.as_view(), name="realization_lite-list"),

    # getting ontology info...
    url(r'^ontologies/$', QOntologyList.as_view(), name="ontology-list"),

    # getting customization info...
    url(r'^customizations/$', QModelCustomizationList.as_view(), name="customization-list"),
    url(r'^customizations/(?P<pk>[0-9]+)/$', QModelCustomizationDetail.as_view(), name="customization-detail"),
    url(r'^customizations/cache/$', get_cached_customizations, name="customization-cache"),

    # getting realization info...
    url(r'^realizations/$', QModelRealizationList.as_view(), name="realization-list"),
    url(r'^realizations/(?P<pk>[0-9]+)/$', QModelRealizationDetail.as_view(), name="realization-detail"),
    url(r'^realizations/cache/$', get_cached_realizations, name="realization-cache"),
)

if settings.DEBUG:
    # only expose pre-defined api urls in debug mode...
    api_urls += patterns('', url(r'^$', api_root))

# automatically add support for different serialization formats (JSON is default)...
api_urls = format_suffix_patterns(api_urls)

services_urls = patterns('',
    # testing (obviously)...
    url(r'^test/$', q_services_test),
    # getting pending messages...
    url(r'^messages/$', get_django_messages),
    # the world-famous load-on-demand paradigm...
    url(r'^load_section/(?P<section_type>[^/]+)/$', q_load_section, name="load_section"),
    # joining a project...
    url(r'^(?P<project_name>[^/]+)/project_join_request/$', q_project_join_request, name="project_join_request"),
    # deleting a customization...
    url(r'^customization_delete/$', q_customization_delete, name="customization_delete"),
    # adding a relationship...
    url(r'^realization_add_relationship_value/$', q_realization_add_relationship_value, name="realization_add_relationsip_value"),
    # removing a relationship...
    url(r'^realization_remove_relationship_value/$', q_realization_remove_relationship_value, name="realization_remove_relationsip_value"),
    # publishing a realization...
    url(r'^realization_publish/$', q_realization_publish, name="realization_publish"),
)

urlpatterns = patterns('',

    # RESTful API...
    url(r'^api/', include(api_urls)),

    # webservices (AJAX POST only) outside of RESTful API...
    url(r'^services/', include(services_urls)),

    # testing (obviously)...
    url(r'^test/$', q_test, name="test"),

    # help...
    url(r'^help/$', RedirectView.as_view(url=settings.Q_HELP_URL, permanent=True), name="help"),

    # customizations...
    url(r'^(?P<project_name>[^/]+)/customize/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/$', q_customize_new, name="customize_new"),
    url(r'^(?P<project_name>[^/]+)/customize/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/(?P<customization_name>[^/]+)/$', q_customize_existing, name="customize_existing"),

    # realizations...
    url(r'^(?P<project_name>[^/]+)/edit/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/$', q_edit_new, name="edit_new"),
    url(r'^(?P<project_name>[^/]+)/edit/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/(?P<realization_pk>[^/]+)/$', q_edit_existing, name="edit_existing"),
    url(r'^(?P<project_name>[^/]+)/view/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/$', q_view_new, name="view_new"),
    url(r'^(?P<project_name>[^/]+)/view/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/(?P<realization_pk>[^/]+)/$', q_view_existing, name="view_existing"),

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
