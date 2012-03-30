from django.conf.urls.defaults import patterns, include, url

from models import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    # the index page (doesn't do anything yet)...
    url(r'^$', 'django_cim_forms.views.index'),

    # ajax calls to server
    url(r'^get_lil_form/$', 'django_cim_forms.views.get_lil_form'),
    url(r'^get_lil_content/$', 'django_cim_forms.views.get_lil_content'),

    # cvs...
    url(r'^cv/(?P<cv_name>\w+)/$', 'django_cim_forms.views_cv.detail'),

    # the forms can be generated for _any_ model in _any_ application...
    url(r'^(?P<app_name>[^/]+)/(?P<model_name>[^/]+)/$', 'django_cim_forms.views.detail'),
    url(r'^(?P<app_name>[^/]+)/(?P<model_name>[^/]+)/(?P<model_id>\d+)/$', 'django_cim_forms.views.detail'),
)

