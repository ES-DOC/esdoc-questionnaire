
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
__date__ ="Feb 1, 2013 4:13:49 PM"

"""
.. module:: fields

Summary of module goes here

"""

import django.forms.models
import django.forms.widgets
import django.forms.fields

from django.contrib.contenttypes.models import ContentType

from dcf.utils import *

def update_field_widget_attributes(field,widget_attributes):
    """
    rather than overriding an attribute, this fn appends it to any existing ones
    as with class='old_class new_class'
    """
    for (key,value) in widget_attributes.iteritems():
        try:
            current_attributes = field.widget.attrs[key]
            field.widget.attrs[key] = "%s %s" % (current_attributes,value)
        except KeyError:
            field.widget.attrs[key] = value


class MetadataField(models.Field):
    """
    the base class for all metadata fields (attributes)
    """
    class Meta:
        abstract = True

    _name = ""
    _type = ""

    def getName(self):
        return self._name

    def getType(self):
        return self._type

    def contribute_to_class(self,cls,name):
        self._name = name
        super(MetadataField,self).contribute_to_class(cls,name)

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
    def Factory(cls,model_field_class_name,**kwargs):
        model_field_class_info = MODELFIELD_MAP[model_field_class_name.lower()]
        model_field_class = model_field_class_info[0]
        model_field_class_kwargs = model_field_class_info[1]

# in theory, I could also have created a new metaclass to achieve multiple inheritance
# but in practise, these two field types are just too dissimilar for that
#       class _MetadataAtomicFieldMetaClass(MetadataField.Meta,modelFieldClass.Meta):
#           pass

        class _MetadataAtomicField(cls,model_field_class):
            def __init__(self,*args,**kwargs):
                # set of kwargs passed to constructor
                # should be default set plus any overrides
                for (key,value) in model_field_class_kwargs.iteritems():
                    if not key in kwargs:
                        kwargs[key] = value
                super(_MetadataAtomicField,self).__init__(**kwargs)
                self._type = model_field_class_name
                
        return _MetadataAtomicField(**kwargs)

class MetadataRelationshipField(MetadataField):
    class Meta:
        abstract = True

    _sourceModelName    = None
    _sourceAppName      = None
    _targetModelName    = None
    _targetAppName      = None

    def __init__(self,*args,**kwargs):
        # explicitly call super on this base class
        # so that the next item in inheritance calls its initializer
        super(MetadataRelationshipField,super).__init__(*args,**kwargs)

    # do some post-initialization
    def initRelationship(self,*args,**kwargs):
        self.null = True                            # null values have to be allowed in order to initialize subForms w/ potentially brand-new (empty) models
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

    def contribute_to_class(self,cls, name):
        preferred_related_name = self._sourceAppName + "." + self._sourceModelName + "." + name.lower()
        if self.related_query_name() != preferred_related_name:
            self.rel.related_name = preferred_related_name
        super(MetadataManyToManyField, self).contribute_to_class(cls, name)

    def __init__(self,*args,**kwargs):
        targetModel = kwargs.pop("targetModel",None)
        sourceModel = kwargs.pop("sourceModel",None)
        if not (targetModel and sourceModel):
            if not (("." in targetModel) and ("." in sourceModel)):
                # have to fully specify (ie: include application) source & target
                msg = "invalid arguments to MetadataRelationshipField"
                raise MetadataError(msg)

        # I need to set the related_name to something unique
        # (since multiple CIM versions may have models w/ the same names and structures)
        # the related_name I'm using is "sourceApp.sourceModel.fieldName"
        # but at this point, I don't know the fieldName
        # so I set a temporary related_name, and then finish the job in contribute_to_class above
        kwargs["related_name"] = sourceModel
        super(MetadataManyToManyField,self).__init__(targetModel,**kwargs)
        self.initRelationship(sourceModel=sourceModel,targetModel=targetModel,**kwargs)
        self._type = self._type.lower() # makes comparisons easier later

class MetadataManyToOneField(models.ForeignKey,MetadataRelationshipField):
    _type = "ManyToOneField"

    def contribute_to_class(self,cls, name):
        preferred_related_name = self._sourceAppName + "." + self._sourceModelName + "." + name.lower()
        if self.related_query_name() != preferred_related_name:
            self.rel.related_name = preferred_related_name
        super(MetadataManyToOneField, self).contribute_to_class(cls, name)

    def __init__(self,*args,**kwargs):
        targetModel = kwargs.pop("targetModel",None)
        sourceModel = kwargs.pop("sourceModel",None)
        if not (targetModel and sourceModel):
            if not (("." in targetModel) and ("." in sourceModel)):
                # have to fully specify (ie: include application) source & target
                msg = "invalid arguments to MetadataRelationshipField"
                raise MetadataError(msg)

        # I need to set the related_name to something unique
        # (since multiple CIM versions may have models w/ the same names and structures)
        # the related_name I'm using is "sourceApp.sourceModel.fieldName"
        # but at this point, I don't know the fieldName
        # so I set a temporary related_name, and then finish the job in contribute_to_class above
        kwargs["related_name"] = sourceModel
        super(MetadataManyToOneField,self).__init__(targetModel,**kwargs)
        self.initRelationship(sourceModel=sourceModel,targetModel=targetModel,**kwargs)
        self._type = self._type.lower() # makes comparisons easier later
