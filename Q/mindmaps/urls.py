from django.conf.urls import patterns, url
from django.contrib import admin

from .views import *

# admin.autodiscover()

urlpatterns = patterns('',

    url(r'^$', mindmaps_index, name="index"),
    url(r'^view/$', mindmaps_view, name="view"),
    url(r'^test/$', mindmaps_test, name="test"),

)