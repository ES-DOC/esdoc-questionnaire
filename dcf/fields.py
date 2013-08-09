
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
__date__ ="Jun 10, 2013 5:41:35 PM"

"""
.. module:: fields

Summary of module goes here

"""

import django.forms.models
import django.forms.fields
import django.forms.widgets

from django.db import models
from django.db.models import get_app, get_model, get_models

from south.modelsinspector import introspector, add_introspection_rules

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

class MetadataFieldType(EnumeratedType):
    pass

MetadataFieldTypes = EnumeratedTypeList([
    MetadataFieldType("ATOMIC","Atomic"),
    MetadataFieldType("RELATIONSHIP","Relationship"),
    MetadataFieldType("ENUMERATION","Enumeration"),
    MetadataFieldType("PROPERTY","Property"),
])

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
        return self._type.lower() in [MetadataEnumerationField._type.lower()]

    def south_field_triple(self):
        field_class_path = self.__class__.__module__ + "." + self.__class__.__name__
        args,kwargs = introspector(self)
        return (field_class_path,args,kwargs)

def isAtomicField(field_type):
    return field_type.lower() in MODELFIELD_MAP.iterkeys()

def isRelationshipField(field_type):
    return field_type.lower() in [field._type.lower() for field in MetadataRelationshipField.__subclasses__()]

def isEnumerationField(field_type):
    return field_type.lower() in [MetadataEnumerationField._type.lower()]

#############################################################
# the set of customizable atomic fields for metadata models #
# each item consists of a name, a corresponding class,      #
# and a set of default kwargs required for that class.      #
#############################################################

MODELFIELD_MAP = {
    "booleanfield"          : [models.BooleanField, {}],
    "charfield"             : [models.CharField, { "max_length" : BIG_STRING}],
    "datefield"             : [models.DateField, { "null" : True, }],
    "datetimefield"         : [models.DateTimeField, { "null" : True, }],
    "decimalfield"          : [models.DecimalField, { "null" : True, "max_digits" : 10, "decimal_places" : 5 }],
    "emailfield"            : [models.EmailField, {}],
    "integerfield"          : [models.IntegerField, { "null" : True}],
    "nullbooleanfield"      : [models.NullBooleanField, {}],
    "positiveintegerfield"  : [models.PositiveIntegerField, {}],
    "textfield"             : [models.TextField, { "null" : True }],
    "timefield"             : [models.TimeField, {}],
    "urlfield"              : [models.URLField, {}],# DEPRECATED IN DJANGO V1.5 { "verify_exists" : False}],
}

class MetadataAtomicField(MetadataField):

    def __init__(self,*args,**kwargs):
        super(MetadataAtomicField,self).__init__(**kwargs)

    @classmethod
    def Factory(cls,model_field_class_name,**kwargs):
        try:
            model_field_class_info = MODELFIELD_MAP[model_field_class_name.lower()]
            model_field_class = model_field_class_info[0]
            model_field_class_kwargs = model_field_class_info[1]
        except:
            msg = "unknown field type: '%s'" % model_field_class_name
            print "error: %s" % msg
            raise MetadataError(msg)

        # in theory, I could also have created a new metaclass to achieve multiple inheritance
        # but in practise, these two field types are just too dissimilar for that
        #       class _MetadataAtomicFieldMetaClass(MetadataField.Meta,modelFieldClass.Meta):
        #           pass

        class _MetadataAtomicField(cls,model_field_class):

            def __init__(self,*args,**kwargs):
                kwargs.update(model_field_class_kwargs)
                super(_MetadataAtomicField,self).__init__(**kwargs)
                self._type   = model_field_class_name

            def south_field_triple(self):
                #field_class_path = model_field_class.__class__.__module__ + "." + model_field_class.__class__.__name__
                #field_class_path = self.__class__.__module__ + "." + self.__class__.__name__
                field_class_path = "django.db.models.fields" + "." + model_field_class.__name__
                args,kwargs = introspector(self)
                return (field_class_path,args,kwargs)

        return _MetadataAtomicField(**kwargs)

