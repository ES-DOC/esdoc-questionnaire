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
from django.db.models.fields import FieldDoesNotExist
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from uuid import uuid4, UUID as generate_uuid
from collections import OrderedDict

from Q.questionnaire import APP_LABEL, q_logger
from Q.questionnaire.q_fields import QPropertyTypes, QAtomicPropertyTypes, allow_unsaved_fk, QUnsavedRelatedManager
from Q.questionnaire.q_utils import EnumeratedType, EnumeratedTypeList, BAD_CHARS_LIST, validate_no_bad_chars, validate_no_bad_suggestion_chars, validate_no_spaces, validate_no_reserved_words, validate_no_profanities, pretty_string, find_in_sequence, serialize_model_to_dict
from Q.questionnaire.q_constants import *

#############
# constants #
#############

# these fields are all handled behind-the-scenes
# there is no point passing them around to serializers or forms
QCUSTOMIZATION_NON_EDITABLE_FIELDS = ["guid", "created", "modified", ]

###############
# global vars #
###############

class CustomizationType(EnumeratedType):

    def __unicode__(self):
        return u"%s" % (self.get_name())

CustomizationTypes = EnumeratedTypeList([
    CustomizationType("MODEL", "Model Customization"),
    CustomizationType("CATEGORY", "Category Customization"),
    CustomizationType("PROPERTY", "Property Customization"),
])

##############
# global fns #
##############

def get_new_customizations(project=None, ontology=None, model_proxy=None, **kwargs):

    key = kwargs.pop("key")
    customizations = kwargs.pop("customizations", {})

    # TODO: CHANGE THIS TO USE GUIDS INSTEAD OF NAMES FOR KEYS
    # TODO: TRY TO REWRITE THIS TO USE "prefix" AGAIN (INSTEAD OF EXPLICIT "key")

    model_proxy_key = key
    if model_proxy_key not in customizations:
        model_customization = QModelCustomization(
            project=project,
            ontology=ontology,
            proxy=model_proxy,
        )
        model_customization.reset()
        customizations[model_proxy_key] = model_customization
    else:
        model_customization = customizations[model_proxy_key]

    category_customizations = []
    for catgegory_proxy in ontology.categorization.category_proxies.all():
        category_proxy_key = "{0}.{1}".format(model_proxy_key, catgegory_proxy.name)
        with allow_unsaved_fk(QCategoryCustomization, ["model_customization"]):
            if category_proxy_key not in customizations:
                category_customization = QCategoryCustomization(
                    proxy=catgegory_proxy,
                    model_customization=model_customization,
                )
                category_customization.reset()
                customizations[category_proxy_key] = category_customization
            else:
                category_customization = customizations[category_proxy_key]
        category_customizations.append(category_customization)
    # assert category_customizations[-1].proxy == ontology.categorization.get_uncategorized_category_proxy()
    model_customization.category_customizations(manager="allow_unsaved_category_customizations_manager").add_potentially_unsaved(*category_customizations)

    property_customizations = []
    for property_proxy in model_proxy.property_proxies.all():
        property_proxy_key = "{0}.{1}".format(model_proxy_key, property_proxy.name)
        with allow_unsaved_fk(QPropertyCustomization, ["model_customization", "category"]):
            # close this context manager before using the custom related manager
            # (too much hackery at once)
            if property_proxy_key not in customizations:
                category_customization = find_in_sequence(
                    lambda c: c.proxy.has_property(property_proxy),
                    category_customizations
                )
                property_customization = QPropertyCustomization(
                    proxy=property_proxy,
                    model_customization=model_customization,
                    category=category_customization,
                )
                property_customization.reset()
                category_customization.property_customizations(manager="allow_unsaved_categories_manager").add_potentially_unsaved(property_customization)
                customizations[property_proxy_key] = property_customization
            else:
                property_customization = customizations[property_proxy_key]
        property_customizations.append(property_customization)

        ############################
        # here begins the icky bit #
        ############################

        if property_customization.use_subforms():
            subform_key = "{0}.{1}".format(model_proxy.name, property_proxy.name)  # this property in this model (only 1 level deep)
            target_model_customizations = []
            for target_model_proxy in property_proxy.relationship_target_models.all():
                target_model_proxy_key = "{0}.{1}".format(subform_key, target_model_proxy.name)
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
            ontology=ontology,
            proxy=model_proxy,
            project=project,
            name__iexact=customization_name,
        )
    else:
        model_customization = QModelCustomization.objects.get(pk=customization_id)
        assert model_customization.ontology == ontology
        assert model_customization.proxy == model_proxy
        assert model_customization.project == project
        if customization_name:
            assert model_customization.name.lower() == customization_name.lower()

    return model_customization

