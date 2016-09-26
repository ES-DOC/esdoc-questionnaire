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

"""
.. module:: models_realizations

The actual CIM Models & Properties to create

"""

from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from uuid import uuid4, UUID as generate_uuid
from collections import OrderedDict
from mptt.models import MPTTModel, TreeForeignKey

from Q.questionnaire import APP_LABEL, q_logger
from Q.questionnaire.models.models_customizations import QModelCustomization, QPropertyCustomization
from Q.questionnaire.models.models_publications import QPublication, QPublicationFormats
from Q.questionnaire.serializers.serializers_base import enumeration_field_to_enumeration_serialization
from Q.questionnaire.q_fields import QVersionField, QCardinalityField, QEnumerationField, QPropertyTypes, QNillableTypes, QUnsavedRelatedManager, allow_unsaved_fk
from Q.questionnaire.q_utils import QError, Version, EnumeratedType, EnumeratedTypeList, pretty_string, find_in_sequence, serialize_model_to_dict
from Q.questionnaire.q_constants import *

#############
# constants #
#############

# these fields are all handled behind-the-scenes
# there is no point passing them around to serializers or forms
QREALIZATION_NON_EDITABLE_FIELDS = ["guid", "created", "modified", ]

###############
# global vars #
###############

class RealizationType(EnumeratedType):

    def __unicode__(self):
        return u"%s" % (self.get_name())

RealizationTypes = EnumeratedTypeList([
    RealizationType("MODEL", "Model Realization"),
    RealizationType("CATEGORY", "Category Realization"),
    RealizationType("PROPERTY", "Property Realization"),
])

##############
# global fns #
##############

def get_new_realizations(project=None, ontology=None, model_proxy=None, **kwargs):

    key = kwargs.pop("key")
    realizations = kwargs.pop("realizations", {})

    # TODO: CHANGE THIS TO USE GUIDS INSTEAD OF NAMES FOR KEYS
    # TODO: TRY TO REWRITE THIS TO USE "prefix" AGAIN (INSTEAD OF EXPLICIT "key")

    # unlike w/ customizations, I do not create the entire possible set all at once
    # instead I just deal w/ the minimum number of properties (based on cardinality)
    # infinite recursion is therefore avoided; not by re-using previously created models
    # as with customizations, but by only creating a finite amount of models
    # hooray

    model = QModel(
        project=project,
        ontology=ontology,
        proxy=model_proxy,
    )
    model.version = Version("0.0.0")
    model.reset()

    properties = []
    for property_proxy in model_proxy.property_proxies.all():
        with allow_unsaved_fk(QProperty, ["model"]):
            property = QProperty(
                model=model,
                proxy=property_proxy,
            )

            property.reset()
        properties.append(property)
    model.properties(manager="allow_unsaved_properties_manager").add_potentially_unsaved(*properties)

    return model

def get_existing_realizations(project=None, ontology=None, model_proxy=None, model_id=None, **kwargs):

    model = QModel.objects.get(pk=model_id)
    assert model.ontology == ontology
    assert model.proxy == model_proxy
    assert model.project == project

    return model

def serialize_new_realizations(current_model_realization, **kwargs):

    # get the model stuff...
    model_serialization = serialize_model_to_dict(
        current_model_realization,
        include={
            "key": current_model_realization.get_key(),
            "version": current_model_realization.version.fully_specified(),
            # "is_complete": current_model_realization.is_complete(),
            "display_detail": False,
            "display_properties": False,
        },
        exclude=QREALIZATION_NON_EDITABLE_FIELDS + ["synchronization", ]
    )

    # and the properties stuff...
    property_serializations = []
    for property_realization in current_model_realization.properties(manager="allow_unsaved_properties_manager").all():
        property_serialization = serialize_model_to_dict(
            property_realization,
            include={
                "enumeration_value": enumeration_field_to_enumeration_serialization(property_realization.enumeration_value),  # both the FormField & the SerializerField ensure that values are converted to lists
                "key": property_realization.get_key(),                                                                        # since serialize_new_realizations is called outside of DRF, I have to do this explicitly here
                # "is_complete": property_realization.is_complete(),
                "possible_relationship_targets": property_realization.get_possible_relationship_targets(),
                # TODO: 'is_multiple' IS COMPUTED IN THE NG CONTROLLER; NO NEED TO REPLICATE IT HERE
                "is_multiple": property_realization.is_multiple(),
                "display_detail": False,
            },
            exclude=QREALIZATION_NON_EDITABLE_FIELDS,
        )

        ############################
        # here begins the icky bit #
        ############################

        relationship_values_serializations = []
        if property_realization.proxy.use_subforms():
            # TODO: IF I WERE TO PRE-CREATE RELATIONSHIPS, THIS IS WHERE I WOULD DO IT
            pass
        property_serialization["relationship_values"] = relationship_values_serializations

        ##########################
        # here ends the icky bit #
        ##########################

        property_serializations.append(property_serialization)

    # and put it all together...
    serialization = OrderedDict(model_serialization)
    serialization["properties"] = property_serializations

    return serialization

