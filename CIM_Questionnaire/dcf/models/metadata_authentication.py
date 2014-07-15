
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
__date__ ="Dec 9, 2013 4:13:03 PM"

"""
.. module:: users

Summary of module goes here

"""

from django.db import models
from django.contrib.auth.models import User
from dcf.utils import *

class MetadataUser(models.Model):

    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        verbose_name        = 'Metadata User'
        verbose_name_plural = 'Metadata Users'

    user = models.OneToOneField(User,related_name='metadata_user')
    projects = models.ManyToManyField("MetadataProject",null=True,blank=True,related_name="metadata_user")
    projects.verbose_name = "Project Membership"

    def __unicode__(self):
        return u'%s' % (self.user)

    def is_member_of(self,project):
        return project in self.projects.all()

    def is_user_of(self,project):
        user_group = project.get_group("user")
        return self.user in user_group.user_set.all()

    def is_admin_of(self,project):
        user_group = project.get_group("admin")
        return self.user in user_group.user_set.all()

    def join_project(self,project):
        self.projects.add(project)
        default_group = project.get_group("default")
        self.add_group(default_group)

    def leave_project(self,project):
        self.projects.remove(project)
        default_group = project.get_group("default")
        self.remove_group(default_group)
        self.remove_user_privileges(project)
        self.remove_admin_privileges(project)

    def add_user_privileges(self,project):
        user_group = project.get_group("user")
        self.add_group(user_group)

    def add_admin_privileges(self,project):
        admin_group = project.get_group("admin")
        self.add_group(admin_group)

    def remove_user_privileges(self,project):
        user_group = project.get_group("user")
        self.remove_group(user_group)

    def remove_admin_privileges(self,project):
        admin_group = project.get_group("admin")
        self.remove_group(admin_group)

    def add_group(self,group):
        group.user_set.add(self.user)

    def remove_group(self,group):
        group.user_set.remove(self.user)

from django.dispatch import receiver
from django.db.models.signals import post_save, m2m_changed
from django.db.utils import ProgrammingError

@receiver(post_save, sender=User)
def user_post_save(sender, **kwargs):
    created = kwargs.pop("created",True)
    user    = kwargs.pop("instance",None)
    if user and created:
        try:
            (metadata_user,created_metadata_user) = MetadataUser.objects.get_or_create(user=user)
        except ProgrammingError:
            if user.is_superuser:
                # this might fail in syncdb w/ the Django admin b/c the full set of db tables will not have been setup yet
                # that's ok, the admin doesn't need to be associated w/ a metadata_user; they have _all_ permissions for _all_ projects
                print "skipped creating user profile for %s" % (user)
                pass
            else:
                msg = "Unable to create user profile for %s" % (user)
                raise MetadataError(msg)

### THIS IS A KNOWN BUG IN DJANGO [https://code.djangoproject.com/ticket/16073]
### I CAN'T USE THIS SIGNAL
### I HAVE MANAGED TO GET THIS FUNCTIONALITY IN THE 'save_formset' FN IN 'admin/admin_authentication.py'
###@receiver(m2m_changed,sender=MetadataUser.projects.through)
###def user_projects_changed(sender, **kwargs):
###    user        = kwargs.pop("instance",None)
###    action      = kwargs.pop("action",None)
###    project_set = kwargs.pop("pk_set",set([]))
###
###    if action == "pre_delete":
###        print "REMOVING %s" % project_set
###    if action == "pre_add":
###        print "ADDING %s" % project_set

