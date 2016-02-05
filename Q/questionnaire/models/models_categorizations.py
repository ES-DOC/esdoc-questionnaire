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
from django.conf import settings
from django.dispatch import Signal
from django.contrib import messages
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError
from uuid import uuid4
from lxml import etree as et
import os

from Q.questionnaire import APP_LABEL, q_logger
from Q.questionnaire.q_fields import QFileField, QVersionField
from Q.questionnaire.models.models_proxies import QModelProxy, QStandardPropertyProxy, QStandardCategoryProxy
from Q.questionnaire.q_utils import QError, CIMTypes, validate_file_extension, validate_file_schema, xpath_fix, get_index, remove_spaces_and_linebreaks
from Q.questionnaire.q_fields import Version
from Q.questionnaire.q_constants import *


###################
# local constants #
###################

UPLOAD_DIR = "categorizations"
UPLOAD_PATH = os.path.join(APP_LABEL, UPLOAD_DIR)  # this will be concatenated w/ MEDIA_ROOT by FileField

####################
# local validators #
####################

# these are no longer being used, b/c file validation is dependant on what type of categorization this is (CIM1 vs CIM2)
# therefore, validation takes place w/in the "clean" fn - when I have access to an instance's type as well as its file

def validate_categorization_file_extension(value):
    valid_extensions = ["xml"]
    return validate_file_extension(value, valid_extensions)

def validate_categorization_file_schema(value):
    schema_path = os.path.join(settings.STATIC_ROOT, APP_LABEL, "xml/categorization.xsd")
    return validate_file_schema(value,schema_path)

###########
# signals #
###########

registered_categorization_signal = Signal(providing_args=["realization", "customization", ])

####################
# the actual class #
####################

class QCategorizationQuerySet(models.QuerySet):
    """
    As of Django 1.7 I can use custom querysets as managers
    to ensure that these custom methods are chainable
    whoo-hoo
    """

    def registered(self):
        return self.filter(is_registered=True)

