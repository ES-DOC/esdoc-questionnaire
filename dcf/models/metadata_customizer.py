
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
__date__ ="Jan 31, 2013 11:26:35 AM"

"""
.. module:: metadata_customizer

Summary of module goes here

"""

from django.db import models
from django.db.models.fields import NOT_PROVIDED
from django.utils.functional import lazy

from django.contrib.contenttypes.models import *
from django.contrib.contenttypes import generic



from dcf.utils import *
from dcf.fields import *
from dcf.models import MetadataCategorization#, MetadataAttributeCategory, MetadataPropertyCategory

class MetadataCustomizer(models.Model):
    class Meta:
        app_label = APP_LABEL
        abstract = True

    # every object involved in customization references a particular project/version/model combination
    # (having version & model may seem like overkill - since models belong to a particular version
    # but I don't know in advance what type of model this will reference,
    # so I would have to use a generic relationship.  this is complicated by the fact that
    # I want to link to the model class and not a model instance, so I would have to use ContentType as opposed to MetadataModel.
    # That is possible, however having done that Django does not allow filtering querysets with GenericForeignKeys.
    # Rather than hack my way through this, I'm just using the name of the model instead of a relationship to its actual class

    project = models.ForeignKey("MetadataProject",blank=False,editable=False)
    version = models.ForeignKey("MetadataVersion",blank=False,editable=False)
    model   = models.CharField(max_length=BIG_STRING,blank=False,editable=False)

    loaded = models.BooleanField(blank=False,editable=False,default=False)

    _guid = models.CharField(max_length=64,unique=True,editable=False,blank=False,default=lambda:str(uuid4()))

    def getGUID(self):
        return self._guid

    def isLoaded(self):
        return self.loaded

    def getField(self,fieldName):
        # return the actual field (not the db representation of the field)
        # this is useful for interaction w/ a webform
        try:
            return self._meta.get_field_by_name(fieldName)[0]
        except models.fields.FieldDoesNotExist:
            return None

    def getCommonCustomizers(self):
        """
        returns a list of customizers (either ModelCustomizers or AtrributeCustomzizers, or PropertyCustomizers)
        belonging to the same project/version/model combination
        """
        model_class = self.__class__
        return model_class.objects.filter(project=self.project,version=self.version,model=self.model)

class MetadataModelCustomizer(MetadataCustomizer):
    class Meta:
        app_label = APP_LABEL
        # TODO: REDO THIS W/ MYSQL (SEE http://stackoverflow.com/questions/6153552/mysql-error-1062-duplicate-entry-for-key-2)
        unique_together = ('project', 'version', 'model', 'name')
        
    name                = models.CharField(max_length=LIL_STRING,verbose_name="Customization Name",blank=False,validators=[validate_no_spaces])
    name.help_text      = "A unique name for this customization (ie: \"basic\" or \"advanced\")"
    description         = models.TextField(verbose_name="Customization Description",blank=True)
    description.help_text = "An explanation of how this customization is intended to be used.  This information is for informational purposes only."
    default             = models.BooleanField(verbose_name="Is Default Customization",blank=True,editable=True)
    default.help_text   = "Defines the default customization that is used by this project/model combination if no explicit customization is provided"

    model_title         = models.CharField(max_length=BIG_STRING,verbose_name="Name that should appear on the Document Form",blank=False)
    model_description   = models.TextField(verbose_name="A description of the document",blank=True)
    model_show_all_categories = models.BooleanField(verbose_name="Display empty categories",default=False)
    model_show_all_categories.help_text = "Include categories in the editing form for which there are no attributes associated with"
    model_show_all_attributes = models.BooleanField(verbose_name="Display uncategorized fields",default=True)
    model_show_all_attributes.help_text = "Include attributes in the editing form that have no associated category.  These will show up below any category tabs."
    model_nested        = models.BooleanField(verbose_name="Include the full component hierarchy",default=True)
    model_nested.help_text ="Some CIM SoftwareComponents are comprised of a hierarchy of nested child components.  Checking this option allows that full hiearchy to be edited at once in the CIM Editor."


