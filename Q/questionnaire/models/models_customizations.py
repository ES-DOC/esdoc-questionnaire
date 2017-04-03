####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from collections import OrderedDict
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.utils.translation import ugettext_lazy as _
from uuid import uuid4

from Q.questionnaire import APP_LABEL, q_logger
from Q.questionnaire.q_fields import QPropertyTypes, QAtomicTypes, QUnsavedRelatedManager, allow_unsaved_fk, QJSONField
from Q.questionnaire.q_utils import EnumeratedType, EnumeratedTypeList, pretty_string, find_in_sequence, serialize_model_to_dict
from Q.questionnaire.q_utils import validate_no_spaces, validate_no_bad_chars, validate_no_reserved_words, validate_no_profanities, BAD_CHARS_LIST
from Q.questionnaire.q_constants import *

#############
# constants #
#############


class CustomizationType(EnumeratedType):

    def __str__(self):
        return "{0}".format(self.get_name())

CustomizationTypes = EnumeratedTypeList([
    CustomizationType("MODEL", "Model Customization"),
    CustomizationType("CATEGORY", "Category Customization"),
    CustomizationType("PROPERTY", "Property Customization"),
])


def get_default_values_schema():
    classes_schema = QCONFIG_SCHEMA["properties"]["classes"]["properties"]["defined"]["items"]
    properties_schema = classes_schema["properties"]["properties"]["properties"]["defined"]["items"]
    properties_values_schema = properties_schema["properties"]["values"]
    return properties_values_schema

######################
# get customizations #
######################


def get_new_customizations(project=None, ontology=None, model_proxy=None, **kwargs):

    key = kwargs.pop("key")
    customizations = kwargs.pop("customizations", {})

    # TODO: CHANGE THIS TO USE GUIDS INSTEAD OF NAMES FOR KEYS
    # TODO: TRY TO REWRITE THIS TO USE "prefix" AGAIN (INSTEAD OF EXPLICIT "key")

    model_proxy_key = key
    if model_proxy_key not in customizations:
        model_customization = QModelCustomization(
            project=project,
            proxy=model_proxy,
        )
        model_customization.reset()
        customizations[model_proxy_key] = model_customization
    else:
        model_customization = customizations[model_proxy_key]

    category_customizations = []
    # TODO: IS THERE A MORE EFFICIENT WAY TO DO THIS?
    # gets _all_ of the categories that are relevant to this model...
    used_category_proxies = [p.category_proxy for p in model_proxy.property_proxies.all()]
    category_proxies = set(model_proxy.category_proxies.all())
    category_proxies.update(used_category_proxies)
    for category_proxy in category_proxies:
    # for category_proxy in model_proxy.category_proxies.all():
    # for catgegory_proxy in ontology.category_proxies.filter(is_meta=False):
        category_proxy_key = "{0}.{1}".format(model_proxy_key, category_proxy.key)
        with allow_unsaved_fk(QCategoryCustomization, ["model_customization"]):
            if category_proxy_key not in customizations:
                category_customization = QCategoryCustomization(
                    project=project,
                    proxy=category_proxy,
                    model_customization=model_customization,
                )
                category_customization.reset()
                customizations[category_proxy_key] = category_customization
            else:
                category_customization = customizations[category_proxy_key]
        category_customizations.append(category_customization)
    model_customization.category_customizations(manager="allow_unsaved_category_customizations_manager").add_potentially_unsaved(*category_customizations)

    property_customizations = []
    for property_proxy in model_proxy.property_proxies.all():
    # for property_proxy in model_proxy.property_proxies.filter(is_meta=False):
    #     property_proxy_key = "{0}.{1}".format(model_proxy_key, property_proxy.name)
        property_proxy_key = "{0}.{1}".format(model_proxy_key, property_proxy.key)
        with allow_unsaved_fk(QPropertyCustomization, ["model_customization", "category_customization"]):
            # close this context manager before using the custom related manager
            # (too much hackery at once!)
            if property_proxy_key not in customizations:
                category_customization = find_in_sequence(
                    lambda c: c.proxy.has_property(property_proxy),
                    category_customizations
                )
                property_customization = QPropertyCustomization(
                    project=project,
                    proxy=property_proxy,
                    model_customization=model_customization,
                    category_customization=category_customization,
                )
                property_customization.reset()
                category_customization.property_customizations(manager="allow_unsaved_category_customizations_manager").add_potentially_unsaved(property_customization)
                customizations[property_proxy_key] = property_customization
            else:
                property_customization = customizations[property_proxy_key]
        property_customizations.append(property_customization)

        ############################
        # here begins the icky bit #
        ############################

        # if property_customization.use_subforms:
        # the trouble w/ using "use_subforms", above, is that it excludes hierarchical properties (which could potentially point to CIM documents)
        # so instead I always fill in relationship_target_models, and rely on the template to exclude appropriate content

        if property_customization.use_subforms or property_customization.relationship_is_hierarchical:
            subform_key = "{0}.{1}".format(model_proxy.key, property_proxy.key)
            target_model_customizations = []
            for target_model_proxy in property_proxy.relationship_target_models.all():
            # for target_model_proxy in property_proxy.relationship_target_models.filter(is_meta=False):
                # notice how I add the "cim_id" attribute (just in-case this is a specialization w/ different objects of the same class)
                # target_model_proxy_key = "{0}.{1}.{2}".format(subform_key, target_model_proxy.name, target_model_proxy.cim_id)
                target_model_proxy_key = "{0}.{1}.{2}".format(subform_key, target_model_proxy.key, target_model_proxy.cim_id)
                if target_model_proxy_key not in customizations:
                    target_model_customization = get_new_customizations(
                        project=project,
                        ontology=ontology,
                        model_proxy=target_model_proxy,
                        key=target_model_proxy_key,
                        customizations=customizations,
                    )
                else:
                    target_model_customization = customizations[target_model_proxy_key]

                target_model_customizations.append(target_model_customization)
            property_customization.relationship_target_model_customizations(manager="allow_unsaved_relationship_target_model_customizations_manager").add_potentially_unsaved(*target_model_customizations)

        ##########################
        # here ends the icky bit #
        ##########################

        model_customization.property_customizations(manager="allow_unsaved_property_customizations_manager").add_potentially_unsaved(*property_customizations)

    return customizations[model_proxy_key]


