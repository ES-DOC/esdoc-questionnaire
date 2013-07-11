
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
__date__ ="Jun 10, 2013 4:10:50 PM"

"""
.. module:: metadata_customizer

Summary of module goes here

"""
from django.db import models

from dcf.utils  import *
from dcf.models import *

from dcf.models.metadata_proxy import *

class MetadataCustomizer(models.Model):
    class Meta:
        app_label   = APP_LABEL
        abstract    = True


    _guid = models.CharField(max_length=64,unique=True,editable=False,blank=False,default=lambda:str(uuid4()))

    project = models.ForeignKey("MetadataProject",blank=False,editable=True)
    version = models.ForeignKey("MetadataVersion",blank=False,editable=True)
    model   = models.CharField(max_length=BIG_STRING,blank=False,editable=True)

    def getGUID(self):
        return self._guid

    def save(self,*args,**kwargs):
        super(MetadataCustomizer,self).save(*args,**kwargs)

    def getCommonCustomizers(self):
        """
        returns a list of customizers (either ModelCustomizers or AtrributeCustomzizers, or PropertyCustomizers)
        belonging to the same project/version/model combination
        """
        model_class = self.__class__
        return model_class.objects.filter(project=self.project,version=self.version,model=self.model)

    def getProject(self):
        return self.project

    def getVersion(self):
        return self.version

    def getCategorization(self):
        # TODO: THIS ASSUMES THERE IS ONE CATEGORIZATION; THERE COULD BE MORE THAN ONE IN A FUTURE VERSION
        categorizations = self.version.categorizations.all()
        return categorizations[0] if categorizations else None

    def getUniqueTogether(self):
        unique_together = self._meta.unique_together
        return list(unique_together)

