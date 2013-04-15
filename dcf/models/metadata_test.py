
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

from dcf.fields import *
from dcf.utils import *

class MetadataTest(models.Model):
    class Meta:
        app_label = APP_LABEL

    name = models.CharField(max_length=LIL_STRING)
    subModel = models.ForeignKey("MetadataTest",blank=True,null=True)

    def __unicode__(self):
        return u'MetadataTest: %s' % self.name



