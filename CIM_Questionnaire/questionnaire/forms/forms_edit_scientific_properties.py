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
.. module:: forms_edit_scientific_properties

classes for CIM Questionnaire scientific_properties edit form creation & manipulation
"""

import time
from django.utils.functional import curry
from django.forms.models import inlineformset_factory

from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes, MetadataAtomicFieldTypes
from CIM_Questionnaire.questionnaire.fields import METADATA_ATOMICFIELD_MAP, EMPTY_CHOICE, NULL_CHOICE, OTHER_CHOICE
from CIM_Questionnaire.questionnaire.forms.forms_edit import MetadataEditingForm, MetadataEditingInlineFormSet
from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel, MetadataScientificProperty
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataScientificPropertyProxy
from CIM_Questionnaire.questionnaire.utils import get_initial_data, model_to_data, find_in_sequence, update_field_widget_attributes, set_field_widget_attributes


def create_scientific_property_form_data(model, scientific_property, scientific_property_customizer=None):

    scientific_property_form_data = model_to_data(
        scientific_property,
        exclude=["model", ],  # no need to pass model, since this is handled by virtue of being an "inline" formset
        include={
            "last_modified": time.strftime("%c"),
            "loaded": False,
        }
    )

    if scientific_property_customizer:

        if scientific_property_customizer.is_enumeration:
            # enumeration fields...
            current_enumeration_value = scientific_property_form_data["enumeration_value"]
            if current_enumeration_value:
                if scientific_property_customizer.enumeration_multi:
                    scientific_property_form_data["enumeration_value"] = current_enumeration_value.split("|")

        else:
            # atomic fields...
            pass

    return scientific_property_form_data


def save_valid_scientific_properties_formset(scientific_properties_formset):

    scientific_property_instances = []
    for scientific_property_instance, scientific_property_form in zip(scientific_properties_formset.save(commit=False), scientific_properties_formset.forms):
        # want to have access to both the instance and the customizer
        # in case I need to check customization details
        assert(scientific_property_instance.name == scientific_property_form.get_current_field_value("name"))

        # TODO: UNLOADED INLINE_FORMSETS ARE NOT SAVING THE FK FIELD APPROPRIATELY
        # THIS MAKES NO SENSE, B/C THE INDIVIDUAL INSTANCES DO HAVE THE "model" FIELD SET
        # BUT THAT CORRESPONDING MetadataModel HAS NO VALUES FOR "standard_properties"
        # RE-SETTING IT AND RE-SAVING IT SEEMS TO DO THE TRICK
        fk_field_name = scientific_properties_formset.fk.name
        fk_model = getattr(scientific_property_instance, fk_field_name)
        setattr(scientific_property_instance, fk_field_name, fk_model)
        scientific_property_instance.save()

        scientific_property_instances.append(scientific_property_instance)

    return scientific_property_instances


class MetadataScientificPropertyForm(MetadataEditingForm):

    class Meta:
        model = MetadataScientificProperty

    # since I am only explicitly displaying the "value_field" I have to be sure to add any fields
    # that the django form init/saving process depends upon to this list
    _hidden_fields = ["proxy", "field_type", "is_enumeration", "category_key", "name", "order", ]

    # list of fields that will be the same for all members of a formset; thus I can cache the query
    cached_fields = []

    def __init__(self, *args, **kwargs):

        # customizers was passed in via curry() in the factory function below
        customizers = kwargs.pop("customizers", None)

        # RIGHT, THIS CAUSED AN AWFUL LOT OF CONFUSION
        # THE CALL TO super() CAN TAKE A "customizer" ARGUMENT
        # BUT I CAN ONLY FIND THAT CUSTOMIZER BY MATCHING IT AGAINST THE VALUE OF "proxy"
        # THAT REQUIRES CALLING get_current_field_value() WHICH CHECKS THE PREFIX OF A FORM
        # BUT THAT PREFIX - AND SOME OTHER THINGS TOO - IS ONLY SET FROM DEEP W/IN THE __init__ FN
        # OF A BASE CLASS; SO I CALL super FIRST W/OUT A "customizer" ARGUMENT AND THEN CUSTOMIZE
        # AT THE END OF THIS __init__ FN

        super(MetadataScientificPropertyForm, self).__init__(*args, **kwargs)

        if customizers:
            proxy_pk = int(self.get_current_field_value("proxy"))
            customizer = find_in_sequence(lambda c: c.proxy.pk == proxy_pk, customizers)
            assert(customizer.name == self.get_current_field_value("name"))  # this is new code; just make sure it works
        else:
            customizer = None

        is_enumeration = self.get_current_field_value("is_enumeration", False)

        if self.instance.pk and is_enumeration:
            # ordinarily, this is done in create_scientific_property_form_data above
            # but if this is an existing model, I still need to do this jiggery-pokery someplace
            current_enumeration_value = self.get_current_field_value("enumeration_value")
            if isinstance(current_enumeration_value, basestring) and customizer.enumeration_multi:
                self.initial["enumeration_value"] = current_enumeration_value.split("|")

        if not is_enumeration:
            update_field_widget_attributes(self.fields["atomic_value"], {"onchange": "copy_value(this,'%s-scientific_property_value');" % self.prefix})
            update_field_widget_attributes(self.fields["atomic_value"], {"class": "atomic_value"})
        else:
            update_field_widget_attributes(self.fields["enumeration_value"], {"class": "multiselect"})

        if customizer:
            # HUH, WHY AM I CALLING THIS EXPLICITLY HERE, WHEN IT OUGHT TO BE CALLED AUTOMATICALLY IN super() ABOVE?
            # B/C customizer IS NOT PASSED TO super() B/C IT NEEDS TO BE FOUND BASED ON THE CURRENT PROXY
            # WHICH GETS RETURNED BY get_current_field_value()
            # WHICH HAS TO HAVE THIS FORM MOSTLY SET UP BEFORE IT WILL WORK
            # WHICH HAPPENS IN THE CALL TO super()
            # (SEE ABOVE)
            self.customize(customizer)

    def customize(self, customizer):

        # customization is done in the form and in the template

        value_field_name = self.get_value_field_name()

        self.fields[value_field_name].help_text = customizer.documentation

        if not customizer.is_enumeration:
            atomic_type = customizer.atomic_type
            if atomic_type:
                if atomic_type != MetadataAtomicFieldTypes.DEFAULT:
                    custom_widget_class = METADATA_ATOMICFIELD_MAP[atomic_type][0]
                    custom_widget_args = METADATA_ATOMICFIELD_MAP[atomic_type][1]
                    self.fields["atomic_value"].widget = custom_widget_class(**custom_widget_args)
                update_field_widget_attributes(self.fields["atomic_value"], {"class": atomic_type.lower()})

        else:
            widget_attributes = {"class": "multiselect"}
            all_enumeration_choices = customizer.enumerate_choices()
            if customizer.enumeration_nullable:
                all_enumeration_choices += NULL_CHOICE
                widget_attributes["class"] += " nullable"
            if customizer.enumeration_open:
                all_enumeration_choices += OTHER_CHOICE
                widget_attributes["class"] += " open"
            if customizer.enumeration_multi:
                self.fields["enumeration_value"].set_choices(all_enumeration_choices, multi=True)
            else:
                all_enumeration_choices = EMPTY_CHOICE + all_enumeration_choices
                self.fields["enumeration_value"].set_choices(all_enumeration_choices, multi=False)

            update_field_widget_attributes(self.fields["enumeration_value"], widget_attributes)
            update_field_widget_attributes(self.fields["enumeration_other_value"], {"class": "other"})

        # extra_attributes...
        if not customizer.edit_extra_standard_name:
            update_field_widget_attributes(self.fields["extra_standard_name"], {"class": "readonly", "readonly": "readonly"})

        if not customizer.edit_extra_description:
            update_field_widget_attributes(self.fields["extra_description"], {"class": "readonly", "readonly": "readonly"})

        if not customizer.edit_extra_units:
            update_field_widget_attributes(self.fields["extra_units"], {"class": "readonly", "readonly": "readonly"})

        set_field_widget_attributes(self.fields["extra_description"], {"cols": "60", "rows": "4"})

        self.customizer = customizer

    def get_value_field_name(self):

        is_enumeration = self.get_current_field_value("is_enumeration", False)

        if not is_enumeration:
            return "atomic_value"
        else:
            return "enumeration_value"

    def get_value_field(self):
        value_field_name = self.get_value_field_name()
        value_fields = self.get_fields_from_list([value_field_name])
        try:
            return value_fields[0]
        except:
            return None

    def has_changed(self):
        # ScientificPropertyForms for now should always be saved, as w/ top-level StandardPropertyForms
        # if I do not override has_changed, then the call to formset.save_existing_forms
        # (which happens when saving an unloaded formset), will only return some of the forms
        # and the loop in save_valid_scientific_properties_formset will be out-of-sync
        # see ticket #246 for more info
        return True


class MetadataScientificPropertyInlineFormSet(MetadataEditingInlineFormSet):

    pass

    # def _construct_form(self, i, **kwargs):
    #
    #     # no longer dealing w/ iterators and keeping everything in order
    #     # instead using find_in_sequence in the __init__ method
    #     # if self.customizers:
    #     #     try:
    #     #         kwargs["customizer"] = next(self.customizers)
    #     #     except StopIteration:
    #     #         # don't worry about not having a customizer for the extra form
    #     #         pass
    #
    #     form = super(MetadataScientificPropertyInlineFormSet, self)._construct_form(i, **kwargs)
    #
    #     for cached_field_name in form.cached_fields:
    #         cached_field = form.fields[cached_field_name]
    #         cached_field_key = u"%s_%s" % (self.prefix, cached_field_name)
    #         cached_field.cache_choices = True
    #         choices = getattr(self, '_cached_choices_%s' % cached_field_key, None)
    #         if choices is None:
    #             choices = list(cached_field.choices)
    #             setattr(self, '_cached_choices_%s' % cached_field_key, choices)
    #         cached_field.choice_cache = choices
    #
    #     return form


def MetadataScientificPropertyInlineFormSetFactory(*args, **kwargs):
    _DEFAULT_PREFIX = "_scientific_properties"

    _prefix = kwargs.pop("prefix", "") + _DEFAULT_PREFIX
    _data = kwargs.pop("data", None)
    _initial = kwargs.pop("initial", [])
    _queryset = kwargs.pop("queryset", MetadataScientificProperty.objects.none())
    _instance = kwargs.pop("instance")
    _customizers = kwargs.pop("customizers", None)
    new_kwargs = {
        "can_delete": False,
        "extra": kwargs.pop("extra", 0),
        "formset": MetadataScientificPropertyInlineFormSet,
        "form": MetadataScientificPropertyForm,
        "fk_name": "model"  # if there's more than 1 fk to MetadataModel, this is the relevant one for this inline form
    }
    new_kwargs.update(kwargs)

    _formset = inlineformset_factory(MetadataModel, MetadataScientificProperty, *args, **new_kwargs)
    if _customizers:
        # no longer dealing w/ iterators and making sure everything is in the same order
        # now I just pass the entire set of customizers and work out which one to use in the __init__ method
        #_formset.customizers = iter(_customizers)
        _formset.form = staticmethod(curry(MetadataScientificPropertyForm, customizers=_customizers))

    if _initial:
        _formset.number_of_properties = len(_initial)
    elif _queryset:
        _formset.number_of_properties = len(_queryset)
    elif _data:
        # this fails w/ a MultiDictKeyError in the case where a non-loaded form happens to have
        # no scientific_properties; that results in _initial being '[]' which evaluates to False,
        # which falls through the if _initial check above, but since the form was not loaded there is
        # no data for the given _prefix; to fix this I use "get" and provide a default value below
        #_formset.number_of_properties = int(_data[u"%s-TOTAL_FORMS" % _prefix])
        # TODO: AN ALTERNATIVE TO THIS WOULD BE TO GIVE None AS THE DEFAULT VALUE FOR _initial ABOVE
        # TODO: AND THEN TO CALL `if _initial is not None` INSTEAD OF `if _initial` ABOVE
        total_forms_key = u"%s-TOTAL_FORMS" % _prefix
        _formset.number_of_properties = int(_data.get(total_forms_key, 0))
    else:
        _formset.number_of_properties = 0

    if _data:
        final_formset = _formset(_data, initial=_initial, instance=_instance, prefix=_prefix)
        #return _formset(_data, initial=_initial, instance=_instance, prefix=_prefix)
    else:
        final_formset = _formset(queryset=_queryset, initial=_initial, instance=_instance, prefix=_prefix)

    return final_formset

    # # notice how both "queryset" and "initial" are passed
    # # this handles both existing and new models
    # # (in the case of existing models, "queryset" is used)
    # # (in the case of new models, "initial" is used)
    # # but both arguments are needed so that "extra" is used properly
    # return _formset(queryset=_queryset, initial=_initial, instance=_instance, prefix=_prefix)
