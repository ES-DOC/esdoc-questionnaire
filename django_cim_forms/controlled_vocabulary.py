import urllib2
from lxml import etree as et
from django.db import models
from django.core.urlresolvers import reverse

import os
rel = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

from django_cim_forms.helpers import *

###############################
# code for CVs & Enumerations #
###############################

CV_PROTOCOL = "http"
CV_DOMAIN = "localhost"
CV_PORT= "8000"
CV_PATH = "/medatadata/cv"
CV_ROOT = rel('cv/')
CV_URL = CV_PROTOCOL + "://" + CV_DOMAIN + ":" + CV_PORT + CV_PATH

def get_cv_remote(cv_name):
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

def get_cv_local(cv_name):
    try:
        cv_filepath  = CV_ROOT + cv_name + ".xml"
        print cv_filepath
        cv_file = open(cv_filepath, 'r')
        cv_text = cv_file.read()
        cv_file.close()
        return cv_text
    except IOError, e:
        msg = e.strerror
        raise MetadataError(msg)

def get_cv(cv_name):
    # TODO: get_cv_remote is timing out... why?
    return get_cv_local(cv_name)
    cv = None
    try:
        cv = get_cv_remote(cv_name)
    except CvError:
        cv = get_cv_local(cv_name)
    return cv

