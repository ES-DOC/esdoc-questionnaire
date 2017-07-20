####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.contrib.auth.models import Group, Permission, User
from django.utils.translation import ugettext_lazy as _
from django.db import models
import os

from Q.questionnaire import APP_LABEL
from Q.questionnaire.q_fields import OverwriteStorage
from Q.questionnaire.q_utils import validate_no_spaces, validate_no_bad_chars, validate_no_reserved_words, validate_no_profanities, validate_in_range
from Q.questionnaire.q_constants import *

# this is the set of groups & corresponding permissions that every project has...
GROUP_PERMISSIONS = {
    "pending": ["view", ],                     # able to view documents (has submitted join request)
    "member": ["view", ],                      # able to view documents
    "user": ["view", "edit", ],                # able to view, create, edit documents
    "admin": ["view", "edit", "customize", ],  # able to view, create, edit documents & customizations
}


def generate_upload_to(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<APP_LABEL>/projects/<project_name>/<filename>
    return os.path.join(APP_LABEL, "projects", instance.name, filename)


def validate_in_project_range(value):
    n_projects = QProject.objects.count()
    if n_projects:
        validate_in_range(value, [0, n_projects])
    else:
        validate_in_range(value, [0, 1])


class QProjectQuerySet(models.QuerySet):
    """
    As of Django 1.7 I can use custom querysets as managers
    to ensure that these custom methods are chainable
    whoo-hoo
    """

    def active_projects(self):
        return self.filter(is_active=True)

    def displayed_projects(self):
        return self.filter(is_displayed=True)


class QProject(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = 'Questionnaire Project'
        verbose_name_plural = 'Questionnaire Projects'

    LOGO_WIDTH = 96
    LOGO_HEIGHT = 96
    LOGO_SIZE = (LOGO_WIDTH, LOGO_HEIGHT)

    objects = QProjectQuerySet.as_manager()

    name = models.CharField(max_length=LIL_STRING, blank=False, unique=True, validators=[validate_no_spaces, validate_no_bad_chars, validate_no_reserved_words, validate_no_profanities])
    # name.help_text = _(
    #     "This is a unique name that identifies the project.  Choose wisely as, unlike the 'title', it will be used in various URLs."
    #     "  Note that this must match up w/ the project name used by other ES-DOC tools."
    # )
    title = models.CharField(max_length=LIL_STRING, blank=False, validators=[validate_no_profanities])
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(blank=False, validators=[validate_in_project_range])
    order.help_text = _(
        "What order should this project be presented in the index page?"
        "  This can be changed in the admin page listing <i>all</i> QProjects."

    )
    email = models.EmailField(blank=False, verbose_name="Contact Email")
    email.help_text = _(
        "Point of contact for this project."
    )
    url = models.URLField(blank=True)
    url.help_text = _(
       "External URL for this project."
    )
    # a logo submitted via the admin will be automatically resized to LOGO_SIZE
    # also, the "max_length" arg allows arbitrarily long filenames
    # also, the "storage" arg ensures the filename doesn't change after resizing
    logo = models.ImageField(upload_to=generate_upload_to, blank=True, null=True, max_length=None, storage=OverwriteStorage())
    logo.help_text = "All images will be resized to %s x %s." % LOGO_SIZE
    display_logo = models.BooleanField(blank=False, default=False)

    authenticated = models.BooleanField(blank=False, default=True)
    is_legacy = models.BooleanField(blank=False, default=False)
    is_legacy.help_text = "A legacy project is one that still uses CIM1;  If a legacy host is specified, then requests get routed there.  Do not check this unless you really know what you're doing."
    is_active = models.BooleanField(blank=False, default=True)
    is_active.help_text = "A project that is not active cannot be used"
    is_displayed = models.BooleanField(blank=False, default=True)
    is_displayed.help_text = "A project that is not displayed is not included in the Index Page, although users can still navigate to it if they know its URL"

    groups = models.ManyToManyField(Group, blank=True)

    ontologies = models.ManyToManyField(
        "QOntology",
        blank=True,
        through="QProjectOntology",  # note my use of the "through" model
        help_text="Only registered ontologies (schemas or specializations) can be added to projects.",
        verbose_name="Supported Ontologies",
    )

    def __str__(self):
        return "{0}".format(self.name)

    def __init__(self, *args, **kwargs):
        super(QProject, self).__init__(*args, **kwargs)
        if self.pk is None:
            self.order = QProject.objects.count()

    def clean(self):
        # force name to be lowercase
        # this avoids hacky methods of ensuring case-insensitive uniqueness
        # this also allows me to query the db w/out using the '__iexact' qualifier, which should reduce db hits
        self.name = self.name.lower()

    def save(self, *args, **kwargs):
        # if the name of this project has changed,
        # then the corresponding names of groups/permissions has to change along with it...
        if self.pk is not None:
            existing_project = QProject.objects.get(pk=self.pk)
            if self.name != existing_project.name:
                groups = self.groups.all()
                permissions = set([permission for group in groups for permission in group.permissions.all()])
                for group in groups:
                    group.name = group.name.replace(existing_project.name, self.name)
                    group.save()
                for permission in permissions:
                    permission.codename = permission.codename.replace(existing_project.name, self.name)
                    permission.name = permission.name.replace(existing_project.name, self.name)
                    permission.save()
        super(QProject, self).save(*args, **kwargs)

    def get_group(self, group_suffix):
        group_name = "{0}_{1}".format(self.name, group_suffix)
        return self.groups.get(name=group_name)

    def get_permission(self, permission_prefix):
        permission_codename = "{0}_{1}".format(permission_prefix, self.name)
        return Permission.objects.get(codename=permission_codename)

    # def get_group(self, group_suffix, create_group=False):
    #     group_name = u"%s_%s" % (self.name, group_suffix)
    #     try:
    #         group = Group.objects.get(name=group_name)
    #     except Group.DoesNotExist:
    #         group = Group(name=group_name)
    #         if create_group:
    #             group.save()
    #     return group

    # def get_permission(self, permission_prefix, create_permission=False):
    #     permission_codename = u"%s_%s" % (permission_prefix, self.name)
    #     permission_description = u"%s %s instances" % (permission_prefix, self.name)
    #     try:
    #         permission = Permission.objects.get(codename=permission_codename)
    #     except Permission.DoesNotExist:
    #         content_type = ContentType.objects.get(app_label=APP_LABEL, model='qproject')
    #         permission = Permission(codename=permission_codename, name=permission_description, content_type=content_type)
    #         if create_permission:
    #             permission.save()
    #     return permission

    def get_admin_users(self):
        admin_group = self.get_group("admin")
        if admin_group:
            return admin_group.user_set.all()
        else:
            return User.objects.none()

    def get_member_users(self):
        member_group = self.get_group("member")
        if member_group:
            return member_group.user_set.all()
        else:
            return User.objects.none()

    def get_pending_users(self):
        pending_group = self.get_group("pending")
        if pending_group:
            return pending_group.user_set.all()
        else:
            return User.objects.none()

    def get_user_users(self):
        user_group = self.get_group("user")
        if user_group:
            return user_group.user_set.all()
        else:
            return User.objects.none()

#################
# through model #
#################

    def add_ontology(self, ontology):
        project_ontology = QProjectOntology(
            project = self,
            ontology = ontology
        )
        project_ontology.save()

    def remove_ontology(self, ontology):
        project_ontology = QProjectOntology.objects.get(project=self, ontology=ontology)
        project_ontology.delete()


# this is explained elsewhere, but I am using a "through" model so that I have access to the save/delete fns/signals
# using the built-in m2m_changed signal is still buggy; it sends the "pre_clear" and "post_clear" signals prior to re-adding models
# which is extremely inefficient; instead I define this class and then add handlers for "post_save" and "post_delete" in signals_projects.py

class QProjectOntology(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "Questionnaire Project Ontology"
        verbose_name_plural = "Questionnaire Project Ontologies"
        unique_together = ("project", "ontology")

    project = models.ForeignKey(
        "QProject",
        related_name="+",  # don't create a backwards relation
    )
    ontology = models.ForeignKey(
        "QOntology",
        related_name="+",  # don't create a backwards relation
        limit_choices_to={"is_registered": True},
    )
