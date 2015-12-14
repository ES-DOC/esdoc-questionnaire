####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.template.loader import render_to_string
from uuid import uuid4

from Q.questionnaire import APP_LABEL
from Q.questionnaire.q_constants import *
from Q.questionnaire.q_utils import QError
from Q.questionnaire.q_fields import PROPERTY_TYPE_CHOICES, QPropertyTypes
from Q.questionnaire.models.models_publications import QPublication, QPublicationFormats


class QModelQuerySet(models.QuerySet):
    """
    As of Django 1.7 I can use custom querysets as managers
    to ensure that these custom methods are chainable
    whoo-hoo
    """

    def root_documents(self):
        return self.filter(is_document=True, is_root=True)

    def published_documents(self):
        return self.filter(is_document=True, is_root=True, is_published=True)

    # TODO: WRITE SOMETHING LIKE A "labelled_documents" QS


class QModel(MPTTModel):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "Questionnaire Model Realization"
        verbose_name_plural = "_Questionnaire Realizations: Models"
        ordering = ("created", )

    objects = QModelQuerySet.as_manager()

    guid = models.UUIDField(default=uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now_add=True, editable=False)
    version = models.CharField(blank=False, default="0.0", max_length=LIL_STRING)

    name = models.CharField(max_length=LIL_STRING, blank=True)
    description = models.TextField(blank=True)

    ontology = models.ForeignKey("QOntology", blank=False, related_name="models")
    proxy = models.ForeignKey("QModelProxy", blank=False, related_name="models")
    project = models.ForeignKey("QProject", blank=False, related_name="models")

    is_document = models.BooleanField(blank=False, null=False, default=False)
    is_root = models.BooleanField(blank=False, null=False, default=False)
    is_complete = models.BooleanField(blank=False, null=False, default=False)
    is_published = models.BooleanField(blank=False, null=False, default=False)

    is_active = models.BooleanField(blank=False, null=False, default=True)

    parent = TreeForeignKey("self", null=True, blank=True, related_name="children")

    synchronization = models.ManyToManyField("QSynchronization", blank=True)

    def is_synchronized(self):
        unsynchronized_types = self.synchronization.all()
        return not unsynchronized_types  # checks if qs is empty

    def is_unsynchronized(self):
        return not self.is_synchronized()

    def get_major_version(self):
        major, minor = self.version.split(".")
        return major

    def get_minor_version(self):
        major, minor = self.version.split(".")
        return minor

    def increment_major_version(self):
        major, minor = self.version.split(".")
        major = int(major) + 1
        self.version = u"%s.%d" % (major, 0)

    def increment_minor_version(self):
        major, minor = self.version.split(".")
        minor = int(major) + 1
        self.version = u"%s.%d" % (major, minor)

    def get_label(self):
        try:
            label_property = self.standard_properties.get(is_label=True)
            return label_property.get_value()
        except QStandardProperty.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        increment_version = kwargs.pop("increment_version", True)
        if increment_version:
            self.increment_minor_version()
        super(QModel, self).save(*args, **kwargs)

    def publish(self, force_save=True, format=QPublicationFormats.ESDOC_XML):

        """
        :param force_save: save the model (after incrementing its version);
        the only reason not to do this is when re-publishing something at the same version b/c of a content error
        :return:
        """
        assert self.is_complete

        major_version = int(self.get_major_version())
        if force_save:
            major_version += 1

        if format == QPublicationFormats.ESDOC_XML:

            publication = self.publish_esdoc_xml(version=major_version)

        else:
            msg = "Unknown publication format: '%s'" % format
            raise QError(msg)

        if force_save:
            self.increment_major_version()
            self.is_published = True
            self.save(increment_version=False)  # I've already fiddled w/ the version; don't increment the minor version

        return publication

    def publish_esdoc_xml(self, **kwargs):

        version = kwargs.pop("version")

        # if publish was called w/ "force_save=False" then version will not have been changed relative to the last publication
        # this means that the following code will modify an existing publication rather than create a new one
        (publication, created_publication) = QPublication.objects.get_or_create(
            model=self,
            name=str(self.guid),
            format=QPublicationFormats.ESDOC_XML.get_type(),
            version=version
        )

        publication_dict = {
            "project": self.project,
            "proxy": self.proxy,
            "model": self,
        }
        publication_template_path = "questionnaire/publications/ESDOC_XML/%s.xml" % self.proxy.name.lower()
        publication_content = render_to_string(publication_template_path, publication_dict)
        publication.content = publication_content
        publication.save()

        return publication

class QProperty(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = True

    guid = models.UUIDField(default=uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now_add=True, editable=False)

    field_type = models.CharField(max_length=LIL_STRING, blank=False, choices=PROPERTY_TYPE_CHOICES)

    def get_value(self):
        field_type = self.field_type
        if field_type == QPropertyTypes.ATOMIC:
            return self.atomic_value
        else:
            msg = "todo: get_value()"
            raise QError(msg)
        # elif field_type == QPropertyTypes.ENUMERATION:
        #     # TODO: DEAL w/ "OTHER"
        # else:  # QPropertyTypes.RELATIONSHIP
        #     return self.relationship_value

class QStandardProperty(QProperty):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "Questionnaire Standard Property Realization"
        verbose_name_plural = "_Questionnaire Realizations: Standard Properties"

    model = models.ForeignKey("QModel", blank=False, related_name="standard_properties")
    proxy = models.ForeignKey("QStandardPropertyProxy", blank=False)

    is_label = models.BooleanField(blank=False, default=False)
    name = models.CharField(max_length=LIL_STRING, blank=True)

    atomic_value = models.TextField(max_length=HUGE_STRING, blank=True, null=True)


class QScientificProperty(QProperty):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "Questionnaire Scientific Property Realization"
        verbose_name_plural = "_Questionnaire Realizations: Scientific Properties"

    model = models.ForeignKey("QModel", blank=False, related_name="scientific_properties")
