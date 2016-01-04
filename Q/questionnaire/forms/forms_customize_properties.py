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

from django.forms import CharField, BooleanField, UUIDField
from django.forms.models import inlineformset_factory, modelform_factory
from django.utils.functional import curry

from Q.questionnaire.forms.forms_customize import QCustomizationForm, QCustomizationInlineFormSet
from Q.questionnaire.models.models_customizations import QModelCustomization, QStandardPropertyCustomization, QScientificPropertyCustomization
from Q.questionnaire.models.models_customizations import QCUSTOMIZATION_UNUSED_SCIENTIFIC_PROPERTY_ENUMERATION_CHOICES
from Q.questionnaire.models.models_proxies import QStandardPropertyProxy, QScientificPropertyProxy
from Q.questionnaire.q_fields import QPropertyTypes, EMPTY_CHOICE, NULL_CHOICE, OTHER_CHOICE
from Q.questionnaire.q_utils import QError, set_field_widget_attributes, update_field_widget_attributes, pretty_string, serialize_model_to_dict

# TODO: I AM EXCLUDING CERTAIN FIELDS SO THAT THEY DON'T CHANGE THE NG-MODEL
# TODO: I AM DOING THIS FOR ALL QCUSTOMIZATIONFORMS
# TODO: DOUBLE-CHECK THAT THIS WORKS
# TODO: (THEY ARE PREFACED BY "##")

#######################
# standard properties #
#######################

