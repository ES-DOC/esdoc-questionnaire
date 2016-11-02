__author__ = 'allyn.treshansky'

from django.db import models
from django.contrib import messages
from django.conf import settings
from django.dispatch import Signal

from lxml import etree as et
from uuid import uuid4
import os
import re

from Q.questionnaire import APP_LABEL, q_logger
from Q.questionnaire.q_fields import QFileField, QVersionField, QAtomicPropertyTypes
from Q.questionnaire.models.models_proxies import QModelProxy, QPropertyProxy
from Q.questionnaire.q_utils import QError, EnumeratedType, EnumeratedTypeList, Version, validate_file_extension, validate_file_schema, validate_no_spaces, validate_no_bad_chars, xpath_fix, remove_spaces_and_linebreaks, get_index
from Q.questionnaire.q_constants import *


###################
# local constants #
###################

ONTOLOGY_UPLOAD_DIR = "ontologies"
ONTOLOGY_UPLOAD_PATH = os.path.join(APP_LABEL, ONTOLOGY_UPLOAD_DIR)

class QOntologyType(EnumeratedType):

    def __str__(self):
        return "{0}".format(self.get_type())

QOntologyTypes = EnumeratedTypeList([
    QOntologyType("SCHEMA", "Schema (ie: CIM2)"),
    QOntologyType("SPECIALIZATION", "Specialization (ie: CMIP6)")
])

####################
# local validators #
####################

def validate_ontology_file_extension(value):
    valid_extensions = ["xml"]
    return validate_file_extension(value, valid_extensions)

def validate_ontology_file_schema(value):
    schema_path = os.path.join(settings.STATIC_ROOT, APP_LABEL, "xml/qxml.xsd")
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

#############
# a manager #
#############

# As of Django 1.7 I can use custom querysets as managers
# (ensures that its custom methods are chainable)
# whoo-hoo

class QOntologyQuerySet(models.QuerySet):

    def registered(self):
        return self.filter(is_registered=True)

    def schemas(self):
        return self.filter(ontology_type=QOntologyTypes.SCHEMA.get_type())

    def specializations(self):
        return self.filter(ontology_type=QOntologyTypes.SPECIALIZATION.get_type())

    def filter_by_key(self, key):
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


