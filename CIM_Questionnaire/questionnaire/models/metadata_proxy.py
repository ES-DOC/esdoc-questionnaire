
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
__date__ ="Dec 18, 2013 3:49:13 PM"

"""
.. module:: questionnaire_proxy

Summary of module goes here

"""

from django.db import models

from django.template.defaultfilters import slugify

from mptt.models import MPTTModel, TreeForeignKey

from uuid import uuid4

from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes, MetadataAtomicFieldTypes
from CIM_Questionnaire.questionnaire.utils import QuestionnaireError, pretty_string
from CIM_Questionnaire.questionnaire.utils import APP_LABEL, LIL_STRING, SMALL_STRING, BIG_STRING, HUGE_STRING, CIM_DOCUMENT_TYPES, CIM_MODEL_STEREOTYPES, CIM_PROPERTY_STEREOTYPES, CIM_NAMESPACES

STANDARD_PROPERTY_STEREOTYPES = ( ("attribute", "attribute"))

DEFAULT_SCIENTIFIC_CATEGORY_KEY = "general-attributes"

class MetadataModelProxy(models.Model):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        unique_together = ("version","name")
        ordering = ['order']

        # TODO: DELETE THESE NEXT TWO LINES
        verbose_name        = '(DISABLE ADMIN ACCESS SOON) Metadata Model Proxy'
        verbose_name_plural = '(DISABLE ADMIN ACCESS SOON) Metadata Model Proxies'

    name                    = models.CharField(max_length=SMALL_STRING,blank=False,null=False)
    stereotype              = models.CharField(max_length=BIG_STRING,blank=True,null=True,choices=[(slugify(stereotype),stereotype) for stereotype in CIM_MODEL_STEREOTYPES])
    namespace               = models.CharField(max_length=LIL_STRING, blank=True, null=True)
    documentation           = models.TextField(blank=True,null=True)
    package                 = models.CharField(max_length=SMALL_STRING,blank=True,null=True)
    order                   = models.PositiveIntegerField(blank=True,null=True)
    version                 = models.ForeignKey("MetadataVersion",blank=False,null=True,related_name="model_proxies")


    def is_document(self):
        is_document = False

        if self.stereotype and self.stereotype.lower() == "document":
            is_document = True

        return is_document
    
    def __unicode__(self):
        return pretty_string(self.name)

    def get_standard_category_proxies(self):
        if self.version.categorization:
            return self.version.categorization.categories.all().order_by("order")
        else:
            return MetadataStandardCategoryProxy.objects.none()

    @classmethod
    def get_proxy_set(cls,model_proxy,vocabularies=None):#MetadataVocabulary.objects.none()): # (commented out to avoid circular imports)

        standard_property_proxies = model_proxy.standard_properties.all().order_by("category__order", "order")

        scientific_property_proxies = {}
        for vocabulary in vocabularies:
            vocabulary_key = vocabulary.get_key()
            for component_proxy in vocabulary.component_proxies.all():
                component_key = component_proxy.get_key()
                model_key = u"%s_%s" % (vocabulary_key, component_key)
                scientific_property_proxies[model_key] = component_proxy.scientific_properties.all().order_by("category__order", "order")

        return (model_proxy, standard_property_proxies, scientific_property_proxies)

class MetadataPropertyProxy(models.Model):
    class Meta:
        app_label   = APP_LABEL
        abstract    = True

    name                = models.CharField(max_length=HUGE_STRING,blank=False,null=False)
    documentation       = models.TextField(blank=True,null=True)
    field_type          = models.CharField(max_length=SMALL_STRING,blank=False,null=True,choices=[(ft.getType(),ft.getName()) for ft in MetadataFieldTypes])
    order               = models.PositiveIntegerField(blank=True,null=True)

    is_label            = models.BooleanField(blank=False,default=False)