class MetadataModelCustomizer(MetadataCustomizer):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        # TODO: REDO THIS W/ MYSQL (SEE http://stackoverflow.com/questions/6153552/mysql-error-1062-duplicate-entry-for-key-2)
        # ACTUALLY, OVERRIDING validate_unique ON THE FORMS WORKS PRETTY WILL
        unique_together = ('project', 'version', 'model', 'name',)
        verbose_name        = 'Model Customizer'
        verbose_name_plural = 'Model Customizers'

    name                = models.CharField(max_length=255,verbose_name="Customization Name",blank=False,validators=[validate_no_spaces])
    name.help_text      = "A unique name for this customization (ie: \"basic\" or \"advanced\")"
    description         = models.TextField(verbose_name="Customization Description",blank=True)
    description.help_text = "An explanation of how this customization is intended to be used.  This information is for informational purposes only."
    default             = models.BooleanField(verbose_name="Is Default Customization",blank=True)
    default.help_text   = "Defines the default customization that is used by this project/model combination if no explicit customization is provided"
    vocabularies        = models.ManyToManyField("MetadataVocabulary",blank=True,null=True)
    vocabularies.help_text = "Choose which Controlled Vocabularies apply to this model."

    model_title         = models.CharField(max_length=BIG_STRING,verbose_name="Name that should appear on the Document Form",blank=False)
    model_description   = models.TextField(verbose_name="A description of the document",blank=True)
    model_show_all_categories = models.BooleanField(verbose_name="Display empty categories",default=False)
    model_show_all_categories.help_text = "Include categories in the editing form for which there are no attributes associated with"
    model_show_all_properties = models.BooleanField(verbose_name="Display uncategorized fields",default=True)
    model_show_all_properties.help_text = "Include attributes in the editing form that have no associated category.  These will show up below any category tabs."
    model_nested        = models.BooleanField(verbose_name="Include the full component hierarchy",default=True)
    model_nested.help_text ="Some CIM SoftwareComponents are comprised of a hierarchy of nested child components.  Checking this option allows that full hiearchy to be edited at once in the CIM Editor."
    model_root_component = models.CharField(max_length=LIL_STRING,verbose_name="Name of the root component",blank=True,validators=[validate_no_spaces])
    model_root_component.help_text = "If this SoftwareComponent uses mulitple CVs, then the corresponding component hierarchies can either be grouped under a single root component, or else kept separate.  If they are to be grouped under a single root component, please provide the component name here."

    def __unicode__(self):
        return u"%s::%s ('%s')" % (self.project,self.model,self.name)

    def getProject(self):
        return self.project

    def getVersion(self):
        return self.version

    def getModel(self):
        """
        .. note: this returns a class not an instance
        """
        version = self.getVersion()
        return version.getModelClass(self.model)

    def updateScientificProperties(self):
        vocabularies = self.vocabularies.all()

        customizer_filter_parameters = {
            "project"   : self.project,
            "version"   : self.version,
            "model"     : self.model,
        }

        scientific_property_proxies = MetadataScientificPropertyProxy.objects.filter(vocabulary__in=vocabularies)
        for scientific_property_proxy in scientific_property_proxies:
            customizer_filter_parameters["proxy"]           = scientific_property_proxy
            customizer_filter_parameters["name"]            = scientific_property_proxy.name
            customizer_filter_parameters["component_name"]  = scientific_property_proxy.component_name
            customizer_filter_parameters["category"]        = scientific_property_proxy.category
            (scientific_property_customizer, created) = MetadataScientificPropertyCustomizer.objects.get_or_create(**customizer_filter_parameters)
            if created:
                print "adding %s to %s" % (scientific_property_customizer,self)
                scientific_property_customizer.reset(scientific_property_proxy)
                scientific_property_customizer.setParent(self)
                scientific_property_customizer.save()


    def getStandardPropertyCustomizers(self):
        return self.standard_property_customizers.all()

    def getScientificPropertyCustomizers(self):
        return self.scientific_property_customizers.all()

    def getPropertyCustomizers(self):
        standard_property_customizers = self.getStandardPropertyCustomizers()
        scientific_property_customizers = self.getScientificPropertyCustomizers()
        return standard_property_customizers + scientific_property_customizers


    def getActiveStandardPropertyCustomizersByCategory(self):
        standard_property_customizers_by_category = {}
        standard_property_customizers = self.getStandardPropertyCustomizers()
        for category in self.getAllStandardCategories():
            current_standard_property_customizers = [
                standard_property_customizer for standard_property_customizer in standard_property_customizers
                if (standard_property_customizer.displayed  and standard_property_customizer.category == category)
            ]
            current_standard_property_customizers.sort(key = lambda x: x.order)
            standard_property_customizers_by_category[category.key] = current_standard_property_customizers
        return standard_property_customizers_by_category

    def getStandardCategories(self):
        if self.model_show_all_categories:
            return self.getAllStandardCategories()
        else:
            return self.getActiveStandardCategories()

    def getActiveStandardCategories(self):
        standard_categories = [standard_property_customizer.category for 
            standard_property_customizer in self.getStandardPropertyCustomizers()
            if (standard_property_customizer.category and standard_property_customizer.displayed)
        ]
        standard_categories = list(set(standard_categories))
        standard_categories.sort(key = lambda x: x.order)
        return standard_categories

    def getAllStandardCategories(self):
        standard_categories = [standard_property_customizer.category for
            standard_property_customizer in self.getStandardPropertyCustomizers()
            if standard_property_customizer.category
        ]
        standard_categories = list(set(standard_categories))
        standard_categories.sort(key = lambda x: x.order)
        return standard_categories

    def __init__(self,*args,**kwargs):
        super(MetadataModelCustomizer,self).__init__(*args,**kwargs)