def get_model_realization_by_fn(fn, current_model_realization):
    if fn(current_model_realization):
        return current_model_realization

    return get_realization_by_fn_recusively(
        fn,
        current_model_realization.properties(manager="allow_unsaved_properties_manager").all(),
        RealizationTypes.MODEL,
    )


def get_property_realization_by_fn(fn, current_model_realization):

    property = find_in_sequence(
        fn,
        current_model_realization.properties(manager="allow_unsaved_properties_manager").all()
    )
    if property:
        return property

    if current_model_realization.is_new():
        return get_realization_by_fn_recusively(
            fn,
            current_model_realization.properties(manager="allow_unsaved_properties_manager").all(),
            RealizationTypes.PROPERTY,
        )
    else:  # current_model_realization.is_existing()
        raise NotImplementedError("todo")
        return find_in_sequence(
            fn,
            QProperty.objects.filter(
                model__project=current_model_realization.project,
                # name=current_model_realization.name,
            )
        )

def get_realization_by_fn_recusively(fn, current_property_realizations, realization_type, **kwargs):
    """
    used in conjunction w/ the "get_<x>_realization_by_fn" fns above
    recursively goes through the realization hierarchy (of unsaved customizations)
    returns the first realization that returns True for fn
    :param fn: fn to call
    :param current_property_realizations: the property realizations from which to begin checking
    :param realization_type: the type of realization to check
    :return: either QModel or QCategory or QProperty or None
    """

    previously_recursed_realizations = kwargs.pop("previously_recursed_realizations", set())

    for property in current_property_realizations:
        property_key = property.get_key()
        if property_key not in previously_recursed_realizations:
            if realization_type == RealizationTypes.PROPERTY and fn(property):
                return property

            if property.proxy.use_subforms():
                target_models = property.relationship_values(manager="allow_unsaved_relationship_values_manager").all()
                for target_model in target_models:

                    if realization_type == RealizationTypes.MODEL:
                        if fn(target_model):
                            return target_model

                    elif realization_type == RealizationTypes.CATEGORY:
                        target_category = find_in_sequence(
                            fn,
                            target_model.categories(manager="allow_unsaved_category_customizations_manager").all()

                        )
                        if target_category:
                            return target_category

                    elif realization_type == RealizationTypes.PROPERTY:
                        pass  # (this will already have been checked above)

                    previously_recursed_realizations.add(property_key)  # only tracking properties b/c those are the only recursive things
                    matching_realization = get_realization_by_fn_recusively(
                        fn,
                        target_model.properties(manager="allow_unsaved_properties_manager").all(),
                        realization_type,
                        previously_recursed_realizations=previously_recursed_realizations,
                    )
                    if matching_realization:
                        return matching_realization