def get_existing_customizations(project=None, ontology=None, model_proxy=None, customization_name=None, customization_id=None):
    """
    can get an existing customization either via id or name
    :param project:
    :param ontology:
    :param model_proxy:
    :param customization_name:
    :param customization_id:
    :return:
    """

    # this fn will throw a "QModelCustomization.DoesNotExist" error if the name is wrong;
    # it is up to the calling method to catch that and do something sensible

    if not customization_id:
        model_customization = QModelCustomization.objects.get(
            proxy=model_proxy,
            project=project,
            name__iexact=customization_name,
        )
    else:
        model_customization = QModelCustomization.objects.get(pk=customization_id)
        assert model_customization.proxy == model_proxy
        assert model_customization.project == project
        if customization_name:
            assert model_customization.name.lower() == customization_name.lower()

    return model_customization


def serialize_customizations(current_model_customization, **kwargs):
    """
    need a special fn to cope w/ this
    b/c getting DRF to work w/ potentially infinite recursion is impossible
    it is likely that these customizations will need to be serialized before they have been saved

    therefore the m2m fields will not yet exist in the db
    the workflow goes:
    * get_new_customizations where calls to create are wrapped in "allow_unsaved_fk" & custom "QUnsavedRelatedManager"
    * those customizations get cached in the current session
    * AJAX calls the RESTful API to access those cached customizations
    * which needs to be serialized via this fn and then passed as data to QModelCustomizationSerializer
    :param customizations
    :return: OrderedDict
    """

    assert current_model_customization.is_new  # the only reason to use this fn is w/ cached unsaved models

    previously_serialized_customizations = kwargs.pop("previously_serialized_customizations", {})
    prefix = kwargs.pop("prefix", None)

    # get model customization stuff...
    model_customization_key = current_model_customization.get_fully_qualified_key(prefix=prefix)
    if model_customization_key not in previously_serialized_customizations:
        model_customization_serialization = serialize_model_to_dict(
            current_model_customization,
            include={
                "key": current_model_customization.key,
                "is_document": current_model_customization.is_document,
                "is_meta": current_model_customization.is_meta,
                "proxy_title": str(current_model_customization.proxy),
                "proxy_id": current_model_customization.proxy.cim_id,
                "display_detail": False,
            },
            exclude=["guid", "created", "modified", "synchronization"]
        )
        previously_serialized_customizations[model_customization_key] = model_customization_serialization
    else:
        model_customization_serialization = previously_serialized_customizations[model_customization_key]

    # and the categories stuff...
    category_customization_serializations = []
    for category_customization in current_model_customization.category_customizations(manager="allow_unsaved_category_customizations_manager").all():
        category_customization_key = category_customization.get_fully_qualified_key(prefix=prefix)
        if category_customization_key not in previously_serialized_customizations:
            category_customization_serialization = serialize_model_to_dict(
                category_customization,
                include={
                    "key": category_customization.key,
                    "is_empty": category_customization.is_empty,
                    "is_meta": category_customization.is_meta,
                    "num_properties": category_customization.property_customizations(manager="allow_unsaved_category_customizations_manager").count(),
                    "proxy_title": str(category_customization.proxy),
                    "proxy_id": category_customization.proxy.cim_id,
                    "display_properties": True,
                    "display_detail": False,
                },
                exclude=["guid", "created", "modified"]
            )
            previously_serialized_customizations[category_customization_key] = category_customization_serialization
        else:
            category_customization_serialization = previously_serialized_customizations[category_customization_key]
        category_customization_serializations.append(category_customization_serialization)

    # and the properties stuff...
    property_customization_serializations = []
    for property_customization in current_model_customization.property_customizations(manager="allow_unsaved_property_customizations_manager").all():
        property_customization_key = property_customization.get_fully_qualified_key(prefix=prefix)
        if property_customization_key not in previously_serialized_customizations:
            category_customization = property_customization.category_customization
            property_customization_serialization = serialize_model_to_dict(
                property_customization,
                include={
                    "key": property_customization.key,
                    "category_key": category_customization.key,
                    "cardinality": property_customization.cardinality,
                    "proxy_title": str(property_customization.proxy),
                    "proxy_id": property_customization.proxy.cim_id,
                    "display_detail": False,
                    "use_subforms": property_customization.use_subforms,
                    "is_meta": property_customization.is_meta,
                },
                exclude=["guid", "created", "modified"]
            )
            ############################
            # here begins the icky bit #
            ############################

            subform_customizations_serializations = []
            # as w/ "get_new_customizations" above this if statement would have excluded hierarchical properties that happen to map to CIM documents
            # if property_customization.use_subforms:
            if property_customization.use_subforms or property_customization.relationship_is_hierarchical:
                subform_prefix = property_customization.get_fully_qualified_key()  # note I do _not_ pass the prefix kwarg
                for subform_model_customization in property_customization.relationship_target_model_customizations(manager="allow_unsaved_relationship_target_model_customizations_manager").all():
                    subform_model_customization_key = subform_model_customization.get_fully_qualified_key(prefix=subform_prefix)
                    # notice how I add the cim_id in-case this is a specialization...
                    if property_customization.has_specialized_values:
                        subform_model_customization_key = "{0}.{1}".format(subform_model_customization_key, subform_model_customization.proxy.cim_id)
                    if subform_model_customization_key not in previously_serialized_customizations:
                        subform_customizations_serialization = serialize_customizations(
                            subform_model_customization,
                            previously_serialized_customizations=previously_serialized_customizations,
                            prefix=subform_prefix,
                        )
                        previously_serialized_customizations[subform_model_customization_key] = subform_customizations_serialization
                    else:
                        subform_customizations_serialization = previously_serialized_customizations[subform_model_customization_key]
                    subform_customizations_serializations.append(subform_customizations_serialization)
            property_customization_serialization["relationship_target_model_customizations"] = subform_customizations_serializations

            ##########################
            # here ends the icky bit #
            ##########################

        else:
            property_customization_serialization = previously_serialized_customizations[property_customization_key]
        property_customization_serializations.append(property_customization_serialization)

    # and put it all together...
    serialization = OrderedDict(model_customization_serialization)
    serialization["categories"] = category_customization_serializations
    serialization["properties"] = property_customization_serializations

    return serialization


