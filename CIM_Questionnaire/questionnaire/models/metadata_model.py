
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
from django.template.defaultfilters import slugify

from questionnaire.utils        import *
from questionnaire.fields       import *
from questionnaire.models       import *

from CIM_Questionnaire.questionnaire.fields import EnumerationField
from CIM_Questionnaire.questionnaire.utils import DEFAULT_VOCABULARY

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

def find_model_by_key(key,sequence):
    for model in sequence:
        if model.get_model_key() == key:
            return model
    return None

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

    def __unicode__(self):
        label_property = find_in_sequence(lambda property: property.is_label==True,self.standard_properties.all())
        if label_property:
            return u"%s : %s" % (self.name,label_property.get_value())
        else:
            return u'%s' % (self.name)

    def get_model_key(self):
        return u"%s_%s" % (self.vocabulary_key,self.component_key)
    
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

    @classmethod
    def get_new_realization_set(cls, project, version, model_proxy, standard_property_proxies, scientific_property_proxies, model_customizer, vocabularies,  is_subrealization=False):
        """creates the full set of realizations required for a particular project/version/proxy combination w/ a specified list of vocabs"""

        model_parameters = {
            "project" : project,
            'version' : version,
            "proxy" : model_proxy,
        }
        # setup the root model...
        model = MetadataModel(**model_parameters)
        model.is_root = True
        if not is_subrealization and model_customizer.model_show_hierarchy:
            # TODO: DON'T LIKE DOING THIS HERE
            model.title = model_customizer.model_root_component
            model.vocabulary_key = slugify(DEFAULT_VOCABULARY)
            model.component_key = slugify(model_customizer.model_root_component)

        # it has to go in a list in-case it is part of a hierarchy
        # (the formsets assume a hierarchy; if not, it will just be a formset w/ 1 form)
        models = []
        models.append(model)

        for vocabulary in vocabularies:
            model_parameters["vocabulary_key"] = slugify(vocabulary.name)
            components = vocabulary.component_proxies.all()
            if components:
                # recursively go through the components of each vocabulary
                # adding corresponding models to the list
                root_component = components[0].get_root()
                model_parameters["parent"] = model
                model_parameters["title"] = u"%s : %s" % (vocabulary.name, root_component.name)
                create_models_from_components(root_component, model_parameters, models)

        standard_properties = {}
        scientific_properties = {}
        for model in models:
            model.reset(True)

            property_key = model.get_model_key()

            standard_properties[property_key] = []
            for standard_property_proxy in standard_property_proxies:
                 standard_property = MetadataStandardProperty(proxy=standard_property_proxy,model=model)
                 standard_property.reset()
                 standard_properties[property_key].append(standard_property)

            scientific_properties[property_key] = []
            try:
                for scientific_property_proxy in scientific_property_proxies[property_key]:
                    scientific_property = MetadataScientificProperty(proxy=scientific_property_proxy,model=model)
                    scientific_property.reset()
                    scientific_properties[property_key].append(scientific_property)
            except KeyError:
                # there were no scientific properties associated w/ this component (or, rather, no components associated w/ this vocabulary)
                # that's okay,
                scientific_properties[property_key] = []

        return (models,standard_properties,scientific_properties)

    @classmethod
    def get_existing_realization_set(cls, models, model_customizer, standard_property_customizers,  is_subrealization=False):
        """retrieves the full set of realizations used by a particular project/version/proxy combination """

        # standard_properties = {
        #     model.get_model_key() : model.standard_properties.all()
        #     for model in models
        # }
        #
        # scientific_properties = {
        #     model.get_model_key() : model.scientific_properties.all().order_by("proxy__category__order","order")
        #     for model in models
        # }

        standard_properties = {}
        scientific_properties = {}
        for model in models:

            property_key = model.get_model_key()
            if is_subrealization:
                property_key += str(model.pk)

            standard_properties[property_key] = model.standard_properties.all()
            scientific_properties[property_key] = model.scientific_properties.all().order_by("proxy__category__order","order")

        return (models, standard_properties, scientific_properties)

class MetadataProperty(models.Model):

    class Meta:
        app_label   = APP_LABEL
        abstract    = True

    name         = models.CharField(max_length=SMALL_STRING,blank=False,null=False)
    order        = models.PositiveIntegerField(blank=True,null=True)
    field_type   = models.CharField(max_length=64,blank=True,choices=[(ft.getType(),ft.getName()) for ft in MetadataFieldTypes])

    is_label     = models.BooleanField(blank=False,default=False)

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
    enumeration_value       = EnumerationField(blank=True,null=True)
    enumeration_other_value = models.CharField(max_length=HUGE_STRING,blank=True,null=True)
    # TODO: IN RESET MAKE THIS FK QS BOUND TO THE CORRECT TYPE OF METADATAMODEL
    relationship_value      = models.ManyToManyField("MetadataModel",blank=True,null=True)
    #relationship_value      = models.ForeignKey("MetadataModel",blank=True,null=True)

    def reset(self):
        # this resets values according to the proxy
        # to reset values according to the customizer, you must go through the corresponding modelform
        proxy = self.proxy

        if not proxy:
            msg = "Trying to reset a standard property w/out a proxy having been specified."
            raise QuestionnaireError(msg)


        self.name         = proxy.name
        self.order        = proxy.order
        self.is_label     = proxy.is_label
        self.field_type   = proxy.field_type
        
        self.atomic_value             = None
        self.enumeration_value        = None
        self.enumeration_other_value  = "Please enter a custom value"

        if self.pk:
            self.relationship_value.clear()

    def save(self,*args,**kwargs):        
        # TODO: if the customizer is required and the field is not displayed and there is no existing default value
        # then set it to default value
        super(MetadataStandardProperty,self).save(*args,**kwargs)

    def get_value(self):
        field_type = self.field_type
        if field_type == MetadataFieldTypes.ATOMIC:
            return self.atomic_value
        elif field_type == MetadaFieldTypes.ENUMERATION:
            # TODO
            pass
        else: # MetadataFieldTypes.RELATIONSHIP
            return u"%s" % self.relationship_value

    def __unicode__(self):
        return u'%s' % (self.name)

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
    enumeration_value       = EnumerationField(blank=True,null=True)
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
        self.is_label     = proxy.is_label
        self.category_key = proxy.category.key

        self.atomic_value             = None
        self.enumeration_value        = None
        self.enumeration_other_value  = "Please enter a custom value"
        
        self.field_type     = MetadataFieldTypes.PROPERTY.getType()
        self.is_enumeration = proxy.choice in ["OR","XOR"]

    def get_value(self):
        if not self.is_enumeration:
            return self.atomic_value
        else: # is_enumeration
            # TODO
            pass