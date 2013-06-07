
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
from django.db import models
#from django.contrib.contenttypes.models import *
import os

from dcf.models import *
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
    name    = models.CharField(max_length=LIL_STRING,blank=True,null=True,unique=True)
### THIS IS NO LONGER TRUE;
### A CATEGORIZATION IS ONLY FOR ATTRIBUTES - AND USERS ARE PREVENTED FROM ADDING NEW ONES
### (A VOCABULARY IS FOR PROPERTIES)
###    # in theory, categories can be either instances of MetadataAttributeCategory or MetadataPropertyCategory so I have to use a generic relationship
###    # however, Django only supports generic foreign keys, not m2m.
###    # so I create a separate relationship table (MetadataCategoryRelation) which has a foreign key to categorization and a generic foreign key to content_types
###    # there are some specific fns (getCategories, getAttributeCategories, getPropertyCategories, addCategory) to obfuscate that
###    categories = models.ManyToManyField("MetadataCategoryRelation",blank=True,null=True)
### AND, ANYWAY, THE RELATIONSHIP TO CATEGORIES IS DEALT W/ AT THE CATEGORY LEVEL, W/ A RELATED_NAME "category"

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
            print "WARNING: THE FILE '%s' ALREADY EXISTS; IT IS BEING OVERWRITTEN." % categorization_file_path
            os.remove(categorization_file_path)

        super(MetadataCategorization, self).save(*args, **kwargs)

    def loadCategorization(self):

        print "I AM LOADING A THE CATEGORIZATION %s" % self.name
        self.file.open()
        categorization_content = et.parse(self.file)
        self.file.close()

        filterParameters = {
            "categorization"    : self
        }
        for i, category in enumerate(categorization_content.xpath("//category")):

            categoryName        = category.xpath("name/text()")
            categoryDescription = category.xpath("description/text()") or None
            categoryKey         = category.xpath("key/text()") or None
            categoryOrder       = category.xpath("order/text()") or None

            filterParameters["name"]  = categoryName[0]

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
                print "attribute %s of model %s has category %s" % (attributeName,modelName,newCategory)
                try:
                    existing_attributes = newCategoryMapping[modelName]
                    newCategoryMapping[modelName].append(attributeName)
                except KeyError:
                    newCategoryMapping[modelName] = [attributeName]

            newCategory.setMapping(newCategoryMapping)
            newCategory.save()


    def getCategories(self):
        return self.categories.all()

    
###    def getCategories(self):
###        return [category.category for category in self.categories.all()]
###
###    def getAttributeCategories(self):
###        return [category.category for category in self.categories.all() if isinstance(category.category,MetadataAttributeCategory)]
###
###    def getPropertyCategories(self):
###        # can't return a list; have to return a QuerySet b/c of where this fn gets used
###        # (initializing the queryset of m2m fields in forms)
###        property_categories = [category.category for category in self.categories.all() if isinstance(category.category,MetadataPropertyCategory)]
###        return MetadataPropertyCategory.objects.filter(id__in=property_categories)
###
###    def addCategory(self,category):
###        category_relation = MetadataCategoryRelation(categorization=self,category=category)
###        category_relation.save()
###        self.categories.add(category_relation)
###
###    def addCategories(self,categories):
###        category_relations = []
###        for category in categories:
###            category_relations.append(MetadataCategoryRelation(categorization=self,category=category))
###        [category_relation.save() for category_relation in category_relations]
###        self.categories.add(*category_relations) # the "*" expands the list into separate items