###################
# some helper fns #
###################


def recurse_through_customizations(fn, current_model_customization, customization_types, **kwargs):
    """
    recursively applies fn recursively to all customization types
    :param fn: fn to call
    :param current_model_customization: the model customization from which to begin checking
    :param customization_types: the types of customizations to check
    :return: either QModelCustomization or QCategoryCustomization or QPropertyCustomization or None
    """

    previously_recursed_customizations = kwargs.pop("previously_recursed_customizations", set())

    if CustomizationTypes.MODEL in customization_types:
        fn(current_model_customization)

    for category_customization in current_model_customization.category_customizations(manager="allow_unsaved_category_customizations_manager").all():
        if CustomizationTypes.CATEGORY in customization_types:
            fn(category_customization)

    for property_customization in current_model_customization.property_customizations(manager="allow_unsaved_property_customizations_manager").all():
        property_customization_key = property_customization.key
        if property_customization_key not in previously_recursed_customizations:
            if CustomizationTypes.PROPERTY in customization_types:
                fn(property_customization)

            # as w/ "get_new_customizations" above this if statement would have excluded hierarchical properties that happen to map to CIM documents
            # if property_customization.use_subforms:
            if property_customization.use_subforms or property_customization.relationship_is_hierarchical:
                target_model_customizations = property_customization.relationship_target_model_customizations(manager="allow_unsaved_relationship_target_model_customizations_manager").all()
                for target_model_customization in target_model_customizations:
                    previously_recursed_customizations.add(property_customization_key)  # only tracking property_customizations b/c those are the only recursive things
                    recurse_through_customizations(
                        fn,
                        target_model_customization,
                        customization_types,
                        previously_recursed_customizations=previously_recursed_customizations,
                    )


