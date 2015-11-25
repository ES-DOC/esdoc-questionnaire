####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

"""
.. module:: urls

url routing for the entire project
"""

from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',

    # ORDER IS IMPORTANT !

    # media (when NOT served through Apache)...
    # TODO: IS EXPOSING THESE A SECURITY RISK?
    url(r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),

    # admin...
    url(r'^admin/', include(admin.site.urls)),

    # mindmaps...
    url(r'^mindmaps/', include('mindmaps.urls')),

    # questionnaire app...
    (r'', include('questionnaire.q_urls')),

    # add a custom 404 page...
    # (this is not the Django-approved way to do things)
    # (it's a catch-all regex in-case none of the above patterns match)
    # (doing it the right way in Django requires setting DEBUG to False in settings.py)
    # (but that means that other Python errors would never be displayed)
    url(r'^.*/$', 'questionnaire.views.q_404'),
)

# handler400 = 'questionnaire.views.q_400'  # bad request error
# handler403 = 'questionnaire.views.q_403'  # permission denied error
handler404 = 'questionnaire.views.q_404'  # page not found error
handler500 = 'questionnaire.views.q_500'  # server error
