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
from django.utils.translation import ugettext_lazy as _

from collections import OrderedDict
from uuid import uuid4

from Q.questionnaire import APP_LABEL, q_logger
from Q.questionnaire.q_fields import QPropertyTypes, QAtomicPropertyTypes, allow_unsaved_fk, QUnsavedRelatedManager
from Q.questionnaire.q_utils import validate_no_bad_chars, validate_no_spaces, validate_no_reserved_words, validate_no_profanities, pretty_string, find_in_sequence, serialize_model_to_dict, QError
from Q.questionnaire.q_constants import *

# ** ########################################### ** #
# ** THESE CLASSES ARE JUST FOR TESTING PURPOSES ** #
# ** ########################################### ** #

###############
# global vars #
###############


##############
# global fns #
##############

def get_new_customizations(model_proxy_key, customizations, project=None, ontology=None, model_proxy=None, **kwargs):

    if model_proxy_key not in customizations:
        model_customization = QModelThing(
            project=project,
            ontology=ontology,
            proxy=model_proxy,
        )
        model_customization.reset()
        customizations[model_proxy_key] = model_customization
    else:
        model_customization = customizations[model_proxy_key]

    property_customizations = []
    for property_proxy in model_proxy.property_proxies.all():
        property_proxy_key = "{0}.{1}".format(model_proxy_key, property_proxy.name)
        with allow_unsaved_fk(QPropertyThing, ["model_customization"]):
            # close this context manager before using the custom related manager
            # (too much hackery at once)
            if property_proxy_key not in customizations:
                property_customization = QPropertyThing(
                    proxy=property_proxy,
                    model_customization=model_customization,
                )
                property_customization.reset()
                customizations[property_proxy_key] = property_customization
            else:
                property_customization = customizations[property_proxy_key]
        property_customizations.append(property_customization)

        if property_customization.use_subforms():
            subform_key = "{0}.{1}".format(model_proxy.name, property_proxy.name)  # this property in this model (only 1 level deep)
            target_model_customizations = []
            for target_model_proxy in property_proxy.relationship_target_models.all():
                target_model_proxy_key = "{0}.{1}".format(subform_key, target_model_proxy.name)
                if target_model_proxy_key not in customizations:
                    target_model_customization = get_new_customizations(
                        target_model_proxy_key,
                        customizations,
                        project=project,
                        ontology=ontology,
                        model_proxy=target_model_proxy,
                    )
                else:
                    target_model_customization = customizations[target_model_proxy_key]
                target_model_customizations.append(target_model_customization)
            property_customization.relationship_target_model_customizations(manager="allow_unsaved_relationship_source_property_customization_related_manager").add_potentially_unsaved(*target_model_customizations)

        # TODO: BOTH OF THESES LINES DO THE SAME THING
        # TODO: BUT I DON'T UNDERSTAND WHY JUST USING THE FIELD W/OUT SPECIFYING THE MANAGER USES MY CUSTOM MANAGER ?!?
        # model_customization.property_customizations.all()
        # model_customization.property_customizations(manager="allow_unsaved_related_model_customization_manager").all()
        model_customization.property_customizations(manager="allow_unsaved_model_customization_related_manager").add_potentially_unsaved(*property_customizations)

    return customizations[model_proxy_key]


#############
# constants #
#############

# these fields are all handled behind-the-scenes
# there is no point passing them around to serializers or forms
QCUSTOMIZATION_NON_EDITABLE_FIELDS = ["guid", "created", "modified", ]

##############
# base class #
##############

class QThing(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = True
        verbose_name = "_Questionnaire Thing (testing only)"
        verbose_name_plural = "_Questionnaire Things (testing only)"

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
    )

    def get_key(self):
        # convert UUID to str b/c UUID does not play nicely w/ JSON
        return str(self.guid)

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

    def is_existing(self):
        return self.pk is not None

    def is_new(self):
        return self.pk is None

    def reset(self):
        msg = "{0} must define a custom 'reset' method.".format(self.__class__.__name__)
        raise NotImplementedError(msg)



class QUnsavedModelCustomizationRelatedManager(QUnsavedRelatedManager):

    def get_unsaved_related_field_name(self):
        field = QPropertyThing.get_field("model_customization")
        return "_unsaved_{0}".format(field.related.name)

class QUnsavedRelationshipSourcePropertyCustomizationManager(QUnsavedRelatedManager):

    def get_unsaved_related_field_name(self):
        field = QModelThing.get_field("relationship_source_property_customization")
        return "_unsaved_{0}".format(field.related.name)

###############
# model thing #
###############

class QModelThing(QThing):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "_Questionnaire Model Thing (testing only)"
        verbose_name_plural = "_Questionnaire Model Things (testing only)"

    allow_unsaved_relationship_source_property_customization_related_manager = QUnsavedRelationshipSourcePropertyCustomizationManager()

    project = models.ForeignKey("QProject", blank=False, related_name="model_things")
    ontology = models.ForeignKey("QOntology", blank=False, null=False)
    proxy = models.ForeignKey("QModelProxy", blank=False, null=False)

    model_title = models.CharField(
        max_length=BIG_STRING,
        blank=False, null=True
    )

    # this fk is just here to provide the other side of the relationship to property_customization
    # I only ever access "property_thing.relationship_target_model_customizations"
    relationship_source_property_customization = models.ForeignKey("QPropertyThing", blank=True, null=True, related_name="relationship_target_model_customizations")

    def __str__(self):
        return pretty_string(self.name)

    def get_fully_qualified_key(self, prefix=None):
        fully_qualified_key = "{0}.{1}".format(self.proxy.get_fully_qualified_key(), self.guid)
        if prefix:
            return "{0}.{1}".format(prefix, fully_qualified_key)
        return fully_qualified_key

    def reset(self):
        proxy = self.proxy
        self.model_title = pretty_string(proxy.name)

    def save(self, *args, **kwargs):
        # force all (custom) "clean" methods to run
        self.full_clean()
        super(QThing, self).save(*args, **kwargs)

###########################
# property customizations #
###########################

class QPropertyThing(QThing):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "_Questionnaire Property Thing (testing only)"
        verbose_name_plural = "_Questionnaire Property Thing (testing only)"

    allow_unsaved_model_customization_related_manager = QUnsavedModelCustomizationRelatedManager()

    proxy = models.ForeignKey("QPropertyProxy", blank=False, null=False)

    model_customization = models.ForeignKey("QModelThing", blank=False, related_name="property_customizations")

    property_title = models.CharField(max_length=LIL_STRING, blank=False, validators=[validate_no_profanities, ])

    # ALL fields...
    field_type = models.CharField(max_length=BIG_STRING, blank=False, choices=[(ft.get_type(), ft.get_name()) for ft in QPropertyTypes])

    # ATOMIC fields...
    pass

    # ENUMERATION fields...
    pass

    # RELATIONSHIP fields...
    relationship_show_subform = models.BooleanField(
        default=False,
        blank=True,
    )

# using the reverse of the fk defined on model_customization for this
# so that I can use a custom manager
# to cope w/ unsaved instances in m2m fields
#    relationship_target_model_customizations = models.ManyToManyField("QModelThing", blank=True, related_name="+")

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

        # ATOMIC fields...
        if self.field_type == QPropertyTypes.ATOMIC:
            pass

        # ENUMERATION fields...
        elif self.field_type == QPropertyTypes.ENUMERATION:
            pass

        # RELATIONSHIP fields...
        else:  # self.field_type == QPropertyTypes.RELATIONSHIP:
            self.relationship_show_subform = not self.use_references()

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
