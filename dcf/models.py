from django.db import models

from uuid import uuid4
import django.forms.models
import django.forms.widgets
import django.forms.fields

from django.contrib.contenttypes.models import ContentType
from django.db.models.fields import NOT_PROVIDED
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

    # every model in the DCF application has a (gu)id & version
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
    def getAppName(cls):
        return cls._meta.app_label

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

    @classmethod
    def getFormClass(cls):
        form_name = cls.getName() + "_form"
        app_name = cls._meta.app_label

        for (full_app_name,app_module) in [(key,value) for (key,value) in sys.modules.iteritems() if app_name in key and value]:
            try:
                FormClass = getattr(app_module,form_name)
                return FormClass
            except AttributeError:
                pass

        return None

    def getField(self,fieldName):
        # return the actual field (not the db representation of the field)
        try:
            return self._meta.get_field_by_name(fieldName)[0]
        except models.fields.FieldDoesNotExist:
            return None

    def getAllFields(self):
        return [f for f in self._meta.fields if issubclass(type(f),MetadataField)] + [f for f in self._meta.many_to_many if issubclass(type(f),MetadataField)]

    def getActiveFieldCategories(self):
        currentFields = [f for f in self._meta.fields if issubclass(type(f),MetadataField)] + [f for f in self._meta.many_to_many if issubclass(type(f),MetadataField)]
        activeFields = [f for f in currentFields if f.is_custom_visible()]
        activeCategories = list(set([f.get_custom_category() for f in activeFields if f.get_custom_category()])) # list(set()) removes duplicates
        return sorted(activeCategories, key=lambda x: x.order)

###################################################
# some code for customizing models                #
# (would rather define these in another module,   #
# but Django insists all models are in models.py) #
###################################################

def getCustomizer(app_name,model_name,customizer_name=""):
    # TODO: need to do something w/ customizer_name!
    customizers = ModelCustomizer.objects.filter(appName=app_name,modelName=model_name)
    if customizers:
        try:
            customizer = customizers.get(name=customizer_name)
        except MultipleObjectsReturned:
            # I don't expect to wind up here, but just in-case something weird happens go ahead and use the default customizer
            customizer = customizers.get(default=1)
        except ModelCustomizer.DoesNotExist:
            customizer = customizers.get(default=1)
    else:
        # this app/model combination has not been customized yet, just create a new one
        customizer = ModelCustomizer(appName=app_name,modelName=model_name)
        customizer.save()

    return customizer

class CustomizerBase(models.Model):
    class Meta:
        abstract = True

    # every model in the DCF application has a (gu)id & version
    _guid = models.CharField(max_length=64,editable=False,blank=True,unique=True)
    _version = models.IntegerField(max_length=64,editable=False,blank=True)

    # every model involved in customization references a particular app/model combination
    appName = models.CharField(max_length=64,blank=False,editable=False)
    modelName = models.CharField(max_length=64,blank=False,editable=False)

    def __init__(self,*args,**kwargs):
        super(CustomizerBase,self).__init__(*args,**kwargs)

        if not self._guid:
            self._guid = str(uuid4())

        if not self._version:
            self._version = 1

    def getGUID(self):
        return self._guid

    def getVersion(self):
        return self._version

    def updateVersion(self,version):
        self._version = version

    def updateGUID(self,guid):
        self._guid = guid

    def getModelName(self):
        return self.modelName

    def getAppName(self):
        return self.appName
    
    def getCommonCustomizers(self):
        # returns a list of customizers (either FieldCategories, ModelCustomizers, or FieldCustomizers)
        # belonging to the same app/model combination
        ModelClass = self.__class__
        return  ModelClass.objects.filter(appName=self.appName,modelName=self.modelName)

    def getModelClass(self):
        # returns the model that this customizer is associated w/
        try:
            ModelType = ContentType.objects.get(app_label=self.appName,model=self.modelName)
        except ObjectDoesNotExist:
            msg = "The model type '%s' does not exist in the application/project '%s'." % (self.modelName,self.appName)
            raise MetadataError(msg)
        ModelClass = ModelType.model_class()
        return ModelClass

    def getField(self,fieldName):
        # return the actual field (not the db representation of the field)
        try:
            return self._meta.get_field_by_name(fieldName)[0]
        except models.fields.FieldDoesNotExist:
            return None

    def getUniqueTogether(self):
        # returns the set of fields (their names) that must be unique_together
        # otherwise returns None
        unique_together = self._meta.unique_together
        for field_set in unique_together:
            return field_set
        return None
    
    def __unicode__(self):
        className = self.__class__.__name__.upper()
        name = u'%s::%s' % (self.getAppName(),self.getModelName())
        try:
            name = u'%s::%s' % (name,self._name)
        except AttributeError:
            pass
        try:
            name = u'%s "%s"' % (name,self.name)
        except AttributeError:
            pass
        return name

