from django.db import models
from django import forms
import django.forms.models
import django.forms.widgets
import django.forms.fields
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from final.controlled_vocabulary import *
from final.helpers import *

############################################################
# the types of fields that a model can have                #
# (these are specified as needed in the models themselves) #
############################################################

class FieldType(EnumeratedType):
    pass

#######################################################
# the ways that (relationship) fields can be added to #
#######################################################

class FieldAddMode(EnumeratedType):
    pass

FieldAddModes = EnumeratedTypeList([
    FieldAddMode("INLINE","add field in-line only"),
    FieldAddMode("REMOTE","add field remote only"),
    FieldAddMode("BOTH","add field in-line or remote"),
])


##########################################################################
# this is a way to customise _any_ widgets used by metadata fields       #
# without having to hard-code _all_ of them; it inserts some css classes #
# and the template knows what to do with that (currently JQuery stuff)   #
##########################################################################


def customize_metadata_widgets(field):
    formfield = field.formfield()

    try:
        # some fields have the isFixed method, which means they should be readonly
        if field.isFixed():
            formfield.widget.attrs.update({"readonly" : "readonly"})
    except AttributeError:
        pass

    # only customize custom fields (ie: only apply this logic to subclasses of MetadataFields)...
    if isinstance(field,MetadataField):

        if field.isReadOnly():
            formfield.widget.attrs.update({"readonly":"readonly"})

        if field.isEnabler():
            #java_string = ""
            #for (key,value) in field._enables.iteritems():
            #    java_string += "\"" + key + "\" : [" + ",".join([u'"%s"'%fieldName for fieldName in value]) + ","
                
            
            #java_string = "toggleStuff(this,{%s})" % java_string[:-1]

            java_string = [",".join([u'"%s"'%key for key in field._enables.keys()]) , ",".join([u'"%s"'%value for value in field._enables[key]])    ]
            java_string = "toggleStuff(this,%s)"% java_string
            
            print java_string
#            formfield.widget.attrs.update({"class" : "enabler", "onclick" : java_string})

        if isinstance(field,MetadataEnumerationField):
            # BoundFields are a bit different, b/c their formfields are MultiValueFields,
            # so I have to specify which corresponding widget I wish to modify...
            if field.isReadOnly():
                # Select widgets use the keyword "disabled" instead of "readonly"... go figure
                formfield.widget.widgets[0].attrs.update({"disabled":"disabled",})

        if isinstance(field,MetadataAtomicField):
            formfield.widget.attrs.update({"class":"atomic"})
            
        if isinstance(field,models.DateField):
            formfield.widget.attrs.update({"class":"datepicker"})

        if isinstance(field,models.BooleanField):
            if field.isEnabler():
                java_string = "toggleStuff(this,[%s])" % ",".join([u'"%s"'%f for f in field.enables])
                formfield.widget.attrs.update({"class":"enabler","onclick":java_string})
            else:
                #print "NOT ENABLER"
                pass

###    if isinstance(field,MetadataDocumentField):
###        formfield.widget.attrs.update({"class" : "adder"})
###        formfield.widget.attrs.update({"title": u'%s/%s'%(field.getAppName(),field.getModelName())})
###
###    if isinstance(field,MetadataAbstractField):
###        java_string = "toggleForm($(this).val(),[%s])" % ",".join([u'"%s"' % choice[0] for choice in field.getChoices()])
###        formfield.widget.attrs.update({"onclick" : java_string})
###        formfield.widget.attrs.update({"class":"abstract-choice"})
###
###    # TODO: other if branches for other field types?
###

    return formfield

########################################################
# the set of customizable fields for metadata models   #
# each item consists of a name, a corresponding class, #
# and a set of default kwargs required for that class. #
########################################################

MODELFIELD_MAP = {
    "booleanfield"          : [models.BooleanField, {}],
    "charfield"             : [models.CharField, { "max_length" : BIG_STRING}],
    "datefield"             : [models.DateField, {}],
    "datetimefield"         : [models.DateTimeField, {}],
    "decimalfield"          : [models.DecimalField, {}],
    "emailfield"            : [models.EmailField, {}],
    "integerfield"          : [models.IntegerField, {}],
    "datetimefield"         : [models.NullBooleanField, {}],
    "nullbooleanfield"      : [models.PositiveIntegerField, {}],
    "textfield"             : [models.TextField, {}],
    "timefield"             : [models.TimeField, {}],
    "urlfield"              : [models.URLField, { "verify_exists" : False}],
}


################################
# the base class of all fields #
################################

