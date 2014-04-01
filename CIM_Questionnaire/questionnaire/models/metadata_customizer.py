
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
__date__ ="Dec 27, 2013 10:30:35 AM"

"""
.. module:: questionnaire_customizer

Summary of module goes here

"""

from django.db import models

from datetime import datetime

from questionnaire.utils        import *
from questionnaire.fields       import *
from questionnaire.models.metadata_proxy    import *

class MetadataCustomizer(models.Model):
    class Meta:
        app_label   = APP_LABEL
        abstract    = True

    created                 = models.DateTimeField(blank=True,null=True,editable=False)
    last_modified           = models.DateTimeField(blank=True,null=True,editable=False)

    def save(self,*args,**kwargs):
        if not self.id:
            self.created = datetime.datetime.today()
        self.last_modified = datetime.datetime.now()
        super(MetadataCustomizer,self).save(*args,**kwargs)

    def get_field(self,field_name):
        try:
            field = self._meta.get_field_by_name(field_name)
        except FieldDoesNotExist:
            msg = "Could not find a field called '%s'" % (field_name)
            #raise QuestionnaireError(msg)
            print msg
            return None
        return field[0]

    @classmethod
    def get_field(cls,field_name):
        try:
            field = cls._meta.get_field_by_name(field_name)
        except FieldDoesNotExist:
            msg = "Could not find a field called '%s'" % (field_name)
            #raise QuestionnaireError(msg)
            print msg
            return None
        return field[0]

    def get_unique_together(self):
        # this fn is required because 'unique_together' validation is only enforced at the modelform
        # if all unique_together fields appear in the modelform; if not, I have to manually validate
        unique_together = self._meta.unique_together
        return list(unique_together)

class MetadataModelCustomizer(MetadataCustomizer):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False

        unique_together = ("name","project","version","proxy") # proxy defines the actual model

        # TODO: DELETE THESE NEXT TWO LINES
        verbose_name        = '(DISABLE ADMIN ACCESS SOON) Metadata Model Customizer'
        verbose_name_plural = '(DISABLE ADMIN ACCESS SOON) Metadata Model Customizers'

    proxy                   = models.ForeignKey("MetadataModelProxy",blank=True,null=True)

    project                 = models.ForeignKey("MetadataProject",blank=True,null=True,related_name="model_customizers")
    version                 = models.ForeignKey("MetadataVersion",blank=True,null=True,related_name="model_customizers")
    vocabularies            = models.ManyToManyField("MetadataVocabulary",blank=True,null=True)    # cannot set 'limit_choices_to' here, instead setting 'queryset' on form

    name                    = models.CharField(max_length=SMALL_STRING,blank=False,null=False)
    name.help_text          = "A unique name for this customization (ie: \"basic\" or \"advanced\")"
    description             = models.TextField(verbose_name="Customization Description",blank=True,null=True)
    description.help_text   = "An explanation of how this customization is intended to be used.  This information is for informational purposes only."
    default                 = models.BooleanField(verbose_name="Is Default Customization",blank=True,default=False)
    default.help_text       = "Defines the default customization that is used by this project/model combination if no explicit customization is provided."
    vocabularies            = models.ManyToManyField("MetadataVocabulary",blank=True,null=True)
    vocabularies.help_text  = "Choose which Controlled Vocabularies apply to this model."

    model_title             = models.CharField(max_length=BIG_STRING,verbose_name="Name that should appear on the Document Form",blank=False,null=True)
    model_description       = models.TextField(verbose_name="A description of the document",blank=True,null=True)
    model_show_all_categories = models.BooleanField(verbose_name="Display empty categories",default=False)
    model_show_all_categories.help_text = "Include categories in the editing form for which there are no attributes associated with"
    model_show_all_properties   = models.BooleanField(verbose_name="Display uncategorized fields",default=True)
    model_show_all_properties.help_text = "Include attributes in the editing form that have no associated category.  These will show up below any category tabs."
    model_show_hierarchy         = models.BooleanField(verbose_name="Include the full component hierarchy",default=True)
    model_show_hierarchy.help_text ="Some CIM SoftwareComponents are comprised of a hierarchy of nested child components.  Checking this option allows that full hiearchy to be edited at once in the CIM Editor."
    model_root_component = models.CharField(max_length=LIL_STRING,verbose_name="Name of the root component",blank=True,validators=[validate_no_spaces],default="RootComponent")
    model_root_component.help_text = "If this component uses mulitple CVs, then the corresponding component hierarchies will be grouped under a single root component.  Please provide the component name here."

    def __unicode__(self):
    #    return u'%s::%s::%s' % (self.project,self.proxy,self.name)
        return u'%s' % (self.name)

    def reset(self):
        proxy = self.proxy

        if not proxy:
            msg = "Trying to reset a customizer w/out a proxy having been specified."
            raise QuestionnaireError(msg)

        self.model_title                = proxy.name
        self.model_description          = proxy.documentation

        self.model_show_all_categories  = self.get_field("model_show_all_categories").default
        self.model_show_all_properties  = self.get_field("model_show_all_properties").default
        self.model_show_hierarchy       = self.get_field("model_show_hierarchy").default
        self.model_root_component       = self.get_field("model_root_component").default

    def clean(self):
        # force name to be lowercase
        # this avoids hacky methods of ensuring case-insensitive uniqueness
        self.name = self.name.lower()

    def save(self,*args,**kwargs):
        # only one customizer can be default at a time
        if self.default:
            try:
                current_default_customizer = MetadataModelCustomizer.objects.get(default=True)
                if self != temp:
                    current_default_customizer.default = False
                    current_default_customizer.save()
            except MetadataModelCustomizer.DoesNotExist:
                pass
        super(MetadataModelCustomizer,self).save(*args,**kwargs)

