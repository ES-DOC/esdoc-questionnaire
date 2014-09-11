
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

from uuid import uuid4

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

    guid = models.CharField(blank=True, null=True, max_length=LIL_STRING, unique=True, editable=False)

    component_order = 0

    def next_component_order(self):
        self.component_order = (self.component_order + 1)
        return self.component_order

    def __unicode__(self):
        return u'%s' % self.name

    def __init__(self,*args,**kwargs):
        super(MetadataVocabulary,self).__init__(*args,**kwargs)
        self.component_order = 0

    def get_key(self):
        return self.guid

    def clean(self):
        # force name to be lowercase
        # this avoids hacky methods of ensuring case-insensitive uniqueness
        self.name = self.name.lower()


    def save(self, *args, **kwargs):

        if not self.guid:
            self.guid = str(uuid4())

        super(MetadataVocabulary, self).save(*args, **kwargs)

    def register(self,**kwargs):

        if not self.document_type:
            msg = "unable to register a vocabulary without an associated document_type"
            print "error: %s" % msg
            raise QuestionnaireError(msg)

        request = kwargs.pop("request",None)

        self.file.open()
        vocabulary_content = et.parse(self.file)
        self.file.close()

        self.old_component_proxies = list(self.component_proxies.all())  # list forces qs evaluation immediately
        self.new_component_proxies = []
        for i, component_proxy_node in enumerate(xpath_fix(vocabulary_content,"./component")):
            # rather than loop over all components ("//component"),
            # I do this recursively in order to keep track of the full component hierarchy
            self.create_component_proxy(component_proxy_node)

        # if there's anything in old_component_proxies not in new_component_proxies, delete it
        for old_component_proxy in self.old_component_proxies:
            if old_component_proxy not in self.new_component_proxies:
                old_component_proxy.delete()

        self.registered = True

        # if I re-registered a vocabulary and there were existing customizations associated w/ it
        # then I better update those cusotmizations so that it has the right content
        from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer, MetadataModelCustomizer
        customizers_to_update = MetadataModelCustomizer.objects.filter(vocabularies__in=[self.pk])
        for customizer in customizers_to_update:
            MetadataCustomizer.update_existing_customizer_set(customizer,[self])


    def unregister(self,**kwargs):
        request = kwargs.pop("request",None)
        print "TODO!!!!"
        self.registered = False

    def create_component_proxy(self,component_proxy_node,parent_component_proxy=None):

        component_proxy_vocabulary = self
        component_proxy_name = xpath_fix(component_proxy_node,"@name")[0]
        component_proxy_order = self.next_component_order()
        component_proxy_documentation_node = xpath_fix(component_proxy_node,"definition/text()") or None
        if component_proxy_documentation_node:
            component_proxy_documentation = component_proxy_documentation_node[0]
        else:
            component_proxy_documentation = u''#None

        (new_component_proxy, created_component_proxy) = MetadataComponentProxy.objects.get_or_create(
            vocabulary = component_proxy_vocabulary,
            name = component_proxy_name,
            parent = parent_component_proxy
        )
        new_component_proxy.documentation = component_proxy_documentation
        new_component_proxy.order = component_proxy_order
        new_component_proxy.save()

        old_category_proxies = list(new_component_proxy.categories.all())  # list forces qs evaluation immediately
        new_category_proxies = []
        category_proxy_component = new_component_proxy
        for i, category_proxy_node in enumerate(xpath_fix(component_proxy_node,"./parametergroup")):

            category_proxy_name = xpath_fix(category_proxy_node,"@name")[0]
            category_proxy_key = slugify(category_proxy_name)
            category_proxy_documentation_node = xpath_fix(category_proxy_node,"definition/text()") or None
            category_proxy_order = i
            if category_proxy_documentation_node:
                category_proxy_documentation = category_proxy_documentation_node[0]
            else:
                category_proxy_documentation = u''#None

            (new_category_proxy, created_category_proxy) = MetadataScientificCategoryProxy.objects.get_or_create(
                component = category_proxy_component,
                name = category_proxy_name
            )
            new_category_proxy.documentation = category_proxy_documentation
            new_category_proxy.key = category_proxy_key
            new_category_proxy.order = category_proxy_order
            new_category_proxy.save()
            new_category_proxies.append(new_category_proxy)

            old_property_proxies = list(new_category_proxy.scientific_properties.all())  # list forces qs evaluation immediately
            new_property_proxies = []
            property_proxy_category = new_category_proxy
            property_proxy_component = new_component_proxy
            for j, property_proxy_node in enumerate(xpath_fix(category_proxy_node, "./parameter")):

                property_proxy_name = xpath_fix(property_proxy_node, "@name")[0]
                property_proxy_choice = xpath_fix(property_proxy_node,"@choice")[0]
                property_proxy_documentation_node = xpath_fix(property_proxy_node,"definition/text()") or None
                property_proxy_order = j
                if property_proxy_documentation_node:
                    property_proxy_documentation = property_proxy_documentation_node[0]
                else:
                    property_proxy_documentation = u''#None
                property_proxy_values = []
                for property_proxy_value in xpath_fix(property_proxy_node,"value"):
                    property_proxy_value_name = xpath_fix(property_proxy_value, "@name")
                    if property_proxy_value_name:
                        property_proxy_values.append(property_proxy_value_name[0])

                (new_property_proxy, created_property_proxy) = MetadataScientificPropertyProxy.objects.get_or_create(
                    category = property_proxy_category,
                    component = property_proxy_component,
                    name = property_proxy_name,
                    choice = property_proxy_choice,
                )
                new_property_proxy.documentation = property_proxy_documentation
                new_property_proxy.order = j
                new_property_proxy.save()
                # TODO: IF THE VALUES ARE CHANGED WILL THEY PROPAGAGE TO THE CUSTOMIZER (SINCE THE PROPERTY IS NOT NEW?)
                # TODO: (IF NOT, I WILL HAVE TO ADD VALUE TO THE CONSTRUCTOR KWARGS ABOVE)
                new_property_proxy.values = "|".join(property_proxy_values)

                new_property_proxies.append(new_property_proxy)

            # if there's anything in old_property_proxies not in new_property_proxies, delete it
            for old_property_proxy in old_property_proxies:
                if old_property_proxy not in new_property_proxies:
                    old_property_proxy.delete()

        # if there's anything in old_category_proxies not in new_category_proxies, delete it
        for old_category_proxy in old_category_proxies:
            if old_category_proxy not in new_category_proxies:
                old_category_proxy.delete()

        for child_component_proxy_node in xpath_fix(component_proxy_node,"./component"):
            self.create_component_proxy(child_component_proxy_node, new_component_proxy)

        self.new_component_proxies.append(new_component_proxy)


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
