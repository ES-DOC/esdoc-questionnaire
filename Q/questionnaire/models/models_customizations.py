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
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from uuid import uuid4, UUID as generate_uuid

from collections import OrderedDict

from Q.questionnaire import APP_LABEL
from Q.questionnaire.q_constants import *
from Q.questionnaire.models.models_proxies import SCIENTIFIC_PROPERTY_CHOICES
from Q.questionnaire.q_fields import QPropertyTypes, QAtomicPropertyTypes, QCardinalityField, QEnumerationField, allow_unsaved_fk, MPTT_FIELDS
from Q.questionnaire.q_utils import validate_no_bad_chars, validate_no_spaces, validate_no_reserved_words, validate_no_profanities, pretty_string, find_in_sequence, serialize_model_to_dict, BAD_CHARS_LIST, QError


##############
# global fns #
##############

def get_new_customization_set(project=None, ontology=None, proxy=None, vocabularies=[]):
    """

    """

    model_customization = QModelCustomization(
        ontology=ontology,
        proxy=proxy,
        project=project,
    )
    model_customization.reset(proxy)

    vocabulary_customizations = []
    for i, vocabulary in enumerate(vocabularies):
        with allow_unsaved_fk(QModelCustomizationVocabulary, ['model_customization', ]):
            vocabulary_customization = QModelCustomizationVocabulary(
                model_customization=model_customization,
                vocabulary=vocabulary,
                order=i+1,
                active=True,
            )
        vocabulary_customizations.append(vocabulary_customization)

    standard_category_customizations = []
    for standard_category_proxy in ontology.categorization.category_proxies.all():
        with allow_unsaved_fk(QStandardCategoryCustomization, ['model_customization', ]):
            standard_category_customization = QStandardCategoryCustomization(
                model_customization=model_customization,
                proxy=standard_category_proxy,
            )
            standard_category_customization.reset(standard_category_proxy)
        standard_category_customizations.append(standard_category_customization)

    standard_property_customizations = []
    for standard_property_proxy in proxy.standard_properties.all():
        with allow_unsaved_fk(QStandardPropertyCustomization, ["model_customization", "category", "relationship_subform_customization", ]):
            standard_property_customization = QStandardPropertyCustomization(
                model_customization=model_customization,
                proxy=standard_property_proxy,
                category=find_in_sequence(
                    lambda category: category.proxy.has_property(standard_property_proxy),
                    standard_category_customizations
                ),
            )
            standard_property_customization.reset(standard_property_proxy)
            # HERE BEGINS THE SUBFORM BIT
            if standard_property_customization.use_subform():
                subform_customization_set = get_new_customization_set(
                    project=project,
                    ontology=ontology,
                    proxy=standard_property_proxy.relationship_target_model,
                    vocabularies=[],  # NO VOCABULARIES USED IN SUBFORMS ?
                )
                standard_property_customization.relationship_subform_customization = subform_customization_set["model_customization"]
                # this is important; I do not have access to unsaved m2m fields, but I can set an attribute on the instance
                standard_property_customization.relationship_subform_customization_set = subform_customization_set
            # HERE ENDS THE SUBFORM BIT
        standard_property_customizations.append(standard_property_customization)

    scientific_category_customizations = []
    scientific_property_customizations = []
    for vocabulary in vocabularies:
        vocabulary_key = vocabulary.get_key()
        for component in vocabulary.component_proxies.all():
            component_key = component.get_key()
            n_categories = len(scientific_category_customizations)
            for scientific_category_proxy in component.category_proxies.all():
                with allow_unsaved_fk(QScientificCategoryCustomization, ["model_customization", ]):
                    scientific_category_customization = QScientificCategoryCustomization(
                        model_customization=model_customization,
                        proxy=scientific_category_proxy,
                        vocabulary_key=vocabulary_key,
                        component_key=component_key
                    )
                    scientific_category_customization.reset(scientific_category_proxy, reset_keys=False)
                scientific_category_customizations.append(scientific_category_customization)
            n_properties = len(scientific_property_customizations)
            for scientific_property_proxy in component.scientific_property_proxies.all():
                with allow_unsaved_fk(QScientificPropertyCustomization, ["category", "model_customization", ]):
                    scientific_property_customization = QScientificPropertyCustomization(
                        model_customization=model_customization,
                        proxy=scientific_property_proxy,
                        vocabulary_key=vocabulary_key,
                        component_key=component_key,
                        category=find_in_sequence(
                            lambda category: category.proxy.has_property(scientific_property_proxy),
                            scientific_category_customizations[n_categories:]  # ignore categories from previous components
                        ),
                    )
                    scientific_property_customization.reset(scientific_property_proxy, reset_keys=False)
                scientific_property_customizations.append(scientific_property_customization)

    customization_set = {
        "model_customization": model_customization,
        "vocabulary_customizations": vocabulary_customizations,
        "standard_category_customizations": standard_category_customizations,
        "standard_property_customizations": standard_property_customizations,
        "scientific_category_customizations": scientific_category_customizations,
        "scientific_property_customizations": scientific_property_customizations,
    }

    return customization_set


