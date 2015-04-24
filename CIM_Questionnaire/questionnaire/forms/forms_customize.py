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

from django.forms import ValidationError
from django.forms.formsets import BaseFormSet, ManagementForm, TOTAL_FORM_COUNT, INITIAL_FORM_COUNT, MAX_NUM_FORM_COUNT
from django.utils.translation import ugettext
from django.template.defaultfilters import slugify

from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary
from CIM_Questionnaire.questionnaire.forms.forms_base import MetadataForm, MetadataInlineFormSet, MetadataFormSet
from CIM_Questionnaire.questionnaire.utils import find_in_sequence, get_data_from_form, get_data_from_formset
from CIM_Questionnaire.questionnaire.utils import QuestionnaireError


class MetadataCustomizerForm(MetadataForm):

    pass


class MetadataCustomizerFormSet(MetadataFormSet):

    def _construct_form(self, i, **kwargs):

        if self.is_bound and i < self.initial_form_count():
            # Import goes here instead of module-level because importing
            # django.db has side effects.
            from django.db import connections
            pk_field = self.model._meta.pk
            pk_name = "%s" % pk_field.name
            pk_key = "%s-%s" % (self.add_prefix(i), pk_name)
            # HERE IS THE DIFFERENT BIT
            # (OH, AND THE ABOVE 3 VARIABLES HAVE BEEN MOVED AROUND AND SIMPLIFIED A BIT JUST TO MAKE THE CODE NICER)
            try:
                pk = self.data[pk_key]
                # here is a difference between customizers & editors formsets (note this difference doesn't exist w/ inlineformsets)
                # in the editing form set (ie: model_components), a form is either completely loaded or unloaded
                # but in the customizer form set (ie: category_customizers), a form can have been rendered but still unloaded b/c it is not loaded until edited via AJAX
                # so pk might be found in data but still be empty in which case I have to explicitly set it to "None"
                if not pk:
                    # TODO: IS THIS REALLY GOING ON?  WHY DOESN'T THIS ISSUE CROP UP IN THE EDITOR?
                    pk = None
            except KeyError:
                # if I am here then the pk_key was not found in data
                # given that this is a bound form,
                # this is probably b/c the form is unloaded
                # double-check this...
                initial = self.initial_extra[i]
                if initial["loaded"] == False:
                    # ...and get the pk another way
                    pk = initial[pk_name]
                    kwargs["initial"] = initial
                else:
                    # ...if it failed for some other reason, though, raise an error
                    msg = "Unable to determine pk from form w/ prefix %s" % self.add_prefix(i)
                    raise QuestionnaireError(msg)
            # HERE ENDS THE DIFFERENT BIT
            try:
                pk = pk_field.get_db_prep_lookup('exact', pk,
                    connection=connections[self.get_queryset().db])
            except:
                import ipdb; ipdb.set_trace()
            if isinstance(pk, list):
                pk = pk[0]
            kwargs['instance'] = self._existing_object(pk)
        if i < self.initial_form_count() and "instance" not in kwargs:
            try:
                kwargs['instance'] = self.get_queryset()[i]
            except IndexError:
                # if this formset has changed based on add/delete via AJAX
                # then the underlying queryset may not have updated
                # if so - since I've already worked out the pk above - just get the model directly
                # (note that in the case of new models, pk will be None and this will return an empty model)
                # (which is the desired behavior anyway - see this same bit of code for MetadataEditingFormSet)
                model_class = self.model
                kwargs['instance'] = model_class.objects.get(pk=pk)
        if i >= self.initial_form_count() and self.initial_extra:
            # Set initial values for extra forms
            try:
                kwargs['initial'] = self.initial_extra[i-self.initial_form_count()]
            except IndexError:
                pass
        # rather than call _construct_form() from super() here (which winds up calling BaseModelFormset),
        # I explicitly call it from BaseFormSet;
        # the former repeates the above "get instance" code w/out handling loaded & unloaded forms
        # since I've already done that, I just want to call the code that builds the actual form
        form = BaseFormSet._construct_form(self, i, **kwargs)

        return form


    # def _construct_form(self, i, **kwargs):
    #
    #     if self.is_bound and i < self.initial_form_count():
    #         # Import goes here instead of module-level because importing
    #         # django.db has side effects.
    #         from django.db import connections
    #         pk_field = self.model._meta.pk
    #         pk_name = "%s" % pk_field.name
    #         pk_key = "%s-%s" % (self.add_prefix(i), pk_name)
    #         # HERE IS THE DIFFERENT BIT
    #         # (OH, AND THE ABOVE 3 VARIABLES HAVE BEEN MOVED AROUND AND SIMPLIFIED A BIT JUST TO MAKE THE CODE NICER)
    #         try:
    #             pk = self.data[pk_key]
    #         except KeyError:  # MultiValueDictKeyError:
    #             # if I am here then the pk_key was not found in data
    #             # given that this is a bound form,
    #             # this is probably b/c the form is unloaded
    #             # double-check this...
    #             initial = self.initial_extra[i]
    #             if initial["loaded"] == False:
    #                 # ...and get the pk another way
    #                 pk = initial[pk_name]
    #                 kwargs["initial"] = initial
    #             else:
    #                 # ...if it failed for some other reason, though, raise an error
    #                 msg = "Unable to determine pk from form w/ prefix %s" % self.add_prefix(i)
    #                 raise QuestionnaireError(msg)
    #         if not pk:
    #             # since I am including the "id" field (for other reasons)
    #             # if this is a _new_ rather than _existing_ model
    #             # then that field will be blank and will be cleaned as u''
    #             # convert that to None, so that get_db_prep_lookup below returns None
    #             pk = None
    #         # HERE ENDS THE DIFFERENT BIT
    #         pk = pk_field.get_db_prep_lookup('exact', pk,
    #             connection=connections[self.get_queryset().db])
    #         if isinstance(pk, list):
    #             pk = pk[0]
    #         kwargs['instance'] = self._existing_object(pk)
    #     # if i < self.initial_form_count() and not kwargs.get('instance'):
    #     if i < self.initial_form_count() and "instance" not in kwargs:
    #         try:
    #             kwargs['instance'] = self.get_queryset()[i]
    #         except IndexError:
    #             # if this formset has changed based on add/delete via AJAX
    #             # then the underlying queryset may not have updated
    #             # if so - since I've already worked out the pk above - just get the model directly
    #             # (note that in the case of new models, pk will be None and this will return an empty model)
    #             # (which is the desired behavior anyway - see this same bit of code for MetadataEditingFormSet)
    #             model_class = self.model
    #             kwargs['instance'] = model_class.objects.get(pk=pk)
    #
    #     if i >= self.initial_form_count() and self.initial_extra:
    #         # Set initial values for extra forms
    #         try:
    #             kwargs['initial'] = self.initial_extra[i-self.initial_form_count()]
    #         except IndexError:
    #             pass
    #
    #     # rather than call _construct_form() from super() here (which winds up calling BaseModelFormset),
    #     # I explicitly call it from BaseFormSet;
    #     # the former repeates the above "get instance" code w/out handling loaded & unloaded forms
    #     # since I've already done that, I just want to call the code that builds the actual form
    #     form = BaseFormSet._construct_form(self, i, **kwargs)
    #
    #     return form

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
            # additionally, note that in create_customizer_forms_from_data,
            # I manually update the data dictionary to include appropriate values for the management form
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
    # (note my use of get_number_of_forms in total_form_count,
    # which varies according to whether this is a model formset or a property formset)

    def total_form_count(self):
        """Returns the total number of forms in this FormSet."""
        if self.is_bound:
            try:
                return min(self.management_form.cleaned_data[TOTAL_FORM_COUNT], self.absolute_max)
            except ValidationError:
                # HERE IS THE NEW CODE
                # (KEPT THE ABOVE TRY CLAUSE IN-CASE A FORM WAS ADDED BY JS)
                # (IN WHICH CASE IT MUST HAVE BEEN LOADED AND THE TRY WILL NOT FAIL)
                return min(self.get_number_of_forms(), self.absolute_max)
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
        # a MetadataInlineFormset can be created in 3 ways:
        # 1) via new models, in which case "initial" will have been passed
        # 2) via an existing queryset, in which case "queryset" will have been passed
        # 3) via data, in which case "data" will have been passed
        # _however_ data may be missing depending on whether or not the form(s) were loaded
        # b/c of that an extra "initial" argument is passed to the factory fns to handle unloaded forms
        # FOR BOUND FORMS, THAT ARGUMENT IS STORED IN self.initial_extra (THIS TOOK A WHILE TO FIGURE OUT!)

        if self.queryset:
            return len(self.queryset)
        elif self.initial:
            return len(self.initial)
        elif self.is_bound and self.initial_extra:
            return len(self.initial_extra)
        else:
            return 0


