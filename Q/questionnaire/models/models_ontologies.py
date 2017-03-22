####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.db import models
from django.conf import settings
from django.contrib import messages
from django.dispatch import Signal
from django.utils.translation import ugettext_lazy as _
import re
import os
import json

from Q.questionnaire import APP_LABEL, q_logger
from Q.questionnaire.models.models_proxies import QModelProxy, QCategoryProxy, QPropertyProxy, ProxyTypes, UNCATEGORIZED_CATEGORY_PROXY_NAME, UNCATEGORIZED_CATEGORY_PROXY_PACKAGE, recurse_through_proxies
from Q.questionnaire.q_fields import QVersionField, QFileField, QPropertyTypes, QAtomicTypes
from Q.questionnaire.q_utils import QError, Version, EnumeratedType, EnumeratedTypeList, find_in_sequence, remove_spaces_and_linebreaks, validate_no_spaces, validate_no_bad_chars, validate_file_extension, validate_file_schema
from Q.questionnaire.q_constants import *

# ontologies (schemas & specializations) are defined in QConfig JSON files
# these are constrained by QCONFIG_SCHEMA
# there are some fns at the end of this file to make dealing w/ that content easier

###################
# local constants #
###################

ONTOLOGY_UPLOAD_DIR = "ontologies"
ONTOLOGY_UPLOAD_PATH = os.path.join(APP_LABEL, ONTOLOGY_UPLOAD_DIR)


class QOntologyType(EnumeratedType):

    def __str__(self):
        return "{0}".format(self.get_type())

QOntologyTypes = EnumeratedTypeList([
    QOntologyType("SPECIALIZATION", "Specialization (ie: CMIP6)"),
    QOntologyType("SCHEMA", "Schema (ie: CIM2)"),
])


###########
# signals #
###########

registered_ontology_signal = Signal(providing_args=["realization", "customization", ])

###################
# some helper fns #
###################


def validate_ontology_file_extension(value):
    valid_extensions = ["json"]
    return validate_file_extension(value, valid_extensions)


def validate_ontology_file_schema(value):
    schema_path = os.path.join(settings.STATIC_ROOT, APP_LABEL, "schemas/qconfig_ontology.schema.json")
    return validate_file_schema(value, schema_path)


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
# a custom manager #
####################

class QOntologyQuerySet(models.QuerySet):

    def active(self):
        return self.filter(is_active=True)

    def registered(self):
        return self.filter(is_registered=True)

    def schemas(self):
        return self.filter(ontology_type=QOntologyTypes.SCHEMA.get_type())

    def specializations(self):
        return self.filter(ontology_type=QOntologyTypes.SPECIALIZATION.get_type())

    def has_key(self, key):
        """
        returns a QOntology matching a given key; however, that key can be underspecified.
        (see "get_name_and_version_from_key" above)
        :param key: QOntology key
        :return: QOntology or None
        """
        name, version = get_name_and_version_from_key(key)
        # this should only return a single object, but I use 'filter' instead of 'get'
        # so that I can still chain the return value
        return self.filter(name=name, version=version)


####################
# the actual model #
####################