class QCategorization(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "Questionnaire Categorization"
        verbose_name_plural = "Questionnaire Categorizations"
        unique_together = ("name", "version",)
        ordering = ("created", )

    objects = QCategorizationQuerySet.as_manager()

    guid = models.UUIDField(default=uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    name = models.CharField(max_length=LIL_STRING, blank=False)
    version = QVersionField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    description.help_text = "This may be overwritten by any descriptive text found in the categorization file."

    file = QFileField(upload_to=UPLOAD_PATH)

    is_registered = models.BooleanField(blank=False, default=False)
    last_registered_version = QVersionField(blank=True, null=True)

    # I need to handle CIM 1.x differently than CIM 2.x
    type = models.CharField(max_length=LIL_STRING, blank=False, choices=[(ct.get_type(), ct.get_name()) for ct in CIMTypes])

    def __unicode__(self):

        if self.version:
            return u"%s [%s]" % (self.name, self.version)
        else:
            return u"%s" % (self.name)

    def is_cim1(self):
        return self.type == CIMTypes.CIM1

    def is_cim2(self):
        return self.type == CIMTypes.CIM2

    def clean(self):
        # force name to be lowercase
        # this avoids hacky methods of ensuring case-insensitive uniqueness
        self.name = self.name.lower()

        # also, validate the file according to the correct schema...
        # (I can't set up this validation in the field definition)
        # (b/c the specific schema to validate against changes based on the type of QOntology)
        if self.is_cim2():
            schema_path = os.path.join(settings.STATIC_ROOT, APP_LABEL, "xml/qcategorization_2.xsd")
        elif self.is_cim1():
            schema_path = os.path.join(settings.STATIC_ROOT, APP_LABEL, "xml/qcategorization_1.xsd")
        else:
            msg = "Unable to determine the categorization type"
            raise QError(msg)
        try:
            validate_file_schema(self.file, schema_path)
        except ValidationError as e:
            raise ValidationError({"file": str(e)})

        # now do normal cleaning...
        return super(QCategorization, self).clean()

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

        if not self.ontologies.count():
            msg = "QCategorization '{0}' has not been associated with any ontologies.  It's kind of silly to register it now.".format(self)
            if request:
                messages.add_message(request, messages.WARNING, msg)
            q_logger.warn(msg)

        try:
            if self.is_cim2():
                self.register_cim2(**kwargs)

            elif self.is_cim1():
                self.register_cim1(**kwargs)

            else:
                msg = "Unable to determine the categorization type"
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

    def register_cim1(self, **kwargs):

        request = kwargs.pop("request", None)
        ontologies = self.ontologies.all()

        try:
            self.file.open()
            categorization_content = et.parse(self.file)
            self.file.close()
        except IOError as e:
            msg = "Error opening file: %s" % self.file
            if request:
                messages.add_message(request, messages.ERROR, msg)
            raise e

        # name can be anything...
        categorization_name = get_index(xpath_fix(categorization_content, "name/text()"), 0)
        # version should match(ish) the instance field...
        categorization_version = get_index(xpath_fix(categorization_content, "version/text()"), 0)
        if self.version.major() != Version(categorization_version).major():
            msg = "The major version of this categorization instance does not match the major version of the categorization file file"
            if request:
                messages.add_message(request, messages.WARNING, msg)
        # description can overwrite the instance field...
        categorization_description = get_index(xpath_fix(categorization_content, "description/text()"), 0)
        if categorization_description:
            self.description = remove_spaces_and_linebreaks(categorization_description)

        old_category_proxies = list(self.category_proxies.all())  # list forces qs evaluation immediately
        new_category_proxies = []

        for i, category_proxy in enumerate(xpath_fix(categorization_content, "//category"), start=1):

            category_proxy_categorization = self
            category_proxy_name = get_index(xpath_fix(category_proxy, "name/text()"), 0)
            category_proxy_key = get_index(xpath_fix(category_proxy, "key/text()"), 0)
            category_proxy_order = get_index(xpath_fix(category_proxy, 'order/text()'), 0)
            category_proxy_documentation = get_index(xpath_fix(category_proxy, "description/text()"), 0)
            if category_proxy_documentation:
                category_proxy_documentation = remove_spaces_and_linebreaks(category_proxy_documentation)

            (new_category_proxy, created_category) = QStandardCategoryProxy.objects.get_or_create(
                categorization=category_proxy_categorization,
                name=category_proxy_name,
            )

            new_category_proxy.documentation = category_proxy_documentation
            new_category_proxy.key = category_proxy_key or slugify(category_proxy_name)
            new_category_proxy.order = category_proxy_order or i

            if not created_category:
                # remove any existing relationships (going to replace them during this registration)...
                new_category_proxy.properties.clear()

            for j, field in enumerate(xpath_fix(categorization_content, "//field[category_key='%s']" % new_category_proxy.key)):

                model_name = get_index(xpath_fix(field, "./ancestor::model/name/text()"), 0)
                field_name = get_index(xpath_fix(field, "name/text()"), 0)

                for ontology in ontologies:
                    try:
                        model_proxy = ontology.model_proxies.get(name__iexact=model_name)
                        property_proxy = model_proxy.standard_properties.get(name__iexact=field_name)
                        new_category_proxy.properties.add(property_proxy)

                    except QModelProxy.DoesNotExist:
                        msg = "Unable to find QModel '%s' specified in QCategorization '%s'" % (model_name, self)
                        if request:
                            messages.add_message(request, messages.WARNING, msg)
                        else:
                            print(msg)
                            pass
                    except QStandardPropertyProxy.DoesNotExist:
                        msg = "Unable to find QStandardProperty '%s' specified in QCategorization '%s'" % (field_name, self)
                        if request:
                            messages.add_message(request, messages.WARNING, msg)
                        else:
                            print(msg)
                            pass

            new_category_proxy.save()
            new_category_proxies.append(new_category_proxy)

    def register_cim2(self, **kwargs):

        request = kwargs.pop("request", None)
        ontologies = self.ontologies.all()

        try:
            self.file.open()
            categorization_content = et.parse(self.file)
            self.file.close()
        except IOError as e:
            msg = "Error opening file: %s" % self.file
            if request:
                messages.add_message(request, messages.ERROR, msg)
            raise e

        # name can be anything...
        categorization_name = get_index(xpath_fix(categorization_content, "name/text()"), 0)
        # version should match(ish) the instance field...
        categorization_version = get_index(xpath_fix(categorization_content, "version/text()"), 0)
        if self.version.major() != Version(categorization_version).major():
            msg = "The major version of this categorization instance does not match the major version of the categorization file file"
            if request:
                messages.add_message(request, messages.WARNING, msg)
        # description can overwrite the instance field...
        categorization_description = get_index(xpath_fix(categorization_content, "description/text()"), 0)
        if categorization_description:
            self.description = remove_spaces_and_linebreaks(categorization_description)

        old_category_proxies = list(self.category_proxies.all())  # list forces qs evaluation immediately
        new_category_proxies = []

        for i, category_proxy in enumerate(xpath_fix(categorization_content, "//category"), start=1):

            category_proxy_categorization = self
            category_proxy_name = get_index(xpath_fix(category_proxy, "name/text()"), 0)
            category_proxy_key = get_index(xpath_fix(category_proxy, "key/text()"), 0)
            category_proxy_order = get_index(xpath_fix(category_proxy, 'order/text()'), 0)
            category_proxy_documentation = get_index(xpath_fix(category_proxy, "description/text()"), 0)
            if category_proxy_documentation:
                category_proxy_documentation = remove_spaces_and_linebreaks(category_proxy_documentation)

            (new_category_proxy, created_category) = QStandardCategoryProxy.objects.get_or_create(
                categorization=category_proxy_categorization,
                name=category_proxy_name,
            )

            new_category_proxy.documentation = category_proxy_documentation
            new_category_proxy.key = category_proxy_key or slugify(category_proxy_name)
            new_category_proxy.order = category_proxy_order or i

            if not created_category:
                # remove any existing relationships (going to replace them during this registration)...
                new_category_proxy.properties.clear()

            for j, field in enumerate(xpath_fix(categorization_content, "//field[category_key='{0}']".format(new_category_proxy.key))):

                fully_specified_model_name = get_index(xpath_fix(field, "./ancestor::model/name/text()"), 0)
                model_package, model_name = fully_specified_model_name.split('.')
                field_name = get_index(xpath_fix(field, "name/text()"), 0)

                for ontology in ontologies:
                    try:
                        model_proxy = ontology.model_proxies.get(package__iexact=model_package, name__iexact=model_name)
                        property_proxy = model_proxy.standard_properties.get(name__iexact=field_name)
                        new_category_proxy.properties.add(property_proxy)

                    except QModelProxy.DoesNotExist:
                        msg = "Unable to find QModel '%s' specified in QCategorization '%s'" % (model_name, self)
                        if request:
                            messages.add_message(request, messages.WARNING, msg)
                        else:
                            print(msg)
                            pass
                    except QStandardPropertyProxy.DoesNotExist:
                        msg = "Unable to find QStandardProperty '%s' specified in QCategorization '%s'" % (field_name, self)
                        if request:
                            messages.add_message(request, messages.WARNING, msg)
                        else:
                            print(msg)
                            pass

            new_category_proxy.save()
            new_category_proxies.append(new_category_proxy)