class MetadataCustomizerInlineFormSet(MetadataInlineFormSet):

    # just using this class to automatically sort the forms based on the field order

    def __iter__(self):
        """Yields the forms in the order they should (initially) be rendered"""
        forms = list(self.forms)
        try:
            forms.sort(key=lambda x: x.initial["order"])
        except KeyError:
            forms.sort(key=lambda x: x.data["%s-order" % x.prefix])
        return iter(forms)

    def __getitem__(self, index):
        """Returns the form at the given index, based on the rendering order"""
        forms = list(self.forms)
        try:
            forms.sort(key = lambda x: x.initial["order"])
        except KeyError:
            forms.sort(key = lambda x: x.data["%s-order" % x.prefix])
        return forms[index]

    def _construct_form(self, i, **kwargs):

        if self.is_bound and i < self.initial_form_count():
            # Import goes here instead of module-level because importing
            # django.db has side effects.
            from django.db import connections
            pk_field = self.model._meta.pk
            pk_name = "%s" % pk_field.name
            pk_key = "%s-%s" % (self.add_prefix(i), pk_name)
            # HERE IS THE DIFFERENT BIT
            # (OH, AND THE ABOVE 3 VARIABLES HAVE BEEN MOVED AROUND AND SIMPLIFIED A BIT JUST TO MAKE THE CODE NICER)
            try:
                pk = self.data[pk_key]
            except KeyError:  # MultiValueDictKeyError:
                # if I am here then the pk_key was not found in data
                # given that this is a bound form,
                # this is probably b/c the form is unloaded
                # double-check this...
                initial = self.initial_extra[i]
                if initial["loaded"] == False:
                    # ...and get the pk another way
                    pk = initial[pk_name]
                    kwargs["initial"] = initial
                else:
                    # ...if it failed for some other reason, though, raise an error
                    msg = "Unable to determine pk from form w/ prefix %s" % self.add_prefix(i)
                    raise QuestionnaireError(msg)
            if not pk:
                # since I am including the "id" field (for other reasons)
                # if this is a _new_ rather than _existing_ model
                # then that field will be blank and will be cleaned as u''
                # convert that to None, so that get_db_prep_lookup below returns None
                pk = None
            # HERE ENDS THE DIFFERENT BIT
            pk = pk_field.get_db_prep_lookup('exact', pk,
                connection=connections[self.get_queryset().db])
            if isinstance(pk, list):
                pk = pk[0]
            kwargs['instance'] = self._existing_object(pk)
        # if i < self.initial_form_count() and not kwargs.get('instance'):
        if i < self.initial_form_count() and "instance" not in kwargs:
            try:
                kwargs['instance'] = self.get_queryset()[i]
            except IndexError:
                # if this formset has changed based on add/delete via AJAX
                # then the underlying queryset may not have updated
                # if so - since I've already worked out the pk above - just get the model directly
                # (note that in the case of new models, pk will be None and this will return an empty model)
                # (which is the desired behavior anyway - see this same bit of code for MetadataEditingFormSet)
                model_class = self.model
                kwargs['instance'] = model_class.objects.get(pk=pk)

        if i >= self.initial_form_count() and self.initial_extra:
            # Set initial values for extra forms
            try:
                kwargs['initial'] = self.initial_extra[i-self.initial_form_count()]
            except IndexError:
                pass

        # rather than call _construct_form() from super() here (which winds up calling BaseModelFormset),
        # I explicitly call it from BaseFormSet;
        # the former repeates the above "get instance" code w/out handling loaded & unloaded forms
        # since I've already done that, I just want to call the code that builds the actual form
        form = BaseFormSet._construct_form(self, i, **kwargs)

        if self.save_as_new:
            # Remove the primary key from the form's data, we are only
            # creating new instances
            form.data[form.add_prefix(self._pk_field.name)] = None

            # Remove the foreign key from the form's data
            # TODO: WHY IS THIS HAPPENING?
            # TODO: I ASSUME B/C INLINE_FORMSETS AUTOMATICALLY HANDLE FK FIELDS?
            form.data[form.add_prefix(self.fk.name)] = None

        # Set the fk value here so that the form can do its validation.
        setattr(form.instance, self.fk.get_attname(), self.instance.pk)

        return form

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
            # additionally, note that in create_edit_forms_from_data,
            # I manually update the data dictionary to include appropriate values for the management form
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
    # (note my use of get_number_of_forms in total_form_count,
    # which varies according to whether this is a model formset or a property formset)

    def total_form_count(self):
        """Returns the total number of forms in this FormSet."""
        if self.is_bound:
            try:
                return min(self.management_form.cleaned_data[TOTAL_FORM_COUNT], self.absolute_max)
            except ValidationError:
                # HERE IS THE NEW CODE
                # (KEPT THE ABOVE TRY CLAUSE IN-CASE A FORM WAS ADDED BY JS)
                # (IN WHICH CASE IT MUST HAVE BEEN LOADED AND THE TRY WILL NOT FAIL)
                return min(self.get_number_of_forms(), self.absolute_max)
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
        # a MetadataInlineFormset can be created in 3 ways:
        # 1) via new models, in which case "initial" will have been passed
        # 2) via an existing queryset, in which case "queryset" will have been passed
        # 3) via data, in which case "data" will have been passed
        # _however_ data may be missing depending on whether or not the form(s) were loaded
        # b/c of that an extra "initial" argument is passed to the factory fns to handle unloaded forms
        # FOR BOUND FORMS, THAT ARGUMENT IS STORED IN self.initial_extra (THIS TOOK A WHILE TO FIGURE OUT!)

        if self.queryset:
            return len(self.queryset)
        elif self.initial:
            return len(self.initial)
        elif self.is_bound and self.initial_extra:
            return len(self.initial_extra)
        else:
            return 0


