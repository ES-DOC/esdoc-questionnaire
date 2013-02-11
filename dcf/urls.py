
####################
#   Django-CIM-Forms
#   Copyright (c) 2012 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Jan 31, 2013 11:05:07 AM"

"""
.. module:: urls

Summary of module goes here

"""

from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    # the index page (just for development)...
    url(r'^$', 'dcf.views.index'),

    # testing (just for development, obviously)...
    url(r'^test/(?P<project_name>[^/]+)/(?P<model_name>[^/]+)/(?P<version_name>[^/]+)/$', 'dcf.views.test'),
    url(r'^test$', 'dcf.views.test'),

    # TODO: custom error handling (400,403,404)?

    # customize a CIM form...
    url(r'^customize/(?P<project_name>[^/]+)/(?P<model_name>[^/]+)/(?P<version_name>[^/]+)/$', 'dcf.views.customize'),
    url(r'^customize/(?P<project_name>[^/]+)/(?P<model_name>[^/]+)/$', 'dcf.views.customize'),
    url(r'^customize/instructions$', 'dcf.views.customize_instructions'),
#
#    # edit a CIM form...
#    url(r'^edit/(?P<version_name>[^/]+)/(?P<project_name>[^/]+)/(?P<model_name>[^/]+)/$', 'dcf.views_edit.edit'),
#    url(r'^edit/(?P<project_name>[^/]+)/(?P<model_name>[^/]+)/$', 'dcf.views_edit.edit'),
#    url(r'^edit/instructions$', 'dcf.views_edit.instructions'),
#
###    # view a CIM form...
###    url(r'^view/(?P<version_name>[^/]+)/(?P<project_name>[^/]+)/(?P<model_name>[^/]+)/$', 'dcf.views.detail'),
###    url(r'^view/(?P<project_name>[^/]+)/(?P<model_name>[^/]+)/$', 'dcf.views.detail'),
#
#
    # AJAX calls...
    url(r'^ajax/get_category/(?P<category_type>[^/]+)/$', 'dcf.views.get_category'),
    url(r'^ajax/edit_category/(?P<category_type>[^/]+)/$', 'dcf.views.edit_category'),
    url(r'^ajax/delete_category/(?P<category_type>[^/]+)/$', 'dcf.views.delete_category'),
###    url(r'^ajax/get_model_hierarchy', 'dcf.views.get_model_hierarchy'),
#
####    # ATOM feed...
####    url(r'^feed/(?P<app_name>[^/]+)/(?P<model_type>[^/]+)/$', MetadataFeed()),
####    url(r'^feed/(?P<app_name>[^/]+)/$', MetadataFeed()),
###

)

