
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
__date__ ="Jun 10, 2013 5:31:04 PM"

"""
.. module:: metadata_version

Summary of module goes here

"""

from django.db import models, DatabaseError
from django.db.models import get_app, get_model, get_models
from django.db.models.fields import NOT_PROVIDED
from django.db.utils import DatabaseError as UtilsDatabaseError
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured, ValidationError



from dcf.models import *
from dcf.utils import *

class MetadataVersion(models.Model):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        # this is one of the few classes that I allow admin access to, so give it pretty names:
        verbose_name        = 'Metadata Version'
        verbose_name_plural = 'Metadata Versions'

    name    = models.CharField(max_length=255,blank=False)
    number  = models.CharField(max_length=64,blank=False)

    models = models.TextField(blank=True) # dictionary of { "model_name" : [ "field_name1" ... "field_nameN" ], }

    def __unicode__(self):
        return u'%s' % (self.getAppName())

    def getAppName(self):
        app_name = self.name.lower() + "_" + re.sub(r'\.','_',self.number)
        return app_name

    def getTitle(self):
        return u'%s %s' % (self.name,self.number)
    
    def setModels(self,models_dict):
        models_dict_string = json.dumps(models_dict,separators=(',',":"))
        self.models = models_dict_string
    
    def getModels(self):
        models_dict_json = json.loads(self.models)
        return models_dict_json

    def getAllModelClasses(self):
        model_classes = []
        models_dict = self.getModels()
        for key in models_dict.keys():
            try:
                app = self.getAppName()
                model = get_model(app,key)
                model_classes.append(model)
            except:
                pass
        return model_classes


    def getModelClass(self,model_name):
        models_dict = self.getModels()
        for key in models_dict.keys():
            if model_name.lower() == key.lower():
                model_name = key
                break

        try:
            app = self.getAppName()
            model = get_model(app,model_name)
        except:
            msg = "unable to find model '%s'" % model_name
            print "error: msg"
            raise MetadataError(msg)
        
        return model
        
    def register(self):
        models_dict = {}
        app = get_app(self.getAppName())

        model_filter_parameters    = {}
        property_filter_parameters = {}

        for model in get_models(app):
            if issubclass(model,MetadataModel):
                model_name = model.getName().lower()
                if model_name in models_dict:
                    msg = "multiple MetadataModels named '%s' exist in MetadataVersion %s" % (model_name,self)
                    print "error: %s" % msg
                    raise MetadataError(msg)

                models_dict[model_name] = []

                model_filter_parameters.clear()
                model_filter_parameters["version"]              = self
                model_filter_parameters["model_name"]           = model_name
                model_filter_parameters["model_title"]          = model.getTitle()
                model_filter_parameters["model_description"]    = model.getDescription()
                model_filter_parameters["document_type"]        = model.getType()

                (model_proxy,created) = MetadataModelProxy.objects.get_or_create(**model_filter_parameters)
                if created:
                    print "created new model proxy: %s" % model_proxy
                else:
                    print "model proxy %s already exists" % model_proxy
                  
                for field in model.getFields():
                    field_name = field.getName()
                    field_type = field.getType().lower()

                    property_filter_parameters.clear()
                    property_filter_parameters["version"]       = self
                    property_filter_parameters["model_name"]    = model_name
                    property_filter_parameters["name"]          = field_name
                    property_filter_parameters["field_type"]    = field_type                    
                    property_filter_parameters["required"]      = field.blank == False
                    property_filter_parameters["editable"]      = field.editable
                    property_filter_parameters["unique"]        = field.unique
                    property_filter_parameters["verbose_name"]  = field.verbose_name
                    property_filter_parameters["documentation"] = field.help_text
                    property_filter_parameters["default_value"] = field.default if (field.default != NOT_PROVIDED) else None

                    if isAtomicField(field_type):
                        property_filter_parameters["type"] = MetadataFieldTypes.ATOMIC

                    elif isRelationshipField(field_type):
                        property_filter_parameters["type"] = MetadataFieldTypes.RELATIONSHIP
                        property_filter_parameters["relationship_target_model"] = ".".join([field.targetAppName,field.targetModelName])
                        property_filter_parameters["relationship_source_model"] = ".".join([field.sourceAppName,field.sourceModelName])

                    elif isEnumerationField(field_type):
                        enumeration = field.getEnumeration()
                        property_filter_parameters["type"] = MetadataFieldTypes.ENUMERATION
                        property_filter_parameters["enumeration_choices"]     = "|".join(enumeration.getChoices())
                        property_filter_parameters["enumeration_open"]        = enumeration.isOpen()
                        property_filter_parameters["enumeration_multi"]       = enumeration.isMulti()
                        property_filter_parameters["enumeration_nullable"]    = enumeration.isNullable()

                    else:
                        pass

                    (property_proxy,created) = MetadataStandardPropertyProxy.objects.get_or_create(**property_filter_parameters)
                    if created:
                        print "created new property proxy: %s" % property_proxy
                    else:
                        print "propery proxy %s already exists" % property_proxy

                    models_dict[model_name].append(field_name)

        self.setModels(models_dict)
        self.save()

    @classmethod
    def factory(cls,*args,**kwargs):
        """
        Builds an instance of a MetadataVersion
        """
        try:
            # by convention, versions should be in their own Django Applications
            # which are named <name>_<number>
            # where any "." in <number> are replaced w/ "_" & names are all lowercase
            # as in "cim_1_8_1"
            app_name = kwargs["name"].lower() + "_" + re.sub(r'\.',"_",kwargs["number"])
            app = get_app(app_name)
        except KeyError:
            msg = "name and number must be specified when creating a MetadataVersion"
            print "error: %s" % msg
            raise MetadataError(msg)
        except ImproperlyConfigured:
            msg = "unable to find a MetadataVersion called '%s'" % app_name
            print "error: %s" % msg
            raise MetadataError(msg)

        try:
            (metadata_version,created) = MetadataVersion.objects.get_or_create(**kwargs)
            if created:
                print "registering MetadataVersion: '%s'" % metadata_version
            else:
                print "MetadataVersion '%s' already exists; skipping registration" % metadata_version
            return metadata_version
        except DatabaseError:
            # depending on the order that django processes models during "syncdb,"
            # MetadataVersion may not exist yet in the db.
            # that's okay - this only has to work during "runserver"
            print "database error while attempting to register MetadataVersion (try restarting server)"
            pass