def create_new_customizer_forms_from_models(model_customizer, standard_category_customizers, standard_property_customizers, scientific_category_customizers, scientific_property_customizers, vocabularies_to_customize=MetadataVocabulary.objects.none(), is_subform=False):

    from .forms_customize_model import create_model_customizer_form_data, MetadataModelCustomizerForm, MetadataModelCustomizerSubForm
    from .forms_customize_categories import create_standard_category_customizer_form_data, MetadataStandardCategoryCustomizerInlineFormSetFactory
    from .forms_customize_categories import create_scientific_category_customizer_form_data, MetadataScientificCategoryCustomizerInlineFormSetFactory
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

    standard_category_customizers_data = [
        create_standard_category_customizer_form_data(model_customizer, standard_category_customizer)
        for standard_category_customizer in standard_category_customizers
    ]

    standard_category_customizer_formset = MetadataStandardCategoryCustomizerInlineFormSetFactory(
        instance=model_customizer,
        initial=standard_category_customizers_data,
        extra=len(standard_category_customizers_data),
        prefix=u"standard_categories"
    )

    standard_property_customizers_data = [create_standard_property_customizer_form_data(model_customizer, standard_property_customizer) for standard_property_customizer in standard_property_customizers]
    standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
        instance=model_customizer,
        initial=standard_property_customizers_data,
        extra=len(standard_property_customizers_data),
        categories=standard_category_customizers,
    )

    scientific_category_customizer_formsets = {}
    for vocabulary_key, scientific_category_customizer_dict in scientific_category_customizers.iteritems():
        scientific_category_customizer_formsets[vocabulary_key] = {}
        for component_key, scientific_category_customizer_list in scientific_category_customizer_dict.iteritems():
            scientific_category_customizers_data = [
                create_scientific_category_customizer_form_data(model_customizer, scientific_category_customizer)
                for scientific_category_customizer in scientific_category_customizer_list
            ]
            scientific_category_customizer_formset = MetadataScientificCategoryCustomizerInlineFormSetFactory(
                instance=model_customizer,
                initial=scientific_category_customizers_data,
                extra=len(scientific_category_customizers_data),
                prefix=u"%s_%s_scientific_categories" % (vocabulary_key, component_key)
            )
            scientific_category_customizer_formsets[vocabulary_key][component_key] = scientific_category_customizer_formset

    scientific_property_customizer_formsets = {}
    for vocabulary_key, scientific_property_customizer_dict in scientific_property_customizers.iteritems():
        scientific_property_customizer_formsets[vocabulary_key] = {}
        for component_key, scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
            model_key = u"%s_%s" % (vocabulary_key, component_key)
            scientific_property_customizers_data = [
                create_scientific_property_customizer_form_data(model_customizer, scientific_property_customizer)
                for scientific_property_customizer in scientific_property_customizers[vocabulary_key][component_key]
            ]
            scientific_property_customizer_formset = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                instance=model_customizer,
                initial=scientific_property_customizers_data,
                extra=len(scientific_property_customizers_data),
                prefix=model_key,
                categories=scientific_category_customizers[vocabulary_key][component_key]
            )
            scientific_property_customizer_formsets[vocabulary_key][component_key] = scientific_property_customizer_formset

    return (model_customizer_form, standard_category_customizer_formset, standard_property_customizer_formset, scientific_category_customizer_formsets, scientific_property_customizer_formsets, model_customizer_vocabularies_formset)


