
####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Sep 30, 2013 3:04:42 PM"

"""
.. module:: views_authenticate

Summary of module goes here

"""

from django.contrib.auth        import authenticate, login, logout

from django.contrib.auth.models import User
from django.utils.html  import mark_safe
from django             import forms

from questionnaire.utils  import *
from questionnaire.views  import *
from questionnaire.forms  import *
from questionnaire.models import *

def questionnaire_login(request):

    next = ""
    if request.GET:
        next = request.GET['next']

    if request.method == "POST":

        local_form  = LocalAuthenticationForm(data=request.POST,prefix="local")
        remote_form = RemoteAuthenticationForm(request.POST,prefix="remote")

        if 'local' in request.POST:

            remove_form_errors(remote_form)

            if local_form.is_valid():
                username = local_form.cleaned_data["username"]
                password = local_form.cleaned_data["password"]
                user = authenticate(username=username, password=password)
                if user is not None:
                    if user.is_active:
                        login(request,user)

                        if next:
                            return HttpResponseRedirect(next)
                        else:
                            return HttpResponseRedirect("/")
                     
        elif "remote" in request.POST:

            remove_form_errors(local_form)
            
            if remote_form.is_valid():
                provider_id  = remote_form.cleaned_data["providers"]
                provider     = QuestionnaireProvider.objects.get(id=provider_id)
                username     = remote_form.cleaned_data["username"]
                provider_url = provider.url.replace("{username}",username)
                #I AM HERE
                return HttpResponseRedirect(provider_url)
                print provider_url
                # goto provider_url and get authentication

                if next:
                    return HttpResponseRedirect(next)
                else:
                    return HttpResponseRedirect("/")

    else:   # request.method == "GET"

        local_form  = LocalAuthenticationForm(prefix="local")
        remote_form = RemoteAuthenticationForm(prefix="remote")

    forms = [remote_form,local_form]


    # gather all the extra information required by the template
    dict = {
        "site"    : get_current_site(request),
        "forms"   : forms,
        "next"    : next,
        "questionnaire_version" : get_version(),
    }

    return render_to_response('questionnaire/questionnaire_login.html', dict, context_instance=RequestContext(request))


def questionnaire_logout(request):

     return render_to_response('questionnaire/questionnaire_logout.html', { }, context_instance=RequestContext(request))


@sensitive_post_parameters()
def questionnaire_user(request,user_name=""):
    try:
        user            = User.objects.get(username=user_name)
        metadata_user   = user.metadata_user
    except User.DoesNotExist:
        msg = "Unable to locate user '%s'" % (user_name)
        return error(request,msg)
    if user.is_superuser:
        msg = "You can't edit details of the site administrator.  Sheesh."
        return error(request,msg)

    current_user = request.user
    if current_user.username != user_name and not current_user.is_superuser:
        msg = "You do not have permission to edit this user."
        return error(request,msg)

    if request.method == "POST":

        password_form  = MetadataPasswordForm(request.POST,instance=user)
        user_form = MetadataUserForm(request.POST,instance=metadata_user)

        if "password_submit" in request.POST:
            remove_form_errors(user_form)
            if password_form.is_valid():
                password_form.save()
                messages.add_message(request, messages.SUCCESS, "Successfully changed password for '%s'" % (user))

        elif "user_submit" in request.POST:
            remove_form_errors(password_form)
            if user_form.is_valid():
                user_form.save()
                messages.add_message(request, messages.SUCCESS, "Successfully changed user details for '%s'" % (user))
        else:
            msg = "unknown action recieved."
            messages.add_message(request, messages.ERROR, msg)


    else:   # request.method == "GET"

        password_form = MetadataPasswordForm(instance=user)
        user_form     = MetadataUserForm(instance=metadata_user)


    # gather all the extra information required by the template
    dict = {
        "site"           : get_current_site(request),
        "user"           : user,
        "password_form"  : password_form,
        "user_form"      : user_form,
        "questionnaire_version" : get_version(),
    }

    return render_to_response('questionnaire/questionnaire_user.html', dict, context_instance=RequestContext(request))

@sensitive_post_parameters()
def questionnaire_register(request):

    next = ""
    if request.GET:
        next = request.GET['next']

    if request.method == 'POST':
        registration_form = MetadataRegistrationForm(request.POST)
        if registration_form.is_valid():
            new_user     = registration_form.save()
            new_username = registration_form.cleaned_data["username"]
            new_user_pwd = registration_form.cleaned_data["password1"]

            # need to authenticate the user before using it to ensure that backend is set
            # (django is weird like this)
            login(request,authenticate(username=new_username,password=new_user_pwd))

            if next:
                return HttpResponseRedirect(next)
            else:
                return HttpResponseRedirect("/user/%s"%(new_username))
        else:
            msg = "Unable to register user."
            messages.add_message(request, messages.ERROR, msg)
    else:
        registration_form = MetadataRegistrationForm()

    # gather all the extra information required by the template
    dict = {
        "site"                  : get_current_site(request),
        "form"                  : registration_form,
        "questionnaire_version" : get_version(),
    }


    return render_to_response('questionnaire/questionnaire_register.html', dict, context_instance=RequestContext(request))
