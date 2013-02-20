
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

from dcf.utils import *
from dcf.fields import *
from dcf.models import MetadataCategorization

@guid()
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

    _loaded = False

    def isLoaded(self):
        return self._loaded

    def getField(self,fieldName):
        # return the actual field (not the db representation of the field)
        # this is useful for interaction w/ a webform
        try:
            return self._meta.get_field_by_name(fieldName)[0]
        except models.fields.FieldDoesNotExist:
            return None

    def getModel(self):
        """
        .. note: this returns a class not an instance
        """
        return self.version.getModel(self.model)

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
        unique_together = ('project', 'version', 'model', 'name')

    name                = models.CharField(max_length=LIL_STRING,verbose_name="Customization Name",blank=False,validators=[validate_no_spaces])
    name.help_text      = "A unique name for this customization (ie: \"basic\" or \"advanced\")"
    description         = models.TextField(verbose_name="Customization Description",blank=True)
    description.help_text = "An explanation of how this customization is intended to be used.  This information is for informational purposes only."
    default             = models.BooleanField(verbose_name="Is Default Customization",blank=True,editable=True)
    default.help_text   = "Defines the default customization that is used by this project/model combination if no explicit customization is provided"

    model_title         = models.CharField(max_length=BIG_STRING,verbose_name="Name that should appear on the Document Form",blank=False)
    model_description   = models.TextField(verbose_name="A description of the document",blank=True)

    attributes          = models.ManyToManyField("MetadataAttributeCustomizer",blank=True,null=True)
    properties          = models.ManyToManyField("MetadataPropertyCustomizer",blank=True,null=True)

    
    def __unicode__(self):
        return u'%s' % self.name
    
    # TODO: CURRENTLY CUSTOMIZERS HAVE:
    # 1. A SINGLE VERSION (BASED ON THE REQUEST)
    # 2. A SINGLE CATEGORIZATION (BASED ON THE VERSION)
    # 3. A SINGLE VOCABULARY (BASED ON THE DEFAULT_VOCABULARY OF THE PROJECT)
    # IN THE FUTURE, USERS SHOULD BE ABLE TO SPECIFY MULTIPLE VOCABULARIES OR A DIFFERENT CATEGORIZATION
    
    def getVersion(self):
        return self.version

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


    # TODO: DO SOMETHING CLEVER W/ REVERSE RELATIONSHIPS HERE
    # TO FIND ALL OF THE ATTRIBUTES/PROPERTIES THAT LINK TO _THIS_ MODEL/VERSION/PROJECT
    pass

    def __init__(self,*args,**kwargs):
        super(MetadataCustomizer,self).__init__(*args,**kwargs)
        _model = self.getModel()

        # only one customizer can be the default one...
        otherCustomizers = self.getCommonCustomizers().exclude(name=self.name)
        if otherCustomizers.count() == 0:
            # therefore, if this is the only customizer, it must be the default one...
            self.default = True

        if not self.isLoaded():
            self.reset(_model)
            self.loadCustomizer()
        
    def reset(self,*args):
        _model = args[0]
        self.model_title = _model.getTitle()
        self.model_description = _model.getDescription()

    def loadCustomizer(self):
        _model = self.getModel()

        self.reset(_model)
        
        new_attributes = _model.getAttributes()
        for i,attribute in enumerate(new_attributes):
            (new_attribute, created) = MetadataAttributeCustomizer.objects.get_or_create(
                                        attribute_name  = attribute.getName(),
                                        attribute_type  = attribute.getType(),
                                        project         = self.project,
                                        version         = self.version,
                                        model           = self.model,
                                        parentGUID      = self.getGUID())
            if created:
                new_attribute.order=(i+1)
                new_attribute.reset(attribute)


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

        self._loaded = True


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

class MetadataAttributeCustomizer(MetadataCustomizer):
    class Meta:
        app_label = APP_LABEL

    parentGUID      = models.CharField(max_length=64,blank=False,editable=False)
    attribute_name  = models.CharField(max_length=LIL_STRING,blank=False)
    attribute_type  = models.CharField(max_length=LIL_STRING,blank=False)
    category        = models.ForeignKey("MetadataAttributeCategory",blank=True,null=True)
    order           = models.PositiveIntegerField(blank=True,null=True)

    # TODO: ADD MORE WAYS OF CUSTOMIZING ATTRIBUTES
    displayed       = models.BooleanField(default=True,blank=True,verbose_name="should attribute be displayed")
    required        = models.BooleanField(default=False,blank=True,verbose_name="is attribute required")
    editable        = models.BooleanField(default=False,blank=True,verbose_name="can attribute be edited")
    unique          = models.BooleanField(default=False,blank=True,verbose_name="must attribute be unique")
    verbose_name    = models.CharField(max_length=64,blank=False,verbose_name="how should this attribute be labeled (overrides default name)")
    default_value   = models.CharField(max_length=128,blank=True,null=True,verbose_name="what is the default value of this attribute")
    documentation   = models.TextField(blank=True,verbose_name="help text to associate with attribute")
    replace         = models.BooleanField(default=False,blank=True,verbose_name="should this attribute be rendered as a subform (as opposed to a standard select widget)")

    
    def reset(self,*args):

        attribute = args[0]

        self.required = (attribute.blank == False)
        self.editable = attribute.editable
        self.unique = attribute.unique
        self.verbose_name = attribute.verbose_name
        self.documentation = attribute.help_text
        self.default_value = attribute.default if (attribute.default != NOT_PROVIDED) else None

        # reset forces a save
        self.save()

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