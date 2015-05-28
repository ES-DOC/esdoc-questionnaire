####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2014 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"
__date__ = "Dec 01, 2014 3:00:00 PM"

"""
.. module:: urls

All URL patterns for questionnaire app.
"""

from django.conf.urls import patterns, url
from django.contrib import admin

from CIM_Questionnaire.questionnaire.views.views_feed import MetadataFeed

admin.autodiscover()

urlpatterns = patterns('',

    # testing (of course)...
    url(r'^test/$', 'questionnaire.views.test', name="questionnaire_test"),

    # project error...
    # url(r'^error/$', 'questionnaire.views.error', name='questionnaire_error'),

    # project help...
    url(r'^help/$', 'questionnaire.views.help', name='questionnaire_help'),

    # authentication...
    url(r'^login/$', 'questionnaire.views.login', name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout',  name='logout'),
    url(r'^register/$', 'questionnaire.views.register', name='register'),
    url(r'^user/$', 'questionnaire.views.user', name='user'),
    url(r'^user/(?P<user_name>[^/]+)/$', 'questionnaire.views.user', name='user'),

    # openid authentication...
    # url(r'^openid/$', 'questionnaire.views.oid_login'),
    # url(r'^openid/process/(?P<token>.*)/$', 'questionnaire.views.oid_process'),

    # customizing...
    url(r'^customize/help$', 'questionnaire.views.customize_help', name="customize_help"),
    url(r'^(?P<project_name>[^/]+)/customize/(?P<version_key>[^/]+)/(?P<model_name>[^/]+)/$', 'questionnaire.views.customize_new', name="customize_new"),
    url(r'^(?P<project_name>[^/]+)/customize/(?P<version_key>[^/]+)/(?P<model_name>[^/]+)/(?P<customizer_name>[^/]+)/$', 'questionnaire.views.customize_existing', name="customize_existing"),

    # editing...
    url(r'^edit/help$', 'questionnaire.views.edit_help', name="edit_help"),
    url(r'^(?P<project_name>[^/]+)/edit/(?P<version_key>[^/]+)/(?P<model_name>[^/]+)/$', 'questionnaire.views.edit_new', name="edit_new"),
    url(r'^(?P<project_name>[^/]+)/edit/(?P<version_key>[^/]+)/(?P<model_name>[^/]+)/(?P<model_id>[^/]+)/$', 'questionnaire.views.edit_existing', name="edit_existing"),

    # viewing...
    url(r'^view/help$', 'questionnaire.views.view_help'),
    url(r'^(?P<project_name>[^/]+)/view/(?P<version_key>[^/]+)/(?P<model_name>[^/]+)/$', 'questionnaire.views.view_new', name="view_new"),
    url(r'^(?P<project_name>[^/]+)/view/(?P<version_key>[^/]+)/(?P<model_name>[^/]+)/(?P<model_id>[^/]+)/$', 'questionnaire.views.view_existing', name="view_existing"),

    # old ajax...
    url(r'^ajax/customize_subform/$', 'questionnaire.views.ajax_customize_subform', name="customize_subform"),
    url(r'^ajax/select_realization/$', 'questionnaire.views.ajax_select_realization', name="select_realization"),

    # new ajax / restful api...
    url(r'^api/(?P<project_name>[^/]+)/get_new_edit_form_section/(?P<section_key>[^/]+)/$', 'questionnaire.views.views_api.api_get_new_edit_form_section', name="api_get_new_edit_form_section"),
    url(r'^api/(?P<project_name>[^/]+)/get_existing_edit_form_section/(?P<model_id>[^/]+)/(?P<section_key>[^/]+)/$', 'questionnaire.views.views_api.api_get_existing_edit_form_section', name="api_get_existing_edit_form_section"),
    url(r'^api/(?P<project_name>[^/]+)/get_new_customize_form_section/(?P<section_key>[^/]+)/$', 'questionnaire.views.views_api.api_get_new_customize_form_section', name="api_get_new_customize_form_section"),
    url(r'^api/(?P<project_name>[^/]+)/get_existing_customize_form_section/(?P<customization_name>[^/]+)/(?P<section_key>[^/]+)/$', 'questionnaire.views.views_api.api_get_existing_customize_form_section', name="api_get_existing_customize_form_section"),

    url(r'^api/add_inheritance_data/$', 'questionnaire.views.views_inheritance.api_add_inheritance_data', name="add_inheritance_data"),
    url(r'api/customize_category/(?P<category_type>[^/]+)/$', 'questionnaire.views.views_categories.api_customize_category', name="customize_category"),
    url(r'^api/publish/$', 'questionnaire.views.views_publish.api_publish', name="api_publish"),

    # atom feeds...
    url(r'^feed/$', MetadataFeed(), name="feed"),
    url(r'^feed/(?P<project_name>[^/]+)/$', MetadataFeed(), name="feed_project"),
    url(r'^feed/(?P<project_name>[^/]+)/(?P<version_key>[^/]+)/$', MetadataFeed(), name="feed_project_version"),
    url(r'^feed/(?P<project_name>[^/]+)/(?P<version_key>[^/]+)/(?P<model_name>[^/]+)/$', MetadataFeed(), name="feed_project_version_proxy"),
    url(r'^feed/(?P<project_name>[^/]+)/(?P<version_key>[^/]+)/(?P<model_name>[^/]+)/(?P<model_guid>[^/]+)/$', 'questionnaire.views.serialize', name="serialize_latest_version"),
    url(r'^feed/(?P<project_name>[^/]+)/(?P<version_key>[^/]+)/(?P<model_name>[^/]+)/(?P<model_guid>[^/]+)/(?P<model_version>[^/]+)/$', 'questionnaire.views.serialize', name="serialize_specific_version"),

    # indices
    url(r'^$', 'questionnaire.views.index', name="index"),
    url(r'^(?P<project_name>[^/]+)/$', 'questionnaire.views.project_index', name="project_index"),

)
