__author__ = 'allyn.treshansky'

from django.db import models
from django.template.defaultfilters import slugify
from mptt.models import MPTTModel, TreeForeignKey
from uuid import uuid4

from Q.questionnaire import APP_LABEL, q_logger
from Q.questionnaire.q_fields import QCardinalityField, QJSONField, QPropertyTypes, QAtomicPropertyTypes
from Q.questionnaire.q_utils import QError, EnumeratedType, EnumeratedTypeList, pretty_string
from Q.questionnaire.q_constants import *

###############
# global vars #
###############

class ProxyType(EnumeratedType):

    def __unicode__(self):
        return u"%s" % (self.get_name())

ProxyTypes = EnumeratedTypeList([
    ProxyType("MODEL", "Model Proxy"),
    ProxyType("CATEGORY", "Category Proxy"),
    ProxyType("PROPERTY", "Property Proxy"),
])

##############
# global fns #
##############

def get_default_parent_model_proxy(current_proxy, proxy_type):
    if proxy_type == ProxyTypes.PROPERTY:
        return get_default_parent_model_proxy_aux(current_proxy.model_proxy)
    elif proxy_type == ProxyTypes.CATEGORY:
        raise NotImplementedError()
        # model_proxies = [p.model_proxy for p in current_proxy.property_proxies.all()]
        # for model_proxy in model_proxies:
        #     pass
    else:  # proxy_type == ProxyTypes.MODEL
        return get_default_parent_model_proxy_aux(current_proxy)

def get_default_parent_model_proxy_aux(current_model_proxy):
    # works its way up the recursive hierarchy until a root document model proxy is found
    pass


######################
# the actual classes #
######################

