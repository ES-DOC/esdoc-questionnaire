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
from django.core.exceptions import ValidationError
from lxml import etree as et
from uuid import uuid4
import os
import re

from Q.questionnaire import APP_LABEL, q_logger
from Q.questionnaire.q_fields import QFileField, QVersionField, QPropertyTypes, QAtomicPropertyTypes
from Q.questionnaire.models.models_customizations import QModelCustomization
from Q.questionnaire.models.models_proxies import QModelProxy, QStandardPropertyProxy
from Q.questionnaire.q_utils import QError, CIMTypes, validate_file_extension, validate_file_schema, validate_no_spaces, validate_no_bad_chars, xpath_fix, remove_spaces_and_linebreaks, get_index
from Q.questionnaire.q_fields import Version
from Q.questionnaire.q_constants import *

###################
# local constants #
###################

UPLOAD_DIR = "ontologies"
UPLOAD_PATH = os.path.join(APP_LABEL, UPLOAD_DIR)  # this will be concatenated w/ MEDIA_ROOT by FileField

####################
# local validators #
####################

# these are no longer being used, b/c file validation is dependant on what type of ontology this is (CIM1 vs CIM2)
# therefore, validation takes place w/in the "clean" fn - when I have access to an instance's type as well as its file

def validate_ontology_file_extension(value):
    valid_extensions = ["xml"]
    return validate_file_extension(value, valid_extensions)

def validate_ontology_file_schema(value):
    schema_path = os.path.join(settings.STATIC_ROOT, APP_LABEL, "xml/ontology.xsd")
    return validate_file_schema(value,schema_path)


###########
# signals #
###########

registered_ontology_signal = Signal(providing_args=["realization", "customization", ])

###################
# some helper fns #
###################

def get_name_and_version_from_key(key):
    """
    given a string representing some QOntology key,
    splits it into its constituent parts: a name and a version
    note that the version in the key can be underspecified
    (for example, "1.10" should match "1.10.0"
    :param key:
    :return:
    """
    match = re.match("^(.*)_(\d+\.\d+\.\d+|\d+\.\d+|\d+)$", key)  # not the most elegant regex, but you get the point

    if not match:
        msg = "'{0}' is an invalid key; it should be of the format 'name_version'".format(key)
        raise QError(msg)

    name, underspecified_version = match.groups()
    version = Version(underspecified_version).fully_specified()

    return name, version

####################
# the actual class #
####################

class QOntologyQuerySet(models.QuerySet):
    """
    As of Django 1.7 I can use custom querysets as managers
    to ensure that these custom methods are chainable
    whoo-hoo
    """

    def registered(self):
        return self.filter(is_registered=True)

    def filter_by_key(self, key):
        """
        returns a QOntology matching a given key; owever, that key can be underspecified.
        (see "get_name_and_version_from_key" above)
        :param key: QOntology key
        :return: QOntology or None
        """

        name, version = get_name_and_version_from_key(key)
        # this should only return a single object, but I use 'filter' instead of 'get'
        # so that I can still chain the return value
        return self.filter(name=name, version=version)

