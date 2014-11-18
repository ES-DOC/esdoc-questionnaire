
####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Jan 2, 2014 10:18:34 AM"

"""
.. module:: metadata_categorization

Summary of module goes here

"""

from django.db import models
from django.contrib import messages
from django.conf import settings
from lxml import etree as et

import os
import re

from CIM_Questionnaire.questionnaire import APP_LABEL
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy, MetadataStandardPropertyProxy, MetadataStandardCategoryProxy
from CIM_Questionnaire.questionnaire.utils import validate_file_extension, validate_file_schema, xpath_fix, OverwriteStorage
from CIM_Questionnaire.questionnaire.utils import LIL_STRING, SMALL_STRING, BIG_STRING, HUGE_STRING

UPLOAD_DIR  = "categorizations"
UPLOAD_PATH = os.path.join(APP_LABEL,UPLOAD_DIR)    # this is a relative path (will be concatenated w/ MEDIA_ROOT by FileFIeld)

def validate_categorization_file_extension(value):
    valid_extensions = ["xml"]
    return validate_file_extension(value,valid_extensions)

def validate_categorization_file_schema(value):
    schema_path = os.path.join(settings.STATIC_ROOT,APP_LABEL,"xml/categorization.xsd")
    return validate_file_schema(value,schema_path)

class MetadataCategorization(models.Model):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        # this is one of the few classes that I allow admin access to, so give it pretty names:
        verbose_name        = 'Metadata Categorization'
        verbose_name_plural = 'Metadata Categorizations'


    name            = models.CharField(max_length=SMALL_STRING,blank=False,null=False,unique=True)
    registered      = models.BooleanField(default=False)

    file            = models.FileField(upload_to=UPLOAD_PATH,validators=[validate_categorization_file_extension,validate_categorization_file_schema],storage=OverwriteStorage())
    file.help_text  = "Note that files with the same names will be overwritten"


    def __unicode__(self):

        if self.name:
            return u'%s' % (self.name)
        else:
            return u'%s' % (os.path.basename(self.file.name))

    def clean(self):
        # force name to be lowercase
        # this avoids hacky methods of ensuring case-insensitive uniqueness
        self.name = self.name.lower()

    def register(self,**kwargs):
        request = kwargs.pop("request",None)

        try:
            self.file.open()
            categorization_content = et.parse(self.file)
            self.file.close()
        except IOError:
            msg = "Error opening file: %s" % self.file
            if request:
                messages.add_message(request, messages.ERROR, msg)
                return


        versions = self.versions.all()
        if not versions:
            msg = "MetadataCategorization '%s' has not been associated with any versions.  It's kind of silly to register it now." % (self)
            if request:
                messages.add_message(request, messages.WARNING, msg)
            else:
                print msg

        new_category_proxy_kwargs = {
            "categorization" : self,
        }
        for i, category in enumerate(xpath_fix(categorization_content,"//category")):
            category_name           = xpath_fix(category,"name/text()")
            category_key            = xpath_fix(category,"key/text()") or None
            category_description    = xpath_fix(category,"description/text()") or None
            category_order          = xpath_fix(category,'order/text()') or None

            new_category_proxy_kwargs["name"]          = category_name[0]
            new_category_proxy_kwargs["key"]           = category_key[0] if category_key else re.sub(r'\s','',category_name[0]).lower()
            new_category_proxy_kwargs["description"]   = category_description[0] if category_description else ""
            new_category_proxy_kwargs["order"]         = category_order[0] if category_order else i

            (new_category_proxy,created_category) = MetadataStandardCategoryProxy.objects.get_or_create(**new_category_proxy_kwargs)

            if not created_category:
                # remove any existing relationships (going to replace them during this registration)...
                new_category_proxy.properties.clear()

            for i, field in enumerate(categorization_content.xpath("//field[category_key='%s']" % (new_category_proxy.key))):

                model_name = field.xpath("./ancestor::model/name/text()")[0]
                field_name = field.xpath("name/text()")[0]

                for version in versions:
                    try:
                        model_proxy    = version.model_proxies.get(name__iexact=model_name)
                        property_proxy = model_proxy.standard_properties.get(name__iexact=field_name)

                        new_category_proxy.properties.add(property_proxy)

                    except MetadataModelProxy.DoesNotExist:
                        msg = "Unable to find MetadataModel '%s' specified in MetadataCategorization '%s'" % (model_name,self)
                        if request:
                            messages.add_message(request, messages.WARNING, msg)
                        else:
                            pass#print msg
                    except MetadataStandardPropertyProxy.DoesNotExist:
                        msg = "Unable to find MetadataProperty '%s' specified in MetadataCategorization '%s'" % (field_name,self)
                        if request:
                            messages.add_message(request, messages.WARNING, msg)
                        else:
                            pass#print msg
                        

            new_category_proxy.save()

        self.registered = True

    def unregister(self,**kwargs):
        request = kwargs.pop("request",None)
        for category in self.categories.all():
            category.delete()
        self.registered = False

from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

@receiver(post_save, sender=MetadataCategorization)
def project_post_save(sender, **kwargs):
    created = kwargs.pop("created",True)
    categorization = kwargs.pop("instance",None)
    # TODO:
    pass

@receiver(post_delete, sender=MetadataCategorization)
def project_post_delete(sender, **kwargs):
    categorization = kwargs.pop("instance",None)
    if categorization:
        try:
            categorization.file.delete(save=False)    # save=False prevents model from re-saving itself
            # TODO: CHECK THAT FILE.URL IS THE RIGHT WAY TO PRINT THIS
            print "deleted %s" % (categorization.file.url)
        except:
            pass

