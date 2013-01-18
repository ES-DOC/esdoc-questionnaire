from django.conf.urls.defaults import patterns, include, url

#from models import *
#from feeds import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    # the index page (doesn't do anything yet)...
    url(r'^$', 'dcf.views.index'),

    # AJAX calls...
    url(r'^ajax/component_nest', 'dcf.views.component_nest'),
    url(r'^ajax/get_field_category', 'dcf.views.get_field_category'),
    url(r'^ajax/delete_field_category', 'dcf.views.delete_field_category'),
    url(r'^ajax/edit_field_category', 'dcf.views.edit_field_category'),

    # customize a model form...
    url(r'^customize/(?P<app_name>[^/]+)/(?P<model_name>[^/]+)/$', 'dcf.views.customize'),
    url(r'^customize/instructions$', 'dcf.views.customize_instructions'),

    url(r'^customize2/(?P<app_name>[^/]+)/(?P<model_name>[^/]+)/$', 'dcf.views.customize2'),

    # edit (or just view) a model form...
    url(r'^edit/(?P<app_name>[^/]+)/(?P<model_name>[^/]+)/$', 'dcf.views.edit'),
    url(r'^edit/instructions$', 'dcf.views.edit_instructions'),

    # these forms can be generated for _any_ model in _any_ application...
    # (make sure these patterns are last)
    url(r'^(?P<app_name>[^/]+)/(?P<model_name>[^/]+)/$', 'dcf.views.detail'),
    url(r'^(?P<app_name>[^/]+)/(?P<model_name>[^/]+)/(?P<model_id>\d+)/$', 'dcf.views.detail'),



#    # ATOM feed...
#    url(r'^feed/(?P<app_name>[^/]+)/(?P<model_type>[^/]+)/$', MetadataFeed()),
#    url(r'^feed/(?P<app_name>[^/]+)/$', MetadataFeed()),
#

)