class MetadataCategoryCustomizer(MetadataCustomizer):
    class Meta:
        app_label   = APP_LABEL
        abstract    = True

    pending_deletion        = models.BooleanField(blank=False,default=False)

class MetadataStandardCategoryCustomizer(MetadataCategoryCustomizer):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False

        ordering        = ['order']
        unique_together = ("name","project","proxy","model_customizer")

    model_customizer        = models.ForeignKey("MetadataModelCustomizer",blank=True,null=True,related_name="standard_property_category_customizers")

    proxy                   = models.ForeignKey("MetadataStandardCategoryProxy",blank=True,null=True)

    project                 = models.ForeignKey("MetadataProject",blank=True,null=True,related_name="model_standard_category_customizers")
    version                 = models.ForeignKey("MetadataVersion",blank=True,null=True,related_name="model_standard_category_customizers")

    name                    = models.CharField(max_length=BIG_STRING,blank=False,null=False)
    key                     = models.CharField(max_length=BIG_STRING,blank=True,null=True)
    description             = models.TextField(blank=True,null=True)
    order                   = models.PositiveIntegerField(blank=True,null=True)
    order.help_text = "Drag and drop the corresponding category widget to modify its order."


    def __unicode__(self):
        #return u'%s::%s' % (self.project,self.proxy)
        return u'%s' % (self.name)

    def __init__(self,*args,**kwargs):
        super(MetadataStandardCategoryCustomizer,self).__init__(*args,**kwargs)
        if not self.project:
            if self.model_customizer:   # put this check in for the ajax_customize_category fn
                self.project = self.model_customizer.project
        if not self.version:
            if self.model_customizer:   # put this check in for the ajax_customize_category fn
                self.version = self.model_customizer.version
        
    def reset(self):
        proxy = self.proxy

        if not proxy:
            msg = "Trying to reset a MetadataStandardCategoryCustomizer w/out a proxy having been specified."
            raise QuestionnaireError(msg)

        self.name               = proxy.name
        self.key                = proxy.key
        self.description        = proxy.description
        self.order              = proxy.order
        self.pending_deletion   = False