def recurse_through_realizations(fn, current_model_realization, realization_types, **kwargs):
    """
    recursively applies fn recursively to all realization types
    :param fn: fn to call
    :param current_model_realization: the model realization from which to begin checking
    :param realization_type: the type of realization to check
    :return: either QModel or QCategory or QProperty or None
    """

    previously_recursed_realizations = kwargs.pop("previously_recursed_realizations", set())
    value = kwargs.pop("value", [])

    # note I work backwards; recursing through the propertries _before_ continuing w/ the current_model_realization

    for property_realization in current_model_realization.properties(manager="allow_unsaved_properties_manager").all():
        property_realization_key = property_realization.get_key()
        if property_realization_key not in previously_recursed_realizations:

            if property_realization.field_type == QPropertyTypes.RELATIONSHIP:
                target_model_realizations = property_realization.relationship_values(manager="allow_unsaved_relationship_values_manager").all()
                for target_model_realization in target_model_realizations:
                    previously_recursed_realizations.add(property_realization_key)  # only tracking property_customizations b/c those are the only recursive things
                    recurse_through_realizations(
                        fn,
                        target_model_realization,
                        realization_types,
                        previously_recursed_realizations=previously_recursed_realizations,
                        value=value,
                    )

            if RealizationTypes.PROPERTY in realization_types:
                value.append(
                    fn(property_realization)
            )

    # for category_customization in current_model_customization.category_customizations(manager="allow_unsaved_category_customizations_manager").all():
    #     if RealizationTypes.CATEGORY in realization_types:
    #         value.append(
    #            fn(category_customization)
    #         )

    if RealizationTypes.MODEL in realization_types:
        value.append(
            fn(current_model_realization)
        )

    return value

def set_owner(model_realization, new_owner):
    recurse_through_realizations(
        lambda c: c.set_owner(new_owner),
        model_realization,
        [RealizationTypes.MODEL],
    )


def set_shared_owner(model_realization, new_owner):
    recurse_through_realizations(
        lambda c: c.set_shared_owner(new_owner),
        model_realization,
        [RealizationTypes.MODEL],
    )


def update_completion(model_realization):

    def _update_completion(r):
        property_completion = [
            p.get_completion()
            for p in r.properties(manager="allow_unsaved_properties_manager").all()
        ]
        model_completion = all(property_completion)
        if model_completion != r.is_complete:
            r.is_complete = model_completion
            r.save()  # force these changes to be persistent the next time this realization is queried; TODO: IS THIS EXTRA SAVE INEFFICIENT?

        return model_completion

    recurse_through_realizations(
        # lambda r: _update_completion(r),  # d'oh! a lambda fn isn't needed here
        _update_completion,
        model_realization,
        [RealizationTypes.MODEL]
    )


##################
# useful structs #
##################

from collections import deque  # I'm not sure I need the full complexity of a deque, but in my head I want a linked-list so this made sense

class PathNode(object):
    """
    used to define a path along a hierarchy of realizations or customizations
    """

    def __init__(self, type=None, guid=None, proxy=None, project=None):
        self._type = type  # the type of node
        self._guid = guid  # the id of the node
        self._proxy = proxy  # the proxy corresponding to the node
        self._project = project  # the project that the realization is part of (only applies to QModelRealization)

    def get_type(self):
        return self._type

    def get_guid(self):
        return self._guid

    def get_proxy(self):
        return self._proxy

    def get_project(self):
        return self._project


##############
# base class #
##############

# TODO: THIS BASE CLASS IS USED W/ MULTIPLE INHERITANCE
# TODO: SHOULD IT BE USED IN A MORE "MIX-IN" FASHION ?
# TODO: AND DEFINED IN "models_base.py" AND USED FOR BOTH Customizations & Realizations?

