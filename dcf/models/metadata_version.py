
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
__date__ ="Jan 31, 2013 11:25:52 AM"

"""
.. module:: metadata_version

Summary of module goes here

"""

from django.db import models, DatabaseError
from django.db.models import get_app, get_model, get_models
from django.db.utils import DatabaseError as UtilsDatabaseError
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured, ValidationError

from dcf.utils import *
from dcf.models import MetadataModel

#@guid()
class MetadataVersion(models.Model):
    class Meta:
        app_label = APP_LABEL
        unique_together     = ("name", "version")
        verbose_name        = 'Metadata Version'
        verbose_name_plural = 'Metadata Versions'

    name    = models.CharField(max_length=LIL_STRING,blank=False)
    version = models.CharField(max_length=LIL_STRING,blank=False)
    # you cannot have a generic m2m field (at least not easily) to the abstract class MetadataModels
    # so I'm just using a CharField to store a '|' separated list of their names in the db
    # (later on at runtime in __init__, I use these to populate a dictionary of classes)
    model_names  = models.CharField(max_length=HUGE_STRING,blank=True)
    # TODO: IN FUTURE I MAY ALLOW USERS TO CHOOSE AMONG A SET OF CATEGORIZATIONS;
    # FOR NOW, THERE IS ONLY ONE
    default_categorization = models.ForeignKey("MetadataCategorization",blank=True,null=True,related_name="version")

    models = {}

    #_guid = models.CharField(max_length=64,unique=True,editable=False,blank=False,default=lambda:str(uuid4()))
    #def getGUID(self):
    #    return self._guid

    def __unicode__(self):
        _name = u'%s %s' % (self.name,self.version)
        return _name

    def __init__(self,*args,**kwargs):
        """
        Initialize a MetadataVersion.
        For each model_name in model_names, get the corresponding MetadataModel class and add it to an internal dictionary.
        """
        super(MetadataVersion,self).__init__(*args,**kwargs)
        app_name = self.name.lower() + "_" + re.sub(r'\.',"_",self.version)
        
        for model_name in self.model_names.split("|"):
            try:
                # TODO: I HAVE NO IDEA WHY get_model WORKS, BUT ContentTypes DOESN'T ?!?
                #model_type = ContentType.objects.get(app_label=app_name,model=model_name)
                #self.models[model_name] = model_type.model_class()
                self.models[model_name] = get_model(app_name,model_name)
            except ObjectDoesNotExist:
                # this might be called during "syncdb" before all MetadataModels exist in the db
                # that's okay - it only has to work during "runserver"
                pass
        
    def loadVersion(self):
        app_name = self.name.lower() + "_" + re.sub(r'\.',"_",self.version)
        app = get_app(app_name)

        _models = []
        for model in get_models(app):
            if issubclass(model,MetadataModel):
                _models.append(model.getName().lower())
        self.model_names = ("|").join(_models)

        self.models = {}

    def getModel(self,model_name):
        try:
            return self.models[model_name.lower()]
        except KeyError:
            return None

    def getProjects(self):
        """
        uses reverse relationship to list all MetadataProjects that have this version as a possible version
        """
        return self.metadataproject_set.all()

    def getDefaultProjects(self):
        """
        uses reverse relationship to list all MetadataProjects that have this version as a default version
        """
        return self.project.all()

    @classmethod
    def factory(cls,kwargs):
        """
        Builds an instance of a MetadataVersion
        """

        print "in MetadataVersion.factory(%s)" % kwargs

        try:
            # by convention, versions should be in their own Django Applications
            # which are named <name>_<version> where any "." in <version> are replaced w/ "_"
            # as in "cim_1_5"
            app_name = kwargs["name"].lower() + "_" + re.sub(r'\.',"_",kwargs["version"])
            print "about to call get_app(%s)" % app_name
            app = get_app(app_name)
        except KeyError:
            msg = "name and version must be specified when creating a MetadataVersion"
            print "error: %s" % msg
            raise MetadataError(msg)
        except ImproperlyConfigured:
            msg = "unable to find a MetadataVersion called '%s'" % app_name
            print "error: %s" % msg
            raise MetadataError(msg)

        try:
            print "about to create metadataversion(%s)" % kwargs
            (metadata_version,created) = MetadataVersion.objects.get_or_create(**kwargs)
            if created:
                print "registering MetadataVersion: '%s'" % metadata_version
            return metadata_version
        except DatabaseError:
            # depending on the order that django processes models during "syncdb,"
            # MetadataVersion may not exist yet in the db.
            # that's okay - this only has to work during "runserver"
            print "database error"
            pass
        except UtilsDatabaseError:
            print "the other kind of database error"
            pass

 