class MetadataStandardPropertyProxy(MetadataPropertyProxy):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        unique_together = ("model_proxy","name")
        ordering = ['order']

        # TODO: DELETE THESE NEXT TWO LINES
        verbose_name        = '(DISABLE ADMIN ACCESS SOON) Metadata Standard Property Proxy'
        verbose_name_plural = '(DISABLE ADMIN ACCESS SOON) Metadata Standard Property Proxies'

    model_proxy = models.ForeignKey("MetadataModelProxy", blank=True, null=True, related_name="standard_properties")
    stereotype = models.CharField(max_length=BIG_STRING, blank=True, null=True, choices=[(slugify(stereotype),stereotype) for stereotype in CIM_PROPERTY_STEREOTYPES])
    namespace = models.CharField(max_length=BIG_STRING, blank=True, null=True, choices=[(slugify(namespace),namespace) for namespace in CIM_NAMESPACES])

    # attributes for ATOMIC fields
    atomic_default  = models.CharField(max_length=BIG_STRING,blank=True)
    atomic_type     = models.CharField(max_length=64,blank=False,null=True,choices=[(ft.getType(),ft.getName()) for ft in MetadataAtomicFieldTypes],default=MetadataAtomicFieldTypes.DEFAULT.getType())

    # attributes for ENUMERATION fields
    enumeration_choices  = models.TextField(blank=True)
    enumeration_open     = models.BooleanField(default=False,blank=True)
    enumeration_multi    = models.BooleanField(default=False,blank=True)
    enumeration_nullable = models.BooleanField(default=False,blank=True)

    # attributes for RELATIONSHIP fields
    relationship_cardinality  = models.CharField(max_length=LIL_STRING,blank=True)
    relationship_target_name  = models.CharField(max_length=BIG_STRING,blank=True,null=True)
    relationship_target_model = models.ForeignKey("MetadataModelProxy",blank=True,null=True)
    
    def __unicode__(self):
        return u'%s' % (self.name)
        #return u'%s::%s' % (self.model_proxy,self.name)

    def get_relationship_cardinality_min(self):
        min, max = self.relationship_cardinality.split("|")
        return min

    def get_relationship_cardinality_max(self):
        min, max = self.relationship_cardinality.split("|")
        return max

    def is_multiple(self):
        _max = self.get_relationship_cardinality_max()
        return _max == u'*' or int(_max) != 1

    def reset(self):

        if self.field_type == MetadataFieldTypes.ATOMIC:
            pass

        elif self.field_type == MetadataFieldTypes.ENUMERATION:
            pass

        elif self.field_type == MetadataFieldTypes.RELATIONSHIP:
            version     = self.model_proxy.version
            target_name = self.relationship_target_name
            try:
                target_proxy = MetadataModelProxy.objects.get(version=version,name__iexact=target_name)
            except MetadataModelProxy.DoesNotExist:
                msg = "unable to locate model '%s' in version '%s'" % (target_name,version)
                raise QuestionnaireError(msg)

            self.relationship_target_model = target_proxy

    def enumerate_choices(self):
        return [(choice, choice) for choice in self.enumeration_choices.split("|")]

SCIENTIFIC_PROPERTY_CHOICES = [
    ("XOR","XOR"),
    ("OR","OR"),
    ("keyboard","keyboard"),
]

class MetadataScientificPropertyProxy(MetadataPropertyProxy):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        unique_together = ("component","category","name")
        ordering = ['order']

        # TODO: DELETE THESE NEXT TWO LINES
        verbose_name        = '(DISABLE ADMIN ACCESS SOON) Metadata Scientific Property Proxy'
        verbose_name_plural = '(DISABLE ADMIN ACCESS SOON) Metadata Scientific Property Proxies'

    component     = models.ForeignKey("MetadataComponentProxy",blank=True,null=True,related_name="scientific_properties")
    category      = models.ForeignKey("MetadataScientificCategoryProxy",blank=True,null=True,related_name="scientific_properties")

    choice        = models.CharField(max_length=LIL_STRING,blank=True,null=True,choices=SCIENTIFIC_PROPERTY_CHOICES)
    # need a text field b/c the set of values can be really really big
    #values        = models.CharField(max_length=HUGE_STRING,blank=True)
    values        = models.TextField(blank=True)

    def enumerate_choices(self):
        return [(choice,choice) for choice in self.values.split("|")]

    def __unicode__(self):
        #return u'%s::%s::%s' % (self.component,self.category,self.name)
        return u'%s'%(self.name)