class FieldCategory(CustomizerBase):
    class Meta:
        unique_together = ('appName', 'modelName', 'key')
        ordering = ['order']

    name = models.CharField(max_length=64,blank=True)
    key = models.CharField(max_length=64,blank=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(blank=True,null=True)
    default = models.BooleanField(default=False,blank=False,editable=False)

    def isDefault(self):
        return self.default

    def __unicode__(self):
        name = u'%s' % self.name
        return name

DEFAULT_FIELD_CATEGORY_NAME = "Basic Properties"
DEFAULT_FIELD_CATEGORY_DESCRIPTION = "" # previously had None here; according to Django Docs though, string fields already use empty string for "no data"


class ModelCustomizer(CustomizerBase):
    class Meta:
        unique_together = ('appName', 'modelName', 'name')

    initialized = models.BooleanField(blank=False,default=False,editable=False)

    temporaryFields = []    # bit of a hack; m2m fields can't be added until the parent has been saved
                            # but working out which m2f fields to add is done in init, _before_ the parent has been saved
                            # so I store the fields temporarily and then add them in the explicit save fn


    name = models.CharField(verbose_name="Name",max_length=64,blank=True,editable=True)
    name.help_text = "A unique name for this customization (ie: \"basic\" or \"advanced\")"
    description = models.TextField(verbose_name="Description",blank=True,editable=True)
    description.help_text = "An explanation of how this customization is intended to be used.  This information is for informational purposes only."
    default = models.BooleanField(verbose_name="Is Default Customization",blank=True,editable=True)
    default.help_text = "Defines the default customization that is used by this app/model combination if no explicit customization is provided"

    categories  = models.ManyToManyField('FieldCategory',null=True,blank=True,verbose_name="Field Categories")
    fields = models.ManyToManyField('FieldCustomizer',null=True,blank=True,verbose_name="Fields")
    fields.help_text = "Each accordion represents a single field of the parent model.  Fields can be re-ordered simply by dragging and dropping them into place."

    def __init__(self,*args,**kwargs):
        super(ModelCustomizer,self).__init__(*args,**kwargs)

        # only one customizer can be the default one...
        otherCustomizers = self.getCommonCustomizers().exclude(_guid=self.getGUID())
        if otherCustomizers.count() == 0:
            # therefore, if this is the only customizer, it must be the default one...
            self.default = True

        if not self.initialized:
            (defaultFieldCategory,created) = FieldCategory.objects.get_or_create(
                appName=self.appName,
                modelName=self.modelName,
                default=True,
                name=DEFAULT_FIELD_CATEGORY_NAME,
                key=DEFAULT_FIELD_CATEGORY_NAME.replace(' ',''),
                description=DEFAULT_FIELD_CATEGORY_DESCRIPTION
            ) # not specifying "order" b/c it can get changed by form


            try:
                ModelType = ContentType.objects.get(app_label=self.appName,model=self.modelName)
            except ObjectDoesNotExist:
                msg = "The model type '%s' does not exist in the application/project '%s'." % (self.modelName,self.appName)
                raise MetadataError(msg)
            ModelClass = ModelType.model_class()

            # setup all the fields only once...
            newFields = [f for f in ModelClass._meta.fields if issubclass(type(f),MetadataField)] + [f for f in ModelClass._meta.many_to_many if issubclass(type(f),MetadataField)]
            for i,f in enumerate(newFields):
                fieldCustomizer = FieldCustomizer.objects.create(_name=f.getName(),_type=f.getType(),_customizerGUID=self.getGUID(),modelName=self.modelName,appName=self.appName)
                #fieldCustomizer.category = defaultFieldCategory
                fieldCustomizer.order = i+1  # the default order is random, but fields can be re-sorted in the form
                fieldCustomizer.reset(f)
                self.temporaryFields.append(fieldCustomizer)
            
            self.initialized = True


    def save(self, *args, **kwargs):
        
        super(ModelCustomizer, self).save(*args, **kwargs)

        # if this is the first time we're saving the model
        # copy over all of the fields that were setup in __init__
        if len(self.temporaryFields):
            self.fields = self.temporaryFields
            self.temporaryFields = []
        
        # only one customizer can be the default one...
        otherCustomizers = self.getCommonCustomizers().exclude(_guid=self.getGUID())
        if otherCustomizers:
            if self.default:
                for customizer in otherCustomizers:
                    customizer.default = False
                    customizer.save()
        else:
            # if this is the only customizer, it must be the default one...
            self.default = True
            
    
class FieldCustomizer(CustomizerBase):
    class Meta:
        ordering = ['order']    # not sure why this isn't working; wrote a custom templatetag to accomplish the same thing

    # a FieldCustomizer has a field name & type (as specified in the DB)
    # and belongs to a particular ModelCustomizer (specified by its GUID)
    _name = models.CharField(max_length=64,blank=False,editable=False)
    _type = models.CharField(max_length=64,blank=False,editable=False)
    _customizerGUID = models.CharField(max_length=64,blank=False,editable=False)

    order = models.PositiveIntegerField(blank=True,null=True)
    category = models.ForeignKey('FieldCategory',blank=True,null=True,verbose_name="what field category (if any) does this field belong to")

    # TODO: ADD MORE WAYS OF CUSTOMIZING FIELDS AS NEEDED...
    displayed = models.BooleanField(default=True,blank=True,verbose_name="should field be displayed")
    required = models.BooleanField(default=False,blank=True,verbose_name="is field required")
    editable = models.BooleanField(default=False,blank=True,verbose_name="can field be edited")
    unique = models.BooleanField(default=False,blank=True,verbose_name="must field be unique")
    verbose_name = models.CharField(max_length=64,blank=False,verbose_name="how should this field be labeled (overrides default name)")
    default_value = models.CharField(max_length=128,blank=True,null=True,verbose_name="does this field have a default value")
    documentation = models.TextField(blank=True,verbose_name="help text to associate with field")
    replace = models.BooleanField(default=False,blank=True,verbose_name="should this field be rendered as a subform (as opposed to a standard select widget)")

    def init(self,*args,**kwargs):
        
        _name = kwargs.pop("name",None)
        _type = kwargs.pop("type",None)
        
        super(FieldCustomizer,self).__init__(*args,**kwargs)


    def reset(self,*args):

        field = args[0]

        self.required = (field.blank == False)
        self.editable = field.editable
        self.unique = field.unique
        self.verbose_name = field.verbose_name
        self.documentation = field.help_text
        self.default_value = field.default if (field.default != NOT_PROVIDED) else None

        # reset forces a save
        self.save()

    def getName(self):
        return self._name

    def getType(self):
        return self._type

    def getCategory(self):
        return self.category

#    def getOrder(self):
#        return self.fieldOrder
#
#    def setOrder(self,order):
#        self.fieldOrder = order