class MetadataField(models.Field):
    class Meta:
        abstract = True

    _required   = False     # by default, fields are not required
    _readonly   = False     # a field can be readonly
    _enables    = {}        # a field can toggle (enable) other fields

    @classmethod
    def comparator(cls,fieldName,fieldOrderList):
        if fieldName in fieldOrderList:
            return fieldOrderList.index(fieldName)
        return len(fieldOrderList)+1

    def isRequired(self):
        return self._required

    def enables(self,enablingDictionary):
        # enablingDictiony lists fields to enable based on value:
        # { val1 : ["f1","f2","f3"], val2 : ["f4","f5","f6" }
        self._enables = enablingDictionary


    def isEnabler(self):
        return bool(self._enables)

    def isReadOnly(self):
        return self._readonly

    def getVerboseName(self):
        verbose_name = self.verbose_name
        if verbose_name != self.name:
            return verbose_name
        return pretty_string(verbose_name)

    def __init__(self,*args,**kwargs):
        kwargs["blank"] = kwargs.pop("blank",True)
        required = not kwargs["blank"]
        readonly = kwargs.pop("readonly",False)
        super(MetadataField,self).__init__(*args,**kwargs)
        self._required = required
        self._readonly = readonly

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
        return _MetadataAtomicField(**kwargs)



class MetadataRelationshipField(MetadataField):

    class Meta:
        abstract = True

    _addMode = FieldAddModes.BOTH   # by default, relationships can be to existing models or to new models created inline

    _sourceModelName    = None
    _sourceAppName      = None
    _targetModelName    = None
    _targetAppName      = None


##    def __init__(self,*args,**kwargs):
##        # this fn doesn't actually ever get called;
##        # the Method Resolution Order for subclasses of MetadataRelationshipField has the django.db.models class first,
##        # so that class's __init__ fn gets called.  However, these classes still have access to all RelationshipField's attributes.
##        super(MetadataRelationshipField,self).__init__(*args,**kwargs)

    # do some post-initialization
    # (see above comment for an explanation of why this stuff isn't in __init__)
    def initRelationship(self,*args,**kwargs):
        self.related_name = self.name   # related_name has to be unique to distinguish between different relationshipFields from the same model to the same model
        self.null = True                # null values have to be allowed in order to initialize subForms w/ potentially brand-new (empty) models
        self.blank = not self.isRequired()

        addMode     = kwargs.pop("addMode",FieldAddModes.BOTH)
        required    = not(kwargs.pop("blank",True))
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

        self._required = required
        self._addMode = addMode


    def canAddRemote(self):
        # returns True if this field is one that can link to existing models
        # returns False if the linked model must be created in-line
        return self.addMode != FieldAddModes.INLINE

    def getTargetModelClass(self):
        ModelType = ContentType.objects.get(app_label=self._targetAppName,model=self._targetModelName)
        ModelClass = ModelType.model_class()
        return ModelClass

    def getSourceModelClass(self):
        ModelType = ContentType.objects.get(app_label=self._sourceAppName,model=self._sourceModelName)
        ModelClass = ModelType.model_class()
        return ModelClass


class MetadataAbstractField():
    pass


class MetadataManyToOneField(models.ForeignKey,MetadataRelationshipField):
    pass

    def __init__(self,*args,**kwargs):
        targetModel = kwargs.pop("targetModel",None)
        sourceModel = kwargs.pop("sourceModel",None)
        super(MetadataManyToOneField,self).__init__(targetModel,**kwargs)
        self.initRelationship(sourceModel=sourceModel,targetModel=targetModel,**kwargs)

class MetadataManyToManyField(models.ManyToManyField,MetadataRelationshipField):
    pass

    def __init__(self,*args,**kwargs):
        targetModel = kwargs.pop("targetModel",None)
        sourceModel = kwargs.pop("sourceModel",None)
        super(MetadataManyToManyField,self).__init__(targetModel,**kwargs)
        self.initRelationship(sourceModel=sourceModel,targetModel=targetModel,**kwargs)

# TODO: "BoundField" has a particular meaning in Django
# I ought to change this class name to something else
class MetadataBoundField(MetadataField):

    _open     = False       # can a user override the bound values?
    _multi    = False       # can a user select more than one bound value?
    _nullable = False       # can a user select no bound values?

    class Meta:
        abstract = True

# I don't understand why __init__ gets called here, but not for RelationshipFields;
# both have multiple inheritance issues?
    def __init__(self,*args,**kwargs):
        open = kwargs.pop("open",False)
        multi = kwargs.pop("multi",False)
        nullable = kwargs.pop("nullable",False)
        super(MetadataBoundField,self).__init__(**kwargs)
        self._open = open
        self._multi = multi
        self._nullable = nullable

#    def initBound(self,*args,**kwargs):
#        self._open = kwargs.pop("open",False)
#        self._multi = kwargs.pop("multi",False)
#        self._nullable = kwargs.pop("nullable",False)

    def isOpen(self):
        return self._open

    def isMulti(self):
        return self._multi

    def isNullable(self):
        return self._nullable

