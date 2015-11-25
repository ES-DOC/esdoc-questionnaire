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
from django.template.defaultfilters import slugify
from mptt.models import MPTTModel, TreeForeignKey
from uuid import uuid4

from Q.questionnaire import APP_LABEL
from Q.questionnaire.q_fields import PROPERTY_TYPE_CHOICES, ATOMIC_PROPERTY_TYPE_CHOICES, QPropertyTypes, QAtomicPropertyTypes, QCardinalityField
from Q.questionnaire.q_utils import QError, validate_no_spaces, pretty_string
from Q.questionnaire.q_constants import *

def get_existing_proxy_set(ontology=None, proxy=None, vocabularies=[]):

    # TODO: DEAL W/ STANDARD & SCIENTIFIC PROXIES

    assert proxy.ontology == ontology

    proxy_set = {
        "model_proxy": proxy,
        # "standard_category_proxies": proxy.standard_category_proxies.all(),
        "standard_property_proxies": proxy.standard_properties.all(),
        # "scientific_category_proxies": [],
        "scientific_property_proxies": [],
    }

    for vocabulary in vocabularies:
        for component_proxy in vocabulary.component_proxies.all():
            # proxy_set["scientific_category_proxies"].append(component_proxy.scientific_category_proxies.all())
            proxy_set["scientific_property_proxies"] += component_proxy.scientific_property_proxies.all()

    return proxy_set