def get_existing_customization_set(project=None, ontology=None, proxy=None, customization_name="", customization_id=None):
    """

    """

    # this will throw a "QModelCustomization.DoesNotExist" error if the name is wrong;
    # it is up to the calling method to catch that and do something sensible
    if not customization_id:
        model_customization = QModelCustomization.objects.get(
            ontology=ontology,
            proxy=proxy,
            project=project,
            name__iexact=customization_name,
        )
    else:
        model_customization = QModelCustomization.objects.get(pk=customization_id)
        assert model_customization.ontology == ontology
        assert model_customization.proxy == proxy
        assert model_customization.project == project
        if customization_name:
            assert model_customization.name.lower() == customization_name.lower()

    vocabulary_customizations = model_customization.get_vocabularies_through()  # this gets the "through" model instead of just QVocabulary instances

    # TODO: I CAN PROBABLY REMOVE ALL THE "order_by" BITS POST v0.15
    standard_category_customizations = model_customization.standard_category_customizations.all().order_by("proxy")

    standard_property_customizations = model_customization.standard_properties.all().order_by("proxy")

    # HERE BEGINS THE SUBFORM BIT
    for standard_property_customization in standard_property_customizations:
        if standard_property_customization.use_subform():
            subform_customization = standard_property_customization.relationship_subform_customization
            subform_customization_set = get_existing_customization_set(
                project=project,
                ontology=ontology,
                proxy=subform_customization.proxy,
                customization_name=customization_name,
                customization_id=subform_customization.pk,
            )
            # this is important; I do not have access to the entire set from the model fields, but I can set an attribute on the instance
            standard_property_customization.relationship_subform_customization_set = subform_customization_set
    # HERE ENDS THE SUBFORM BIT

    scientific_category_customizations = model_customization.scientific_category_customizations.all().order_by("proxy")

    scientific_property_customizations = model_customization.scientific_properties.all().order_by("proxy")

    customization_set = {
        "model_customization": model_customization,
        "vocabulary_customizations": vocabulary_customizations,
        "standard_category_customizations": standard_category_customizations,
        "standard_property_customizations": standard_property_customizations,
        "scientific_category_customizations": scientific_category_customizations,
        "scientific_property_customizations": scientific_property_customizations,
    }

    return customization_set


def get_related_model_customizations(customization_set):
    """
    gets all subform customizations that are part of this set
    (if this is called w/ unsaved instances, then I have to recurse through sets)
    (otherwise, it's straightforward to access the db via querysets)
    :param customization_set:
    :return:
    """
    model_customization = customization_set["model_customization"]
    if not model_customization.pk:
        standard_property_customizations = customization_set["standard_property_customizations"]
        related_model_customizations = get_related_model_customizations_recurse(standard_property_customizations)
    else:
        related_model_customizations = list(QModelCustomization.objects.filter(project=model_customization.project, name=model_customization.name))
    return related_model_customizations


def get_related_model_customizations_recurse(properties, related_model_customizations=[]):
    for property in properties:
        if property.relationship_show_subform:
            subform_customization_set = property.relationship_subform_customization_set
            related_model_customizations.append(subform_customization_set["model_customization"])
            related_model_customizations = get_related_model_customizations_recurse(
                subform_customization_set["standard_property_customizations"],
                related_model_customizations
            )
    return related_model_customizations



def get_related_standard_property_customizations(customization_set):
    """
    :param customization_set:
    :return:
    """
    standard_property_customizations = customization_set["standard_property_customizations"]
    related_standard_property_customizations = get_related_standard_property_customizations_recurse(standard_property_customizations)
    return related_standard_property_customizations


def get_related_standard_property_customizations_recurse(properties, related_standard_property_customizations=[]):
    for property in properties:
        related_standard_property_customizations.append(property)
        if property.relationship_show_subform:
            subform_customization_set = property.relationship_subform_customization_set
            related_standard_property_customizations = get_related_standard_property_customizations_recurse(
                subform_customization_set["standard_property_customizations"],
                related_standard_property_customizations
            )
    return related_standard_property_customizations


def delete_customization_set(model_customization):

    assert model_customization.pk
    assert not model_customization.is_default

    related_model_customizations = QModelCustomization.objects.filter(project=model_customization.project, name=model_customization.name)
    for related_model_customization in related_model_customizations:
        # the "on_delete" argument ensures that all related standard/scientific categories/properties are deleted as well
        related_model_customization.delete()


