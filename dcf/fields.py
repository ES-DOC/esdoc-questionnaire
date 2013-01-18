from django.db import models
from django import forms

import django.forms.models
import django.forms.widgets
import django.forms.fields

from django.contrib.contenttypes.models import ContentType

from dcf.helpers import *

def updateFieldWidgetAttributes(field,widgetAttributes):
    for (key,value) in widgetAttributes.iteritems():
        try:
            currentAttrs = field.widget.attrs[key]
            field.widget.attrs[key] = "%s %s" % (currentAttrs,value)
        except KeyError:
            field.widget.attrs[key] = value

####################################################
# the types of fields that a model can have.       #
# these are rendered as tabs in the template,      #
# with each tab displaying all fields of that type #
# they function a bit like tags,                   #
# but each field can only have one type            #
####################################################

#class FieldType(EnumeratedType):
#    pass



################################
# the base class of all fields #
################################

class MetadataField(models.Field):
    class Meta:
        abstract = True

    _type = ""

    def getName(self):
        return self.name

    def getType(self):
        return self._type.strip()

    def init(self,*args,**kwargs):
        super(MetadataField,self).__init__(*args,**kwargs)

        self._name = self.name

    def customize(self,customField):
        # record all of the values so I can access them later from templatetags if needed...
        self.custom_order = customField.order
        self.custom_category = customField.category
        self.custom_displayed = customField.displayed
        self.custom_required = customField.required
        self.custom_editable = customField.editable
        self.custom_unique = customField.unique
        self.custom_verbose_name = customField.verbose_name
        self.custom_default_value = customField.default_value
        self.custom_documentation = customField.documentation
        self.custom_replace = customField.replace


    def get_custom_help_text(self):
        if self.custom_documentation != self.help_text:
            return self.custom_documentation
        else:
            return self.help_text

    def get_custom_verbose_name(self):
        try:
            current_verbose_name = self.verbose_name
        except AttributeError:
            current_verbose_name = pretty_string(field.label)
        if self.custom_verbose_name != current_verbose_name:
            return self.custom_verbose_name
        else:
            return current_verbose_name

    def get_custom_category(self):
        return self.custom_category

    def get_custom_required(self):
        return self.custom_required

    def get_custom_default_value(self):
        return self.custom_default_value
    
    def is_custom_visible(self):
        return self.custom_displayed
    
    def is_custom_subform(self):
        return self.custom_replace

#############################################################
# the set of customizable atomic fields for metadata models #
# each item consists of a name, a corresponding class,      #
# and a set of default kwargs required for that class.      #
#############################################################

MODELFIELD_MAP = {
    "booleanfield"          : [models.BooleanField, {}],
    "charfield"             : [models.CharField, { "max_length" : BIG_STRING}],
    "datefield"             : [models.DateField, {}],
    "datetimefield"         : [models.DateTimeField, {}],
    "decimalfield"          : [models.DecimalField, { "null" : True}],
    "emailfield"            : [models.EmailField, {}],
    "integerfield"          : [models.IntegerField, { "null" : True}],
    "nullbooleanfield"      : [models.NullBooleanField, {}],
    "positiveintegerfield"  : [models.PositiveIntegerField, {}],
    "textfield"             : [models.TextField, {}],
    "timefield"             : [models.TimeField, {}],
    "urlfield"              : [models.URLField, { "verify_exists" : False}],
}

class MetadataAtomicField(MetadataField):

    def __init__(self,*args,**kwargs):
        super(MetadataAtomicField,self).__init__(**kwargs)


    @classmethod
    def Factory(cls,modelFieldClassName,**kwargs):
        modelFieldClassInfo = MODELFIELD_MAP[modelFieldClassName.lower()]
        modelFieldClass = modelFieldClassInfo[0]
        modelFieldKwargs = modelFieldClassInfo[1]

# in theory, I could also have created a new metaclass to achieve multiple inheritance
# but in practise, these two field types are just too dissimilar for that
#       class _MetadataAtomicFieldMetaClass(MetadataField.Meta,modelFieldClass.Meta):
#           pass

        class _MetadataAtomicField(cls,modelFieldClass):
            def __init__(self,*args,**kwargs):
                # set of kwargs passed to constructor
                # should be default set plus any overrides
                for (key,value) in modelFieldKwargs.iteritems():
                    if not key in kwargs:
                        kwargs[key] = value
                super(_MetadataAtomicField,self).__init__(**kwargs)
                self._type = modelFieldClassName


        return _MetadataAtomicField(**kwargs)

class MetadataRelationshipField(MetadataField):
    class Meta:
        abstract = True

    _sourceModelName    = None
    _sourceAppName      = None
    _targetModelName    = None
    _targetAppName      = None

    # do some post-initialization
    def initRelationship(self,*args,**kwargs):
        self.related_name = self.name   # related_name has to be unique to distinguish between different relationshipFields from the same model to the same model
        self.null = True                # null values have to be allowed in order to initialize subForms w/ potentially brand-new (empty) models

        self.help_text = kwargs.pop("help_text","") # if I don't explicitly set the help_text, then prevent Django from adding the standard m2m documentation
        targetModel = kwargs.pop("targetModel",None)
        sourceModel = kwargs.pop("sourceModel",None)

        if sourceModel:
            sourceAppAndModel = sourceModel.split(".")
            self._sourceModelName = sourceAppAndModel[1].lower()
            self._sourceAppName = sourceAppAndModel[0].lower()
        if targetModel:
            targetAppAndModel = targetModel.split(".")
            self._targetModelName = targetAppAndModel[1].lower()
            self._targetAppName = targetAppAndModel[0].lower()

    def getTargetModelClass(self):
        try:
            ModelType = ContentType.objects.get(app_label=self._targetAppName,model=self._targetModelName)
            ModelClass = ModelType.model_class()
            return ModelClass
        except django.contrib.contenttypes.models.ContentType.DoesNotExist:
            # handles the case where model is accessed before target is loaded (during syncdb, for instance)
            return None

    def getSourceModelClass(self):
        try:
            ModelType = ContentType.objects.get(app_label=self._sourceAppName,model=self._sourceModelName)
            ModelClass = ModelType.model_class()
            return ModelClass
        except django.contrib.contenttypes.models.ContentType.DoesNotExist:
            # handles the case where model is accessed before target is loaded (during syncdb, for instance)
            return None

class MetadataManyToManyField(models.ManyToManyField,MetadataRelationshipField):
    _type = "ManyToManyField"
    pass


    def __init__(self,*args,**kwargs):
        targetModel = kwargs.pop("targetModel",None)
        sourceModel = kwargs.pop("sourceModel",None)
        super(MetadataManyToManyField,self).__init__(targetModel,**kwargs)
        self.initRelationship(sourceModel=sourceModel,targetModel=targetModel,**kwargs)
        self._type = self._type.lower() # makes comparisons easier later

