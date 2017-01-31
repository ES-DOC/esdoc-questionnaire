from django.conf.urls import patterns, url, include
from django.views.generic.base import RedirectView
from django.conf import settings
from rest_framework.urlpatterns import format_suffix_patterns

from Q.things.views import *
from Q.things.views.api import *
from Q.things.views.services import *

api_urls = patterns('',

    # getting project info...
    url(r'^proxies/$', ThingProxyList.as_view(), name="thing-proxy-list"),
    url(r'^proxies/(?P<pk>[0-9]+)/$', ThingProxyDetail.as_view(), name="thing-proxy-detail"),

    url(r'^ontologies/$', ThingOntologyList.as_view(), name="thing-ontology-list"),
)

if settings.DEBUG:
    # only expose pre-defined api urls in debug mode...
    api_urls += patterns('', url(r'^$', api_root))

# automatically add support for different serialization formats (JSON is default)...
api_urls = format_suffix_patterns(api_urls)

services_urls = patterns('',
    # testing (obviously)...
    url(r'^test/$', q_services_test),
    # getting pending messages...
    # url(r'^messages/$', get_django_messages),
    # getting a component hierarchy
    url(r'^get_hierarchy/$', q_get_hierarchy, name="get_hierarchy"),
)

urlpatterns = patterns('',

    # RESTful API...
    url(r'^api/', include(api_urls)),

    # webservices (AJAX POST only) outside of RESTful API...
    url(r'^services/', include(services_urls)),

    # help...
    url(r'^help/$', RedirectView.as_view(url=settings.Q_HELP_URL, permanent=True), name="help"),

    # index...
    url(r'^$', 'things.views.index', name="index"),

)