#        # only one customizer can be the default one...
#        otherCustomizers = self.getCommonCustomizers().exclude(name=self.name)
#        if otherCustomizers.count() == 0:
#            # therefore, if this is the only customizer, it must be the default one...
#            self.default = True

    def save(self, *args, **kwargs):
        # only one customizer can be the default one...
        otherCustomizers = self.getCommonCustomizers().exclude(name=self.name)
        if otherCustomizers:
            if self.default:
                for customizer in otherCustomizers:
                    customizer.default = False
                    customizer.save()
        else:
            # if this is the only customizer, it must be the default one...
            self.default = True

        super(MetadataModelCustomizer, self).save(*args, **kwargs)

    def reset(self,proxy):

        self.model_title        = proxy.model_title
        self.model_description  = proxy.model_description
        self.show_all_categories = False
        self.show_all_properties = False
        self.model_nested        = True

class MetadataPropertyCustomizer(MetadataCustomizer):
    class Meta:
        app_label   = APP_LABEL
        abstract    = True

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=64,blank=True,choices=[(type.getType(),type.getName()) for type in MetadataFieldTypes])

    # ways to customize _any_ field...
    displayed           = models.BooleanField(default=True,blank=True,verbose_name="should this property be displayed?")
    required            = models.BooleanField(default=True,blank=True,verbose_name="is this property required?")
    editable            = models.BooleanField(default=True,blank=True,verbose_name="can the value of this property be edited?")
    unique              = models.BooleanField(default=False,blank=True,verbose_name="must the value of this property be unique?")
    verbose_name        = models.CharField(max_length=64,blank=False,verbose_name="how should this property be labeled (overrides default name)?")
    default_value       = models.CharField(max_length=128,blank=True,null=True,verbose_name="what is the default value of this property?")
    documentation       = models.TextField(blank=True,verbose_name="what is the help text to associate with property?")
    suggestions         = models.TextField(blank=True,verbose_name="are there any suggestions you would like to offer to users?")
    suggestions.help_text = "Please enter a \"|\" separated list.  These suggestions will only take effect for text fields, in the case of Standard Properties, or for text fields or when \"OTHER\" is selected, in the case of Scientific Properties.  They appear as an auto-complete widget and not as a formal enumeration."


   
    def save(self,*args,**kwargs):
        if self.parent:
            self.setParent(self.parent)
        super(MetadataPropertyCustomizer,self).save(*args,**kwargs)

    def setParent(self,model_customizer):
        self.parent     = model_customizer
        self.project    = model_customizer.project
        self.version    = model_customizer.version
        self.model      = model_customizer.model

    def __unicode__(self):
        if self.parent:
            return u'%s::%s (%s)' % (self.parent.model,self.name,self.parent.name)
        return u'%s' % self.name

