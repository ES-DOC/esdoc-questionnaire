from django.conf.urls.defaults import patterns, include, url

from models import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',


    url(r'^test$', 'final.views.test'),

    # the index page (doesn't do anything yet)...
    url(r'^$', 'final.views.index'),

    # ajax calls to server
    url(r'^add_form/$', 'final.views.add_form'),
    url(r'^get_content/$', 'final.views.get_content'),

    # cvs...
    url(r'^cv/(?P<cv_name>\w+)/$', 'final.views_cv.detail'),

    # these forms can be generated for _any_ model in _any_ application...
    url(r'^(?P<app_name>[^/]+)/(?P<model_name>[^/]+)/$', 'final.views.detail'),
    url(r'^(?P<app_name>[^/]+)/(?P<model_name>[^/]+)/(?P<model_id>\d+)/$', 'final.views.detail'),
)

