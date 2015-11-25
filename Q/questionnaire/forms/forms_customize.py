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

# from djangular.forms import NgModelForm, NgModelFormMixin, NgFormValidationMixin

from django.forms import ValidationError
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import curry

from Q.questionnaire.forms.forms_base import QForm, QInlineFormSet
from Q.questionnaire.q_utils import set_field_widget_attributes, update_field_widget_attributes, pretty_string, serialize_model_to_dict


class QCustomizationForm(QForm):
    class Meta:
        abstract = True

    def validate_unique(self):
        model_customization = self.instance
        try:
            model_customization.validate_unique()
        except ValidationError as e:
            # if there is a validation error then apply that error to the individual fields
            # so it shows up in the form and is rendered nicely
            unique_together_fields_list = model_customization.get_unique_together()
            for unique_together_fields in unique_together_fields_list:
                if any(field.lower() in " ".join(e.messages).lower() for field in unique_together_fields):
                    msg = [u'An instance with this {0} already exists.'.format(
                        " / ".join([pretty_string(utf) for utf in unique_together_fields])
                        )
                    ]
                    for unique_together_field in unique_together_fields:
                        self.errors[unique_together_field] = msg

class QCustomizationInlineFormSet(QInlineFormSet):

    pass


def get_customization_forms(customization_set):
    """
    calls either get_new_customization_forms or get_existing_customization_forms
    based on whether the customization_set is new or existing
    also, returns the results as a dictionary rather than a list
    :param customization_set:
    :return:
    """
    model_customization = customization_set["model_customization"]
    if model_customization.pk:
        model_customization_form, vocabulary_customizations_formset, standard_category_customizations_formset, standard_property_customizations_formset = \
            get_existing_customization_forms(customization_set)
    else:
        model_customization_form, vocabulary_customizations_formset, standard_category_customizations_formset, standard_property_customizations_formset, scientific_category_customizations_formset, scientific_property_customizations_formset = \
            get_new_customization_forms(customization_set)

    return {
        model_customization_form.form_name: model_customization_form,
        vocabulary_customizations_formset.formset_name: vocabulary_customizations_formset,
        standard_category_customizations_formset.formset_name: standard_category_customizations_formset,
        standard_property_customizations_formset.formset_name: standard_property_customizations_formset,
        scientific_property_customizations_formset.formset_name: scientific_property_customizations_formset,
    }


def get_new_customization_forms(customization_set):

    # TODO: REPLACE MOST OF THIS FN W/ A CALL TO "serialize_customization_set"

    from .forms_customize_models import QModelCustomizationForm
    from .forms_customize_vocabularies import QModelCustomizationVocabularyFormSetFactory
    from .forms_customize_categories import QStandardCategoryCustomizationInlineFormSetFactory, QScientificCategoryCustomizationInlineFormSetFactory
    from .forms_customize_properties import QStandardPropertyCustomizationInlineFormSetFactory, QScientificPropertyCustomizationInlineFormSetFactory

    # forms just need an instance
    # formsets need initial data (or a queryset for existing instances)

    model_customization = customization_set["model_customization"]
    vocabulary_customizations = customization_set["vocabulary_customizations"]
    standard_category_customizations = customization_set["standard_category_customizations"]
    standard_property_customizations = customization_set["standard_property_customizations"]
    scientific_category_customizations = customization_set["scientific_category_customizations"]
    scientific_property_customizations = customization_set["scientific_property_customizations"]

    model_customization_form = QModelCustomizationForm(
        instance=model_customization,
        # prefix="model_customization",  # this MUST match the model name used by ng
        scope_prefix="model_customization",  # ths MUST match the model name used by ng
        form_name="model_customization_form",
    )

    initial_standard_category_customizations_data = []
    for i, scc in enumerate(standard_category_customizations):
        initial_standard_category_customizations_data.append(
            serialize_model_to_dict(scc, include={
                "model_customization": model_customization.pk,
                "key": scc.get_key(),
            })
        )

    standard_category_customizations_formset = QStandardCategoryCustomizationInlineFormSetFactory(
        instance=model_customization,
        initial=initial_standard_category_customizations_data,
        extra=len(initial_standard_category_customizations_data),
        # prefix="model_customization.standard_categories",  # this MUST match the model name used by ng
        scope_prefix="model_customization.standard_categories",  # this MUST match the model name used by ng
        formset_name="model_customization_standard_categories_formset",
    )

    initial_standard_property_customizations_data = []
    for i, spc in enumerate(standard_property_customizations):
        initial_standard_property_customizations_data.append(
            serialize_model_to_dict(spc, include={
                "model_customization": model_customization.pk,
                "enumeration_choices": spc.get_enumeration_choices_value(),
                "key": spc.get_key(),
                "category_key": spc.category.get_key(),
            })
        )

    standard_property_customizations_formset = QStandardPropertyCustomizationInlineFormSetFactory(
        instance=model_customization,
        initial=initial_standard_property_customizations_data,
        extra=len(initial_standard_property_customizations_data),
        # prefix="model_customization.standard_categories",  # this MUST match the model name used by ng
        scope_prefix="model_customization.standard_properties",  # this MUST match the model name used by ng
        formset_name="model_customization_standard_properties_formset",
    )

    initial_vocabulary_customizations_data = []
    for i, vc in enumerate(vocabulary_customizations):
        vocabulary = vc.vocabulary
        initial_vocabulary_customizations_data.append(
            serialize_model_to_dict(vc, include={
                "model_customization": model_customization.pk,
                "vocabulary_name": str(vocabulary),
                "vocabulary_key": vocabulary.get_key(),
                "display_detail": i == 0,  # the 1st vocab is displayed by default
            })
        )

    vocabulary_customizations_formset = QModelCustomizationVocabularyFormSetFactory(
        instance=model_customization,
        initial=initial_vocabulary_customizations_data,
        extra=len(initial_vocabulary_customizations_data),
        # prefix="model_customization.vocabularies",  # this MUST match the model name used by ng
        scope_prefix="model_customization.vocabularies",  # this MUST match the model name used by ng
        formset_name="model_customization_vocabularies_formset",
    )

    initial_scientific_category_customizations_data = []
    for i, scc in enumerate(scientific_category_customizations):
        initial_scientific_category_customizations_data.append(
            serialize_model_to_dict(scc, include={
                "model_customization": model_customization.pk,
                "key": scc.get_key(),
            })
        )

    scientific_category_customizations_formset = QScientificCategoryCustomizationInlineFormSetFactory(
        instance=model_customization,
        initial=initial_scientific_category_customizations_data,
        extra=len(initial_scientific_category_customizations_data),
        # prefix="model_customization.scientific_categories",  # this MUST match the model name used by ng
        scope_prefix="model_customization.scientific_categories",  # this MUST match the model name used by ng
        formset_name="model_customization_scientific_categories_formset",
    )

    initial_scientific_property_customizations_data = []
    for i, spc in enumerate(scientific_property_customizations):
        initial_scientific_property_customizations_data.append(
            serialize_model_to_dict(spc, include={
                "model_customization": model_customization.pk,
                "enumeration_choices": spc.get_enumeration_choices_value(),
                "key": spc.get_key(),
                "category_key": spc.category.get_key(),
            })
        )

    scientific_property_customizations_formset = QScientificPropertyCustomizationInlineFormSetFactory(
        instance=model_customization,
        initial=initial_scientific_property_customizations_data,
        extra=len(initial_scientific_property_customizations_data),
        # prefix="model_customization.scientific_categories",  # this MUST match the model name used by ng
        scope_prefix="model_customization.scientific_properties",  # this MUST match the model name used by ng
        formset_name="model_customization_scientific_properties_formset",
    )

    return model_customization_form, vocabulary_customizations_formset, standard_category_customizations_formset, standard_property_customizations_formset, scientific_category_customizations_formset, scientific_property_customizations_formset


def get_existing_customization_forms(customization_set):

    from .forms_customize_models import QModelCustomizationForm
    from .forms_customize_vocabularies import QModelCustomizationVocabularyFormSetFactory
    from .forms_customize_categories import QStandardCategoryCustomizationInlineFormSetFactory
    from .forms_customize_properties import QStandardPropertyCustomizationInlineFormSetFactory

    # forms just need an instance
    # formsets need a queryset (or initial_data for new instances)

    model_customization = customization_set["model_customization"]
    vocabulary_customizations = customization_set["vocabulary_customizations"]
    standard_category_customizations = customization_set["standard_category_customizations"]
    standard_property_customizations = customization_set["standard_property_customizations"]

    model_customization_form = QModelCustomizationForm(
        instance=model_customization,
        # prefix="model_customization",  # this MUST match the model name used by ng
        scope_prefix="model_customization",  # ths MUST match the model name used by ng
        form_name="model_customization_form",
    )

    vocabulary_customizations_formset = QModelCustomizationVocabularyFormSetFactory(
        instance=model_customization,
        queryset=vocabulary_customizations,
        # prefix="model_customization.vocabularies",  # this MUST match the model name used by ng
        scope_prefix="model_customization.vocabularies",  # this MUST match the model name used by ng
        formset_name="model_customization_vocabularies_formset",
    )

    standard_category_customizations_formset = QStandardCategoryCustomizationInlineFormSetFactory(
        instance=model_customization,
        queryset=standard_category_customizations,
        # prefix="model_customization.standard_categories",  # this MUST match the model name used by ng
        scope_prefix="model_customization.standard_categories",  # this MUST match the model name used by ng
        formset_name="model_customization_standard_categories_formset",
    )

    standard_property_customizations_formset = QStandardPropertyCustomizationInlineFormSetFactory(
        instance=model_customization,
        queryset=standard_property_customizations,
        # prefix="model_customization.standard_categories",  # this MUST match the model name used by ng
        scope_prefix="model_customization.standard_properties",  # this MUST match the model name used by ng
        formset_name="model_customization_standard_properties_formset",
    )

    return model_customization_form, vocabulary_customizations_formset, standard_category_customizations_formset, standard_property_customizations_formset