class MetadataScientificCategoryCustomizer(MetadataCategoryCustomizer):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False

        ordering        = ['order']
        unique_together = ("name","project","proxy","vocabulary_key","component_key","model_customizer")

    model_customizer        = models.ForeignKey("MetadataModelCustomizer",blank=True,null=True,related_name="scientific_property_category_customizers")

    proxy                   = models.ForeignKey("MetadataScientificCategoryProxy",blank=True,null=True)

    project                 = models.ForeignKey("MetadataProject",blank=True,null=True,related_name="model_scientific_category_customizers")
    vocabulary_key          = models.CharField(blank=True,null=True,max_length=BIG_STRING)
    component_key           = models.CharField(blank=True,null=True,max_length=BIG_STRING)

    name                    = models.CharField(max_length=BIG_STRING,blank=False,null=False)
    key                     = models.CharField(max_length=BIG_STRING,blank=True,null=True)
    description             = models.TextField(blank=True,null=True)
    order                   = models.PositiveIntegerField(blank=True,null=True)
    order.help_text = "Drag and drop the corresponding category widget to modify its order."


    def __unicode__(self):
        #return u'%s::%s' % (self.project,self.proxy)
        return u'%s'%(self.name)

    def __init__(self,*args,**kwargs):
        super(MetadataScientificCategoryCustomizer,self).__init__(*args,**kwargs)
        if not self.project:
            if self.model_customizer:   # put this check in for the ajax_customize_category fn
                self.project = self.model_customizer.project

    def reset(self,reset_keys=False):
        proxy = self.proxy
        if not self.proxy:
            msg = "Trying to reset a MetadataScientificCategoryCustomizer w/out a proxy having been specified."
            raise QuestionnaireError(msg)

        if proxy:
            self.name               = proxy.name
            self.description        = proxy.description
            self.key                = proxy.key
            self.order              = proxy.order

            if reset_keys:
                component = proxy.component
                self.component_key      = slugify(component.name)
                self.vocabulary_key     = slugify(component.vocabulary.name)

        self.pending_deletion   = False



class MetadataPropertyCustomizer(MetadataCustomizer):
    class Meta:
        app_label   = APP_LABEL
        abstract    = True
        ordering = ['order']

    name        = models.CharField(max_length=SMALL_STRING,blank=False,null=False)
    order       = models.PositiveIntegerField(blank=True,null=True)
    field_type  = models.CharField(max_length=64,blank=True,choices=[(ft.getType(),ft.getName()) for ft in MetadataFieldTypes])

    # ways to customize _any_ field...
    displayed           = models.BooleanField(default=True,blank=True,verbose_name="should this property be displayed?")
    required            = models.BooleanField(default=True,blank=True,verbose_name="is this property required?")
    editable            = models.BooleanField(default=True,blank=True,verbose_name="can the value of this property be edited?")
    unique              = models.BooleanField(default=False,blank=True,verbose_name="must the value of this property be unique?")
    verbose_name        = models.CharField(max_length=64,blank=False,verbose_name="how should this property be labeled (overrides default name)?")
    default_value       = models.CharField(max_length=128,blank=True,null=True,verbose_name="what is the default value of this property?")
    documentation       = models.TextField(blank=True,verbose_name="what is the help text to associate with property?")
    inline_help         = models.BooleanField(default=False,blank=True,verbose_name="should the help text be displayed inline?")
    
    
