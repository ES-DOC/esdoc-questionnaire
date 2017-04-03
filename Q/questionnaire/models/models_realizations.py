####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.template.loader import render_to_string
from uuid import uuid4
import copy

from Q.questionnaire import APP_LABEL, q_logger
from Q.questionnaire.q_fields import QVersionField, QEnumerationField, QJSONField, QPropertyTypes, QNillableTypes, QUnsavedRelatedManager, allow_unsaved_fk, ENUMERATION_OTHER_CHOICE, ENUMERATION_OTHER_DOCUMENTATION, ENUMERATION_OTHER_PREFIX
from Q.questionnaire.models.models_customizations import QModelCustomization
from Q.questionnaire.models.models_publications import QPublication, QPublicationFormats
from Q.questionnaire.models.models_references import QReference
from Q.questionnaire.serializers.serializers_references import create_empty_reference_list_serialization
from Q.questionnaire.q_utils import QError, EnumeratedType, EnumeratedTypeList, Version, find_in_sequence, pretty_string, serialize_model_to_dict
from Q.questionnaire.q_constants import *

#############
# constants #
#############


class RealizationType(EnumeratedType):

    def __str__(self):
        return "{0}".format(self.get_name())

RealizationTypes = EnumeratedTypeList([
    RealizationType("MODEL", "Model Realization"),
    RealizationType("CATEGORY", "Category Realization"),
    RealizationType("PROPERTY", "Property Realization"),
])

####################
# get realizations #
####################


def get_new_realizations(project=None, ontology=None, model_proxy=None, **kwargs):
    # unlike w/ customizations, I do not create the entire possible set all at once
    # instead I just deal w/ the minimum number of properties (based on cardinality)
    # infinite recursion is therefore avoided; not by re-using previously created models
    # as with customizations, but by only creating a finite amount of models
    # hooray!

    parent_property = kwargs.pop("parent_property", None)
    if parent_property is not None:
        is_active = parent_property.is_required
    else:
        is_active = True
    model_realization = QModelRealization(
        project=project,
        proxy=model_proxy,
        version="0.0.0",
        is_active=is_active
    )
    model_realization.reset()

    category_realizations = []
    # TODO: IS THERE A MORE EFFICIENT WAY TO DO THIS?
    # gets _all_ of the categories that are relevant to this model...
    used_category_proxies = [p.category_proxy for p in model_proxy.property_proxies.all()]
    category_proxies = set(model_proxy.category_proxies.all())
    category_proxies.update(used_category_proxies)
    for category_proxy in category_proxies:
    # for category_proxy in model_proxy.category_proxies.all():
        with allow_unsaved_fk(QCategoryRealization, ["model"]):
            category_realization = QCategoryRealization(
                proxy=category_proxy,
                model=model_realization,
            )
            category_realization.reset()
        category_realizations.append(category_realization)
    model_realization.categories(manager="allow_unsaved_categories_manager").add_potentially_unsaved(*category_realizations)

    property_realizations = []
    for property_proxy in model_proxy.property_proxies.all():
        property_category_realization = find_in_sequence(
            lambda c: c.proxy == property_proxy.category_proxy,
            category_realizations
        )
        with allow_unsaved_fk(QPropertyRealization, ["model", "category"]):
            property_realization = QPropertyRealization(
                proxy=property_proxy,
                field_type=property_proxy.field_type,    # TODO: I AM HAVING TO PASS "field_type" SO THAT IT'S SET IN "__init__" IN ORDER TO SETUP ANY ENUMERATIONS;
                model=model_realization,                 # TODO: AN ALTERNATIVE WOULD BE TO CALL "reset" FROM "__init__" WHENEVER "is_new" IS True.
                category=property_category_realization,
            )
            property_realization.reset()
            property_category_realization.properties(manager="allow_unsaved_category_properties_manager").add_potentially_unsaved(property_realization)
            # here begins the icky bit
            if property_realization.field_type == QPropertyTypes.RELATIONSHIP and property_realization.is_hierarchical:  # property_realization.is_required:
                target_relationship_values = []
                # TODO: IF I WERE TO PRE-CREATE ALL RELATIONSHIPS THEN HERE IS WHERE I WOULD DO IT
                # TODO: BUT THAT WOULD BE MIND-BOGGLINGLY COMPLEX...
                # TODO: ...B/C I WOULD NEED TO KNOW IN ADVANCE WHAT TYPES OF RELATIONSHIPS TO CREATE IN THE CASE OF MULTIPLE TYPES OF TARGETS;
                # TODO: AS IT IS, I GET AROUND THIS BY ONLY PRE-CREATING SPECIALIZATIONS WHICH ARE EXPLICIT IN THEIR TARGET PROXIES
                # TODO: BUT I STILL CANNOT HANDLE THIS FOR NON-SPECIALIZED PROXIES
                if property_realization.has_specialized_values:

                    # assert property_realization.cardinality_min == len(property_proxy.values)

                    for target_model_proxy_id in property_proxy.values:
                        target_model_proxy = property_proxy.relationship_target_models.get(cim_id=target_model_proxy_id)
                        kwargs.update({"parent_property": property_realization})
                        with allow_unsaved_fk(QModelRealization, ["relationship_property"]):  # this lets me access the parent property of a model
                            new_model_realization = get_new_realizations(
                                project=project,
                                ontology=target_model_proxy.ontology,
                                model_proxy=target_model_proxy,
                                **kwargs
                            )
                            new_model_realization.relationship_property = property_realization
                        target_relationship_values.append(new_model_realization)
                    property_realization.relationship_values(manager="allow_unsaved_relationship_values_manager").add_potentially_unsaved(*target_relationship_values)

                # here ends the icky bit
        property_realizations.append(property_realization)
    model_realization.properties(manager="allow_unsaved_properties_manager").add_potentially_unsaved(*property_realizations)

    return model_realization


