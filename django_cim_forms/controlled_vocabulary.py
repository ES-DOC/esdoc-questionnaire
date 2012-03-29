import urllib2
from lxml import etree as et
from django.db import models
from django.core.urlresolvers import reverse

from django_cim_forms.helpers import *

###############################
# code for CVs & Enumerations #
###############################

CV_PROTOCOL = "http"
CV_DOMAIN = "localhost"
CV_PORT= "8000"
CV_PATH = "/medatadata/cv"

CV_URL = CV_PROTOCOL + "://" + CV_DOMAIN + ":" + CV_PORT + CV_PATH

def get_cv(cv_name):
    CV_URL = reverse('django_cim_forms.views_cv.detail')
    cv_url = CV_URL + cv_name
    cv_request = urllib2.Request(cv_url)
    try:
        cv_response = urllib2.urlopen(cv_request)
    except urllib2.HTTPError, e:
        error_msg = "request to %s failed with code %s" % (cv_url, e.code)
        raise CvError(msg=error_msg)
    except urllib2.URLError, e:
        msg = "unable to reach %s; %s" % (cv_url, e.reason)
        raise MetadataError(msg)
    else:
        return cv_response.read()

class MetadataCV(models.Model):
    pass

class MetadataEnumeration(models.Model):

    name = models.CharField(max_length=25,blank=False)

    class Meta:
        abstract = True

    def __unicode__(self):
        return u'%s' % self.name

    @classmethod
    def add(cls,*args,**kwargs):
        name = kwargs.pop("name",None)
        if name:
            cls.objects.get_or_create(name=name)

    @classmethod
    def loadEnumerations(cls,*args,**kwargs):
        enum = kwargs.pop("enum",[])
        cls._enum = enum
        for name in enum:
            cls.add(name=name)
