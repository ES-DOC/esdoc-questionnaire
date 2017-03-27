####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.utils.translation import ugettext_lazy as _

from Q.questionnaire import APP_LABEL, q_logger
from Q.questionnaire.models.models_sites import get_site

# This is a custom UserProfile for the Q
# it includes Q-specific things
# I still use the built-in Django User for managing users
# however, I use django-allauth for authentication
# this lets me share users w/ registered OAuth providers (in the long-term)


class QUserProfile(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = 'Questionnaire User Profile'
        verbose_name_plural = 'Questionnaire User Profiles'

    # 1to1 relationship w/ standard Django User...
    user = models.OneToOneField(User, related_name='profile')

    # extra profile info associated w/ a Questionnaire User...
    projects = models.ManyToManyField("QProject", blank=True, verbose_name="Project Membership")
    change_password = models.BooleanField(default=False, verbose_name="Change password at next logon")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    institute = models.ForeignKey("QInstitute", blank=True, null=True, limit_choices_to={"is_active": True})
    institute.verbose_name = "Publication Institute"
    institute.help_text = _(
        "Please select the institute for which you intend to publish documents.  "
        "If no selection is made, you will be unable to publish."
    )

    @property
    def is_verified(self):
        if self.user.is_authenticated and not self.user.is_superuser:
            try:
                email = EmailAddress.objects.get(email=self.user.email)
                return email.verified
            except EmailAddress.DoesNotExist:
                pass
        return False

    def __str__(self):
        return str(self.user)

    def is_admin_of(self, project):
        project_admin_group = project.get_group("admin")
        return self.user in project_admin_group.user_set.all()

    def is_member_of(self, project):
        project_member_group = project.get_group("member")
        return self.user in project_member_group.user_set.all()

    def is_pending_of(self, project):
        project_pending_group = project.get_group("pending")
        return self.user in project_pending_group.user_set.all()

    def is_user_of(self, project):
        project_user_group = project.get_group("user")
        return self.user in project_user_group.user_set.all()

    def add_group(self, group):
        group.user_set.add(self.user)

    def remove_group(self, group):
        group.user_set.remove(self.user)

    def add_pending_permissions(self, project):
        pending_permission_group = project.get_group("pending")
        self.add_group(pending_permission_group)

    def add_member_permissions(self, project):
        member_permission_group = project.get_group("member")
        self.add_group(member_permission_group)

    def add_user_permissions(self, project):
        user_permission_group = project.get_group("user")
        self.add_group(user_permission_group)

    def add_admin_permissions(self, project):
        admin_permission_group = project.get_group("admin")
        self.add_group(admin_permission_group)

    def remove_admin_permissions(self, project):
        admin_permission_group = project.get_group("admin")
        self.remove_group(admin_permission_group)

    def remove_member_permissions(self, project):
        member_permission_group = project.get_group("member")
        self.remove_group(member_permission_group)

    def remove_pending_permissions(self, project):
        pending_permission_group = project.get_group("pending")
        self.remove_group(pending_permission_group)

    def remove_user_permissions(self, project):
        user_permission_group = project.get_group("user")
        self.remove_group(user_permission_group)

    def join_project(self, project):
        self.projects.add(project)
        self.remove_pending_permissions(project)
        self.add_member_permissions(project)
        self.add_user_permissions(project)

    def leave_project(self, project):
        self.projects.remove(project)
        self.remove_pending_permissions(project)
        self.remove_member_permissions(project)
        self.remove_user_permissions(project)
        self.remove_admin_permissions(project)

    def created(self):
        # this fns is referenced in "signals_users.py"
        mail_content = "User '{0}' created (on site '{1}').".format(
            self, get_site(),
        )
        mail_from = settings.EMAIL_HOST_USER
        mail_to = [settings.EMAIL_HOST_USER, ]

        try:

            send_mail(
                "ES-DOC Questionnaire user joined",
                mail_content,
                mail_from,
                mail_to,
                fail_silently=False
            )

        except Exception as e:
            q_logger.error(e)


def is_admin_of(user, project):
    if user.is_authenticated():
        return user.is_superuser or user.profile.is_admin_of(project)
    else:
        return False


def is_member_of(user, project):
    if user.is_authenticated():
        return user.is_superuser or user.profile.is_member_of(project)
    else:
        return False


def is_pending_of(user, project):
    if user.is_authenticated():
        return not user.is_superuser and user.profile.is_pending_of(project)
    else:
        return False


def is_user_of(user, project):
    if user.is_authenticated():
        return user.is_superuser or user.profile.is_user_of(project)
    else:
        return False


def get_institute(user):
    if user.is_authenticated():
        if user.is_superuser:
            return None
        else:
            return user.profile.institute
    else:
        return None

#######################
# user / project code #
#######################

def project_join_request(project, user, site=None):

    mail_content = "User '{0}' wants to join project '{1}'.  (Request sent from site '{2}.)".format(
        user.username, project.name, site,
    )
    mail_from = settings.EMAIL_HOST_USER
    mail_to = [settings.EMAIL_HOST_USER, ]

    try:

        send_mail(
            "ES-DOC Questionnaire project join request",
            mail_content,
            mail_from,
            mail_to,
            fail_silently=False
        )

        user.profile.add_pending_permissions(project)

        return True

    except Exception as e:
        q_logger.error(e)
        return False


def project_join(project, user, site=None):

    mail_content = "User '{0}' has joined project '{1}.".format(
        user.username, project.name,
    )
    mail_from = settings.EMAIL_HOST_USER
    mail_to = [user.email, project.email]
    try:

        send_mail(
            "ES-DOC Questionnaire project join request",
            mail_content,
            mail_from,
            mail_to,
            fail_silently=False
        )

        user.profile.join_project(project)

        return True

    except Exception as e:
        q_logger.error(e)
        return False