def get_existing_realizations(project=None, ontology=None, model_proxy=None, model_id=None):
    """
    can get an existing realization
    :param project:
    :param ontology:
    :param model_proxy:
    :param model_id:
    :return:
    """

    # this fn will throw a "QModelRealization.DoesNotExist" error if the arguments are wrong;
    # it is up to the calling method to catch that and do something sensible

    model_realization = QModelRealization.objects.get(pk=model_id)

    if project and model_realization.project != project:
        raise QModelRealization.DoesNotExist
    if model_proxy and model_realization.proxy != model_proxy:
        raise QModelRealization.DoesNotExist

    return model_realization


def serialize_realizations(current_model_realization, **kwargs):
    """
    need a special fn to cope w/ this
    b/c it is likely that these realizations will need to be serialized before they have been saved
    therefore the m2m fields will not yet exist in the db
    the workflow goes:
    * get_new_realizations where calls to create are wrapped in "allow_unsaved_fk" & custom "QUnsavedRelatedManager"
    * those realizations get cached in the current session
    * AJAX calls the RESTful API to access those cached realizations
    * which needs to be serialized via this fn and then passed as data to QModelRealizationSerializer
    :param current_model_realization
    :return: OrderedDict
    """

    # get the model stuff...
    model_serialization = serialize_model_to_dict(
        current_model_realization,
        include={
            "key": current_model_realization.key,
            "is_meta": current_model_realization.is_meta,
            # "version": current_model_realization.version.fully_specified(),
            "title": current_model_realization.title,
            "is_selected": False,
            "display_detail": False,
        },
        exclude=["guid", "created", "modified", "synchronization"]
    )

    # and the categories stuff...
    category_serializations = []
    for category_realization in current_model_realization.categories(manager="allow_unsaved_categories_manager").all():
        category_serialization = serialize_model_to_dict(
            category_realization,
            include={
                "key": category_realization.key,
                "is_uncategorized": category_realization.is_uncategorized,
                "properties_keys": category_realization.get_properties_keys(),
                "display_detail": True,
            },
            exclude=["guid", "created", "modified"]
        )
        category_serializations.append(category_serialization)

    # and the properties stuff...
    property_serializations = []
    for property_realization in current_model_realization.properties(manager="allow_unsaved_properties_manager").all():
        property_serialization = serialize_model_to_dict(
            property_realization,
            include={
                "relationship_references": create_empty_reference_list_serialization(),  # just a placeholder
                "key": property_realization.key,
                "is_meta": property_realization.is_meta,
                "is_hierarchical": property_realization.is_hierarchical,
                "cardinality_min": property_realization.cardinality_min,
                "cardinality_max": property_realization.cardinality_max,
                "is_multiple": property_realization.is_multiple,
                "is_infinite": property_realization.is_infinite,
                "possible_relationship_target_types": property_realization.get_potential_relationship_target_types(),
                "category_key": property_realization.category_key,
                "display_detail": True,
            },
            exclude=["guid", "created", "modified"]
        )
        # here begins the icky bit
        target_model_serializations = []
        if property_realization.field_type == QPropertyTypes.RELATIONSHIP:
            target_model_realizations = property_realization.relationship_values(manager="allow_unsaved_relationship_values_manager").all()
            for target_model_realization in target_model_realizations:
                target_model_serialization = serialize_realizations(target_model_realization)
                target_model_serializations.append(target_model_serialization)
        property_serialization["relationship_values"] = target_model_serializations
        # here ends the icky bit

        property_serializations.append(property_serialization)

    # and put it all together...
    serialization = OrderedDict(model_serialization)
    serialization["categories"] = category_serializations
    serialization["properties"] = property_serializations

    return serialization