# BIG CHANGE
# CANNOT DEAL W/ M2M BEFORE SAVING
# SO REVERSING THIS; NOW ATTRIBUTES/PROPERTIES HAVE FOREIGN KEYS TO MODELS
#    attributes          = models.ManyToManyField("MetadataAttributeCustomizer",blank=True,null=True)
    properties          = models.ManyToManyField("MetadataPropertyCustomizer",blank=True,null=True)
    temporary_attributes = []
    temporary_properties = []

   
    def __unicode__(self):
        return u'%s' % self.name

    def getProject(self):
        return self.project

    def getVersion(self):
        return self.version

    def getModel(self):
        """
        .. note: this returns a class not an instance
        """
        version = self.getVersion()
        return version.getModel(self.model)
        
    def getCategorization(self):
        return self.version.default_categorization

    def getCategorizations(self):
        default_categorization = self.getCategorization()
        if default_categorization:
            return MetadataCategorization.objects.filter(id=default_categorization.id)
        else:
            return MetadataCategorization.objects.none()

    def getVocabulary(self):
        return self.project.default_vocabulary

    def getVocabularies(self):
        return self.project.vocabularies.all()

 
    def __init__(self,*args,**kwargs):
        super(MetadataCustomizer,self).__init__(*args,**kwargs)
        _model = self.getModel()

        # only one customizer can be the default one...
        otherCustomizers = self.getCommonCustomizers().exclude(name=self.name)
        if otherCustomizers.count() == 0:
            # therefore, if this is the only customizer, it must be the default one...
            self.default = True

        if not self.isLoaded():
            self.loadCustomizer()
            self.loaded = True


    def reset(self,*args):
        _model = args[0]
        self.model_title = _model.getTitle()
        self.model_description = _model.getDescription()

    def loadCustomizer(self):
        _model = self.getModel()

        self.reset(_model)

        self.temporary_attributes = []
        new_attributes = _model.getAttributes()
        for i,attribute in enumerate(new_attributes):
            temporary_attribute = MetadataAttributeCustomizer(
                attribute_name  = attribute.getName(),
                attribute_type  = attribute.getType(),
                project         = self.project,
                version         = self.version,
                model           = self.model,
                order           = (i+1))
            temporary_attribute.reset(attribute)
            self.temporary_attributes.append(temporary_attribute)
            

      
        new_properties = self.getVocabulary().getProperties()
        # limit the properties to those associated with _this_ model
        for i,property in enumerate(new_properties.filter(model_name__iexact=_model.getName())):
            (new_property, created) = MetadataPropertyCustomizer.objects.get_or_create(
                                        property    = property,
                                        project     = self.project,
                                        version     = self.version,
                                        model       = self.model,
                                        parentGUID  = self.getGUID())
            if created:
                new_property.order=(i+1)
                new_property.reset(property)


        # I CANNOT ADD TO A M2M FIELD BEFORE ITS'S BEEN SAVED
        # AND SAVING IS EXPENSIVE, SO I DON'T DO ANYTHING HERE
        # INSTEAD I INITIALIZE THE CORRESPONDING FIELDS IN THE CORRESPONDING FORM
        # CONFIDENT THAT THE ATTRIBUTES & PROPERTIES HAVE ALREADY BEEN CREATED ABOVE

    


    def save(self, *args, **kwargs):
        super(MetadataModelCustomizer, self).save(*args, **kwargs)        

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

###        # now save the attributes/properties setup in init
###        if len(self.temporary_attributes):
###            for temporary_attribute in self.temporary_attributes:
###                temporary_attribute.parent = self
###                temporary_attribute.save()
###            self.temporary_attributes = []

    def recursivelyUpdateFields(self,new_fields):
        """
        changes the value of new_fields[name] with the specified value
        then checks all the subform_customizers of child attributes and does the same
        """
        for (field_name,field_value) in new_fields.iteritems():
            setattr(self,field_name,field_value)


        for attribute_customizer in self.attributes.all():
            if attribute_customizer.subform_customizer:
                attribute_customizer.subform_customizer.recursivelyUpateFields(new_fields)
        self.save(force_update=True)

