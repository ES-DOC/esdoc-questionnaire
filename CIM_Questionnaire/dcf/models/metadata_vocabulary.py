
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
__date__ ="Jun 10, 2013 4:11:41 PM"

"""
.. module:: metadata_vocabulary

Summary of module goes here

"""
from django.db import models
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


class MetadataVocabulary(models.Model):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        # this is one of the few classes that I allow admin access to, so give it pretty names:
        verbose_name        = 'Metadata Vocabulary'
        verbose_name_plural = 'Metadata Vocabularies'

#    project = models.ForeignKey("MetadataProject",blank=True,null=True,related_name="vocabularies")
    projects = models.ManyToManyField("MetadataProject",blank=True,null=True,related_name="vocabularies")
#    file    = models.FileField(verbose_name="Vocabulary File",upload_to=_UPLOAD_PATH,validators=[validate_vocabulary_file_extension,validate_vocabulary_file_schema])
    file    = models.FileField(verbose_name="Vocabulary File",upload_to=_UPLOAD_PATH,validators=[validate_vocabulary_file_extension])
    name    = models.CharField(max_length=255,blank=True,null=True,unique=True)
    document_type = models.CharField(max_length=64,blank=False,choices=CIM_DOCUMENT_TYPES)

    component_tree = models.TextField(blank=True)
    component_list = models.TextField(blank=True)
    
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

        force_overwrite = kwargs.pop("force_overwrite",True)
        if force_overwrite:
            if os.path.exists(vocabulary_file_path):
                print "warning: the file '%s' is being overwritten" % vocabulary_file_path
                os.remove(vocabulary_file_path)

        print "ABOUT TO SAVE"
        super(MetadataVocabulary, self).save(*args, **kwargs)

    def register(self):

        # this is a pretty intensive fn.
        # thankfully, it only gets run when setting up the db,
        # and not while using the forms.

        if not self.document_type:
            msg = "unable to register a vocabulary without an associated document_type"
            print "error: %s" % msg
            raise MetadataError(msg)

        self.file.open()
        vocabulary_content = et.parse(self.file)
        self.file.close()

        component_hierarchy = {}

        category_filter_parameters  = { "vocabulary" : self }
        property_filter_parameters  = { "vocabulary" : self, "model_name" : self.document_type, "type" : MetadataFieldTypes.PROPERTY }
        value_filter_parameters     = { }

        for i, component in enumerate(vocabulary_content.xpath("//component")):
            component_name = component.xpath("@name")[0]

            # parse the component hierarchy buried w/in the CV into a dictionary-of-lists-of-dictionaries
            component_ancestors = component.xpath("./ancestor-or-self::component/@name")
            current_component_hierarchy = component_hierarchy
            for ancestor in component_ancestors:
                if type(current_component_hierarchy) is dict:
                    current_component_hierarchy = current_component_hierarchy.setdefault(ancestor,[])
                elif type(current_component_hierarchy) is list:
                    found = False
                    for _dict in current_component_hierarchy:
                        if ancestor in _dict:
                            current_component_hierarchy = _dict.setdefault(ancestor,[])
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
                category_filter_parameters["defaults"] = {"order" : (i+1), "description" : ""}

                (new_category, created) = MetadataScientificCategory.objects.get_or_create(**category_filter_parameters)
                if created:
                    print "created category %s" % new_category

                for i, property in enumerate(parameter_group.xpath("./parameter")):

                    property_name = property.xpath("@name")[0]
                    property_choice = property.xpath("@choice")[0]
                    property_definition = property.xpath("./definition/text()")

                    property_filter_parameters["name"] = property_name
                    property_filter_parameters["choice"] = property_choice
                    property_filter_parameters["category"] = new_category
                    property_filter_parameters["documentation"] = property_definition[0] if property_definition else ""
            
                    (new_property, created) = MetadataScientificPropertyProxy.objects.get_or_create(**property_filter_parameters)
                    if created:
                        print "created property %s" % new_property

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

                        (new_value, created) = MetadataScientificPropertyProxyValue.objects.get_or_create(**value_filter_parameters)

                        if created:
                            print "created property value %s" % new_value

        print "converting component hierarchy to dictionary & list..."
        self.setComponents(component_hierarchy)
        self.save(force_overwrite=False) # have to ensure component_hierarchy gets saved in the db

    def setComponents(self,components_hierarchy):
        component_list = []
        component_list_generator = list_from_tree(components_hierarchy)
        for component in component_list_generator:
            component_list += component

        component_list_string = "|".join(component_list)
        component_tree_string = json.dumps(components_hierarchy)
        self.component_tree = component_tree_string
        self.component_list = component_list_string

    def getComponentTree(self):
        return json.loads(self.component_tree)

    def getComponentList(self):
        return self.component_list.split("|")

def list_from_tree(tree):
    yield tree.keys()
    for (key,value) in tree.iteritems():
        if isinstance(value,list):
            for list_item in value:
                for key in list_from_tree(list_item):
                    yield key