
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
__date__ ="Jan 31, 2013 11:26:17 AM"

"""
.. module:: metadata_project

Summary of module goes here

"""

from django.core.exceptions import ValidationError

from dcf.utils import *

@guid()
class MetadataProject(models.Model):

    class Meta:
        app_label = APP_LABEL
        verbose_name = 'Metadata Project'
        verbose_name_plural = 'Metadata Projects'

    name        = models.CharField(max_length=LIL_STRING,blank=False,unique=True,validators=[validate_no_spaces])
    long_name   = models.CharField(max_length=BIG_STRING,blank=True)
    description = models.TextField(blank=True)
    
    default_version     = models.ForeignKey("MetadataVersion",blank=True,null=True,related_name="project")
    default_vocabulary  = models.ForeignKey("MetadataVocabulary",blank=True,null=True,related_name="project")
    versions            = models.ManyToManyField("MetadataVersion",blank=True,null=True,verbose_name="Associated Versions")
    vocabularies        = models.ManyToManyField("MetadataVocabulary",blank=True,null=True,verbose_name="Associated Vocabularies")


    def __unicode__(self):
        if self.long_name:
            return u'%s' % self.long_name
        else:
            return u'%s' % self.name
        
    def getDefaultVersion(self):
        return self.default_version

    def getDefaultVocabulary(self):
        return self.default_vocabulary

# cannot use clean here b/c saving m2m fields is a two-sept process
# versions is not set when this is called
# so I use a custom clean method on the admin form for MetadataProjects
# (since these are only ever modified in the admin anyway)
#    def clean(self, *args, **kwargs):
#        default_version = self.default_version
#        if not self in default_version.getProjects():
#           raise ValidationError("A project's default_version must be it's the set of versions")
#         super(MetadataProject,self).clean(*args,**kwargs)
            