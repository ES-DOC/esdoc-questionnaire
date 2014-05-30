
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
__date__ ="Dec 18, 2013 1:19:49 PM"

"""
.. module:: questionnaire_model

Summary of module goes here

"""

from django.db                  import models
from django.contrib             import admin
from django.db.models.loading   import cache

from south.db                   import db

from django.utils import timezone

from questionnaire.utils        import *
from questionnaire.fields       import *
from questionnaire.models       import *

from django.db import models

from mptt.models import MPTTModel, TreeForeignKey

############################################
# create a hiearchy of models based on the #
# built-in hiearchical relationships that  #
# mppt adds to components                  #
############################################


def create_models_from_components(component_node,model_parameters,models=[]):
        title = model_parameters["title"]
        model_parameters["title"] = title[:title.index(" : ")] + " : " + component_node.name
        model_parameters["component_key"] = slugify(component_node.name)

        model = MetadataModel(**model_parameters)
        models.append(model)
        for child_component in component_node.get_children():
            model_parameters["parent"] = model
            create_models_from_components(child_component,model_parameters,models)


#################
# MetadataModel #
#################


class MetadataModel(MPTTModel):
    # ideally, MetadataModel should be an ABC
    # but Django Models already have a metaclass: django.db.models.base.ModelBase
    # see http://stackoverflow.com/questions/8723639/a-django-model-that-subclasses-an-abc-gives-a-metaclass-conflict for a description of the problem
    # and http://code.activestate.com/recipes/204197-solving-the-metaclass-conflict/ for a solution that just isn't worth the hassle
    #from abc import *
    #__metaclass__ = ABCMeta
    # ACTUALLY, I HAVE CHANGED HOW MODELS WORK;
    # THEY ARE NO LONGER ABSTRACT AND ARE GENERATED VIA PROXIES RATHER THAN DIRECTLY IN CODE
    class Meta:
        app_label   = APP_LABEL
        abstract    = False

#        unique_together = ("proxy","project","version","vocabulary_key","component_key")

    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')

    created                 = models.DateTimeField(blank=True,null=True,editable=False)
    last_modified           = models.DateTimeField(blank=True,null=True,editable=False)

    proxy           = models.ForeignKey("MetadataModelProxy",blank=False,null=True,related_name="models")
    project         = models.ForeignKey("MetadataProject",blank=True,null=True,related_name="models")
    version         = models.ForeignKey("MetadataVersion",blank=False,null=True,related_name="models")

    is_document     = models.BooleanField(blank=False,null=False,default=False)
    is_root         = models.BooleanField(blank=False,null=False,default=False)

    vocabulary_key  = models.CharField(max_length=BIG_STRING,blank=True,null=True)
    component_key   = models.CharField(max_length=BIG_STRING,blank=True,null=True)
    title           = models.CharField(max_length=BIG_STRING,blank=True,null=True)

    active          = models.BooleanField(blank=False,null=False,default=True)
    name            = models.CharField(max_length=SMALL_STRING,blank=False,null=False)
    description     = models.CharField(max_length=HUGE_STRING,blank=True,null=True)
    order           = models.PositiveIntegerField(blank=True,null=True)

# NONE OF THIS STUFF IS EXPLICITLY NEEDED B/C OF THE TreeForeignKey FIELD ABOVE
#    #parent_model = models.ForeignKey('self',null=True,blank=True,related_name="child_models")
#    #child_models = models.ManyToManyField('self',related_name='parent_model')
#
#    def add_child(self,child):
#        # TODO: CHECK IT DOESN'T ALREADY EXIST
#        #self.child_models.add(child)
#        child.parent_model = self
#
#    def get_children(self):
#        return self.child_models.all()
#
#    def get_parent(self):
#        return self.parent_model
#
#    def get_descendents(self,descendents=[]):
#        children = self.get_children()
#        for child in children:
#            descendents.append(child)
#            child.get_descendents(descendents)
#        return descendents
#
#    def get_ancestors(self,ancestors=[]):
#        parent = self.get_parent()
#        if parent:
#            ancestores.append(parent)
#            parent.get_ancestors(ancestors)
#        return ancestors

    def __unicode__(self):
        return u'%s' % (self.name)

    def reset(self,reset_properties=False):
        # this resets values according to the proxy
        # to reset values according to the customizer, you must go through the corresponding modelform
        proxy = self.proxy

        if not proxy:
            msg = "Trying to reset a model w/out a proxy having been specified."
            raise QuestionnaireError(msg)

        self.active       = True
        self.name         = proxy.name
        self.order        = proxy.order
        self.description  = proxy.documentation
        self.version      = proxy.version

        self.is_document = proxy.is_document()

    def save(self,*args,**kwargs):
        if not self.id:
            self.created = timezone.now()
        self.last_modified = timezone.now()
        super(MetadataModel,self).save(*args,**kwargs)

