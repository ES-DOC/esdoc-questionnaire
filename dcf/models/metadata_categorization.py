
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
__date__ ="Jun 10, 2013 4:11:32 PM"

"""
.. module:: metadata_categorization

Summary of module goes here

"""

from django.db import models
import os

from dcf.models import *
from dcf.utils  import *

_UPLOAD_DIR  = "categorizations"
_UPLOAD_PATH = os.path.join(APP_LABEL,_UPLOAD_DIR)    # this is a relative path (will be concatenated w/ MEDIA_ROOT by FileFIeld)
_SCHEMA_PATH = os.path.join(settings.STATIC_ROOT,APP_LABEL,"xml/categorization.xsd") # this is an absolute path

def validate_categorization_file_extension(value):
    valid_extensions = ["xml"]
    return validate_file_extension(value,valid_extensions)

def validate_categorization_file_schema(value):
    return validate_file_schema(value,_SCHEMA_PATH)

class MetadataCategorization(models.Model):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        # this is one of the few classes that I allow admin access to, so give it pretty names:
        verbose_name        = 'Metadata Categorization'
        verbose_name_plural = 'Metadata Categorizations'

    version = models.ForeignKey("MetadataVersion",blank=True,related_name="categorizations")
    file    = models.FileField(verbose_name="Categorization File",upload_to=_UPLOAD_PATH,validators=[validate_categorization_file_extension,validate_categorization_file_schema])
    name    = models.CharField(max_length=255,blank=True,null=True,unique=True)

    def __unicode__(self):
        if self.file:
            return u'%s' % os.path.basename(self.file.name)
        return u'%s' % self

    def save(self, *args, **kwargs):
        """
        before saving a categorization, check if a file of the same name already exists.
        if so, overwrite it.
        """
        categorization_file_name = os.path.basename(self.file.name)
        categorization_file_path = os.path.join(settings.MEDIA_ROOT,APP_LABEL,_UPLOAD_DIR,categorization_file_name)

        if not self.name:
            self.name = categorization_file_name

        if os.path.exists(categorization_file_path):
            print "warning: the file '%s' is being overwritten" % categorization_file_path
            os.remove(categorization_file_path)

        return super(MetadataCategorization, self).save(*args, **kwargs)


    def register(self):

        if not self.version:
            msg = "unable to register a categorization without an associated version"
            print "error: %s" % msg
            raise MetadataError(msg)

        self.file.open()
        categorization_content = et.parse(self.file)
        self.file.close()

        category_filter_parameters = { "categorization" : self }
        properties_to_save = []

        for i, category in enumerate(categorization_content.xpath("//category")):

            category_name        = category.xpath("name/text()")
            category_description = category.xpath("description/text()") or None
            category_key         = category.xpath("key/text()") or None
            category_order       = category.xpath("order/text()") or None
            category_filter_parameters["name"]          = category_name[0]
            category_filter_parameters["description"]   = category_description[0] if category_description else ""
            category_filter_parameters["key"]           = category_key[0] if category_key else re.sub(r'\s','',category_name[0]).lower()
            category_filter_parameters["order"]         = category_order[0] if category_order else (i+1)

            (new_category, created) = MetadataStandardCategory.objects.get_or_create(**category_filter_parameters)

            for i, field in enumerate(categorization_content.xpath("//field[category_key='%s']"%new_category.key)):

                model_name = field.xpath("./ancestor::model/name/text()")[0]
                field_name = field.xpath("name/text()")[0]

                try:
                    # (not using a filter here, b/c I want to do a case insensitive search...)
                    property = MetadataStandardPropertyProxy.objects.get(version=self.version,model_name__iexact=model_name,name__iexact=field_name)
                except MetadataStandardPropertyProxy.DoesNotExist:
                    msg = "could not find property '%s' for model '%s' in version '%s'; creating a proxy anyway, but a mismatch between the categorization and the version is a bad idea" % \
                        (field_name, model_name, self.version)
                    print "WARNING: %s" % msg
                    #raise MetadataError(msg)
                    property = MetadataStandardPropertyProxy(version=self.version,model_name=model_name.lower(),name=field_name.lower())

                if property.category != new_category:
                    property.category = new_category
                    properties_to_save.append(property)

        for property in set(properties_to_save):
            property.save()
            
class MetadataCategory(models.Model):
    class Meta:
        app_label   = APP_LABEL
        abstract    = True
        ordering    = [ "order" ]

    name        = models.CharField(max_length=64,blank=True,editable=True)
    description = models.TextField(blank=True,editable=True)
    order       = models.PositiveIntegerField(blank=True,null=True,editable=True)
    key         = models.CharField(max_length=64,blank=True,editable=True)
    remove      = models.BooleanField(blank=False,null=False,default=False)

    def __unicode__(self):
        return u'%s' % self.name


class MetadataStandardCategory(MetadataCategory):
    # comes from categorization; bound to schema properties
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        unique_together = ("categorization","name")

    categorization  = models.ForeignKey("MetadataCategorization",blank=False,null=False,editable=False,related_name="categories")

    def __init__(self,*args,**kwargs):
        super(MetadataStandardCategory,self).__init__(*args,**kwargs)

class MetadataScientificCategory(MetadataCategory):
    # comes from vocabulary/user; bound to CV properties
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        unique_together = ("vocabulary","component_name","name")

    vocabulary      = models.ForeignKey("MetadataVocabulary",blank=True,null=True,editable=False,related_name="categories")
    project         = models.ForeignKey("MetadataProject",blank=True,null=True,editable=False,related_name="categories")
    component_name  = models.CharField(max_length=64,blank=True,null=True)

    def __init__(self,*args,**kwargs):
        super(MetadataScientificCategory,self).__init__(*args,**kwargs)

    def isCustom(self):
        if self.vocabulary:
            return True
        else:
            return False