def create_existing_customizer_forms_from_models(model_customizer, standard_category_customizers, standard_property_customizers, scientific_category_customizers, scientific_property_customizers, vocabularies_to_customize=MetadataVocabulary.objects.none(), is_subform=False):

    # TODO: CAN I GET RID OF THE NEED FOR "create_model_customizer_form_data"?
    from .forms_customize_model import create_model_customizer_form_data, MetadataModelCustomizerForm, MetadataModelCustomizerSubForm
    from .forms_customize_categories import MetadataStandardCategoryCustomizerInlineFormSetFactory
    from .forms_customize_categories import MetadataScientificCategoryCustomizerInlineFormSetFactory
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

    standard_category_customizer_formset = MetadataStandardCategoryCustomizerInlineFormSetFactory(
        instance=model_customizer,
        queryset=standard_category_customizers,
        prefix=u"standard_categories",
    )

    standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
        instance=model_customizer,
        queryset=standard_property_customizers,
        # don't pass extra; w/ existing (queryset) models, extra ought to be 0
        # extra=len(standard_property_customizers),
        categories=standard_category_customizers,
    )

    scientific_category_customizer_formsets = {}
    for vocabulary_key, scientific_category_customizer_dict in scientific_category_customizers.iteritems():
        scientific_category_customizer_formsets[vocabulary_key] = {}
        for component_key, scientific_category_customizer_list in scientific_category_customizer_dict.iteritems():
            scientific_category_customizer_formset = MetadataScientificCategoryCustomizerInlineFormSetFactory(
                instance=model_customizer,
                queryset=scientific_category_customizer_list,
                prefix=u"%s_%s_scientific_categories" % (vocabulary_key, component_key),
            )
            scientific_category_customizer_formsets[vocabulary_key][component_key] = scientific_category_customizer_formset

    scientific_property_customizer_formsets = {}
    for vocabulary_key, scientific_property_customizer_dict in scientific_property_customizers.iteritems():
        scientific_property_customizer_formsets[vocabulary_key] = {}
        for component_key, scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
            scientific_property_customizer_formset = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                instance=model_customizer,
                queryset=scientific_property_customizer_list,
                prefix=u"%s_%s" % (vocabulary_key, component_key),
                categories=scientific_category_customizers[vocabulary_key][component_key],
            )
            scientific_property_customizer_formsets[vocabulary_key][component_key] = scientific_property_customizer_formset

    return (model_customizer_form, standard_category_customizer_formset, standard_property_customizer_formset, scientific_category_customizer_formsets, scientific_property_customizer_formsets, model_customizer_vocabularies_formset)


