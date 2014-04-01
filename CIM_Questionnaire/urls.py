from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
    # ORDER IS IMPORTANT!

    # admin...
    url(r'^admin/',     include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # media (when NOT served through the Apache web server)...
    url(r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT} ),

    # questionnaire
    (r'', include('questionnaire.urls')),

    # old application-specific stuff...

    # django-cim-forms
    (r'^metadata/', include('django_cim_forms.urls')),
    (r'', include('dycore.urls')),

    # dcf
    (r'^dcf/', include('dcf.urls')),

)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )