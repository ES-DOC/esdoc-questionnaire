####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2014 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"
__date__ = "Dec 01, 2014 3:00:00 PM"

"""
.. module:: forms_customize

Base classes for CIM Questionnaire customization form creation & manipulation
"""

from django.template.defaultfilters import slugify

from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary
from CIM_Questionnaire.questionnaire.forms.forms_base import MetadataForm, MetadataInlineFormSet
from CIM_Questionnaire.questionnaire.utils import find_in_sequence, get_data_from_form, get_data_from_formset


class MetadataCustomizerForm(MetadataForm):

    def __init__(self, *args, **kwargs):

        initial = kwargs.pop("initial", None) or {}

        initial["loaded"] = True
        kwargs["initial"] = initial

        super(MetadataCustomizerForm, self).__init__(*args, **kwargs)


class MetadataCustomizerInlineFormSet(MetadataInlineFormSet):

    # just using this class to automatically sort the forms based on the field order

    def __iter__(self):
        """Yields the forms in the order they should (initially) be rendered"""
        forms = list(self.forms)
        try:
            forms.sort(key=lambda x: x.initial["order"])
        except KeyError:
            forms.sort(key = lambda x: x.data["%s-order"%(x.prefix)])
        return iter(forms)

    def __getitem__(self, index):
        """Returns the form at the given index, based on the rendering order"""
        forms = list(self.forms)
        try:
            forms.sort(key = lambda x: x.initial["order"])
        except KeyError:
            forms.sort(key = lambda x: x.data["%s-order" % x.prefix])
        return forms[index]

    # also using it to cache fk or m2m fields to avoid needless db hits

    def _construct_form(self, i, **kwargs):

        form = super(MetadataCustomizerInlineFormSet, self)._construct_form(i, **kwargs)

        for cached_field_name in form.cached_fields:
            cached_field = form.fields[cached_field_name]
            cached_field_key = u"%s_%s" % (self.prefix, cached_field_name)
            cached_field.cache_choices = True
            choices = getattr(self, '_cached_choices_%s' % cached_field_key, None)
            if choices is None:
                choices = list(cached_field.choices)
                setattr(self, '_cached_choices_%s' % cached_field_key, choices)
            cached_field.choice_cache = choices

        return form


def create_new_customizer_forms_from_models(model_customizer, standard_category_customizers, standard_property_customizers, scientific_category_customizers, scientific_property_customizers, vocabularies_to_customize=MetadataVocabulary.objects.none(), is_subform=False):

    from .forms_customize_model import create_model_customizer_form_data, MetadataModelCustomizerForm, MetadataModelCustomizerSubForm
    from .forms_customize_standard_properties import create_standard_property_customizer_form_data, MetadataStandardPropertyCustomizerInlineFormSetFactory
    from .forms_customize_scientific_properties import create_scientific_property_customizer_form_data, MetadataScientificPropertyCustomizerInlineFormSetFactory
    from .forms_customize_vocabularies import create_model_customizer_vocabulary_form_data, MetadataModelCustomizerVocabularyFormSetFactory

    model_customizer_data = create_model_customizer_form_data(model_customizer, standard_category_customizers,scientific_category_customizers, vocabularies=vocabularies_to_customize)
    if is_subform:
        model_customizer_form = MetadataModelCustomizerSubForm(initial=model_customizer_data, all_vocabularies=vocabularies_to_customize)
        model_customizer_vocabularies_formset = None
    else:
        model_customizer_form = MetadataModelCustomizerForm(initial=model_customizer_data, all_vocabularies=vocabularies_to_customize)
        model_customizer_vocabularies_data = \
            [create_model_customizer_vocabulary_form_data(model_customizer, vocabulary, i)
             for i, vocabulary in enumerate(vocabularies_to_customize)]
        model_customizer_vocabularies_formset = MetadataModelCustomizerVocabularyFormSetFactory(
            instance=model_customizer,
            initial=model_customizer_vocabularies_data,
            extra=len(model_customizer_vocabularies_data),
        )

    standard_property_customizers_data = [create_standard_property_customizer_form_data(model_customizer, standard_property_customizer) for standard_property_customizer in standard_property_customizers]
    standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
        instance=model_customizer,
        initial=standard_property_customizers_data,
        extra=len(standard_property_customizers_data),
        categories=standard_category_customizers,
    )

    scientific_property_customizer_formsets = {}
    for vocabulary_key,scientific_property_customizer_dict in scientific_property_customizers.iteritems():
        scientific_property_customizer_formsets[vocabulary_key] = {}
        for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
            model_key = u"%s_%s" % (vocabulary_key, component_key)
            scientific_property_customizers_data = [
                create_scientific_property_customizer_form_data(model_customizer, scientific_property_customizer)
                for scientific_property_customizer in scientific_property_customizers[vocabulary_key][component_key]
            ]
            scientific_property_customizer_formsets[vocabulary_key][component_key] = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                instance=model_customizer,
                initial=scientific_property_customizers_data,
                extra=len(scientific_property_customizers_data),
                prefix=model_key,
                categories=scientific_category_customizers[vocabulary_key][component_key]
            )

    return (model_customizer_form, standard_property_customizer_formset, scientific_property_customizer_formsets, model_customizer_vocabularies_formset)


def create_existing_customizer_forms_from_models(model_customizer, standard_category_customizers, standard_property_customizers, scientific_category_customizers, scientific_property_customizers, vocabularies_to_customize=MetadataVocabulary.objects.none(), is_subform=False):

    # TODO: CAN I GET RID OF THE NEED FOR "create_model_customizer_form_data"?
    from .forms_customize_model import create_model_customizer_form_data, MetadataModelCustomizerForm, MetadataModelCustomizerSubForm
    from .forms_customize_standard_properties import MetadataStandardPropertyCustomizerInlineFormSetFactory
    from .forms_customize_scientific_properties import MetadataScientificPropertyCustomizerInlineFormSetFactory
    from .forms_customize_vocabularies import MetadataModelCustomizerVocabularyFormSetFactory

    model_customizer_data = create_model_customizer_form_data(model_customizer, standard_category_customizers, scientific_category_customizers, vocabularies=vocabularies_to_customize)
    if is_subform:
        model_customizer_form = MetadataModelCustomizerSubForm(instance=model_customizer, initial=model_customizer_data, all_vocabularies=vocabularies_to_customize)
        model_customizer_vocabularies_formset = None
    else:
        model_customizer_form = MetadataModelCustomizerForm(instance=model_customizer, initial=model_customizer_data, all_vocabularies=vocabularies_to_customize)
        model_customizer_vocabularies_formset = MetadataModelCustomizerVocabularyFormSetFactory(
            instance=model_customizer,
        )

    standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
        instance=model_customizer,
        queryset=standard_property_customizers,
        # don't pass extra; w/ existing (queryset) models, extra ought to be 0
        # extra=len(standard_property_customizers),
        categories=standard_category_customizers,
    )

    scientific_property_customizer_formsets = {}
    for vocabulary_key,scientific_property_customizer_dict in scientific_property_customizers.iteritems():
        scientific_property_customizer_formsets[vocabulary_key] = {}
        for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
            scientific_property_customizer_formsets[vocabulary_key][component_key] = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                instance=model_customizer,
                queryset=scientific_property_customizer_list,
                # don't pass extra; w/ existing (queryset) models, extra ought to be 0
                # extra=len(scientific_property_customizer_list),
                prefix=u"%s_%s" % (vocabulary_key, component_key),
                categories=scientific_category_customizers[vocabulary_key][component_key],
            )

    return (model_customizer_form, standard_property_customizer_formset, scientific_property_customizer_formsets, model_customizer_vocabularies_formset)


