####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

from django.db import models
from django.contrib import messages
from django.conf import settings
from django.dispatch import Signal
from django.template.defaultfilters import slugify
from lxml import etree as et
from uuid import uuid4
import os

from Q.questionnaire import APP_LABEL
from Q.questionnaire.q_fields import QFileField, QVersionField, QPropertyTypes, QAtomicPropertyTypes
from Q.questionnaire.models.models_customizations import QModelCustomization
from Q.questionnaire.models.models_proxies import QModelProxy, QStandardPropertyProxy, QScientificPropertyProxy, QScientificCategoryProxy, QComponentProxy
from Q.questionnaire.q_utils import validate_file_extension, validate_file_schema, validate_no_spaces, validate_no_bad_chars, xpath_fix, remove_spaces_and_linebreaks, get_index, QError
from Q.questionnaire.q_constants import *

###################
# local constants #
###################

UPLOAD_DIR = "vocabularies"
UPLOAD_PATH = os.path.join(APP_LABEL, UPLOAD_DIR)  # this will be concatenated w/ MEDIA_ROOT by FileField

DEFAULT_VOCABULARY_KEY = "DEFAULT_VOCABULARY"
DEFAULT_COMPONENT_KEY = "DEFAULT_COMPONENT"

####################
# local validators #
####################

def validate_vocabulary_file_extension(value):
    valid_extensions = ["xml"]
    return validate_file_extension(value, valid_extensions)

def validate_vocabulary_file_schema(value):
    schema_path = os.path.join(settings.STATIC_ROOT, APP_LABEL, "xml/vocabulary.xsd")
    return validate_file_schema(value,schema_path)

###########
# signals #
###########

registered_vocabulary_signal = Signal(providing_args=["realization", "customization", ])

####################
# the actual class #
####################

class QVocabularyQuerySet(models.QuerySet):
    """
    As of Django 1.7 I can use custom querysets as managers
    to ensure that these custom methods are chainable
    whoo-hoo
    """

    def registered(self):
        return self.filter(is_registered=True)


