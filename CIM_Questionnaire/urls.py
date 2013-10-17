from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    # admin...
    url(r'^admin/',     include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

#    # project-specific stuff...
#
#    # project index
#    url(r'^$',         'questionnaire.views.index'),
#    url(r'index/$',    'questionnaire.views.index',    name='questionnaire_index'),
#
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
