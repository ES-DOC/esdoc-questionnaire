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

user_list = UserViewSet.as_view({
    'get': 'list',
})

user_detail = UserViewSet.as_view({
    'get': 'retrieve',
})

api_urls = patterns('',

    # list all api urls...
    url(r'^$', api_root),

    # TESTING
    url(r'^users/$', user_list, name="user-list"),
    url(r'^users/(?P<pk>[0-9]+)/$', user_detail, name="user-detail"),
    # END TESTING

    # getting project info...
    url(r'^projects/$', QProjectList.as_view(), name="project-list"),
    url(r'^projects/(?P<pk>[0-9]+)/$', QProjectDetail.as_view(), name="project-detail"),

    # just some lite serializations for populating the project page...
    url(r'^ontologies/$', QOntologyList.as_view(), name="ontology-list"),
    url(r'^models_lite/$', QModelLiteList.as_view(), name="model_lite-list"),
    url(r'^customizations_lite/$', QCustomizationLiteList.as_view(), name="customization_lite-list"),

    # customizations...
    url(r'^customizations/$', QModelCustomizationList.as_view(), name="customization-list"),
    url(r'^customizations/cache/$', get_cached_customization, name="customization-cache"),
    url(r'^customizations/(?P<pk>[0-9]+)/$', QModelCustomizationDetail.as_view(), name="customization-detail"),

    # realizations...
    # url(r'^models/$', QModelList.as_view(), name="model-list"),
    # url(r'^models/cache/$', get_cached_realization, name="model-cache"),
    # url(r'^models/(?P<pk>[0-9]+)/$', QModelDetail.as_view(), name="model-detail"),
)

# automatically add support for different serialization formats (JSON is default)...
api_urls = format_suffix_patterns(api_urls)

services_urls = patterns('',
    # getting pending messages...
    url(r'^messages/$', get_django_messages),
    # joining a project...
    url(r'^(?P<project_name>[^/]+)/project_join_request/$', q_project_join_request, name="project_join_request"),
    # publishing a document...
    url(r'^document_publish/$', q_document_publish, name="document_publish"),
    # deleting a customization...
    url(r'^customization_delete/$', q_customization_delete, name="customization_delete"),
    # dealing w/ load-on-demand sections...
    url(r'^load_section/(?P<section_type>[^/]+)/$', q_load_section, name="load_section"),
    url(r'^load_subform_section/(?P<section_type>[^/]+)/$', q_load_subform_section, name="load_subform_section"),
)

urlpatterns = patterns('',

    # RESTful API...
    url(r'^api/', include(api_urls)),

    # webservices (AJAX POST only) outside of RESTful API...
    url(r'^services/', include(services_urls)),

    # help...
    url(r'^help/$', RedirectView.as_view(url=settings.Q_HELP_URL, permanent=True), name="help"),

    # TODO: REMOVE THIS
    # PRE v0.15 CODE
    url(r'^bak/api/(?P<project_name>[^/]+)/get_new_edit_form_section/(?P<section_key>[^/]+)/$', 'questionnaire.views.views_api_bak.api_get_new_edit_form_section', name="api_get_new_edit_form_section"),
    url(r'^bak/api/(?P<project_name>[^/]+)/get_existing_edit_form_section/(?P<model_id>[^/]+)/(?P<section_key>[^/]+)/$', 'questionnaire.views.views_api_bak.api_get_existing_edit_form_section', name="api_get_existing_edit_form_section"),
    url(r'^bak/ajax/select_realization', 'questionnaire.views.views_ajax_bak.ajax_select_realization', name="ajax_select_realization"),
    url(r'^bak/api/add_inheritance_data/$', 'questionnaire.views.views_inheritance_bak.api_add_inheritance_data', name="add_inheritance_data"),

    # customizations...
    url(r'^(?P<project_name>[^/]+)/customize/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/$', q_customize_new, name="customize_new"),
    url(r'^(?P<project_name>[^/]+)/customize/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/(?P<customization_name>[^/]+)/$', q_customize_existing, name="customize_existing"),

    # realizations...
    url(r'^(?P<project_name>[^/]+)/edit/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/$', q_edit_new, name="edit_new"),
    url(r'^(?P<project_name>[^/]+)/edit/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/(?P<pk>[^/]+)/$', q_edit_existing, name="edit_existing"),
    url(r'^(?P<project_name>[^/]+)/view/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/$', q_view_new, name="view_new"),
    url(r'^(?P<project_name>[^/]+)/view/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/(?P<pk>[^/]+)/$', q_view_existing, name="view_existing"),

    # users...
    url(r'^users/$', q_user),
    url(r'^users/(?P<user_name>[^/]+)/$', q_user, name="user"),
    url(r'^users/(?P<user_name>[^/]+)/password$', q_password, name="password"),
    url(r'^login/$', q_login, name="login"),
    url(r'^logout/$', q_logout, name="logout"),
    url(r'^register/$', q_register, name="register"),

    # testing (obviously)...
    url(r'^test/$', 'questionnaire.views.q_test', name="test"),
    url(r'^test/(?P<pk>[0-9]+)/$', 'questionnaire.views.q_test', name="test"),

    # legacy code...
    # TODO: AT WHAT POINT CAN I REMOVE THIS?
    url(r'^metadata/dycore/dycoremodel/$', 'questionnaire.views.views_legacy.q_legacy_edit'),
    url(r'^metadata/dycore/dycoremodel/(?P<realization_label>[^/]+)/$', 'questionnaire.views.views_legacy.q_legacy_view'),
    url(r'^metadata/feed/dycore/modelcomponent/$', 'questionnaire.views.views_legacy.q_legacy_feed'),
    url(r'^metadata/feed/dycore/$', 'questionnaire.views.views_legacy.q_legacy_feed'),
    url(r'^metadata/feed/$', 'questionnaire.views.views_legacy.q_legacy_feed'),
    url(r'^metadata/xml/dycore/dycoremodel/(?P<id>[^/]+)/$', 'questionnaire.views.views_legacy.q_legacy_publication'),

    # publications (ATOM feed)...
    url(r'^feed/$', QFeed(), name="feed"),
    url(r'^feed/(?P<project_name>[^/]+)/$', QFeed(), name="feed_project"),
    url(r'^feed/(?P<project_name>[^/]+)/(?P<ontology_key>[^/]+)/$', QFeed(), name="feed_project_ontology"),
    url(r'^feed/(?P<project_name>[^/]+)/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/$', QFeed(), name="feed_project_ontology_proxy"),
    url(r'^feed/(?P<project_name>[^/]+)/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/(?P<guid>[^/]+)/$', q_publication, name="publication_latest"),
    url(r'^feed/(?P<project_name>[^/]+)/(?P<ontology_key>[^/]+)/(?P<document_type>[^/]+)/(?P<guid>[^/]+)/(?P<version>[^/]+)/$', q_publication, name="publication_version"),

    # projects...
    url(r'^(?P<project_name>[^/]+)/$', q_project, name="project"),

    # index...
    url(r'^$', 'questionnaire.views.q_index', name="index"),

)
