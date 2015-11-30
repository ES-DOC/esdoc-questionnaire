####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.debug import sensitive_post_parameters
from honeypot.decorators import check_honeypot
# note that there is a difference between the auth functions & views
# the later use built-in forms, etc. while the former just perform the functionality
from django.contrib.auth import authenticate, login as login_function
from django.contrib.auth.views import logout as logout_view, password_change as password_change_view
from django.contrib import messages

from Q.questionnaire.views.views_base import add_parameters_to_context
from Q.questionnaire.views.views_errors import q_error
from Q.questionnaire.forms.forms_users import QUserRegistrationForm, QUserLoginForm, QUserProfileForm, QUserPasswordForm


def q_user(request, user_name=None):

    current_user = request.user

    try:
        user = User.objects.get(username=user_name)
    except User.DoesNotExist:
        if not user_name:
            msg = u"Please specify a user."
        else:
            msg = u"Unable to locate user '%s'" % (user_name)
        return q_error(request, error_msg=msg)
    if current_user.username != user_name and not current_user.is_superuser:
        msg = u"You do not have permission to edit this user."
        return q_error(request, error_msg=msg)
    if user.is_superuser:
        msg = u"You can't edit the details of the site administrator.  Sheesh."
        return q_error(request, error_msg=msg)
    if not user.is_active:
        msg = u"This user's account has been disabled."
        return q_error(request, error_msg=msg)

    user_profile = user.profile

    context = add_parameters_to_context(request)
    next_page = context.get("next")

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

    # gather all the extra information required by the template
    _dict = {
        "user": user,
        "projects": user_profile.projects.all(),
        "form": user_form
    }

    return render_to_response('questionnaire/q_user.html', _dict, context_instance=RequestContext(request))


@sensitive_post_parameters()
def q_password(request, user_name=None):
    current_user = request.user

    try:
        user = User.objects.get(username=user_name)
    except User.DoesNotExist:
        if not user_name:
            msg = u"Please specify a user."
        else:
            msg = u"Unable to locate user '%s'" % (user_name)
        return q_error(request, error_msg=msg)
    if current_user.username != user_name:
        msg = u"You do not have permission to edit this user."
        return q_error(request, error_msg=msg)
    if not user.is_active:
        msg = u"This user's account has been disabled."
        return q_error(request, error_msg=msg)

    context = add_parameters_to_context(request)
    next_page = context.get("next", u"/users/%s" % user.username)

    response = password_change_view(
        request,
        template_name='questionnaire/q_password.html',
        post_change_redirect=next_page,
        password_change_form=QUserPasswordForm,
    )

    # if request.method == "POST" and response.status_code < 400:
    #     msg = "Successfully changed password."
    #     messages.add_message(request, messages.SUCCESS, msg)

    return response


@sensitive_post_parameters()
def q_login(request):

    context = add_parameters_to_context(request)
    next_page = context.get("next")

    if request.method == "GET":

        login_form = QUserLoginForm(request)

    else:  # request.method == "POST":

        data = request.POST
        login_form = QUserLoginForm(request, data=data)

        if login_form.is_valid():
            username = login_form.cleaned_data["username"]
            user_pwd = login_form.cleaned_data["password"]
            user = authenticate(username=username, password=user_pwd)
            if user is not None:
                if user.is_active:
                    login_function(request, user)

                    if next_page:
                        return HttpResponseRedirect(next_page)
                    else:
                        return HttpResponseRedirect("/")

        # no need to do additional processing; the forms will sort themselves out w/ errors
        # else:
        #     pass

    # gather all the extra information required by the template
    _dict = {
        "form": login_form,
    }

    return render_to_response('questionnaire/q_login.html', _dict, context_instance=context)


@sensitive_post_parameters()
def q_logout(request):

    # just use the built-in logout view
    return logout_view(request, next_page=request.GET.get("next"))


@check_honeypot
@sensitive_post_parameters()
def q_register(request):

    context = add_parameters_to_context(request)
    next_page = context.get("next")

    if request.method == "GET":

        registration_form = QUserRegistrationForm()

    else:  # request.method == "POST":

        data = request.POST
        registration_form = QUserRegistrationForm(data=data)

        if registration_form.is_valid():

            registration_form.save()
            new_username = registration_form.cleaned_data["username"]
            new_user_pwd = registration_form.cleaned_data["password1"]

            # need to authenticate new_user before logging in (Django is weird like that)
            new_user = authenticate(username=new_username, password=new_user_pwd)
            if new_user is not None:
                login_function(request, new_user)

                if next_page:
                    return HttpResponseRedirect(next_page)
                else:
                    return HttpResponseRedirect("/users/%s" % (new_username))

        # no need to do additional processing; the forms will sort themselves out w/ errors
        # else:
        #     pass

    # gather all the extra information required by the template
    _dict = {
        "form": registration_form,
    }

    return render_to_response('questionnaire/q_register.html', _dict, context_instance=context)