class MetadataAttributeCustomizer(MetadataCustomizer):
    class Meta:
        app_label = APP_LABEL

    #parentGUID        = models.CharField(max_length=64,blank=False,editable=False)
    parent             = models.ForeignKey("MetadataModelCustomizer",blank=True,null=True,related_name="attributes")
    attribute_name     = models.CharField(max_length=LIL_STRING,blank=False)
    attribute_type     = models.CharField(max_length=LIL_STRING,blank=False)
    category           = models.ForeignKey("MetadataAttributeCategory",blank=True,null=True)
    order              = models.PositiveIntegerField(blank=True,null=True)

    # ways to customize _any_ field...
    displayed           = models.BooleanField(default=True,blank=True,verbose_name="should this property be displayed?")
    required            = models.BooleanField(default=False,blank=True,verbose_name="is this property required?")
    editable            = models.BooleanField(default=False,blank=True,verbose_name="can the value of this property be edited?")
    unique              = models.BooleanField(default=False,blank=True,verbose_name="must the value of this property be unique?")
    verbose_name        = models.CharField(max_length=64,blank=False,verbose_name="how should this property be labeled (overrides default name)?")
    default_value       = models.CharField(max_length=128,blank=True,null=True,verbose_name="what is the default value of this property?")
    documentation       = models.TextField(blank=True,verbose_name="what is the help text to associate with property?")

    # ways to customize enumeration fields...
    enumerations         = EnumerationField(blank=False,verbose_name="choose the property values that should be presented to the user:")
    default_enumerations = EnumerationField(blank=True,verbose_name="choose the default value(s), if any, for this property:")
    enumeration_choices  = models.TextField(blank=True,max_length=HUGE_STRING) # (made a textfield b/c kept running into max_length limit for big enumerations)
    open                 = models.BooleanField(default=False,blank=True,verbose_name="check if a user can specify a custom property value.")
    multi                = models.BooleanField(default=False,blank=True,verbose_name="check if a user can specify multiple property values.")
    nullable             = models.BooleanField(default=False,blank=True,verbose_name="check if a user can specify an explicit \"NONE\" value.")

    # ways to customize relationship fields...
    cardinality                 = CardinalityField(blank=False,verbose_name="how many instances (min/max) of this property are desired?")
    customize_subform           = models.BooleanField(default=False,blank=True,verbose_name="should this property be rendered in its own subform?")
    customize_subform.help_text = "Checking this radio button will cause the property to be rendered as a nested subform within the <i>parent</i> form; All properties of this model will be available to view and edit in that subform.\
                                   Unchecking it will cause the attribute to be rendered as a simple select widget."
    subform_customizer  = models.ForeignKey("MetadataModelCustomizer",blank=True,null=True,related_name="subform_customizer")

    def __unicode__(self):
        return u'%s::%s' % (self.parent.name if self.parent else "unspecified", self.attribute_name)
    
    def reset(self,*args,**kwargs):
        attribute = args[0]
        force_save = kwargs.pop("force_save",False)        

        model_name = self.model.lower()
        categorization = self.version.default_categorization
        for category in categorization.getCategories():
            category_mapping = category.getMapping()
            try:
                if self.attribute_name.lower() in [attribute_name.lower() for attribute_name in category_mapping[model_name]]:                    
                    self.category = category                 
            except KeyError:
                pass
        
        self.required = (attribute.blank == False)
        self.editable = attribute.editable
        self.unique = attribute.unique
        self.verbose_name = attribute.verbose_name
        self.documentation = attribute.help_text
        self.default_value = attribute.default if (attribute.default != NOT_PROVIDED) else None

        self.attribute_type = attribute.getType()

        if self.isAtomicField():
            pass

        if self.isRelationshipField():
            self.customize_subform = False

        if self.isEnumerationField():
            enum          = attribute.getEnumerationClass()            
            self.open     = enum.isOpen
            self.multi    = enum.isMulti
            self.nullable = enum.isNullable
            self.enumeration_choices = "|".join(enum.getChoices())

            if self.attribute_name == "role":
                print "FLARB"
                print "enum=%s"%enum
                print "choices=%s"%self.enumeration_choices

        if force_save:
            self.save()

    def save(self,*args,**kwargs):
        # just make sure that the parent exists before saving
        # (parent ought to be set by virtue of this model being exposed in an inlineformset)
        # (but the associated project & version may not have been set yet)
        if self.parent and (not (hasattr(self,"project") or hasattr(self,"version"))):
            print "need to fix things"
            self.setParent(self.parent)
        return super(MetadataAttributeCustomizer,self).save(*args,**kwargs)

    def setParent(self,model_customizer):
        self.parent = model_customizer
        self.project = model_customizer.project
        self.version = model_customizer.version

    def isAtomicField(self):
        return self.attribute_type.lower() in MODELFIELD_MAP.iterkeys()

    def isRelationshipField(self):
        return self.attribute_type.lower() in [field._type.lower() for field in MetadataRelationshipField.__subclasses__()]

    def isEnumerationField(self):
        return self.attribute_type.lower() in [field._type.lower() for field in MetadataEnumerationField.__subclasses__()] + [MetadataEnumerationField._type.lower()]

    def getName(self):
        return self.attribute_name

    def getType(self):
        return self.attribute_type

    def getCategory(self):
        return self.category

class MetadataPropertyCustomizer(MetadataCustomizer):
    class Meta:
        app_label = APP_LABEL


    parentGUID  = models.CharField(max_length=64,blank=False,editable=False)
    property    = models.ForeignKey("MetadataProperty",blank=False)
    category    = models.ForeignKey("MetadataPropertyCategory",blank=True,null=True)
    order       = models.PositiveIntegerField(blank=True,null=True)

    # TODO: ADD MORE WAYS OF CUSTOMIZING ATTRIBUTES
    displayed       = models.BooleanField(default=True,blank=True,verbose_name="should property be displayed")
    required        = models.BooleanField(default=False,blank=True,verbose_name="is property required")
    editable        = models.BooleanField(default=False,blank=True,verbose_name="can property be edited")
    verbose_name    = models.CharField(max_length=64,blank=False,verbose_name="how should this property be labeled (overrides default name)")
    default_value   = models.CharField(max_length=128,blank=True,null=True,verbose_name="what is the default value of this property")
    documentation   = models.TextField(blank=True,verbose_name="help text to associate with property")
    open        = models.BooleanField(default=False,blank=True,verbose_name="can a user specify their own property value")
    multi       = models.BooleanField(default=False,blank=True,verbose_name="can a user specify more than one property value")
    nullable    = models.BooleanField(default=False,blank=True,verbose_name="do you want to provide an explicit \"none\" value")

    def reset(self,*args):

        property = args[0]

        self.displayed = True
        self.required = True
        self.editable = True
        self.verbose_name = property.long_name
        self.default_value = None
        self.documentation = ""
        self.open = property.open
        self.multi = property.multi
        self.nullable = property.nullable

        # reset forces a save
        self.save()

    def getName(self):
        return self.property.short_name

    def getCategory(self):
        return self.category

    def getValues(self):
        return self.property.getValues()