class MetadataBoundWidget(django.forms.widgets.MultiWidget):

    custom_choices = []
    _multi = False

    def __init__(self,*args,**kwargs):

        custom_choices = kwargs.pop("choices",None)
        multi = kwargs.pop("multi",False)

        if multi:
            widgets = (
                django.forms.fields.SelectMultiple(choices=custom_choices,attrs={"class":"enumeration-value"}),
                django.forms.fields.TextInput(attrs={"class":"enumeration-other"}),
            )
        else:
            widgets = (
                django.forms.fields.Select(choices=custom_choices,attrs={"class":"enumeration-value"}),
                django.forms.fields.TextInput(attrs={"class":"enumeration-other"}),
            )
        super(MetadataBoundWidget,self).__init__(widgets,*args,**kwargs)
        self.custom_choices = custom_choices
        self._multi = multi

    def decompress(self, value):
        if self._multi:
            if value:
                val = [val.split("|") for val in value.split("||")]
                return [val[0],val[1][0]]
            return [[u''],u'']
        else:
            if value:
                return value.split("|")
            return [u'',u'']

class MetadataBoundFormField(django.forms.fields.MultiValueField):

    custom_choices = []
    _multi = False

    def __init__(self,*args,**kwargs):

        custom_choices = kwargs.pop("choices",None)
        multi = kwargs.pop("multi",False)
        fields = (
            django.forms.fields.CharField(max_length=HUGE_STRING,required=True),
            django.forms.fields.CharField(max_length=HUGE_STRING,required=False),
        )
        widget = MetadataBoundWidget(choices=custom_choices,multi=multi)
        super(MetadataBoundFormField,self).__init__(fields,widget,*args,**kwargs)
        self.widget = widget # why is this line still needed, even though widget is passed into *args above?
        self.custom_choices = custom_choices
        self._multi = multi



    def compress(self, data_list):
        if self._multi:
            if data_list:
                return "||".join(["|".join(data_list[0]),data_list[1]])
        else:
            if data_list:
                return "|".join(data_list)

    def clean(self,value):

        if value != [None,None]:
#        if value[0]==None:
#            value[0] = u' '
#        if value[1]==None:
#            value[1]= u' '



            if self._multi:
                # if this is a multiple bound field
                # then the value will be a list of lists
                if not OTHER_CHOICE[0][0] in value[0]:
                    value[1] = u' '
                else:
                    if value[1].strip() == u'':
                        msg = "unspecified OTHER value"
                        raise forms.ValidationError(msg)
                    elif "|" in value[1]:
                        msg = "bad value ('|' character is not allowed)"
                        raise forms.ValidationError(msg)
                return "||".join(["|".join(value[0]),value[1]])

            else:
                # if this is not a multiple bound field
                # then the value will just be a simple list
                if value[0] != OTHER_CHOICE[0][0]:
                    value[1] = u' '
                else:
                    if value[1].strip() == u'':
                        msg = "unspecified OTHER value"
                        raise forms.ValidationError(msg)
                    elif "|" in value[1]:
                        msg = "bad value ('|' character is not allowed)"
                        raise forms.ValidationError(msg)
                return "|".join(value)

class MetadataEnumerationField(models.CharField,MetadataBoundField):

    _enumerationModelName   = None
    _enumerationAppName     = None


    def formfield(self,*args,**kwargs):
        custom_choices = []
        EnumerationClass = self.getEnumerationClass()
        if EnumerationClass:
            if not EnumerationClass.isLoaded():
                EnumerationClass.loadEnumerations()
            custom_choices = [(enumeration.name,pretty_string(enumeration.name)) for enumeration in EnumerationClass.objects.all()]

        if self.isOpen():
            custom_choices += OTHER_CHOICE
        if self.isNullable():
            custom_choices += NONE_CHOICE

        return MetadataBoundFormField(choices=custom_choices,multi=self.isMulti())


    def getEnumerationClass(self):
        try:
            ModelType = ContentType.objects.get(app_label=self._enumerationAppName,model=self._enumerationModelName)
            return ModelType.model_class()
        except:
            return None

    def __init__(self,*args,**kwargs):
        enumeration = kwargs.pop('enumeration',None)
        kwargs["max_length"] = HUGE_STRING        
        super(MetadataEnumerationField,self).__init__(*args,**kwargs)
        if enumeration:
            enumerationAppAndModel = enumeration.split(".")
            self._enumerationModelName = enumerationAppAndModel[1].lower()
            self._enumerationAppName = enumerationAppAndModel[0].lower()
# apparently, this is not needed (super() above calls BoundField.__init__()
#        self.initBound(*args,**kwargs)
        
# TODO: PROPERTY FIELD

class MetadataPropertyField(models.CharField,MetadataBoundField):
    pass

    def formfield(self,**kwargs):
        return MetadataBoundFormField(choices=self._choices)
    
    def __init__(self,*args,**kwargs):
        kwargs["max_length"] = HUGE_STRING
        super(MetadataPropertyField,self).__init__(*args,**kwargs)
        
# TODO: MUTLIPLE FIELD