class QVocabulary(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "Questionnaire Vocabulary"
        verbose_name_plural = "Questionnaire Vocabularies"
        unique_together = ("name", "version")
        ordering = ("created", )

    objects = QVocabularyQuerySet.as_manager()

    guid = models.UUIDField(default=uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now_add=True, editable=False)

    name = models.CharField(max_length=LIL_STRING, blank=False, validators=[validate_no_spaces, validate_no_bad_chars])
    version = QVersionField(blank=False)
    description = models.TextField(blank=True, null=True)
    url = models.URLField(blank=False)

    document_type = models.CharField(max_length=LIL_STRING, blank=False, choices=[(dt, dt) for dt in CIM_DOCUMENT_TYPES])

    file = QFileField(blank=False, upload_to=UPLOAD_PATH, validators=[validate_vocabulary_file_extension, validate_vocabulary_file_schema, ])

    is_registered = models.BooleanField(blank=False, default=False)
    last_registered_version = QVersionField(blank=True, null=True)

    def __unicode__(self):

        if self.version:
            return u"%s [%s]" % (self.name, self.version)
        else:
            return u"%s" % (self.name)

    def clean(self):
        # force name to be lowercase
        # this avoids hacky methods of ensuring case-insensitive uniqueness
        self.name = self.name.lower()

    def get_key(self):
        return u"%s" % (self.guid)

    def register(self, **kwargs):

        if not self.document_type:
            msg = "Unable to register a vocabulary without an associated document_type"
            raise QError(msg)

        request = kwargs.pop("request", None)

        try:
            self.file.open()
            vocabulary_content = et.parse(self.file)
            self.file.close()
        except IOError:
            msg = "Error opening file: %s" % self.file
            if request:
                messages.add_message(request, messages.ERROR, msg)
                return

        self.old_component_proxies = list(self.component_proxies.all())  # list forces qs evaluation immediately
        self.new_component_proxies = []
        self.component_order = 0
        for i, component_proxy_node in enumerate(xpath_fix(vocabulary_content,"./component")):
            # rather than loop over all components ("//component"),
            # I do this recursively in order to keep track of the full component hierarchy
            self.create_component_proxy(component_proxy_node)

        # if there's anything in old_component_proxies not in new_component_proxies, delete it
        for old_component_proxy in self.old_component_proxies:
            if old_component_proxy not in self.new_component_proxies:
                old_component_proxy.delete()

        self.is_registered = True
        self.last_registered_version = self.version

        # if I re-registered a vocabulary and there were existing customizations associated w/ it
        # then I better update those customizations so that they have the right content
        customizations_to_update = [customization for customization in QModelCustomization.objects.filter(vocabularies__in=[self.pk])]
        for customization in customizations_to_update:
            registered_vocabulary_signal.send_robust(
                sender=self,
                customization=customization
            )

    def create_component_proxy(self, component_proxy_node, parent_component_proxy=None):
        """
        recursively create component proxies, keeping track of their hierarchy
        :param component_proxy_node:
        :param parent_component_proxy:
        :return:
        """

        self.component_order += 1

        component_proxy_vocabulary = self
        component_proxy_name = get_index(xpath_fix(component_proxy_node, "@name"), 0)
        component_proxy_order = self.component_order
        component_proxy_documentation = get_index(xpath_fix(component_proxy_node, "definition/text()"), 0)
        if component_proxy_documentation:
            component_proxy_documentation = remove_spaces_and_linebreaks(component_proxy_documentation)

        (new_component_proxy, created_component_proxy) = QComponentProxy.objects.get_or_create(
            vocabulary=component_proxy_vocabulary,
            name=component_proxy_name,
            parent=parent_component_proxy
        )

        new_component_proxy.documentation = component_proxy_documentation
        new_component_proxy.order = component_proxy_order
        new_component_proxy.save()

        old_category_proxies = list(new_component_proxy.category_proxies.all())  # list forces qs evaluation immediately
        new_category_proxies = []

        category_proxy_component = new_component_proxy
        for i, category_proxy_node in enumerate(xpath_fix(component_proxy_node, "./parametergroup")):

            category_proxy_name = xpath_fix(category_proxy_node, "@name")[0]
            category_proxy_key = slugify(category_proxy_name)
            category_proxy_order = i + 1
            category_proxy_documentation = get_index(xpath_fix(category_proxy_node, "definition/text()"), 0)
            if category_proxy_documentation:
                category_proxy_documentation = remove_spaces_and_linebreaks(category_proxy_documentation)

            (new_category_proxy, created_category_proxy) = QScientificCategoryProxy.objects.get_or_create(
                component_proxy=category_proxy_component,
                name=category_proxy_name
            )

            new_category_proxy.documentation = category_proxy_documentation
            new_category_proxy.order = category_proxy_order
            new_category_proxy.key = category_proxy_key
            new_category_proxy.save()

            new_category_proxies.append(new_category_proxy)

            old_property_proxies = list(new_category_proxy.properties.all())  # list forces qs evaluation immediately
            new_property_proxies = []

            property_proxy_component = new_component_proxy
            property_proxy_category = new_category_proxy
            for j, property_proxy_node in enumerate(xpath_fix(category_proxy_node, "./parameter")):

                property_proxy_name = get_index(xpath_fix(property_proxy_node, "@name"), 0)
                property_proxy_choice = get_index(xpath_fix(property_proxy_node, "@choice"), 0)
                property_proxy_order = j + 1
                property_proxy_documentation = get_index(xpath_fix(property_proxy_node, "definition/text()"), 0)
                if property_proxy_documentation:
                    property_proxy_documentation = remove_spaces_and_linebreaks(property_proxy_documentation)
                property_proxy_enumeration_values = []
                for property_proxy_enumeration_value in xpath_fix(property_proxy_node, "value"):
                    property_proxy_enumeration_value_name = get_index(xpath_fix(property_proxy_enumeration_value, "@name"), 0)
                    if property_proxy_enumeration_value_name:
                        property_proxy_enumeration_values.append(property_proxy_enumeration_value_name)

                (new_property_proxy, created_property_proxy) = QScientificPropertyProxy.objects.get_or_create(
                    component_proxy=property_proxy_component,
                    category=property_proxy_category,
                    name=property_proxy_name,
                )

                new_property_proxy.choice = property_proxy_choice
                new_property_proxy.documentation = property_proxy_documentation
                new_property_proxy.order = property_proxy_order
                new_property_proxy.enumeration_choices = "|".join(property_proxy_enumeration_values)
                new_property_proxy.save()

                new_property_proxies.append(new_property_proxy)

            # if there's anything in old_property_proxies not in new_property_proxies, delete it
            for old_property_proxy in old_property_proxies:
                if old_property_proxy not in new_property_proxies:
                    old_property_proxy.delete()

            # reset whatever's left
            for property_proxy in QScientificPropertyProxy.objects.filter(component_proxy=new_component_proxy, category=new_category_proxy):
                property_proxy.reset()
                property_proxy.save()

        # if there's anything in old_category_proxies not in new_category_proxies, delete it
        for old_category_proxy in old_category_proxies:
            if old_category_proxy not in new_category_proxies:
                old_category_proxy.delete()

        # recurse
        for child_component_proxy_node in xpath_fix(component_proxy_node, "./component"):
            self.create_component_proxy(child_component_proxy_node, new_component_proxy)

        # (do this last in case any m2m fields are added recursively)
        self.new_component_proxies.append(new_component_proxy)