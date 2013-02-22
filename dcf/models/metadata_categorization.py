
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
__date__ ="Jan 31, 2013 11:27:10 AM"

"""
.. module:: metadata_categorization

Summary of module goes here

"""
from django.db import models, DatabaseError
from django.db.models import get_app, get_models
from django.contrib.contenttypes.models import *
from django.contrib.contenttypes import generic
import json
import os

from dcf.utils import *

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
        app_label = APP_LABEL
        verbose_name        = 'Metadata Categorization'
        verbose_name_plural = 'Metadata Categorizations'
    
    file    = models.FileField(verbose_name="Categorization File",upload_to=_UPLOAD_PATH,validators=[validate_categorization_file_extension,validate_categorization_file_schema])

    # in theory, categories can be either instances of MetadataAttributeCategory or MetadataPropertyCategory so I have to use a generic relationship
    # however, Django only supports generic foreign keys, not m2m.
    # so I create a separate relationship table (MetadataCategoryRelation) which has a foreign key to categorization and a generic foreign key to content_types
    # there are some specific fns (getCategories, getAttributeCategories, getPropertyCategories, addCategory) to obfuscate that
    categories = models.ManyToManyField("MetadataCategoryRelation",blank=True,null=True)

    def __unicode__(self):
        if self.file:
            return u'%s' % os.path.basename(self.file.name)
        return u'%s' % self

    def save(self, *args, **kwargs):
        """
        before saving a categorization, check if a file of the same name already exists.
        if so, overwrite it.
        """
        categorization_file_path = os.path.join(settings.MEDIA_ROOT,APP_LABEL,_UPLOAD_DIR,self.file.name)

        if os.path.exists(categorization_file_path):
            print "WARNING: THE FILE '%s' ALREADY EXISTS; IT IS BEING OVERWRITTEN." % categorization_file_path
            os.remove(categorization_file_path)

        super(MetadataCategorization, self).save(*args, **kwargs)

    def loadCategorization(self):
        self.file.open()
        categorization_content = et.parse(self.file)
        self.file.close()
        
        newCategories = []
        for i, category in enumerate(categorization_content.xpath("//category")):

            categoryName        = category.xpath("name/text()")
            categoryDescription = category.xpath("description/text()") or None
            categoryKey         = category.xpath("key/text()") or None
            categoryOrder       = category.xpath("order/text()") or None

            filterParameters  = {}
            filterParameters["name"]            = categoryName[0]
            if categoryDescription:
                filterParameters["description"] = categoryDescription[0]
            if categoryKey:
                filterParameters["key"]         = categoryKey[0]
            else:
                filterParameters["key"]         = re.sub(r'\s','',categoryName[0]).lower()
            if categoryOrder:
                filterParameters["order"]       = categoryOrder[0]
            else:
                filterParameters["order"]       = (i+1)

            (newCategory, created) = MetadataAttributeCategory.objects.get_or_create(**filterParameters)

            newCategoryMapping = {}
            for i, field in enumerate(categorization_content.xpath("//field[category_key='%s']"%newCategory.key)):
                attributeName = field.xpath("name/text()")[0]
                modelName = field.xpath("./ancestor::model/name/text()")[0]
                # at this point I know that "attributeName" of "modelName" has "newCategory"
                # I am storing this as a dictionary and using JSON to encode/decode it
                try:
                    existing_attributes = newCategoryMapping[modelName]
                    newCategoryMapping[modelName].append(attributeName)
                except KeyError:
                    newCategoryMapping[modelName] = [attributeName]

            newCategory.setMapping(newCategoryMapping)
            newCategory.save()
            newCategories.append(newCategory)

        self.addCategories(newCategories)


    def getCategories(self):
        return [category.category for category in self.categories.all()]

    def getAttributeCategories(self):
        return [category.category for category in self.categories.all() if isinstance(category.category,MetadataAttributeCategory)]

    def getPropertyCategories(self):
        # can't return a list; have to return a QuerySet b/c of where this fn gets used
        # (initializing the queryset of m2m fields in forms)
        property_categories = [category.category for category in self.categories.all() if isinstance(category.category,MetadataPropertyCategory)]
        return MetadataPropertyCategory.objects.filter(id__in=property_categories)

    def addCategory(self,category):
        category_relation = MetadataCategoryRelation(categorization=self,category=category)
        category_relation.save()
        self.categories.add(category_relation)

    def addCategories(self,categories):
        category_relations = []
        for category in categories:
            category_relations.append(MetadataCategoryRelation(categorization=self,category=category))
        [category_relation.save() for category_relation in category_relations]
        self.categories.add(*category_relations) # the "*" expands the list into separate items


class MetadataCategory(models.Model):
    class Meta:
        app_label = APP_LABEL
        abstract = True

    _type = None

    name        = models.CharField(max_length=64,blank=True,editable=True)
    description = models.TextField(blank=True,editable=True)
    order       = models.PositiveIntegerField(blank=True,null=True,editable=True)
    key         = models.CharField(max_length=64,blank=True,editable=True,unique=True)

    def getType(self):
        return self._type

    def save(self,*args,**kwargs):
        if not self.order:
            # categories ought to have a default id
            self.order = self.id
        super(MetadataCategory,self).save(*args,**kwargs)


@guid()
class MetadataAttributeCategory(MetadataCategory):

    mapping = models.CharField(max_length=HUGE_STRING,blank=True)

    _type = CategoryTypes.ATTRIBUTE

    def getMapping(self):
        try:
            return json.loads(self.mapping)
        except ValueError:
            # mapping is empty
            return {}

    def setMapping(self,mapping):
        if isinstance(mapping,dict):
            self.mapping=json.dumps(mapping,separators=(',',':'))
        else:
            msg = "a category mapping must be a dictionary"
            raise MetadataError(msg)

    def __unicode__(self):
        return u'%s' % self.name

@guid()
class MetadataPropertyCategory(MetadataCategory):

    mapping = models.CharField(max_length=HUGE_STRING,blank=True)

    _type = CategoryTypes.PROPERTY

    def getMapping(self):
        try:
            return json.loads(self.mapping)
        except ValueError:
            # mapping is empty
            return {}

    def setMapping(self,mapping):
        if isinstance(mapping,dict):
            self.mapping=json.dumps(mapping,separators=(',',':'))
        else:
            msg = "a category mapping must be a dictionary"
            raise MetadataError(msg)

    def __unicode__(self):
        return u'%s' % self.name


_METADATA_CATEGORY_LIMITS = {'model_in':('metadataattributecategory','metadatapropertycategory')}

class MetadataCategoryRelation(models.Model):
    class Meta:
        app_label = APP_LABEL

    # this uses a generic foreign key to contenttypes
    # (but the limit_choices_to kwarg ensures it only applies to attribute & property categories)
    content_type    = models.ForeignKey(ContentType,limit_choices_to=_METADATA_CATEGORY_LIMITS)
    object_id       = models.PositiveIntegerField()
    category        = generic.GenericForeignKey("content_type","object_id")
    categorization  = models.ForeignKey(MetadataCategorization)

    def __unicode__(self):
        return u'%s' % self.category