###################
# some helper fns #
###################


def get_root_realization(current_realization):
    """
    kind of like recurse_through_realizations below,
    but works from the bottom-up
    :param self:
    :return: QModelRealization
    """
    if isinstance(current_realization, QPropertyRealization):
        return get_root_realization(current_realization.model)
    elif isinstance(current_realization, QCategoryRealization):
        return get_root_realization(current_realization.model)
    else:
        parent_property = current_realization.relationship_property
        if parent_property:
            return get_root_realization(parent_property)
        else:
            # this realization has no parent_property, it must therefore be the root
            return current_realization


def recurse_through_realizations(fn, current_model_realization, realization_types, **kwargs):
    """
    recursively applies fn recursively to all realization_types
    :param fn: fn to call
    :param current_model_realization: the model realization from which to begin checking
    :param realization_types: the types of customizations to check
    :return: either QModelRealization or QCategoryRealization or QPropertyRealization or None
    """

    previously_recursed_realizations = kwargs.pop("previously_recursed_realizations", set())

    if RealizationTypes.MODEL in realization_types:
        fn(current_model_realization)

    for category_realization in current_model_realization.categories(manager="allow_unsaved_categories_manager").all():
        if RealizationTypes.CATEGORY in realization_types:
            fn(category_realization)

    for property_realization in current_model_realization.properties(manager="allow_unsaved_properties_manager").all():
        property_realization_key = property_realization.key

        if property_realization_key not in previously_recursed_realizations:

            if RealizationTypes.PROPERTY in realization_types:
                fn(property)

            if property_realization.field_type == QPropertyTypes.RELATIONSHIP:
                previously_recursed_realizations.add(property_realization_key)
                target_model_realizations = property_realization.relationship_values(manager="allow_unsaved_relationship_values_manager").all()
                for target_model_realization in target_model_realizations:
                    recurse_through_realizations(
                        fn,
                        target_model_realization,
                        realization_types,
                        previously_recursed_realizations=previously_recursed_realizations,
                    )


def get_realization_by_fn(fn, current_model_realization, realization_types, **kwargs):
    """
    just like the above fn, except it returns the first realization for which fn returns true
    :param fn: fn to call
    :param current_model_realization: the model customization from which to begin checking
    :param realization_types: the types of customizations to check
    :return: either QModelRealization or QCategoryRealization or QPropertyRealization or None
    """

    previously_recursed_realizations = kwargs.pop("previously_recursed_realizations", set())

    if RealizationTypes.MODEL in realization_types:
        if fn(current_model_realization):
            return current_model_realization

    if RealizationTypes.CATEGORY in realization_types:
        category_realization = find_in_sequence(
            fn,
            current_model_realization.categories(manager="allow_unsaved_categories_manager").all()
        )
        if category_realization:
            return category_realization

    for property_realization in current_model_realization.properties(manager="allow_unsaved_properties_manager").all():
        property_realization_key = property_realization.key
        if property_realization_key not in previously_recursed_realizations:

            if RealizationTypes.PROPERTY in realization_types and fn(property_realization):
                return property_realization

            if property_realization.field_type == QPropertyTypes.RELATIONSHIP:
                previously_recursed_realizations.add(property_realization_key)
                target_model_realizations = property_realization.relationship_values(manager="allow_unsaved_relationship_values_manager").all()
                for target_model_realization in target_model_realizations:
                    matching_realization = get_realization_by_fn(
                        fn,
                        target_model_realization,
                        realization_types,
                        previously_recursed_realizations=previously_recursed_realizations,
                    )
                    if matching_realization:  # break out of the loop as soon as I find a match
                        return matching_realization


