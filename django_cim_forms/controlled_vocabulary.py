#    Django-CIM-Forms
#    Copyright (c) 2012 CoG. All rights reserved.
#
#    Developed by: Earth System CoG
#    University of Colorado, Boulder
#    http://cires.colorado.edu/
#
#    This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].

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
CV_PATH = "/medadata/cv"
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
    _enum = []

    class Meta:
        abstract = True

    def __unicode__(self):
        return u'%s' % self.name

#    @classmethod
#    def addEnum(self,*args,**kwargs):
#        enum = kwargs.pop("enum",[])
#        self._enum.append(enum)

    @classmethod
    def isLoaded(cls,*args,**kwargs):
        # an enumeration class is "loaded" if it doesn't have more items
        # than are already in the database
        enum = kwargs.pop("enum",cls._enum)
        return len(enum) <= len(cls.objects.all())

    @classmethod
    def loadEnumerations(cls,*args,**kwargs):
        enum = kwargs.pop("enum",cls._enum)
        enum.sort()
        for name in enum:
            cls.objects.get_or_create(name=name)



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

    VALUE_SEPARATOR_TOKEN = "||"
    VALUE_NAME_SEPARATOR_TOKEN = "|"

    def isRequired(self):
        return True

    def getVerboseName(self):
        return "Value"

    def to_python(self, values, *args, **kwargs):
        if not values:
            # return nothing if there is no value
            return
        elif isinstance(values,list):
            # return value if it's already a list
            return values
        else:
            # otherwise create a list (of lists)
            return [tuple(val.split(self.VALUE_NAME_SEPARATOR_TOKEN)) for val in values.split(self.VALUE_SEPARATOR_TOKEN) if val]

    def get_db_prep_value(self, values, *args, **kwargs):
        if not values:
            return
        assert(isinstance(values, list) or isinstance(values, tuple))
        return self.VALUE_SEPARATOR_TOKEN.join([self.VALUE_NAME_SEPARATOR_TOKEN.join(val) for val in values])

    def value_to_string(self, obj, *args, **kwargs):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

###    def south_field_triple(self):
###        # just a one-off custom field that needs migration in South
###        from south.modelsinspector import introspector
###        field_class = "django_cim_forms.controlled_vocabulary." + self.__class__.__name__
###        args, kwargs = introspector(self)
###        return (field_class, args, kwargs)

class MetadataControlledVocabulary(models.Model):
    class Meta:
        abstract = True

    _name = "MetadataControlledVocabulary"

    shortName = models.CharField(max_length=HUGE_STRING,blank=False)
    longName = models.CharField(max_length=HUGE_STRING,blank=True)
    values = MetadataControlledVocabularyValueField(blank=True,null=True)
    parent = models.ForeignKey("self",blank=True,null=True)

    open = models.NullBooleanField()        # can a user override the bound values?
    multi = models.NullBooleanField()       # can a user select more than one bound value?
    nullable = models.NullBooleanField()    # can a user select no bound values?
    custom = models.NullBooleanField()      # must a user provide a custom value?

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
            # create the property if it doesn't already exist...
            shortName = item.xpath("shortName/text()") or None
            longName = item.xpath("longName/text()") or None
            if shortName: shortName = strip_completely(shortName[0])
            if longName: longName = strip_completely(longName[0])
            (model,created) = cls.objects.get_or_create(shortName=shortName,longName=longName)
            # figure out if it has values
            # and, if so, work out if they are "open," "multi," or "nullable"...
            xpath_values_expression="//item[shortName/text()='%s']/values" % shortName
            values = cv.xpath(xpath_values_expression)
            if values:
                open = values[0].xpath("@open")
                model.open = open and open[0].lower()=="true"
                multi = values[0].xpath("@multi")
                model.multi = multi and multi[0].lower()=="true"
                nullable = values[0].xpath("@nullable")
                model.nullable = nullable and nullable[0].lower()=="true"
                custom = values[0].xpath("@custom")
                model.custom = custom and custom[0].lower()=="true"

            if model.custom:
                # all custom models must be open
                # this is to ensure that the "OTHER" option is used in the combobox field
                # this causes the textbox field to appear
                model.open = True

            # figure out its specific value choices...
            xpath_value_expression="//item[shortName/text()='%s']/values/value" % shortName
            values = cv.xpath(xpath_value_expression)
            valueChoices = ""
#            if model.custom:
#                print "%s IS CUSTOM AND VALUES=%s" % (model, values)
            for value in values:
                valueShortName = value.xpath("shortName/text()")
                valueShortName = strip_completely(valueShortName[0])                
                valueLongName = value.xpath("longName/text()")
                #longName can have embedded markup in it, so I'm doing things a bit differently...
                #valueLongName = v for v in value.xpath("longName/child::node()")
                #valueLongName = value.find("longName")

                #if not valueLongName:
                if valueLongName is None:
                    valueChoices += "%s|%s||" % (valueShortName,valueShortName)
                else:
                    #valueLongName = et.tostring(valueLongName)
                    #valueLongName.replace("&lt;","<")
                    #valueLongName.replace("&gt;",">")
                    #valueLongName = strip_completely(valueLongName)
                    valueLongName = strip_completely(valueLongName[0])
                    valueChoices += "%s|%s||" % (valueShortName,valueLongName)
            model.values = valueChoices

            # figure out if it has a parent...
            parent = None
            xpath_parent_expression = "//item[shortName/text()='%s']/parent::items/parent::item" % shortName
            parents = cv.xpath(xpath_parent_expression)
            if parents:
                parentShortName = parents[0].xpath("shortName/text()") or None
                parentLongName = parents[0].xpath("longName/text()") or None
                if parentShortName: parentShortName = strip_completely(parentShortName[0])
                if parentLongName: parentLongName = strip_completely(parentLongName[0])
                try:
                    parent = cls.objects.get(shortName=parentShortName,longName=parentLongName)
                except:
                    pass
            model.parent = parent

            if created:
                print "storing %s" % model
                model.save()