def rename_customization_set(customization_set, new_name):
    # TODO: RIGHT NOW THIS FUNCTIONALITY IS HANDLED PURELY VIA THE CLIENT-SIDE
    # TODO: I THINK THAT'S CORRECT, BUT SERVER-SIDE FN STILL NEEDS TO BE TESTED
    # TODO: ACTUALLY, MAYBE I CAN EXPOSE THIS FN FROM THE "PROJECT" VIEW
    model_customization = customization_set["model_customization"]
    model_customization.name = new_name
    # if model_customization.pk:
    #     model_customization.save()
    related_model_customizations = get_related_model_customizations(customization_set)
    for related_model_customization in related_model_customizations:
        related_model_customization.name = new_name
        # if related_model_customization.pk:
        #     related_model_customization.save()


def serialize_customization_set(customization_set):
    """
    need a special fn to cope w/ this
    b/c it is likely that the customization_set will need to be serialized before it has been saved
    therefore the m2m fields will not yet exist in the db
    the workflow goes:
    * get_new_customization_set where calls to create are wrapped in "allow_unsaved_fk"
    * that customization_set gets cached in the current session
    * AJAX calls to the RESTful API access that cached customization_set
    * which needs to be serialized via this fn and then passed as data to QModelCustomizationSerializer
    * that fn uses my custom "serialize_model_to_dict" fn which correctly handles m2m fields
    :param model_customization:
    :return:
    """

    # get model customization stuff...
    serialization = OrderedDict(serialize_model_to_dict(
        customization_set["model_customization"],
        include={},
        exclude=QCUSTOMIZATION_NON_EDITABLE_FIELDS + ["synchronization", ]
    ))

    # add vocabulary customization stuff...
    serialization["vocabularies"] = [
        serialize_model_to_dict(
            vc,
            include={
                "display_detail": i == 0,  # by default, display the 1st vocabulary in the list
                "vocabulary_name": str(vc.vocabulary),
                "vocabulary_key": vc.vocabulary.get_key(),
                "components": [
                    serialize_model_to_dict(
                        component,
                        include={
                            "key": component.get_key(),
                            "num_properties": component.scientific_property_proxies.count(),
                        },
                        exclude=MPTT_FIELDS + QCUSTOMIZATION_NON_EDITABLE_FIELDS + ["id", "vocabulary", ],
                    )
                    for component in vc.vocabulary.component_proxies.all()
                ]
            },
            exclude=QCUSTOMIZATION_NON_EDITABLE_FIELDS
        )
        for i, vc in enumerate(customization_set["vocabulary_customizations"])
    ]

    # add standard categories...
    serialization["standard_categories"] = [
        serialize_model_to_dict(
            sc,
            include={
                "key": sc.get_key(),
                "display_properties": True,
                "display_detail": False,

            },
            exclude=QCUSTOMIZATION_NON_EDITABLE_FIELDS,
        )
        for sc in customization_set["standard_category_customizations"]
    ]

    # add standard properties...
    # (not using a list comprehension for standard_properties b/c of the complexities of subforms)
    serialization["standard_properties"] = []
    for sp in customization_set["standard_property_customizations"]:
        if sp.relationship_show_subform:
            # I am working w/ the full customization_set even though the field is only bound to the model_customization
            subform_serialization = serialize_customization_set(sp.relationship_subform_customization_set)
        else:
            subform_serialization = OrderedDict({})
        category = sp.category
        serialization["standard_properties"].append(
            serialize_model_to_dict(
                sp,
                include={
                    "key": sp.get_key(),
                    # not all properties of subforms are categorized
                    # (that's okay for now, since I don't display the category widget in subforms anyway)
                    "category_key": category.get_key() if category else None,
                    "display_detail": False,
                    "enumeration_choices": sp.get_enumeration_choices_value(),
                    "relationship_subform_customization": subform_serialization,
                },
                exclude=QCUSTOMIZATION_NON_EDITABLE_FIELDS,
            )
        )

    # add scientific categories...
    serialization["scientific_categories"] = [
        serialize_model_to_dict(
            sc,
            include={
                "key": sc.get_key(),
                "display_properties": True,
                "display_detail": False,
            },
            exclude=QCUSTOMIZATION_NON_EDITABLE_FIELDS,
        )
        for sc in customization_set["scientific_category_customizations"]
    ]

    # and scientific properties...
    serialization["scientific_properties"] = [
        serialize_model_to_dict(
            sp,
            include={
                "key": sp.get_key(),
                "category_key": sp.category.get_key(),
                "display_detail": False,
            },
            exclude=QCUSTOMIZATION_NON_EDITABLE_FIELDS,
        )
        for sp in customization_set["scientific_property_customizations"]
    ]

    return serialization

######################
# the actual classes #
######################

# these fields are all handled behind-the-scenes
# there is no point passing them around to serializers or forms
QCUSTOMIZATION_NON_EDITABLE_FIELDS = ["guid", "created", "modified", ]