class MetadataCategoryProxy(models.Model):
    class Meta:
        app_label   = APP_LABEL
        abstract    = True

    description             = models.TextField(blank=True,null=True)
    order                   = models.PositiveIntegerField(blank=True,null=True)

class MetadataStandardCategoryProxy(MetadataCategoryProxy):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        unique_together = ("categorization","name")
        ordering = ['order']

        # TODO: DELETE THESE NEXT TWO LINES
        verbose_name        = '(DISABLE ADMIN ACCESS SOON) Metadata Standard Category Proxy'
        verbose_name_plural = '(DISABLE ADMIN ACCESS SOON) Metadata Standard Category Proxies'

    categorization  = models.ForeignKey("MetadataCategorization",blank=False,null=False,related_name="categories")
    properties      = models.ManyToManyField("MetadataStandardPropertyProxy",blank=True,null=True,related_name="category")

    name                    = models.CharField(max_length=BIG_STRING,blank=False,null=False)
    key                     = models.CharField(max_length=BIG_STRING,blank=False,null=False)

    def __unicode__(self):
        return u'%s' % (self.name)

    def has_property(self,standard_property_proxy):
        return standard_property_proxy in self.properties.all()

class MetadataScientificCategoryProxy(MetadataCategoryProxy):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        unique_together = ("component","name")
        ordering = ['order']

        # TODO: DELETE THESE NEXT TWO LINES
        verbose_name        = '(DISABLE ADMIN ACCESS SOON) Metadata Scientific Category Proxy'
        verbose_name_plural = '(DISABLE ADMIN ACCESS SOON) Metadata Scientific Category Proxies'

    component  = models.ForeignKey("MetadataComponentProxy",blank=True,null=True,related_name="categories")

    name                    = models.CharField(max_length=BIG_STRING,blank=False,null=False)
    key                     = models.CharField(max_length=BIG_STRING,blank=False,null=False)

    def __unicode__(self):
        return u'%s' % (self.name)

    def has_property(self,scientific_property_proxy):
        return scientific_property_proxy in self.properties.all()

    def is_default_category(self):
        return self.key == DEFAULT_SCIENTIFIC_CATEGORY_KEY

class MetadataComponentProxy(MPTTModel):
    name          = models.CharField(max_length=SMALL_STRING, blank=False, null=False)
    documentation = models.TextField(blank=True, null=True)
    order         = models.PositiveIntegerField(blank=True, null=True)
    vocabulary    = models.ForeignKey("MetadataVocabulary", blank=False, null=True, related_name="component_proxies")

    guid = models.CharField(blank=True, null=True, max_length=LIL_STRING, unique=True, editable=False)

    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')

    class Meta:
        app_label = APP_LABEL
        abstract = False
        unique_together = ("vocabulary", "name", "parent", )
        ordering = ['order']

        # TODO: DELETE THESE NEXT TWO LINES
        verbose_name = '(DISABLE ADMIN ACCESS SOON) Metadata Component Proxy'
        verbose_name_plural = '(DISABLE ADMIN ACCESS SOON) Metadata Component Proxies'

    def __unicode__(self):
        return u'%s' % (self.name)
        #return u'%s::%s' % (self.vocabulary,self.name)

    def get_key(self):
        return self.guid

    def save(self, *args, **kwargs):

        if not self.guid:
            self.guid = str(uuid4())

        super(MetadataComponentProxy, self).save(*args, **kwargs)