######################
# the actual classes #
######################

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

    categorization = models.ForeignKey(
        "QCategorization",
        related_name="ontologies",
        blank=True, null=True,
        on_delete=models.SET_NULL
    )

    ontology_type = models.CharField(
        choices=[(ot.get_type(), ot.get_name()) for ot in QOntologyTypes],
        default=QOntologyTypes.SPECIALIZATION.get_type(),
        max_length=SMALL_STRING, blank=False,
    )

    file = QFileField(blank=False, upload_to=ONTOLOGY_UPLOAD_PATH, validators=[validate_ontology_file_extension, validate_ontology_file_schema, ])

    name = models.CharField(max_length=LIL_STRING, blank=False, validators=[validate_no_spaces, validate_no_bad_chars])
    version = QVersionField(blank=False)
    url = models.URLField(blank=False)
    description = models.TextField(blank=True, null=True)
    description.help_text = "This may be overwritten by any descriptive text found in the QXML file."

    # "key" is a way of uniquely but intuitively referring to this ontology in a URL and elsewhere
    key = models.CharField(max_length=SMALL_STRING, blank=False, editable=False)

    is_registered = models.BooleanField(blank=False, default=False)
    last_registered_version = QVersionField(blank=True, null=True)  # used to enforce only re-registering "patch" releases

    def __init__(self, *args, **kwargs):
        super(QOntology, self).__init__(*args, **kwargs)
        self._original_key = self.key

    def __str__(self):
        if self.version:
            return "{0} [{1}]".format(self.name, self.version)
        else:
            return "{0}".format(self.name)

    def clean(self):
        # force name to be lowercase...
        # this avoids hacky methods of ensuring case-insensitive uniqueness
        self.name = self.name.lower()

        return super(QOntology, self).clean()

    def get_fully_qualified_key(self, prefix=None):
        fully_qualified_key = "{0}".format(self.guid)
        if prefix:
            return "{0}.{1}".format(prefix, fully_qualified_key)
        return fully_qualified_key

    def get_key(self):
        return "{0}_{1}".format(self.name, self.version)

    def is_schema(self):
        return self.ontology_type == QOntologyTypes.SCHEMA

    def is_specialization(self):
        return not self.is_schema()

    def parse_schema(self, **kwargs):
        """
        registers a CIM2 ontology schema QXML file
        :param kwargs:
        :return:
        """

        request = kwargs.pop("request", None)

        try:
            self.file.open()
            ontology_content = et.parse(self.file)
            self.file.close()
        except IOError as e:
            msg = "Error opening file: {0}".format(self.file)
            if request:
                messages.add_message(request, messages.ERROR, msg)
            raise e

        recategorization_needed = False

        # name should match the instance field...
        ontology_name = get_index(xpath_fix(ontology_content, "name/text()"), 0)
        if self.name != ontology_name:
            msg = "The name of this ontology instance does not match the name of the QXML file"
            if request:
                messages.add_message(request, messages.WARNING, msg)

        # version should match(ish) the instance field...
        ontology_version = get_index(xpath_fix(ontology_content, "version/text()"), 0)
        if self.version.major() != Version(ontology_version).major():
            msg = "The major version of this ontology instance does not match the major version of the QXML file"
            if request:
                messages.add_message(request, messages.WARNING, msg)

        # description can overwrite the instance field (ie: the field set in the admin interface)...
        ontology_description = get_index(xpath_fix(ontology_content, "description/text()"), 0)
        if ontology_description:
            self.description = remove_spaces_and_linebreaks(ontology_description)

        old_model_proxies = list(self.model_proxies.all())  # list forces qs evaluation immediately
        new_model_proxies = []

        model_proxy_schema = self
        for i, model_proxy in enumerate(xpath_fix(ontology_content, "//classes/class"), start=1):
            model_proxy_package = xpath_fix(model_proxy, "@package")[0]
            model_proxy_stereotype = get_index(xpath_fix(model_proxy, "@stereotype"), 0)
            model_proxy_is_meta = get_index(xpath_fix(model_proxy, "@is_meta"), 0)

            model_proxy_name = xpath_fix(model_proxy, "name/text()")[0]
            model_proxy_documentation = get_index(xpath_fix(model_proxy, "description/text()"), 0)
            if model_proxy_documentation is not None:
                model_proxy_documentation = remove_spaces_and_linebreaks(model_proxy_documentation)
            else:
                model_proxy_documentation = ""

            (new_model_proxy, created_model_proxy) = QModelProxy.objects.get_or_create(
                # these 3 fields are the "defining" ones (other fields can change w/out creating new proxies)
                package=model_proxy_package,
                ontology=model_proxy_schema,
                name=model_proxy_name,
            )

            new_model_proxy.order = i
            new_model_proxy.stereotype = model_proxy_stereotype
            new_model_proxy.documentation = model_proxy_documentation
            if model_proxy_is_meta is not None:
                new_model_proxy.is_meta = model_proxy_is_meta == "true"

            if created_model_proxy:
                recategorization_needed = True

            new_model_proxy.save()
            new_model_proxies.append(new_model_proxy)

            old_property_proxies = list(new_model_proxy.property_proxies.all())  # list forces qs evaluation immediately
            new_property_proxies = []

            for j, property_proxy in enumerate(xpath_fix(model_proxy, "attributes/attribute"), start=1):
                property_proxy_package = get_index(xpath_fix(property_proxy, "@package"), 0)
                property_proxy_stereotype = get_index(xpath_fix(property_proxy, "@stereotype"), 0)
                property_proxy_is_nillable = get_index(xpath_fix(property_proxy, "@is_nillable"), 0)
                property_proxy_is_meta = get_index(xpath_fix(property_proxy, "@is_meta"), 0)

                property_proxy_name = re.sub(r'\.', '_', str(xpath_fix(property_proxy, "name/text()")[0]))
                property_proxy_documentation = get_index(xpath_fix(property_proxy, "description/text()"), 0)
                if property_proxy_documentation is not None:
                    property_proxy_documentation = remove_spaces_and_linebreaks(property_proxy_documentation)
                else:
                    property_proxy_documentation = ""
                property_proxy_cardinality_min = get_index(xpath_fix(property_proxy, "cardinality/@min"), 0)
                property_proxy_cardinality_max = get_index(xpath_fix(property_proxy, "cardinality/@max"), 0)
                property_proxy_field_type = xpath_fix(property_proxy, "type/text()")[0]

                (new_property_proxy, created_property) = QPropertyProxy.objects.get_or_create(
                    # these 3 fields are the "defining" ones (other fields can change w/out creating new proxies)
                    # TODO: WHAT ABOUT "package"?
                    model_proxy=new_model_proxy,
                    name=property_proxy_name,
                    field_type=property_proxy_field_type
                )

                new_property_proxy.order = j
                new_property_proxy.stereotype = property_proxy_stereotype
                new_property_proxy.documentation = property_proxy_documentation
                if property_proxy_is_nillable is not None:
                    new_property_proxy.is_nillable = property_proxy_is_nillable == "true"
                if property_proxy_is_meta is not None:
                    new_property_proxy.is_meta = property_proxy_is_meta == "true"
                new_property_proxy.cardinality = "{0}|{1}".format(
                    property_proxy_cardinality_min,
                    property_proxy_cardinality_max if property_proxy_cardinality_max != "N" else "*",
                )

                # atomic properties...
                property_proxy_atomic_type = get_index(xpath_fix(property_proxy, "atomic/atomic_type/text()"), 0)
                if property_proxy_atomic_type is not None:
                    if property_proxy_atomic_type == u"STRING":
                        property_proxy_atomic_type = u"DEFAULT"
                    property_proxy_atomic_type = QAtomicPropertyTypes.get(property_proxy_atomic_type)
                    new_property_proxy.atomic_type = property_proxy_atomic_type

                # enumeration properties...
                property_proxy_enumeration_is_open = get_index(xpath_fix(property_proxy, "enumeration/@is_open"), 0)
                if property_proxy_enumeration_is_open is not None:
                    new_property_proxy.enumeration_is_open = property_proxy_enumeration_is_open == "true"
                # TODO: FACTOR OUT THIS PROPERTY IN FAVOR OF USING "cardinality" DIRECTLY, AS PER #429
                property_proxy_enumeration_is_multi = get_index(xpath_fix(property_proxy, "enumeration/@is_multi"), 0)
                if property_proxy_enumeration_is_multi is not None:
                    new_property_proxy.enumeration_is_multi = property_proxy_enumeration_is_multi == "true"
                property_proxy_enumeration = []
                for k, enumeration_member_proxy in enumerate(xpath_fix(property_proxy, "enumeration/choices/choice"), start=1):
                    enumeration_member_proxy_value = get_index(xpath_fix(enumeration_member_proxy, "value/text()"), 0)
                    enumeration_member_proxy_documentation = get_index(xpath_fix(enumeration_member_proxy, "description/text()"), 0)
                    property_proxy_enumeration_member = {
                        "order": k,
                        "value": enumeration_member_proxy_value,
                        "name": enumeration_member_proxy_value,
                        "documentation": enumeration_member_proxy_documentation,
                    }
                    property_proxy_enumeration.append(property_proxy_enumeration_member)
                new_property_proxy.enumeration = property_proxy_enumeration

                # relationship properties...
                property_proxy_relationship_target_names = "|".join(
                    xpath_fix(property_proxy, "relationship/targets/target/text()")
                )
                new_property_proxy.relationship_target_names = property_proxy_relationship_target_names

                if created_property:
                    recategorization_needed = True

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
            for property_proxy in model_proxy.property_proxies.all():
                property_proxy.reset()
                property_proxy.save()

        if recategorization_needed:
            msg = "Since you are re-registering an existing version, you will also have to re-register the corresponding categorization"
            if request:
                messages.add_message(request, messages.WARNING, msg)

    def parse_specialization(self, **kwargs):
        """
        registers a CIM2 ontology specialization QXML file
        :param kwargs:
        :return:
        """

        msg = "{0} has not defined 'parse_specialization' method.".format(self.__class__.__name__)
        raise NotImplementedError(msg)

    def register(self, **kwargs):

        request = kwargs.get("request")

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

        try:
            if self.is_schema():
                self.parse_schema()
            else:
                self.parse_specialization()
            self.is_registered = True
            self.last_registered_version = self.version
        except Exception as e:
            # if something goes wrong, record it in the logs and return immediately
            # (but don't crash)
            q_logger.error(e)
            if request:
                messages.add_message(request, messages.ERROR, str(e))
            return

        # # if I re-registered an ontology and there were existing customizations associated w/ it
        # # then I better update those customizations so that they have the right content
        # customizations_to_update = [customization for customization in QModelCustomization.objects.filter(proxy__ontology=self) if customization.proxy.is_document()]
        # for customization in customizations_to_update:
        #     registered_ontology_signal.send_robust(
        #         sender=self,
        #         customization=customization
        #     )
        #
        # # TODO: DO THE SAME THING FOR EXISTING DOCUMENTATIONS

        if request:
            msg = "Successfully registered ontology: {0}".format(self)
            messages.add_message(request, messages.SUCCESS, msg)

    def save(self, *args, **kwargs):
        _current_key = self.get_key()
        if _current_key != self._original_key:
            self.key = _current_key
        super(QOntology, self).save(*args, **kwargs)
        self._original_key = self.key
