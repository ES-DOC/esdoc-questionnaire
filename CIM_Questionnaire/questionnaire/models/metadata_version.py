
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
from django.conf import settings
from lxml import etree as et

import os
import re

from CIM_Questionnaire.questionnaire.models import MetadataModelProxy, MetadataStandardCategoryProxy, MetadataStandardPropertyProxy
from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes, MetadataAtomicFieldTypes, OverwriteStorage
from CIM_Questionnaire.questionnaire.utils import APP_LABEL, LIL_STRING, SMALL_STRING, BIG_STRING, HUGE_STRING
from CIM_Questionnaire.questionnaire.utils import validate_file_extension, validate_file_schema, validate_no_spaces, validate_no_bad_chars, xpath_fix, remove_spaces_and_linebreaks, get_index

UPLOAD_DIR  = "versions"
UPLOAD_PATH = os.path.join(APP_LABEL,UPLOAD_DIR)    # this is a relative path (will be concatenated w/ MEDIA_ROOT by FileField)

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
        unique_together = ("name", "version")
        # this is one of the few classes that I allow admin access to, so give it pretty names:
        verbose_name        = 'Metadata Version'
        verbose_name_plural = 'Metadata Versions'

    name = models.CharField(max_length=SMALL_STRING, blank=False, null=False, validators=[validate_no_spaces, validate_no_bad_chars])
    version = models.CharField(max_length=SMALL_STRING, blank=False, null=False, validators=[validate_no_spaces, validate_no_bad_chars])
    key = models.CharField(max_length=SMALL_STRING, blank=False, null=False, editable=False)

    url = models.URLField(blank=False)
    url.help_text = "This URL is used as the namespace of serialized documents"
    file = models.FileField(upload_to=UPLOAD_PATH, validators=[validate_version_file_extension,validate_version_file_schema], storage=OverwriteStorage(), max_length=SMALL_STRING)
    file.help_text = "Note that files with the same names will be overwritten"
    categorization  = models.ForeignKey("MetadataCategorization", blank=True, null=True, related_name="versions", on_delete=models.SET_NULL)
    categorization.help_text = "A version can only have a single categorization."

    registered = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        super(MetadataVersion, self).__init__(*args, **kwargs)
        self._original_key = self.get_key()

    def save(self, *args, **kwargs):
        _current_key = self.get_key()
        if _current_key != self._original_key:
            self.key = self.get_key()
        super(MetadataVersion, self).save(*args, **kwargs)
        self._original_key = self.key

    # def save(self, *args, **kwargs):
    #     if self.pk:
    #         existing_version = MetadataVersion.objects.get(pk=self.pk)
    #         if existing_version.name != self.name or existing_version.version != self.version
    #             self.key = u"%s_%s" % (self.name, self.version)
    #     else:
    #         self.key = u"%s_%s" % (self.name, self.version)
    #     super(MetadataVersion, self).save(*args, **kwargs)

    def __unicode__(self):

        if self.name:
            if self.version:
                return u"%s [%s]" % (self.name, self.version)
            else:
                return u'%s' % (self.name)
        else:
            return u'%s' % (os.path.basename(self.file.name))

    def clean(self):
        # force name to be lowercase
        # this avoids hacky methods of ensuring case-insensitive uniqueness
        # this also allows me to query the db w/out using the '__iexact' qualifier, which should reduce db hits
        self.name = self.name.lower()

    def get_key(self):
        return u"%s_%s" % (self.name, self.version)

    def register(self, **kwargs):

        request = kwargs.pop("request",None)

        try:
            self.file.open()
            version_content = et.parse(self.file)
            self.file.close()
        except IOError:
            msg = "Error opening file: %s" % self.file
            if request:
                messages.add_message(request, messages.ERROR, msg)
                return

        recategorization_needed = False

        old_model_proxies = list(self.model_proxies.all())  # list forces qs evaluation immediately
        new_model_proxies = []

        for i, model_proxy in enumerate(xpath_fix(version_content, "//classes/class")):

            model_proxy_version = self
            model_proxy_name = xpath_fix(model_proxy, "name/text()")[0]
            model_proxy_stereotype = get_index(xpath_fix(model_proxy, "@stereotype"), 0)
            model_proxy_namespace = get_index(xpath_fix(model_proxy, "@namespace"), 0)
            model_proxy_package = get_index(xpath_fix(model_proxy, "@package"), 0)
            model_proxy_documentation = get_index(xpath_fix(model_proxy, "description/text()"), 0)
            if model_proxy_documentation:
                model_proxy_documentation = remove_spaces_and_linebreaks(model_proxy_documentation)
            else:
                model_proxy_documentation = u""

            (new_model_proxy, created_model_proxy) = MetadataModelProxy.objects.get_or_create(
                version = model_proxy_version,
                name = model_proxy_name,
            )

            if created_model_proxy:
                recategorization_needed = True

            new_model_proxy.order = i
            new_model_proxy.stereotype = model_proxy_stereotype
            new_model_proxy.namespace = model_proxy_namespace
            new_model_proxy.package = model_proxy_package
            new_model_proxy.documentation = model_proxy_documentation
            new_model_proxy.save()
            new_model_proxies.append(new_model_proxy)

            old_property_proxies = list(new_model_proxy.standard_properties.all())  # list forces qs evaluation immediately
            new_property_proxies = []

            for j, property_proxy in enumerate(xpath_fix(model_proxy, "attributes/attribute")):

                property_proxy_name = re.sub(r'\.', '_', str(xpath_fix(property_proxy, "name/text()")[0]))
                property_proxy_field_type = xpath_fix(property_proxy, "type/text()")[0]
                property_proxy_is_label = get_index(xpath_fix(property_proxy, "@is_label"), 0)
                property_proxy_stereotype = get_index(xpath_fix(property_proxy, "@stereotype"), 0)
                property_proxy_namespace = get_index(xpath_fix(property_proxy, "@namespace"), 0)
                property_proxy_required = get_index(xpath_fix(property_proxy, "@required"), 0)
                property_proxy_documentation = get_index(xpath_fix(property_proxy, "description/text()"), 0)
                if property_proxy_documentation:
                    property_proxy_documentation = remove_spaces_and_linebreaks(property_proxy_documentation)
                else:
                    property_proxy_documentation = u""
                property_proxy_atomic_type = get_index(xpath_fix(property_proxy, "atomic/atomic_type/text()"), 0)
                if property_proxy_atomic_type:
                    if property_proxy_atomic_type == u"STRING":
                        property_proxy_atomic_type = u"DEFAULT"
                    property_proxy_atomic_type = MetadataAtomicFieldTypes.get(property_proxy_atomic_type)
                property_proxy_enumeration_choices = []
                for property_proxy_enumeration_choice in xpath_fix(property_proxy, "enumeration/choice"):
                    property_proxy_enumeration_choices.append(xpath_fix(property_proxy_enumeration_choice, "text()")[0])
                property_proxy_relationship_cardinality_min = get_index(xpath_fix(property_proxy, "relationship/cardinality/@min"), 0)
                property_proxy_relationship_cardinality_max = get_index(xpath_fix(property_proxy, "relationship/cardinality/@max"), 0)
                property_proxy_relationship_target_name = get_index(xpath_fix(property_proxy, "relationship/target/text()"), 0)
                if property_proxy_relationship_cardinality_min and property_proxy_relationship_cardinality_max:
                    property_proxy_relationship_cardinality = u"%s|%s" % (property_proxy_relationship_cardinality_min, property_proxy_relationship_cardinality_max)
                else:
                    property_proxy_relationship_cardinality = u""

                (new_property_proxy, created_property) = MetadataStandardPropertyProxy.objects.get_or_create(
                    model_proxy=new_model_proxy,
                    name=property_proxy_name,
                    field_type=property_proxy_field_type
                )

                if created_property:
                    recategorization_needed = True

                new_property_proxy.order = j
                new_property_proxy.is_label = property_proxy_is_label == "true"
                new_property_proxy.stereotype = property_proxy_stereotype
                new_property_proxy.namespace = property_proxy_namespace
                new_property_proxy.required = bool(property_proxy_required and property_proxy_required.lower() == "true")
                new_property_proxy.documentation = property_proxy_documentation
                new_property_proxy.atomic_type = property_proxy_atomic_type
                new_property_proxy.enumeration_choices = "|".join(property_proxy_enumeration_choices)
                new_property_proxy.relationship_cardinality = property_proxy_relationship_cardinality
                new_property_proxy.relationship_target_name = property_proxy_relationship_target_name
                new_property_proxy.save()
                new_property_proxies.append(new_property_proxy)

            # if there's anything in old_property_proxies not in new_property_proxies, delete it
            for old_property_proxy in old_property_proxies:
                if old_property_proxy not in new_property_proxies:
                    old_property_proxy.delete()

            new_model_proxy.save()  # save again for the m2m relationship

        # if there's anything in old_model_proxies not in new_model_proxies, delete it
        for old_model_proxy in old_model_proxies:
            if old_model_proxy not in new_model_proxies:
                old_model_proxy.delete()


        # reset whatever's left
        for model_proxy in MetadataModelProxy.objects.filter(version=self):
            for property_proxy in model_proxy.standard_properties.all():
                property_proxy.reset()
                property_proxy.save()

        if recategorization_needed:
            msg = "Since you are re-registering an existing version, you will also have to re-register the corresponding categorization"
            if request:
                messages.add_message(request, messages.WARNING, msg)

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
            version.file.delete(save=False)    # save=False prevents model from re-saving itself
            # TODO: CHECK THAT FILE.URL IS THE RIGHT WAY TO PRINT THIS
            print "deleted %s" % (version.file.url)
        except:
            pass