from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',

    url(r'^$', 'mindmaps.views.mindmaps_index', name="index"),
    url(r'^view/$', 'mindmaps.views.mindmaps_view', name="view"),
    #url(r'^test/$', 'mindmaps.views.mindmaps_test', name="test"),
)
