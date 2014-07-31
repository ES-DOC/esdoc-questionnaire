
####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Dec 18, 2013 1:05:22 PM"

"""
.. module:: questionnaire_version

Summary of module goes here

"""

from django.db import models
from django.contrib import messages

import os
import re

from questionnaire.utils    import *
from questionnaire.models   import *
from questionnaire.fields   import *

UPLOAD_DIR  = "versions"
UPLOAD_PATH = os.path.join(APP_LABEL,UPLOAD_DIR)    # this is a relative path (will be concatenated w/ MEDIA_ROOT by FileFIeld)

def validate_version_file_extension(value):
    valid_extensions = ["xml"]
    return validate_file_extension(value,valid_extensions)

def validate_version_file_schema(value):
    schema_path = os.path.join(settings.STATIC_ROOT,APP_LABEL,"xml/version.xsd")
    return validate_file_schema(value,schema_path)

class MetadataVersion(models.Model):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False
        # this is one of the few classes that I allow admin access to, so give it pretty names:
        verbose_name        = 'Metadata Version'
        verbose_name_plural = 'Metadata Versions'

    
    name            = models.CharField(max_length=SMALL_STRING,blank=False,null=False,unique=True)
    registered      = models.BooleanField(default=False)
    url             = models.URLField(blank=True)
    file            = models.FileField(upload_to=UPLOAD_PATH,validators=[validate_version_file_extension,validate_version_file_schema],storage=OverwriteStorage())
    file.help_text  = "Note that files with the same names will be overwritten"
    categorization  = models.ForeignKey("MetadataCategorization",blank=True,null=True,related_name="versions",on_delete=models.SET_NULL)
    categorization.help_text = "A version can only have a single categorization."


    def __unicode__(self):

        if self.name:
            return u'%s' % (self.name)
        else:
            return u'%s' % (os.path.basename(self.file.name))

    def clean(self):
        # force name to be lowercase
        # this avoids hacky methods of ensuring case-insensitive uniqueness
        # this also allows me to query the db w/out using the '__iexact' qualifier, which should reduce db hits
        self.name = self.name.lower()

    def register(self,**kwargs):
        request = kwargs.pop("request",None)

        self.file.open()
        try:
            version_content = et.parse(self.file)
        finally:
            self.file.close()

        recategorization_needed = False

        # TODO: SHOULD I DELETE THE EXISTING PROXIES?
        new_model_proxy_kwargs = {
            "version"   : self
        }
        for i, version_model_proxy in enumerate(xpath_fix(version_content,"//classes/class")):
            version_model_proxy_name          = xpath_fix(version_model_proxy,"name/text()")
            version_model_proxy_documentation = xpath_fix(version_model_proxy,"description/text()") or None
            version_model_proxy_stereotype    = xpath_fix(version_model_proxy,"@stereotype") or None

            new_model_proxy_kwargs["name"]              = re.sub(r'\.','_',str(version_model_proxy_name[0]))
            if version_model_proxy_documentation:
                new_model_proxy_kwargs["documentation"] = version_model_proxy_documentation[0]
            if version_model_proxy_stereotype:
                new_model_proxy_kwargs["stereotype"]    = version_model_proxy_stereotype[0]
            new_model_proxy_kwargs["order"]             = i

            (new_model_proxy,created_model) = MetadataModelProxy.objects.get_or_create(**new_model_proxy_kwargs)
            if not created_model:
                recategorization_needed = True
                # TODO: THIS WILL DELETE ASSOCIATED PROPERTY CUSTOMIZATIONS WHICH IS A REALLY BAD IDEA!
                # delete all old properties (going to replace them during this registration)...
                old_model_proxy_properties = new_model_proxy.standard_properties.all()
                old_model_proxy_properties.delete()
           
            new_standard_property_proxy_kwargs = {
                "model_proxy"   : new_model_proxy
            }
            for j, version_property_proxy in enumerate(xpath_fix(version_model_proxy,"attributes/attribute")):
                version_property_proxy_name = xpath_fix(version_property_proxy,"name/text()")
                version_property_proxy_type = xpath_fix(version_property_proxy,"type/text()")
                version_property_proxy_documentation = xpath_fix(version_property_proxy,"description/text()") or None
                version_property_proxy_is_label = xpath_fix(version_property_proxy,"@is_label") or ["false"]
                atomic_type = xpath_fix(version_property_proxy,"atomic/atomic_type/text()") or None
                enumeration_choices = []
                relationship_cardinality_min = xpath_fix(version_property_proxy,"relationship/cardinality/@min")
                relationship_cardinality_max = xpath_fix(version_property_proxy,"relationship/cardinality/@max")
                relationship_target_name = xpath_fix(version_property_proxy,"relationship/target/text()")
                for version_property_proxy_enumeration_choice in xpath_fix(version_property_proxy,"enumeration/choice"):
                    enumeration_choices.append(xpath_fix(version_property_proxy_enumeration_choice,"text()")[0])
                new_standard_property_proxy_kwargs["field_type"] = MetadataFieldTypes.get(version_property_proxy_type[0])
                new_standard_property_proxy_kwargs["name"] = re.sub(r'\.','_',str(version_property_proxy_name[0]))
                if version_property_proxy_documentation:
                    new_standard_property_proxy_kwargs["documentation"] = version_property_proxy_documentation[0]
                new_standard_property_proxy_kwargs["order"] = j
                new_standard_property_proxy_kwargs["is_label"] = bool(version_property_proxy_is_label[0].lower()=="true")
                if atomic_type:
                    atomic_type = atomic_type[0]
                    if atomic_type == u"STRING":
                        atomic_type = "DEFAULT"
                    new_standard_property_proxy_kwargs["atomic_type"] = MetadataAtomicFieldTypes.get(atomic_type)
                else:
                    new_standard_property_proxy_kwargs.pop("atomic_type",None)
                new_standard_property_proxy_kwargs["enumeration_choices"]   = "|".join(enumeration_choices)
                if relationship_cardinality_min and relationship_cardinality_max:
                    new_standard_property_proxy_kwargs["relationship_cardinality"] = "%s|%s"%(relationship_cardinality_min[0],relationship_cardinality_max[0])
                if relationship_target_name:
                    new_standard_property_proxy_kwargs["relationship_target_name"] = relationship_target_name[0]

                (new_standard_property_proxy,created_property) = MetadataStandardPropertyProxy.objects.get_or_create(**new_standard_property_proxy_kwargs)
                new_standard_property_proxy.save()


            new_model_proxy.save()
        
        for model_proxy in MetadataModelProxy.objects.filter(version=self):
            for property_proxy in model_proxy.standard_properties.all():
                property_proxy.reset()
                property_proxy.save()
                
        if recategorization_needed:
            msg = "Since you are re-registering an existing version, you will also have to re-register the corresponding categorization"
            if request:
                messages.add_message(request, messages.WARNING, msg)
            else:
                print msg

        self.registered = True
            
    def unregister(self,**kwargs):
        request = kwargs.pop("request",None)

        if not self.registered:

            msg = "This version is not currently registered.  No action was taken."
            if request:
                messages.add_message(request, messages.WARNING, msg)
            else:
                print msg
        else:

            for model in self.model_proxies.all():
                model.delete()
            self.registered = False

from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

@receiver(post_save, sender=MetadataVersion)
def project_post_save(sender, **kwargs):
    created = kwargs.pop("created",True)
    version = kwargs.pop("instance",None)
    # TODO: DON'T THINK I WANT TO AUTOMATICALLY REGISTER VERSION MODELS, RIGHT?
    pass

@receiver(post_delete, sender=MetadataVersion)
def project_post_delete(sender, **kwargs):
    version = kwargs.pop("instance",None)
    if version:
        try:
            self.file.delete(save=False)    # save=False prevents model from re-saving itself
            # TODO: CHECK THAT FILE.URL IS THE RIGHT WAY TO PRINT THIS
            print "deleted %s" % (self.file.url)
        except:
            pass
