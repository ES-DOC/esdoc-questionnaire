from django.conf.urls.defaults import patterns, include, url

#from models import *
#from feeds import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    # the index page (doesn't do anything yet)...
    url(r'^$', 'dcf.views.index'),

    # the test page is just for testing, obviously...
    url(r'^test$', 'dcf.views.test'),

    # AJAX calls...
    url(r'^ajax/component_nest', 'dcf.views.component_nest'),
    url(r'^ajax/get_field_category', 'dcf.views.get_field_category'),
    url(r'^ajax/delete_field_category', 'dcf.views.delete_field_category'),
    url(r'^ajax/edit_field_category', 'dcf.views.edit_field_category'),

    # display instructions for a model form...
    url(r'^instructions$', 'dcf.views.instructions'),

    # customize a model form...
    url(r'^customize/(?P<app_name>[^/]+)/(?P<model_name>[^/]+)/$', 'dcf.views.customize'),
    url(r'^customize/instructions$', 'dcf.views.customize_instructions'),
    
    # these forms can be generated for _any_ model in _any_ application...
    # (make sure these patterns are last)
    url(r'^(?P<app_name>[^/]+)/(?P<model_name>[^/]+)/$', 'dcf.views.detail'),
    url(r'^(?P<app_name>[^/]+)/(?P<model_name>[^/]+)/(?P<model_id>\d+)/$', 'dcf.views.detail'),



#    # ATOM feed...
#    url(r'^feed/(?P<app_name>[^/]+)/(?P<model_type>[^/]+)/$', MetadataFeed()),
#    url(r'^feed/(?P<app_name>[^/]+)/$', MetadataFeed()),
#

)

