
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
__date__ ="Jan 27, 2014 5:20:10 PM"

"""
.. module:: forms_authentication

Summary of module goes here

"""

from django.forms import *

from django.contrib.auth.forms  import PasswordChangeForm, AdminPasswordChangeForm, AuthenticationForm, UserCreationForm

# from django.utils.html          import mark_safe

from CIM_Questionnaire.questionnaire.models.metadata_authentication import MetadataUser, MetadataOpenIDProvider
from CIM_Questionnaire.questionnaire.utils import update_field_widget_attributes, validate_password, validate_no_bad_chars

class LocalAuthenticationForm(AuthenticationForm):

    @classmethod
    def get_title(cls):
        return "local account"


# class RemoteAuthenticationForm(forms.Form):
#     providers  = ChoiceField(choices=[None,None]) # this is overwritten in __init__, to dynamically load choices
#     username   = CharField(max_length=SMALL_STRING,label="Username (if needed)",required=False)
#
#     def __init__(self,*args,**kwargs):
#         super(RemoteAuthenticationForm,self).__init__(*args,**kwargs)
#         CHOICES = [(provider.id,mark_safe(u"<img align='center' title='%s' height='32px' src='%s'/>"%(provider.title,provider.icon.url))) for provider in MetadataOpenIDProvider.objects.filter(active=True)]
#         self.fields["providers"] = ChoiceField(choices=CHOICES,widget=RadioSelect())
#         update_field_widget_attributes(self.fields["providers"],{"class":"provider_choice"})
#
#     @classmethod
#     def get_title(cls):
#         return "open-id"


class MetadataPasswordForm(AdminPasswordChangeForm):
    pass

    def __init__(self,*args,**kwargs):
        user = kwargs.pop("instance",None)
        super(MetadataPasswordForm,self).__init__(user,*args,**kwargs)
        self.fields["password1"].validators = [validate_password,]
        self.fields["password1"].help_text = "Passwords must have a minimum length of 6 and a mixture of letters and non-letters."

# using a validator, defined in "utils.py," for this now
# (b/c I can re-use that code elsewhere)
#    def clean_password1(self):
#        password1 = self.cleaned_data.get('password1')
#        if len(password1) < 6:
#            raise forms.ValidationError("A password must contain at least %s characters" % (PASSWORD_LENGTH))
#        return password1

class MetadataUserForm(ModelForm):

    class Meta:
        model   = MetadataUser
        fields  = [
                    # "first_name","last_name","email","projects",
                    "first_name","last_name","email",
                  ]

    first_name = CharField(label="First Name",required=False,validators=[validate_no_bad_chars,])
    last_name  = CharField(label="Last Name",required=False,validators=[validate_no_bad_chars,])
    email      = EmailField(label="Email",required=False,validators=[validate_no_bad_chars,])

    def __init__(self,*args,**kwargs):
        super(MetadataUserForm,self).__init__(*args,**kwargs)

        metadata_user   = self.instance
        user            = metadata_user.user

        self.fields["first_name"].initial = user.first_name
        self.fields["last_name"].initial  = user.last_name
        # self.fields["projects"].help_text = None
        # self.fields["projects"].help_text = "Please contact the project to become a project member.  (Project contact details can be found on their landing page.)"
        #
        # update_field_widget_attributes(self.fields["projects"],{"readonly":"readonly"})

    def save(self,commit=True):
        first_name = self.cleaned_data["first_name"]
        last_name  = self.cleaned_data["last_name"]
        email      = self.cleaned_data["email"]

        metadata_user   = self.instance
        user            = metadata_user.user

        user.first_name = first_name
        user.last_name  = last_name
        user.email      = email

        if commit:
            user.save()
        return user


class MetadataRegistrationForm(UserCreationForm):
    pass

    def __init__(self,*args,**kwargs):
        super(MetadataRegistrationForm,self).__init__(*args,**kwargs)
        self.fields["password1"].validators = [validate_password,]
        self.fields["password1"].help_text = "Passwords must have a minimum length of 6 and a mixture of letters and non-letters."
        