class MetadataRelationshipField(MetadataField):
    class Meta:
        abstract = True

    sourceModelName    = None
    sourceAppName      = None
    targetModelName    = None
    targetAppName      = None

    def __init__(self,*args,**kwargs):
        # explicitly call super on this base class
        # so that the next item in inheritance calls its initializer
        super(MetadataRelationshipField,self).__init__(*args,**kwargs)

    def getTargetModelClass(self):
        try:
            ModelType = ContentType.objects.get(app_label=self.targetAppName,model=self.targetModelName)
            ModelClass = ModelType.model_class()
            return ModelClass
        except django.contrib.contenttypes.models.ContentType.DoesNotExist:
            # handles the case where model is accessed before target is loaded (during syncdb, for instance)
            return None

    def getSourceModelClass(self):
        try:
            ModelType = ContentType.objects.get(app_label=self.sourceAppName,model=self.sourceModelName)
            ModelClass = ModelType.model_class()
            return ModelClass
        except django.contrib.contenttypes.models.ContentType.DoesNotExist:
            # handles the case where model is accessed before target is loaded (during syncdb, for instance)
            return None

class MetadataManyToManyField(models.ManyToManyField,MetadataRelationshipField):
    _type = "manytomanyfield"

    def contribute_to_class(self,cls, name):
        preferred_related_name = name.lower() + "." + self.sourceAppName + "." + self.sourceModelName + "." + self.targetAppName + "." + self.targetModelName
        if self.related_query_name() != preferred_related_name:
            self.rel.related_name = preferred_related_name
        super(MetadataManyToManyField, self).contribute_to_class(cls, name)

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
        kwargs["related_name"]  = str(uuid4())

        super(MetadataManyToManyField,self).__init__(targetModel,**kwargs)

        self.null = True
        self.help_text = kwargs.pop("help_text","")

        if sourceModel:
            (self.sourceAppName,self.sourceModelName) = sourceModel.split(".")
        if targetModel:
            (self.targetAppName,self.targetModelName) = targetModel.split(".")


    def update(self,instances):
        super(MetadataManyToManyField,self).clear()
        super(MetadataManyToManyField,self).add(instances)


class MetadataManyToOneField(models.ForeignKey,MetadataRelationshipField):
    _type = "manytoonefield"

    def contribute_to_class(self,cls, name):
        preferred_related_name = name.lower() + "." + self.sourceAppName + "." + self.sourceModelName + "." + self.targetAppName + "." + self.targetModelName
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
        kwargs["related_name"]  = str(uuid4())        

        super(MetadataManyToOneField,self).__init__(targetModel,**kwargs)

        self.null = True
        self.help_text = kwargs.pop("help_text","")

        if sourceModel:
            (self.sourceAppName,self.sourceModelName) = sourceModel.split(".")
        if targetModel:
            (self.targetAppName,self.targetModelName) = targetModel.split(".")


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
            if "||" in value:
                val = [v.split("|") for v in value.split("||")]
                return [val[0],val[1][0]]
            else:
                return value.split("|")
        else:
            return [u'',u'']

class MetadataEnumerationFormField(django.forms.fields.MultiValueField):

    def __init__(self,*args,**kwargs):
        fields = (
            django.forms.fields.CharField(required=False),
            django.forms.fields.CharField(required=False,initial="lalala")
        )
        widget = MetadataEnumerationFormFieldWidget()
        super(MetadataEnumerationFormField,self).__init__(fields,widget,*args,**kwargs)
        self.widget = widget

    def compress(self,data_list):
        if isinstance(data_list[0],list):
            return "||".join(["|".join(data_list[0]),data_list[1]])
        else:
            return "|".join(data_list)

    def clean(self,value):
        enumeration_value = value[0]
        enumeration_other = value[1]

        if isinstance(enumeration_value,list):
            # multi...
            if OPEN_CHOICE[0][0] not in enumeration_value:
                enumeration_other = u""
            else:
                if enumeration_other.strip() == u"":
                    msg = "Unspecified OTHER value"
                    raise forms.ValidationError(msg)
                elif "|" in enumeration_other:
                    msg = "Invalid character in field."
                    raise forms.ValidationError(msg)
            return "||".join(["|".join(value[0]),value[1]])

        else:
            # not multi...
            if OPEN_CHOICE[0][0] != enumeration_value:
                enumeration_other = u""
            else:
                if enumeration_other.strip() == u"":
                    msg = "Unspecified OTHER value"
                    raise forms.ValidationError(msg)
                elif "|" in enumeration_other:
                    msg = "Invalid character in field."
                    raise forms.ValidationError(msg)
            return "|".join(value)
        
