####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.forms import ValidationError, ModelForm, CharField, EmailField
from django.contrib.auth.forms import AdminPasswordChangeForm, AuthenticationForm, UserCreationForm
from django.utils.translation import ugettext_lazy as _

from Q.questionnaire.models.models_users import QUserProfile
from Q.questionnaire.q_utils import validate_no_bad_chars, update_field_widget_attributes, set_field_widget_attributes


class QUserProfileForm(ModelForm):

    class Meta:
        model = QUserProfile
        fields = ["first_name", "last_name", "description", "email", "institute"]

    first_name = CharField(label="First Name", required=False, validators=[validate_no_bad_chars])
    last_name = CharField(label="Last Name", required=False, validators=[validate_no_bad_chars])
    email = EmailField(label="Email")

    def __init__(self, *args, **kwargs):

        super(QUserProfileForm, self).__init__(*args, **kwargs)

        profile = self.instance
        user = profile.user

        self.fields["first_name"].initial = user.first_name
        self.fields["last_name"].initial = user.last_name
        self.fields["email"].initial = user.email

        update_field_widget_attributes(self.fields["email"], {"readonly": True})
        set_field_widget_attributes(self.fields["description"], {"rows": 2})

    def save(self, *args, **kwargs):

        commit = kwargs.get("commit", True)
        profile = super(QUserProfileForm, self).save(*args, **kwargs)

        user = profile.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()

        return profile
