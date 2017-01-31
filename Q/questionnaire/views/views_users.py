####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

# # note that there is a difference between the auth functions & views
# # the later use built-in forms, etc. while the former just perform the functionality
# from django.contrib.auth import authenticate, login as login_function
# from django.contrib.auth.views import logout as logout_view, password_change as password_change_view


from allauth.account.models import EmailAddress
from allauth.account.views import SignupView, LoginView, EmailView, ConfirmEmailView, PasswordResetView, PasswordResetFromKeyView, PasswordChangeView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.debug import sensitive_post_parameters
from honeypot.decorators import check_honeypot  # TODO

from Q.questionnaire.forms.forms_users import QUserProfileForm
from Q.questionnaire.views.views_base import add_parameters_to_context
from Q.questionnaire.views.views_errors import q_error


class QSignupView(SignupView):
    redirect_field_name = "next"
    template_name = 'account/q_signup.html'

    @property
    def success_url(self):
        """
        If no redirect parameter was passed, this is the location the view should goto
        :return:
        """
        return reverse("account_profile", kwargs={
            "username": self.request.POST["username"]
        })

q_signup = QSignupView.as_view()


class QLoginView(LoginView):
    """
    subclasses the default LoginView provided by allauth
    but uses a Q-specific Q-specific redirection
    (since I changed the url used to access UserProfiles)
    """
    redirect_field_name = "next"
    template_name = 'account/q_login.html'

    @property
    def success_url(self):
        """
        If no redirect parameter was passed, this is the location the view should goto
        :return:
        """
        return reverse("account_profile", kwargs={
            "username": self.request.POST["login"]
        })

q_login = QLoginView.as_view()


class QEmailView(EmailView):
    redirect_field_name = "next"
    template_name = "account/q_email.html"

    @property
    def success_url(self):
        """
        If no redirect parameter was passed, this is the location the view should goto
        :return:
        """
        email = self.request.POST["email"]
        email_address = EmailAddress.objects.get(email=email)
        user = email_address.user
        return reverse("account_profile", kwargs={
            "username": user.username
        })

q_email = login_required(QEmailView.as_view())


class QConfirmEmailView(ConfirmEmailView):
    redirect_field_name = "next"
    template_name = "account/q_confirm_email.html"

    # rather than overload the success_url fn
    # ConfirmEmailView makes use of the "get_email_confirmation_redirect_url" fn
    # and that has been overloaded by QAccountAdapter

q_confirm_email = QConfirmEmailView.as_view()


class QPasswordResetView(PasswordResetView):
    redirect_field_name = "next"
    template_name = "account/q_password_reset.html"

    @property
    def success_url(self):
        msg = "Successfully sent password reset email.  Please contact ES-DOC if you do not receive it within a short while."
        messages.add_message(self.request, messages.INFO, msg)
        user = self.request.user
        if user.is_authenticated():
            return reverse("account_profile", kwargs={
                "username": user.username
            })
        else:
            return reverse("index")

q_password_reset = QPasswordResetView.as_view()


class QPasswordResetFromKeyView(PasswordResetFromKeyView):
    redirect_field_name = "next"
    template_name = "account/q_password_reset_from_key.html"

    @property
    def success_url(self):
        user = self.request.user
        if user.is_authenticated():
            return reverse("account_profile", kwargs={
                "username": user.username
            })
        else:
            return reverse("index")

q_password_reset_from_key = QPasswordResetFromKeyView.as_view()


class QPasswordChangeView(PasswordChangeView):
    redirect_field_name = "next"
    template_name = "account/q_password_change.html"

    @property
    def success_url(self):
        user = self.request.user
        if user.is_authenticated():
            return reverse("account_profile", kwargs={
                "username": user.username
            })
        else:
            return reverse("index")


q_password_change = login_required(QPasswordChangeView.as_view())


def q_profile(request, username=None):
    context = add_parameters_to_context(request)
    next_page = context.get("next")

    current_user = request.user

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        if not username:
            msg = "Please specify a user."
        else:
            msg = "Unable to locate user '{0}'".format(username)
        return q_error(request, error_msg=msg)

    read_only = False
    if current_user.username != username:
        if not current_user.is_superuser:
            read_only = True
        # msg = "You do not have permission to edit this user."
        # return q_error(request, error_msg=msg)
    if user.is_superuser:
        msg = "You can't view the details of the site administrator.  Sheesh."
        return q_error(request, error_msg=msg)
    if not user.is_active:
        msg = "This user's account has been disabled."
        return q_error(request, error_msg=msg)

    user_profile = user.profile

    if request.method == "GET":

        user_form = QUserProfileForm(instance=user_profile)

    else:  # request.method == "POST":

        data = request.POST
        user_form = QUserProfileForm(instance=user_profile, data=data)
        if user_form.is_valid():

            msg = "Successfully changed user details."
            messages.add_message(request, messages.SUCCESS, msg)

            user_profile = user_form.save()
            if user_profile is not None:
                if next_page:
                    return HttpResponseRedirect(next_page)

        else:
            msg = "Error changing user details."
            messages.add_message(request, messages.WARNING, msg)

    template_context = {
        "user": user,
        "is_verified": user_profile.is_verified,
        "read_only": read_only,
        "form": user_form,
        "projects": user_profile.projects.all(),
    }

    return render_to_response('account/q_profile.html', template_context, context_instance=RequestContext(request))