class MetadataStandardPropertyCustomizer(MetadataPropertyCustomizer):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        verbose_name        = 'Standard Prop. Customizer'
        verbose_name_plural = 'Standard Prop. Customizers'

    parent = models.ForeignKey("MetadataModelCustomizer",related_name="standard_property_customizers",blank=False,null=True)

    proxy       = models.ForeignKey("MetadataStandardPropertyProxy",blank=True,related_name="customizer")
    category    = models.ForeignKey("MetadataStandardCategory",blank=True,null=True)
    field_type  = models.CharField(max_length=64,blank=True,null=True)
    order       = models.PositiveIntegerField(blank=True,null=True)

    # ways to customize an enumeration...
    enumeration_values   = EnumerationField(blank=True,null=True,verbose_name="choose the property values that should be presented to the user:")
    enumeration_default  = EnumerationField(blank=True,null=True,verbose_name="choose the default value(s), if any, for this property:")
    enumeration_choices  = models.TextField(blank=True,null=True)
    enumeration_open     = models.BooleanField(default=False,blank=True,verbose_name="check if a user can specify a custom property value.")
    enumeration_multi    = models.BooleanField(default=False,blank=True,verbose_name="check if a user can specify multiple property values.")
    enumeration_nullable = models.BooleanField(default=False,blank=True,verbose_name="check if a user can specify an explicit \"NONE\" value.")


    # ways to customize a relationship...
    relationship_target_model   = models.CharField(max_length=64,blank=True)
    relationship_source_model   = models.CharField(max_length=64,blank=True)
    relationship_cardinality    = CardinalityField(blank=True,verbose_name="how many instances (min/max) of this property are desired?")
    customize_subform           = models.BooleanField(default=False,blank=True,verbose_name="should this property be rendered in its own subform?")
    customize_subform.help_text = "Checking this radio button will cause the property to be rendered as a nested subform within the <i>parent</i> form; All properties of this model will be available to view and edit in that subform.\
                                   Unchecking it will cause the attribute to be rendered as a simple select widget."
    subform_customizer          = models.ForeignKey("MetadataModelCustomizer",blank=True,null=True,related_name="property_customizer")

    def getMin(self):
        try:
            cardinality = self.relationship_cardinality.split("|")
            return cardinality[0]
        except:
            return None

    def getMax(self):
        try:
            cardinality = self.relationship_cardinality.split("|")
            return cardinality[1]
        except:
            return None

    def save(self,*args,**kwargs):
        super(MetadataStandardPropertyCustomizer,self).save(*args,**kwargs)

    def reset(self,new_proxy):

        self.proxy          = new_proxy

        self.name           = new_proxy.name
        self.type           = new_proxy.type
        self.field_type     = new_proxy.field_type

        self.category       = new_proxy.category
        self.order          = new_proxy.id

        self.required       = new_proxy.required
        self.editable       = new_proxy.editable
        self.unique         = new_proxy.unique
        self.verbose_name   = new_proxy.verbose_name or new_proxy.name
        self.default_value  = new_proxy.default_value
        self.documentation  = new_proxy.documentation

        self.enumeration_choices    = new_proxy.enumeration_choices
        self.enumeration_open       = new_proxy.enumeration_open
        self.enumeration_multi      = new_proxy.enumeration_multi
        self.enumeration_nullable   = new_proxy.enumeration_nullable

        self.relationship_target_model  = new_proxy.relationship_target_model
        self.relationship_source_model  = new_proxy.relationship_source_model

    @classmethod
    def getDataFromProxy(cls,proxy):
        data = {
            "name"           : proxy.name,
            "type"           : proxy.type,
            "field_type"     : proxy.field_type,

            "category"       : proxy.category,
            "order"          : proxy.id,

            "required"       : proxy.required,
            "editable"       : proxy.editable,
            "unique"         : proxy.unique,
            "verbose_name"   : proxy.verbose_name or proxy.name,
            "default_value"  : proxy.default_value,
            "documentation"  : proxy.documentation,

            "enumeration_choices"    : proxy.enumeration_choices,
            "enumeration_open"       : proxy.enumeration_open,
            "enumeration_multi"      : proxy.enumeration_multi,
            "enumeration_nullable"   : proxy.enumeration_nullable,

            "relationship_target_model"  : proxy.relationship_target_model,
            "relationship_source_model"  : proxy.relationship_source_model,
        }
        return data

