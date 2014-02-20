
####################
#   Django-CIM-Forms
#   Copyright (c) 2012 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Jun 10, 2013 4:11:53 PM"

"""
.. module:: metadata_project

Summary of module goes here

"""

from django.db import models
from django.contrib.auth.models import Group, Permission

from dcf.utils import *

# THIS IS THE SET OF GROUPS & CORRESPONDING PERMISSIONS THAT EVERY PROJECT HAS:
GROUP_PERMISSIONS = {
    "default"   : [ "view", ],                      # able to view instances
    "user"      : [ "view", "edit", ],              # default + able edit instances
    "admin"     : [ "view", "edit", "customize", ], # default + user + able to customize instances
}

class MetadataProject(models.Model):
    class Meta:
        app_label           = APP_LABEL
        abstract            = False
        # this is one of the few classes that I allow admin access to, so give it pretty names:
        verbose_name        = 'Metadata Project'
        verbose_name_plural = 'Metadata Projects'


    _guid = models.CharField(max_length=64,unique=True,editable=False,blank=False,default=lambda:str(uuid4()))

    name        = models.CharField(max_length=255,blank=False,unique=True,validators=[validate_no_spaces])
    title       = models.CharField(max_length=BIG_STRING,blank=False)
    description = models.TextField(blank=True)

    default_version     = models.ForeignKey("MetadataVersion",blank=True,null=True,related_name="project")

    restriction_customize   = models.CharField(max_length=64,blank=True,null=True)
    restriction_edit        = models.CharField(max_length=64,blank=True,null=True)

    authenticated           = models.BooleanField(default=False)

    def getGUID(self):
        return self._guid

    def __unicode__(self):
        if self.title:
            return u'%s' % self.title
        else:
            return u'%s' % self.name

    def getName(self):
        return self.name
    
    def getTitle(self):
        return self.title

    def getDefaultVersion(self):
        return self.default_version

    def get_group(self,group_suffix):
        group_name = "%s_%s" % (self.name,group_suffix)
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            group = Group(name=group_name)
            group.save()
        return group

    def get_all_groups(self):
        groups = []
        for group_suffix in GROUP_PERMISSIONS.keys():
            groups.append(self.get_group(group_suffix))
        return groups

    def get_permission(self,permission_prefix):
        permission_description  = "%s %s instances" % (permission_prefix,self.name)
        permission_codename     = "%s_%s" % (permission_prefix,self.name)
        try:
            permission = Permission.objects.get(codename=permission_codename)
        except Permission.DoesNotExist:
            content_type = ContentType.objects.get_for_model(self.__class__)
            permission = Permission(name=permission_description,codename=permission_codename,content_type=content_type)
            permission.save()
        return permission

from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

@receiver(post_save, sender=MetadataProject)
def project_post_save(sender, **kwargs):
    created = kwargs.pop("created",True)
    project = kwargs.pop("instance",None)
    if project and created:
        for group_suffix,permission_prefixes in GROUP_PERMISSIONS.iteritems():
            group = project.get_group(group_suffix)
            for permission_prefix in permission_prefixes:
                permission = project.get_permission(permission_prefix)
                group.permissions.add(permission)
            group.save()

@receiver(post_delete, sender=MetadataProject)
def project_post_delete(sender, **kwargs):
    project = kwargs.pop("instance",None)
    if project:
        groups = [project.get_group(group_suffix) for group_suffix in GROUP_PERMISSIONS.keys()]
        permissions = set([permission for group in groups for permission in group.permissions.all()])
        for permission in permissions:
            permission.delete()
        for group in groups:
            group.delete()
