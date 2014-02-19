from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',

    # media (when NOT served through the Apache web server)...
    url(r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT} ),

    # admin...
    url(r'^admin/',     include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # authentication...
    # authentication is handled by dcf for now

    # application-specific stuff...
    # to appear in next release

    # django-cim-forms
    (r'^metadata/', include('django_cim_forms.urls')),
    (r'', include('dycore.urls')),

    # dcf
    (r'^dcf/', include('dcf.urls')),

    # index
    url(r'^$', 'dcf.views.index'),
    
)