def create_customizer_forms_from_data(data, model_customizer, standard_category_customizers, standard_property_customizers, scientific_category_customizers, scientific_property_customizers, vocabularies_to_customize=MetadataVocabulary.objects.none(), is_subform=False, subform_prefix=""):
    """This creates and validates forms based on POST data"""

    from .forms_customize_model import create_model_customizer_form_data, MetadataModelCustomizerForm, MetadataModelCustomizerSubForm
    from .forms_customize_standard_properties import create_standard_property_customizer_form_data, MetadataStandardPropertyCustomizerInlineFormSetFactory
    from .forms_customize_scientific_properties import create_scientific_property_customizer_form_data, MetadataScientificPropertyCustomizerInlineFormSetFactory
    from .forms_customize_vocabularies import create_model_customizer_vocabulary_form_data, MetadataModelCustomizerVocabularyFormSetFactory

    if is_subform:
        if subform_prefix:
            model_customizer_form = MetadataModelCustomizerSubForm(data, instance=model_customizer, all_vocabularies=vocabularies_to_customize, prefix=subform_prefix)
        else:
            model_customizer_form = MetadataModelCustomizerSubForm(data, instance=model_customizer, all_vocabularies=vocabularies_to_customize)
    else:
        model_customizer_form = MetadataModelCustomizerForm(data, instance=model_customizer, all_vocabularies=vocabularies_to_customize)
    model_customizer_form_validity = model_customizer_form.is_valid()

    if model_customizer_form_validity:
        model_customizer_instance = model_customizer_form.save(commit=False)

    # now do some post-processing validation
    # (b/c I have to compare the content of model_customizer_vocabularies_formset & model_customizer_form)

    validity = [model_customizer_form_validity]

    if is_subform:
        model_customizer_vocabularies_formset = None
        active_vocabulary_keys = []
    else:
        model_customizer_vocabularies_formset = MetadataModelCustomizerVocabularyFormSetFactory(
            data=data,
            instance=model_customizer_instance if model_customizer_form_validity else model_customizer,
        )
        validity += [model_customizer_vocabularies_formset.is_valid()]
        active_vocabulary_forms = model_customizer_vocabularies_formset.get_active_forms()
        active_vocabulary_keys = \
            [active_vocabulary_form.cleaned_data["vocabulary"].get_key()
             for active_vocabulary_form in active_vocabulary_forms
            ]
    if is_subform and subform_prefix:
        standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance=model_customizer_instance if model_customizer_form_validity else model_customizer,
            data=data,
            categories=standard_category_customizers,
            # TODO: WORKING OUT THE APPROPRIATE PREFIX SHOULD BE AUTOMATIC!
            prefix=u"standard_property-%s" % subform_prefix
        )
    else:
        standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance=model_customizer_instance if model_customizer_form_validity else model_customizer,
            data=data,
            categories=standard_category_customizers,
        )
    validity += [standard_property_customizer_formset.is_valid()]

    scientific_property_customizer_formsets = {}
    for vocabulary_key, scientific_property_customizer_dict in scientific_property_customizers.iteritems():
        scientific_property_customizer_formsets[vocabulary_key] = {}
        for component_key, scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
            model_key = u"%s_%s" % (vocabulary_key, component_key)
            if is_subform and subform_prefix:
                scientific_property_customizer_formsets[vocabulary_key][component_key] = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                    instance=model_customizer_instance if model_customizer_form_validity else model_customizer,
                    data=data,
                    prefix=u"%s-%s" % (model_key, subform_prefix),
                    categories=scientific_category_customizers[vocabulary_key][component_key]
                )
            else:
                scientific_property_customizer_formsets[vocabulary_key][component_key] = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                    instance=model_customizer_instance if model_customizer_form_validity else model_customizer,
                    data=data,
                    prefix=model_key,
                    categories=scientific_category_customizers[vocabulary_key][component_key]
                )
            if vocabulary_key in active_vocabulary_keys:
                validity += [scientific_property_customizer_formsets[vocabulary_key][component_key].is_valid()]

    return (validity, model_customizer_form, standard_property_customizer_formset, scientific_property_customizer_formsets, model_customizer_vocabularies_formset)


def get_data_from_customizer_forms(model_customizer_form, standard_property_customizer_formset, scientific_property_customizer_formsets):

    # TODO: DEAL w/ VOCABULARYFORMS AS WELL
    data = {}

    model_customizer_form_data = get_data_from_form(model_customizer_form)
    data.update(model_customizer_form_data)

    standard_property_customizer_formset_data = get_data_from_formset(standard_property_customizer_formset)
    data.update(standard_property_customizer_formset_data)

    for vocabulary_key,scientific_property_customizer_formset_dict in scientific_property_customizer_formsets.iteritems():
        for component_key,scientific_property_customizer_formset in scientific_property_customizer_formset_dict.iteritems():
            scientific_property_customizer_formset_data = get_data_from_formset(scientific_property_customizer_formset)
            data.update(scientific_property_customizer_formset_data)

    data_copy = data.copy()
    for key, value in data.iteritems():
        if value == None:
            data_copy.pop(key)

    return data_copy


