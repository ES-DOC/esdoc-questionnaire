
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

from django.forms import *

import django.forms.models
import django.forms.widgets
import django.forms.fields

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from django.db.models import get_app, get_models

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

def update_widget_attributes(widget,widget_attributes):
    """
    as above, but operates on a widget instead of a formfield
    (this is useful when dealing w/ multivaluefields)
    """
    for (key,value) in widget_attributes.iteritems():
        try:
            current_attributes = widget.attrs[key]
            widget.attrs[key] = "%s %s" % (current_attributes,value)
        except KeyError:
            widget.attrs[key] = value

class CardinalityFormFieldWidget(django.forms.widgets.MultiWidget):
    def __init__(self,*args,**kwargs):
        widgets = (
            django.forms.fields.Select(choices=[(str(i),str(i)) for i in range(0,11)]),
            django.forms.fields.Select(choices=[('*','*')]+[(str(i),str(i)) for i in range(0,11)][1:]),
        )
        super(CardinalityFormFieldWidget,self).__init__(widgets,*args,**kwargs)

    def decompress(self,value):
        if value:
            return value.split("|")
        else:
            return [u'',u'']
        
class CardinalityFormField(django.forms.fields.MultiValueField):

  def __init__(self,*args,**kwargs):
      #verbose_name = kwargs.pop("verbose_name")
      #blank = kwargs.pop("blank")
      fields = (
          django.forms.fields.CharField(max_length=2),
          django.forms.fields.CharField(max_length=2)
      )
      widget = CardinalityFormFieldWidget()
      super(CardinalityFormField,self).__init__(fields,widget,*args,**kwargs)
      self.widget = widget

  def compress(self, data_list):
      return "|".join(data_list)

  def clean(self,value):
      min = value[0]
      max = value[1]

      if (min > max) and (max != "*"):
          msg = "min must be less than or equal to max"
          raise ValidationError(msg)

      return "|".join(value)


class CardinalityField(models.CharField):

    def formfield(self,**kwargs):
        return CardinalityFormField(label=self.verbose_name.capitalize())

    def __init__(self,*args,**kwargs):
        kwargs["max_length"] = 8
        
        super(CardinalityField,self).__init__(*args,**kwargs)

class EnumerationFormField(django.forms.fields.MultipleChoiceField):

    def __init__(self,*args,**kwargs):
        kwargs.pop("max_length",None)
        super(EnumerationFormField,self).__init__(**kwargs)

    def get_choices_from_widget(self):
        return self.widget.choices

    def clean(self,value):
        # an enumeration can be invalid in 2 ways:
        # 1) not specifying a value when field is required
        # 2) specifying a value other than that provided by choices
        if not value and self.required:
            raise ValidationError(self.error_messages['required'])
        if not set(value).issubset(set([choice[0] for choice in self.get_choices_from_widget()])):
            msg = "Select a valid choice.  %s is not among the available choices" % value
            raise ValidationError(msg)
        return value
        #return super(EnumerationFormField,self).clean(value)


class EnumerationField(models.TextField):

    _choices = None

    def formfield(self,**kwargs):
        new_kwargs = {
            "label"       : self.verbose_name.capitalize(),
            "form_class"  : EnumerationFormField,
            "required"    : not self.blank,
            # TODO: THIS FN GETS CALLED TWICE
            # IT SEEMS LIKE ONLY THE 1st TIME (BEFORE setChoices() HAS BEEN CALLED)
            # "STICKS"; NOT SURE WHY
            # HENCE, THE ADDITIONAL CUSTOMIZATION OF THE WIDGET IN forms_customize.py
            "choices"     : self.getChoices(),
            "initial"     : [choice[0] for choice in self.getChoices()],
        }
        new_kwargs.update(kwargs)
        return super(EnumerationField,self).formfield(**new_kwargs)

    def __init__(self,*args,**kwargs):
        #kwargs["max_length"] = kwargs.get("max_length",None) or HUGE_STRING
        super(EnumerationField,self).__init__(*args,**kwargs)

    #def get_db_prep_value(self, value):
    def get_db_prep_value(self, value, connection, prepared=False):
        if isinstance(value, basestring):
            return value
        elif isinstance(value, list):
            return "|".join(value)

    def to_python(self, value):
        if isinstance(value, list):
            return value
        else:
            return value.split("|")

    def validate(self,value,model_instance):
        # I already validated against the formfield
        # no need to do anything here
        return

    def setChoices(self,choices):
        self._choices = choices

    def getChoices(self):
        return self._choices


###
###
###

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

    def isAtomicField(self):
        return self._type.lower() in MODELFIELD_MAP.iterkeys()

    def isRelationshipField(self):
        return self._type.lower() in [field._type.lower() for field in MetadataRelationshipField.__subclasses__()]

    def isEnumerationField(self):
        return self._type.lower() in [field._type.lower() for field in MetadataEnumerationField.__subclasses__()] + [MetadataEnumerationField._type.lower()]

# these next three fns are used in the case where a form is unbound;
# in that case there is no "self" to use in the above fns

def is_atomic_field(field_type):
    return field_type.lower() in MODELFIELD_MAP.iterkeys()

def is_relationship_field(field_type):
    return field_type.lower() in [field._type.lower() for field in MetadataRelationshipField.__subclasses__()]

def is_enumeration_field(field_type):
    valid_types = [field._type.lower() for field in MetadataEnumerationField.__subclasses__()] + [MetadataEnumerationField._type.lower()]
    return field_type.lower() in valid_types

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
    "decimalfield"          : [models.DecimalField, { "null" : True, "max_digits" : 10, "decimal_places" : 5 }],
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
###        #preferred_related_name = self._sourceAppName + "." + self._sourceModelName + "." + name.lower()
        preferred_related_name = name.lower() + "." + self._sourceAppName + "." + self._sourceModelName + "." + self._targetAppName + "." + self._targetModelName
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
        # TODO
