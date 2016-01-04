####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"

from django.conf.urls import patterns, url
# from django.contrib import admin

from .views import *

# admin.autodiscover()

urlpatterns = patterns('',

    url(r'^$', mindmaps_index, name="index"),
    url(r'^view/$', mindmaps_view, name="view"),
    url(r'^test/$', mindmaps_test, name="test"),

)