def get_customization_by_fn(fn, current_model_customization, customization_types, **kwargs):
    """
    just like the above fn, except it returns the first customization for which fn returns true
    :param fn: fn to call
    :param current_model_customization: the model customization from which to begin checking
    :param customization_types: the types of customizations to check
    :return: either QModelCustomization or QCategoryCustomization or QPropertyCustomization or None
    """
    previously_recursed_customizations = kwargs.pop("previously_recursed_customizations", set())

    if CustomizationTypes.MODEL in customization_types:
        if fn(current_model_customization):
            return current_model_customization

    if CustomizationTypes.CATEGORY in customization_types:
        category_customization = find_in_sequence(
            fn,
            current_model_customization.category_customizations(manager="allow_unsaved_category_customizations_manager").all()
        )
        if category_customization:
            return category_customization

    for property_customization in current_model_customization.property_customizations(manager="allow_unsaved_property_customizations_manager").all():
        property_customization_key = property_customization.key
        if property_customization_key not in previously_recursed_customizations:
            if CustomizationTypes.PROPERTY in customization_types and fn(property_customization):
                return property_customization
            # as w/ "get_new_customizations" above, this if statement would have excluded hierarchical properties that happen to map to CIM documents
            # if property_customization.use_subforms:
            if property_customization.use_subforms or property_customization.relationship_is_hierarchical:
                target_model_customizations = property_customization.relationship_target_model_customizations(manager="allow_unsaved_relationship_target_model_customizations_manager").all()
                previously_recursed_customizations.add(property_customization_key)  # only tracking property_customizations b/c those are the only recursive things
                for target_model_customization in target_model_customizations:
                    matching_customization = get_customization_by_fn(
                        fn,
                        target_model_customization,
                        customization_types,
                        previously_recursed_customizations=previously_recursed_customizations,
                    )
                    if matching_customization:  # break out of the for loop as soon as I found a match
                        return matching_customization


def get_model_customization_by_key(key, current_model_customization, **kwargs):
    return get_customization_by_fn(
        lambda c: c.key == key,
        current_model_customization,
        [CustomizationTypes.MODEL],
    )


def get_category_customization_by_key(key, current_model_customization, **kwargs):
    return get_customization_by_fn(
        lambda c: c.key == key,
        current_model_customization,
        [CustomizationTypes.CATEGORY],
    )


def get_property_customization_by_key(key, current_model_customization, **kwargs):
    return get_customization_by_fn(
        lambda c: c.key == key,
        current_model_customization,
        [CustomizationTypes.PROPERTY],
    )


def set_name(model_customization, new_name):
    recurse_through_customizations(
        lambda c: c.set_name(new_name),
        model_customization,
        [CustomizationTypes.MODEL, CustomizationTypes.CATEGORY, CustomizationTypes.PROPERTY],
    )


def set_owner(model_customization, new_owner):
    recurse_through_customizations(
        lambda c: c.set_owner(new_owner),
        model_customization,
        [CustomizationTypes.MODEL],
    )


def set_shared_owner(model_customization, new_owner):
    recurse_through_customizations(
        lambda c: c.set_shared_owner(new_owner),
        model_customization,
        [CustomizationTypes.MODEL],
    )

#####################
# the actual models #
#####################