class MetadataProperty(models.Model):

    class Meta:
        app_label   = APP_LABEL
        abstract    = True

    name         = models.CharField(max_length=SMALL_STRING,blank=False,null=False)
    order        = models.PositiveIntegerField(blank=True,null=True)
    field_type   = models.CharField(max_length=64,blank=True,choices=[(ft.getType(),ft.getName()) for ft in MetadataFieldTypes])

    def get_default_value(self):
        return "DEFAULT VALUE"
    

class MetadataStandardProperty(MetadataProperty):

    class Meta:
        app_label   = APP_LABEL
        abstract    = False

        ordering    = ['order']

    model           = models.ForeignKey("MetadataModel",blank=False,null=True,related_name="standard_properties")
    proxy           = models.ForeignKey("MetadataStandardPropertyProxy",blank=True,null=True)

    atomic_value            = models.CharField(max_length=HUGE_STRING,blank=True,null=True)
    enumeration_value       = models.CharField(max_length=HUGE_STRING,blank=True,null=True)
    enumeration_other_value = models.CharField(max_length=HUGE_STRING,blank=True,null=True)
    relationship_value      = models.ForeignKey("MetadataModel",blank=True,null=True)

    def reset(self):
        # this resets values according to the proxy
        # to reset values according to the customizer, you must go through the corresponding modelform
        proxy = self.proxy

        if not proxy:
            msg = "Trying to reset a standard property w/out a proxy having been specified."
            raise QuestionnaireError(msg)


        self.name         = proxy.name
        self.order        = proxy.order
        self.field_type   = proxy.field_type
        
        self.atomic_value             = None
        self.enumeration_value        = None
        self.enumeration_other_value  = "Please enter a custom value"
        self.relationship_value       = None

    def save(self,*args,**kwargs):        
        # TODO: if the customizer is required and the field is not displayed and there is no existing default value
        # then set it to default value
        super(MetadataStandardProperty,self).save(*args,**kwargs)

class MetadataScientificProperty(MetadataProperty):

    class Meta:
        app_label   = APP_LABEL
        abstract    = False

        ordering    = ['order']

    model           = models.ForeignKey("MetadataModel",blank=False,null=True,related_name="scientific_properties")
    proxy           = models.ForeignKey("MetadataScientificPropertyProxy",blank=True,null=True)

    is_enumeration  = models.BooleanField(blank=False,null=False,default=False)

    category_key = models.CharField(max_length=BIG_STRING,blank=True,null=True)

    atomic_value            = models.CharField(max_length=HUGE_STRING,blank=True,null=True)
    enumeration_value       = models.CharField(max_length=HUGE_STRING,blank=True,null=True)
    enumeration_other_value = models.CharField(max_length=HUGE_STRING,blank=True,null=True)

    extra_standard_name         = models.CharField(blank=True,null=True,max_length=BIG_STRING)
    extra_description           = models.TextField(blank=True,null=True)
    extra_units                 = models.CharField(blank=True,null=True,max_length=BIG_STRING)

    def reset(self):
        # this resets values according to the proxy
        # to reset values according to the customizer, you must go through the corresponding form
        proxy = self.proxy

        if not proxy:
            msg = "Trying to reset a scientific property w/out a proxy having been specified."
            raise QuestionnaireError(msg)

        self.name         = proxy.name
        self.order        = proxy.order
        self.category_key = proxy.category.key

        self.atomic_value             = None
        self.enumeration_value        = None
        self.enumeration_other_value  = "Please enter a custom value"
        
        self.field_type     = MetadataFieldTypes.PROPERTY.getType()
        self.is_enumeration = proxy.choice in ["OR","XOR"]
        