class QProxy(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = True
        verbose_name = "_Questionnaire Proxy"
        verbose_name_plural = "_Questionnaire Proxies"
        # ordering = ("order", )  # this is an abstract class, 'ordering' attribute belongs on concrete classes

    guid = models.UUIDField(default=uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    name = models.CharField(max_length=SMALL_STRING, blank=False)
    documentation = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(blank=True, null=True)

    is_meta = models.BooleanField(default=False)
    is_specialized = models.BooleanField(default=False)

    def __eq__(self, other):
        if isinstance(other, QProxy ):
            return self.guid == other.guid
        return NotImplemented

    def __ne__(self, other):
        equality_result = self.__eq__(other)
        if equality_result is NotImplemented:
            return equality_result
        return not equality_result

    def __str__(self):
        return pretty_string(self.name)

    def get_fully_qualified_key(self, parent_key=None):
        msg = "{0} must define a custom 'get_fully_qualified_key' method.".format(self.__class__.__name__)
        raise NotImplementedError(msg)

    def reset(self):
        msg = "{0} must define a custom 'reset' method.".format(self.__class__.__name__)
        raise NotImplementedError(msg)


class QModelProxy(QProxy):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "_Questionnaire Proxy: Model"
        verbose_name_plural = "_Questionnaire Proxies: Models"
        ordering = ("order", )

    ontology = models.ForeignKey("QOntology", blank=False, null=False, related_name="model_proxies")

    package = models.CharField(max_length=SMALL_STRING, blank=True, null=True)
    stereotype = models.CharField(
        choices=[(slugify(cs), cs) for cs in CIM_MODEL_STEREOTYPES],
        max_length=BIG_STRING, blank=True, null=True,
    )

    def get_fully_qualified_key(self, prefix=None):
        fully_qualified_key = "{0}.{1}".format(self.ontology.get_fully_qualified_key(), self.guid)
        if prefix:
            return "{0}.{1}".format(prefix, fully_qualified_key)
        return fully_qualified_key

    def is_document(self):
        if self.stereotype:
            return self.stereotype.lower() == "document"
        return False

    def reset(self):
        self.is_specialized = self.ontology.is_specialization()


class QCategoryProxy(QProxy):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "_Questionnaire Proxy: Category"
        verbose_name_plural = "_Questionnaire Proxies: Categories"
        ordering = ("order", )

    categorization = models.ForeignKey("QCategorization", blank=False, related_name="category_proxies")

    # property_proxies is accessed via the reverse lookup from the 'category' field of 'QPropertyProxy'

    # 'name,' 'order,' & 'description,' fields are inherited from QProxy

    def get_fully_qualified_key(self, prefix=None):
        fully_qualified_key = "{0}".format(self.guid)
        if prefix:
            return "{0}.{1}".format(prefix, fully_qualified_key)
        return fully_qualified_key

    def get_key(self):
        # even though categories have human-readable keys defined in categorization files,
        # internally, I want to use guids just to make them similar to all other proxies
        return str(self.guid)

    def has_property(self, property_proxy):
        return property_proxy in self.property_proxies.all()

class QPropertyProxy(QProxy):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "_Questionnaire Proxy: Property"
        verbose_name_plural = "_Questionnaire Proxies: Properties"
        ordering = ("order", )

    model_proxy = models.ForeignKey("QModelProxy", blank=False, related_name="property_proxies")

    stereotype = models.CharField(
        choices=[(slugify(cs), cs) for cs in CIM_PROPERTY_STEREOTYPES],
        max_length=BIG_STRING, blank=True, null=True,
    )

    cardinality = QCardinalityField(blank=False)
    is_nillable = models.BooleanField(default=True)
    field_type = models.CharField(
        choices=[(pt.get_type(), pt.get_name()) for pt in QPropertyTypes],
        max_length=SMALL_STRING, blank=False,
    )
    category = models.ForeignKey("QCategoryProxy", blank=True, null=True, related_name="property_proxies")

    # ATOMIC fields...
    atomic_default = models.CharField(max_length=BIG_STRING, blank=True, null=True)
    atomic_type = models.CharField(
        choices=[(pt.get_type(), pt.get_name()) for pt in QAtomicPropertyTypes],
        default=QAtomicPropertyTypes.DEFAULT.get_type(),
        max_length=SMALL_STRING, blank=False,
    )

    # ENUMERATION fields...
    enumeration = QJSONField(blank=True, null=True)
    enumeration_open = models.BooleanField(default=False)
    enumeration_multi = models.BooleanField(default=False)

    # RELATIONSHIP fields...
    relationship_target_names = models.TextField(blank=False, default="")  # set during registration
    #relationship_target_models = models.ManyToManyField("QModelProxy", blank=True, related_name="+")  # set during reset (after everything has been registered)
    relationship_target_models = models.ManyToManyField("QModelProxy", blank=True, related_name="parent_property_proxies")  # set during reset (after everything has been registered)

    def get_fully_qualified_key(self, prefix=None):
        fully_qualified_key = "{0}.{1}".format(self.model_proxy.get_fully_qualified_key(), self.guid)
        if prefix:
            return "{0}.{1}".format(prefix, fully_qualified_key)
        return fully_qualified_key

    def is_multiple(self):
        cardinality_max = self.get_cardinality_max()
        return cardinality_max == u'*' or int(cardinality_max) > 1

    def is_optional(self):
        return not self.is_required()

    def is_required(self):
        cardinality_min = self.get_cardinality_min()
        return int(cardinality_min) > 0

    def is_single(self):
        return not self.is_multiple()

    def reset(self):

        if self.field_type == QPropertyTypes.ATOMIC:
            pass

        elif self.field_type == QPropertyTypes.ENUMERATION:
            pass

        elif self.field_type == QPropertyTypes.RELATIONSHIP:

            ontology = self.model_proxy.ontology

            self.relationship_target_models.clear()
            target_names = self.relationship_target_names.split('|')
            for target_name in target_names:
                try:
                    if '.' in target_name:
                        package, name = target_name.split('.')
                        target_model = QModelProxy.objects.get(
                            ontology=ontology,
                            package__iexact=package,
                            name__iexact=name
                        )
                    else:
                        target_model = QModelProxy.objects.get(
                            ontology=ontology,
                            name__iexact=target_name
                        )
                    self.relationship_target_models.add(target_model)
                except QModelProxy.DoesNotExist:
                    msg = "unable to locate model '{0}'".format(target_name)
                    raise QError(msg)

    # TODO: THESE NEXT 2 FNS ARE REPEATED IN QPropetyCustomization

    def use_references(self):
        """
        As of v0.14 all RELATIONSHIPS to a CIM Document _must_ use a reference
        :return: Boolean
        """
        if self.field_type == QPropertyTypes.RELATIONSHIP:
            target_models_are_documents = [tm.is_document() for tm in self.relationship_target_models.all()]
            # double-check that all targets are the same type of class...
            assert len(set(target_models_are_documents)) == 1
            return all(target_models_are_documents)
        return False

    def use_subforms(self):
        """
        As of v0.14 all RELATIONSHIPS to a CIM Entity (non-Document) _must_ use a subform
        :return: Boolean
        """
        if self.field_type == QPropertyTypes.RELATIONSHIP:
            target_models_are_documents = [tm.is_document() for tm in self.relationship_target_models.all()]
            # double-check that all targets are the same type of class...
            assert len(set(target_models_are_documents)) == 1
            return not any(target_models_are_documents)
        return False
