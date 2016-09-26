####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

from django.forms import ValidationError, ModelForm, CharField, EmailField
from django.contrib.auth.forms import AdminPasswordChangeForm, AuthenticationForm, UserCreationForm
from django.utils.translation import ugettext_lazy as _

from Q.questionnaire.forms.forms_base import bootstrap_form
from Q.questionnaire.models.models_users import QUserProfile
from Q.questionnaire.q_utils import validate_no_spaces, validate_no_bad_chars, validate_password, update_field_widget_attributes
from Q.questionnaire.q_constants import PASSWORD_LENGTH


class QUserRegistrationForm(UserCreationForm):
    """
    Just like the standard Django UserCreationForm,
    except it has some extra validators on the password
    """

    def __init__(self, *args, **kwargs):
        super(QUserRegistrationForm, self).__init__(*args, **kwargs)
        bootstrap_form(self)
        self.fields["password1"].validators = [validate_no_spaces, validate_password, ]
        self.fields["password1"].help_text = \
            "Passwords must have a minimum length of %s and a mixture of letters and non-letters." % (PASSWORD_LENGTH)


class QUserPasswordForm(AdminPasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super(QUserPasswordForm, self).__init__(*args, **kwargs)
        bootstrap_form(self)
        self.fields["password1"].validators = [validate_no_spaces, validate_password, ]
        self.fields["password1"].help_text = \
            "Passwords must have a minimum length of %s and a mixture of letters and non-letters." % (PASSWORD_LENGTH)


class QUserLoginForm(AuthenticationForm):
    """
    Just like the standard Django AuthenticationForm,
    except it has some custom error messages
    """

    def confirm_login_allowed(self, user):
        """
        ensure that only "active" users can login
        :param user:
        :return:
        """
        if not user.is_active:

            raise ValidationError(
                self.error_messages["inactive"],
                code='inactive',
            )

    def __init__(self, *args, **kwargs):
        super(QUserLoginForm, self).__init__(*args, **kwargs)
        bootstrap_form(self)
        # replace the default Django authentication error messages...
        self.error_messages = {
            "invalid_login": _("Please enter a correct %(username)s and password. "
                               "Note that both fields are case-sensitive."),
            "inactive": _("This account is inactive.  "
                          "Please contact the administrator if you believe this is incorrect."),
        }


class QUserProfileForm(ModelForm):

    class Meta:
        model = QUserProfile
        fields = ["first_name", "last_name", "email", "institute", ]

    first_name = CharField(label="First Name", required=False, validators=[validate_no_bad_chars, ])
    last_name = CharField(label="Last Name", required=False, validators=[validate_no_bad_chars, ])
    email = EmailField(label="Email", required=False, validators=[validate_no_bad_chars, ])

    def __init__(self, *args, **kwargs):

        super(QUserProfileForm, self).__init__(*args, **kwargs)
        bootstrap_form(self)

        profile = self.instance
        user = profile.user

        self.fields["first_name"].initial = user.first_name
        self.fields["last_name"].initial = user.last_name
        self.fields["email"].initial = user.email

    def save(self, *args, **kwargs):

        commit = kwargs.get("commit", True)
        profile = super(QUserProfileForm, self).save(*args, **kwargs)

        user = profile.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()

        return profile