class QStandardPropertyCustomizationForm(QCustomizationForm):
    class Meta:
        model = QStandardPropertyCustomization
        fields = [
            'id',
            'name',
            'order',
            'cardinality',
            'field_type',
            'displayed',
            'required',
            'editable',
            'unique',
            'verbose_name',
            'documentation',
            'inline_help',
            'model_customization',
            'proxy',
            'category',
            'inherited',
            'atomic_default',
            'atomic_type',
            'atomic_suggestions',
            'enumeration_choices',
            'enumeration_default',
            'enumeration_open',
            'enumeration_multi',
            'enumeration_nullable',
            'relationship_show_subform',
##            'relationship_subform_customization',
            'key',
            'category_key',
            'display_detail',
        ]

    _common_fields = ["displayed", "required", "editable", "unique", "verbose_name", "documentation", "inline_help", "inherited", ]
    _header_fields = ["name", "order", "category", "category_key", ]
    _atomic_fields = ["atomic_type", "atomic_default", "atomic_suggestions", ]
    _enumeration_fields = ["enumeration_choices", "enumeration_default", "enumeration_open", "enumeration_multi", "enumeration_nullable", ]
    # TODO: REPLACE CARDINALITY...
    _relationship_fields = ["relationship_show_subform", ]  ## "relationship_subform_customization" is hidden
    _hidden_fields = ["key", 'category_key', ]  ## "relationship_subform_customization", ]

    # form-only fields...
    key = UUIDField()
    category_key = UUIDField()
    display_detail = BooleanField(initial=False)

    def __init__(self, *args, **kwargs):
        super(QStandardPropertyCustomizationForm, self).__init__(*args, **kwargs)

        is_new_property = not self.instance.pk
        proxy = self.get_proxy()
        field_type = self.get_field_type()

        if field_type == QPropertyTypes.ATOMIC:
            # things to do for ATOMIC fields...
            # TODO: THIS IS NO LONGER TRUE; "atomic_type" IS NOW A REQUIRED FIELD W/ A DEFAULT VALUE
            # # since atomic_fields only shows up if this is an ATOMIC field, it cannot be required
            # # but when I do display it, I can force users to make a choice
            # atomic_type_field = self.fields["atomic_type"]
            # atomic_type_field.required = True
            # atomic_type_field.empty_label = None
            # atomic_type_field.choices.remove(EMPTY_CHOICE[0])
            set_field_widget_attributes(self.fields["atomic_suggestions"], {"rows": 2})
            update_field_widget_attributes(self.fields["atomic_type"], {"class": "select single show-tick"})

        elif field_type == QPropertyTypes.ENUMERATION:
            # things to do for ENUMERATION fields...
            self.unbootstrap_fields(["enumeration_open", "enumeration_multi", "enumeration_nullable", ])
            choices = proxy.enumeration_choices.split('|')
            enumeration_choices_field = self.fields["enumeration_choices"]
            enumeration_default_field = self.fields["enumeration_default"]
            enumeration_choices_field.set_choices(choices)
            enumeration_default_field.set_choices(choices)
            update_field_widget_attributes(enumeration_choices_field, {"class": "select multiple show-tick"})
            update_field_widget_attributes(enumeration_default_field, {"class": "select multiple show-tick"})
            if is_new_property:
                self.initial["enumeration_choices"] = choices

        else:  # field_type == QPropertyTypes.RELATIONSHIP
            # things to do for RELATIONSHIP fields...
            self.unbootstrap_fields(["relationship_show_subform"])
            update_field_widget_attributes(self.fields["relationship_show_subform"], {
                "ng-disabled": "true",
                "readonly": "readonly",
            })
            update_field_widget_attributes(self.fields["cardinality"], {
                "class": "cardinality",
            })

        # things to do for ALL fields...

        # TODO: DOUBLE-CHECK THAT I SHOULD SET ".initial[key]" and not ".fields[key].initial"
        self.initial["key"] = self.instance.get_key()
        try:
            self.initial["category_key"] = self.instance.category.get_key()
        except AttributeError:
            # sometimes properties in subforms don't have categories
            # ...that's okay
            pass

        if proxy.is_required():
            # if a property is required by the CIM
            # (then property.reset() will have set the "required" field to True)
            # then don't allow users to change the "required" or "displayed" fields
            update_field_widget_attributes(self.fields["required"], {
                "ng-disabled": "true",
                "readonly": "readonly",
            })
            update_field_widget_attributes(self.fields["displayed"], {
                "ng-disabled": "true",
                "readonly": "readonly",
            })

        self.unbootstrap_fields(["displayed", "required", "editable", "unique", "inline_help", "inherited", ])
        set_field_widget_attributes(self.fields["documentation"], {"rows": 2})

    def get_field_type(self):
        return self.get_current_field_value("field_type")

    def get_proxy(self):
        proxy_id = self.get_current_field_value("proxy")
        return QStandardPropertyProxy.objects.get(pk=proxy_id)

    def get_hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)

    def get_atomic_fields(self):
        fields = self._common_fields + self._atomic_fields
        return self.get_fields_from_list(fields)

    def get_enumeration_fields(self):
        fields = self._common_fields + self._enumeration_fields
        return self.get_fields_from_list(fields)

    def get_relationship_fields(self):
        fields = self._common_fields + self._relationship_fields
        return self.get_fields_from_list(fields)

    def get_fields_for_field_type(self):

        field_type = self.get_current_field_value("field_type")

        if field_type == QPropertyTypes.ATOMIC:
            fields = self.get_atomic_fields()

        elif field_type == QPropertyTypes.ENUMERATION:
            fields = self.get_enumeration_fields()

        elif field_type == QPropertyTypes.RELATIONSHIP:
            fields = self.get_relationship_fields()

        else:
            msg = "Unknown field_type: '{0}'".format(field_type)
            raise QError(msg)

        return fields

    def get_subform_key(self):

        instance = self.instance

        subform_customization = instance.relationship_subform_customization
        if subform_customization:
            return subform_customization.get_key()

        return None

        # TODO: THIS CODE FAILED B/C IT COULD BE CALLED W/ RELATIONSHIP FIELDS
        # TODO: THAT LINKED TO CIM MODELS (AND SHOULD THEREFORE BE RENDERED AS REFERENCES, NOT SUBFORMS)
        # TODO: THIS FN GETS CALLED IN THE "<div class='modal'...>" ELEMENT IN "_q_section_customize_standard_property.html"
        # TODO: I TRIED WRAPPING THAT ELEMENT W/ AN "ng-if" BOUND TO "relationship_show_subform"
        # TODO: BUT THE ng CODE STILL SEEMED TO BE CALLED
        # TODO: FIGURE OUT A BETTER SOLUTION - I LIKED THIS CODE
        # assert instance.relationship_show_subform
        # return instance.relationship_subform_customization.get_key()


