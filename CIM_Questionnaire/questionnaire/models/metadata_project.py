
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
__date__ ="Oct 14, 2013 4:59:13 PM"

"""
.. module:: project

Summary of module goes here

"""

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, Permission

from CIM_Questionnaire.questionnaire import APP_LABEL
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer, MetadataModelCustomizer
from CIM_Questionnaire.questionnaire.utils import validate_no_spaces, validate_no_reserved_words, QuestionnaireError

# THIS IS THE SET OF GROUPS & CORRESPONDING PERMISSIONS THAT EVERY PROJECT HAS:
GROUP_PERMISSIONS = {
    "default"   : [ "view", ],                      # able to view instances
    "user"      : [ "view", "edit", ],              # default + able edit instances
    "admin"     : [ "view", "edit", "customize", ], # default + user + able to customize instances
}

class MetadataProject(models.Model):
    class Meta:
        app_label = APP_LABEL
        abstract = False

        # this is one of the few classes that I allow admin access to, so give it pretty names:
        verbose_name        = 'Metadata Project'
        verbose_name_plural = 'Metadata Projects'

    name          = models.CharField(max_length=255,blank=False,unique=True,validators=[validate_no_spaces,validate_no_reserved_words])
    title         = models.CharField(max_length=255,blank=False)
    description   = models.TextField(blank=True)
    url           = models.URLField(blank=True)
    providers     = models.ManyToManyField("MetadataOpenIDProvider",blank=True)
    vocabularies  = models.ManyToManyField("MetadataVocabulary", blank=True, null=True, through="MetadataProjectVocabulary") # note my use of the 'through' kwarg; this is to detect changes in the vocabularies m2m relationship
    active        = models.BooleanField(blank=False,null=False,default=True)
    authenticated = models.BooleanField(blank=False,null=False,default=False)
    email         = models.EmailField(blank=True,null=True,verbose_name="Contact Email")

    def __unicode__(self):
        return u'%s' % self.name

    def clean(self):
        # force name to be lowercase
        # this avoids hacky methods of ensuring case-insensitive uniqueness
        # this also allows me to query the db w/out using the '__iexact' qualifier, which should reduce db hits
        self.name = self.name.lower()

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

    def add_vocabulary(self, vocabulary):
        project_vocabulary_relationship = MetadataProjectVocabulary(project=self, vocabulary = vocabulary)
        project_vocabulary_relationship.save()

    def remove_vocabulary(self, vocabulary):
        try:
            project_vocabulary_relationship = MetadataProjectVocabulary.objects.get(project=self, vocabulary=vocabulary)
            project_vocabulary_relationship.delete()
        except MetadataProjectVocabulary.DoesNotExist:
            msg = "Vocabulary %s is not associated w/ project %s" % (vocabulary, self)
            raise QuestionnaireError(msg)

from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, m2m_changed

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


# a known Django bug prevents this signal from being fired from the admin
# see https://code.djangoproject.com/ticket/16073
# so I just track the changes myself (see MetadataProjectVocabulary below used as the 'through' table for the vocabularies field)
# @receiver(m2m_changed, sender=MetadataProject.vocabularies.through)
# def project_vocabularies_changed(sender, **kwargs):
# pass


# NOTE THAT SETTING UP THIS CLASS REQUIRED ME TO OVERWRITE SOME OF THE MIGRATION CODE
# (see questionnaire/migrations/0026...)
class MetadataProjectVocabulary(models.Model):
    class Meta:
        app_label = APP_LABEL
        abstract = False
        unique_together = ("project", "vocabulary")

    project = models.ForeignKey("MetadataProject")
    vocabulary = models.ForeignKey("MetadataVocabulary")

    # TODO: IS THERE ANY WAY TO TRIGGER AN UPDATE OF CUSTOMIZERS & REALIZATIONS
    # TODO: ONLY WHEN _ALL_ MetadataProjectVocabularies HAVE BEEN SAVED/DELETED?

    def save(self, *args, **kwargs):
        super(MetadataProjectVocabulary, self).save(*args, **kwargs)
        new_vocabulary = self.vocabulary
        customizers_to_update = MetadataModelCustomizer.objects.filter(project=self.project, proxy__name__iexact=new_vocabulary.document_type)
        for customizer_to_update in customizers_to_update:
            vocabularies = list(customizer_to_update.vocabularies.all())
            vocabularies.append(new_vocabulary)
            MetadataCustomizer.update_existing_customizer_set(customizer_to_update, vocabularies)
        # TODO: DO THE SAME THING FOR REALIZATIONS?

    def delete(self, *args, **kwargs):
        super(MetadataProjectVocabulary, self).delete(*args, **kwargs)
        old_vocabulary = self.vocabulary
        customizers_to_update = MetadataModelCustomizer.objects.filter(project=self.project, proxy__name__iexact=old_vocabulary.document_type)
        for customizer_to_update in customizers_to_update:
            vocabularies = list(customizer_to_update.vocabularies.all())
            try:
                vocabularies.remove(old_vocabulary)
                MetadataCustomizer.update_existing_customizer_set(customizer_to_update, vocabularies)
            except ValueError:
                # old_vocabulary wasn't active in the customizer so no need to update it
                pass
        # TODO: DO THE SAME THING FOR REALIZATIONS?
