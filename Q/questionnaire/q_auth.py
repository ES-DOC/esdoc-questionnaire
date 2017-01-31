####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from allauth import app_settings
from allauth.account.adapter import DefaultAccountAdapter
from allauth.compat import is_authenticated
from allauth.utils import email_address_exists, resolve_url
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.forms import ValidationError as FormValidationError
import warnings

from Q.questionnaire.q_utils import validate_password


class QAccountAdapter(DefaultAccountAdapter):
    """
    Overriding some default django-allauth behavior to be Q-specific
    (as per http://django-allauth.readthedocs.io/en/latest/advanced.htm)

    """
    def get_from_email(self):
        """
        Use the email address specified in the Q configuration file
        instead of the built-in one used by django-allauth
        """
        return settings.EMAIL_HOST_USER

    def clean_password(self, password, user=None):
        """
        uses the Q-specific password validator
        """
        try:
            validate_password(password)
            return password
        except ValidationError as e:
            raise FormValidationError(e.message)

    # TODO: SHOULD I OVERRIDE THIS TO ALLOW DUPLICATES FOR SUPERUSERS?
    def validate_unique_email(self, email):
        """
        :param email:
        :return:
        """
        if email_address_exists(email):
            raise FormValidationError(self.error_messages['email_taken'])
        return email

    # need to override some of these redirection fns
    # b/c the Q uses a different URL for profiles than allauth

    def get_login_redirect_url(self, request):
        """
        Returns the default URL to redirect to after logging in.  Note
        that URLs passed explicitly (e.g. by passing along a `next`
        GET parameter) take precedence over the value returned here.
        """
        assert is_authenticated(request.user)
        url = getattr(settings, "LOGIN_REDIRECT_URLNAME", None)
        if url:
            warnings.warn("LOGIN_REDIRECT_URLNAME is deprecated, simply"
                          " use LOGIN_REDIRECT_URL with a URL name",
                          DeprecationWarning)
        else:
            # here is the different part...
            url = reverse("account_profile", kwargs={
                "username": request.user.username
            })
        return resolve_url(url)

    def get_logout_redirect_url(self, request):
        """
        Returns the URL to redirect to after the user logs out. Note that
        this method is also invoked if you attempt to log out while no users
        is logged in. Therefore, request.user is not guaranteed to be an
        authenticated user.
        """
        # here is the different bit...
        # return resolve_url(app_settings.LOGOUT_REDIRECT_URL)
        url = reverse("index")
        return resolve_url(url)

    def get_email_confirmation_redirect_url(self, request):
        """
        The URL to return to after successful e-mail confirmation.
        """
        if is_authenticated(request.user):
            # here is a different part...
            if getattr(app_settings, "EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL", None):
                return app_settings.EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL
            else:
                return self.get_login_redirect_url(request)
        else:
            # but here is the important different part...
            url = reverse("index")
            return resolve_url(url)