class QStandardPropertyCustomizationInlineFormSet(QCustomizationInlineFormSet):
    pass


def QStandardPropertyCustomizationInlineFormSetFactory(*args, **kwargs):

    instance = kwargs.pop("instance", None)
    initial = kwargs.pop("initial", [])
    queryset = kwargs.pop("queryset", QStandardPropertyCustomization.objects.none())
    prefix = kwargs.pop("prefix", None)
    scope_prefix = kwargs.pop("scope_prefix", None)
    formset_name = kwargs.pop("formset_name", None)

    form = QStandardPropertyCustomizationForm
    formset = QStandardPropertyCustomizationInlineFormSet

    kwargs.update({
        "can_delete": False,
        "extra": kwargs.pop("extra", 0),
        "form": form,
        "formset": formset,
        "fk_name": "model_customization",   # required in-case there are more than 1 fk's to the parent model
    })
    formset = inlineformset_factory(QModelCustomization, QStandardPropertyCustomization, *args, **kwargs)
    formset.form = staticmethod(curry(form, formset_class=formset))
    formset.scope_prefix = scope_prefix
    formset.formset_name = formset_name

    # TODO: NOT SURE I NEED "queryset" W/ AN _INLINE_ FORMSET; INSTANCE SHOULD BE ENOUGH, RIGHT?
    return formset(instance=instance, initial=initial, queryset=queryset)


#########################
# scientific properties #
#########################