# an artifact of the old Metafor mindmap to XML process is that it always adds
# "other" and "N/A" as potential choices for every (non-boolean) property enumeration.
# the ES-DOC Questionnaire has its own method for customizing if a property should include "OTHER" or "NONE"
# so I make sure to remove those unused choices; odds are the user will almost never want to use them
# and if they do, they can always manually add them back in.
# I do this both in setting up the customization (QScientificPropertyCustomization.reset)
# and the form (QScientificPropertyCustomizationForm.__init__)
QCUSTOMIZATION_UNUSED_SCIENTIFIC_PROPERTY_ENUMERATION_CHOICES = ["other", "N/A", ]


class QCustomization(models.Model):

    class Meta:
        app_label = APP_LABEL
        abstract = True
        ordering = ["created", ]

    guid = models.UUIDField(default=uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now_add=True, editable=False)

    def __unicode__(self):
        return u"%s" % self.name

    def save(self, *args, **kwargs):
        self.modified = timezone.now()
        super(QCustomization, self).save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super(QCustomization, self).__init__(*args, **kwargs)

        # no longer doing this automatically
        # now doing it explicitly in get_new_customization_set above
        # (the problem was that rest_framework would create objects and _then_ assign a pk)
        # if not self.pk:
        #     try:
        #         self.reset(self.proxy)
        #     except ObjectDoesNotExist:
        #         # if you are building a customization via the admin
        #         # then the proxy will not be set until after saving
        #         # that's okay
        #         pass

    def reset(self, proxy):
        msg = "{0} must define a custom 'reset' method.".format(self.__class__.__name__)
        raise NotImplementedError(msg)

    def get_field(self, field_name):
        """
        convenience fn for getting the Django Field instance from a model
        """
        try:
            field = self._meta.get_field_by_name(field_name)
            return field[0]
        except FieldDoesNotExist:
            return None

    @classmethod
    def get_field(cls, field_name):
        """
        convenience fn for getting the Django Field instance from a model class
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

    def get_key(self):
        # convert UUID to str b/c UUID does not play nicely w/ JSON
        return str(self.guid)


class QModelCustomizationQuerySet(models.QuerySet):
    """
    As of Django 1.7 I can use custom querysets as managers
    to ensure that these custom methods are chainable
    whoo-hoo
    """

    def documents(self):
        return self.filter(proxy__stereotype__iexact="document")

class QModelCustomization(QCustomization):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "Questionnaire Model Customization"
        verbose_name_plural = "_Questionnaire Customizations: Models"
        # I CANNOT ENFORCE THIS HERE B/C "standard_property.relationship_subform_customization" COULD POTENTIALLY POINT TO THE SAME PROJECT/PROXY/PROJECT COMBINATION
        # INSTEAD I HAVE MODIFIED THE "clean" FN BELOW
        # TODO: WHY DIDN'T THIS ISSUE ARISE PRE V0.15 ?
        # unique_together = ("project", "proxy", "name", )

    objects = QModelCustomizationQuerySet.as_manager()

    ontology = models.ForeignKey("QOntology", blank=False, related_name="model_customizations")
    proxy = models.ForeignKey("QModelProxy", blank=False, related_name="model_customizations")
    project = models.ForeignKey("QProject", blank=False, related_name="model_customizations")

    name = models.CharField(max_length=LIL_STRING, blank=False, verbose_name="Customization Name", validators=[validate_no_bad_chars, validate_no_spaces, validate_no_reserved_words, validate_no_profanities])
    name.help_text = "A unique name for this customization.  Spaces or the following characters are not allowed: \"%s\"." % BAD_CHARS_LIST
    description = models.TextField(blank=True, verbose_name="Customization Description")
    description.help_text = "An explanation of how this customization is intended to be used. This information is for informational purposes only."
    is_default = models.BooleanField(blank=False, null=False, default=False, verbose_name="Is Default Customization?")
    is_default.help_text = "Every CIM Document Type must have one default customization. If this is the first customization you are creating, please ensure this checkbox is selected."

    vocabularies = models.ManyToManyField(
        "QVocabulary",
        blank=True,
        through="QModelCustomizationVocabulary",  # note my use of the "through" model
        related_name="model_customizer",
        verbose_name="Vocabularies to include",
        help_text=_(
            "<p>These are the CVs that are associated with this document type and project.</p>"
            "<p>Clicking on <strong>&quot;active&quot;</strong> will enable or disable all of the properties contained within a CV.</p>"
            "<p>Dragging-and-dropping a CV will change the order in which it appears in the Editor.</p>"
        )

    )

    model_title = models.CharField(max_length=BIG_STRING, verbose_name="Name that should appear on the Document Form", blank=False, null=True)
    model_description = models.TextField(verbose_name="A description of the document", blank=True, null=True)
    model_description.help_text = "This text will appear as documentation in the editing form.  Inline HTML formatting is permitted.  The initial documentation comes from the ontology."
    model_show_all_categories = models.BooleanField(verbose_name="Display empty categories?", default=False)
    model_show_all_categories.help_text = "Include categories in the editing form for which there are no (visible) properties associated with"
    model_show_hierarchy = models.BooleanField(verbose_name="Nest the full document hierarchy within a root document?", default=True)
    model_show_hierarchy.help_text = "A CIM Document that uses 1 or 0 CVs does not need a root component acting as a <i>parent</i> of all components."
    model_hierarchy_name = models.CharField(max_length=LIL_STRING, verbose_name="Title of the document hierarchy tree", default="Component Hierarchy", blank=False)
    model_hierarchy_name.help_text = "What should the title be for the widget that navigates the document hierarchy?"
    model_root_component = models.CharField(max_length=LIL_STRING, verbose_name="Name of the root component", blank=True, validators=[validate_no_spaces], default="RootComponent")

    synchronization = models.ManyToManyField("QSynchronization", blank=True)

    def is_synchronized(self):
        unsynchronized_types = self.synchronization.all()
        return not unsynchronized_types  # checks if qs is empty

    def is_unsynchronized(self):
        return not self.is_synchronized()

    def reset(self, proxy):

        self.proxy = proxy

        self.model_title = pretty_string(proxy.name)
        self.model_description = proxy.documentation
        self.model_show_all_categories = self.get_field("model_show_all_categories").default
        self.model_show_hierarchy = self.get_field("model_show_hierarchy").default
        self.model_hierarchy_name = self.get_field("model_hierarchy_name").default
        self.model_root_component = self.get_field("model_root_component").default

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

    def save(self, *args, **kwargs):
        # force all (custom) "clean" methods to run
        self.full_clean()

        super(QModelCustomization, self).save(*args, **kwargs)

    def get_vocabularies(self):
        # using related_name in the order_by fn as per http://stackoverflow.com/questions/3893955/django-manytomanyfield-ordering-using-through
        # (this means follow the reverse relationship from vocabulary back to QModelCustomizationVocabulary, and use that ordering)
        return self.vocabularies.all().order_by("link_to_vocabulary")

    def get_active_vocabularies(self):
        return self.vocabularies.filter(link_to_vocabulary__active=True).order_by("link_to_vocabulary")

    def get_vocabularies_through(self):
        """
        returns the through model instead of QVocabulary instances
        :return:
        """
        return self.link_to_model_customization.all()

    ###########################################
    # some fns which are called from handlers #
    ###########################################

    def update_vocabulary_order(self):
        """
        run when a MetadataModelCustomizerVocabulary is added/removed;
        this can happen when a MetadataVocabulary is added/removed from a MetadataProject;
        re-orders the model_customizer_vocabularies as needed
        :return:
        """
        for i, vocabulary in enumerate(self.get_vocabularies_through()):
            if vocabulary.order != i+1:
                vocabulary.order = i+1
                vocabulary.save()

    def updated_vocabulary(self, model_customization_vocabulary):
        # just a placeholder, nothing to do yet
        # (this gets called when adding a vocabulary to a project)
        # (but there is also a signal when adding a vocabulary to a customization)
        # (which calls the above "update_vocabulary_order" fn)
        # (so this is sort of redundant)
        pass

    def updated_ontology(self):

        standard_property_customizers = list(self.standard_property_customizers.all())  # the list fn forces immediate qs evaluation
        for standard_property_customizer in standard_property_customizers:

            if standard_property_customizer.field_type == QPropertyTypes.RELATIONSHIP:
                # recurse through subforms...
                target_model_customizer = standard_property_customizer.target_model_customizer
                if target_model_customizer:
                    target_model_customizer.updated_ontology()

            standard_property_proxy = standard_property_customizer.proxy
            # TODO: DOUBLE-CHECK _ALL_ THE WAYS THAT THE ONTOLOGY COULD HAVE BEEN CHANGED
            if standard_property_proxy.required and not standard_property_customizer.required:
                standard_property_customizer.required = True
                standard_property_customizer.save()


class QCategoryCustomizationQuerySet(models.QuerySet):
    """
    As of Django 1.7 I can use custom querysets as managers
    to ensure that these custom methods are chainable
    whoo-hoo
    """

    def get_by_key(self, key):
        if isinstance(key, basestring):
            key = generate_uuid(key)
        return self.get(guid=key)
        # try:
        #     return self.get(guid=key)
        # except ObjectDoesNotExist:
        #     return None

class QCategoryCustomization(QCustomization):

    class Meta:
        app_label = APP_LABEL
        abstract = True

    objects = QCategoryCustomizationQuerySet.as_manager()

    name = models.CharField(blank=False, max_length=SMALL_STRING)
    name.help_text = "Be wary of changing a category's name; doing so deviates from a known controlled vocabulary and could confuse users."
    description = models.TextField(blank=True, null=True, verbose_name="Category Description")
    order = models.PositiveIntegerField(blank=True, null=True)

    def get_key(self):
        # convert UUID to str b/c UUID does not play nicely w/ JSON
        return str(self.guid)

class QStandardCategoryCustomization(QCategoryCustomization):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        ordering = ["order", ]
        verbose_name = "Questionnaire Standard Category Customization"
        verbose_name_plural = "_Questionnaire Customizations: Standard Categories"

    model_customization = models.ForeignKey("QModelCustomization", related_name="standard_category_customizations")
    proxy = models.ForeignKey("QStandardCategoryProxy")

    def reset(self, proxy):

        self.proxy = proxy

        self.name = proxy.name
        self.description = proxy.documentation
        self.order = proxy.order


class QScientificCategoryCustomization(QCategoryCustomization):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        ordering = ["order", ]
        verbose_name = "Questionnaire Scientific Category Customization"
        verbose_name_plural = "_Questionnaire Customizations: Scientific Categories"

    model_customization = models.ForeignKey("QModelCustomization", related_name="scientific_category_customizations")
    proxy = models.ForeignKey("QScientificCategoryProxy")

    vocabulary_key = models.UUIDField()
    component_key = models.UUIDField()

    def get_vocabulary_key(self):
        # convert UUID to str b/c UUID does not play nicely w/ JSON
        return str(self.vocabulary_key)

    def get_component_key(self):
        # convert UUID to str b/c UUID does not play nicely w/ JSON
        return str(self.component_key)

    def reset(self, proxy, reset_keys=True):

        self.proxy = proxy

        self.name = proxy.name
        self.description = proxy.documentation
        self.order = proxy.order

        if reset_keys:
            # there is no need to _always_ do this,
            # b/c in get_new_customization_set I have already passed these values in as strings
            # (which is faster than these fk lookups)
            component = proxy.component_proxy
            vocabulary = component.vocabulary
            self.component_key = component.guid
            self.vocabulary_key = vocabulary.guid


class QPropertyCustomization(QCustomization):

    class Meta:
        app_label = APP_LABEL
        abstract = True

    name = models.CharField(max_length=SMALL_STRING, blank=False)
    order = models.PositiveIntegerField(blank=True, null=True)

    cardinality = QCardinalityField(blank=False)
    field_type = models.CharField(
        max_length=SMALL_STRING,
        blank=False,
        null=True,
        choices=[(ft.get_type(), ft.get_name()) for ft in QPropertyTypes],
    )

    # ways to customize _any_ field...
    displayed = models.BooleanField(default=True, blank=True, verbose_name="Should this property be displayed?")
    displayed.help_text = _(
        "A property that is defined as required <em>in the CIM or a CV</em> must be displayed."
    )
    required = models.BooleanField(default=True, blank=True, verbose_name="Is this property required?")
    required.help_text = _(
        "All required properties must be completed prior to publication.  "
        "A property that is defined as required <em>in the CIM or a CV</em> cannot be made optional."
    )
    editable = models.BooleanField(default=True, blank=True, verbose_name="Can the value of this property be edited?")
    unique = models.BooleanField(default=False, blank=True, verbose_name="Must the value of this property be unique?")
    verbose_name = models.CharField(max_length=LIL_STRING, blank=False, verbose_name="How should this property be labeled (overrides default name)?")

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

    def get_key(self):
        # convert UUID to str b/c UUID does not play nicely w/ JSON
        return str(self.guid)

class QStandardPropertyCustomization(QPropertyCustomization):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "Questionnaire Standard Property Customization"
        verbose_name_plural = "_Questionnaire Customizations: Standard Properties"
        ordering = ["order"]

    model_customization = models.ForeignKey("QModelCustomization", blank=False, related_name="standard_properties", on_delete=models.CASCADE)
    proxy = models.ForeignKey("QStandardPropertyProxy", blank=False)
    category = models.ForeignKey("QStandardCategoryCustomization", blank=True, null=True, on_delete=models.SET_NULL, related_name="standard_properties")

    inherited = models.BooleanField(default=False, blank=True, verbose_name="Can this property be inherited by children?")
    inherited.help_text = "Enabling inheritance will allow the corresponding properties of child components to 'inherit' the value of this property.  The editing form will allow users the ability to 'opt-out' of this inheritance."

    # ways to customize an atomic field...
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
    )
    atomic_type.help_text = "By default, all fields are rendered as strings.  However, a field can be customized to accept longer snippets of text, dates, email addresses, etc."
    atomic_suggestions = models.TextField(blank=True, null=True, verbose_name="Are there any suggestions you would like to offer as auto-completion options?")
    atomic_suggestions.help_text = "Please enter a \"|\" separated list of words or phrases.  (These suggestions will only take effect for text fields.)"

    # enumeration fields...
    enumeration_choices = QEnumerationField(blank=True, null=True, verbose_name="Choose the property values that should be presented to users.")
    enumeration_default = QEnumerationField(blank=True, null=True, verbose_name="Choose the default value(s), if any, for this property.")
    enumeration_open = models.BooleanField(default=False, verbose_name="Check if a user can specify a custom property value.")
    enumeration_multi = models.BooleanField(default=False, verbose_name="Check if a user can specify multiple property values.")
    enumeration_nullable = models.BooleanField(default=False, verbose_name="Check if a user can specify an explicit <em>NONE</em> value.")

    # relationship fields...
    relationship_show_subform = models.BooleanField(
        default=False,
        blank=True,
        verbose_name=_(
            "Should this property be rendered in its own subform?"
            "<div class='documentation'>Note that a relationship to another CIM Document cannot use subforms, while a relationship to anything else must use subforms.</div>"
        )
    )
    relationship_show_subform.help_text = "Checking this will cause the property to be rendered as a nested subform within the parent form; All properties of this model will be available to view and edit in that subform.\
                                          Unchecking it will cause the attribute to be rendered as a simple <em>reference</em> widget."
    relationship_subform_customization = models.ForeignKey("QModelCustomization", blank=True, null=True, related_name="property_customizer")

    def reset(self, proxy):

        self.proxy = proxy

        self.name = proxy.name
        self.order = proxy.order
        self.cardinality = proxy.cardinality
        self.field_type = proxy.field_type

        # any field...
        self.displayed = True
        self.required = proxy.is_required()
        self.editable = True
        self.unique = False
        self.verbose_name = pretty_string(proxy.name)
        self.documentation = proxy.documentation
        self.inline_help = False

        self.inherited = False

        # atomic fields...
        if self.field_type == QPropertyTypes.ATOMIC:
            self.atomic_default = proxy.atomic_default
            self.atomic_type = proxy.atomic_type
            self.atomic_suggestions = ""

        # enumeration fields...
        elif self.field_type == QPropertyTypes.ENUMERATION:
            self.enumeration_choices = proxy.enumeration_choices
            self.enumeration_default = ""
            self.enumeration_open = proxy.enumeration_open
            self.enumeration_multi = proxy.enumeration_multi
            self.enumeration_nullable = proxy.enumeration_nullable

        # relationship fields...
        else:  # self.field_type == QPropertyTypes.RELATIONSHIP:
            self.relationship_show_subform = not self.use_reference()

    def use_reference(self):
        """
        As of v0.14 all RELATIONSHIPS to a CIM Document _must_ use a reference
        :return: Boolean
        """
        if self.field_type == QPropertyTypes.RELATIONSHIP:
            return self.proxy.relationship_target_model.is_document()
        return False

    def use_subform(self):
        """
        As of v0.14 all RELATIONSHIPS to a CIM Entity (non-Document) _must_ use a subform
        :return: Boolean
        """
        if self.field_type == QPropertyTypes.RELATIONSHIP:
            return not self.proxy.relationship_target_model.is_document()
        return False

    # TODO: REWRITE (OR REMOVE) THIS FN POST v0.15
    def render_as_formset(self):
        if self.use_subform():
            cardinality_max = self.get_cardinality_max()
            return cardinality_max == "*" or int(cardinality_max) > 1
        return False

class QScientificPropertyCustomization(QPropertyCustomization):

    class Meta:
        app_label = APP_LABEL
        abstract = False
        verbose_name = "Questionnaire Scientific Property Customization"
        verbose_name_plural = "_Questionnaire Customizations: Scientific Properties"
        ordering = ["order"]

    model_customization = models.ForeignKey("QModelCustomization", blank=False, related_name="scientific_properties", on_delete=models.CASCADE)
    proxy = models.ForeignKey("QScientificPropertyProxy", blank=False)
    category = models.ForeignKey("QScientificCategoryCustomization", blank=True, null=True, on_delete=models.SET_NULL, related_name="scientific_properties")

    vocabulary_key = models.UUIDField()
    component_key = models.UUIDField()

    choice = models.CharField(max_length=LIL_STRING, blank=True, null=True, choices=SCIENTIFIC_PROPERTY_CHOICES)

    display_extra_standard_name = models.BooleanField(null=False, blank=False, default=False)
    display_extra_description = models.BooleanField(null=False, blank=False, default=False)
    display_extra_units = models.BooleanField(null=False, blank=False, default=False)

    edit_extra_standard_name = models.BooleanField(null=False, blank=False, default=False)
    edit_extra_description = models.BooleanField(null=False, blank=False, default=False)
    edit_extra_units = models.BooleanField(null=False, blank=False, default=False)

    # ATOMIC fields
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
    )
    atomic_type.help_text = "By default, all fields are rendered as strings.  However, a field can be customized to accept longer snippets of text, dates, email addresses, etc."
    atomic_suggestions = models.TextField(blank=True, null=True, verbose_name="Are there any suggestions you would like to offer as auto-completion options?")
    atomic_suggestions.help_text = "Please enter a \"|\" separated list of words or phrases.  (These suggestions will only take effect for text fields.)"

    # ENUMERATION fields
    enumeration_choices = QEnumerationField(blank=True, null=True, verbose_name="Choose the property values that should be presented to users.")
    enumeration_default = QEnumerationField(blank=True, null=True, verbose_name="Choose the default value(s), if any, for this property.")
    enumeration_open = models.BooleanField(default=False, verbose_name="Check if a user can specify a custom property value.")
    enumeration_multi = models.BooleanField(default=False, verbose_name="Check if a user can specify multiple property values.")
    enumeration_nullable = models.BooleanField(default=False, verbose_name="Check if a user can specify an explicit <em>NONE</em> value.")

    def get_vocabulary_key(self):
        # convert UUID to str b/c UUID does not play nicely w/ JSON
        return str(self.vocabulary_key)

    def get_component_key(self):
        # convert UUID to str b/c UUID does not play nicely w/ JSON
        return str(self.component_key)

    def reset(self, proxy, reset_keys=True):

        self.proxy = proxy

        self.name = proxy.name
        self.order = proxy.order
        self.cardinality = proxy.cardinality
        self.field_type = proxy.field_type

        # any field...
        self.displayed = True
        self.required = proxy.is_required()
        self.editable = True
        self.unique = False
        self.verbose_name = pretty_string(proxy.name)
        self.documentation = proxy.documentation
        self.inline_help = False

        self.choice = proxy.choice
        self.display_extra_standard_name = False
        self.display_extra_description = False
        self.display_extra_units = False
        self.edit_extra_standard_name = False
        self.edit_extra_description = False
        self.edit_extra_units = False

        # atomic fields...
        if self.field_type == QPropertyTypes.ATOMIC:
            self.atomic_default = proxy.atomic_default
            self.atomic_type = proxy.atomic_type
            self.atomic_suggestions = ""

        # enumeration fields...
        elif self.field_type == QPropertyTypes.ENUMERATION:
            # see the comment near QCUSTOMIZATION_UNUSED_SCIENTIFIC_PROPERTY_ENUMERATION_CHOICES
            # to understand why I am getting rid of some of the proxy's enumeration_choices
            enumeration_choices = proxy.enumeration_choices
            unused_enumeration_choices = "|".join(QCUSTOMIZATION_UNUSED_SCIENTIFIC_PROPERTY_ENUMERATION_CHOICES)
            self.enumeration_choices = enumeration_choices.replace(unused_enumeration_choices, "")
            self.enumeration_default = ""
            self.enumeration_open = proxy.enumeration_open
            self.enumeration_multi = proxy.enumeration_multi
            self.enumeration_nullable = proxy.enumeration_nullable

        # relationship fields...
        else:  # self.field_type == QPropertyTypes.RELATIONSHIP:
            msg = "ScientificProperties cannot be RELATIONSHIPS"
            raise QError(msg)

        if reset_keys:
            # there is no need to _always_ do this,
            # b/c in get_new_customization_set I have already passed these values in as strings
            # (which is faster than these fk lookups)
            component = proxy.component_proxy
            vocabulary = component.vocabulary
            self.component_key = component.guid
            self.vocabulary_key = vocabulary.guid

#################
# through model #
#################

class QModelCustomizationVocabulary(models.Model):
    class Meta:
        app_label = APP_LABEL
        abstract = False
        unique_together = ("model_customization", "vocabulary", )
        ordering = ["order", ]
        verbose_name = "Questionnaire Vocabulary Customization"
        verbose_name_plural = "_Questionnaire Customizations: Vocabularies"

    model_customization = models.ForeignKey("QModelCustomization", related_name="link_to_model_customization")
    vocabulary = models.ForeignKey("QVocabulary", related_name="link_to_vocabulary")

    order = models.PositiveIntegerField(blank=False, default=1)
    active = models.BooleanField(default=False)

    def __unicode__(self):
        return u"%s :: %s" % (self.model_customization, self.vocabulary)

    # QModelCustomizationVocabulary does not inherit from QCustomization
    # so I need to explicitly re-define "get_field"
    def get_field(self, field_name):
        """
        convenience fn for getting the Django Field instance from a model
        """
        try:
            field = self._meta.get_field_by_name(field_name)
            return field[0]
        except FieldDoesNotExist:
            return None
