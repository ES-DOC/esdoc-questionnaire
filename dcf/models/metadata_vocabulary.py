
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
__date__ ="Jan 31, 2013 11:26:58 AM"

"""
.. module:: metadata_vocabulary

Summary of module goes here

"""

from django.db import models, DatabaseError
from django.db.models import get_app, get_models
import os

from dcf.utils import *
from dcf.models import *

_UPLOAD_DIR  = "vocabularies"
_UPLOAD_PATH = os.path.join(APP_LABEL,_UPLOAD_DIR)    # this is a relative path (will be concatenated w/ MEDIA_ROOT by FileFIeld)
_SCHEMA_PATH = os.path.join(settings.MEDIA_ROOT,APP_LABEL,_UPLOAD_DIR,"vocabulary.xsd") # this is an absolute path

def validate_vocabulary_file_extension(value):
    valid_extensions = ["xml"]
    return validate_file_extension(value,valid_extensions)

def validate_vocabulary_file_schema(value):
    return validate_file_schema(value,_SCHEMA_PATH)

@guid()
class MetadataVocabulary(models.Model):
    class Meta:
        app_label = APP_LABEL
        verbose_name        = 'Metadata Vocabulary'
        verbose_name_plural = 'Metadata Vocabularies'

    file    = models.FileField(verbose_name="Vocabulary File",upload_to=_UPLOAD_PATH,validators=[validate_vocabulary_file_extension,validate_vocabulary_file_schema])

    # unlike w/ a categorization, this can only have propertycategories (not attributecategories)
    # so a relationship table for a generic m2m field is not required here
    # (the get/set category fns below are therefore much simpler)
    categories = models.ManyToManyField("MetadataPropertyCategory",blank=True,null=True)
    properties = models.ManyToManyField("MetadataProperty",blank=True,null=True)

    def __unicode__(self):
        if self.file:
            return u'%s' % os.path.basename(self.file.name)
        return u'%s' % self

    def save(self, *args, **kwargs):
        """
        before saving a vocabulary, check if a file of the same name already exists.
        if so, overwrite it.
        """
        vocabulary_file_path = os.path.join(settings.MEDIA_ROOT,APP_LABEL,_UPLOAD_DIR,self.file.name)
        if os.path.exists(vocabulary_file_path):
            print "WARNING: THE FILE '%s' ALREADY EXISTS; IT IS BEING OVERWRITTEN." % vocabulary_file_path
            os.remove(vocabulary_file_path)

        super(MetadataVocabulary, self).save(*args, **kwargs)

    def loadProperty(self,property_element,modelName):
        propertyShortName = property_element.xpath("shortName/text()")[0]
        propertyLongName = property_element.xpath("longName/text()") or None
        if propertyLongName:
            propertyLongName = propertyLongName[0]
        else:
            propertyLongName = propertyShortName

## whoops, categories are defined on customizers - I can use the mapping to work it out
##        parent = property_element.xpath("./ancestor::property")
##        if parent:
##            parent = parent[0]  # xpath returns a list
##            parentShortName = parent.xpath("shortName/text()")[0]
##            parentCategory = MetadataPropertyCategory.objects.get(name=parentShortName)
##
##            (newProperty, created) = MetadataProperty.objects.get_or_create(short_name=propertyShortName,long_name=propertyLongName,model_name=modelName,category=parentCategory)

        (newProperty, created) = MetadataProperty.objects.get_or_create(short_name=propertyShortName,long_name=propertyLongName,model_name=modelName)

        values = property_element.xpath("./values")
        if values:
            values = values[0]  # xpath returns a list

            valueOpen = values.xpath("@open")
            valueMulti = values.xpath("@multi")
            valueNullable = values.xpath("@nullable")
            newProperty.open = valueOpen and valueOpen[0].lower()=="true"
            newProperty.multi = valueMulti and valueMulti[0].lower()=="true"
            newProperty.nullable = valueNullable and valueNullable[0].lower()=="true"

            newValues = []
            for value in values.xpath(".//value"):
                valueShortName = value.xpath("shortName/text()")[0]
                valueLongName  = value.xpath("longName/text()") or None
                if valueLongName:
                    valueLongName = valueLongName[0]
                else:
                    valueLongName = valueShortName
                newValues.append((valueShortName,valueLongName))

            newProperty.setValues(newValues)
            newProperty.save()

        return newProperty

    def loadVocabulary(self):
        self.file.open()
        vocabulary_content = et.parse(self.file)
        self.file.close()


        newProperties = []
        for i, model in enumerate(vocabulary_content.xpath("//model")):
            modelName = model.xpath("name/text()")[0].lower()
            for i, property in enumerate(model.xpath(".//property")):
                propertyShortName = property.xpath("shortName/text()")[0]
                propertyLongName = property.xpath("longName/text()") or None
                if propertyLongName:
                    propertyLongName = propertyLongName[0]
                else:
                    propertyLongName = propertyShortName

                hasProperties = property.xpath("./properties")
                hasValues = property.xpath("./values")

                if hasProperties:
                    # if this bit of the vocab has sub-properties,
                    # then it is actually a category, not a property

                    (newCategory, created) = MetadataPropertyCategory.objects.get_or_create(name=propertyShortName,description=propertyLongName,key=re.sub(r'\s','',propertyShortName).lower())

                    newCategoryMapping = {}
                    for i, subProperty in enumerate(hasProperties[0].xpath(".//property")):
                        newSubProperty = self.loadProperty(subProperty,modelName)
                        newProperties.append(newSubProperty)
                        # TODO: SORT OUT MAPPING
                        try:
                            existing_properties = newCategoryMapping[propertyShortName]
                            newCategoryMapping[modelName].append(newSubProperty.short_name)
                        except KeyError:
                            newCategoryMapping[modelName] = [newSubProperty.short_name]
                    if newCategoryMapping:
                        newCategory.setMapping(newCategoryMapping)
                        newCategory.save()
                    
                elif hasValues:
                    # if this bit of the vocab has sub-values
                    # then it is actually a property, not a category

                    newProperty = self.loadProperty(property,modelName)
                    newProperties.append(newProperty)
                



            self.addProperties(newProperties)

    def getProperties(self):
        return self.properties.all()

    def addProperty(self,property):
        self.properties.add(property)

    def addProperties(self,properties):
        # TODO: ENSURE THAT PROPERTIES ARGUMENT IS OF TYPE LIST
        self.properties.add(*properties)

    def getCategories(self):
        return self.categories.all()

    def getAttributeCategories(self):
        return MetadataAttributeCategory.objects.none()

    def getPropertyCategories(self):
        return self.categories.all()

    def addCategory(self,category):
        self.categories.add(category)

    def addCategories(self,categories):
        self.categories.add(*categories) # the "*" expands the list into separate items

