
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

from dcf.views import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    # the index page (just for development)...
    url(r'^$', 'dcf.views.index'),

    # TODO: custom error handling (400,403,404)?

    # customize a CIM form...
    url(r'^customize/(?P<project_name>[^/]+)/(?P<model_name>[^/]+)/(?P<version_number>[^/]+)/$', 'dcf.views.customize_new',name="customize_new"),
    url(r'^customize/(?P<project_name>[^/]+)/(?P<model_name>[^/]+)/(?P<version_number>[^/]+)/(?P<customizer_id>[^/]+)/$', 'dcf.views.customize_existing',name="customize_existing"),
    url(r'^customize/instructions$', 'dcf.views.customize_instructions'),

    # edit a CIM form...
    url(r'^edit/(?P<project_name>[^/]+)/(?P<model_name>[^/]+)/(?P<version_number>[^/]+)/$', 'dcf.views.edit_new', name="edit_new"),
    url(r'^edit/(?P<project_name>[^/]+)/(?P<model_name>[^/]+)/(?P<version_number>[^/]+)/(?P<model_id>[^/]+)/$', 'dcf.views.edit_existing', name="edit_existing"),

    # AJAX calls...
    url(r'^ajax/customize_subform/$', 'dcf.views.customize_subform'),
    url(r'^ajax/customize_category/$', 'dcf.views.customize_category'),
    url(r'^ajax/add_model/$', 'dcf.views.add_model'),

    # ATOM feed...
    url(r'^feed/(?P<project_name>[^/]+)/(?P<model_name>[^/]+)/(?P<version_number>[^/]+)/(?P<model_id>[^/]+)/$', 'dcf.views.serialize'),
    url(r'^feed/(?P<project_name>[^/]+)/(?P<model_name>[^/]+)/(?P<version_number>[^/]+)/$', MetadataFeed()),
    url(r'^feed/(?P<project_name>[^/]+)/(?P<model_name>[^/]+)/$', MetadataFeed()),
    url(r'^feed/(?P<project_name>[^/]+)/$', MetadataFeed()),

)