class MetadataScientificPropertyCustomizer(MetadataPropertyCustomizer):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        verbose_name        = 'Scientific Prop. Customizer'
        verbose_name_plural = 'Scientific Prop. Customizers'

    parent = models.ForeignKey("MetadataModelCustomizer",related_name="scientific_property_customizers",blank=False,null=True)

    proxy       = models.ForeignKey("MetadataScientificPropertyProxy",blank=True,related_name="customizer")
    category    = models.ForeignKey("MetadataScientificCategory",blank=True,null=True)
    order       = models.PositiveIntegerField(blank=True,null=True)

    component_name  = models.CharField(max_length=64,blank=True)
    vocabulary      = models.ForeignKey("MetadataVocabulary",blank=True,null=True)
    choice          = models.CharField(max_length=64,blank=False,choices=SCIENTIFIC_PROPERTY_CHOICES)
    open            = models.BooleanField(default=True,blank=True,verbose_name="check if a user can specify a custom property value.")
    multi           = models.BooleanField(default=True,blank=True,verbose_name="check if a user can specify multiple property values.")
    nullable        = models.BooleanField(default=True,blank=True,verbose_name="check if a user can specify an explicit \"NONE\" value.")


    show_extra_attributes           = models.BooleanField(default=True,blank=True,verbose_name="check if extra property attributes should be displayed.")
    show_extra_attributes.help_text = "Check if the 'standard_name', 'long_name', 'description', and 'units' should be displayed along with the value of this property."
    edit_extra_attributes           = models.BooleanField(default=False,blank=True,verbose_name="check if a user can edit the extra property attributes.")

    standard_name   = models.CharField(max_length=64,blank=True,null=True)
    long_name       = models.CharField(max_length=64,blank=True,null=True)
    description     = models.TextField(max_length=64,blank=True,null=True)

    value          = EnumerationField(blank=True,null=True,verbose_name="choose the property values that should be presented to the user:")
    value_default  = EnumerationField(blank=True,null=True,verbose_name="choose the default value(s), if any, for this property:")
    value_choices  = models.TextField(blank=True,null=True)
    value_format    = models.CharField(max_length=LIL_STRING,blank=True,null=True,choices=SCIENTIFIC_PROPERTY_FORMAT,verbose_name="what is the format (ie: \"string\" or \"char\") for this property value?")
    value_units     = models.CharField(max_length=LIL_STRING,blank=True,null=True)

    def save(self,*args,**kwargs):
        super(MetadataScientificPropertyCustomizer,self).save(*args,**kwargs)

    def reset(self,new_proxy):

        values = new_proxy.values.all()
        self.proxy     = new_proxy

        self.name           = new_proxy.name
        self.type           = new_proxy.type

        self.category       = new_proxy.category
        self.order          = new_proxy.id

        self.required       = new_proxy.required
        self.editable       = new_proxy.editable
        self.unique         = new_proxy.unique
        self.verbose_name   = new_proxy.verbose_name or new_proxy.name
        self.default_value  = new_proxy.default_value
        self.documentation  = new_proxy.documentation

        self.component_name = new_proxy.component_name
        self.vocabulary     = new_proxy.vocabulary

        self.choice          = new_proxy.choice
        self.open            = False
        self.multi           = (new_proxy.choice == "OR")
        self.nullable        = False

        self.value_choices   = "|".join([str(value.name) for value in values]),
        self.value_format    = values[0].format,  # these will be the same for each value, so just take the 1st one
        self.value_units     = values[0].units,   # these will be the same for each value, so just take the 1st one

        self.standard_name   = new_proxy.standard_name
        self.long_name       = new_proxy.long_name
        self.description     = new_proxy.description

        self.show_extra_attributes = True
        self.edit_extra_attributes = False
        
    @classmethod
    def getDataFromProxy(cls,proxy):
        values = proxy.values.all()
        data = {
            "name"           : proxy.name,
            "type"           : proxy.type,

            "category"       : proxy.category,
            "order"          : proxy.id,

            "required"       : proxy.required,
            "editable"       : proxy.editable,
            "unique"         : proxy.unique,
            "verbose_name"   : proxy.verbose_name or proxy.name,
            "default_value"  : proxy.default_value,
            "documentation"  : proxy.documentation,

            "component_name" : proxy.component_name,
            "vocabulary"     : proxy.vocabulary,

            "choice"         : proxy.choice,
            "open"           : False,
            "multi"          : (proxy.choice == "OR"),
            "nullable"       : False,

            "value_choices"  : "|".join([value.name for value in values]),
            "value_format"   : values[0].format,  # these will be the same for each value, so just take the 1st one
            "value_units"    : values[0].units,   # these will be the same for each value, so just take the 1st one
        }
        return data