class MetadataEnumerationField(models.CharField,MetadataField):
    class Meta:
        abstract = False

    _type = "EnumerationField"

    _args   = None
    _kwargs = None

    enumerationAppName    = ""
    enumerationModelName  = ""

    open        = False
    multi       = False
    nullable    = False

    def __init__(self,*args,**kwargs):
        enumeration = kwargs.pop('enumeration',None)
        kwargs["max_length"] = HUGE_STRING
        super(MetadataEnumerationField,self).__init__(*args,**kwargs)

        self._args      = args
        self._kwargs    = kwargs
        
        if enumeration:
            (self.enumerationAppName, self.enumerationModelName) =  enumeration.split(".")

    def formfield(self,**kwargs):
        return MetadataEnumerationFormField()
        
    def getEnumeration(self):
        try:
            app = get_app(self.enumerationAppName)
            # using getattr b/c enumerations are _not_ Django Models
            # so I can't use ContentTypes magic
            enumeration = getattr(app,self.enumerationModelName)
            return enumeration
        except:
            msg = "failed to get enumeration '%s.%s'" % (self.enumerationAppName,self.enumerationModelName)
            print "error: %s" % msg
            return None

    def south_field_triple(self):
        field_class_path = self.__class__.__module__ + "." + self.__class__.__name__
        args,kwargs = introspector(self)
        return (field_class_path,args,kwargs)

#################################
# fields used by the customizer #
# ###############################

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
    _choices     = None

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

    def south_field_triple(self):
        field_class_path = self.__class__.__module__ + "." + self.__class__.__name__
        args,kwargs = introspector(self)
        return (field_class_path,args,kwargs)

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

    def south_field_triple(self):
        field_class_path = self.__class__.__module__ + "." + self.__class__.__name__
        args,kwargs = introspector(self)
        return (field_class_path,args,kwargs)

#class MetadataPropertyValueFormFieldWidget(django.forms.widgets.MultiWidget):
#
#    def __init__(self,*args,**kwargs):
#        widgets = (
#            # these will be replaced by the form's __init__ method
#            # but I need to put something in the tuple so I can change it later
#            django.forms.fields.TextInput(),
#            django.forms.fields.TextInput()
#        )
#        super(MetadataPropertyValueFormFieldWidget,self).__init__(widgets,*args,**kwargs)
#
#    def decompress(self,value):
#        if value:
#            return value.split("|")
#        else:
#            return [u'',u'']
#
#class MetadataPropertyValueFormField(django.forms.fields.MultiValueField):
#
#    def __init__(self,*args,**kwargs):
#        fields = (
#            django.forms.fields.CharField(),
#            django.forms.fields.CharField(required=False)
#        )
#        widget = MetadataPropertyValueFormFieldWidget()
#        super(MetadataPropertyValueFormField,self).__init__(fields,widget,*args,**kwargs)
#        self.widget = widget
#
#class MetadataPropertyValueField(models.CharField,MetadataField):
#    # very similar to MetadataEnumerationField, but choices don't come from an external class
#
#    def __init__(self,*args,**kwargs):
#        kwargs["max_length"] = HUGE_STRING
#        super(MetadataPropertyValueField,self).__init__(*args,**kwargs)
#
#    def formfield(self,**kwargs):
#        return MetadataPropertyValueFormField()
#


#add_introspection_rules(
#    [
##        (
##            # field_class
##            [EnumerationField],
##            # args
##            [],
##            # kwargs
##            {
##            "blank" :
##            "null" :
##            "verbose_name" :
##            },
##        ),
#    ],
#    # location
#    ["^dcf\.fields\.EnumerationField"]
#)
#
#add_introspection_rules(
#    [
##        (
##            # field_class
##            [CardinalityField],
##            # args
##            [],
##            # kwargs
##            {
##            "blank" :
##            "null" :
##            "verbose_name" :
##            },
##        ),
#    ],
#    # location
#    ["^dcf\.fields\.CardinalityField"]
#)
#
#
#add_introspection_rules(
#    [
#    ],
#    # location
#    ["^dcf\.fields\.MetadataEnumerationField"]
#)
