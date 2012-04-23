import urllib2
from lxml import etree as et
from django.db import models
from django.core.urlresolvers import reverse

import os
rel = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

import re
strip_completely = lambda *s: re.sub(r'\s+',' ',*s).strip()

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


#########
# Enums #
#########

class MetadataEnumeration(models.Model):

    name = models.CharField(max_length=BIG_STRING,blank=False)

    class Meta:
        abstract = True
        #order_with_respect_to = 'name'

    def __unicode__(self):
        return u'%s' % self.name

    @classmethod
    def loadEnumerations(cls,*args,**kwargs):
        enum = kwargs.pop("enum",cls._enum)
        enum.sort()
        for name in enum:
            cls.objects.get_or_create(name=name)


def get_enumeration(enumerationClass,enumerationName):
    try:
        enumeration = enumerationClass.objects.get(name=enumerationName)
        return enumeration
    except enumerationClass.DoesNotExist:
        return None
        
#######
# CVs #
#######

class MetadataControlledVocabularyValueField(models.TextField):
    # values is a list of '||' separated terms;
    # each term is a list of '|' separated terms
    # eg: "shortName1|longName1||shortName2|longName2||shortName3||shortName4|longName4"
    # this gets serialized to a list of tuples
    # eg: [(shortname1,longName1),(shortName2,longName2),(shortName3,shortName3),(shortName4,longName4)]

    __metaclass__ = models.SubfieldBase

    value_separator_token = "||"
    value_name_separator_token = "|"

    def to_python(self, values):
        if not values:
            # return nothing if there is no value
            return
        elif isinstance(values,list):
            # return value if it's already a list
            return values
        else:
            # otherwise create a list (of lists)
            return [tuple(val.split(self.value_name_separator_token)) for val in values.split(self.value_separator_token) if val]

    def get_db_prep_value(self, values):
        if not values:
            return
        assert(isinstance(values, list) or isinstance(values, tuple))

        return self.value_separator_token.join([self.value_name_separator_token.join(val) for val in values])

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

class MetadataControlledVocabulary(models.Model):

    class Meta:
        abstract = True

    _name = "MetadataControlledVocabulary"

    shortName = models.CharField(max_length=HUGE_STRING,blank=False)
    longName = models.CharField(max_length=HUGE_STRING,blank=True)

    values = MetadataControlledVocabularyValueField(blank=True,null=True)

    def getName(self):
        return self._name

    def __unicode__(self):
        name = u'%s' % self.getName()
        if self.longName:
            name = u'%s' % self.longName
        else:
            name = u'%s' % self.shortName
        return name

    @classmethod
    def loadCV(cls,*args,**kwargs):
        cv_name = kwargs.pop("cv_name",cls._cv_name)
        parser = et.XMLParser(remove_blank_text=True)
        cv = et.fromstring(get_cv(cv_name),parser)
        xpath_item_expression = "//item"
        items = cv.xpath(xpath_item_expression)
        for item in items:
            shortName = item.xpath("shortName/text()") or None
            longName = item.xpath("longName/text()") or None
            if shortName: shortName = strip_completely(shortName[0])
            if longName: longName = strip_completely(longName[0])
            (model,created) = cls.objects.get_or_create(shortName=shortName,longName=longName)
            xpath_value_expression="//item[shortName/text()='%s']/values/value" % shortName
            values = cv.xpath(xpath_value_expression)
            value_choices = ""
            for value in values:
                valueShortName = value.xpath("shortName/text()")
                valueLongName = value.xpath("longName/text()")
                valueShortName = strip_completely(valueShortName[0])
                if not valueLongName:
                    value_choices += "%s|%s||" % (valueShortName,valueShortName)
                else:
                    valueLongName = strip_completely(valueLongName[0])
                    value_choices += "%s|%s||" % (valueShortName,valueLongName)
            model.values = value_choices
            if created:
                print "storing %s" % model
                model.save()
