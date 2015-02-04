
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
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone

from mptt.models import MPTTModel, TreeForeignKey
from uuid import uuid4

from CIM_Questionnaire.questionnaire.models.metadata_serialization import MetadataModelSerialization, MetadataSerializationFormats
from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes, EnumerationField, EMPTY_CHOICE, NULL_CHOICE, OTHER_CHOICE
from CIM_Questionnaire.questionnaire.utils import APP_LABEL, DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY, LIL_STRING, SMALL_STRING, BIG_STRING, HUGE_STRING, QuestionnaireError
from CIM_Questionnaire.questionnaire.utils import find_in_sequence
from CIM_Questionnaire.questionnaire import get_version


#############################################
# create a hierarchy of models based on the #
# built-in hierarchical relationships that  #
# mppt adds to components                   #
#############################################

def create_models_from_components(component_node,model_parameters,models=[]):
    """
    recursively look through mppt components to recreate that hierarchy in models
    :param component_node:
    :param model_parameters:
    :param models:
    :return: None
    """
    title = model_parameters["title"]
    model_parameters["title"] = title[:title.index(" : ")] + " : " + component_node.name
    model_parameters["component_key"] = component_node.get_key()

    model = MetadataModel(**model_parameters)
    models.append(model)
    for child_component in component_node.get_children():
        model_parameters["parent"] = model
        create_models_from_components(child_component,model_parameters,models)


def get_model_parent_dictionary(models):
    """
    given a list of models, returns a dictionary of parent-child relationships (based on keys)
    :param models:
    :return: model_instances
    """
    model_parent_dictionary = {}
    for model in models:
        if model.parent:
            model_parent_dictionary[model.get_model_key()] = model.parent.get_model_key()
        else:
            model_parent_dictionary[model.get_model_key()] = None
    return model_parent_dictionary


#################
# MetadataModel #
#################

