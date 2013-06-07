
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
__date__ ="Apr 9, 2013 10:27:48 PM"

"""
.. module:: metadata_test

Summary of module goes here

"""

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

from django.db import models
from django.db.models.signals import pre_save

import os

from dcf.fields import *
from dcf.utils import *

class MetadataTest(models.Model):
    class Meta:
        app_label = APP_LABEL

    name = models.CharField(max_length=LIL_STRING)
    subModel = models.ForeignKey("MetadataTest",blank=True,null=True)

    def __unicode__(self):
        return u'MetadataTest: %s' % self.name



_UPLOAD_DIR  = "test"
_UPLOAD_PATH = os.path.join(APP_LABEL,_UPLOAD_DIR)

class MetadataTestFileModel(models.Model):
    class Meta:
        app_label = APP_LABEL

    name = models.CharField(max_length=LIL_STRING,blank=True,null=True,unique=True)
    file = models.FileField(upload_to=_UPLOAD_PATH)

# in code..
# x = MetadataTestFileModel()
# f = open("file.txt")
# x.file = File(f)
# x.save()

    def save(self, *args, **kwargs):


        file_name = os.path.basename(self.file.name)
        file_path = os.path.join(settings.MEDIA_ROOT,APP_LABEL,_UPLOAD_DIR,file_name)

        print "file_name=%s" % file_name
        print "file_path=%s" % file_path

        if not self.name:
            self.name = file_name

        if os.path.exists(file_path):
            print "WARNING: THE FILE '%s' ALREADY EXISTS; IT IS BEING OVERWRITTEN." % file_path
            os.remove(file_path)


        super(MetadataTestFileModel, self).save(*args, **kwargs)

    
def check_file(sender, instance, *args, **kwargs):
    print "check_file"
    
pre_save.connect(check_file, sender=MetadataTestFileModel)

