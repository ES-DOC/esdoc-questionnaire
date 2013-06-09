
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

from django.db import models
import json
import os

from dcf.utils import *
from dcf.models import *

_UPLOAD_DIR  = "vocabularies"
_UPLOAD_PATH = os.path.join(APP_LABEL,_UPLOAD_DIR)    # this is a relative path (will be concatenated w/ MEDIA_ROOT by FileFIeld)
_SCHEMA_PATH = os.path.join(settings.STATIC_ROOT,APP_LABEL,"xml/mmxml.xsd") # this is an absolute path

def validate_vocabulary_file_extension(value):
    valid_extensions = ["xml"]
    return validate_file_extension(value,valid_extensions)

def validate_vocabulary_file_schema(value):
    return validate_file_schema(value,_SCHEMA_PATH)

#@guid()
class MetadataVocabulary(models.Model):
    class Meta:
        app_label = APP_LABEL
        verbose_name        = 'Metadata Vocabulary'
        verbose_name_plural = 'Metadata Vocabularies'

    file    = models.FileField(verbose_name="Vocabulary File",upload_to=_UPLOAD_PATH,validators=[validate_vocabulary_file_extension,validate_vocabulary_file_schema])
    name    = models.CharField(max_length=LIL_STRING,blank=True,null=True,unique=True)

    component_hierarchy = models.TextField(blank=True,null=True) # using TextField b/c the hierarchy could be arbitrariliy big
   
    def __unicode__(self):
        if self.file:
            return u'%s' % os.path.basename(self.file.name)
        return u'%s' % self

    def save(self, *args, **kwargs):
        """
        before saving a vocabulary, check if a file of the same name already exists.
        if so, overwrite it.
        """
        vocabulary_file_name = os.path.basename(self.file.name)
        vocabulary_file_path = os.path.join(settings.MEDIA_ROOT,APP_LABEL,_UPLOAD_DIR,vocabulary_file_name)

        if not self.name:
            self.name = vocabulary_file_name

        if os.path.exists(vocabulary_file_path):
            print "WARNING: THE FILE '%s' ALREADY EXISTS; IT IS BEING OVERWRITTEN." % vocabulary_file_path
            os.remove(vocabulary_file_path)

        super(MetadataVocabulary, self).save(*args, **kwargs)

    def loadVocabulary(self):
        self.file.open()
        vocabulary_content = et.parse(self.file)
        self.file.close()

        _component_hierarchy = {}

        category_filter_parameters = {
            "vocabulary"    : self
        }
        property_filter_parameters = {
            "vocabulary"    : self
        }
        value_filter_parameters = {

        }

        for i, component in enumerate(vocabulary_content.xpath("//component")):
            component_name = component.xpath("@name")[0]
            component_ancestors = component.xpath("./ancestor-or-self::component/@name")
            current_component_hierarchy = _component_hierarchy
            for ancestor in component_ancestors:
                if type(current_component_hierarchy) is dict:
                    current_component_hierarchy = current_component_hierarchy.setdefault(ancestor,[])
                elif type(current_component_hierarchy) is list:
                    found = False
                    for _dict in current_component_hierarchy:
                        if ancestor in _dict:
                            current_component_hierarchy = _dict.setdefault(ancestor,[])
                    # these weird next 4 lines break out of the for loop enclosing the if statement
                            found = True
                            break
                    if found:
                        continue
                    current_component_hierarchy.append({ancestor : []})
                    current_component_hierarchy = current_component_hierarchy[-1][ancestor]


            category_filter_parameters["component_name"] = component_name.lower()
            property_filter_parameters["component_name"] = component_name.lower()
            
            for i, parameter_group in enumerate(component.xpath("./parametergroup")):

                parameter_group_name = parameter_group.xpath("@name")[0]

                category_filter_parameters["name"]  = parameter_group_name
                category_filter_parameters["key"]   = re.sub(r'\s','',parameter_group_name).lower()

                (new_category, created) = MetadataPropertyCategory.objects.get_or_create(**category_filter_parameters)

                new_category_mapping = {}
                for i, property in enumerate(parameter_group.xpath("./parameter")):

                    property_name = property.xpath("@name")[0]
                    property_choice = property.xpath("@choice")[0]
                    property_definition = property.xpath("./definition/text()")

                    property_filter_parameters["name"] = property_name
                    property_filter_parameters["choice"] = property_choice
                    property_filter_parameters["default_category"] = new_category
                    property_filter_parameters["description"] = property_definition[0] if property_definition else ""

                    (new_property, created) = MetadataProperty.objects.get_or_create(**property_filter_parameters)

                    value_filter_parameters["property"] = new_property
                    for i, value in enumerate(property.xpath("./value")):
                        value_name   = value.xpath("@name")
                        value_units  = value.xpath("@units")
                        value_format = value.xpath("@format")

                        if value_name:
                            value_filter_parameters["name"] = value_name[0]
                        if value_units:
                            value_filter_parameters["units"] = value_units[0]
                        if value_format:
                            value_filter_parameters["format"] = value_format[0]

                        (new_value, created) = MetadataPropertyValue.objects.get_or_create(**value_filter_parameters)

        # using json dumps/loads because I save the heierarchy as a string but serialize it as JSON (to pass to JQuery/HTML)
        self.component_hierarchy = json.dumps(_component_hierarchy,separators=(',',':'))
        self.save() # have to ensure component_hierarchy gets saved in the db-

        
