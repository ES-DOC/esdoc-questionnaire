#    Django-CIM-Forms
#    Copyright (c) 2012 CoG. All rights reserved.
#
#    Developed by: Earth System CoG
#    University of Colorado, Boulder
#    http://cires.colorado.edu/
#
#    This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].

from django.conf import settings
from django.core import serializers

##################
# some constants #
##################

HUGE_STRING = 800
BIG_STRING  = 400
LIL_STRING  = 100

import re
strip_spaces        = lambda *s: re.sub(r'\s+',' ',*s).strip()
strip_underscores   = lambda *s: re.sub(r'_',' ',*s).strip()
pretty_string       = lambda *s: re.sub('(?<=[a-z])(?=[A-Z])',' ',strip_spaces(strip_underscores(*s))).title()

JSON_SERIALIZER = serializers.get_serializer("json")()

##################
# error handling #
##################

class MetadataError(Exception):
    def __init__(self,msg='unspecified metadata error'):
        self.msg = msg
    def __str__(self):
        return "MetadataError: " + self.msg

################################################################################
# some classes to manage lists of enumerated types (not metadata enumerations) #
# (used by models for fieldTypes & forms for subFormTypes and logging below)   #
################################################################################

class EnumeratedType(object):

    def __init__(self, type=None, name=None, cls=None):
        self._type  = type  # the key of this type
        self._name  = name  # the pretty name of this type
        self._class = cls   # the Python class used by this type (not always relevant)

    def getType(self):
        return self._type

    def getName(self):
        return self._name

    def getClass(self):
        return self._class

    def __unicode__(self):
        name = u'%s' % self._type
        return name

    # comparisons are made via the _type attribute...
    def __eq__(self,other):
        if isinstance(other,self.__class__):
            return self.getType() == other.getType()
        return False
    def __ne__(self,other):
        return not self.__eq__(other)

class EnumeratedTypeError(Exception):
    def __init__(self,msg='invalid enumerated type'):
        self.msg = msg
    def __str__(self):
        return "EnumeratedTypeError: " + self.msg

# this used to be based on deque to preserve FIFO order...
# but since I changed to adding fields to this list as needed in class's __init__() fn,
# that doesn't make much sense; so I'm basing it on a simple list
# and adding an ordering fn
class EnumeratedTypeList(list):

    def __getattr__(self,type):
        for et in self:
            if et.getType() == type:
                return et
        raise EnumeratedTypeError("unable to find %s" % str(type))

    # a method for sorting these lists
    # order is a list of EnumeratatedType._types
    @classmethod
    def comparator(cls,et,etOrderList):
        etType = et.getType()
        if etType in etOrderList:
            # if the type being compared is in the orderList, return it's position
            return etOrderList.index(etType)
        # otherwise return a value greater than the last position of the orderList
        return len(etOrderList)+1
