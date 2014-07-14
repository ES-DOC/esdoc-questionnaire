
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
__date__ ="Dec 28, 2013 9:17:37 PM"

"""
.. module:: questionnaire_vocabulary

Note my use of mptt for efficient handling of component hiearchies.

"""

from django.db import models

from django.template.defaultfilters import slugify
from lxml import etree as et
from django.conf import settings

import os
import re

from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataComponentProxy, MetadataScientificCategoryProxy, MetadataScientificPropertyProxy

from CIM_Questionnaire.questionnaire.utils import validate_file_extension, validate_file_schema, validate_no_spaces, xpath_fix
from CIM_Questionnaire.questionnaire.utils import HUGE_STRING, BIG_STRING, SMALL_STRING, LIL_STRING, CIM_DOCUMENT_TYPES
from CIM_Questionnaire.questionnaire.utils import QuestionnaireError, OverwriteStorage


from CIM_Questionnaire.questionnaire import APP_LABEL

UPLOAD_DIR  = "vocabularies"
UPLOAD_PATH = os.path.join(APP_LABEL,UPLOAD_DIR)    # this is a relative path (will be concatenated w/ MEDIA_ROOT by FileFIeld)

def validate_vocabulary_file_extension(value):
    valid_extensions = ["xml"]
    return validate_file_extension(value,valid_extensions)

def validate_vocabulary_file_schema(value):
    # TODO: REWRITE SCHEMA
    schema_path = os.path.join(settings.STATIC_ROOT,APP_LABEL,"xml/vocabulary.xsd")
    return validate_file_schema(value,schema_path)

class MetadataVocabulary(models.Model):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        # this is one of the few classes that I allow admin access to, so give it pretty names:
        verbose_name        = 'Metadata Vocabulary'
        verbose_name_plural = 'Metadata Vocabularies'

    name            = models.CharField(max_length=SMALL_STRING,blank=False,null=False,unique=True,validators=[validate_no_spaces,])
    registered      = models.BooleanField(default=False)
    file            = models.FileField(upload_to=UPLOAD_PATH,validators=[validate_vocabulary_file_extension,],storage=OverwriteStorage())
    file.help_text  = "Note that files with the same names will be overwritten"
    document_type   = models.CharField(max_length=64,blank=False,choices=[(document_type,document_type) for document_type in CIM_DOCUMENT_TYPES])

    component_order = 0

    def next_component_order(self):
        self.component_order = (self.component_order + 1)
        return self.component_order

    def __unicode__(self):
        return u'%s' % self.name

    def __init__(self,*args,**kwargs):
        super(MetadataVocabulary,self).__init__(*args,**kwargs)
        self.component_order = 0

    def clean(self):
        # force name to be lowercase
        # this avoids hacky methods of ensuring case-insensitive uniqueness
        self.name = self.name.lower()

    def register(self,**kwargs):

        if not self.document_type:
            msg = "unable to register a vocabulary without an associated document_type"
            print "error: %s" % msg
            raise QuestionnaireError(msg)

        request = kwargs.pop("request",None)

        self.file.open()
        vocabulary_content = et.parse(self.file)
        self.file.close()

        # note that this is done slightly differently than w/ 'pure' xpath
        # so that I can recursively keep track of the full component hierarchy
        for i, vocabulary_component_proxy in enumerate(xpath_fix(vocabulary_content,"./component")):
            self.create_component_proxy(vocabulary_component_proxy)

        self.registered = True

    def unregister(self,**kwargs):
        request = kwargs.pop("request",None)
        print "TODO!!!!"
        self.registered = False

    def create_component_proxy(self,component_proxy_node,parent_component_proxy=None):
        new_component_proxy_kwargs = {
            "vocabulary"        : self,
            "order"             : self.next_component_order()
        }
        component_proxy_name = xpath_fix(component_proxy_node,"@name")[0]
        component_proxy_documentation = xpath_fix(component_proxy_node,"definition/text()") or None

        new_component_proxy_kwargs["name"] = component_proxy_name.lower()
        if component_proxy_documentation:
            new_component_proxy_kwargs["documentation"] = component_proxy_documentation[0]
        new_component_proxy_kwargs["parent"] = parent_component_proxy
        
        (new_component_proxy,created_component_proxy) = MetadataComponentProxy.objects.get_or_create(**new_component_proxy_kwargs)

        new_category_proxy_kwargs = {
            "component"  : new_component_proxy,
        }
        for i, category_proxy_node in enumerate(xpath_fix(component_proxy_node,"./parametergroup")):
            category_proxy_name = xpath_fix(category_proxy_node,"@name")[0]
            category_proxy_documentation = xpath_fix(category_proxy_node,"definition/text()") or None
            new_category_proxy_kwargs["order"]  = i
            new_category_proxy_kwargs["name"]   = category_proxy_name
            new_category_proxy_kwargs["key"]    = slugify(category_proxy_name)

            if category_proxy_documentation:
                new_category_proxy_kwargs["documentation"] = category_proxy_documentation[0]

            (new_category_proxy,created_category_proxy) = MetadataScientificCategoryProxy.objects.get_or_create(**new_category_proxy_kwargs)

            if not created_category_proxy:
                # delete all old properties (going to replace them during this registration)...
                old_category_proxy_properties = new_category_proxy.scientific_properties.all()
                old_category_proxy_properties.delete()

            new_property_proxy_kwargs = {
                "component"  : new_component_proxy,
                "category"   : new_category_proxy,
            }
            for j, property_proxy_node in enumerate(xpath_fix(category_proxy_node,"./parameter")):
                property_proxy_name         = xpath_fix(property_proxy_node,"@name")[0]
                property_proxy_choice       = xpath_fix(property_proxy_node,"@choice")[0]
                property_proxy_description  = xpath_fix(property_proxy_node,"definition/text()") or None
                property_proxy_values       = xpath_fix(property_proxy_node,"value")

                property_proxy_values = []
                for property_proxy_value in xpath_fix(property_proxy_node,"value"):
                    property_value_name = xpath_fix(property_proxy_value,"@name")
                    if property_value_name:
                        property_proxy_values.append(property_value_name[0])

                new_property_proxy_kwargs["order"]  = j
                new_property_proxy_kwargs["name"]   = property_proxy_name
                new_property_proxy_kwargs["choice"] = property_proxy_choice
                new_property_proxy_kwargs["values"] = "|".join(property_proxy_values)

                if property_proxy_description:
                    new_property_proxy_kwargs["documentation"] = property_proxy_description[0]

                (new_property_proxy,created_property_proxy) = MetadataScientificPropertyProxy.objects.get_or_create(**new_property_proxy_kwargs)

        for vocabulary_component_proxy in xpath_fix(component_proxy_node,"./component"):
            self.create_component_proxy(vocabulary_component_proxy,new_component_proxy)

from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

@receiver(post_save, sender=MetadataVocabulary)
def vocabulary_post_save(sender, **kwargs):
    created = kwargs.pop("created",True)
    vocabulary = kwargs.pop("instance",None)
    # TODO:
    pass

@receiver(post_delete, sender=MetadataVocabulary)
def vocabulary_post_delete(sender, **kwargs):
    vocabulary = kwargs.pop("instance",None)
    if vocabulary:
        try:
            vocabulary.file.delete(save=False)    # save=False prevents model from re-saving itself
            print "deleted %s" % (vocabulary.file.url)
        except:
            pass