###
###        newProperties = []
###        for i, model in enumerate(vocabulary_content.xpath("//model")):
###            modelName = model.xpath("name/text()")[0].lower()
###            for i, property in enumerate(model.xpath(".//property")):
###                propertyShortName = property.xpath("shortName/text()")[0]
###                propertyLongName = property.xpath("longName/text()") or None
###                if propertyLongName:
###                    propertyLongName = propertyLongName[0]
###                else:
###                    propertyLongName = propertyShortName
###
###                hasProperties = property.xpath("./properties")
###                hasValues = property.xpath("./values")
###
###                if hasProperties:
###                    # if this bit of the vocab has sub-properties,
###                    # then it is actually a category, not a property
###
###                    filter_parameters = {
###                        "vocabulary"    : self,
###                        "name"          : propertyShortName,
###                        "description"   : propertyLongName,
###                        "key"           : re.sub(r'\s','',propertyShortName).lower()
###                    }
###
###                    (newCategory, created) = MetadataPropertyCategory.objects.get_or_create(**filter_parameters)
###
###                    newCategoryMapping = {}
###                    for i, subProperty in enumerate(hasProperties[0].xpath(".//property")):
###                        newSubProperty = self.loadProperty(subProperty,modelName)
###                        newProperties.append(newSubProperty)
###                        # TODO: SORT OUT MAPPING
###                        try:
###                            existing_properties = newCategoryMapping[propertyShortName]
###                            newCategoryMapping[modelName].append(newSubProperty.short_name)
###                        except KeyError:
###                            newCategoryMapping[modelName] = [newSubProperty.short_name]
###                    if newCategoryMapping:
###                        newCategory.setMapping(newCategoryMapping)
###                        newCategory.save()
###
###                elif hasValues:
###                    # if this bit of the vocab has sub-values
###                    # then it is actually a property, not a category
###
###                    newProperty = self.loadProperty(property,modelName)
###                    newProperties.append(newProperty)
###
###            self.addProperties(newProperties)

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

    def getCategories(self):
        return self.categories.all()

    def getProperties(self):
        return self.default_properties.all()

    def addProperty(self,property):
        self.default_properties.add(property)

    def addProperties(self,properties):
        # TODO: ENSURE THAT PROPERTIES ARGUMENT IS OF TYPE LIST
        self.default_properties.add(*properties)

    def getComponents(self):
        return json.loads(self.component_hierarchy)