def save_valid_forms(model_customizer_form, standard_property_customizer_formset, scientific_property_customizer_formsets, model_customizer_vocabularies_formset):

    model_customizer_instance = model_customizer_form.save()

    if model_customizer_vocabularies_formset:
        model_customizer_vocabularies_formset.save()
        active_vocabulary_forms = model_customizer_vocabularies_formset.get_active_forms()
        active_vocabularies = \
            [active_vocabulary_form.cleaned_data["vocabulary"]
            for active_vocabulary_form in active_vocabulary_forms
            ]
    else:
        active_vocabularies = []

    standard_categories_to_process = model_customizer_form.standard_categories_to_process
    scientific_categories_to_process = model_customizer_form.scientific_categories_to_process

    # save (or delete) the standard category customizers...
    active_standard_categories = []
    for standard_category_to_process in standard_categories_to_process:
        standard_category_customizer = standard_category_to_process.object
        if standard_category_customizer.pending_deletion:
            standard_category_to_process.delete()
        else:
            standard_category_customizer.model_customizer = model_customizer_instance
            standard_category_to_process.save()
            active_standard_categories.append(standard_category_customizer)

    # save (or delete) the scientific category customizers...
    # TODO: DO I REALLY NEED TO DEAL W/ ALL scientific_category_customizers OR JUST THE ONES IN active_vocabularies?
    active_scientific_categories = {}
    for vocabulary_key, scientific_categories_to_process_dict in scientific_categories_to_process.iteritems():
        active_scientific_categories[vocabulary_key] = {}
        for component_key, scientific_categories_to_process_list in scientific_categories_to_process_dict.iteritems():
            active_scientific_categories[vocabulary_key][component_key] = []
            for scientific_category_to_process in scientific_categories_to_process_list:
                scientific_category_customizer = scientific_category_to_process.object
                if scientific_category_customizer.pending_deletion:
                    scientific_category_customizer.delete()
                else:
                    scientific_category_customizer.model_customizer = model_customizer_instance
                    scientific_category_customizer.vocabulary_key = vocabulary_key
                    scientific_category_customizer.component_key = component_key
                    scientific_category_customizer.model_key = u"%s_%s" % (vocabulary_key, component_key)
                    scientific_category_customizer.save()
                    active_scientific_categories[vocabulary_key][component_key].append(scientific_category_customizer)

    # save the standard property customizers...
    standard_property_customizer_instances = standard_property_customizer_formset.save(commit=False)
    for standard_property_customizer_instance in standard_property_customizer_instances:
        category_key = slugify(standard_property_customizer_instance.category_name)
        category = find_in_sequence(lambda category: category.key==category_key,active_standard_categories)
        standard_property_customizer_instance.category = category
        standard_property_customizer_instance.save()

    # save the scientific property customizers...
    for (vocabulary_key, formset_dictionary) in scientific_property_customizer_formsets.iteritems():
        if find_in_sequence(lambda vocabulary: vocabulary.get_key()==vocabulary_key, active_vocabularies):
            for (component_key,scientific_property_customizer_formset) in formset_dictionary.iteritems():
                scientific_property_customizer_instances = scientific_property_customizer_formset.save(commit=False)
                for scientific_property_customizer_instance in scientific_property_customizer_instances:
                    # TODO: DOES THIS WORK FOR CATEGORY_KEY SINCE CHANGING TO USING GUIDS
                    # TODO: CHANGE CODE TO USE GUIDS FOR CATEGORIES AS WELL AS COMPONENTS/VOCABULARIES
                    category_key = slugify(scientific_property_customizer_instance.category_name)
                    category = find_in_sequence(lambda category: category.key == category_key, active_scientific_categories[vocabulary_key][component_key])
                    scientific_property_customizer_instance.category = category
                    scientific_property_customizer_instance.save()

    return model_customizer_instance