class QProxy(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = True
        ordering = ("order", )  # TODO: CHECK IF ORDERING HAS TO BE SET ON NON-ABSTRACT FIELDS!

    guid = models.UUIDField(default=uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now_add=True, editable=False)

    name = models.CharField(max_length=SMALL_STRING, blank=False)
    documentation = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(blank=True, null=True)

    def __unicode__(self):

        return pretty_string(self.name)


class QModelProxy(QProxy):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "Questionnaire Model Proxy"
        verbose_name_plural = "_Questionnaire Proxies: Models"
        ordering = ("order", )

    ontology = models.ForeignKey("QOntology", blank=False, related_name="model_proxies")

    stereotype = models.CharField(
        max_length=BIG_STRING, blank=True, null=True,
        choices=[(slugify(stereotype), stereotype) for stereotype in CIM_MODEL_STEREOTYPES]
    )
    namespace = models.CharField(max_length=BIG_STRING, blank=True, null=True)
    package = models.CharField(max_length=BIG_STRING, blank=True, null=True)

    def is_document(self):
        return self.stereotype and self.stereotype.lower() == "document"


class QPropertyProxy(QProxy):

    class Meta:
        app_label = APP_LABEL
        abstract = True

    cardinality = QCardinalityField(blank=False)
    field_type = models.CharField(max_length=SMALL_STRING, blank=False, null=True, choices=PROPERTY_TYPE_CHOICES)

    def is_required(self):
        return int(self.get_cardinality_min()) > 0

    def is_optional(self):
        return not self.is_required()


class QStandardPropertyProxy(QPropertyProxy):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        unique_together = ("model_proxy", "name",)
        verbose_name = "Questionnaire Standard Property Proxy"
        verbose_name_plural = "_Questionnaire Proxies: Standard Properties"
        ordering = ("order", )

    model_proxy = models.ForeignKey("QModelProxy", blank=False, related_name="standard_properties")

    stereotype = models.CharField(max_length=BIG_STRING, blank=True, null=True, choices=[(slugify(cs), cs) for cs in CIM_PROPERTY_STEREOTYPES])
    namespace = models.CharField(max_length=BIG_STRING, blank=True, null=True, choices=[(slugify(cn), cn) for cn in CIM_NAMESPACES])

    is_label = models.BooleanField(blank=False, default=False)

    # ATOMIC fields
    atomic_default = models.CharField(max_length=BIG_STRING, blank=True, null=True)
    atomic_type = models.CharField(max_length=LIL_STRING, blank=True, null=True, choices=ATOMIC_PROPERTY_TYPE_CHOICES)

    # ENUMERATION fields
    enumeration_choices = models.TextField(blank=True, null=True)
    enumeration_open = models.BooleanField(default=False)
    enumeration_multi = models.BooleanField(default=False)
    enumeration_nullable = models.BooleanField(default=False)

    # RELATIONSHIP fields
    relationship_target_name = models.CharField(max_length=BIG_STRING, blank=True, null=True)  # set during registration
    relationship_target_model = models.ForeignKey("QModelProxy", blank=True, null=True)  # set during reset (after all models have been registered)

    def reset(self):

        if self.field_type == QPropertyTypes.ATOMIC:
            pass

        elif self.field_type == QPropertyTypes.ENUMERATION:
            pass

        elif self.field_type == QPropertyTypes.RELATIONSHIP:
            ontology = self.model_proxy.ontology
            target_name = self.relationship_target_name
            try:
                target_model = QModelProxy.objects.get(ontology=ontology, name__iexact=target_name)
                self.relationship_target_model = target_model
            except QModelProxy.DoesNotExist:
                msg = "unable to locate model '%s' in ontology '%s'" % (target_name, ontology)
                raise QError(msg)


SCIENTIFIC_PROPERTY_CHOICES = [
    ("XOR", "XOR"),
    ("OR", "OR"),
    ("keyboard", "keyboard"),
]

class QScientificPropertyProxy(QPropertyProxy):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        unique_together = ("component_proxy", "category", "name",)
        verbose_name = "Questionnaire Scientific Property Proxies"
        verbose_name_plural = "_Questionnaire Proxies: Scientific Properties"
        ordering = ("order", )

    component_proxy = models.ForeignKey("QComponentProxy", blank=False, related_name="scientific_property_proxies")
    category = models.ForeignKey("QScientificCategoryProxy", blank=True, null=True, related_name="properties")

    choice = models.CharField(max_length=LIL_STRING, blank=True, null=True, choices=SCIENTIFIC_PROPERTY_CHOICES)

    # ATOMIC fields
    atomic_default = models.CharField(max_length=BIG_STRING, blank=True, null=True)
    atomic_type = models.CharField(max_length=LIL_STRING, blank=True, null=True, choices=ATOMIC_PROPERTY_TYPE_CHOICES)

    # ENUMERATION fields
    enumeration_choices = models.TextField(blank=True, default=u"")
    enumeration_open = models.BooleanField(default=False)
    enumeration_multi = models.BooleanField(default=False)
    enumeration_nullable = models.BooleanField(default=False)

    # scientific properties cannot be RELATIONSHIPS

    def __init__(self, *args, **kwargs):
        super(QScientificPropertyProxy, self).__init__(*args, **kwargs)

        if self.field_type == QPropertyTypes.RELATIONSHIP:
            msg = "QScientificPropertyProxies cannot be RELATIONSHIPS"
            raise QError(msg)

    def reset(self):

        if self.choice == "keyboard":
            self.field_type = QPropertyTypes.ATOMIC
            self.atomic_type = QAtomicPropertyTypes.DEFAULT

        else:
            self.field_type = QPropertyTypes.ENUMERATION
            if self.choice == "XOR":
                self.enumeration_multi = False
            else:  # self.choice == "OR"
                self.enumeration_multi = True



class QCategoryProxy(QProxy):

    class Meta:
        app_label = APP_LABEL
        abstract = True

    key = models.CharField(max_length=SMALL_STRING, blank=True, validators=[validate_no_spaces, ])

    def get_key(self):
        return self.key


class QStandardCategoryProxy(QCategoryProxy):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        unique_together = ("categorization", "name")
        verbose_name = "Questionnaire Standard Category Proxy"
        verbose_name_plural = "_Questionnaire Proxies: Standard Categories"
        ordering = ("order", )

    categorization = models.ForeignKey("QCategorization", blank=False, related_name="category_proxies")
    properties = models.ManyToManyField("QStandardPropertyProxy", blank=True, related_name="category")

    def has_property(self, property_proxy):
        return property_proxy in self.properties.all()


class QScientificCategoryProxy(QCategoryProxy):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        unique_together = ("component_proxy", "name")
        verbose_name = "Questionnaire Scientific Category Proxy"
        verbose_name_plural = "_Questionnaire Proxies: Scientific Categories"
        ordering = ("order", )

    component_proxy = models.ForeignKey("QComponentProxy", blank=False, related_name="category_proxies")
    # defining properties as a reverse reletaionship on QScientificPropertyProxy
    # properties = models.ManyToManyField("QScientificPropertyProxy", blank=True, related_name="category")

    def has_property(self, property_proxy):
        return property_proxy in self.properties.all()

class QComponentProxy(MPTTModel):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        unique_together = ("vocabulary", "name")
        verbose_name = "Questionnaire Component Proxy"
        verbose_name_plural = "_Questionnaire Proxies: Components"
        ordering = ("order", )

    guid = models.UUIDField(default=uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now_add=True, editable=False)

    name = models.CharField(max_length=SMALL_STRING, blank=False)
    documentation = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(blank=True, null=True)

    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')

    vocabulary = models.ForeignKey("QVocabulary", blank=False, related_name="component_proxies")

    def __unicode__(self):
        return "{0}".format(self.name)

    def get_key(self):
        return str(self.guid)