class QCustomization(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = True

    guid = models.UUIDField(default=uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    # all customizations share a name
    # (this makes finding related customizations simple: ".filter(project=parent.project, name=parent.name)" )
    name = models.CharField(
        max_length=LIL_STRING,
        blank=False,
        verbose_name="Customization Name",
        validators=[validate_no_bad_chars, validate_no_spaces, validate_no_reserved_words, validate_no_profanities],
        help_text="A unique name for this customization.  Only alphanumeric characters are allowed."
    )

    def __eq__(self, other):
        if isinstance(other, QCustomization):
            return self.guid == other.guid
        return NotImplemented

    def __ne__(self, other):
        equality_result = self.__eq__(other)
        if equality_result is NotImplemented:
            return equality_result
        return not equality_result

    @property
    def key(self):
        # convert self.guid to str b/c UUID does not play nicely w/ JSON
        return str(self.guid)

    @property
    def is_meta(self):
        return self.proxy.is_meta is True

    @property
    def is_new(self):
        return self.pk is None

    @property
    def is_existing(self):
        return self.pk is not None

    @classmethod
    def get_field(cls, field_name):
        """
        convenience fn for getting the Django Field instance from a model class
        note that this is a classmethod; when called from an instance it will just convert that instance to its class
        """
        try:
            field = cls._meta.get_field_by_name(field_name)
            return field[0]
        except FieldDoesNotExist:
            return None

    def get_unique_together(self):
        """
        'unique_together' validation is only enforced if all the unique_together fields appear in the ModelForm
        this fn returns the fields to check for manual validation
        """
        unique_together = self._meta.unique_together
        return list(unique_together)

    def reset(self, **kwargs):
        msg = "{0} must define a custom 'reset' method.".format(self.__class__.__name__)
        raise NotImplementedError(msg)


class QModelCustomizationQuerySet(models.QuerySet):
    """
    As of Django 1.7 I can use custom querysets as managers
    to ensure that these custom methods are chainable
    whoo-hoo
    """

    def documents(self):
        return self.filter(proxy__is_document=True)

    def owned_documents(self, user):
        return self.documents().filter(owner=user)

    def shared_documents(self, user):
        return self.documents().filter(shared_owners__in=[user.pk])


class QModelCustomization(QCustomization):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        ordering = ("order", )
        verbose_name = "_Questionnaire Customization: Model"
        verbose_name_plural = "_Questionnaire Customizations: Models"

    class _QModelCustomizationUnsavedRelatedManager(QUnsavedRelatedManager):
        field_name = "relationship_source_property_customization"

    objects = QModelCustomizationQuerySet.as_manager()
    allow_unsaved_relationship_target_model_customizations_manager = _QModelCustomizationUnsavedRelatedManager()

    owner = models.ForeignKey(User, blank=False, null=True, related_name="owned_customizations", on_delete=models.SET_NULL)
    shared_owners = models.ManyToManyField(User, blank=True, related_name="shared_customizations")

    project = models.ForeignKey("QProject", blank=False, related_name="model_customizations")
    proxy = models.ForeignKey("QModelProxy", blank=False, related_name="model_customizations")

    synchronization = models.ManyToManyField("QSynchronization", blank=True)
    order = models.PositiveIntegerField(blank=False)

    documentation = models.TextField(
        blank=True,
        null=True,
        help_text="An explanation of how this customization is intended to be used. This information is for informational purposes only.",
        verbose_name="Customization Description",
    )

    is_default = models.BooleanField(
        default=False,
        help_text="Every CIM Document Type must have one default customization. If this is the first customization you are creating, please ensure this checkbox is selected.",
        verbose_name="Is Default Customization?"
    )

    model_title = models.CharField(
        max_length=BIG_STRING,
        verbose_name="Name that should appear on the Document Form",
        blank=False, null=True
    )
    model_description = models.TextField(
        blank=True,
        null=True,
        help_text="This text will appear as documentation in the editing form.  Inline HTML formatting is permitted.  The initial documentation comes from the ontology.",
        verbose_name="A description of the document",
    )
    model_hierarchy_title = models.CharField(
        max_length=SMALL_STRING,
        help_text="This text will appear as a label for the tree view widget used to navigate the hierarchy of components",
        verbose_name="Title to use for the component hierarchy tree",
        blank=True, null=True,
    )
    model_show_empty_categories = models.BooleanField(
        default=False,
        verbose_name="Display empty categories?",
        help_text="Include categories in the editing form for which there are no (visible) properties associated with.",
    )

    # this fk is just here to provide the other side of the relationship to property_customization
    # I only ever access "property_customization.relationship_target_model_customizations"
    relationship_source_property_customization = models.ForeignKey("QPropertyCustomization", blank=True, null=True, related_name="relationship_target_model_customizations")

    def __str__(self):
        return pretty_string(self.name)

    def get_fully_qualified_key(self, prefix=None):
        fully_qualified_key = "{0}.{1}".format(
            self.proxy.fully_qualified_key,
            self.key,
        )
        if prefix:
            return "{0}.{1}".format(prefix, fully_qualified_key)
        return fully_qualified_key

    @property
    def is_synchronized(self):
        return self.synchronization.count() == 0  # checks if qs is empty

    @property
    def is_unsynchronized(self):
        return not self.is_synchronized

    @property
    def is_document(self):
        return self.proxy.is_document is True

    def set_name(self, new_name):
        # used w/ "recurse_through_customization" in global fn "set_name" above
        self.name = new_name

    def set_owner(self, new_owner):
        # used w/ "recurse_through_customization" in global fn "set_owner" above
        self.owner = new_owner

    def set_shared_owner(self, new_shared_owner):
        # used w/ "recurse_through_customization" in global fn "set_shared_owner" above
        self.shared_owners.add(new_shared_owner)

    def clean(self, *args, **kwargs):

        other_customizers = QModelCustomization.objects.filter(
            proxy=self.proxy,
            project=self.project,
        ).exclude(pk=self.pk)

        # there can be only 1 "default" customization for each project/proxy/ontology combination
        if self.is_default:
            if other_customizers.filter(is_default=True).count() != 0:
                raise ValidationError({
                    "is_default": _("A default customization already exists.  There can be only one default customization per project.")
                })

        if self.proxy.is_document:

            if other_customizers.filter(proxy__is_document=True, name=self.name).count() != 0:
                raise ValidationError({
                    "name": _("A customization for this proxy and project with this name already exists."),
                    "proxy": _("A customization for this proxy and project with this name already exists."),
                    "project": _("A customization for this proxy and project with this name already exists."),
                })

        super(QModelCustomization, self).clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        # force all (custom) "clean" methods to run
        self.full_clean()
        super(QModelCustomization, self).save(*args, **kwargs)

    def reset(self, **kwargs):
        force_save = kwargs.pop("force_save", False)
        proxy = self.proxy

        self.order = proxy.order

        self.model_title = pretty_string(proxy.name)
        self.model_description = proxy.documentation
        self.model_show_empty_categories = False

        if self.proxy.has_hierarchical_properties:
            self.model_hierarchy_title = "Component Hierarchy"

        if force_save:
            self.save()

    ##################################################
    # some fns which are called from signal handlers #
    ##################################################

    def updated_ontology(self):
        raise NotImplementedError

##############
# categories #
##############


class QCategoryCustomization(QCustomization):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "_Questionnaire Customization: Category"
        verbose_name_plural = "_Questionnaire Customizations: Categories"
        ordering = ("order",)

    class _QCategoryCustomizationUnsavedRelatedManager(QUnsavedRelatedManager):
        field_name = "model_customization"

    # custom managers...
    objects = models.Manager()
    allow_unsaved_category_customizations_manager = _QCategoryCustomizationUnsavedRelatedManager()

    project = models.ForeignKey("QProject", blank=False, related_name="category_customizations")
    proxy = models.ForeignKey("QCategoryProxy", blank=False)
    model_customization = models.ForeignKey("QModelCustomization", blank=False, related_name="category_customizations")

    category_title = models.CharField(max_length=TINY_STRING, blank=False, validators=[validate_no_profanities], verbose_name="Title")
    category_description = models.TextField(blank=True, null=True, verbose_name="Description")
    is_hidden = models.BooleanField(default=False, verbose_name="Should this category <u>not</u> be displayed?")
    is_hidden.help_text = _(
        "Note that hiding a category will not hide all of its member properties; "
        "It will simply not render them in a parent tab."
    )
    order = models.PositiveIntegerField(blank=True, null=True, verbose_name="Order")
    order.help_text = _(
        "Do not modify this value directly <em>here</em>.  "
        "Instead, drag and drop individual category widgets on the main form."
    )

    def __str__(self):
        return pretty_string(self.category_title)

    @property
    def is_empty(self):
        n_displayed_properties = self.property_customizations.filter(is_hidden=False).count()
        return n_displayed_properties == 0

    def get_fully_qualified_key(self, prefix=None):
        fully_qualified_key = "{0}.{1}".format(
            self.proxy.fully_qualified_key,
            self.key,
        )
        if prefix:
            return "{0}.{1}".format(prefix, fully_qualified_key)
        return fully_qualified_key

    def has_property(self, property_customization):
        return property_customization in self.property_customizations.all()

    def set_name(self, new_name):
        # used w/ "recurse_through_customization" in global fn "set_name" above
        self.name = new_name

    def reset(self, **kwargs):
        force_save = kwargs.pop("force_save", None)
        proxy = self.proxy

        self.category_title = proxy.name
        self.category_description = proxy.documentation
        self.is_hidden = proxy.is_uncategorized
        self.order = proxy.order

        if force_save:
            self.save()

###########################
# property customizations #
###########################


class QPropertyCustomization(QCustomization):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "_Questionnaire Customization: Property"
        verbose_name_plural = "_Questionnaire Customizations: Properties"
        ordering = ("order",)

    class _QPropertyCustomizationUnsavedRelatedManager(QUnsavedRelatedManager):
        field_name = "model_customization"

    class _QCategoryCustomizationUnsavedRelatedManager(QUnsavedRelatedManager):
        field_name = "category_customization"

    # custom managers...
    objects = models.Manager()
    allow_unsaved_property_customizations_manager = _QPropertyCustomizationUnsavedRelatedManager()
    allow_unsaved_category_customizations_manager = _QCategoryCustomizationUnsavedRelatedManager()

    project = models.ForeignKey("QProject", blank=False, related_name="property_customizations")
    proxy = models.ForeignKey("QPropertyProxy", blank=False, null=False)

    model_customization = models.ForeignKey("QModelCustomization", blank=False, related_name="property_customizations")
    category_customization = models.ForeignKey("QCategoryCustomization", blank=True, null=True, related_name="property_customizations")

    # all property types...

    property_title = models.CharField(max_length=LIL_STRING, blank=False, validators=[validate_no_profanities, ])
    is_required = models.BooleanField(default=True, blank=True, verbose_name="Is this property required?")
    is_required.help_text = _(
        "All required properties must be completed prior to publication.  "
        "A property that is defined as required <em>in the CIM or a CV</em> cannot be made optional."
    )
    is_hidden = models.BooleanField(default=True, blank=True, verbose_name="Should this property <u>not</u> be displayed?")
    is_hidden.help_text = _(
        "A property that is defined as required in an ontology should not be hidden."
    )
    is_editable = models.BooleanField(default=True, verbose_name="Can this property be edited?")
    is_editable.help_text = _(
        "If this field is disabled, this is because a default value was set by the ontology itself"
        "and should not therefore be overridden by the ES-DOC Questionnaire."
    )
    is_nillable = models.BooleanField(default=True, verbose_name="Should <i>nillable</i> options be allowed?")
    is_nillable.help_text = \
        "A nillable property can be intentionally left blank for several reasons: {0}.".format(
            ", ".join([nr[0] for nr in NIL_REASONS])
        )
    property_description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_(
            "What is the help text to associate with this property?"
            "<p class='documentation'>Any initial help text comes from the CIM.</p>"
            "<p class='documentation'>Note that basic HTML tags are supported.</p>"
        )
    )
    inline_help = models.BooleanField(default=False, blank=True, verbose_name="Should the help text be displayed inline?")
    order = models.PositiveIntegerField(blank=True, null=True)
    field_type = models.CharField(max_length=BIG_STRING, blank=False, choices=[(ft.get_type(), ft.get_name()) for ft in QPropertyTypes])
    can_inherit = models.BooleanField(default=False, verbose_name="Can this property be inherited by children?")
    can_inherit.help_text = _(
        "Enabling inheritance will allow the corresponding properties of child components to 'inherit' the value of this property.  "
        "The editing form will allow users the ability to 'opt-out' of this inheritance."
    )

    default_values = QJSONField(
        blank=True, null=True, schema=get_default_values_schema,
        verbose_name=_(
            "What are the default values for this property?"
            "<p class='documentation'>Please enter a comma-separated list of strings.</p>"
        ),
        help_text=_(
            "If this field is disabled, this is because a default value was set by the ontology itself"
            "and should not therefore be overridden by the ES-DOC Questionnaire.  "
            "<em>In this case, the property should also not be editable.</em>"
        )
    )

    # ATOMIC property types...
    atomic_type = models.CharField(
        max_length=BIG_STRING,
        blank=False,
        verbose_name="How should this field be rendered?",
        choices=[(ft.get_type(), ft.get_name()) for ft in QAtomicTypes],
        default=QAtomicTypes.DEFAULT.get_type(),
        help_text=_(
            "By default, all fields are rendered as strings.  "
            "However, a field can be customized to accept longer snippets of text, dates, email addresses, etc."
        )
    )
    atomic_suggestions = models.TextField(
        blank=True,
        null=True,
        verbose_name="Are there any suggestions you would like to offer as auto-completion options?",
        help_text="Please enter a '|' separated list of words or phrases."
    )

    # ENUMERATION fields...

    enumeration_is_open = models.BooleanField(default=False, verbose_name='Can a user can specify a custom "OTHER" value?')

    # RELATIONSHIP fields...
    # using the reverse of the fk defined on model_customization instead of this field
    # (so that I can use a custom manager to cope w/ unsaved instances)
    # relationship_target_model_customizations = models.ManyToManyField("QModelCustomization", blank=True, related_name="+")
    relationship_show_subforms = models.BooleanField(
        default=False,
        verbose_name=_(
            "Should this property be rendered in its own subform?"
            "<p class='documentation'>Note that a relationship to another CIM Document <u>cannot</u> use subforms, "
            "while a relationship to anything else <u>must</u> use subforms.</p>"
        ),
        help_text=_(
            "Checking this will cause the property to be rendered as a nested subform within the parent form;  "
            "All properties of the target model will be available to view and edit in that subform.  "
            "Unchecking it will cause the attribute to be rendered as a <em>reference</em> widget.  "
            "<br/>(Note that a &quot;hierarchical&quot; model can still be customized using this technique even though "
            "the corresponding target models will display as top-level forms rather than subforms.)"
        )
    )
    relationship_is_hierarchical = models.BooleanField(
        default=False,
        verbose_name=_(
            "Should this property be rendered as part of a hierarchy?"
        ),
        help_text=_(
            "Checking this will cause the property to be rendered in a treeview; "
            "All properties of the target model will be avaialble as a pane next to that treeview.  "
            "This value is set by the ontology itself.  Unless you know what you're doing, <em>don't mess with it</em>."
        )
    )

    def __str__(self):
        return pretty_string(self.proxy.name)

    def get_fully_qualified_key(self, prefix=None):
        fully_qualified_key = "{0}.{1}".format(
            self.proxy.fully_qualified_key,
            self.key
        )
        if prefix:
            return "{0}.{1}".format(prefix, fully_qualified_key)
        return fully_qualified_key

    def set_name(self, new_name):
        # used w/ "recurse_through_customization" in global fn "set_name" above
        self.name = new_name

    @property
    def cardinality_min(self):
        cardinality_min = self.proxy.cardinality_min
        return int(cardinality_min)

    @property
    def cardinality_max(self):
        cardinality_max = self.proxy.cardinality_max
        if cardinality_max != CARDINALITY_INFINITE:
            return int(cardinality_max)
        return cardinality_max

    @property
    def cardinality(self):
        return "{0}.{1}".format(
            self.cardinality_min,
            self.cardinality_max,
        )

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
            target_models_are_documents = [tm.is_document for tm in self.proxy.relationship_target_models.all()]
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
            target_models_are_documents = [tm.is_document for tm in self.proxy.relationship_target_models.all()]
            assert len(set(target_models_are_documents)) == 1
            return not any(target_models_are_documents)
        return False

    @property
    def has_specialized_values(self):
        return self.proxy.values is not None

    def reset(self, **kwargs):
        force_save = kwargs.pop("force_save", False)

        proxy = self.proxy

        # all fields...

        self.property_title = pretty_string(proxy.name)
        self.property_description = proxy.documentation
        self.order = proxy.order
        self.is_required = proxy.is_required
        self.is_hidden = False  # not proxy.is_required
        self.is_nillable = not proxy.is_required
        self.inline_help = False
        self.default_values = proxy.values
        self.is_editable = not self.has_specialized_values  # if the proxy provided default values, then do not allow the customizer to override them
        self.can_inherit = False

        assert self.category_customization is not None  # even "uncategorized" properties should use the "UncategorizedCategory"

        self.field_type = proxy.field_type

        # ATOMIC fields...

        if self.field_type == QPropertyTypes.ATOMIC:
            self.atomic_type = proxy.atomic_type
            self.atomic_suggestions = ""

        # ENUMERATION fields...

        elif self.field_type == QPropertyTypes.ENUMERATION:
            self.enumeration_is_open = proxy.enumeration_is_open
            # TODO: DO I NEED TO DEAL W/ "enumeration_choices" OR "enumeration_default" ?

        # RELATIONSHIP fields...

        else:  # self.field_type == QPropertyTypes.RELATIONSHIP
            self.relationship_show_subforms = self.use_subforms
            self.relationship_is_hierarchical = proxy.is_hierarchical

        if force_save:
            self.save()