###        kwargs["related_name"] = sourceModel
#        kwargs["related_name"] = "+"
        kwargs["related_name"] = str(uuid4())
        super(MetadataManyToManyField,self).__init__(targetModel,**kwargs)
        self.initRelationship(sourceModel=sourceModel,targetModel=targetModel,**kwargs)
        self._type = self._type.lower() # makes comparisons easier later


class MetadataManyToOneField(models.ForeignKey,MetadataRelationshipField):
    _type = "ManyToOneField"

    def contribute_to_class(self,cls, name):
        ## TODO: I CAN'T GET THIS TO WORK, SO FOR NOW I'M SETTING related_name TO '+' IN THE CONSTRUCTOR
###        #preferred_related_name = self._sourceAppName + "." + self._sourceModelName + "." + name.lower()
        preferred_related_name = name.lower() + "." + self._sourceAppName + "." + self._sourceModelName + "." + self._targetAppName + "." + self._targetModelName

        if self.related_query_name() != preferred_related_name:
            self.rel.related_name = preferred_related_name
        super(MetadataManyToOneField, self).contribute_to_class(cls, name)

    def __init__(self,*args,**kwargs):
        abstract    = kwargs.pop("abstract",False)
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
## TODO
###        kwargs["related_name"] = sourceModel
#        kwargs["related_name"] = "+"
        kwargs["related_name"] = str(uuid4())
        super(MetadataManyToOneField,self).__init__(targetModel,**kwargs)
        self.initRelationship(sourceModel=sourceModel,targetModel=targetModel,**kwargs)
        self._type = self._type.lower() # makes comparisons easier later

class MetadataEnumerationFormFieldWidget(django.forms.widgets.MultiWidget):
    
    def __init__(self,*args,**kwargs):
        widgets = (
            # these will be replaced by the form's __init__ method
            # but I need to put something in the tuple so I can change it later
            django.forms.fields.TextInput(),
            django.forms.fields.TextInput()
        )
        super(MetadataEnumerationFormFieldWidget,self).__init__(widgets,*args,**kwargs)

    def decompress(self,value):
        if value:
            return value.split("|")
        else:
            return [u'',u'']
        
class MetadataEnumerationFormField(django.forms.fields.MultiValueField):

    def __init__(self,*args,**kwargs):
        fields = (
            django.forms.fields.CharField(),
            django.forms.fields.CharField(required=False)
        )
        widget = MetadataEnumerationFormFieldWidget()
        super(MetadataEnumerationFormField,self).__init__(fields,widget,*args,**kwargs)
        self.widget = widget

class MetadataEnumerationField(models.CharField,MetadataField):
    _type = "EnumerationField"

    open        = False
    multi       = False
    nullable    = False

    def __init__(self,*args,**kwargs):
        enumeration = kwargs.pop('enumeration',None)
        kwargs["max_length"] = HUGE_STRING
        super(MetadataEnumerationField,self).__init__(*args,**kwargs)

        if enumeration:
            enumerationAppAndModel = enumeration.split(".")
            self._enumerationModelName = enumerationAppAndModel[1].lower()
            self._enumerationAppName = enumerationAppAndModel[0].lower()

    def formfield(self,**kwargs):
        return MetadataEnumerationFormField()

    def getEnumerationClass(self):
            
        try:
            ModelType = ContentType.objects.get(app_label=self._enumerationAppName,model=self._enumerationModelName)
            return ModelType.model_class()
        except:
            print "ERROR: failed to get enumerationclass: %s" % ".".join(self._enumerationAppName,self._enumerationModelName)
            return None



## ACTUALLY, THESE CAN BE OVERRIDDEN BY THE CUSTOMIZER

    def isOpen(self):
        return self.open

    def isMulti(self):
        return self.multi

    def isNullable(self):
        return self.nullable

class MetadataTestField(models.ForeignKey):

    def isAbstract(self):
        return self.rel.to == ContentType

    def contribute_to_class(self,cls,name):

        super(MetadataTestField, self).contribute_to_class(cls, name)

        if self.isAbstract():
            # if this field is abstract, then I need to add some other fields to get GenericRelations working
            new_object_id_field = models.PositiveIntegerField()
            new_object_id_field.contribute_to_class(cls,name+"_object_id")
            new_content_object_field = generic.GenericForeignKey(name,name+"_object_id")
            new_content_object_field.contribute_to_class(cls,name+"content_object")


    def __init__(self,*args,**kwargs):
        abstract    = kwargs.pop("abstract",False)
        targetModel = kwargs.pop("targetModel",None)
        sourceModel = kwargs.pop("sourceModel",None)
        if not (targetModel and sourceModel):
            if not (("." in targetModel) and ("." in sourceModel)):
                # have to fully specify (ie: include application) source & target
                msg = "invalid arguments to MetadataRelationshipField"
                raise MetadataError(msg)


        if abstract:
            # can't get_subclasses of an abstract model (since it's not in ContentTypes)
            # so instead I'm looking through the superclasses of concrete models
            (targetAppName,targetModelName) = targetModel.split(".")
            child_classes = [model for model in get_models(get_app(targetAppName)) if has_superclass(model,targetModel)]
            targetModel = ContentType
            kwargs["limit_choices_to"] = { "model_in" : tuple([child_class._meta.object_name for child_class in child_classes]) }

        super(MetadataTestField,self).__init__(targetModel,**kwargs)