class QScientificPropertyCustomizationForm(QCustomizationForm):
    class Meta:
        model = QScientificPropertyCustomization
        fields = [
            'id',
            'name',
            'order',
            'cardinality',
            'field_type',
            'displayed',
            'required',
            'editable',
            'unique',
            'verbose_name',
            'documentation',
            'inline_help',
            'model_customization',
            'proxy',
            'choice',
            'display_extra_standard_name',
            'display_extra_description',
            'display_extra_units',
            'edit_extra_standard_name',
            'edit_extra_description',
            'edit_extra_units',
            'category',
            'atomic_default',
            'atomic_type',
            'atomic_suggestions',
            'enumeration_choices',
            'enumeration_default',
            'enumeration_open',
            'enumeration_multi',
            'enumeration_nullable',
            'key',
            'category_key',
            'display_detail',
        ]

    _common_fields = ["displayed", "required", "editable", "unique", "verbose_name", "documentation", "inline_help", ]
    _header_fields = ["name", "order", "category", "category_key", ]
    _atomic_fields = ["atomic_type", "atomic_default", "atomic_suggestions", ]
    _enumeration_fields = ["enumeration_choices", "enumeration_default", "enumeration_open", "enumeration_multi", "enumeration_nullable", ]
    _extra_fields = ['display_extra_standard_name', 'display_extra_description', 'display_extra_units', 'edit_extra_standard_name', 'edit_extra_description', 'edit_extra_units', ]
    _hidden_fields = ["key", 'category_key',]

    # form-only fields...
    key = UUIDField()
    category_key = UUIDField()
    display_detail = BooleanField(initial=False)

    def __init__(self, *args, **kwargs):
        super(QScientificPropertyCustomizationForm, self).__init__(*args, **kwargs)

        is_new_property = not self.instance.pk
        proxy = self.get_proxy()
        field_type = self.get_field_type()

        if field_type == QPropertyTypes.ATOMIC:
            # things to do for ATOMIC fields...
            # TODO: THIS IS NO LONGER TRUE; "atomic_type" IS NOW A REQUIRED FIELD W/ A DEFAULT VALUE
            # # since atomic_fields only shows up if this is an ATOMIC field, it cannot be required
            # # but when I do display it, I can force users to make a choice
            # atomic_type_field = self.fields["atomic_type"]
            # atomic_type_field.required = True
            # atomic_type_field.empty_label = None
            # atomic_type_field.choices.remove(EMPTY_CHOICE[0])
            set_field_widget_attributes(self.fields["atomic_suggestions"], {"rows": 2})
            update_field_widget_attributes(self.fields["atomic_type"], {"class": "select single show-tick"})

        elif field_type == QPropertyTypes.ENUMERATION:
            # things to do for ENUMERATION fields...
            self.unbootstrap_fields(["enumeration_open", "enumeration_multi", "enumeration_nullable", ])
            choices = proxy.enumeration_choices.split('|')
            enumeration_choices_field = self.fields["enumeration_choices"]
            enumeration_default_field = self.fields["enumeration_default"]
            enumeration_choices_field.set_choices(choices)
            enumeration_default_field.set_choices(choices)
            update_field_widget_attributes(enumeration_choices_field, {"class": "select multiple show-tick"})
            update_field_widget_attributes(enumeration_default_field, {"class": "select multiple show-tick"})
            if is_new_property:
                # see the comments for QCUSTOMIZATION_UNUSED_SCIENTIFIC_PROPERTY_ENUMERATION_CHOICES
                # to understand why I remove certain enumeration_choices
                self.initial["enumeration_choices"] = [choice for choice in choices if choice not in QCUSTOMIZATION_UNUSED_SCIENTIFIC_PROPERTY_ENUMERATION_CHOICES]

        else:  # field_type == QPropertyTypes.RELATIONSHIP
            msg = "ScientificProperties cannot be RELATIONSHIPS"
            raise QError(msg)

        # things to do for ALL fields...

        # TODO: DOUBLE-CHECK THAT I SHOULD SET ".initial[key]" and not ".fields[key].initial"
        self.initial["key"] = self.instance.get_key()
        self.initial["category_key"] = self.instance.category.get_key()

        self.unbootstrap_fields(self._extra_fields + ["displayed", "required", "editable", "unique", "inline_help", ])
        set_field_widget_attributes(self.fields["documentation"], {"rows": 2})

    def get_field_type(self):
        return self.get_current_field_value("field_type")

    def get_proxy(self):
        proxy_id = self.get_current_field_value("proxy")
        return QScientificPropertyProxy.objects.get(pk=proxy_id)

    def get_hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)

    def get_atomic_fields(self):
        fields = self._common_fields + self._atomic_fields
        return self.get_fields_from_list(fields)

    def get_enumeration_fields(self):
        fields = self._common_fields + self._enumeration_fields
        return self.get_fields_from_list(fields)

    def get_extra_fields(self):
        return self.get_fields_from_list(self._extra_fields)

    def get_fields_for_field_type(self):

        field_type = self.get_field_type()

        if field_type == QPropertyTypes.ATOMIC:
            fields = self.get_atomic_fields()

        elif field_type == QPropertyTypes.ENUMERATION:
            fields = self.get_enumeration_fields()

        else:
            msg = "Unknown field_type: '{0}'".format(field_type)
            raise QError(msg)

        return fields


class QScientificPropertyCustomizationInlineFormSet(QCustomizationInlineFormSet):
    pass


def QScientificPropertyCustomizationInlineFormSetFactory(*args, **kwargs):

    instance = kwargs.pop("instance", None)
    initial = kwargs.pop("initial", [])
    queryset = kwargs.pop("queryset", QScientificPropertyCustomization.objects.none())
    prefix = kwargs.pop("prefix", None)
    scope_prefix = kwargs.pop("scope_prefix", None)
    formset_name = kwargs.pop("formset_name", None)

    form = QScientificPropertyCustomizationForm
    formset = QScientificPropertyCustomizationInlineFormSet

    kwargs.update({
        "can_delete": False,
        "extra": kwargs.pop("extra", 0),
        "form": form,
        "formset": formset,
        "fk_name": "model_customization",   # required in-case there are more than 1 fk's to the parent model
    })
    formset = inlineformset_factory(QModelCustomization, QScientificPropertyCustomization, *args, **kwargs)
    formset.form = staticmethod(curry(form, formset_class=formset))
    formset.scope_prefix = scope_prefix
    formset.formset_name = formset_name

    # TODO: NOT SURE I NEED "queryset" W/ AN _INLINE_ FORMSET; INSTANCE SHOULD BE ENOUGH, RIGHT?
    return formset(instance=instance, initial=initial, queryset=queryset)
