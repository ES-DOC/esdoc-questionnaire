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
from django.utils.translation import ugettext_lazy as _

from uuid import uuid4

from Q.questionnaire import APP_LABEL, q_logger
from Q.questionnaire.q_fields import QPropertyTypes, QAtomicTypes, QJSONField
from Q.questionnaire.q_utils import QError, EnumeratedType, EnumeratedTypeList, pretty_string, validate_no_spaces, legacy_code
from Q.questionnaire.q_constants import *

###################
# local constants #
###################

UNCATEGORIZED_CATEGORY_PROXY_NAME = "uncategorized"
UNCATEGORIZED_CATEGORY_PROXY_PACKAGE = "uncategorized"


class ProxyType(EnumeratedType):

    def __str__(self):
        return "{0}".format(self.get_name())

ProxyTypes = EnumeratedTypeList([
    ProxyType("MODEL", "Model Realization"),
    ProxyType("CATEGORY", "Category Realization"),
    ProxyType("PROPERTY", "Property Realization"),
])

###################
# some helper fns #
###################


def get_enumeration_choices_schema():
    classes_schema = QCONFIG_SCHEMA["properties"]["classes"]["properties"]["defined"]["items"]
    properties_schema = classes_schema["properties"]["properties"]["properties"]["defined"]["items"]
    enumeration_members_schema = properties_schema["properties"]["enumeration_members"]
    return enumeration_members_schema


def get_label_schema():
    classes_schema = QCONFIG_SCHEMA["properties"]["classes"]["properties"]["defined"]["items"]
    classes_label_schema = classes_schema["properties"]["label"]
    return classes_label_schema


def get_values_schema():
    classes_schema = QCONFIG_SCHEMA["properties"]["classes"]["properties"]["defined"]["items"]
    properties_schema = classes_schema["properties"]["properties"]["properties"]["defined"]["items"]
    properties_values_schema = properties_schema["properties"]["values"]
    return properties_values_schema


def recurse_through_proxies(current_model_proxy, proxy_types, **kwargs):
    """
    recursively gathers all proxies of a certain type
    :param current_model_proxy: the model proxy from which to begin checking
    :param realization_types: the types of proxies to check
    :return: a set of proxies
    """

    all_proxies = kwargs.pop("all_proxies", set())

    for property_proxy in current_model_proxy.property_proxies.all():

        if property_proxy not in all_proxies:

            if ProxyTypes.PROPERTY in proxy_types:
                all_proxies.add(property_proxy)

            if property_proxy.field_type == QPropertyTypes.RELATIONSHIP:
                for target_model_proxy in property_proxy.relationship_target_models.all():
                    recurse_through_proxies(
                        target_model_proxy,
                        proxy_types,
                        all_proxies=all_proxies,
                    )

    for category_proxy in current_model_proxy.category_proxies.all():
        if ProxyTypes.CATEGORY in proxy_types:
            all_proxies.add(category_proxy)

    if ProxyTypes.MODEL in proxy_types:
        all_proxies.add(current_model_proxy)

    return all_proxies

#####################
# the actual models #
#####################


