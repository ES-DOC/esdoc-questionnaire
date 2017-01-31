####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
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
from allauth.account import views as account_views

from Q.questionnaire.views.views_users import *

admin.autodiscover()

account_urls = patterns('',

    # customize authentication views w/ Q-specific code as needed...

    url(r"^signup/$", q_signup, name="account_signup"),
    url(r"^login/$", q_login, name="account_login"),
    url(r"^logout/$", account_views.logout, name="account_logout"),

    url(r"^password/change/$", q_password_change, name="account_change_password"),
    url(r"^password/set/$", account_views.password_set, name="account_set_password"),

    url(r"^inactive/$", account_views.account_inactive, name="account_inactive"),

    # email
    url(r"^email/$", q_email, name="account_email"),
    url(r"^confirm-email/$", account_views.email_verification_sent, name="account_email_verification_sent"),
    url(r"^confirm-email/(?P<key>[-:\w]+)/$", q_confirm_email, name="account_confirm_email"),

    # password reset
    url(r"^password/reset/$", q_password_reset, name="account_reset_password"),
    url(r"^password/reset/done/$", account_views.password_reset_done, name="account_reset_password_done"),
    url(r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$", q_password_reset_from_key, name="account_reset_password_from_key"),
    url(r"^password/reset/key/done/$", account_views.password_reset_from_key_done, name="account_reset_password_from_key_done"),
)

urlpatterns = patterns('',

    # ORDER IS IMPORTANT !!

    # media (when NOT served through Apache)...
    # TODO: IS EXPOSING THESE A SECURITY RISK?
    url(r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),

    # admin...
    url(r'^admin/', include(admin.site.urls)),

    # 3rd-party authentication...
    url(r'^accounts/', include(account_urls)),
    url(r'^accounts/profile/(?P<username>[^/]+)/$', q_profile, name="account_profile"),
    url(r'^accounts/profile/', q_profile, name="account_profile"),

    # mindmaps app...
    url(r'^mindmaps/', include('mindmaps.urls')),

    # questionnaire app...
    (r'', include('questionnaire.q_urls')),

    # add a custom 404 page...
    # (this is not the Django-approved way to do things)
    # (it's a catch-all regex in-case none of the above patterns match)
    # (doing it the Django-approved requires setting "DEBUG" to "False" in settings.py)
    # (but that means that other Python errors would never be displayed)
    url(r'^.*/$', 'questionnaire.views.q_404'),
)

# handler400 = 'questionnaire.views.q_400'  # bad request error
# handler403 = 'questionnaire.views.q_403'  # permission denied error
handler404 = 'questionnaire.views.q_404'  # page not found error
handler500 = 'questionnaire.views.q_500'  # server error