def create_customizer_forms_from_data(data, model_customizer, standard_category_customizers, standard_property_customizers, scientific_category_customizers, scientific_property_customizers, vocabularies_to_customize=MetadataVocabulary.objects.none(), is_subform=False, subform_prefix=""):
    """This creates and validates forms based on POST data"""

    from .forms_customize_model import create_model_customizer_form_data, MetadataModelCustomizerForm, MetadataModelCustomizerSubForm
    from .forms_customize_vocabularies import create_model_customizer_vocabulary_form_data, MetadataModelCustomizerVocabularyFormSetFactory
    from .forms_customize_categories import create_standard_category_customizer_form_data, MetadataStandardCategoryCustomizerInlineFormSetFactory
    from .forms_customize_standard_properties import create_standard_property_customizer_form_data, MetadataStandardPropertyCustomizerInlineFormSetFactory
    from .forms_customize_categories import create_scientific_category_customizer_form_data, MetadataScientificCategoryCustomizerInlineFormSetFactory
    from .forms_customize_scientific_properties import create_scientific_property_customizer_form_data, MetadataScientificPropertyCustomizerInlineFormSetFactory

    if is_subform:
        if subform_prefix:
            model_customizer_form = MetadataModelCustomizerSubForm(data, instance=model_customizer, all_vocabularies=vocabularies_to_customize, prefix=subform_prefix)
        else:
            model_customizer_form = MetadataModelCustomizerSubForm(data, instance=model_customizer, all_vocabularies=vocabularies_to_customize)
    else:
        model_customizer_form = MetadataModelCustomizerForm(data, instance=model_customizer, all_vocabularies=vocabularies_to_customize)
    model_customizer_form_validity = model_customizer_form.is_valid()  # MetadataForm.is_valid() has a default kwarg "loaded=True"; model_customizer_form is always loaded

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

        # TODO: category customizers

        standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance=model_customizer_instance if model_customizer_form_validity else model_customizer,
            data=data,
            categories=standard_category_customizers,
            # TODO: WORKING OUT THE APPROPRIATE PREFIX SHOULD BE AUTOMATIC!
            prefix=u"standard_property-%s" % subform_prefix
        )

    else:

        standard_category_customizer_formset = MetadataStandardCategoryCustomizerInlineFormSetFactory(
            instance=model_customizer_instance if model_customizer_form_validity else model_customizer,
            data=data,
            prefix="standard_categories",
        )

        standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance=model_customizer_instance if model_customizer_form_validity else model_customizer,
            data=data,
            categories=standard_category_customizers,
        )

    # standard_category_customizer_forms are always loaded (it's only scientific categories & properties that are loaded-on-demand)
    loaded_standard_category_forms = standard_category_customizer_formset.get_loaded_forms()
    loaded_prefixes = [form.prefix for form in loaded_standard_category_forms]
    validity += [standard_category_customizer_formset.is_valid(loaded_prefixes=loaded_prefixes)]

    # standard_property_customizer_forms are always loaded (it's only scientific categories & properties that are loaded-on-demand)
    loaded_standard_property_forms = standard_property_customizer_formset.get_loaded_forms()
    loaded_prefixes = [form.prefix for form in loaded_standard_property_forms]
    validity += [standard_property_customizer_formset.is_valid(loaded_prefixes=loaded_prefixes)]

    scientific_category_customizer_formsets = {}
    for vocabulary_key, scientific_category_customizer_dict in scientific_category_customizers.iteritems():
        scientific_category_customizer_formsets[vocabulary_key] = {}
        for component_key, scientific_category_customizer_list in scientific_category_customizer_dict.iteritems():

            # unlike w/ the editing forms, I need to create the form 1st
            # and _then_ work out whether or not it's loaded

            scientific_category_customizers_data = [
                create_scientific_category_customizer_form_data(model_customizer, scientific_category_customizer)
                for scientific_category_customizer in scientific_category_customizer_list
            ]
            scientific_category_customizer_formset = MetadataScientificCategoryCustomizerInlineFormSetFactory(
                instance=model_customizer_instance if model_customizer_form_validity else model_customizer,
                initial=scientific_category_customizers_data,
                data=data,
                prefix=u"%s_%s_scientific_categories" % (vocabulary_key, component_key)
            )

            loaded_scientific_category_property_forms = scientific_category_customizer_formset.get_loaded_forms()
            loaded_prefixes = [form.prefix for form in loaded_scientific_category_property_forms]
            loaded = True if loaded_prefixes else False  # the entire formset is loaded/unloaded, rather than individual forms

            if not loaded:
                # manually add default values for management form (prior to calling is_valid)...
                scientific_category_customizer_formset.data[scientific_category_customizer_formset.add_prefix(TOTAL_FORM_COUNT)] = \
                    scientific_category_customizer_formset.total_form_count()
                scientific_category_customizer_formset.data[scientific_category_customizer_formset.add_prefix(INITIAL_FORM_COUNT)] = \
                    scientific_category_customizer_formset.initial_form_count()
                scientific_category_customizer_formset.data[scientific_category_customizer_formset.add_prefix(MAX_NUM_FORM_COUNT)] = \
                    scientific_category_customizer_formset.absolute_max

            if vocabulary_key in active_vocabulary_keys:
                validity += [scientific_category_customizer_formset.is_valid(loaded_prefixes=loaded_prefixes)]

            scientific_category_customizer_formsets[vocabulary_key][component_key] = scientific_category_customizer_formset

    scientific_property_customizer_formsets = {}
    for vocabulary_key, scientific_property_customizer_dict in scientific_property_customizers.iteritems():
        scientific_property_customizer_formsets[vocabulary_key] = {}
        for component_key, scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
            model_key = u"%s_%s" % (vocabulary_key, component_key)

            # unlike w/ the editing forms, I need to create the form 1st
            # and _then_ work out whether or not it's loaded

            scientific_property_customizer_formset_data = [
                create_scientific_property_customizer_form_data(model_customizer, scientific_property_customizer)
                for scientific_property_customizer in scientific_property_customizer_list
            ]

            if is_subform and subform_prefix:
                scientific_property_customizer_formset = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                    instance=model_customizer_instance if model_customizer_form_validity else model_customizer,
                    data=data,
                    initial=scientific_property_customizer_formset_data,
                    categories=scientific_category_customizers[vocabulary_key][component_key],
                    prefix=u"%s-%s" % (model_key, subform_prefix),
                )
            else:
                scientific_property_customizer_formset = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                    instance=model_customizer_instance if model_customizer_form_validity else model_customizer,
                    data=data,
                    initial=scientific_property_customizer_formset_data,
                    categories=scientific_category_customizers[vocabulary_key][component_key],
                    prefix=model_key,
                )

            loaded_forms = scientific_property_customizer_formset.get_loaded_forms()
            loaded_prefixes = [form.prefix for form in loaded_forms]
            loaded = True if loaded_prefixes else False  # the entire formset is loaded/unloaded, rather than individual forms

            if not loaded:
                # manually add default values for management form (prior to calling is_valid)...
                scientific_property_customizer_formset.data[scientific_property_customizer_formset.add_prefix(TOTAL_FORM_COUNT)] = \
                    scientific_property_customizer_formset.total_form_count()
                scientific_property_customizer_formset.data[scientific_property_customizer_formset.add_prefix(INITIAL_FORM_COUNT)] = \
                    scientific_property_customizer_formset.initial_form_count()
                scientific_property_customizer_formset.data[scientific_property_customizer_formset.add_prefix(MAX_NUM_FORM_COUNT)] = \
                    scientific_property_customizer_formset.absolute_max

            if vocabulary_key in active_vocabulary_keys:
                validity += [scientific_property_customizer_formset.is_valid(loaded_prefixes=loaded_prefixes)]

            scientific_property_customizer_formsets[vocabulary_key][component_key] = scientific_property_customizer_formset

    return (validity, model_customizer_form, standard_category_customizer_formset, standard_property_customizer_formset, scientific_category_customizer_formsets, scientific_property_customizer_formsets, model_customizer_vocabularies_formset)


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


