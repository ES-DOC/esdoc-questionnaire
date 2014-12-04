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
.. module:: forms_edit

Base classes for CIM Questionnaire edit form creation & manipulation
"""

from django.forms import ValidationError
from django.forms.formsets import ManagementForm, TOTAL_FORM_COUNT, INITIAL_FORM_COUNT, MAX_NUM_FORM_COUNT
from django.utils.translation import ugettext

from CIM_Questionnaire.questionnaire.forms.base import MetadataForm, MetadataFormSet, MetadataInlineFormSet
from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes
from CIM_Questionnaire.questionnaire.utils import get_data_from_formset


class MetadataEditingForm(MetadataForm):

    customizer = None

    def __init__(self, *args, **kwargs):
        # customizer gets passed in via curry() in the factory functions
        customizer = kwargs.pop("customizer", None)

        super(MetadataEditingForm, self).__init__(*args, **kwargs)

        if customizer:
            self.customize(customizer)

    def get_customizer(self):
        return self.customizer

    def get_hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)

    def get_header_fields(self):
        return self.get_fields_from_list(self._header_fields)


class MetadataEditingFormSet(MetadataFormSet):

    number_of_properties = 0       # lets me keep track of the number of forms w/out having to actually render them

    @property
    def management_form(self):
        """Returns the ManagementForm instance for this FormSet."""

        initial_forms = self.initial_form_count()
        total_forms = initial_forms + self.extra
        # Allow all existing related objects/inlines to be displayed,
        # but don't allow extra beyond max_num.
        if initial_forms > self.max_num >= 0:
            total_forms = initial_forms
        elif total_forms > self.max_num >= 0:
            total_forms = self.max_num

        initial = {
            TOTAL_FORM_COUNT: total_forms,
            INITIAL_FORM_COUNT: initial_forms,
            MAX_NUM_FORM_COUNT: self.absolute_max,
        }

        if self.is_bound:
            # passing initial along w/ data just in case formset was not loaded
            form = ManagementForm(self.data, auto_id=self.auto_id, prefix=self.prefix, initial=initial)
            if not form.is_valid():
                raise ValidationError(
                    ugettext('ManagementForm data is missing or has been tampered with'),
                    code='missing_management_form',
                )
        else:
            form = ManagementForm(auto_id=self.auto_id, prefix=self.prefix, initial=initial)
        return form

    # if these formsets are not loaded,
    # then accessing total_form_count or initial_form_count via the management_form will fail
    # so I override them below...

    def total_form_count(self):
        """Returns the total number of forms in this FormSet."""
        if self.is_bound:
            try:
                return min(self.management_form.cleaned_data[TOTAL_FORM_COUNT], self.absolute_max)
            except ValidationError:
                # HERE IS THE NEW CODE
                # (KEPT THE ABOVE TRY CLAUSE IN-CASE A FORM WAS ADDED BY JS)
                # (IN WHICH CASE IT MUST HAVE BEEN LOADED AND THE TRY WILL NOT FAIL)
                return min(self.number_of_properties, self.absolute_max)
        else:
            initial_forms = self.initial_form_count()
            total_forms = initial_forms + self.extra
            # Allow all existing related objects/inlines to be displayed,
            # but don't allow extra beyond max_num.
            if initial_forms > self.max_num >= 0:
                total_forms = initial_forms
            elif total_forms > self.max_num >= 0:
                total_forms = self.max_num
        return total_forms

    def initial_form_count(self):
        # Use the length of the initial data if it's there, 0 otherwise.
        return len(self.initial) if self.initial else 0


class MetadataEditingInlineFormSet(MetadataInlineFormSet):

    number_of_properties = 0       # lets me keep track of the number of forms w/out having to actually render them

    @property
    def management_form(self):
        """Returns the ManagementForm instance for this FormSet."""

        initial_forms = self.initial_form_count()
        total_forms = initial_forms + self.extra
        # Allow all existing related objects/inlines to be displayed,
        # but don't allow extra beyond max_num.
        if initial_forms > self.max_num >= 0:
            total_forms = initial_forms
        elif total_forms > self.max_num >= 0:
            total_forms = self.max_num

        initial = {
            TOTAL_FORM_COUNT: total_forms,
            INITIAL_FORM_COUNT: initial_forms,
            MAX_NUM_FORM_COUNT: self.absolute_max,
        }

        if self.is_bound:
            # passing initial along w/ data just in case formset was not loaded
            form = ManagementForm(self.data, auto_id=self.auto_id, prefix=self.prefix, initial=initial)
            if not form.is_valid():
                raise ValidationError(
                    ugettext('ManagementForm data is missing or has been tampered with'),
                    code='missing_management_form',
                )
        else:
            form = ManagementForm(auto_id=self.auto_id, prefix=self.prefix, initial=initial)
        return form

    # if these formsets are not loaded,
    # then accessing total_form_count or initial_form_count via the management_form will fail
    # so I override them below...

    def total_form_count(self):
        """Returns the total number of forms in this FormSet."""
        if self.is_bound:
            try:
                return min(self.management_form.cleaned_data[TOTAL_FORM_COUNT], self.absolute_max)
            except ValidationError:
                # HERE IS THE NEW CODE
                # (KEPT THE ABOVE TRY CLAUSE IN-CASE A FORM WAS ADDED BY JS)
                # (IN WHICH CASE IT MUST HAVE BEEN LOADED AND THE TRY WILL NOT FAIL)
                return min(self.number_of_properties, self.absolute_max)
        else:
            initial_forms = self.initial_form_count()
            total_forms = initial_forms + self.extra
            # Allow all existing related objects/inlines to be displayed,
            # but don't allow extra beyond max_num.
            if initial_forms > self.max_num >= 0:
                total_forms = initial_forms
            elif total_forms > self.max_num >= 0:
                total_forms = self.max_num
        return total_forms

    def initial_form_count(self):
        # Use the length of the initial data if it's there, 0 otherwise.
        return len(self.initial) if self.initial else 0


def create_new_edit_forms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties,scientific_property_customizers):

    from .forms_edit_model import create_model_form_data, MetadataModelFormSetFactory
    from .forms_edit_standard_properties import create_standard_property_form_data, MetadataStandardPropertyInlineFormSetFactory
    from .forms_edit_scientific_properties import create_scientific_property_form_data, MetadataScientificPropertyInlineFormSetFactory

    model_keys = [model.get_model_key() for model in models]

    models_data = [create_model_form_data(model, model_customizer) for model in models]
    model_formset = MetadataModelFormSetFactory(
        initial=models_data,
        extra=len(models_data),
        prefixes=model_keys,
        customizer=model_customizer,
    )

    standard_properties_formsets = {}
    scientific_properties_formsets = {}
    for model_key, model in zip(model_keys, models):

        standard_properties_data = [
            create_standard_property_form_data(model, standard_property, standard_property_customizer)
            for standard_property, standard_property_customizer in
            zip(standard_properties[model_key], standard_property_customizers)
            if standard_property_customizer.displayed
        ]
        standard_properties_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
            instance=model,
            prefix=model_key,
            initial=standard_properties_data,
            extra=len(standard_properties_data),
            customizers=standard_property_customizers,
        )

        # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
        if model_key not in scientific_property_customizers:
            scientific_property_customizers[model_key] = []

        scientific_properties_data = [
            create_scientific_property_form_data(model, scientific_property, scientific_property_customizer)
            for scientific_property, scientific_property_customizer in
            zip(scientific_properties[model_key], scientific_property_customizers[model_key])
            if scientific_property_customizer.displayed
        ]
        scientific_properties_formsets[model_key] = MetadataScientificPropertyInlineFormSetFactory(
            instance=model,
            prefix=model_key,
            initial=scientific_properties_data,
            extra=len(scientific_properties_data),
            customizers=scientific_property_customizers[model_key],
        )

    return (model_formset, standard_properties_formsets, scientific_properties_formsets)


def create_existing_edit_forms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers):

    from .forms_edit_model import create_model_form_data, MetadataModelFormSetFactory
    from .forms_edit_standard_properties import create_standard_property_form_data, MetadataStandardPropertyInlineFormSetFactory
    from .forms_edit_scientific_properties import create_scientific_property_form_data, MetadataScientificPropertyInlineFormSetFactory

    model_keys = [model.get_model_key() for model in models]

    model_formset = MetadataModelFormSetFactory(
        queryset=models,
        prefixes=model_keys,
        customizer=model_customizer,
    )

    standard_properties_formsets = {}
    scientific_properties_formsets = {}
    for model_key, model in zip(model_keys,models):

        standard_properties_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
            instance=model,
            prefix=model_key,
            queryset=standard_properties[model_key],
            customizers=standard_property_customizers,
        )

        # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
        if model_key not in scientific_property_customizers:
            scientific_property_customizers[model_key] = []

        scientific_properties_formsets[model_key] = MetadataScientificPropertyInlineFormSetFactory(
            instance=model,
            prefix=model_key,
            queryset=scientific_properties[model_key],
            customizers=scientific_property_customizers[model_key],
        )

    return (model_formset, standard_properties_formsets, scientific_properties_formsets)


def create_new_edit_subforms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix="", subform_min=0, subform_max=1,  increment_prefix=0):

    from .forms_edit_model import create_model_form_data, MetadataModelSubFormSetFactory
    from .forms_edit_standard_properties import create_standard_property_form_data, MetadataStandardPropertyInlineFormSetFactory
    from .forms_edit_scientific_properties import create_scientific_property_form_data, MetadataScientificPropertyInlineFormSetFactory

    model_keys = [model.get_model_key() for model in models]

    models_data = [create_model_form_data(model, model_customizer) for model in models]
    model_formset = MetadataModelSubFormSetFactory(
        initial=models_data,
        extra=len(models_data),
        prefix=subform_prefix,
        customizer=model_customizer,
        min=subform_min,
        max=subform_max,
        increment_prefix=increment_prefix,
    )

    standard_properties_formsets = {}
    scientific_properties_formsets = {}
    for i, (model, model_form) in enumerate(zip(models,model_formset.forms)):

        model_prefix = model_form.prefix
        submodel_key = model.get_model_key() + "-%s" % i

        standard_properties_data = [
            create_standard_property_form_data(model, standard_property, standard_property_customizer)
            for standard_property, standard_property_customizer in zip(standard_properties[submodel_key], standard_property_customizers)
            if standard_property_customizer.displayed
        ]
        standard_properties_formsets[model_prefix] = MetadataStandardPropertyInlineFormSetFactory(
            instance=model,
            initial=standard_properties_data,
            extra=len(standard_properties_data),
            customizers=standard_property_customizers,
            prefix=model_prefix,
        )

        # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
        if submodel_key not in scientific_property_customizers:
            scientific_property_customizers[submodel_key] = []

        scientific_properties_data = [
            create_scientific_property_form_data(model, scientific_property, scientific_property_customizer)
            for scientific_property, scientific_property_customizer in zip(scientific_properties[submodel_key], scientific_property_customizers[submodel_key])
            if scientific_property_customizer.displayed
        ]
        assert(len(scientific_properties_data) == len(scientific_properties[submodel_key]))
        scientific_properties_formsets[model_prefix] = MetadataScientificPropertyInlineFormSetFactory(
            instance=model,
            initial=scientific_properties_data,
            extra=len(scientific_properties_data),
            customizers=scientific_property_customizers[submodel_key],
            prefix=model_prefix,
        )

    return (model_formset, standard_properties_formsets, scientific_properties_formsets)


def create_existing_edit_subforms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix="", subform_min=0, subform_max=1, increment_prefix=0):

    from .forms_edit_model import MetadataModelSubFormSetFactory
    from .forms_edit_standard_properties import MetadataStandardPropertyInlineSubFormSetFactory
    from .forms_edit_scientific_properties import MetadataScientificPropertyInlineFormSetFactory

    model_keys = [model.get_model_key() for model in models]

    model_formset = MetadataModelSubFormSetFactory(
        queryset=models,
        prefix=subform_prefix,
        customizer=model_customizer,
        min=subform_min,
        max=subform_max,
        increment_prefix=increment_prefix,
    )

    standard_properties_formsets = {}
    scientific_properties_formsets = {}
    for i, (model, model_form) in enumerate(zip(models, model_formset.forms)):

        model_prefix = model_form.prefix
        submodel_key = model.get_model_key() + "-%s" % i

        standard_properties_formsets[model_prefix] = MetadataStandardPropertyInlineSubFormSetFactory(
            instance=model,
            prefix=model_prefix,
            queryset=standard_properties[submodel_key],
            customizers=standard_property_customizers,
        )

        # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
        if submodel_key not in scientific_property_customizers:
            scientific_property_customizers[submodel_key] = []

        scientific_properties_formsets[model_prefix] = MetadataScientificPropertyInlineFormSetFactory(
            instance=model,
            prefix=model_prefix,
            queryset=scientific_properties[submodel_key],
            customizers=scientific_property_customizers[submodel_key],
        )

    return (model_formset, standard_properties_formsets, scientific_properties_formsets)


def create_edit_forms_from_data(data, models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers):
    """
    This creates and validates forms based on POST data
    However, not all of the forms may have been loaded
    """
    from .forms_edit_model import create_model_form_data, MetadataModelFormSetFactory
    from .forms_edit_standard_properties import create_standard_property_form_data, MetadataStandardPropertyInlineFormSetFactory
    from .forms_edit_scientific_properties import create_scientific_property_form_data, MetadataScientificPropertyInlineFormSetFactory

    model_keys = [model.get_model_key() for model in models]

    models_data = [create_model_form_data(model, model_customizer) for model in models]

    model_formset = MetadataModelFormSetFactory(
        data=data,
        initial=models_data,  # look at this; I'm passing initial AND data (this is to provide default values to unloaded forms)
        prefixes=model_keys,
        customizer=model_customizer,
    )

    loaded_model_forms = model_formset.get_loaded_forms()
    loaded_model_keys = [model_form.prefix for model_form in loaded_model_forms]

    model_formset_validity = model_formset.is_valid(loaded_prefixes=loaded_model_keys)
    if model_formset_validity:
        model_instances = model_formset.save(commit=False)
    validity = [model_formset_validity]

    standard_properties_formsets = {}
    scientific_properties_formsets = {}

    for (i, model_key) in enumerate(model_keys):

        loaded = model_key in loaded_model_keys

        # create and validate the standard properties...

        standard_properties_post_data = data.copy()
        standard_properties_initial_data = []

        if not loaded:
            # re-create initial data in case there will be no corresponding post data...
            standard_properties_initial_data = [
                # TODO: THE 1st ARGUMENT IS MEANT TO BE model BUT IT ISN'T USED
                # TODO: SO I CAN GET AWAY W/ PASSING None
                # TODO: REWRITE THIS FN TO NOT TAKE model
                create_standard_property_form_data(None, standard_property, standard_property_customizer)
                for standard_property, standard_property_customizer in
                zip(standard_properties[model_key], standard_property_customizers)
                if standard_property_customizer.displayed
            ]

        standard_properties_formset = MetadataStandardPropertyInlineFormSetFactory(
            instance=model_instances[i] if model_formset_validity else models[i],
            prefix=model_key,
            data=standard_properties_post_data,
            initial=standard_properties_initial_data,  # look at this; I'm passing initial AND data (this is to provide default values to unloaded forms)
            customizers=standard_property_customizers,
        )

        if not loaded:
            # manually add default values for management_form (prior to calling is_valid)...
            standard_properties_post_data[standard_properties_formset.add_prefix(TOTAL_FORM_COUNT)] = standard_properties_formset.total_form_count()
            standard_properties_post_data[standard_properties_formset.add_prefix(INITIAL_FORM_COUNT)] = standard_properties_formset.initial_form_count()
            standard_properties_post_data[standard_properties_formset.add_prefix(MAX_NUM_FORM_COUNT)] = standard_properties_formset.absolute_max

        validity += [standard_properties_formset.is_valid(loaded_prefixes=[form.prefix for form in standard_properties_formset.forms if loaded])]

        standard_properties_formsets[model_key] = standard_properties_formset

        # create and validate the scientific properties...

        scientific_properties_post_data = data.copy()
        scientific_properties_initial_data = []

        # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
        if model_key not in scientific_property_customizers:
            scientific_property_customizers[model_key] = []

        if not loaded:
            # re-create initial data in case there will be no corresponding post data...
            scientific_properties_initial_data = [
                # TODO: THE 1st ARGUMENT IS MEANT TO BE model BUT IT ISN'T USED
                # TODO: SO I CAN GET AWAY W/ PASSING None
                # TODO: REWRITE THIS FN TO NOT TAKE model
                create_scientific_property_form_data(None, scientific_property, scientific_property_customizer)
                for scientific_property, scientific_property_customizer in
                zip(scientific_properties[model_key], scientific_property_customizers[model_key])
                if scientific_property_customizer.displayed
            ]

        scientific_properties_formset = MetadataScientificPropertyInlineFormSetFactory(
            instance=model_instances[i] if model_formset_validity else models[i],
            prefix=model_key,
            data=scientific_properties_post_data,
            initial=scientific_properties_initial_data,  # look at this; I'm passing initial AND data (this is to provide default values to unloaded forms)
            customizers=scientific_property_customizers[model_key],
        )

        if not loaded:
            # manually add default values for management_form (prior to calling is_valid)...
            scientific_properties_post_data[scientific_properties_formset.add_prefix(TOTAL_FORM_COUNT)] = scientific_properties_formset.total_form_count()
            scientific_properties_post_data[scientific_properties_formset.add_prefix(INITIAL_FORM_COUNT)] = scientific_properties_formset.initial_form_count()
            scientific_properties_post_data[scientific_properties_formset.add_prefix(MAX_NUM_FORM_COUNT)] = scientific_properties_formset.absolute_max

        validity += [scientific_properties_formset.is_valid(loaded_prefixes=[form.prefix for form in scientific_properties_formset.forms if loaded])]

        scientific_properties_formsets[model_key] = scientific_properties_formset

    return (validity, model_formset, standard_properties_formsets, scientific_properties_formsets)


def create_edit_subforms_from_data(data, models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix="", subform_min=0, subform_max=1):
    """This creates and validates forms based on POST data"""

    from .forms_edit_model import create_model_form_data, MetadataModelSubFormSetFactory
    from .forms_edit_standard_properties import create_standard_property_form_data, MetadataStandardPropertyInlineSubFormSetFactory
    from .forms_edit_scientific_properties import create_scientific_property_form_data, MetadataScientificPropertyInlineFormSetFactory

    models_data = [create_model_form_data(model, model_customizer) for model in models]

    model_formset = MetadataModelSubFormSetFactory(
        data=data,
        initial=models_data,
        prefix=subform_prefix,
        customizer=model_customizer,
        min=subform_min,
        max=subform_max,
    )

    # because this is a subform and has potentially been added/removed via AJAX
    # the underlying instances may not have been set;
    # this code fixes that
    for model_form in model_formset.forms:
        instance_pk = model_form.instance.pk
        form_pk = model_form.get_current_field_value("id", None)
        if (not instance_pk) and form_pk:
            model_form.instance = MetadataModel.objects.get(pk=form_pk)

    loaded_model_forms = model_formset.get_loaded_forms()
    loaded_model_prefixes = [model_form.prefix for model_form in loaded_model_forms]

    model_formset_validity = model_formset.is_valid(loaded_prefixes=loaded_model_prefixes)
    if model_formset_validity:
        model_instances = model_formset.save(commit=False)

    validity = [model_formset_validity]

    standard_properties_formsets = {}
    scientific_properties_formsets = {}

    for (i, model_form) in enumerate(model_formset.forms):

        subform_prefix = model_form.prefix
        subform_key = u"%s_%s-%s" % (model_form.get_current_field_value("vocabulary_key"), model_form.get_current_field_value("component_key"), i)

        loaded = subform_prefix in loaded_model_prefixes

        standard_properties_data = [
            # TODO: THE 1st ARGUMENT IS MEANT TO BE model BUT IT ISN'T USED
            # TODO: SO I CAN GET AWAY W/ PASSING None
            # TODO: REWRITE THIS FN TO NOT TAKE model

            create_standard_property_form_data(None, standard_property, standard_property_customizer)
            for standard_property, standard_property_customizer in
            zip(standard_properties[subform_key], standard_property_customizers)
            if standard_property_customizer.displayed
        ]

        standard_properties_formsets[subform_prefix] = MetadataStandardPropertyInlineSubFormSetFactory(
            instance=model_instances[i] if model_formset_validity else model_form.instance,
            prefix=subform_prefix,
            data=data,
            initial=standard_properties_data,  # look at this; I'm passing initial AND data (this is to provide default values to unloaded forms)
            customizers=standard_property_customizers,
        )

        loaded_standard_property_prefixes = [form.prefix for form in standard_properties_formsets[subform_prefix].forms if loaded]
        validity += [standard_properties_formsets[subform_prefix].is_valid(loaded_prefixes=loaded_standard_property_prefixes)]

        # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
        if subform_prefix not in scientific_property_customizers:
            scientific_property_customizers[subform_prefix] = []

        scientific_properties_data = [
            # TODO: THE 1st ARGUMENT IS MEANT TO BE model BUT IT ISN'T USED
            # TODO: SO I CAN GET AWAY W/ PASSING None
            # TODO: REWRITE THIS FN TO NOT TAKE model
            create_scientific_property_form_data(None, scientific_property, scientific_property_customizer)
            for scientific_property, scientific_property_customizer in
            zip(scientific_properties[subform_key], scientific_property_customizers[subform_prefix])
            if scientific_property_customizer.displayed
        ]

        scientific_properties_formsets[subform_prefix] = MetadataScientificPropertyInlineFormSetFactory(
            instance=model_instances[i] if model_formset_validity else model_form.instance,
            prefix=subform_prefix,
            data=data,
            initial=scientific_properties_data,  # look at this; I'm passing initial AND data (this is to provide default values to unloaded forms)
            customizers=scientific_property_customizers[subform_prefix],
        )

        loaded_scientific_property_prefixes = [form.prefix for form in scientific_properties_formsets[subform_prefix].forms if loaded]
        validity += [scientific_properties_formsets[subform_prefix].is_valid(loaded_prefixes=loaded_scientific_property_prefixes)]

    return (validity, model_formset, standard_properties_formsets, scientific_properties_formsets)


def get_data_from_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, simulate_post=False):

    data = {}

    model_formset_data = get_data_from_formset(model_formset)
    data.update(model_formset_data)

    for standard_property_formset in standard_properties_formsets.values():
        standard_property_formset_data = get_data_from_formset(standard_property_formset)
        data.update(standard_property_formset_data)

        for standard_property_form in standard_property_formset:
            field_type = standard_property_form.get_current_field_value("field_type")
            customizer = standard_property_form.customizer
            if field_type == MetadataFieldTypes.RELATIONSHIP and customizer.relationship_show_subform:

                (subform_customizer, model_subformset, standard_properties_subformsets, scientific_properties_subformsets) = \
                    standard_property_form.get_subform_tuple()

                subform_data = get_data_from_edit_forms(model_subformset, standard_properties_subformsets, scientific_properties_subformsets, simulate_post=simulate_post)
                data.update(subform_data)

    for scientific_property_formset in scientific_properties_formsets.values():
        scientific_property_formset_data = get_data_from_formset(scientific_property_formset)
        data.update(scientific_property_formset_data)

    # THIS BIT IS REQUIRED TO SIMULATE POST DATA TO VIEWS
    # (IN DJANGO IF A FIELD HAS NO VALUE IT DOES NOT GET INCLUDED UPON FORM SUBMISSION)
    # HOWEVER, WHEN USING THIS FN IN TESTING - WHERE I DO NOT INTEND TO USE THE RETURNED DATA AS A POST -
    # I RUN INTO PROBLEMS B/C THE get_data_from_form / get_data_from_formset SEARCHES FOR DATA FROM ALL FORM FIELDS
    # SO IF I RUN get_data_from_edit_forms WITH THE INTENTION OF USING IT AS A POST,
    # I NEED TO ENSURE THAT I CLEAN THE DATA BEFORE SENDING THE POST
    if simulate_post:
        data_copy = data.copy()
        for key, value in data.iteritems():
            if value == None:
                data_copy.pop(key)
        return data_copy
    else:
        return data


def get_data_from_existing_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets):

    data = {}

    model_formset_data = get_data_from_formset(model_formset)
    data.update(model_formset_data)

    for standard_property_formset in standard_properties_formsets.values():
        standard_property_formset_data = get_data_from_formset(standard_property_formset)
        data.update(standard_property_formset_data)

        for standard_property_form in standard_property_formset:
            field_type = standard_property_form.get_current_field_value("field_type")
            customizer = standard_property_form.customizer
            if field_type == MetadataFieldTypes.RELATIONSHIP and customizer.relationship_show_subform:

                (subform_customizer, model_subformset, standard_properties_subformsets, scientific_properties_subformsets) = \
                    standard_property_form.get_subform_tuple()

                subform_data = get_data_from_edit_forms(model_subformset, standard_properties_subformsets, scientific_properties_subformsets)
                data.update(subform_data)

    for scientific_property_formset in scientific_properties_formsets.values():
        scientific_property_formset_data = get_data_from_formset(scientific_property_formset)
        data.update(scientific_property_formset_data)

    data_copy = data.copy()
    for key, value in data.iteritems():
        if value == None:
            data_copy.pop(key)

    return data_copy


def save_valid_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, model_parent_dictionary={}):

    from .forms_edit_model import save_valid_model_formset
    from .forms_edit_standard_properties import save_valid_standard_properties_formset
    from .forms_edit_scientific_properties import save_valid_scientific_properties_formset

    model_instances = save_valid_model_formset(model_formset, model_parent_dictionary=model_parent_dictionary)

    for standard_properties_formset in standard_properties_formsets.values():
        save_valid_standard_properties_formset(standard_properties_formset)

    for scientific_properties_formset in scientific_properties_formsets.values():
        save_valid_scientific_properties_formset(scientific_properties_formset)

    return model_instances


def save_valid_subforms(model_subform, standard_properties_subformset, scientific_properties_subformset, model_parent_dictionary={}):
    # almost like the above function, but works w/ a single form, formset, formset
    # b/c I deal w/ subforms one form at a time (in case anything has been added/removed via JS)

    # TODO: MAKE THE commit KWARG CONDITIONAL ON WHETHER THE FORM CHANGED (OR IS NEW) TO CUT DOWN ON DB HITS
    # (NOTE, I'LL HAVE TO CHANGE THE LOOP BELOW ONCE I'VE DONE THIS)
    model_instance = model_subform.save(commit=True)

    # for standard_property_formset in standard_properties_formsets.values():
    #     standard_property_instances = standard_property_formset.save(commit=False)
    #     for standard_property_instance in standard_property_instances:
    #         standard_property_instance.save()

    # using zip here is the only way that I managed to get saving to work
    # I have to save via the inlineformset (so that the inline fk gets saved appropriately)
    # but I also need access to the underlying form so I can check certain customization details
    # NOTE THAT force_clean() MUST HAVE BEEN CALLED AFTER VALIDATION BUT PRIOR TO SAVING FOR THIS TO WORK
 #   for standard_property_instance, standard_property_form in zip(standard_properties_subformset.save(commit=True),standard_properties_subformset.forms):


    standard_property_instances = [sp.save(commit=False) for sp in standard_properties_subformset.forms]
    for standard_property_instance, standard_property_form in zip(standard_property_instances, standard_properties_subformset.forms):
    #for standard_property_form in standard_properties_subformset.forms:
        assert(standard_property_instance.name == standard_property_form.get_current_field_value("name"))
        # TODO: NO IDEA WHY I HAVE TO EXPLICITLY ADD THIS HERE
        # BUT NOT IN THE ABOVE save_valid_forms FUNCTION?!?
        standard_property_instance.model = model_instance
        standard_property_instance.save()
        if standard_property_instance.field_type == MetadataFieldTypes.RELATIONSHIP and standard_property_form.customizer.relationship_show_subform:

            (subform_customizer, model_subformset, standard_properties_subformsets, scientific_properties_subformsets) = \
                standard_property_form.get_subform_tuple()

            for model_subform in model_subformset.forms:
                property_key = model_subform.prefix

                subform_has_changed = any([
                    # don't bother checking model_subformset - if the properties have changed, I'll be saving it regardless
                    #model_subform.has_changed(),
                    any([form.has_changed() for form in standard_properties_subformsets[property_key]]),
                    any([form.has_changed() for form in scientific_properties_subformsets[property_key]]),
                ])

                if subform_has_changed:
                    subform_model_instance = save_valid_subforms(model_subform,standard_properties_subformsets[property_key], scientific_properties_subformsets[property_key])
                    standard_property_instance.relationship_value.add(subform_model_instance)
            standard_property_instance.save()

    scientific_property_instances = scientific_properties_subformset.save(commit=False)
    for scientific_property_instance in scientific_property_instances:
        scientific_property_instance.save()

    return model_instance