class MetadataModel(MPTTModel):

    class Meta:
        app_label   = APP_LABEL
        abstract    = False

        # TODO: DELETE THESE NEXT TWO LINES
        verbose_name        = '(DISABLE ADMIN ACCESS SOON) Metadata Model'
        verbose_name_plural = '(DISABLE ADMIN ACCESS SOON) Metadata Models'

    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')

    created         = models.DateTimeField(blank=True,null=True,editable=False)
    last_modified   = models.DateTimeField(blank=True,null=True,editable=False)

    guid = models.CharField(blank=True, null=True, max_length=LIL_STRING, unique=True, editable=False)
    document_version = models.CharField(blank=False, max_length=LIL_STRING, editable=False, default="0.0")

    proxy           = models.ForeignKey("MetadataModelProxy", blank=False, null=True, related_name="models")
    project         = models.ForeignKey("MetadataProject", blank=True, null=True, related_name="models")
    version         = models.ForeignKey("MetadataVersion", blank=False, null=True, related_name="models")

    is_document     = models.BooleanField(blank=False, null=False, default=False)
    is_root         = models.BooleanField(blank=False, null=False, default=False)
    is_published    = models.BooleanField(blank=False, null=False, default=False)

    vocabulary_key  = models.CharField(max_length=BIG_STRING, blank=True, null=True)
    component_key   = models.CharField(max_length=BIG_STRING, blank=True, null=True)
    title           = models.CharField(max_length=BIG_STRING, blank=True, null=True)

    active          = models.BooleanField(blank=False, null=False, default=True)
    name            = models.CharField(max_length=SMALL_STRING, blank=False, null=False)
    description     = models.CharField(max_length=HUGE_STRING, blank=True, null=True)
    order           = models.PositiveIntegerField(blank=True, null=True)

    def __unicode__(self):
        label = self.get_label()
        if label:
            return u"%s : %s" % (self.name, label)
        else:
            return u'%s' % self.name

    def get_label(self):
        label_property = find_in_sequence(lambda property: property.is_label == True, self.standard_properties.all())
        if label_property:
            return u"%s" % label_property.get_value()
        else:
            return None

    def get_model_key(self):
        return u"%s_%s" % (self.vocabulary_key, self.component_key)
    
    def reset(self):
        # this resets values according to the proxy
        # to reset values according to the customizer, you must go through the corresponding form
        proxy = self.proxy

        if not proxy:
            msg = "Trying to reset a model w/out a proxy having been specified."
            raise QuestionnaireError(msg)

        self.active      = True
        self.name        = proxy.name
        self.order       = proxy.order
        self.description = proxy.documentation
        self.version     = proxy.version

        self.is_document = proxy.is_document()

    def save(self,*args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        if not self.guid:
            self.guid = str(uuid4())
        self.document_version = u"%s.%s" % (self.get_major_version(), int(self.get_minor_version())+1)
        self.last_modified = timezone.now()
        super(MetadataModel, self).save(*args, **kwargs)

    def update(self, model_customization):
        """
        looks through the customization and checks if any properties are set to display that do not already exist in this instance
        :param model_customization:
        :return:
        """
        standard_properties = self.standard_properties.all()
        for standard_property_customization in model_customization.standard_property_customizers.all():
            if standard_property_customization.displayed:
                standard_property_proxy = standard_property_customization.proxy
                standard_property = find_in_sequence(lambda sp: sp.proxy == standard_property_proxy, standard_properties)
                if standard_property:
                    if standard_property.field_type == "RELATIONSHIP":
                        for submodel in standard_property.relationship_value.all():
                            submodel_customizer = standard_property_customization.subform_customizer
                            if submodel_customizer:
                                submodel.update(submodel_customizer)
                else:
                    new_standard_property = MetadataStandardProperty(
                        proxy=standard_property_proxy,
                        model=self,
                    )
                    new_standard_property.reset()
                    new_standard_property.save()
                    # TODO: DOES THIS WORK FOR ALL TYPES OF STANDARD_PROPERTIES?
                    pass

    def get_id(self):
        return self.guid

    def get_major_version(self):
        major, minor = self.document_version.split(".")
        return major

    def get_minor_version(self):
        major, minor = self.document_version.split(".")
        return minor

    def publish(self, force_save=True):

        if not self.id:
            raise QuestionnaireError("cannot publish an unsaved model")

        # TODO: SHOULD I UPDATE THE MAJOR VERSIONS OF ALL CHILD COMPONENTS?
        # [https://github.com/ES-DOC/esdoc-questionnaire/issues/15]
        self.document_version = u"%s.%s" % (int(self.get_major_version())+1, 0)
        self.is_published = True

        if force_save:
            self.save()
            self.serialize()

    # NO LONGER SERIALIZING TO FILE
    # INSTEAD SERIALIZING TO MODEL (MetadataModelSerialization) AND GENERATING ON-DEMAND
    # SO THAT ATOM FEED CAN LIST ALL SERIALIZATIONS (ie: ALL VERSIONS) IN THE DB
    # def serialize(self):
    #
    #     dict = {
    #         "project" : self.project,
    #         "version" : self.version,
    #         "proxy" : self.proxy,
    #         "model" : self
    #     }
    #     serialization_template_path = "questionnaire/serialization/%s.xml" % (self.proxy.name.lower())
    #     serialized_model = render_to_string(serialization_template_path, dict )
    #
    #     serialized_model_path = os.path.join(settings.MEDIA_ROOT,"questionnaire/feed",self.project.name.lower(),self.version.name.lower(),self.proxy.name.lower())
    #     serialized_model_path += u"/%s_%s.xml" % (self.get_id(), self.get_major_version())
    #     if not os.path.exists(os.path.dirname(serialized_model_path)):
    #         os.makedirs(os.path.dirname(serialized_model_path))
    #
    #     with open(serialized_model_path, 'w') as file:
    #         file.write(serialized_model)

    def serialize(self, serialization_version=None, serialization_format=MetadataSerializationFormats.ESDOC_XML):

        serialization_dict = {
            "format" : MetadataSerializationFormats.ESDOC_XML,
            "project" : self.project,
            "version" : self.version,
            "proxy" : self.proxy,
            "model" : self,
            "questionnaire_version" : get_version(),

        }
        serialization_template_path = "questionnaire/serialization/%s/%s.xml" % (serialization_format.getType(), self.proxy.name.lower())
        serialized_model = render_to_string(serialization_template_path, serialization_dict )

        new_serialization_kwargs = {
            "model" : self,
            "name" : self.guid,
            "format" : serialization_format,
        }
        if serialization_version:
            new_serialization_kwargs["version"] = serialization_version
        else:
            new_serialization_kwargs["version"] = self.get_major_version()
        (serialization, created_serialization) = MetadataModelSerialization.objects.get_or_create(**new_serialization_kwargs)

        serialization.content = serialized_model
        if created_serialization:
            serialization.publication_date = timezone.now()

        serialization.save()

    @classmethod
    def get_new_realization_set(cls, project, version, model_proxy, standard_property_proxies, scientific_property_proxies, model_customizer, vocabularies):
        """
        creates the full set of realizations required for a particular project/version/proxy combination w/ a specified list of vocabs
        :param project
        :param version
        :param model_proxy
        :param standard_property_proxies
        :param scientific_property_proxies
        :param vocabularies
        """

        models = []
        model_parameters = {
            "project" : project,
            'version' : version,
            "proxy" : model_proxy,
        }

        if model_customizer.model_show_hierarchy or len(vocabularies) == 0:
            # setup the root model...
            model = MetadataModel(**model_parameters)
            model.vocabulary_key = DEFAULT_VOCABULARY_KEY
            model.component_key = DEFAULT_COMPONENT_KEY
            model.title = model_customizer.model_root_component
            model.is_root = True
            models.append(model)

        for vocabulary in vocabularies:
            if model_customizer.model_show_hierarchy:
                model_parameters["parent"] = model
                model_parameters["is_root"] = False
            else:
                model_parameters.pop("parent",None)
                model_parameters["is_root"] = True
            model_parameters["vocabulary_key"] = vocabulary.get_key()
            components = vocabulary.component_proxies.all()
            if components:
                # recursively go through the components of each vocabulary,
                # adding corresponding models to the list
                root_component = components[0].get_root()
                model_parameters["title"] = u"%s : %s" % (vocabulary.name, root_component.name)
                create_models_from_components(root_component, model_parameters, models)

        standard_properties = {}
        scientific_properties = {}
        for i, model in enumerate(models):
            model.reset()

            property_key = model.get_model_key()
            # since this is _not_ being created in the context of a subform,
            # each model in models corresponds to a separate component and will therefore have a unique key

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

        return (models, standard_properties, scientific_properties)

    @classmethod
    def get_new_subrealization_set(cls, project, version, model_proxy, standard_property_proxies, scientific_property_proxies, model_customizer, vocabularies, parent_vocabulary_key, parent_component_key):
        """creates the full set of realizations required for a particular project/version/proxy combination w/ a specified list of vocabs"""

        model_parameters = {
            "project" : project,
            'version' : version,
            "proxy" : model_proxy,
        }
        # setup the root model...
        model = MetadataModel(**model_parameters)
        model.vocabulary_key = parent_vocabulary_key
        model.component_key = parent_component_key
        model.is_root = True

        if model_customizer.model_show_hierarchy:
            # TODO: DON'T LIKE DOING THIS HERE
            model.title = model_customizer.model_root_component

        # it has to go in a list in-case
        #  is part of a hierarchy
        # (the formsets assume a hierarchy; if not, it will just be a formset w/ 1 form)
        models = []
        models.append(model)

        for vocabulary in vocabularies:
            model_parameters["vocabulary_key"] = vocabulary.get_key()
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
        for i, model in enumerate(models):
            model.reset()

            property_key = model.get_model_key()
            # since this _is_ being created in the context of a subform,
            # then all models will correspond to the same component (ie: the component of the "parent" model of the property w/ subforms)
            # so I add a counter to make it unique (and using the format "-i" keeps it consistent w/ how forms & formsets work in Django)
            property_key += "-%s" % (i)

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

        return (models, standard_properties, scientific_properties)

    @classmethod
    def get_existing_realization_set(cls, models, model_customizer, vocabularies=None):

        """retrieves the full set of realizations used by a particular project/version/proxy combination """

        standard_properties = {}
        scientific_properties = {}
        for model in models:

            property_key = model.get_model_key()

            standard_properties[property_key] = model.standard_properties.all()
            if not vocabularies:
                scientific_properties[property_key] = model.scientific_properties.all().order_by("proxy__category__order","order")
            else:
                # TODO: THIS IS LIKELY TO BE AN INEFFICIENT DB CALL; RESTRUCTURE IT
                scientific_properties[property_key] = model.scientific_properties.filter(proxy__component__vocabulary__in=vocabularies).order_by("proxy__category__order","order")

        return (models, standard_properties, scientific_properties)

    @classmethod
    def get_existing_subrealization_set(cls, models, model_customizer, vocabularies=None):

        """retrieves the full set of realizations used by a particular project/version/proxy combination """

        standard_properties = {}
        scientific_properties = {}
        for i, model in enumerate(models):

            property_key = model.get_model_key()
            # since this _is_ being created in the context of a subform,
            # then all models will correspond to the same component (ie: the component of the "parent" model of the property w/ subforms)
            # so I add a counter to make it unique (and using the format "-i" keeps it consistent w/ how forms & formsets work in Django)
            property_key += "-%s" % (i)

            standard_properties[property_key] = model.standard_properties.all()
            if not vocabularies:
                scientific_properties[property_key] = model.scientific_properties.all().order_by("proxy__category__order","order")
            else:
                # TODO: THIS IS LIKELY TO BE AN INEFFICIENT DB CALL; RESTRUCTURE IT
                scientific_properties[property_key] = model.scientific_properties.filter(proxy__component__vocabulary__in=vocabularies).order_by("proxy__category__order","order")

        return (models, standard_properties, scientific_properties)

    @classmethod
    def save_realization_set(cls,models,standard_properties,scientific_properties):

        # this fn is called outside of the forms
        # hence, I have to set model explicitly in each property
        # since it's not automated by virtue of being in an inlineformset

        for model in models:
            model_key = model.get_model_key()

            model.save()

            for standard_property in standard_properties[model_key]:
                standard_property.model = model
                standard_property.save()

            for scientific_property in scientific_properties[model_key]:
                scientific_property.model = model
                scientific_property.save()

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
        app_label = APP_LABEL
        abstract = False

        ordering = ['order']

        # TODO: DELETE THESE NEXT TWO LINES
        verbose_name        = '(DISABLE ADMIN ACCESS SOON) Metadata Standard Property'
        verbose_name_plural = '(DISABLE ADMIN ACCESS SOON) Metadata Standard Properties'

    model        = models.ForeignKey("MetadataModel",blank=False,null=True,related_name="standard_properties")
    proxy        = models.ForeignKey("MetadataStandardPropertyProxy",blank=True,null=True)

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
        if self.proxy:
            self.is_label = self.proxy.is_label
        super(MetadataStandardProperty,self).save(*args,**kwargs)

    def get_value(self):
        """

        :return:
        """
        field_type = self.field_type

        if field_type == MetadataFieldTypes.ATOMIC:
            return self.atomic_value

        elif field_type == MetadataFieldTypes.ENUMERATION:
            enumerations = self.enumeration_value.split("|")
            if OTHER_CHOICE[0] in enumerations:
                if self.enumeration_other_value:
                    enumerations.append(u"OTHER: %s" % (self.enumeration_other_value))
            return enumerations

        else: # MetadataFieldTypes.RELATIONSHIP
            return self.relationship_value.all()

    def __unicode__(self):
        return u'%s' % (self.name)

class MetadataScientificProperty(MetadataProperty):

    class Meta:
        app_label   = APP_LABEL
        abstract    = False

        ordering    = ['order']

        # TODO: DELETE THESE NEXT TWO LINES
        verbose_name        = '(DISABLE ADMIN ACCESS SOON) Metadata Scientific Property'
        verbose_name_plural = '(DISABLE ADMIN ACCESS SOON) Metadata Scientific Properties'

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