####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2014 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"
__date__ = "Dec 01, 2014 3:00:00 PM"

"""
.. module:: forms_authentication

Forms used for registering, viewing, authenticating, modifying users
"""

from django.forms import *
from django.contrib.auth.forms import AdminPasswordChangeForm, AuthenticationForm, UserCreationForm
from django.utils.translation import ugettext_lazy as _

from CIM_Questionnaire.questionnaire.models.metadata_authentication import MetadataUser
from CIM_Questionnaire.questionnaire.utils import validate_password, validate_no_bad_chars


class LocalAuthenticationForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super(LocalAuthenticationForm, self).__init__(*args, **kwargs)

        # replace the default Django authentication error messages...
        self.error_messages = {
            "invalid_login": _("Please enter a correct %(username)s and password. "
                               "Note that both fields are case-sensitive."),
            "inactive": _("This account is inactive."),
        }

    @classmethod
    def get_title(cls):
        return "local account"


# class RemoteAuthenticationForm(forms.Form):
#     providers  = ChoiceField(choices=[None,None]) # this is overwritten in __init__, to dynamically load choices
#     username   = CharField(max_length=SMALL_STRING,label="Username (if needed)",required=False)
#
#     def __init__(self,*args,**kwargs):
#         super(RemoteAuthenticationForm,self).__init__(*args,**kwargs)
#         CHOICES = [(provider.id,mark_safe(u"<img align='center' title='%s' height='32px' src='%s'/>" %
#                    (provider.title,provider.icon.url)))
#                    for provider in MetadataOpenIDProvider.objects.filter(active=True)
#                   ]
#         self.fields["providers"] = ChoiceField(choices=CHOICES,widget=RadioSelect())
#         update_field_widget_attributes(self.fields["providers"],{"class":"provider_choice"})
#
#     @classmethod
#     def get_title(cls):
#         return "open-id"


class MetadataPasswordForm(AdminPasswordChangeForm):
    pass

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("instance", None)
        super(MetadataPasswordForm, self).__init__(user, *args, **kwargs)
        self.fields["password1"].validators = [validate_password, ]
        self.fields["password1"].help_text = \
            "Passwords must have a minimum length of 6 and a mixture of letters and non-letters."


class MetadataUserForm(ModelForm):

    class Meta:
        model = MetadataUser
        fields = ["first_name", "last_name", "email", ]

    first_name = CharField(label="First Name", required=False, validators=[validate_no_bad_chars, ])
    last_name = CharField(label="Last Name", required=False, validators=[validate_no_bad_chars, ])
    email = EmailField(label="Email", required=False, validators=[validate_no_bad_chars, ])

    def __init__(self, *args, **kwargs):
        super(MetadataUserForm, self).__init__(*args, **kwargs)

        metadata_user = self.instance
        user = metadata_user.user

        self.fields["first_name"].initial = user.first_name
        self.fields["last_name"].initial = user.last_name
        # self.fields["projects"].help_text = None
        # update_field_widget_attributes(self.fields["projects"], {"readonly": "readonly"})

    def save(self, commit=True):
        first_name = self.cleaned_data["first_name"]
        last_name = self.cleaned_data["last_name"]
        email = self.cleaned_data["email"]

        metadata_user = self.instance
        user = metadata_user.user

        user.first_name = first_name
        user.last_name = last_name
        user.email = email

        if commit:
            user.save()
        return user


class MetadataRegistrationForm(UserCreationForm):
    pass

    def __init__(self, *args, **kwargs):
        super(MetadataRegistrationForm, self).__init__(*args, **kwargs)
        self.fields["password1"].validators = [validate_password, ]
        self.fields["password1"].help_text = \
            "Passwords must have a minimum length of 6 and a mixture of letters and non-letters."
