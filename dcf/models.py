from django.db import models

from uuid import uuid4
import django.forms.models
import django.forms.widgets
import django.forms.fields

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from dcf.helpers import *
from dcf.fields import *

def CIMDocument(documentType,documentName,documentRestriction=""):
    def decorator(obj):
        obj._isCIMDocument = True                           # specify this model as a CIM Document
        obj._cimDocumentType = documentType                 # identify the CIM type of that Document
        obj._cimDocumentName = documentName                 # identify how this model should be named in the CIM
        obj._cimDocumentRestriction = documentRestriction   # specify what permission is needed to view/edit this document
        return obj
    return decorator

############################################
# the base classes for all metadata models #
############################################

class MetadataModel(models.Model):
    # ideally, MetadataModel should be an ABC
    # but Django Models already have a metaclass: django.db.models.base.ModelBase
    # see http://stackoverflow.com/questions/8723639/a-django-model-that-subclasses-an-abc-gives-a-metaclass-conflict for a description of the problem
    # and http://code.activestate.com/recipes/204197-solving-the-metaclass-conflict/ for a solution that just isn't worth the hassle
    #from abc import *
    #__metaclass__ = ABCMeta
    class Meta:
        abstract = True

    # every subclass needs to have its own instances of this next set of attributes:
    _name = "MetadataModel"     # the name of the model; required
    _title = "Metadata Model"   # a pretty title for the model for display purposes

    # if a model is a CIM Document, then these attributes get set using the @CIMDocument decorator
    _isCIMDocument = False
    _cimDocumentType = ""
    _cimDocumentName = ""
    _cimDocumentRestriction = ""

    # every model has a (gu)id & version
    # (but since 'editable=False', they won't show up in forms)
    _guid = models.CharField(max_length=64,editable=False,blank=True,unique=True)
    _version = models.IntegerField(max_length=64,editable=False,blank=True)

    def __init__(self,*args,**kwargs):
        super(MetadataModel,self).__init__(*args,**kwargs)

        if not self._guid:
            self._guid = str(uuid4())

        if not self._version:
            self._version = 1

    @classmethod
    def getName(cls):
        name = cls._name
        if name:
            return name.strip()
        return name

    @classmethod
    def getTitle(cls):
        title = cls._title
        if title:
            return title.strip()
        return title
    
##################################################
# some code for customizing models               #
# (would rather define these in another module,  #
# but Django insists all models are in models.py #
##################################################