def serialize_new_customizations(current_model_customization, **kwargs):
    """
    need a special fn to cope w/ this
    b/c getting DRF to work w/ potentially infinite recursion is impossible
    it is likely that these customizations will need to be serialized before they have been saved

    therefore the m2m fields will not yet exist in the db
    the workflow goes:
    * get_new_customizations where calls to create are wrapped in "allow_unsaved_fk" & custom "QUnsavedRelatedManager" are used
    * those customizations get cached in the current session
    * AJAX calls to the RESTful API access those cached customizations
    * which needs to be serialized via this fn and then passed as data to QModelCustomizationSerializer
    :param customizations
    :return: OrderedDict
    """
    previously_serialized_customizations = kwargs.pop("previously_serialized_customizations", {})
    prefix = kwargs.pop("prefix", None)

    # get model customization stuff...
    model_customization_key = current_model_customization.get_fully_qualified_key(prefix=prefix)
    if model_customization_key not in previously_serialized_customizations:
        model_customization_serialization = serialize_model_to_dict(
            current_model_customization,
            include={
                "key": current_model_customization.get_key(),
                "proxy_name": str(current_model_customization.proxy),
                "display_detail": False,
            },
            exclude=QCUSTOMIZATION_NON_EDITABLE_FIELDS + ["synchronization", ]
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
                    "key": category_customization.get_key(),
                    "num_properties": category_customization.property_customizations(manager="allow_unsaved_categories_manager").count(),
                    "proxy_name": str(category_customization.proxy),
                    "display_properties": True,
                    "display_detail": False,
                },
                exclude=QCUSTOMIZATION_NON_EDITABLE_FIELDS
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
            use_subforms = property_customization.use_subforms()
            category_customization = property_customization.category
            property_customization_serialization = serialize_model_to_dict(
                property_customization,
                include={
                    "key": property_customization.get_key(),
                    "category_key": category_customization.get_key(),
                    "proxy_name": str(property_customization.proxy),
                    "display_detail": False,
                    # "enumeration_choices": standard_property_customization.get_enumeration_choices_value(),
                    "use_subforms": use_subforms,
                },
                exclude=QCUSTOMIZATION_NON_EDITABLE_FIELDS
            )

            ############################
            # here begins the icky bit #
            ############################

            subform_customizations_serializations = []
            if use_subforms:
                subform_prefix = property_customization.get_fully_qualified_key()  # note I do _not_ pass the prefix kwarg
                for subform_model_customization in property_customization.relationship_target_model_customizations(manager="allow_unsaved_relationship_target_model_customizations_manager").all():
                    subform_model_customization_key = subform_model_customization.get_fully_qualified_key(prefix=subform_prefix)
                    if subform_model_customization_key not in previously_serialized_customizations:
                        subform_customizations_serialization = serialize_new_customizations(
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

def get_model_customization_by_fn(fn, current_model_customization):
    """
    returns the 1st matching QModelCustomization in the customization hierarchy...
    if the top-level model_customization matches, this is simple
    if the cusotmizations are existing (ie: already saved), this is straightforward
    if the customizations are new (ie: not saved), this is icky
    :param fn: fn to use to find customization
    :param customizations: customizations to check
    :return: QModelCustomization
    """
    # RECALL THAT AS OF v0.16.0.0 INSTEAD OF PASSING A COMPLEX NESTED DICTIONARY
    # I AM JUST PASSING A SINGLE model_customization INSTANCE W/ ALL ITS M2M FIELDS ALREADY COMPLETE
    if fn(current_model_customization):
        return current_model_customization

    if current_model_customization.is_new():
        return get_customization_by_fn_recusively(
            fn,
            current_model_customization.property_customizations(manager="allow_unsaved_property_customizations_manager").all(),
            CustomizationTypes.MODEL,
        )
    else:  # current_model_customization.is_existing()
        return find_in_sequence(
            fn,
            QModelCustomization.objects.filter(
                project=current_model_customization.project,
                name=current_model_customization.name,
            )
        )


def get_category_customization_by_fn(fn, current_model_customization):
    """
    returns the 1st matching QCategoryCustomization in the customization hierarchy...
    if the top-level category_customization matches, this is simple
    if the cusotmizations are existing (ie: already saved), this is straightforward
    if the customizations are new (ie: not saved), this is icky
    :param fn: fn to use to find customization
    :param current_model_customization: customizations to check
    :return: QCategoryCustomization
    """
    # RECALL THAT AS OF v0.16.0.0 INSTEAD OF PASSING A COMPLEX NESTED DICTIONARY
    # I AM JUST PASSING A SINGLE model_customization INSTANCE W/ ALL ITS M2M FIELDS ALREADY COMPLETE

    category_customization = find_in_sequence(
        fn,
        current_model_customization.category_customizations(manager="allow_unsaved_category_customizations_manager").all()
    )
    if category_customization:
        return category_customization

    if current_model_customization.is_new():
        return get_customization_by_fn_recusively(
            fn,
            current_model_customization.property_customizations(manager="allow_unsaved_property_customizations_manager").all(),
            CustomizationTypes.CATEGORY,
        )
    else:  # current_model_customization.is_existing()
        return find_in_sequence(
            fn,
            QCategoryCustomization.objects.filter(
                model_customization__project=current_model_customization.project,
                name=current_model_customization.name,
            )
        )


def get_property_customization_by_fn(fn, current_model_customization):
    """
    returns the 1st matching QPropertyCustomization in the customization hierarchy...
    if the top-level property_customization matches, this is simple
    if the cusotmizations are existing (ie: already saved), this is straightforward
    if the customizations are new (ie: not saved), this is icky
    :param fn: fn to use to find customization
    :param current_model_customization: customizations to check
    :return: QPropertyCustomization
    """
    # RECALL THAT AS OF v0.16.0.0 INSTEAD OF PASSING A COMPLEX NESTED DICTIONARY
    # I AM JUST PASSING A SINGLE model_customization INSTANCE W/ ALL ITS M2M FIELDS ALREADY COMPLETE

    property_customization = find_in_sequence(
        fn,
        current_model_customization.property_customizations(manager="allow_unsaved_property_customizations_manager").all()
    )
    if property_customization:
        return property_customization

    if current_model_customization.is_new():
        return get_customization_by_fn_recusively(
            fn,
            current_model_customization.property_customizations(manager="allow_unsaved_property_customizations_manager").all(),
            CustomizationTypes.PROPERTY,
        )
    else:  # current_model_customization.is_existing()
        return find_in_sequence(
            fn,
            QPropertyCustomization.objects.filter(
                model_customization__project=current_model_customization.project,
                name=current_model_customization.name,
            )
        )


def get_customization_by_fn_recusively(fn, current_property_customizations, customization_type, **kwargs):
    """
    used in conjunction w/ the "get_<x>_customization_by_fn" fns above
    recursively goes through the customization hierarchy (of unsaved customizations)
    returns the first customization that returns True for fn
    :param fn: fn to call
    :param property_customizations: the property customizations from which to begin checking
    :param customization_type: the type of customization to check
    :return: either QModelCustomization or QCategoryCustomization or QPropertyCustomization or None
    """

    previously_recursed_customizations = kwargs.pop("previously_recursed_customizations", set())

    for property_customization in current_property_customizations:
        property_customization_key = property_customization.get_key()
        if property_customization_key not in previously_recursed_customizations:
            if customization_type == CustomizationTypes.PROPERTY and fn(property_customization):
                return property_customization

            if property_customization.use_subforms():
                target_model_customizations = property_customization.relationship_target_model_customizations(manager="allow_unsaved_relationship_target_model_customizations_manager").all()
                for target_model_customization in target_model_customizations:

                    if customization_type == CustomizationTypes.MODEL:
                        if fn(target_model_customization):
                            return target_model_customization

                    elif customization_type == CustomizationTypes.CATEGORY:
                        target_category_customization = find_in_sequence(
                            fn,
                            target_model_customization.category_customizations(manager="allow_unsaved_category_customizations_manager").all()

                        )
                        if target_category_customization:
                            return target_category_customization

                    else:  # customization_type == CustomizationTypes.PROPERTY
                        pass  # (this will already have been checked above)

                    previously_recursed_customizations.add(property_customization_key)  # only tracking property_customizations b/c those are the only recursive things
                    matching_customization = get_customization_by_fn_recusively(
                        fn,
                        target_model_customization.property_customizations(manager="allow_unsaved_property_customizations_manager").all(),
                        customization_type,
                        previously_recursed_customizations=previously_recursed_customizations,
                    )
                    if matching_customization:
                        return matching_customization


def recurse_through_customizations(fn, current_model_customization, customization_types, **kwargs):
    """
    recursively applies fn recursively to all customization types
    :param fn: fn to call
    :param current_model_customization: the model customization from which to begin checking
    :param customization_type: the type of customizations to check
    :return: either QModelCustomization or QCategoryCustomization or QPropertyCustomization or None
    """

    previously_recursed_customizations = kwargs.pop("previously_recursed_customizations", set())

    if CustomizationTypes.MODEL in customization_types:
        fn(current_model_customization)

    for category_customization in current_model_customization.category_customizations(manager="allow_unsaved_category_customizations_manager").all():
        if CustomizationTypes.CATEGORY in customization_types:
            fn(category_customization)

    for property_customization in current_model_customization.property_customizations(manager="allow_unsaved_property_customizations_manager").all():
        property_customization_key = property_customization.get_key()
        if property_customization_key not in previously_recursed_customizations:
            if CustomizationTypes.PROPERTY in customization_types:
                fn(property_customization)

            if property_customization.use_subforms():
                target_model_customizations = property_customization.relationship_target_model_customizations(manager="allow_unsaved_relationship_target_model_customizations_manager").all()
                for target_model_customization in target_model_customizations:
                    previously_recursed_customizations.add(property_customization_key)  # only tracking property_customizations b/c those are the only recursive things
                    recurse_through_customizations(
                        fn,
                        target_model_customization,
                        customization_types,
                        previously_recursed_customizations=previously_recursed_customizations,
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


##############
# base class #
##############

class QCustomization(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = True
        verbose_name = "_Questionnaire Customization"
        verbose_name_plural = "_Questionnaire Customizations"

    guid = models.UUIDField(default=uuid4, editable=False)  # unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    # all customizations share a name
    # (this makes finding related customizations simple: ".filter(project=parent.project, name=parent.name)" )
    name = models.CharField(
        max_length=LIL_STRING,
        blank=False,
        verbose_name="Customization Name",
        validators=[validate_no_bad_chars, validate_no_spaces, validate_no_reserved_words, validate_no_profanities],
        help_text="A unique name for this customization.  Spaces or the following characters are not allowed: \"%s\"." % BAD_CHARS_LIST,
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

    def get_fully_qualified_key(self, parent_key=None):
        msg = "{0} must define a custom 'get_fully_qualified_key' method.".format(self.__class__.__name__)
        raise NotImplementedError(msg)

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

    def get_unique_together(self):
        """
        'unique_together' validation is only enforced if all the unique_together fields appear in the ModelForm
        this fn returns the fields to check for manual validation
        """
        unique_together = self._meta.unique_together
        return list(unique_together)


#######################
# model customization #
#######################

class QModelCustomizationQuerySet(models.QuerySet):
    """
    As of Django 1.7 I can use custom querysets as managers
    to ensure that these custom methods are chainable
    whoo-hoo
    """

    def documents(self):
        return self.filter(proxy__stereotype__iexact="document")

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

    # custom managers...
    objects = QModelCustomizationQuerySet.as_manager()
    allow_unsaved_relationship_target_model_customizations_manager = _QModelCustomizationUnsavedRelatedManager()

    owner = models.ForeignKey(User, blank=False, null=True, related_name="owned_customizations", on_delete=models.SET_NULL)
    shared_owners = models.ManyToManyField(User, blank=True, related_name="shared_customizations")

    project = models.ForeignKey("QProject", blank=False, related_name="model_customizations")
    ontology = models.ForeignKey("QOntology", blank=False, null=False)
    proxy = models.ForeignKey("QModelProxy", blank=False, null=False)

    description = models.TextField(
        blank=True,
        help_text="An explanation of how this customization is intended to be used. This information is for informational purposes only.",
        verbose_name="Customization Description",
    )

    order = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    is_default = models.BooleanField(
        blank=False,
        null=False,
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
    model_show_all_categories = models.BooleanField(
        default=False,
        verbose_name="Display empty categories?",
        help_text="Include categories in the editing form for which there are no (visible) properties associated with",
    )

    # this fk is just here to provide the other side of the relationship to property_customization
    # I only ever access "property_customization.relationship_target_model_customizations"
    relationship_source_property_customization = models.ForeignKey("QPropertyCustomization", blank=True, null=True, related_name="relationship_target_model_customizations")

    synchronization = models.ManyToManyField("QSynchronization", blank=True)

    def __str__(self):
        return pretty_string(self.name)

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

        if self.proxy.is_document():

            if other_customizers.filter(proxy__stereotype__iexact="document", name=self.name).count() != 0:
                raise ValidationError({
                    "name": _("A customization for this proxy and project with this name already exists."),
                    # "proxy": _("A customization for this proxy and project with this name already exists."),
                    # "project": _("A customization for this proxy and project with this name already exists."),
                })

        super(QModelCustomization, self).clean(*args, **kwargs)

    def get_fully_qualified_key(self, prefix=None):
        fully_qualified_key = "{0}.{1}".format(self.proxy.get_fully_qualified_key(), self.guid)
        if prefix:
            return "{0}.{1}".format(prefix, fully_qualified_key)
        return fully_qualified_key

    def is_synchronized(self):
        return self.synchronization.count() == 0

    def is_unsynchronized(self):
        return not self.is_synchronized()

    def reset(self):
        proxy = self.proxy

        self.order = proxy.order

        self.model_title = pretty_string(proxy.name)
        self.model_description = proxy.documentation
        self.model_show_all_categories = False

    def save(self, *args, **kwargs):
        # force all (custom) "clean" methods to run
        self.full_clean()
        super(QModelCustomization, self).save(*args, **kwargs)

    ##################################################
    # some fns which are called from signal handlers #
    ##################################################

    def updated_ontology(self):

        property_customizers = list(self.property_customizers.all())  # the list fn forces immediate qs evaluation
        for property_customizer in property_customizers:

            if property_customizer.field_type == QPropertyTypes.RELATIONSHIP:
                # recurse through subforms...
                for target_model_customizer in property_customizer.target_model_customizers.all():
                    target_model_customizer.updated_ontology()

            property_proxy = property_customizer.proxy
            # TODO: DOUBLE-CHECK _ALL_ THE WAYS THAT THE ONTOLOGY COULD HAVE BEEN CHANGED
            if property_proxy.required and not property_customizer.required:
                property_customizer.required = True
                property_customizer.save()


##########################
# category customization #
##########################

class QCategoryCustomizationQuerySet(models.QuerySet):
    """
    As of Django 1.7 I can use custom querysets as managers
    to ensure that these custom methods are chainable
    whoo-hoo
    """

    def get_by_key(self, key):
        if isinstance(key, basestring):
            key = generate_uuid(key)
        # TODO: THERE IS THE CHANCE OF MULTIPLE CUSTOMIZATIONS W/ THE SAME KEY B/C OF RECURSION
        # TODO: THIS MAKES SURE TO ONLY EVER RETURN THE 1ST ONE
        # TODO: IN THE LONG-TERM, I SHOULD FIX THIS FROM HAPPENING
        # return self.get(guid=key)
        matching_category_customizations = self.filter(guid=key)
        if matching_category_customizations:
            return matching_category_customizations[0]
        return None


class QCategoryCustomization(QCustomization):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        ordering = ("order", )
        verbose_name = "_Questionnaire Customization: Category"
        verbose_name_plural = "_Questionnaire Customizations: Categories"

    class _QCategoryCustomizationUnsavedRelatedManager(QUnsavedRelatedManager):
        field_name = "model_customization"

    # custom managers...
    objects = QCategoryCustomizationQuerySet.as_manager()
    allow_unsaved_category_customizations_manager = _QCategoryCustomizationUnsavedRelatedManager()

    proxy = models.ForeignKey("QCategoryProxy", blank=False, null=False)

    model_customization = models.ForeignKey("QModelCustomization", blank=False, related_name="category_customizations")

    category_title = models.CharField(max_length=TINY_STRING, blank=False, validators=[validate_no_profanities, ])
    documentation = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return pretty_string(self.category_title)

    def get_fully_qualified_key(self, prefix=None):
        fully_qualified_key = "{0}.{1}".format(self.proxy.get_fully_qualified_key(), self.guid)
        if prefix:
            return "{0}.{1}".format(prefix, fully_qualified_key)
        return fully_qualified_key

    def has_property(self, property_customization):
        return property_customization in self.property_customizations.all()

    def set_name(self, new_name):
        # used w/ "recurse_through_customization" in global fn "set_name" above
        self.name = new_name

    def reset(self):

        proxy = self.proxy

        self.category_title = proxy.name
        self.documentation = proxy.documentation
        self.order = proxy.order

###########################
# property customizations #
###########################


class QPropertyCustomization(QCustomization):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        ordering = ("order", )
        verbose_name = "_Questionnaire Customization: Property"
        verbose_name_plural = "_Questionnaire Customizations: Properties"

    class _QPropertyCustomizationUnsavedRelatedManager(QUnsavedRelatedManager):
        field_name = "model_customization"

    class _QCategoryCustomizationUnsavedRelatedManager(QUnsavedRelatedManager):
        field_name = "category"

    # custom managers...
    # according to Django [https://docs.djangoproject.com/en/1.9/topics/db/managers/#custom-managers-and-model-inheritance], the 1st manager specified is the default manager; so I must explicitly reset "objects" here
    objects = models.Manager()
    allow_unsaved_property_customizations_manager = _QPropertyCustomizationUnsavedRelatedManager()
    allow_unsaved_categories_manager = _QCategoryCustomizationUnsavedRelatedManager()

    proxy = models.ForeignKey("QPropertyProxy", blank=False, null=False)

    model_customization = models.ForeignKey("QModelCustomization", blank=False, related_name="property_customizations")
    category = models.ForeignKey("QCategoryCustomization", blank=True, null=True, related_name="property_customizations")

    # ALL fields...
    property_title = models.CharField(max_length=LIL_STRING, blank=False, validators=[validate_no_profanities, ])
    is_required = models.BooleanField(default=True, blank=True, verbose_name="Is this property required?")
    is_required.help_text = _(
        "All required properties must be completed prior to publication.  "
        "A property that is defined as required <em>in the CIM or a CV</em> cannot be made optional."
    )
    is_hidden = models.BooleanField(default=True, blank=True, verbose_name="Should this property <u>not</u> be displayed?")
    is_hidden.help_text = _(
        "A property that is defined as required in an ontology cannot be hidden."
    )
    is_editable = models.BooleanField(default=True, verbose_name="Can this property be edited?")
    is_nillable = models.BooleanField(default=True, verbose_name="Should <i>nillable</i> options be allowed?")
    is_nillable.help_text = \
        "A nillable property can be intentionally left blank for several reasons: {0}.".format(
            ", ".join([nr[0] for nr in NIL_REASONS])
        )
    documentation = models.TextField(
        blank=True,
        null=True,
        verbose_name=_(
            "What is the help text to associate with this property?"
            "<div class='documentation'>Any initial help text comes from the CIM Schema or a CIM Controlled Vocabulary.</div>"
            "<div class='documentation'>Note that basic HTML tags are supported.</div>"
        )
    )
    inline_help = models.BooleanField(default=False, blank=True, verbose_name="Should the help text be displayed inline?")
    order = models.PositiveIntegerField(blank=True, null=True)
    field_type = models.CharField(max_length=BIG_STRING, blank=False, choices=[(ft.get_type(), ft.get_name()) for ft in QPropertyTypes])

    # ATOMIC fields...
    atomic_default = models.CharField(
        max_length=BIG_STRING,
        blank=True,
        null=True,
        verbose_name=_(
            "What is the default value of this property?"
            "<div class='documentation'>Note that this only applies to new and not existing documents</div>"
        )
    )
    atomic_type = models.CharField(
        max_length=BIG_STRING,
        blank=False,
        verbose_name="How should this field be rendered?",
        choices=[(ft.get_type(), ft.get_name()) for ft in QAtomicPropertyTypes],
        default=QAtomicPropertyTypes.DEFAULT.get_type(),
        help_text = "By default, all fields are rendered as strings.  However, a field can be customized to accept longer snippets of text, dates, email addresses, etc.",
    )
    atomic_suggestions = models.TextField(
        blank=True,
        null=True,
        validators=[validate_no_bad_suggestion_chars],
        verbose_name="Are there any suggestions you would like to offer as auto-completion options?",
        help_text="Please enter a \"|\" separated list of words or phrases.  (These suggestions will only take effect for text fields.)",
    )

    # ENUMERATION fields...
    enumeration_open = models.BooleanField(blank=False, default=False, verbose_name='Can a user can specify a custom "OTHER" value?')

    # RELATIONSHIP fields...
    relationship_show_subform = models.BooleanField(
        default=False,
        blank=True,
        verbose_name=_(
            "Should this property be rendered in its own subform?"
            "<div class='documentation'>Note that a relationship to another CIM Document cannot use subforms, while a relationship to anything else must use subforms.</div>"
        ),
        help_text=_(
            "Checking this will cause the property to be rendered as a nested subform within the parent form;"
            "All properties of this model will be available to view and edit in that subform."
            "Unchecking it will cause the attribute to be rendered as a <em>reference</em> widget."
        )
    )

    # using the reverse of the fk defined on model_customization instead of this field
    # (so that I can use a custom manager to cope w/ unsaved instances)
    # relationship_target_model_customizations = models.ManyToManyField("QModelCustomization", blank=True, related_name="+")

    def __str__(self):
        return pretty_string(self.proxy.name)

    def get_fully_qualified_key(self, prefix=None):
        fully_qualified_key = "{0}.{1}".format(self.proxy.get_fully_qualified_key(), self.guid)
        if prefix:
            return "{0}.{1}".format(prefix, fully_qualified_key)
        return fully_qualified_key

    def reset(self):

        proxy = self.proxy

        self.field_type = proxy.field_type

        # ALL field types...
        self.property_title = pretty_string(proxy.name)
        self.order = proxy.order
        self.is_required = proxy.is_required()
        self.is_hidden = False
        self.is_editable = True
        self.is_nillable = not proxy.is_required()
        self.documentation = proxy.documentation
        self.inline_help = False

        assert self.category is not None  # even "uncategorized" properties should use the "UncategorizedCategory"

        # ATOMIC fields...
        if self.field_type == QPropertyTypes.ATOMIC:
            self.atomic_default = proxy.atomic_default
            self.atomic_type = proxy.atomic_type
            self.atomic_suggestions = ""

        # ENUMERATION fields...
        elif self.field_type == QPropertyTypes.ENUMERATION:
            self.enumeration_open = proxy.enumeration_open
            # TODO: DO I NEED TO DEAL W/ "enumeration_choices" OR "enumeration_default" ?

        # RELATIONSHIP fields...
        else:  # self.field_type == QPropertyTypes.RELATIONSHIP:
            self.relationship_show_subform = not self.use_references()

    def set_name(self, new_name):
        # used w/ "recurse_through_customization" in global fn "set_name" above
        self.name = new_name

    def use_references(self):
        """
        As of v0.14 all RELATIONSHIPS to a CIM Document _must_ use a reference
        :return: Boolean
        """
        if self.field_type == QPropertyTypes.RELATIONSHIP:
            target_models_are_documents = [tm.is_document() for tm in self.proxy.relationship_target_models.all()]
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
            target_models_are_documents = [tm.is_document() for tm in self.proxy.relationship_target_models.all()]
            # double-check that all targets are the same type of class...
            assert len(set(target_models_are_documents)) == 1
            return not any(target_models_are_documents)
        return False