def save_valid_forms(model_customizer_form, standard_category_customizer_formset, standard_property_customizer_formset, scientific_category_customizer_formsets, scientific_property_customizer_formsets, model_customizer_vocabularies_formset):
    from .forms_customize_categories import save_valid_categories_formset

    model_customizer_instance = model_customizer_form.save(commit=True)

    if model_customizer_vocabularies_formset:
        model_customizer_vocabularies_formset.save()
        active_vocabulary_forms = model_customizer_vocabularies_formset.get_active_forms()
        active_vocabularies = \
            [active_vocabulary_form.cleaned_data["vocabulary"]
             for active_vocabulary_form in active_vocabulary_forms
             ]
    else:
        active_vocabularies = []

    # save the standard category customizers...
    standard_category_customizer_instances = save_valid_categories_formset(standard_category_customizer_formset)
    # standard_category_customizer_formset.save(commit=True)
    # standard_category_customizer_instances = model_customizer_instance.standard_property_category_customizers.all()

    # save the standard property customizers...
    # (this is pretty straightforward, since standard categories & properties are always loaded)
    standard_property_customizer_instances = standard_property_customizer_formset.save(commit=False)
    for standard_property_customizer_instance in standard_property_customizer_instances:
        category_key = slugify(standard_property_customizer_instance.category_name)
        category = find_in_sequence(lambda c: c.key == category_key, standard_category_customizer_instances)
        standard_property_customizer_instance.category = category
        standard_property_customizer_instance.model_customizer = model_customizer_instance
        standard_property_customizer_instance.save()

    # save the scientific category & scientific property customizers...
    for vocabulary in active_vocabularies:
        vocabulary_key = vocabulary.get_key()
        for component in vocabulary.component_proxies.all():
            component_key = component.get_key()

            # TODO: CHECK THAT THIS WORKS FOR ADDED/DELETED CATEGORIES
            scientific_category_customizer_instances = save_valid_categories_formset(scientific_category_customizer_formsets[vocabulary_key][component_key])

            scientific_property_customizer_instances = scientific_property_customizer_formsets[vocabulary_key][component_key].save(commit=False)
            for scientific_property_customizer_instance in scientific_property_customizer_instances:
                category_key = slugify(scientific_property_customizer_instance.category_name)
                category = find_in_sequence(lambda c: c.key == category_key, scientific_category_customizer_instances)
                scientific_property_customizer_instance.category = category
                scientific_property_customizer_instance.model_customizer = model_customizer_instance
                scientific_property_customizer_instance.save()

    return model_customizer_instance