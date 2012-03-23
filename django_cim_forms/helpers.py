# module imports
from functools import wraps
from django.conf import settings
from collections import deque
from django.core import serializers

####################################################
# some useful helpers for the metadata application #
####################################################

##################
# some constants #
##################

BIG_STRING = 100
LIL_STRING = 25

json_serializer = serializers.get_serializer("json")()

################################################################################
# some classes to manage lists of enumerated types (not metadata enumerations) #
# (used by models for fieldTypes & forms for subFormTypes and logging below)   #
################################################################################

class EnumeratedType(object):

    def __init__(self, type=None, name=None, cls=None):
        self._type = type # the key of this type
        self._name = name # the pretty name of this type
        self._class = cls # the Python class used by this type (not always relevant)

    def getType(self):
        return self._type

    def getName(self):
        return self._name

    def getClass(self):
        return self._class

    # comparisons of ets are made via their _type attribute...
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

# basing this on deque preserves FIFO order...
class EnumeratedTypeList(deque):

    def __getattr__(self,type):
        for et in self:
            if et.getType() == type:
                return et
        raise EnumeratedTypeError("unable to find %s" % str(type))

#################################################################################
# decorators to log methods/classes                                             #
# this isn't full-featured logging; it basically just echoes the call to stdout #
#################################################################################

class LoggingType(EnumeratedType):
    def __init__(self, type=None, name=None, value=None):
        super(LoggingType,self).__init__(type,name)
        self._value = value # the value of this type

    def getValue(self):
        return self._value

LoggingTypes = EnumeratedTypeList([
    LoggingType("NONE","no logging",0),
    LoggingType("SOME","some logging",1),
    LoggingType("FULL","all logging",2),
])

# there really isn't a good way to distinguish between methods and class methods
# so I've written two separate decorators for logging

def log_fn(logging_type=LoggingTypes.SOME):
    def _decorator(fn):
        @wraps(fn)
        def _wrapper_for_fn(*args,**kwargs):
            if settings.DEBUG:
                logging_value = logging_type.getValue()
                if logging_value==LoggingTypes.NONE.getValue():
                    print ""
                if logging_value>=LoggingTypes.SOME.getValue():
                    print "calling '%s'" % fn.__name__
                if logging_value>=LoggingTypes.FULL.getValue():
                    arglist = ", ".join(map(str,args))
                    if kwargs:
                        # this only gets provided kwargs; not default kwargs
                        arglist += ", "
                        arglist += ", ".join(map(lambda kw: "%s=%s" % (kw, str(kwargs[kw])), kwargs.keys()))
                    print "with arguments: (%s)" % arglist
                    #fn_args, fn_vargs, fn_kwargs, fn_defaults = inspect.getargspec(fn)
            return fn(*args,**kwargs)
        return _wrapper_for_fn
    return _decorator

def log_class_fn(logging_type=LoggingTypes.SOME):
    def _decorator(fn):
        @wraps(fn)
        def _wrapper_for_class_fn(*args,**kwargs):
            if settings.DEBUG:
                logging_value = logging_type.getValue()
                if logging_value>=LoggingTypes.NONE.getValue():
                    print ""
                if logging_value>=LoggingTypes.SOME.getValue():
                    # the first argument of a class method will be self...
                    print "calling '%s.%s'" % (args[0].__class__.__name__,fn.__name__)
                if logging_value>=LoggingTypes.FULL.getValue():
                    # so I slice it from the arglist here...
                    arglist = ", ".join(map(str,args[1:]))
                    if kwargs:
                        # this only gets provided kwargs; not default kwargs
                        arglist += ", "
                        arglist += ", ".join(map(lambda kw: "%s=%s" % (kw, str(kwargs[kw])), kwargs.keys()))
                    print "with arguments: (%s)" % arglist
                    #fn_args, fn_vargs, fn_kwargs, fn_defaults = inspect.getargspec(fn)
            return fn(*args,**kwargs)
        return _wrapper_for_class_fn
    return _decorator

##################
# error handling #
##################

# TODO: add useful information to this exception...
class MetadataError(Exception):
    def __init__(self,msg='unspecified error'):
        self.msg = msg
    def __str__(self):
        return "MetadataError: " + self.msg