class MetadataStandardPropertyCustomizer(MetadataPropertyCustomizer):
    class Meta:
        app_label    = APP_LABEL
        abstract     = False

    proxy            = models.ForeignKey("MetadataStandardPropertyProxy",blank=True,null=True)
    model_customizer = models.ForeignKey("MetadataModelCustomizer",blank=False,null=True,related_name="standard_property_customizers")

    category         = models.ForeignKey("MetadataStandardCategoryCustomizer",blank=True,null=True,related_name="standard_propery_customizers")
    category_name    = models.CharField(blank=True,null=True,max_length=BIG_STRING)

    inherited           = models.BooleanField(default=False,blank=True,verbose_name="can this property be inherited by children?")
    inherited.help_text = "Enabling inheritance will allow the correponding properties of child components to 'inherit' the value of this property.  The editing form will allow users the ability to 'opt-out' of this inheritance."

    # ways to customize an atomic field
    suggestions         = models.TextField(blank=True,verbose_name="are there any suggestions you would like to offer to users?")
    suggestions.help_text = "Please enter a \"|\" separated list.  These suggestions will only take effect for text fields, in the case of Standard Properties, or for text fields or when \"OTHER\" is selected, in the case of Scientific Properties.  They appear as an auto-complete widget and not as a formal enumeration."

    # ways to customize an enumeration field
    enumeration_choices  = EnumerationField(blank=True,null=True,verbose_name="choose the property values that should be presented to users.")
    enumeration_default  = EnumerationField(blank=True,null=True,verbose_name="choose the default value(s), if any, for this property.")
    enumeration_open     = models.BooleanField(default=False,blank=True,verbose_name="check if a user can specify a custom property value.")
    enumeration_multi    = models.BooleanField(default=False,blank=True,verbose_name="check if a user can specify multiple property values.")
    enumeration_nullable = models.BooleanField(default=False,blank=True,verbose_name="check if a user can specify an explicit \"NONE\" value.")

    # ways to customize a relationship field
    relationship_cardinality   = CardinalityField(blank=True,verbose_name="how many instances (min/max) of this property are allowed?")
    relationship_show_subform  = models.BooleanField(default=False,blank=True,verbose_name="should this property be rendered in its own subform?")
    relationship_show_subform.help_text = "Checking this will cause the property to be rendered as a nested subform within the <i>parent</i> form; All properties of this model will be available to view and edit in that subform.\
                                          Unchecking it will cause the attribute to be rendered as a simple select widget.  This option is only available if the \"parent\" customizer has been saved."
    subform_customizer         = models.ForeignKey("MetadataModelCustomizer",blank=True,null=True,related_name="property_customizer")

#    def __unicode__(self):
#        return u'%s::%s' % (self.model_customizer,self.proxy.name)

    def __init__(self,*args,**kwargs):
        super(MetadataStandardPropertyCustomizer,self).__init__(*args,**kwargs)

    def reset(self,reset_category=False):
        proxy = self.proxy

        if not proxy:
            msg = "Trying to reset a MetadataStandardPropertyCustomizer w/out a proxy having been specified."
            raise QuestionnaireError(msg)

        self.field_type     = proxy.field_type
        self.name           = proxy.name
        self.order          = proxy.order
        self.verbose_name   = proxy.name
        self.documentation  = proxy.documentation
        self.inline_help    = False

        # atomic fields...
        
        # enumeration fields...
        if self.field_type == MetadataFieldTypes.ENUMERATION:
            enumeration_choices_field = self.get_field("enumeration_choices")
            enumeration_choices_field.set_choices(proxy.enumeration_choices.split("|"))

        # relationship fields...
        if self.field_type == MetadataFieldTypes.RELATIONSHIP:
            self.relationship_cardinality = proxy.relationship_cardinality.split("|")
            self.relationship_show_subform = False

        if reset_category:
            if self.category:
                self.category.reset()
        
class MetadataScientificPropertyCustomizer(MetadataPropertyCustomizer):
    class Meta:
        app_label    = APP_LABEL
        abstract     = False

    proxy            = models.ForeignKey("MetadataScientificPropertyProxy",blank=True,null=True)
    model_customizer = models.ForeignKey("MetadataModelCustomizer",blank=False,null=True,related_name="scientific_property_customizers")

    vocabulary_key   = models.CharField(blank=True,null=True,max_length=BIG_STRING)
    component_key   = models.CharField(blank=True,null=True,max_length=BIG_STRING)

    category         = models.ForeignKey("MetadataScientificCategoryCustomizer",blank=True,null=True,related_name="scientific_propery_customizers")
    category_name    = models.CharField(blank=True,null=True,max_length=BIG_STRING)
    
#    def __unicode__(self):
#        return u'%s::%s' % (self.model_customizer,self.proxy.name)

    def reset(self,reset_category=False):
        proxy = self.proxy
        
        if not proxy:
            msg = "Trying to reset a MetadataScientificPropertyCustomizer w/out a proxy having been specified."
            raise QuestionnaireError(msg)

        self.name           = proxy.name
        self.order          = proxy.order
        self.verbose_name   = proxy.name
        self.field_type     = MetadataFieldTypes.PROPERTY
        self.inline_help    = False

        if reset_category:
            if self.category:
                self.category.reset()
