
####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Jan 14, 2014 4:51:41 PM"

"""
.. module:: urls

Summary of module goes here

"""

from django.conf.urls import patterns, url
from django.contrib import admin

from CIM_Questionnaire.questionnaire.views.views_feed import MetadataFeed


admin.autodiscover()

urlpatterns = patterns('',

    # testing (obviously)...
    url(r'^test/$',     'questionnaire.views.test'),

#    # project error...
#    url(r'^error/$',   'questionnaire.views.error',    name='questionnaire_error'),

    # project help...
    url(r'^help/$',    'questionnaire.views.help',     name='questionnaire_help'),

    # authentication...
    url(r'^login/$', 'questionnaire.views.login', name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout',  name='logout'),
    url(r'^register/$', 'questionnaire.views.register', name='register'),
    url(r'^user/$', 'questionnaire.views.user', name='user'),
    url(r'^user/(?P<user_name>[^/]+)/$', 'questionnaire.views.user', name='user'),

    # openid authentication...
    #url(r'^openid/$', 'questionnaire.views.oid_login'),
    #url(r'^openid/process/(?P<token>.*)/$', 'questionnaire.views.oid_process'),

    # indices
    url(r'^$',                                'questionnaire.views.index', name="index"),
    url(r'^(?P<project_name>[^/]+)/$',        'questionnaire.views.project_index', name="project_index"),

    # customizing...
    url(r'^customize/help$', 'questionnaire.views.customize_help', name="customize_help"),
    url(r'^(?P<project_name>[^/]+)/customize/(?P<version_name>[^/]+)/(?P<model_name>[^/]+)/$', 'questionnaire.views.customize_new', name="customize_new"),
    url(r'^(?P<project_name>[^/]+)/customize/(?P<version_name>[^/]+)/(?P<model_name>[^/]+)/(?P<customizer_name>[^/]+)/$', 'questionnaire.views.customize_existing', name="customize_existing"),

    # editing...
    url(r'^edit/help$', 'questionnaire.views.edit_help', name="edit_help"),
    url(r'^(?P<project_name>[^/]+)/edit/(?P<version_name>[^/]+)/(?P<model_name>[^/]+)/$', 'questionnaire.views.edit_new', name="edit_new"),
    url(r'^(?P<project_name>[^/]+)/edit/(?P<version_name>[^/]+)/(?P<model_name>[^/]+)/(?P<model_id>[^/]+)/$', 'questionnaire.views.edit_existing', name="edit_existing"),

    # viewing...
    url(r'^view/help$', 'questionnaire.views.view_help'),
    url(r'^(?P<project_name>[^/]+)/view/(?P<version_name>[^/]+)/(?P<model_name>[^/]+)/(?P<model_id>[^/]+)/$', 'questionnaire.views.view_existing', name="view_existing"),

    # ajax...
    url(r'^ajax/customize_subform/$', 'questionnaire.views.ajax_customize_subform', name="customize_subform"),
    url(r'^ajax/customize_category/$', 'questionnaire.views.ajax_customize_category'),
    url(r'^ajax/customize_category/(?P<category_id>[^/]+)/$', 'questionnaire.views.ajax_customize_category'),
    url(r'^ajax/select_realization/$', 'questionnaire.views.ajax_select_realization', name="select_realization"),

    # atom feeds...
    url(r'^feed$', MetadataFeed()),
    url(r'^feed/(?P<project_name>[^/]+)/$', MetadataFeed()),
    url(r'^feed/(?P<project_name>[^/]+)/(?P<version_name>[^/]+)/$', MetadataFeed()),
    url(r'^feed/(?P<project_name>[^/]+)/(?P<version_name>[^/]+)/(?P<model_name>[^/]+)/$', MetadataFeed()),
    url(r'^feed/(?P<project_name>[^/]+)/(?P<version_name>[^/]+)/(?P<model_name>[^/]+)/(?P<model_id>[^/]+)/$', 'questionnaire.views.serialize', name="serialize"),

)
