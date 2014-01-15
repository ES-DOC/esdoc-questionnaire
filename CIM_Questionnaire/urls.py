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

    # project-specific stuff...

    # project index
    url(r'^$',          'questionnaire.views.index'),
    url(r'^index/$',    'questionnaire.views.index',    name='questionnaire_index'),
    url(r'^test/$',     'questionnaire.views.test'),

    # authentication...
    #url(r'^login/$',    'questionnaire.views.login'),
    #url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'cog/account/login.html'}, name='login'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'questionnaire/questionnaire_login.html'}, name='login'),

    # openid authentication...
    url(r'^openid/$', 'questionnaire.views.oid_login'),
    url(r'^openid/process/(?P<token>.*)/$', 'questionnaire.views.oid_process'),
    

#    # project error
#    url(r'^error/$',   'questionnaire.views.error',    name='questionnaire_error'),
#
#    # project help
#    url(r'^help/$',    'questionnaire.views.help',     name='questionnaire_help'),
#
#    # project authentication
#    url(r'^login/$',   'questionnaire.views.login',    name='questionnaire_login'),

    # application-specific stuff...

    # django-cim-forms
    (r'^metadata/', include('django_cim_forms.urls')),
    (r'', include('dycore.urls')),

    # dcf
    (r'^dcf/', include('dcf.urls')),

)