class FieldCategory(models.Model):
    class Meta:
        unique_together = ('_app', '_model', 'key')
        ordering = ['order']

    _app = models.CharField(max_length=64,blank=False,editable=False)
    _model = models.CharField(max_length=64,blank=False,editable=False)
    _isDefault = models.BooleanField(default=False,blank=False,editable=False)
    name = models.CharField(max_length=64,blank=True)
    key = models.CharField(max_length=64,blank=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(blank=True,null=True)

    def isDefault(self):
        return self._isDefault

    def __unicode__(self):
        name = u'%s' % self.name
        return name

DEFAULT_FIELD_CATEGORY_NAME = "my default category"
DEFAULT_FIELD_CATEGORY_DESCRIPTION = "" # previously had None here; according to Django Docs though, string fields already use empty string for "no data"

class MetadataCustomizer(models.Model):
    class Meta:
        abstract = True

    def getField(self,fieldName):
        # return the actual field (not the db representation of the field)
        try:
            return self._meta.get_field_by_name(fieldName)[0]
        except models.fields.FieldDoesNotExist:
            return None

class ModelCustomizer(MetadataCustomizer):
    _app = models.CharField(max_length=64,blank=False,editable=False)
    _model = models.CharField(max_length=64,blank=False,editable=False)
    _initialized = models.BooleanField(blank=False,default=False,editable=False)

    temporaryFields = []    # bit of a hack; m2m fields can't be added until the parent has been saved
                            # but working out which m2f fields to add is done in init, _before_ the parent has been saved
                            # so I store the fields temporarily and then add them in the explicit save fn


    categories  = models.ManyToManyField('FieldCategory',null=True,blank=True,verbose_name="Field Categories")
    fields = models.ManyToManyField('FieldCustomizer',null=True,blank=True,verbose_name="Fields")
    fields.help_text = "Each accordion represents a single field of the parent model.  Fields can be re-ordered simply by dragging and dropping them into place."

    def __init__(self,*args,**kwargs):
        super(ModelCustomizer,self).__init__(*args,**kwargs)
        
        if not self._initialized:
            # setup all the fields only once

            (defaultFieldCategory,created) = FieldCategory.objects.get_or_create(
                _app=self._app,
                _model=self._model,
                _isDefault=True,
                name=DEFAULT_FIELD_CATEGORY_NAME,
                key=DEFAULT_FIELD_CATEGORY_NAME.replace(' ',''),
                description=DEFAULT_FIELD_CATEGORY_DESCRIPTION,
                order=0
            )

            try:
                ModelType = ContentType.objects.get(app_label=self._app,model=self._model)
            except ObjectDoesNotExist:
                msg = "The model type '%s' does not exist in the application/project '%s'." % (self._model,self._app)
                raise MetadataError(msg)
            ModelClass = ModelType.model_class()


            newFields = [f for f in ModelClass._meta.fields if issubclass(type(f),MetadataField)] + [f for f in ModelClass._meta.many_to_many if issubclass(type(f),MetadataField)]
            for i,f in enumerate(newFields):
                fieldCustomizer = FieldCustomizer.objects.create(_name=f.getName(),_type=f.getType(),_model=self._model,_app=self._app)
                #fieldCustomizer.category = defaultFieldCategory
                fieldCustomizer.order = i  # the default order is random, but fields can be re-sorted in the form
                fieldCustomizer.reset(f)
                self.temporaryFields.append(fieldCustomizer)

            
            self._initialized = True

    def save(self, *args, **kwargs):
        
        super(ModelCustomizer, self).save(*args, **kwargs)

        if len(self.temporaryFields):
            self.fields = self.temporaryFields
            self.temporaryFields = []
            
    def getModelClass(self):
        try:
            ModelType = ContentType.objects.get(app_label=self._app,model=self._model)
        except ObjectDoesNotExist:
            msg = "The model type '%s' does not exist in the application/project '%s'." % (self._model,self._app)
            raise MetadataError(msg)
        ModelClass = ModelType.model_class()
        return ModelClass

    def getName(self):
        return self._model

    def getApp(self):
        return self._app
    
class FieldCustomizer(MetadataCustomizer):
    class Meta:
        ordering = ['order']    # not sure why this isn't working; wrote a custom templatetag to accomplish the same thing

    _name = models.CharField(max_length=64,blank=False,editable=False)
    _type = models.CharField(max_length=64,blank=False,editable=False)
    _model = models.CharField(max_length=64,blank=False,editable=False)
    _app = models.CharField(max_length=64,blank=False,editable=False)

    order = models.PositiveIntegerField(blank=True,null=True)
    category = models.ForeignKey('FieldCategory',blank=True,null=True,verbose_name="what field category (if any) does this field belong to")

    displayed = models.BooleanField(default=True,blank=True,verbose_name="should field be displayed")
    required = models.BooleanField(default=False,blank=True,verbose_name="is field required")
    editable = models.BooleanField(default=False,blank=True,verbose_name="can field be edited")
    unique = models.BooleanField(default=False,blank=True,verbose_name="must field be unique")
    verbose_name = models.CharField(max_length=64,blank=True,verbose_name="how should this field be labeled (overrides default name)")
    documentation = models.TextField(blank=True,verbose_name="help text to associate with field")
    replace = models.BooleanField(default=False,blank=True,verbose_name="should this field be rendered as a subform (as opposed to a standard select widget)")

    def init(self,*args,**kwargs):
        
        _name = kwargs.pop("name",None)
        _type = kwargs.pop("type",None)
        _model = kwargs.pop("model",None)
        _app = kwargs.pop("app",None)

        super(FieldCustomizer,self).__init__(*args,**kwargs)
        

    def reset(self,*args):

        field = args[0]

        self.required = (field.blank == False)
        self.editable = field.editable
        self.unique = field.unique
        self.verbose_name = field.verbose_name
        self.documentation = field.help_text

        # reset forces a save
        self.save()

    def getName(self):
        return self._name

    def getApp(self):
        return self._app

    def getType(self):
        return self._type

    def getModel(self):
        return self._model

    def getCategory(self):
        return self.category

#    def getOrder(self):
#        return self.fieldOrder
#
#    def setOrder(self,order):
#        self.fieldOrder = order