def get_model_realization_by_key(key, current_model_realization, **kwargs):
    return get_realization_by_fn(
        lambda r: r.key == key,
        current_model_realization,
        [RealizationTypes.MODEL],
    )


def get_property_realization_by_key(key, current_model_realization, **kwargs):
    return get_realization_by_fn(
        lambda r: r.key == key,
        current_model_realization,
        [RealizationTypes.PROPERTY],
    )


def set_owner(model_realization, new_owner):
    recurse_through_realizations(
        lambda r: r.set_owner(new_owner),
        model_realization,
        [RealizationTypes.MODEL],
    )


def set_shared_owner(model_realization, new_owner):
    recurse_through_realizations(
        lambda r: r.set_shared_owner(new_owner),
        model_realization,
        [RealizationTypes.MODEL],
    )


def set_version(model_realization, new_version):
    recurse_through_realizations(
        lambda r: r.set_version(new_version, force_save=True),
        model_realization,
        [RealizationTypes.MODEL],
    )


# this fn is not needed;
# QModelRealization.update_completion automatically computes "is_complete" of categories & properties and recurses through relationships
# def update_completion(model_realization):
#     recurse_through_realizations(
#         lambda r: r.update_completion(force_save=True),
#         model_realization,
#         [RealizationTypes.MODEL, RealizationTypes.CATEGORY, RealizationTypes.PROPERTY]
#     )

#####################
# the actual models #
#####################