class QOntology(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "Questionnaire Ontology"
        verbose_name_plural = "Questionnaire Ontologies"
        unique_together = ("name", "version")

    objects = QOntologyQuerySet.as_manager()

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    name = models.CharField(max_length=BIG_STRING, blank=False, validators=[validate_no_spaces, validate_no_bad_chars])
    version = QVersionField(blank=False)
    documentation = models.TextField(blank=True, null=True)
    documentation.help_text = "This may be overwritten by any descriptive text found in the QConfig file."
    url = models.URLField(blank=True, null=True)

    file = QFileField(blank=False, upload_to=ONTOLOGY_UPLOAD_PATH, validators=[validate_ontology_file_extension, validate_ontology_file_schema])

    last_registered_version = QVersionField(blank=True, null=True)  # used to enforce only re-registering "patch" releases

    ontology_type = models.CharField(
        max_length=SMALL_STRING, blank=False,
        choices=[(ot.get_type(), ot.get_name()) for ot in QOntologyTypes],
    )

    is_registered = models.BooleanField(blank=False, default=False)
    is_active = models.BooleanField(blank=False, default=True)

    parent = models.ForeignKey("self", blank=True, null=True, related_name="children", verbose_name="Base Ontology")
    parent.help_text = _(
        "Which existing ontology (if any) is this ontology based upon?"
    )

    def __str__(self):
        return "{0} [{1}]".format(
            self.name,
            self.version
        )

    @property
    def key(self):
        return "{0}_{1}".format(self.name, self.version)

    @property
    def is_schema(self):
        return self.ontology_type == QOntologyTypes.SCHEMA

    @property
    def is_specialization(self):
        return self.ontology_type == QOntologyTypes.SPECIALIZATION

    def get_all_proxies(self, proxy_types=[ProxyTypes.MODEL, ProxyTypes.CATEGORY, ProxyTypes.PROPERTY]):
        all_proxies = set()
        for model_proxy in self.model_proxies.all():
            all_proxies.update(recurse_through_proxies(model_proxy, proxy_types))
        return all_proxies

    def parse_ontology_content(self, ontology_content):

        # 1st do some logical checks on the content...

        # name should match
        ontology_name = ontology_content.get("name")
        if self.name != ontology_name:
            msg = "The name of this ontology instance does not match that found in the QConfig file"
            raise QError(msg)

        # version should match(ish)
        ontology_version = ontology_content.get("version")
        if self.version.major() != Version(ontology_version).major():
            msg = "The major version of this ontology instance does not match that found in the QConfig file"
            raise QError(msg)

        # documentation can be overwritten
        ontology_documentation = ontology_content.get("documentation")
        if ontology_documentation:
            self.documentation = remove_spaces_and_linebreaks(ontology_documentation)

        # type should match...
        ontology_type = QOntologyTypes.get(ontology_content.get("ontology_type"))
        assert ontology_type is not None, "invalid ontology_type specified"
        if self.ontology_type != ontology_type:
            msg = "The ontology_type of this ontology instance does not match that found in the QConfig file"
            raise QError(msg)

        # if specified, parent must match (and it must be specified for SPECIALIZATIONS)
        ontology_base_key = ontology_content.get("ontology_base")
        if ontology_base_key:
            ontology_base = QOntology.objects.has_key(ontology_base_key).first()
            # (self.parent.is_registered will already have been checked by the "register" fn)
            if self.parent != ontology_base:
                msg = "The ontology_base of this ontology instance does not match that found in the QConfig file"
                raise QError(msg)
        elif ontology_type == QOntologyTypes.SPECIALIZATION:
            msg = "A SPECIALIZATION must include an ontology_base"
            raise QError(msg)

        # now create / setup all of the proxies contained in this ontology...

        old_model_proxies = list(self.model_proxies.all())
        new_model_proxies = []

        inherited_classes = ontology_content["classes"]["inherited"]  # inherited classes are included at the start
        excluded_classes = ontology_content["classes"]["excluded"] # excluded classes don't have to be used at all
        defined_classes = ontology_content["classes"]["defined"]  # defined classes are added as normal

        if self.parent:
            inherited_model_proxies = self.parent.model_proxies.in_fully_qualified_names(inherited_classes)
            # AS OF V0.17.0, PROXIES ARE NOT CONSTRAINED BY ONTOLOGY;
            # THEREFORE THERE IS NO NEED TO COPY INHERITED PROXIES ACROSS
            # (THAT'S WHY I DON'T DO ANYTING W/ "inherited_model_proxies" ABOVE)

        for ontology_model_order, ontology_model in enumerate(defined_classes, start=len(new_model_proxies)+1):
            new_model_proxy = self.parse_ontology_content_model(ontology_model, ontology_model_order)
            new_model_proxies.append(new_model_proxy)

        # if there's anything in old_model_proxies not in new_model_proxies, delete it...
        for old_model_proxy in old_model_proxies:
            if old_model_proxy not in new_model_proxies:
                old_model_proxy.delete()

        # reset whatever's left...
        for model_proxy in QModelProxy.objects.filter(ontology=self):
            model_proxy.reset(force_save=True)
            for category_proxy in model_proxy.category_proxies.filter(ontology=self):
                category_proxy.reset(force_save=True)
            for property_proxy in model_proxy.property_proxies.filter(ontology=self):
                property_proxy.reset(force_save=True)

    def parse_ontology_content_model(self, ontology_content, new_model_proxy_order):

        new_model_proxy_name = ontology_content["name"]
        new_model_proxy_package = ontology_content["package"]
        # a SPECIALIZATION model ought to have an explicit id; a SCHEMA model can just create one dynamically
        new_model_proxy_id = ontology_content.get("id", "{}.{}".format(self.key, new_model_proxy_name))

        parent_model_proxy = None
        if self.parent:
            try:
                parent_model_proxy = self.parent.model_proxies.get(package=new_model_proxy_package, name=new_model_proxy_name)
            except QModelProxy.DoesNotExist:
                # not everything in a specialization has to be based on a parent model, right?
                pass

        (new_model_proxy, created_model_proxy) = QModelProxy.objects.get_or_create(
            # these fields are the "defining" ones (other fields can change below w/out creating new proxies)
            ontology=self,
            name=new_model_proxy_name,
            package=new_model_proxy_package,
            cim_id=new_model_proxy_id,
        )

        new_model_proxy.order = new_model_proxy_order
        new_model_proxy.is_document = ontology_content.get("is_document", False)
        new_model_proxy.is_meta = ontology_content.get("is_meta", False)
        new_model_proxy_documentation = ontology_content.get("documentation")
        if new_model_proxy_documentation:
            new_model_proxy.documentation = remove_spaces_and_linebreaks(new_model_proxy_documentation)
        new_model_proxy_label = ontology_content.get("label")
        if new_model_proxy_label is None and parent_model_proxy is not None:
            new_model_proxy_label = parent_model_proxy.label
        new_model_proxy.label = new_model_proxy_label

        new_model_proxy.save()

        # ...now add any categories...

        old_category_proxies = list(new_model_proxy.category_proxies.all())
        new_category_proxies = []

        inherited_categories = ontology_content["categories"]["inherited"]  # inherited categories are included at the start
        excluded_categories = ontology_content["categories"]["excluded"]  # excluded categories don't have to be uesd at all
        defined_categories = ontology_content["categories"]["defined"]  # defined categories are added as normal

        if parent_model_proxy:
            for inherited_category_order, inherited_category_proxy in enumerate(parent_model_proxy.category_proxies.filter(name__in=inherited_categories), start=1):
                new_model_proxy.category_proxies.add(inherited_category_proxy)
                new_category_proxies.append(inherited_category_proxy)
        else:
            assert len(inherited_categories) == 0, "it makes no sense to specify 'inherited_categories' w/out providing a base model"

        for ontology_category_order, ontology_category in enumerate(defined_categories, start=len(new_category_proxies) + 1):
            new_category_proxy = self.parse_ontology_content_category(ontology_category, ontology_category_order, new_model_proxy)
            new_category_proxies.append(new_category_proxy)

        # TODO: ONLY DELETE A category_proxy IF THERE ARE NO OTHER MODELS (FROM ANY ONTOLOGY) LINKED TO IT
        for old_category_proxy in old_category_proxies:
            if old_category_proxy not in new_category_proxies:
                old_category_proxy.delete()

        # (don't forget to create a placeholder category for properties that are uncategorized)
        uncategorized_category_proxy, created_uncategorized_category_proxy = QCategoryProxy.objects.get_or_create(
            ontology=self,
            model_proxy=new_model_proxy,
            name=UNCATEGORIZED_CATEGORY_PROXY_NAME,
            is_uncategorized=True,
        )
        if created_uncategorized_category_proxy:
            uncategorized_category_proxy.order = len(new_category_proxies) + 1
            uncategorized_category_proxy.save()
            new_category_proxies.append(uncategorized_category_proxy)

        # ...now add any properties...

        old_property_proxies = list(new_model_proxy.property_proxies.all())
        new_property_proxies = []

        inherited_properties = ontology_content["properties"]["inherited"]  # inherited properties are included at the start
        excluded_properties = ontology_content["properties"]["excluded"]  # excluded properties don't have to be uesd at all
        defined_properties = ontology_content["properties"]["defined"]  # defined properties are added as normal

        if parent_model_proxy:
            for inherited_property_order, inherited_property_proxy in enumerate(parent_model_proxy.property_proxies.filter(name__in=inherited_properties), start=1):
                new_model_proxy.property_proxies.add(inherited_property_proxy)
                new_property_proxies.append(inherited_property_proxy)
        else:
            assert len(inherited_properties) == 0, "it makes no sense to specify 'inherited_properties' w/out providing a base model"

        for ontology_property_order, ontology_property in enumerate(defined_properties, start=len(new_property_proxies) + 1):
            new_property_proxy = self.parse_ontology_content_property(ontology_property, ontology_property_order, new_model_proxy)
            new_property_proxies.append(new_property_proxy)

        # TODO: ONLY DELETE A property_proxy IF THERE ARE NO OTHER MODELS (FROM ANY ONTOLOGY) LINKED TO IT
        for old_property_proxy in old_property_proxies:
            if old_property_proxy not in new_property_proxies:
                old_property_proxy.delete()

        return new_model_proxy

    def parse_ontology_content_category(self, ontology_content, new_category_proxy_order, model_proxy):
        new_category_proxy_name = ontology_content["name"]
        new_category_proxy_id = ontology_content["id"]

        (new_category_proxy, created_category_proxy) = QCategoryProxy.objects.get_or_create(
            # these fields are the "defining" ones (other fields can change below w/out creating new proxies)
            ontology=self,
            model_proxy=model_proxy,
            name=new_category_proxy_name,
            cim_id=new_category_proxy_id,
        )

        new_category_proxy.order = new_category_proxy_order
        new_category_proxy_documentation = ontology_content.get("documentation")
        if new_category_proxy_documentation:
            new_category_proxy.documentation = remove_spaces_and_linebreaks(new_category_proxy_documentation)

        new_category_proxy.save()

        return new_category_proxy

    def parse_ontology_content_property(self, ontology_content, new_property_proxy_order, model_proxy):

        new_property_proxy_name = ontology_content["name"]
        new_property_proxy_id = ontology_content.get("id")
        new_property_proxy_field_type = QPropertyTypes.get(ontology_content["property_type"])
        assert new_property_proxy_field_type is not None, "invalid property_type specified"

        (new_property_proxy, created_property_proxy) = QPropertyProxy.objects.get_or_create(
            # these fields are the "defining" ones (other fields can change below w/out creating new proxies)
            ontology=self,
            model_proxy=model_proxy,
            name=new_property_proxy_name,
            cim_id=new_property_proxy_id,
            field_type=new_property_proxy_field_type,
        )

        category_id = ontology_content.get("category_id")
        new_property_proxy.category_id = category_id
        new_property_proxy.category_proxy = find_in_sequence(lambda c: c.cim_id == category_id, model_proxy.category_proxies.all())

        new_property_proxy.order = new_property_proxy_order
        new_property_proxy.is_meta = ontology_content.get("is_meta", False)
        new_property_proxy.is_nillable = ontology_content.get("is_nillable", False)
        new_property_proxy.is_hierarchical = ontology_content.get("is_hierarchical", False)
        new_property_proxy_documentation = ontology_content.get("documentation")
        if new_property_proxy_documentation:
            new_property_proxy.documentation = remove_spaces_and_linebreaks(new_property_proxy_documentation)
        new_property_proxy_cardinality = re.split("\.|,", ontology_content.get("cardinality"))  # TODO: DECIDE ONCE-AND-FOR-ALL IF "cardinality" IS SPLIT ON '.' OR ','
        new_property_proxy.cardinality_min = new_property_proxy_cardinality[0]
        new_property_proxy.cardinality_max = new_property_proxy_cardinality[1]
        new_property_proxy.values = ontology_content.get("values")
        if new_property_proxy_field_type == QPropertyTypes.ATOMIC:
            new_property_proxy_atomic_type_type = ontology_content.get("atomic_type")
            if new_property_proxy_atomic_type_type == "STRING":
                new_property_proxy_atomic_type_type = "DEFAULT"
            new_property_proxy_atomic_type = QAtomicTypes.get(new_property_proxy_atomic_type_type)
            assert new_property_proxy_atomic_type is not None, "invalid atomic_type specified"
            new_property_proxy.atomic_type = new_property_proxy_atomic_type
        elif new_property_proxy_field_type == QPropertyTypes.ENUMERATION:
            new_property_proxy.enumeration_is_open = ontology_content.get("enumeration_is_open")
            new_property_proxy.enumeration_choices = ontology_content.get("enumeration_members")
        else:  # new_property_proxy_field_type == QPropertyTypes.RELATIONSHIP
            new_property_proxy.relationship_target_names = ontology_content.get("relationship_targets")  # target_names are set now; target_models are set later in  "QPropertyProxy.reset"

        new_property_proxy.save()

        return new_property_proxy

    def parse_specialization(self, ontology_content, **kwargs):
        request = kwargs.get("request")

        # 1st do some logical checks on the content...

        # name should match the instance field...
        ontology_name = ontology_content.get("name")
        if self.name != ontology_name:
            msg = "The name of this ontology instance does not match the name found in the QConfig file"
            if request:
                messages.add_message(request, messages.WARNING, msg)
            raise QError(msg)

        # version should match(ish) the instance field...
        ontology_version = ontology_content.get("version")
        if self.version.major() != Version(ontology_version).major():
            msg = "The major version of this ontology instance does not match the major version of the QConfig file"
            if request:
                messages.add_message(request, messages.WARNING, msg)
            raise QError(msg)

        # documentation can overwrite the instance field (ie: the field set in the admin interface)...
        ontology_documentation = ontology_content.get("documentation")
        if ontology_documentation:
            self.documentation = remove_spaces_and_linebreaks(ontology_documentation)

        # type must match the instance field...
        ontology_type = QOntologyTypes.get(ontology_content["ontology_type"])
        assert ontology_type is not None, "invalid ontology_type specified"
        if self.ontology_type != ontology_type:
            msg = "This ontology is a {0}, but the content is for a {1}".format(self.ontology_type, ontology_type)
            if request:
                messages.add_message(request, messages.WARNING, msg)
            raise QError(msg)

        # if specified, parent must exist and match the instance field (and it must be specified for SPECIALIZATIONS)...
        ontology_base_key = ontology_content.get("ontology_base")
        if ontology_base_key:
            ontology_base = QOntology.objects.has_key(ontology_base_key).first()
            if ontology_base != self.parent:
                msg = "Invalid key '{0}' specified for 'ontology_base' (expected '{1}')".format(ontology_base_key, self.parent.key)
                if request:
                    messages.add_message(request, messages.WARNING, msg)
                raise QError(msg)
            if not ontology_base.is_registered:
                msg = "ontology_base must be registered before specialization"
                if request:
                    messages.add_message(request, messages.WARNING, msg)
                raise QError(msg)
        elif ontology_type == QOntologyTypes.SPECIALIZATION:
            msg = "A specialization must include an ontology_base"
            if request:
                messages.add_message(request, messages.WARNING, msg)
            raise QError(msg)

        # now create / setup all of the proxies contained in this ontology...

        inherited_classes = get_inherited_classes(ontology_content)  # inherited classes are included at the start
        excluded_classes = get_excluded_classes(ontology_content)  # excluded classes don't have to be used at all
        defined_classes = get_defined_classes(ontology_content)  # defined classes are added as normal

        old_model_proxies = list(self.model_proxies.all())
        new_model_proxies = []

        if self.parent:
            inherited_model_proxies = self.parent.model_proxies.in_fully_qualified_names(inherited_classes)
            # AS OF 0.17.0, PROXIES ARE NOT CONSTRAINED BY ONTOLOGY; THEREFORE INHERITANCE DOESN'T HAVE TO COPY ANYTHING ACROSSS
            # for inherited_model_order, inherited_model_proxy in enumerate(inherited_model_proxies, start=1):
            #     new_model_proxy = self.inherit_model_proxy(inherited_model_proxy, inherited_model_order)
            #     new_model_proxies.append(new_model_proxy)

        for ontology_model_order, ontology_model in enumerate(defined_classes, start=len(new_model_proxies)+1):

            ontology_model_name = ontology_model["name"]
            ontology_model_package = ontology_model["package"]
            # HERE IS ONE DIFFERENCE BETWEEN SPECIALIZATIONS & SCHEMAS...
            # SCHEMA MODELS MUST HAVE EXPLICIT "cim_ids"...
            ontology_model_id = ontology_model.get("id")
            assert ontology_model_id is not None

            (new_model_proxy, created_model_proxy) = QModelProxy.objects.get_or_create(
                # these fields are the "defining" ones (other fields can change w/out creating new proxies)
                ontology=self,
                name=ontology_model_name,
                package=ontology_model_package,
                cim_id=ontology_model_id,
            )

            ontology_class_documentation = ontology_model.get("documentation")
            ontology_class_is_document = ontology_model.get("is_document")
            ontology_class_is_meta = ontology_model.get("is_meta", False)
            ontology_class_label = ontology_model.get("label", None)
            if ontology_class_label is None and self.parent is not None:
                parent_model_proxy = self.parent.model_proxies.get(package=ontology_model_package, name=ontology_model_name)
                ontology_class_label = parent_model_proxy.label

            if ontology_class_documentation:
                new_model_proxy.documentation = remove_spaces_and_linebreaks(ontology_class_documentation)
            new_model_proxy.is_document = ontology_class_is_document
            new_model_proxy.is_meta = ontology_class_is_meta
            new_model_proxy.label = ontology_class_label
            new_model_proxy.order = ontology_model_order

            new_model_proxy.save()
            new_model_proxies.append(new_model_proxy)

            fully_qualified_class_name = "{0}.{1}".format(ontology_model_package, ontology_model_name)

            inherited_categories = get_inherited_categories(ontology_content, fully_qualified_class_name) # inherited categories are included at the start
            excluded_categories = get_excluded_categories(ontology_content, fully_qualified_class_name) # excluded categories don't have to be uesd at all
            defined_categories = get_defined_categories(ontology_content, fully_qualified_class_name) # defined categories are added as normal

            inherited_properties = get_inherited_properties(ontology_content, fully_qualified_class_name) # inherited properties are included at the start
            excluded_properties = get_excluded_properties(ontology_content, fully_qualified_class_name) # excluded properties don't have to be uesd at all
            defined_properties = get_defined_properties(ontology_content, fully_qualified_class_name) # defined properties are added as normal

            old_category_proxies = list(new_model_proxy.category_proxies.all())
            new_category_proxies = []

            old_property_proxies = list(new_model_proxy.property_proxies.all())
            new_property_proxies = []

            if self.parent:
                try:
                    parent_model_proxy = self.parent.model_proxies.get(package=ontology_model_package, name=ontology_model_name)
                    inherited_property_proxies = parent_model_proxy.property_proxies.filter(name__in=inherited_properties)
                    # AS OF 0.17.0, PROXIES ARE NOT CONSTRAINED BY ONTOLOGY; THEREFORE INHERITANCE DOESN'T HAVE TO COPY ANYTHING ACROSS
                    for inherited_property_order, inherited_property_proxy in enumerate(inherited_property_proxies, start=1):
                        new_model_proxy.property_proxies.add(inherited_property_proxy)
                        new_property_proxies.append(inherited_property_proxy)
                    # for inherited_property_order, inherited_property_proxy in enumerate(inherited_property_proxies, start=1):
                    #     new_property_proxy = self.inherit_property_proxy(new_model_proxy, inherited_property_proxy, inherited_property_order)
                    #     new_property_proxies.append(new_property_proxy)
                    inherited_category_proxies = parent_model_proxy.category_proxies.filter(name__in=inherited_categories)
                    # AS OF 0.17.0, PROXIES ARE NOT CONSTRAINED BY ONTOLOGY; THEREFORE INHERITANCE DOESN'T HAVE TO COPY ANYTHING ACROSSS
                    for inherited_category_order, inherited_category_proxy in enumerate(inherited_category_proxies, start=1):
                        new_model_proxy.category_proxies.add(inherited_category_proxy)
                        new_category_proxies.append(inherited_category_proxy)
                    # for inherited_category_order, inherited_category_proxy in enumerate(inherited_category_proxies, start=1):
                    #     new_category_proxy = self.inherit_category_proxy(new_model_proxy, inherited_category_proxy, inherited_category_order)
                    #     new_category_proxies.append(new_category_proxy)
                except QModelProxy.DoesNotExist:
                    assert len(inherited_properties) == 0, "it makes no sense to specify 'inherited_properties' w/out providing a base model"
                    assert len(inherited_categories) == 0, "it makes no sense to specify 'inherited_categories' w/out providing a base model"

            for ontology_category_order, ontology_category in enumerate(defined_categories, start=len(new_category_proxies) + 1):
                ontology_category_name = ontology_category["name"]
                # HERE IS ONE DIFFERENCE BETWEEN SPECIALIZATIONS & SCHEMAS...
                # SCHEMA MODELS MUST HAVE EXPLICIT "cim_ids"...
                ontology_category_id = ontology_category.get("id")
                assert ontology_category_id is not None

                (new_category_proxy, created_category_proxy) = QCategoryProxy.objects.get_or_create(
                    ontology=self,
                    model_proxy=new_model_proxy,
                    name=ontology_category_name,
                    cim_id=ontology_category_id,
                )

                ontology_category_documentation = ontology_category.get("documentation")
                if ontology_category_documentation:
                    new_category_proxy.documentation = remove_spaces_and_linebreaks(ontology_category_documentation)
                new_category_proxy.order = ontology_category_order
                new_category_proxy.save()
                new_category_proxies.append(new_category_proxy)

            # if there's anything in old_category_proxies not in new_category_proxies, delete it...
            for old_category_proxy in old_category_proxies:
                if old_category_proxy not in new_category_proxies:
                    old_category_proxy.delete()

            for ontology_property_order, ontology_property in enumerate(defined_properties, start=len(new_property_proxies)+1):
                ontology_property_name = ontology_property["name"]
                ontology_property_id = ontology_property.get("id")
                ontology_property_field_type = QPropertyTypes.get(ontology_property["property_type"])
                assert ontology_property_field_type is not None, "invalid property_type specified"

                (new_property_proxy, created_property_proxy) = QPropertyProxy.objects.get_or_create(
                    ontology=self,
                    model_proxy=new_model_proxy,
                    name=ontology_property_name,
                    cim_id=ontology_property_id,
                    field_type=ontology_property_field_type
                )
                ontology_property_documentation = ontology_property.get("documentation")
                ontology_property_cardinality_min, ontology_property_cardinality_max = re.split("\.|,", ontology_property.get("cardinality"))  # TODO: WE NEED TO DECIDE IF CARDINALITY IS SPLIT ON '.' OR ','
                ontology_property_is_meta = ontology_property.get("is_meta", False)
                ontology_property_is_nillable = ontology_property.get("is_nillable", False)
                ontology_property_is_hierarchical = ontology_property.get("is_hierarchical", False)
                ontology_property_category_id = ontology_property.get("category_id")

                if ontology_property_documentation:
                    new_property_proxy.documentation = remove_spaces_and_linebreaks(ontology_property_documentation)
                new_property_proxy.is_meta = ontology_property_is_meta
                new_property_proxy.order = ontology_property_order
                new_property_proxy.cardinality_min = ontology_property_cardinality_min
                new_property_proxy.cardinality_max = ontology_property_cardinality_max
                new_property_proxy.is_nillable = ontology_property_is_nillable
                new_property_proxy.is_hierarchical = ontology_property_is_hierarchical
                new_property_proxy.category_id = ontology_property_category_id

                if ontology_property_field_type == QPropertyTypes.ATOMIC:
                    ontology_property_atomic_type = ontology_property.get("atomic_type")
                    if ontology_property_atomic_type == "STRING":
                        ontology_property_atomic_type = "DEFAULT"
                    ontology_property_atomic_type = QAtomicTypes.get(ontology_property_atomic_type)
                    assert ontology_property_atomic_type is not None
                    new_property_proxy.atomic_type = ontology_property_atomic_type

                elif ontology_property_field_type == QPropertyTypes.ENUMERATION:
                    ontology_property_enumeration_is_open = ontology_property.get("enumeration_is_open")
                    ontology_property_enumeration_choices = ontology_property.get("enumeration_members")
                    new_property_proxy.enumeration_is_open = ontology_property_enumeration_is_open
                    new_property_proxy.enumeration_choices = ontology_property_enumeration_choices

                else:  # ontology_property_field_type == QPropertyTypes.RELATIONSHIP
                    ontology_property_relationship_targets = ontology_property.get("relationship_targets")
                    # as w/ category_key above, just recording target names for now...
                    # during the "reset" fn (after all proxies are registered) links to the actual models will be set
                    new_property_proxy.relationship_target_names = ontology_property_relationship_targets

                new_property_proxy.values = ontology_property.get("values")

                new_property_proxy.save()
                new_property_proxies.append(new_property_proxy)

            # if there's anything in old_property_proxies not in new_property_proxies, delete it...
            for old_property_proxy in old_property_proxies:
                if old_property_proxy not in new_property_proxies:
                    old_property_proxy.delete()

            # save parent again for the m2m relationship...
            new_model_proxy.save()

        # if there's anything in old_model_proxies not in new_model_proxies, delete it...
        for old_model_proxy in old_model_proxies:
            if old_model_proxy not in new_model_proxies:
                old_model_proxy.delete()

        # TODO: DO THE SAME CHECK FOR NEW / EXISTING category_proxies

        # reset whatever's left...
        for model_proxy in QModelProxy.objects.filter(ontology=self):
            model_proxy.reset(force_save=True)
            for category_proxy in model_proxy.category_proxies.all():
                category_proxy.reset(force_save=True)
            for property_proxy in model_proxy.property_proxies.all():
                property_proxy.reset(force_save=True)

    def parse_schema(self, ontology_content, **kwargs):

        request = kwargs.get("request")

        # 1st do some logical checks on the content...

        # name should match the instance field...
        ontology_name = ontology_content.get("name")
        if self.name != ontology_name:
            msg = "The name of this ontology instance does not match the name found in the QConfig file"
            if request:
                messages.add_message(request, messages.WARNING, msg)
            raise QError(msg)

        # version should match(ish) the instance field...
        ontology_version = ontology_content.get("version")
        if self.version.major() != Version(ontology_version).major():
            msg = "The major version of this ontology instance does not match the major version of the QConfig file"
            if request:
                messages.add_message(request, messages.WARNING, msg)
            raise QError(msg)

        # documentation can overwrite the instance field (ie: the field set in the admin interface)...
        ontology_documentation = ontology_content.get("documentation")
        if ontology_documentation:
            self.documentation = remove_spaces_and_linebreaks(ontology_documentation)

        # type must match the instance field...
        ontology_type = QOntologyTypes.get(ontology_content["ontology_type"])
        assert ontology_type is not None, "invalid ontology_type specified"
        if self.ontology_type != ontology_type:
            msg = "This ontology is a {0}, but the content is for a {1}".format(self.ontology_type, ontology_type)
            if request:
                messages.add_message(request, messages.WARNING, msg)
            raise QError(msg)

        # if specified, parent must exist and match the instance field (and it must be specified for SPECIALIZATIONS)...
        ontology_base_key = ontology_content.get("ontology_base")
        if ontology_base_key:
            ontology_base = QOntology.objects.has_key(ontology_base_key).first()
            if ontology_base != self.parent:
                msg = "Invalid key '{0}' specified for 'ontology_base' (expected '{1}')".format(ontology_base_key, self.parent.key)
                if request:
                    messages.add_message(request, messages.WARNING, msg)
                raise QError(msg)
            if not ontology_base.is_registered:
                msg = "ontology_base must be registered before specialization"
                if request:
                    messages.add_message(request, messages.WARNING, msg)
                raise QError(msg)
        elif ontology_type == QOntologyTypes.SPECIALIZATION:
            msg = "A specialization must include an ontology_base"
            if request:
                messages.add_message(request, messages.WARNING, msg)
            raise QError(msg)

        # now create / setup all of the proxies contained in this ontology...

        inherited_classes = get_inherited_classes(ontology_content)  # inherited classes are included at the start
        excluded_classes = get_excluded_classes(ontology_content)  # excluded classes don't have to be used at all
        defined_classes = get_defined_classes(ontology_content)  # defined classes are added as normal

        old_model_proxies = list(self.model_proxies.all())
        new_model_proxies = []

        if self.parent:
            inherited_model_proxies = self.parent.model_proxies.in_fully_qualified_names(inherited_classes)
            # AS OF 0.17.0, PROXIES ARE NOT CONSTRAINED BY ONTOLOGY; THEREFORE INHERITANCE DOESN'T HAVE TO COPY ANYTHING ACROSSS
            # for inherited_model_order, inherited_model_proxy in enumerate(inherited_model_proxies, start=1):
            #     new_model_proxy = self.inherit_model_proxy(inherited_model_proxy, inherited_model_order)
            #     new_model_proxies.append(new_model_proxy)

        for ontology_model_order, ontology_model in enumerate(defined_classes, start=len(new_model_proxies)+1):

            ontology_model_name = ontology_model["name"]
            ontology_model_package = ontology_model["package"]
            # HERE IS ONE DIFFERENCE BETWEEN SPECIALIZATIONS & SCHEMAS...
            # SCHEMA MODELS PROBABLY DON'T HAVE EXPLICIT "cim_ids"...
            ontology_model_id = ontology_model.get("id", "{}.{}".format(self.key, ontology_model_name))

            (new_model_proxy, created_model_proxy) = QModelProxy.objects.get_or_create(
                # these fields are the "defining" ones (other fields can change w/out creating new proxies)
                ontology=self,
                name=ontology_model_name,
                package=ontology_model_package,
                cim_id=ontology_model_id,
            )

            ontology_class_documentation = ontology_model.get("documentation")
            ontology_class_is_document = ontology_model.get("is_document")
            ontology_class_is_meta = ontology_model.get("is_meta", False)
            ontology_class_label = ontology_model.get("label", None)
            if ontology_class_label is None and self.parent is not None:
                parent_model_proxy = self.parent.model_proxies.get(package=ontology_model_package, name=ontology_model_name)
                ontology_class_label = parent_model_proxy.label

            if ontology_class_documentation:
                new_model_proxy.documentation = remove_spaces_and_linebreaks(ontology_class_documentation)
            new_model_proxy.is_document = ontology_class_is_document
            new_model_proxy.is_meta = ontology_class_is_meta
            new_model_proxy.label = ontology_class_label
            new_model_proxy.order = ontology_model_order

            new_model_proxy.save()
            new_model_proxies.append(new_model_proxy)

            fully_qualified_class_name = "{0}.{1}".format(ontology_model_package, ontology_model_name)

            inherited_categories = get_inherited_categories(ontology_content, fully_qualified_class_name) # inherited categories are included at the start
            excluded_categories = get_excluded_categories(ontology_content, fully_qualified_class_name) # excluded categories don't have to be uesd at all
            defined_categories = get_defined_categories(ontology_content, fully_qualified_class_name) # defined categories are added as normal

            inherited_properties = get_inherited_properties(ontology_content, fully_qualified_class_name) # inherited properties are included at the start
            excluded_properties = get_excluded_properties(ontology_content, fully_qualified_class_name) # excluded properties don't have to be uesd at all
            defined_properties = get_defined_properties(ontology_content, fully_qualified_class_name) # defined properties are added as normal

            old_category_proxies = list(new_model_proxy.category_proxies.all())
            new_category_proxies = []

            old_property_proxies = list(new_model_proxy.property_proxies.all())
            new_property_proxies = []

            if self.parent:
                parent_model_proxy = self.parent.model_proxies.get(package=ontology_model_package, name=ontology_model_name)
                inherited_property_proxies = parent_model_proxy.property_proxies.filter(name__in=inherited_properties)
                # AS OF 0.17.0, PROXIES ARE NOT CONSTRAINED BY ONTOLOGY; THEREFORE INHERITANCE DOESN'T HAVE TO COPY ANYTHING ACROSS
                for inherited_property_order, inherited_property_proxy in enumerate(inherited_property_proxies, start=1):
                    new_model_proxy.property_proxies.add(inherited_property_proxy)
                    new_property_proxies.append(inherited_property_proxy)
                    # new_property_proxy = self.inherit_property_proxy(new_model_proxy, inherited_property_proxy, inherited_property_order)
                    # new_property_proxies.append(new_property_proxy)
                inherited_category_proxies = parent_model_proxy.category_proxies.filter(name__in=inherited_categories)
                # AS OF 0.17.0, PROXIES ARE NOT CONSTRAINED BY ONTOLOGY; THEREFORE INHERITANCE DOESN'T HAVE TO COPY ANYTHING ACROSSS
                for inherited_category_order, inherited_category_proxy in enumerate(inherited_category_proxies, start=1):
                    new_model_proxy.category_proxies.add(inherited_category_proxy)
                    new_category_proxies.append(inherited_category_proxy)
                    # new_category_proxy = self.inherit_category_proxy(new_model_proxy, inherited_category_proxy, inherited_category_order)
                    # new_category_proxies.append(new_category_proxy)

            for ontology_category_order, ontology_category in enumerate(defined_categories, start=len(new_category_proxies) + 1):
                ontology_category_name = ontology_category["name"]
                ontology_category_id = ontology_category.get("id")
                assert ontology_category_id is not None

                (new_category_proxy, created_category_proxy) = QCategoryProxy.objects.get_or_create(
                    ontology=self,
                    model_proxy=new_model_proxy,
                    name=ontology_category_name,
                    cim_id=ontology_category_id,
                )

                ontology_category_documentation = ontology_category.get("documentation")
                if ontology_category_documentation:
                    new_category_proxy.documentation = remove_spaces_and_linebreaks(ontology_category_documentation)
                new_category_proxy.order = ontology_category_order
                new_category_proxy.save()
                new_category_proxies.append(new_category_proxy)

            # if there's anything in old_category_proxies not in new_category_proxies, delete it...
            for old_category_proxy in old_category_proxies:
                if old_category_proxy not in new_category_proxies:
                    old_category_proxy.delete()

            for ontology_property_order, ontology_property in enumerate(defined_properties, start=len(new_property_proxies)+1):

                ontology_property_name = ontology_property["name"]
                ontology_property_id = ontology_property.get("id")
                ontology_property_field_type = QPropertyTypes.get(ontology_property["property_type"])
                assert ontology_property_field_type is not None, "invalid property_type specified"

                (new_property_proxy, created_property_proxy) = QPropertyProxy.objects.get_or_create(
                    ontology=self,
                    model_proxy=new_model_proxy,
                    name=ontology_property_name,
                    cim_id=ontology_property_id,
                    field_type=ontology_property_field_type
                )

                ontology_property_documentation = ontology_property.get("documentation")
                ontology_property_cardinality_min, ontology_property_cardinality_max = re.split("\.|,", ontology_property.get("cardinality"))  # TODO: WE NEED TO DECIDE IF CARDINALITY IS SPLIT ON '.' OR ','
                ontology_property_is_meta = ontology_property.get("is_meta", False)
                ontology_property_is_nillable = ontology_property.get("is_nillable", False)
                ontology_property_is_hierarchical = ontology_property.get("is_hierarchical", False)
                ontology_property_category_id = ontology_property.get("category_id")

                if ontology_property_documentation:
                    new_property_proxy.documentation = remove_spaces_and_linebreaks(ontology_property_documentation)
                new_property_proxy.is_meta = ontology_property_is_meta
                new_property_proxy.order = ontology_property_order
                new_property_proxy.cardinality_min = ontology_property_cardinality_min
                new_property_proxy.cardinality_max = ontology_property_cardinality_max
                new_property_proxy.is_nillable = ontology_property_is_nillable
                new_property_proxy.is_hierarchical = ontology_property_is_hierarchical
                new_property_proxy.category_id = ontology_property_category_id

                if ontology_property_field_type == QPropertyTypes.ATOMIC:
                    ontology_property_atomic_type = ontology_property.get("atomic_type")
                    if ontology_property_atomic_type == "STRING":
                        ontology_property_atomic_type = "DEFAULT"
                    ontology_property_atomic_type = QAtomicTypes.get(ontology_property_atomic_type)
                    assert ontology_property_atomic_type is not None
                    new_property_proxy.atomic_type = ontology_property_atomic_type

                elif ontology_property_field_type == QPropertyTypes.ENUMERATION:
                    ontology_property_enumeration_is_open = ontology_property.get("enumeration_is_open")
                    ontology_property_enumeration_choices = ontology_property.get("enumeration_members")
                    new_property_proxy.enumeration_is_open = ontology_property_enumeration_is_open
                    new_property_proxy.enumeration_choices = ontology_property_enumeration_choices

                else:  # ontology_property_field_type == QPropertyTypes.RELATIONSHIP
                    ontology_property_relationship_targets = ontology_property.get("relationship_targets")
                    # just recording target names for now...
                    # during the "reset" fn (after _all_ proxies have been registered) links to the actual models will be set
                    new_property_proxy.relationship_target_names = ontology_property_relationship_targets

                new_property_proxy.values = ontology_property.get("values")

                new_property_proxy.save()
                new_property_proxies.append(new_property_proxy)

            # if there's anything in old_property_proxies not in new_property_proxies, delete it...
            for old_property_proxy in old_property_proxies:
                if old_property_proxy not in new_property_proxies:
                    old_property_proxy.delete()

            # save parent again for the m2m relationships...
            new_model_proxy.save()

        # if there's anything in old_model_proxies not in new_model_proxies, delete it...
        for old_model_proxy in old_model_proxies:
            if old_model_proxy not in new_model_proxies:
                old_model_proxy.delete()

        # TODO: DO THE SAME CHECK FOR NEW / EXISTING category_proxies

        # reset whatever's left...
        for model_proxy in QModelProxy.objects.filter(ontology=self):
            model_proxy.reset(force_save=True)
            for category_proxy in model_proxy.category_proxies.all():
                category_proxy.reset(force_save=True)
            for property_proxy in model_proxy.property_proxies.all():
                property_proxy.reset(force_save=True)

    def inherit_model_proxy(self, inherited_model_proxy, inherited_order):
        (new_model_proxy, created_model_proxy) = QModelProxy.objects.get_or_create(
            ontology=self,
            name=inherited_model_proxy.name,
            package=inherited_model_proxy.package,
            cim_id=inherited_model_proxy.cim_id,
        )
        new_model_proxy.documentation = inherited_model_proxy.documentation
        new_model_proxy.is_document = inherited_model_proxy.is_document
        new_model_proxy.is_meta = inherited_model_proxy.is_meta
        new_model_proxy.label = inherited_model_proxy.label
        new_model_proxy.order = inherited_order
        new_model_proxy.save()

        old_category_proxies = list(new_model_proxy.category_proxies.all())
        new_category_proxies = []

        for inherited_category_order, inherited_category_proxy in enumerate(inherited_model_proxy.category_proxies.all(), start=1):
            new_category_proxy = self.inherit_category_proxy(new_model_proxy, inherited_category_proxy, inherited_category_order)
            new_category_proxies.append(new_category_proxy)

        # if there's anything in old_category_proxies not in new_category_proxies, delete it...
        for old_category_proxy in old_category_proxies:
            if old_category_proxy not in new_category_proxies:
                old_category_proxy.delete()

        old_property_proxies = list(new_model_proxy.property_proxies.all())
        new_property_proxies = []

        for inherited_property_order, inherited_property_proxy in enumerate(inherited_model_proxy.property_proxies.all(), start=1):
            new_property_proxy = self.inherit_property_proxy(new_model_proxy, inherited_property_proxy, inherited_property_order)
            new_property_proxies.append(new_property_proxy)

        # if there's anything in old_property_proxies not in new_property_proxies, delete it...
        for old_property_proxy in old_property_proxies:
            if old_property_proxy not in new_property_proxies:
                old_property_proxy.delete()

        new_model_proxy.save()
        return new_model_proxy

    def inherit_category_proxy(self, model_proxy, inherited_category_proxy, inherited_order):
        (new_category_proxy, created_category_proxy) = QCategoryProxy.objects.get_or_create(
            model_proxy=model_proxy,
            name=inherited_category_proxy.name,
            cim_id=inherited_category_proxy.cim_id,
        )
        new_category_proxy.documentation = inherited_category_proxy.documentation
        new_category_proxy.order = inherited_order

        new_category_proxy.save()
        return new_category_proxy

    def inherit_property_proxy(self, model_proxy, inherited_property_proxy, inherited_order):

        (new_property_proxy, created_property_proxy) = QPropertyProxy.objects.get_or_create(
            model_proxy=model_proxy,
            name=inherited_property_proxy.name,
            cim_id=inherited_property_proxy.cim_id,
            field_type=inherited_property_proxy.field_type
        )
        new_property_proxy.documentation = inherited_property_proxy.documentation
        new_property_proxy.is_meta = inherited_property_proxy.is_meta
        new_property_proxy.cardinality_min = inherited_property_proxy.cardinality_min
        new_property_proxy.cardinality_max = inherited_property_proxy.cardinality_max
        new_property_proxy.is_nillable = inherited_property_proxy.is_nillable
        new_property_proxy.is_hierarchical = inherited_property_proxy.is_hierarchical
        new_property_proxy.order = inherited_order
        new_property_proxy.atomic_type = inherited_property_proxy.atomic_type
        new_property_proxy.enumeration_is_open = inherited_property_proxy.enumeration_is_open
        new_property_proxy.enumeration_choices = inherited_property_proxy.enumeration_choices
        new_property_proxy.relationship_target_names = inherited_property_proxy.relationship_target_names
        new_property_proxy.values = inherited_property_proxy.values

        # TODO: FIGURE OUT HOW/IF TO ADD CATEGORIES

        new_property_proxy.save()

        if new_property_proxy.field_type == QPropertyTypes.RELATIONSHIP:
            for inherited_model_proxy_order, inherited_model_proxy in enumerate(inherited_property_proxy.relationship_target_models.all(), start=self.model_proxies.count()+1):
                try:
                    new_model_proxy = self.model_proxies.get(package=inherited_model_proxy.package, name=inherited_model_proxy.name, cim_id=inherited_model_proxy.cim_id)
                except QModelProxy.DoesNotExist:
                    new_model_proxy = self.inherit_model_proxy(inherited_model_proxy, inherited_model_proxy_order)
                new_property_proxy.relationship_target_models.add(new_model_proxy)
            new_property_proxy.save()

        return new_property_proxy

    def register(self, **kwargs):
        request = kwargs.get("request")

        # check the file is valid...
        try:
            self.file.open()
            ontology_content = json.load(self.file)
            self.file.close()
        except IOError as e:
            msg = "Error opening file: {0}".format(self.file)
            if request:
                messages.add_message(request, messages.ERROR, msg)
            raise e

        # check I'm allowed to re-register the ontology...
        if self.last_registered_version:
            last_registered_version_major = self.get_last_registered_version_major()
            last_registered_version_minor = self.get_last_registered_version_minor()
            current_version_major = self.get_version_major()
            current_version_minor = self.get_version_minor()
            if last_registered_version_major != current_version_major or last_registered_version_minor != current_version_minor:
                if request:
                    msg = "You are not allowed to re-register anything other than a new patch version."
                    messages.add_message(request, messages.ERROR, msg)
                return

        # check if a registered parent exists...
        if self.parent and not self.parent.is_registered:
            if request:
                msg = "You are not allowed to register an ontology whose parent has not yet been registered."
                messages.add_message(request, messages.ERROR, msg)
            return

        try:
            self.parse_ontology_content(ontology_content)
            # record that registration occurred...
            self.last_registered_version = self.version
            self.is_registered = True
        except Exception as e:
            # if something goes wrong, record it in the logs and return immediately (but don't crash)...
            q_logger.error(e)
            if request:
                messages.add_message(request, messages.ERROR, str(e))
            return

        # update any existing customizations & realizations...
        # customizations_to_update = [
        #     customization for customization in QModelCustomization.objects.filter(proxy__ontology=self)
        #     if customization.proxy.is_meta
        # ]
        # for customization in customizations_to_update:
        #     registered_ontology_signal.send_robust(
        #         sender=self,
        #         customization=customization
        #     )
        # realizations_to_update = [
        #     realization for realization in QModel.objects.filter(proxy__ontology=self)
        #     if realization.proxy.is_meta
        # ]
        # for realization in realizations_to_update:
        #     registered_ontology_signal.send_robust(
        #         sender=self,
        #         realization=realization
        #     )

        # hooray, you're done...
        if request:
            msg = "Successfully registered ontology: {0}".format(self)
            messages.add_message(request, messages.SUCCESS, msg)

    def register_bak(self, **kwargs):
        request = kwargs.get("request")

        # check the file is valid...
        try:
            self.file.open()
            ontology_content = json.load(self.file)
            self.file.close()
        except IOError as e:
            msg = "Error opening file: {0}".format(self.file)
            if request:
                messages.add_message(request, messages.ERROR, msg)
            raise e

        # check I'm allowed to register the ontology...
        if self.last_registered_version:
            last_registered_version_major = self.get_last_registered_version_major()
            last_registered_version_minor = self.get_last_registered_version_minor()
            current_version_major = self.get_version_major()
            current_version_minor = self.get_version_minor()
            if last_registered_version_major != current_version_major or last_registered_version_minor != current_version_minor:
                if request:
                    msg = "You are not allowed to re-register anything other than a new patch version."
                    messages.add_message(request, messages.ERROR, msg)
                return
        if self.parent and not self.parent.is_registered:
            if request:
                msg = "You are not allowed to register an ontology whose parent has not yet been registered."
                messages.add_message(request, messages.ERROR, msg)
            return

        try:
            # do the actual parsing...
            # TODO: CAN "parse_schema" & "parse_specialization" BE COLLAPSED INTO A SINGLE FN?
            if self.ontology_type == QOntologyTypes.SCHEMA:
                self.parse_schema(ontology_content, request=request)
            else:
                self.parse_specialization(ontology_content, request=request)
            # deal w/ any uncategorized properties...
            for model_proxy in self.model_proxies.all():
                uncategorized_category_proxy, created_uncategorized_category_proxy = QCategoryProxy.objects.get_or_create(
                    ontology=self,
                    name=UNCATEGORIZED_CATEGORY_PROXY_NAME,
                    model_proxy=model_proxy,
                    is_uncategorized=True,
                )
                if created_uncategorized_category_proxy:
                    uncategorized_category_proxy.order = model_proxy.category_proxies.count()
                    uncategorized_category_proxy.save()
                    model_proxy.category_proxies.add(uncategorized_category_proxy)
                model_proxy.save()
                for uncategorized_property_proxy in model_proxy.property_proxies.filter(category_proxy=None):
                    uncategorized_property_proxy.category_proxy = uncategorized_category_proxy
                    uncategorized_property_proxy.save()
            # record that registration occurred...
            self.last_registered_version = self.version
            self.is_registered = True
        except Exception as e:
            # if something goes wrong, record it in the logs and return immediately (but don't crash)...
            q_logger.error(e)
            if request:
                messages.add_message(request, messages.ERROR, str(e))
            return

        # update any existing customizations & realizations...
        # customizations_to_update = [
        #     customization for customization in QModelCustomization.objects.filter(proxy__ontology=self)
        #     if customization.proxy.is_meta
        # ]
        # for customization in customizations_to_update:
        #     registered_ontology_signal.send_robust(
        #         sender=self,
        #         customization=customization
        #     )
        # realizations_to_update = [
        #     realization for realization in QModel.objects.filter(proxy__ontology=self)
        #     if realization.proxy.is_meta
        # ]
        # for realization in realizations_to_update:
        #     registered_ontology_signal.send_robust(
        #         sender=self,
        #         realization=realization
        #     )

        # hooray, you're done...
        if request:
            msg = "Successfully registered ontology: {0}".format(self)
            messages.add_message(request, messages.SUCCESS, msg)


###########################################################
# some more helper fns defined to work w/ QConfig content #
# (the assumption is that the content will have already   #
# been validated when the QOntology was 1st loaded)       #
###########################################################


def get_inherited_classes(qconfig_content):
    """
    :param qconfig_content: ontology definition
    :return: section of qconfig_content dealing w/ inherited classes
    """
    return qconfig_content["classes"]["inherited"]


def get_excluded_classes(qconfig_content):
    """
    :param qconfig_content: ontology definition
    :return: section of qconfig_content dealing w/ excluded classes
    """
    return qconfig_content["classes"]["excluded"]


def get_defined_classes(qconfig_content):
    """
    :param qconfig_content: ontology definition
    :return: section of qconfig_content dealing w/ excluded classes
    """
    return qconfig_content["classes"]["defined"]


def get_inherited_categories(qconfig_content, fully_qualified_class_name):
    """
    :param qconfig_content: ontology definition
    :param fully_qualified_class_name: class to search
    :return: section of qconfig_content dealing w/ inherited categories for a given class
    """
    class_package, class_name = fully_qualified_class_name.split('.')
    defined_classes = get_defined_classes(qconfig_content)
    defined_class = find_in_sequence(
        lambda c: c.get("package") == class_package and c.get("name") == class_name,
        defined_classes
    )
    if defined_class is None:
        msg = "Unable to locate '{0}' in qconfig".format(fully_qualified_class_name)
        raise QError(msg)
    return defined_class["categories"]["inherited"]


def get_excluded_categories(qconfig_content, fully_qualified_class_name):
    """
    :param qconfig_content: ontology definition
    :param fully_qualified_class_name: class to search
    :return: section of qconfig_content dealing w/ excluded categories for a given class
    """
    class_package, class_name = fully_qualified_class_name.split('.')
    defined_classes = get_defined_classes(qconfig_content)
    defined_class = find_in_sequence(
        lambda c: c.get("package") == class_package and c.get("name") == class_name,
        defined_classes
    )
    if defined_class is None:
        msg = "Unable to locate '{0}' in qconfig".format(fully_qualified_class_name)
        raise QError(msg)
    return defined_class["categories"]["excluded"]


def get_defined_categories(qconfig_content, fully_qualified_class_name):
    """
    :param qconfig_content: ontology definition
    :param fully_qualified_class_name: class to search
    :return: section of qconfig_content dealing w/ defined categories for a given class
    """
    class_package, class_name = fully_qualified_class_name.split('.')
    defined_classes = get_defined_classes(qconfig_content)
    defined_class = find_in_sequence(
        lambda c: c.get("package") == class_package and c.get("name") == class_name,
        defined_classes
    )
    if defined_class is None:
        msg = "Unable to locate '{0}' in qconfig".format(fully_qualified_class_name)
        raise QError(msg)
    return defined_class["categories"]["defined"]


def get_inherited_properties(qconfig_content, fully_qualified_class_name):
    """
    :param qconfig_content: ontology definition
    :param fully_qualified_class_name: class to search
    :return: section of qconfig_content dealing w/ inherited properties for a given class
    """
    class_package, class_name = fully_qualified_class_name.split('.')
    defined_classes = get_defined_classes(qconfig_content)
    defined_class = find_in_sequence(
        lambda c: c.get("package") == class_package and c.get("name") == class_name,
        defined_classes
    )
    if defined_class is None:
        msg = "Unable to locate '{0}' in qconfig".format(fully_qualified_class_name)
        raise QError(msg)
    return defined_class["properties"]["inherited"]


def get_excluded_properties(qconfig_content, fully_qualified_class_name):
    """
    :param qconfig_content: ontology definition
    :param fully_qualified_class_name: class to search
    :return: section of qconfig_content dealing w/ excluded properties for a given class
    """
    class_package, class_name = fully_qualified_class_name.split('.')
    defined_classes = get_defined_classes(qconfig_content)
    defined_class = find_in_sequence(
        lambda c: c.get("package") == class_package and c.get("name") == class_name,
        defined_classes
    )
    if defined_class is None:
        msg = "Unable to locate '{0}' in qconfig".format(fully_qualified_class_name)
        raise QError(msg)
    return defined_class["properties"]["excluded"]


def get_defined_properties(qconfig_content, fully_qualified_class_name):
    """
    :param qconfig_content: ontology definition
    :param fully_qualified_class_name: class to search
    :return: section of qconfig_content dealing w/ defined properties for a given class
    """
    class_package, class_name = fully_qualified_class_name.split('.')
    defined_classes = get_defined_classes(qconfig_content)
    defined_class = find_in_sequence(
        lambda c: c.get("package") == class_package and c.get("name") == class_name,
        defined_classes
    )
    if defined_class is None:
        msg = "Unable to locate '{0}' in qconfig".format(fully_qualified_class_name)
        raise QError(msg)
    return defined_class["properties"]["defined"]