class QRealization(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = True
        verbose_name = "_Questionnaire Realization"
        verbose_name_plural = "_Questionnaire Realization"

    guid = models.UUIDField(default=uuid4, editable=False)  # unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def __eq__(self, other):
        if isinstance(other, QRealization):
            return self.guid == other.guid
        return NotImplemented

    def __ne__(self, other):
        equality_result = self.__eq__(other)
        if equality_result is NotImplemented:
            return equality_result
        return not equality_result

    def get_default_customization(self):
        """
        given any realization, get the corresponding customization
        this is not as easy as it sounds, b/c there could be potential recursion & re-use of proxies throughout the customization hierarchy
        so I create a "path" locating the current realization and then walk along that path starting from the default customization
        in a really recursive situation, this might wind up needlessly looping around the same customizations but I don't know a way around that
        :return: QCustomization
        """

        # walk backwards from the current realization to the top-level model realization & record the path...
        path = self.get_path()

        # get the starting path_node (the one corresponding to the top-level realization)...
        node = path.popleft()
        # get the starting customization (the one corresponding to the top-level customization)...
        customization = QModelCustomization.objects.get(proxy=node.get_proxy(), project=node.get_project(), is_default=True)

        while len(path):
            # walk forwards along the path moving through the customizations...
            node = path.popleft()
            node_type = node.get_type()
            if node_type == RealizationTypes.PROPERTY:
                assert isinstance(customization, QModelCustomization)
                customization = customization.property_customizations.get(proxy=node.get_proxy())
            elif node_type == RealizationTypes.MODEL:
                assert isinstance(customization, QPropertyCustomization)
                customization = customization.relationship_target_model_customizations.get(proxy=node.get_proxy())

        # return whichever customization you wound up at...
        return customization

    def get_path(self, **kwargs):
        path = kwargs.get("path", deque())
        if isinstance(self, QProperty):
            path.appendleft(PathNode(RealizationTypes.PROPERTY, self.guid, self.proxy))
            return self.model.get_path(path=path)
        elif isinstance(self, QModel):
            path.appendleft(PathNode(RealizationTypes.MODEL, self.guid, self.proxy, self.project))  # notice that QModel includes a project
            parent_property = self.relationship_property
            if parent_property:
                return parent_property.get_path(path=path)
            return path
        else:
            msg = "I don't know how to find a customization for {0}".format(self)
            raise QError(msg)

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

    def get_key(self):
        # convert UUID to str b/c UUID does not play nicely w/ JSON
        return str(self.guid)

    def is_existing(self):
        return self.pk is not None

    def is_new(self):
        return self.pk is None

    def reset(self):
        msg = "{0} must define a custom 'reset' method.".format(self.__class__.__name__)
        raise NotImplementedError(msg)

######################
# model realizations #
######################

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

    def owned_documents(self, user):
        return self.root_documents().filter(owner=user)

    def shared_documents(self, user):
        return self.root_documents().filter(shared_owners__in=[user.pk])

class QModel(MPTTModel, QRealization):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "Questionnaire Realization: Model"
        verbose_name_plural = "_Questionnaire Realizations: Models"
        ordering = ("created", )

    class _QRelationshipValuesUnsavedRelatedManager(QUnsavedRelatedManager):

        def get_unsaved_related_field_name(self):
            _field = QModel.get_field("relationship_property")
            _related_field_name = _field.related.name
            _unsaved_related_field_name = "_unsaved_{0}".format(_related_field_name)
            return _unsaved_related_field_name

    # custom managers...
    # according to Django [https://docs.djangoproject.com/en/1.9/topics/db/managers/#custom-managers-and-model-inheritance], the 1st manager specified is the default manager; so I must explicitly reset "objects" here
    objects = QModelQuerySet.as_manager()
    allow_unsaved_relationship_values_manager = _QRelationshipValuesUnsavedRelatedManager()

    owner = models.ForeignKey(User, blank=False, null=True, related_name="owned_models", on_delete=models.SET_NULL)
    shared_owners = models.ManyToManyField(User, blank=True, related_name="shared_models")

    parent = TreeForeignKey("self", null=True, blank=True, related_name="children")

    project = models.ForeignKey("QProject", blank=False, related_name="models")
    ontology = models.ForeignKey("QOntology", blank=False, related_name="models")
    proxy = models.ForeignKey("QModelProxy", blank=False, related_name="models")

    name = models.CharField(max_length=LIL_STRING, blank=True)
    description = models.TextField(blank=True)
    version = QVersionField(blank=True, null=True)  # I am using the full complexity of a "major.minor.patch" version, even though I don't expose "patch"

    is_document = models.BooleanField(blank=False, null=False, default=False)
    is_root = models.BooleanField(blank=False, null=False, default=False)
    is_published = models.BooleanField(blank=False, null=False, default=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)

    is_complete = models.BooleanField(blank=False, null=False, default=False)

    synchronization = models.ManyToManyField("QSynchronization", blank=True)

    # this fk is just here to provide the other side of the relationship to QProperty
    # I only ever access "property.relationship_values"
    relationship_property = models.ForeignKey("QProperty", blank=True, null=True, related_name="relationship_values")

    def __str__(self):
        return pretty_string(self.name)

    # def is_complete(self):
    #     completion = recurse_through_realizations(
    #         lambda p: p.is_complete(),
    #         self,
    #         [RealizationTypes.PROPERTY]
    #     )
    #     return all(completion)

    def is_synchronized(self):
        return self.synchronization.count() == 0  # checks if qs is empty

    def is_unsynchronized(self):
        return not self.is_synchronized()

    def publish(self, **kwargs):
        """
        :param force_save: save the model (after incrementing its version);
        the only reason not to do this is when re-publishing something at the same version b/c of a content error
        :return:
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
        publication_dict = {
            "project": self.project,
            "ontology": self.ontology,
            "proxy": self.proxy,
            "model": self,
            "publication_format": publication_format,
        }
        publication_template_path = "{0}/publications/{1}/{2}.xml".format(APP_LABEL, publication_format, self.proxy.name)
        publication_content = render_to_string(publication_template_path, publication_dict)
        publication.content = publication_content
        publication.save()

        self.is_published = True
        if force_save:
            self.save()

        return publication

    def reset(self):

        # this resets values according to the proxy
        # to reset values according to the customizer, you must go through the client
        # (ie: Djangular forms and NG controllers)
        proxy = self.proxy

        self.name = proxy.name
        self.description = proxy.documentation

        self.is_document = proxy.is_document()
        # TODO:
        # self.is_root = ?!?
        self.is_active = True

        self.is_complete = False

    def set_owner(self, new_owner):
        # used w/ "recurse_through_realization" in global fn "set_owner" above
        self.owner = new_owner

    def set_shared_owner(self, new_shared_owner):
        # used w/ "recurse_through_realization" in global fn "set_shared_owner" above
        self.shared_owners.add(new_shared_owner)

#########################
# property realizations #
#########################

class QProperty(QRealization):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "Questionnaire Realization: Property"
        verbose_name_plural = "_Questionnaire Realizations: Properties"
        ordering = ("order", )

    class _QPropertyUnsavedRelatedManager(QUnsavedRelatedManager):

        def get_unsaved_related_field_name(self):
            _field = QProperty.get_field("model")
            _related_field_name = _field.related.name
            _unsaved_related_field_name = "_unsaved_{0}".format(_related_field_name)
            return _unsaved_related_field_name

    # custom managers...
    # according to Django [https://docs.djangoproject.com/en/1.9/topics/db/managers/#custom-managers-and-model-inheritance], the 1st manager specified is the default manager; so I must explicitly reset "objects" here
    objects = models.Manager()
    allow_unsaved_properties_manager = _QPropertyUnsavedRelatedManager()

    model = models.ForeignKey("QModel", blank=False, related_name="properties")
    proxy = models.ForeignKey("QPropertyProxy", blank=False)

    name = models.CharField(max_length=SMALL_STRING, blank=False, null=False)
    order = models.PositiveIntegerField(blank=True, null=True)

    field_type = models.CharField(max_length=BIG_STRING, blank=False, choices=[(ft.get_type(), ft.get_name()) for ft in QPropertyTypes])

    cardinality = QCardinalityField(blank=False)

    is_complete = models.BooleanField(blank=False, null=False, default=False)

    atomic_value = models.TextField(blank=True, null=True)
    enumeration_value = QEnumerationField(blank=False, null=True)
    enumeration_other_value = models.CharField(max_length=HUGE_STRING, blank=True, null=True)

    # using the reverse of the fk defined on model instead of this field
    # (so that I can use a custom manager to cope w/ unsaved instances)
    # relationship_values = models.ManyToManyField("QModel", blank=True, related_name="+")
    # TODO: relationship_references = ?!?

    is_nil = models.BooleanField(default=False)
    nil_reason = models.CharField(
        max_length=BIG_STRING,
        blank=False,
        default=QNillableTypes.first().get_type(),
        choices=[(nt.get_type(), nt.get_description()) for nt in QNillableTypes],
    )

    def __str__(self):
        return pretty_string(self.name)

    def get_customization(self):
        # TODO
        return None
        raise NotImplementedError()

    def get_possible_relationship_targets(self):
        if self.field_type == QPropertyTypes.RELATIONSHIP:
            return [
                {"pk": target.pk, "name": target.name}
                for target in self.proxy.relationship_target_models.all()
            ]
        return []

    def get_value(self):
        # returns the value field for this particular property type
        if self.field_type == QPropertyTypes.ATOMIC:
            return self.atomic_value
        elif self.field_type == QPropertyTypes.ENUMERATION:
            return self.enumeration_value
        else:  # self.field_type == QPropertyTYpes.RELATIONSHIP
            return self.relationship_values.all()

    def get_completion(self):

        cardinality_min = int(self.get_cardinality_min())
        if cardinality_min:
            # if ths property is required then check some things...

            if self.is_nil:
                # something that s required but explicitly set to "nil" is still considered complete
                return True

            if self.field_type == QPropertyTypes.ATOMIC:
                if self.atomic_value:
                    return True
                return False

            elif self.field_type == QPropertyTypes.ENUMERATION:
                if self.enumeration_value:
                    return True
                return False

            else:  # self.field_type == QPropertyTypes.RELATIONSHIP
                relationship_completion = [m.is_complete for m in self.relationship_values.all()]  # TODO: DOES THIS WORK W/ UNSAVED FIELDS ?!?
                return len(relationship_completion) == cardinality_min and all(relationship_completion)

        else:
            # a non-required property is complete by default
            # TODO: WHAT ABOUT PROPERTIES THAT ARE _CUSTOMIZED_ TO BE REQUIRED ?!?
            return True

    def get_completion2(self):

        # ordinarily, the 'is_complete' field is used for this
        # but when calling update_completion (from outside the client), I explicitly compute it
        # this is used by the Project View

        if int(self.get_cardinality_min()) > 0:
            # if ths property is required then check some things...

            if self.is_nil:
                # something that s required but explicitly set to "nil" is still considered complete
                return True

            if self.field_type == QPropertyTypes.ATOMIC:
                if self.atomic_value:
                    return True
                return False

            elif self.field_type == QPropertyTypes.ENUMERATION:
                if self.enumeration_value:
                    return True
                return False

            else:  # self.field_type == QPropertyTypes.RELATIONSHIP
                relationship_completion = [m.is_complete for m in self.relationship_values.all()]  # TODO: DOES THIS WORK W/ UNSAVED FIELDS ?!?
                return len(relationship_completion) and all(relationship_completion)

        else:
            # a non-required property is complete by default
            # TODO: WHAT ABOUT PROPERTIES THAT ARE _CUSTOMIZED_ TO BE REQUIRED ?!?
            return True

        if self.is_nil:
            return True
    # def is_complete(self):
    #     # TODO:
    #     import ipdb; ipdb.set_trace()
    #     if int(self.get_cardinality_min()) > 0:
    #         # if this property is required check some things...
    #
    #         if self.is_nil:
    #             # something that is required but explicitly set to "nil" is still considered complete
    #             return True
    #
    #         value = self.get_value()
    #         if value:
    #             return True
    #         else:
    #             return False
    #
    #     else:
    #         # a non-required property is complete by default
    #         # TODO: WHAT ABOUT PROPERTIES THAT ARE _CUSTOMIZED_ TO BE REQUIRED ?!?
    #         return True


    def is_multiple(self):
        cardinality_max = self.get_cardinality_max()
        return cardinality_max == u'*' or int(cardinality_max) > 1

    def is_single(self):
        return not self.is_multiple()

    def reset(self):

        # this resets values according to the proxy
        # to reset values according to the customizer, you must go through the client
        # (ie: Djangular forms and NG controllers)
        proxy = self.proxy

        field_type = proxy.field_type
        self.field_type = field_type

        self.cardinality = proxy.cardinality

        self.name = proxy.name
        self.description = proxy.documentation
        self.order = proxy.order
        self.is_nil = False
        self.nil_reason = self.get_field("nil_reason").default

        self.is_complete = False

        if field_type == QPropertyTypes.ATOMIC:
            self.atomic_value = None

        elif field_type == QPropertyTypes.ENUMERATION:
            # TODO: THIS IS NOT THE RIGHT PLACE FOR THIS CODE
            # TODO: SINCE "reset" ONLY GETS CALLED FOR NEW MODELS
            # TODO: INSTEAD I OUGHT TO RUN THIS WHEN THE FORM IS CREATED
            enumeration_value_field = self.get_field("enumeration_value")
            enumeration_value_field.set_choices(proxy.get_enumeration_members())
            enumeration_value_field.set_cardinality(proxy.get_cardinality_min(), proxy.get_cardinality_max())
            self.enumeration_other_value = None

        else:  # field_type == QPropertyTypes.RELATIONSHIP
            # self.relationship_values(manager="allow_unsaved_relationship_values_manager").clear()
            pass