class QOntology(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "Questionnaire Ontology"
        verbose_name_plural = "Questionnaire Ontologies"
        unique_together = ("name", "version")

    objects = QOntologyQuerySet.as_manager()

    guid = models.UUIDField(default=uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    name = models.CharField(max_length=LIL_STRING, blank=False, validators=[validate_no_spaces, validate_no_bad_chars])
    version = QVersionField(blank=False)
    description = models.TextField(blank=True, null=True)
    description.help_text = "This may be overwritten by any descriptive text found in the QXML file."

    # I need to handle CIM 1.x differently than CIM 2.x
    type = models.CharField(max_length=LIL_STRING, blank=False, choices=[(ct.get_type(), ct.get_name()) for ct in CIMTypes])

    # "key" is a way of uniquely but intuitively referring to this ontology in a URL and elsewhere
    key = models.CharField(max_length=SMALL_STRING, blank=False, editable=False)

    url = models.URLField(blank=False)
    url.help_text = "This URL might be used as the namespace of serialized XML documents"
    file = QFileField(blank=False, upload_to=UPLOAD_PATH)

    categorization = models.ForeignKey("QCategorization", blank=True, null=True, related_name="ontologies", on_delete=models.SET_NULL)

    is_registered = models.BooleanField(blank=False, default=False)
    last_registered_version = QVersionField(blank=True, null=True)  # used to enforce only re-registering "patch" releases

    def __unicode__(self):

        if self.version:
            return u"%s [%s]" % (self.name, self.version)
        else:
            return u"%s" % (self.name)

    def __init__(self, *args, **kwargs):
        super(QOntology, self).__init__(*args, **kwargs)
        self._original_key = self.key

    def save(self, *args, **kwargs):
        _current_key = self.get_key()
        if _current_key != self._original_key:
            self.key = _current_key
        super(QOntology, self).save(*args, **kwargs)
        self._original_key = self.key

    def clean(self):
        # force name to be lowercase...
        # this avoids hacky methods of ensuring case-insensitive uniqueness
        self.name = self.name.lower()

        # also, validate the file according to the QXML Schema...
        # (I can't set up this validation in the field definition)
        # (b/c the specific schema to validate against changes based on the type of QOntology)
        if self.is_cim2():
            schema_path = os.path.join(settings.STATIC_ROOT, APP_LABEL, "xml/qxml_2.xsd")
        elif self.is_cim1():
            schema_path = os.path.join(settings.STATIC_ROOT, APP_LABEL, "xml/qxml_1.xsd")
        else:
            msg = "Unable to determine the ontology type"
            raise QError(msg)
        try:
            validate_file_schema(self.file, schema_path)
        except ValidationError as e:
            raise ValidationError({"file": str(e)})

        # now do normal cleaning...
        return super(QOntology, self).clean()

    def get_key(self):
        return "{0}_{1}".format(self.name, self.version)

    def is_cim1(self):
        return self.type == CIMTypes.CIM1

    def is_cim2(self):
        return self.type == CIMTypes.CIM2

    def register(self, **kwargs):

        request = kwargs.get("request")

        if self.last_registered_version:
            last_registered_version_major = self.last_registered_version.get_version_major()
            last_registered_version_minor = self.last_registered_version.get_version_minor()
            current_version_major = self.version.get_version_major()
            current_version_minor = self.version.get_version_minor()
            if last_registered_version_major != current_version_major or last_registered_version_minor != current_version_minor:
                if request:
                    msg = "You are not allowed to re-register anything other than a new patch version."
                    messages.add_message(request, messages.ERROR, msg)
                return

        try:
            if self.is_cim2():
                self.register_cim2(**kwargs)

            elif self.is_cim1():
                self.register_cim1(**kwargs)

            else:
                msg = "Unable to determine the ontology type"
                raise QError(msg)
        except Exception as e:
            # if something goes wrong, record it in the logs, return immediately & don't set "is_registered" to True
            # (but don't crash)
            q_logger.error(e)
            if request:
                messages.add_message(request, messages.ERROR, str(e))
            return

        self.is_registered = True
        self.last_registered_version = self.version

        # if I re-registered an ontology and there were existing customizations associated w/ it
        # then I better update those customizations so that they have the right content
        customizations_to_update = [customization for customization in QModelCustomization.objects.filter(proxy__ontology=self) if customization.proxy.is_document()]
        for customization in customizations_to_update:
            registered_ontology_signal.send_robust(
                sender=self,
                customization=customization
            )

        # TODO: DO THE SAME THING FOR EXISTING DOCUMENTATIONS

    def register_cim1(self, **kwargs):

        request = kwargs.pop("request", None)

        try:
            self.file.open()
            ontology_content = et.parse(self.file)
            self.file.close()
        except IOError as e:
            msg = "Error opening file: %s" % self.file
            if request:
                messages.add_message(request, messages.ERROR, msg)
            raise e

        recategorization_needed = False

        # name can be anything...
        ontology_name = get_index(xpath_fix(ontology_content, "name/text()"), 0)
        # version is not specified in CIM1.x
        ontology_version = get_index(xpath_fix(ontology_content, "version/text()"), 0)
        # description can overwrite the instance field...
        ontology_description = get_index(xpath_fix(ontology_content, "description/text()"), 0)
        if ontology_description:
            self.description = remove_spaces_and_linebreaks(ontology_description)

        old_model_proxies = list(self.model_proxies.all())  # list forces qs evaluation immediately
        new_model_proxies = []

        for i, model_proxy in enumerate(xpath_fix(ontology_content, "//classes/class")):

            model_proxy_ontology = self
            model_proxy_name = xpath_fix(model_proxy, "name/text()")[0]
            model_proxy_stereotype = get_index(xpath_fix(model_proxy, "@stereotype"), 0)
            model_proxy_namespace = get_index(xpath_fix(model_proxy, "@namespace"), 0)
            model_proxy_package = get_index(xpath_fix(model_proxy, "@package"), 0)
            model_proxy_documentation = get_index(xpath_fix(model_proxy, "description/text()"), 0)
            if model_proxy_documentation:
                model_proxy_documentation = remove_spaces_and_linebreaks(model_proxy_documentation)
            else:
                model_proxy_documentation = u""

            (new_model_proxy, created_model_proxy) = QModelProxy.objects.get_or_create(
                ontology=model_proxy_ontology,
                name=model_proxy_name,
            )

            if created_model_proxy:
                recategorization_needed = True

            new_model_proxy.order = i + 1
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
                    property_proxy_atomic_type = QAtomicPropertyTypes.get(property_proxy_atomic_type)
                property_proxy_enumeration_choices = []
                for property_proxy_enumeration_choice in xpath_fix(property_proxy, "enumeration/choice"):
                    property_proxy_enumeration_choices.append(xpath_fix(property_proxy_enumeration_choice, "text()")[0])
                property_proxy_relationship_cardinality_min = get_index(xpath_fix(property_proxy, "relationship/cardinality/@min"), 0)
                property_proxy_relationship_cardinality_max = get_index(xpath_fix(property_proxy, "relationship/cardinality/@max"), 0)
                property_proxy_relationship_target_name = get_index(xpath_fix(property_proxy, "relationship/target/text()"), 0)

                (new_property_proxy, created_property) = QStandardPropertyProxy.objects.get_or_create(
                    model_proxy=new_model_proxy,
                    name=property_proxy_name,
                    field_type=property_proxy_field_type
                )

                if created_property:
                    recategorization_needed = True

                new_property_proxy.order = j + 1
                new_property_proxy.documentation = property_proxy_documentation
                new_property_proxy.is_label = property_proxy_is_label == "true"
                new_property_proxy.stereotype = property_proxy_stereotype
                new_property_proxy.namespace = property_proxy_namespace
                if property_proxy_field_type == QPropertyTypes.RELATIONSHIP:
                    if property_proxy_relationship_cardinality_min and property_proxy_relationship_cardinality_max:
                        new_property_proxy.cardinality = u"%s|%s" % (property_proxy_relationship_cardinality_min, property_proxy_relationship_cardinality_max)
                else:
                    if property_proxy_required:
                        new_property_proxy.cardinality = u"1|1"
                new_property_proxy.atomic_type = property_proxy_atomic_type
                new_property_proxy.enumeration_choices = "|".join(property_proxy_enumeration_choices)
                if property_proxy_relationship_target_name:
                    new_property_proxy.relationship_target_names = property_proxy_relationship_target_name
                else:
                    new_property_proxy.property_proxy_relationship_target_names = ""
                new_property_proxy.save()
                new_property_proxies.append(new_property_proxy)

            # if there's anything in old_property_proxies not in new_property_proxies, delete it
            for old_property_proxy in old_property_proxies:
                if old_property_proxy not in new_property_proxies:
                    old_property_proxy.delete()

            new_model_proxy.save()  # save parent again for the m2m relationship

        # if there's anything in old_model_proxies not in new_model_proxies, delete it
        for old_model_proxy in old_model_proxies:
            if old_model_proxy not in new_model_proxies:
                old_model_proxy.delete()

        # reset whatever's left
        for model_proxy in QModelProxy.objects.filter(ontology=self):
            for property_proxy in model_proxy.standard_properties.all():
                property_proxy.reset()
                property_proxy.save()

        if recategorization_needed:
            msg = "Since you are re-registering an existing version, you will also have to re-register the corresponding categorization"
            if request:
                messages.add_message(request, messages.WARNING, msg)

    def register_cim2(self, **kwargs):

        request = kwargs.pop("request", None)

        try:
            self.file.open()
            ontology_content = et.parse(self.file)
            self.file.close()
        except IOError as e:
            msg = "Error opening file: %s" % self.file
            if request:
                messages.add_message(request, messages.ERROR, msg)
            raise e

        recategorization_needed = False

        # name can be anything...
        ontology_name = get_index(xpath_fix(ontology_content, "name/text()"), 0)
        # version should match(ish) the instance field...
        ontology_version = get_index(xpath_fix(ontology_content, "version/text()"), 0)
        if self.version.major() != Version(ontology_version).major():
            msg = "The major version of this ontology instance does not match the major version of the QXML file"
            if request:
                messages.add_message(request, messages.WARNING, msg)

        # description can overwrite the instance field...
        ontology_description = get_index(xpath_fix(ontology_content, "description/text()"), 0)
        if ontology_description:
            self.description = remove_spaces_and_linebreaks(ontology_description)

        old_model_proxies = list(self.model_proxies.all())  # list forces qs evaluation immediately
        new_model_proxies = []

        for i, model_proxy in enumerate(xpath_fix(ontology_content, "//classes/class")):

            model_proxy_ontology = self
            model_proxy_name = xpath_fix(model_proxy, "name/text()")[0]
            model_proxy_package = xpath_fix(model_proxy, "@package")[0]
            model_proxy_stereotype = get_index(xpath_fix(model_proxy, "@stereotype"), 0)
            model_proxy_documentation = get_index(xpath_fix(model_proxy, "description/text()"), 0)
            if model_proxy_documentation:
                model_proxy_documentation = remove_spaces_and_linebreaks(model_proxy_documentation)
            else:
                model_proxy_documentation = u""

            (new_model_proxy, created_model_proxy) = QModelProxy.objects.get_or_create(
                package=model_proxy_package,
                ontology=model_proxy_ontology,
                name=model_proxy_name,
            )

            if created_model_proxy:
                recategorization_needed = True

            new_model_proxy.order = i + 1
            new_model_proxy.stereotype = model_proxy_stereotype
            new_model_proxy.documentation = model_proxy_documentation
            new_model_proxy.save()
            new_model_proxies.append(new_model_proxy)

            old_property_proxies = list(new_model_proxy.standard_properties.all())  # list forces qs evaluation immediately
            new_property_proxies = []

            for j, property_proxy in enumerate(xpath_fix(model_proxy, "attributes/attribute")):

                property_proxy_name = re.sub(r'\.', '_', str(xpath_fix(property_proxy, "name/text()")[0]))
                property_proxy_field_type = xpath_fix(property_proxy, "type/text()")[0]
                # TODO: I AM NOT CURRENTLY USING PACKAGES FOR PROPERTIES, SHOULD I?
                property_proxy_package = get_index(xpath_fix(property_proxy, "@package"), 0)
                property_proxy_stereotype = get_index(xpath_fix(property_proxy, "@stereotype"), 0)
                # TODO: MAY NEED TO REVISIT HOW LABELS WORK IN CIM2
                property_proxy_is_label = get_index(xpath_fix(property_proxy, "@is_label"), 0)
                property_proxy_documentation = get_index(xpath_fix(property_proxy, "description/text()"), 0)
                if property_proxy_documentation:
                    property_proxy_documentation = remove_spaces_and_linebreaks(property_proxy_documentation)
                else:
                    property_proxy_documentation = u""
                property_proxy_cardinality_min = get_index(xpath_fix(property_proxy, "cardinality/@min"), 0)
                property_proxy_cardinality_max = get_index(xpath_fix(property_proxy, "cardinality/@max"), 0)
                # atomic properties...
                property_proxy_atomic_type = get_index(xpath_fix(property_proxy, "atomic/atomic_type/text()"), 0)
                if property_proxy_atomic_type:
                    if property_proxy_atomic_type == u"STRING":
                        property_proxy_atomic_type = u"DEFAULT"
                    property_proxy_atomic_type = QAtomicPropertyTypes.get(property_proxy_atomic_type)
                # enumeration properties...
                property_proxy_enumeration_is_open = get_index(xpath_fix(property_proxy, "enumeration/@is_open"), 0)
                property_proxy_enumeration_is_multi = get_index(xpath_fix(property_proxy, "enumeration/@is_multi"), 0)
                property_proxy_enumeration_is_nillable = get_index(xpath_fix(property_proxy, "enumeration/@is_nillable"), 0)
                property_proxy_enumeration_choices = []
                for property_proxy_enumeration_choice in xpath_fix(property_proxy, "enumeration/choices/choice"):
                    # TODO: HOW DO I COPE W/ ENUMERATION CHOICES W/ DESCRIPTIONS ?
                    property_proxy_enumeration_choices.append(xpath_fix(property_proxy_enumeration_choice, "value/text()")[0])
                # relationship properties...
                property_proxy_relationship_target_names = "|".join(
                    # note that each target_name is fully-qualified
                    xpath_fix(property_proxy, "relationship/targets/target/text()")
                )

                (new_property_proxy, created_property) = QStandardPropertyProxy.objects.get_or_create(
                    model_proxy=new_model_proxy,
                    name=property_proxy_name,
                    field_type=property_proxy_field_type
                )

                if created_property:
                    recategorization_needed = True

                new_property_proxy.order = j + 1
                new_property_proxy.package = property_proxy_package
                new_property_proxy.documentation = property_proxy_documentation
                new_property_proxy.is_label = property_proxy_is_label == "true"
                new_property_proxy.stereotype = property_proxy_stereotype
                new_property_proxy.cardinality = "{0}|{1}".format(
                    property_proxy_cardinality_min,
                    property_proxy_cardinality_max if property_proxy_cardinality_max != "N" else "*",
                )
                new_property_proxy.atomic_type = property_proxy_atomic_type
                if property_proxy_enumeration_is_open:
                    new_property_proxy.enumeration_is_open = property_proxy_enumeration_is_open == "true"
                if property_proxy_enumeration_is_multi:
                    new_property_proxy.enumeration_is_multi = property_proxy_enumeration_is_multi == "true"
                if property_proxy_enumeration_is_nillable:
                    new_property_proxy.enumeration_is_nillable = property_proxy_enumeration_is_nillable == "true"
                new_property_proxy.enumeration_choices = "|".join(property_proxy_enumeration_choices)
                new_property_proxy.relationship_target_names = property_proxy_relationship_target_names
                new_property_proxy.save()
                new_property_proxies.append(new_property_proxy)

            # if there's anything in old_property_proxies not in new_property_proxies, delete it
            for old_property_proxy in old_property_proxies:
                if old_property_proxy not in new_property_proxies:
                    old_property_proxy.delete()

            new_model_proxy.save()  # save parent again for the m2m relationship

        # if there's anything in old_model_proxies not in new_model_proxies, delete it
        for old_model_proxy in old_model_proxies:
            if old_model_proxy not in new_model_proxies:
                old_model_proxy.delete()

        # reset whatever's left
        for model_proxy in QModelProxy.objects.filter(ontology=self):
            for property_proxy in model_proxy.standard_properties.all():
                property_proxy.reset()
                property_proxy.save()

        if recategorization_needed:
            msg = "Since you are re-registering an existing version, you will also have to re-register the corresponding categorization"
            if request:
                messages.add_message(request, messages.WARNING, msg)