class QProxy(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = True

    guid = models.UUIDField(default=uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    order = models.PositiveIntegerField(blank=True, null=True)
    is_meta = models.NullBooleanField()

    name = models.CharField(max_length=SMALL_STRING, blank=False)
    documentation = models.TextField(blank=True, null=True)

    cim_id = models.CharField(
        blank=True, null=True, unique=True,
        max_length=SMALL_STRING, validators=[validate_no_spaces],
        help_text=_(
            "A unique, CIM-specific, identifier.  "
            "This is distinct from the automatically-generated key.  "
            "It is required for distinguishing specialized objects of the same class."
        )
    )

    def __eq__(self, other):
        if isinstance(other, QProxy):
            return self.guid == other.guid
        return NotImplemented

    def __ne__(self, other):
        equality_result = self.__eq__(other)
        if equality_result is NotImplemented:
            return equality_result
        return not equality_result

    def __str__(self):
        # return self.cim_id
        return pretty_string(self.name)

    def save(self, *args, **kwargs):
        """
        overloads the save method to ensure that blank cim_id fields are not used in the unique validation
        (null field values are ignored, while blank strings are not)
        :param args:
        :param kwargs:
        :return:
        """
        if not self.cim_id:
            self.cim_id = None
        super(QProxy, self).save(*args, **kwargs)

    @property
    def key(self):
        # convert self.guid to str b/c UUID does not play nicely w/ JSON
        return str(self.guid)

    def reset(self, **kwargs):
        msg = "{0} must define a custom 'reset' method.".format(self.__class__.__name__)
        raise NotImplementedError(msg)


class QModelProxyManager(models.Manager):

    # used when getting inherited / excluded models from an ontology...

    def in_fully_qualified_names(self, fully_qualified_names):
        all_model_proxies = self.get_queryset()
        fully_qualified_pks = [
            all_model_proxies.get(name=name, package=package).pk
            for package, name in [fully_qualified_name.split('.') for fully_qualified_name in fully_qualified_names]
        ]
        return all_model_proxies.filter(pk__in=fully_qualified_pks)


class QModelProxy(QProxy):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "_Questionnaire Proxy: Model"
        verbose_name_plural = "_Questionnaire Proxy: Models"
        unique_together = ("ontology", "name", "package", "cim_id")
        # TODO: I HAD TO ADD "ordering" TO THE META OPTIONS ONCE THE CIM2 GENERATORS NO LONGER CREATED PROXIES IN A SENSIBLE ORDER
        # TODO: FIRSTLY, I WOULD LIKE TO ADD THIS PROPERTY TO THE ABSTRACT BASE CLASS INSTEAD OF EACH CHILD CLASS EXPLICITLY
        # TODO: SECONDLY, THIS INTRODUCES AN EXTRA DB HIT FOR EVERY PROXY QS
        # TODO: THIRDLY, IN PREVIOUS VERSIONS OF THE Q I DID AWAY W/ EXPLICLIT ORDERING (IN ORDER TO ALLOW INSTANCES TO BE RE-ORDERED IN THE CLIENT); SHOULDN'T I STILL BE DOING THAT?
        ordering = ["order"]

    objects = QModelProxyManager()

    ontology = models.ForeignKey("QOntology", blank=True, null=True, related_name="model_proxies")

    # property_proxies = models.ManyToManyField("QPropertyProxy", blank=True, related_name="model_proxies")
    # category_proxies = models.ManyToManyField("QCategoryProxy", blank=True, related_name="model_proxies")

    package = models.CharField(max_length=SMALL_STRING, blank=False)

    is_document = models.NullBooleanField()
    label = QJSONField(blank=True, null=True, schema=get_label_schema)

    def fully_qualified_key(self):
        return "{0}.{1}".format(
            self.ontology.guid,
            self.key,
        )

    @property
    def fully_qualified_name(self):
        if self.cim_id is not None:
            return self.cim_id
        else:
            return "{0}.{1}".format(
                self.ontology,
                self.name,
            )

    @property
    def has_hierarchical_properties(self):
        return self.property_proxies.hierarchical().count() > 0

    def reset(self, **kwargs):
        force_save = kwargs.pop("force_save", False)
        if force_save:
            self.save()


class QCategoryProxy(QProxy):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "_Questionnaire Proxy: Category"
        verbose_name_plural = "_Questionnaire Proxy: Categories"
        unique_together = ("model_proxy", "name", "cim_id")
        # TODO: SEE THE COMMENTS REGARDING "ordering" FOR QModelProxy ABOVE
        ordering = ["order"]

    ontology = models.ForeignKey("QOntology", blank=True, null=True, related_name="category_proxies")

    model_proxy = models.ForeignKey("QModelProxy", blank=False, related_name="category_proxies")

    is_uncategorized = models.BooleanField(default=False)
    is_uncategorized.help_text = _(
        "An 'uncategorized' category is one which was not specified by the CIM; it acts as a placeholder within which to nest properties in the Questionnaire."
    )

    def fully_qualified_key(self):
        return "{0}.{1}".format(
            self.model_proxy.get_fully_qualified_key(),
            self.key,
        )

    def has_property(self, property_proxy):
        return property_proxy in self.property_proxies.all()

    def reset(self, **kwargs):
        force_save = kwargs.pop("force_save", False)
        if force_save:
            self.save()


class QPropertyProxyManager(models.Manager):

    # used when getting inherited / excluded properties from an ontology...

    # NO LONGER USED; PROPERTIES NO LONGER HAVE QUALIFYING PACKAGES, SO INSTEAD I CAN JUST CALL SOMETHING LIKE
    # "property_proxies.filter(name__in=list_of_property_names)"
    @legacy_code
    def in_fully_qualified_names(self, fully_qualified_names):
        all_property_proxies = self.get_queryset()
        fully_qualified_pks = [
            all_property_proxies.get(name=name, package=package).pk
            for package, name in [fully_qualified_name.split('.') for fully_qualified_name in fully_qualified_names]
            ]
        return all_property_proxies.filter(pk__in=fully_qualified_pks)

    def hierarchical(self):
        return self.get_queryset().filter(is_hierarchical=True)


class QPropertyProxy(QProxy):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "_Questionnaire Proxy: Property"
        verbose_name_plural = "_Questionnaire Proxy: Properties"
        # unique_together = ("model_proxy", "name")
        # TODO: SEE THE COMMENTS REGARDING "ordering" FOR QModelProxy ABOVE
        ordering = ["order"]

    objects = QPropertyProxyManager()

    ontology = models.ForeignKey("QOntology", blank=True, null=True, related_name="property_proxies")

    model_proxy = models.ForeignKey("QModelProxy", blank=False, related_name="property_proxies")

    category_proxy = models.ForeignKey("QCategoryProxy", blank=True, null=True, related_name="property_proxies")

    # as w/ relationships below, it takes 2 fields to setup categories...
    # the id is specified in the specialization & used in the "QPropertyProxy.reset" fn to actually link to the correct category_proxy
    category_id = models.CharField(blank=True, null=True, max_length=SMALL_STRING)

    field_type = models.CharField(
        max_length=SMALL_STRING, blank=False,
        choices=[(pt.get_type(), pt.get_name()) for pt in QPropertyTypes],
    )
    # despite all of the effort going into QCardinalityField, I never actually expose it
    # so I am just using basic built-in fields instead (b/c they were needlessly complicated)...
    cardinality_min = models.CharField(max_length=2, blank=False, choices=CARDINALITY_MIN_CHOICES)
    cardinality_max = models.CharField(max_length=2, blank=False, choices=CARDINALITY_MAX_CHOICES)
    is_nillable = models.BooleanField(default=True)

    is_hierarchical = models.BooleanField(default=False)

    # the schema is generic enough that I can store the default value of any proxy field_type here...
    values = QJSONField(blank=True, null=True, schema=get_values_schema)

    # atomic_default
    atomic_type = models.CharField(
        max_length=SMALL_STRING, blank=True, null=True,
        choices=[(at.get_type(), at.get_name()) for at in QAtomicTypes],
    )
    enumeration_is_open = models.BooleanField(default=False)
    enumeration_choices = QJSONField(blank=True, null=True, schema=get_enumeration_choices_schema)
    # it takes 2 fields to setup relationships...
    # (b/c I can't add models until all proxies have been registered)
    relationship_target_names = QJSONField(blank=True, null=True)  # overloading JSON just to store a list (b/c Django doesn't have a built-in list field)
    relationship_target_models = models.ManyToManyField("QModelProxy", blank=True)

    def fully_qualified_key(self):
        return "{0}.{1}".format(
            self.model_proxy.get_fully_qualified_key(),
            self.key,
        )

    @property
    def is_optional(self):
        return int(self.cardinality_min) == 0

    @property
    def is_required(self):
        return not self.is_optional

    @property
    def is_infinite(self):
        return self.cardinality_max == CARDINALITY_INFINITE

    @property
    def is_multiple(self):
        return self.is_infinite or int(self.cardinality_max) > 1

    @property
    def is_single(self):
        return int(self.cardinality_max) == 1

    @property
    def use_references(self):
        """
        As of v0.14 all RELATIONSHIPS to a CIM Document _must_ use a reference
        :return: Boolean
        """
        if self.field_type == QPropertyTypes.RELATIONSHIP:
            target_models_are_documents = [tm.is_document for tm in self.relationship_target_models.all()]
            assert len(set(target_models_are_documents)) == 1
            return all(target_models_are_documents)
        return False

    @property
    def use_subforms(self):
        """
        As of v0.14 all RELATIONSHIPS to a CIM Entity (non-Document) _must_ use a subform
        :return: Boolean
        """
        if self.field_type == QPropertyTypes.RELATIONSHIP:
            target_models_are_documents = [tm.is_document for tm in self.relationship_target_models.all()]
            assert len(set(target_models_are_documents)) == 1
            return not any(target_models_are_documents)
        return False

    def reset(self, **kwargs):
        force_save = kwargs.pop("force_save", False)

        # category_id = self.category_id
        # if category_id:
        #     self.category_proxy = self.model_proxy.category_proxies.get(cim_id=category_id)

        if self.is_hierarchical:
            assert self.field_type == QPropertyTypes.RELATIONSHIP

        if self.field_type == QPropertyTypes.ATOMIC:
            assert self.atomic_type is not None

        elif self.field_type == QPropertyTypes.ENUMERATION:
            pass

        else:  # self.field_type == QPropertyTypes.RELATIONSHIP

            self.relationship_target_models.clear()
            for relationship_target in self.relationship_target_names:
                # relationship_target_package, relationship_target_name = relationship_target.split('.')
                if self.values:
                    # if this is specialized, there will be further constraints on which target objects to point to...
                    for relationship_target_value in self.values:
                        try:
                            relationship_target_model = QModelProxy.objects.get(
                                # ontology=ontology,
                                # package=relationship_target_package,
                                # name=relationship_target_name,
                                cim_id=relationship_target_value
                            )
                            self.relationship_target_models.add(relationship_target_model)
                        except QModelProxy.DoesNotExist:
                            msg = "unable to locate model '{0}'".format(relationship_target)
                            raise QError(msg)
                else:
                    # if this is not specialized, just use the unconstrained target...
                    try:
                        relationship_target_model = QModelProxy.objects.get(
                            # ontology=ontology,
                            # package=relationship_target_package,
                            # name=relationship_target_name
                            cim_id=relationship_target
                        )
                        self.relationship_target_models.add(relationship_target_model)
                    except QModelProxy.DoesNotExist:
                        msg = "unable to locate model '{0}'".format(relationship_target)
                        raise QError(msg)
        if force_save:
            self.save()