class QRealization(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = True

    guid = models.UUIDField(default=uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    is_complete = models.BooleanField(blank=False, null=False, default=False)

    order = models.PositiveIntegerField(blank=True, null=True)

    name = models.CharField(max_length=SMALL_STRING, blank=False)

    def __eq__(self, other):
        if isinstance(other, QRealization):
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
    def is_new(self):
        return self.pk is None

    @property
    def is_existing(self):
        return self.pk is not None

    @property
    def is_meta(self):
        return self.proxy.is_meta is True

    @property
    def title(self):
        proxy_id = self.proxy.cim_id
        proxy_title = proxy_id.rsplit('.')[-1]
        return pretty_string(proxy_title)

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

    def get_default_customization(self):
        root_realization = get_root_realization(self)
        try:
            default_root_customization = QModelCustomization.objects.get(
                project=self.project,
                proxy=root_realization.proxy,
                is_default=True
            )
            if self.proxy == default_root_customization.proxy:
                return default_root_customization
            else:
                default_customization = QModelCustomization.objects.filter(
                    project=self.project,
                    proxy=self.proxy,
                    name=default_root_customization.name
                ).first()  # filter might return more than one b/c of all the recursion involved in setting up customizations
                return default_customization
        except ObjectDoesNotExist:
            msg = "There is no default customization associated with {0}".format(self)
            raise QError(msg)

    def reset(self):
        msg = "{0} must define a custom 'reset' method.".format(self.__class__.__name__)
        raise NotImplementedError(msg)


class QModelRealizationQuerySet(models.QuerySet):
    """
    As of Django 1.7 I can use custom querysets as managers
    to ensure that these custom methods are chainable
    whoo-hoo
    """

    def root_documents(self):
        return self.filter(proxy__is_document=True, is_root=True)

    def published_documents(self):
        return self.filter(proxy__is_document=True, is_root=True, is_published=True)

    def owned_documents(self, user):
        return self.root_documents().filter(owner=user)

    def shared_documents(self, user):
        return self.root_documents().filter(shared_owners__in=[user.pk])


class QModelRealization(QRealization):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "_Questionnaire Realization: Model"
        verbose_name_plural = "_Questionnaire Realizations: Models"
        ordering = ("order",)

    class _QRelationshipValuesUnsavedRelatedManager(QUnsavedRelatedManager):
        field_name = "relationship_property"

    # custom managers...
    objects = QModelRealizationQuerySet.as_manager()
    allow_unsaved_relationship_values_manager = _QRelationshipValuesUnsavedRelatedManager()

    owner = models.ForeignKey(User, blank=False, null=True, related_name="owned_models", on_delete=models.SET_NULL)
    shared_owners = models.ManyToManyField(User, blank=True, related_name="shared_models")

    project = models.ForeignKey("QProject", blank=False, related_name="models")
    proxy = models.ForeignKey("QModelProxy", blank=False, related_name="models")

    version = QVersionField(blank=True, null=True)  # I am using the full complexity of a "major.minor.patch" version, even though I don't expose "patch"

    is_root = models.BooleanField(blank=False, null=False, default=False)
    is_published = models.BooleanField(blank=False, null=False, default=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)

    synchronization = models.ManyToManyField("QSynchronization", blank=True)

    # this fk is just here to provide the other side of the relationship to QProperty
    # I only ever access "property.relationship_values"
    relationship_property = models.ForeignKey("QPropertyRealization", blank=True, null=True, related_name="relationship_values")

    def __str__(self):
        return "{0}: {1}".format(
            self.name,
            self.label
        )

    @property
    def label(self):
        proxy_label = self.proxy.label
        if proxy_label is not None:
            return proxy_label["text"].format(
                *[self.properties.get(name=field).value for field in proxy_label["fields"]]
            )

    @property
    def is_document(self):
        return self.proxy.is_document is True

    @property
    def is_synchronized(self):
        return self.synchronization.count() == 0  # checks if qs is empty

    @property
    def is_unsynchronized(self):
        return not self.is_synchronized()

    def publish(self, **kwargs):
        """
        :param force_save: save the model (after incrementing its version);
        the only reason not to do this is when re-publishing something at the same version b/c of a content error
        :return: QPublication
        """
        force_save = kwargs.pop("force_save", True)
        publication_format = kwargs.pop("format", QPublicationFormats.CIM2_XML)

        assert self.is_document
        assert self.is_complete

        if force_save:
            # reset the minor.patch version...
            self.version -= "0.{0}.{1}".format(self.version.minor(), self.version.patch())
            # and increment the major version...
            self.version += "1.0.0"

        (publication, create_publication) = QPublication.objects.get_or_create(
            name=self.guid,
            version=self.version,
            format=publication_format,
            model=self,
        )

        template_context = {
            "project": self.project,
            "ontology": self.proxy.ontology,
            "proxy": self.proxy,
            "model": self,
            "publication_format": publication_format,
        }
        publication_template_path = "{0}/publications/{1}/{2}".format(APP_LABEL, publication_format, "publication_model.xml")
        publication_content = render_to_string(publication_template_path, template_context)
        publication.content = publication_content
        publication.save()

        self.is_published = True
        if force_save:
            self.save()

        return publication

    def reset(self):
        # this resets values according to the proxy...
        # to reset values according to the customizer, you must explicitly call customize and/or go through the client
        proxy = self.proxy

        # TODO: self.is_root = ?!?
        # self.is_active = True
        self.is_complete = False
        self.order = proxy.order
        self.name = proxy.name

    def set_owner(self, new_owner, **kwargs):
        # used w/ "recurse_through_customization" in global fn "set_owner" above
        self.owner = new_owner
        if kwargs.pop("force_save", False):
            self.save()

    def set_shared_owner(self, new_shared_owner, **kwargs):
        # used w/ "recurse_through_customization" in global fn "set_shared_owner" above
        self.shared_owners.add(new_shared_owner)
        if kwargs.pop("force_save", False):
            self.save()

    def set_version(self, new_version, **kwargs):
        # used w/ "recurse_through_customization" in global fn "set_version" above
        self.version = new_version
        if kwargs.pop("force_save", False):
            self.save()

    def update_completion(self, **kwargs):
        property_realizations_completion = [
            property_realization.update_completion(**kwargs)
            for property_realization in self.properties(manager="allow_unsaved_properties_manager").all()
        ]

        for category_realization in self.categories(manager="allow_unsaved_categories_manager").all():
            category_realization.update_completion(**kwargs)

        self.is_complete = all(property_realizations_completion)
        if kwargs.get("force_save", False):
            self.save()
        return self.is_complete


class QCategoryRealization(QRealization):
    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "_Questionnaire Realization: Category"
        verbose_name_plural = "_Questionnaire Realizations: Categories"
        ordering = ("order",)

    class _QCategoryUnsavedRelatedManager(QUnsavedRelatedManager):
        field_name = "model"

    objects = models.Manager()
    allow_unsaved_categories_manager = _QCategoryUnsavedRelatedManager()

    proxy = models.ForeignKey("QCategoryProxy", blank=False, related_name="categories")
    model = models.ForeignKey("QModelRealization", blank=False, related_name="categories")

    category_value = models.CharField(max_length=HUGE_STRING, blank=False, null=False)

    def __str__(self):
        return "{0}: {1}".format(
            self.name,
            self.value
        )

    @property
    def value(self):
        return self.category_value

    @property
    def is_uncategorized(self):
        return self.proxy.is_uncategorized

    def get_properties_keys(self):
        properties = self.properties(manager="allow_unsaved_category_properties_manager").all()
        return [p.key for p in properties]

    def update_completion(self, **kwargs):
        properties_completion = self.properties.values("is_complete")  # TODO: DOES THIS WORK W/ UNSAVED PROPERTIES?
        self.is_complete = all(properties_completion)
        if kwargs.get("force_save", False):
            self.save()
        return self.is_complete

    def reset(self):
        # this resets values according to the proxy...
        # to reset values according to the customizer, you must explicitly call customize and/or go through the client
        proxy = self.proxy

        self.is_complete = False
        self.order = proxy.order
        self.name = proxy.name

        self.category_value = proxy.name


class QPropertyRealization(QRealization):
    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "_Questionnaire Realization: Property"
        verbose_name_plural = "_Questionnaire Realizations: Properties"
        ordering = ("order",)

    class _QPropertyUnsavedRelatedManager(QUnsavedRelatedManager):
        field_name = "model"

    class _QCategoryPropertyUnsavedRelatedManager(QUnsavedRelatedManager):
        field_name = "category"

    objects = models.Manager()
    allow_unsaved_properties_manager = _QPropertyUnsavedRelatedManager()
    allow_unsaved_category_properties_manager = _QCategoryPropertyUnsavedRelatedManager()

    proxy = models.ForeignKey("QPropertyProxy", blank=False, related_name="properties")
    model = models.ForeignKey("QModelRealization", blank=False, related_name="properties")
    category = models.ForeignKey("QCategoryRealization", blank=True, null=True, related_name="properties")

    is_nil = models.BooleanField(default=False)
    nil_reason = models.CharField(
        max_length=BIG_STRING,
        blank=False,
        default=QNillableTypes.first().get_type(),
        choices=[(nt.get_type(), nt.get_description()) for nt in QNillableTypes],
    )

    field_type = models.CharField(max_length=BIG_STRING, blank=False, choices=[(ft.get_type(), ft.get_name()) for ft in QPropertyTypes])

    atomic_value = models.TextField(blank=True, null=True)
    enumeration_value = QEnumerationField(blank=True, null=True)
    enumeration_other_value = models.CharField(blank=True, null=True, max_length=HUGE_STRING)

    # relationship_references = models.ManyToManyField(blank=True, null=True)
    relationship_references = models.ManyToManyField(QReference, blank=True, related_name="properties")

    def __init__(self, *args, **kwargs):
        super(QPropertyRealization, self).__init__(*args, **kwargs)
        if self.field_type == QPropertyTypes.ENUMERATION:
            # originally all of this was done in the "reset" fn below, but that only gets called for new objects
            # then I tried adding it to the "QPropertyForm.__init__" fn, but that only deals w/ form fields (not model fields)
            # so it has wound up here...
            proxy = self.proxy
            enumeration_choices = copy.copy(proxy.enumeration_choices)  # make a copy of the value so that "update" below doesn't modify the original
            if proxy.enumeration_is_open:
                enumeration_choices.append({
                    "value": ENUMERATION_OTHER_CHOICE,
                    "documentation": ENUMERATION_OTHER_DOCUMENTATION,
                    "order": len(enumeration_choices) + 1,
                })
            enumeration_value_field = self.get_field("enumeration_value")
            enumeration_value_field.complete_choices = enumeration_choices
            enumeration_value_field.is_multiple = proxy.is_multiple
            # TODO: THE ABOVE CHANGES SEEM TO BE LOST BY THE TIME WE SETUP THE CORRESPONDING FORM ?!?
            # TODO: SEE THE COMMENTS IN "QPropertyRealizationForm.__init__" AND "QEnumerationFormField" FOR MORE INFO

    def __str__(self):
        return "{0}: {1}".format(
            self.name,
            self.value
        )

    @property
    def value(self):
        field_type = self.field_type
        if field_type == QPropertyTypes.ATOMIC:
            return self.atomic_value
        elif field_type == QPropertyTypes.ENUMERATION:
            enumeration_value = self.enumeration_value
            if enumeration_value:
                # clever lil hack to return -1 if ENUMERATION_OTHER_CHOICE is not in enumeration_value w/out resorting to looping through the array twice...
                enumeration_other_index = next((i for i, enum in enumerate(enumeration_value) if enum == ENUMERATION_OTHER_CHOICE), -1)
                if enumeration_other_index >= 0:
                    enumeration_value[enumeration_other_index] = "{0}:{1}".format(
                        ENUMERATION_OTHER_PREFIX,
                        self.enumeration_other_value,
                    )
                return enumeration_value
            return []
        else:  # field_type == QPropertyTypes.RELATIONSHIP
            return self.relationship_values.all()

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
    def category_key(self):
        return self.category.key

    @property
    def has_specialized_values(self):
        return self.proxy.values is not None

    @property
    def is_infinite(self):
        return self.proxy.is_infinite

    @property
    def is_multiple(self):
        return self.proxy.is_multiple

    @property
    def is_single(self):
        return self.proxy.is_single

    @property
    def is_required(self):
        return self.proxy.is_required

    @property
    def is_optional(self):
        return self.proxy.is_optional

    @property
    def is_hierarchical(self):
        return self.proxy.is_hierarchical

    def get_potential_relationship_target_types(self):
        """
        returns an array w/ some useful info for working out which type of Realization I can use as a relationship target
        :return:
        """
        if self.field_type == QPropertyTypes.RELATIONSHIP:
            potential_relationship_target_types_qs = self.proxy.relationship_target_models.values("name", "pk")
            # ("values" returns a ValuesQuerySet, which doesn't serialize natively into JSON; so I convert it to a list)
            return [potential_relationship_target_type for potential_relationship_target_type in potential_relationship_target_types_qs]
        return []

    def update_completion(self, **kwargs):
        if self.is_required:
            if self.is_nil:
                # something that's required but explicitly set to "nil" is still considered complete
                property_completion = True
            else:
                field_type = self.field_type
                if field_type != QPropertyTypes.RELATIONSHIP:
                    # otherwise anything w/ a value is considered complete...
                    property_completion = bool(self.value)
                else:  # field_type == QPropertyTypes.RELATIONSHIP
                    # ...and relationships are dealt w/ recursively
                    relationship_values_completion = [
                        relationship_value.update_completion(**kwargs)
                        for relationship_value in self.relationship_values(manager="allow_unsaved_relationship_values_manager").all()
                    ]
                    property_completion = len(relationship_values_completion) >= self.cardinality_min and all(relationship_values_completion)
        else:
            # a non-required property is complete by default
            # TODO: WHAT ABOUT PROPERTIES THAT ARE _CUSTOMIZED_ TO BE REQUIRED ?!?
            property_completion = True

        self.is_complete = property_completion
        if kwargs.get("force_save", False):
            self.save()
        return self.is_complete

    def reset(self):
        # this resets values according to the proxy...
        # to reset values according to the customizer, you must explicitly call customize and/or go through the client
        proxy = self.proxy

        self.order = proxy.order
        self.name = proxy.name

        self.is_complete = not proxy.is_required  # anything not required is complete by default

        self.is_nil = False
        self.nil_reason = self.get_field("nil_reason").default

        self.field_type = proxy.field_type
        if self.field_type == QPropertyTypes.ATOMIC:
            pass
        elif self.field_type == QPropertyTypes.ENUMERATION:
            self.enumeration_value = []
            self.enumeration_other_value = None
        else:  # self.field_type == QPropertyTypes.RELATIONSHIP:
            if not self.is_hierarchical:
                self.relationship_values(manager="allow_unsaved_relationship_values_manager").clear()
