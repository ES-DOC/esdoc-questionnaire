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

from django.forms import CharField, BooleanField, ChoiceField, UUIDField
from django.forms.models import inlineformset_factory, modelform_factory
from django.utils.functional import curry

from Q.questionnaire.forms.forms_customize import QCustomizationForm
from Q.questionnaire.models.models_customizations import QModelCustomization, QPropertyCustomization
from Q.questionnaire.models.models_proxies import QPropertyProxy
from Q.questionnaire.q_fields import QPropertyTypes
from Q.questionnaire.q_utils import QError, set_field_widget_attributes, update_field_widget_attributes, pretty_string, serialize_model_to_dict

# TODO: I AM EXCLUDING CERTAIN FIELDS SO THAT THEY DON'T CHANGE THE NG-MODEL
# TODO: I AM DOING THIS FOR ALL QCUSTOMIZATIONFORMS
# TODO: DOUBLE-CHECK THAT THIS WORKS


class QPropertyCustomizationForm(QCustomizationForm):
    class Meta:
        model = QPropertyCustomization
        fields = [
            'id',
            'proxy',
            'model_customization',
            'category',
            # 'name',
            'property_title',
            'is_required',
            'is_hidden',
            'is_editable',
            'is_nillable',
            'documentation',
            'inline_help',
            'order',
            'field_type',
            'atomic_default',
            'atomic_type',
            'atomic_suggestions',
            'enumeration_open',
            'relationship_show_subform',
            # 'relationship_target_model_customizations',

            # 'enumeration_choices',
            # 'enumeration_default',

            'subform_targets',
            'key',
            'category_key',
            'display_detail',
        ]

    _common_fields = ["is_hidden", "is_required", "is_editable", "is_nillable", "property_title", "documentation", "inline_help", ]
    # _header_fields = ["property_title", "order", "category", "category_key", ]
    _atomic_fields = ["atomic_type", "atomic_default", "atomic_suggestions", ]
    _enumeration_fields = ["enumeration_open", ]  # "enumeration_choices", "enumeration_default",
    _relationship_fields = ["relationship_show_subform", ]  ## "relationship_target_model_customizations" is not used
    _hidden_fields = ["key", 'category_key', ]

    # form-only fields...
    key = UUIDField()
    category_key = UUIDField()
    display_detail = BooleanField(initial=False)
    subform_targets = ChoiceField(required=True, choices=[])  # choices will be replaced in __init__ below

    def __init__(self, *args, **kwargs):
        super(QPropertyCustomizationForm, self).__init__(*args, **kwargs)

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
            self.unbootstrap_fields(["enumeration_open", ])
            # choices = proxy.enumeration_choices.split('|')
            # enumeration_choices_field = self.fields["enumeration_choices"]
            # enumeration_default_field = self.fields["enumeration_default"]
            # enumeration_choices_field.set_choices(choices)
            # enumeration_default_field.set_choices(choices)
            # update_field_widget_attributes(enumeration_choices_field, {"class": "select multiple show-tick"})
            # update_field_widget_attributes(enumeration_default_field, {"class": "select multiple show-tick"})
            # if is_new_property:
            #     self.initial["enumeration_choices"] = choices

        else:  # field_type == QPropertyTypes.RELATIONSHIP
            # things to do for RELATIONSHIP fields...
            self.unbootstrap_fields(["relationship_show_subform"])
            update_field_widget_attributes(self.fields["relationship_show_subform"], {
                "ng-disabled": "true",
                "readonly": "readonly",
            })
            self.fields["subform_targets"].choices = [
                (relationship_subform_customization.get_key(), str(relationship_subform_customization.proxy))
                for relationship_subform_customization in self.instance.relationship_target_model_customizations(manager="allow_unsaved_relationship_target_model_customizations_manager").all()
            ]
            update_field_widget_attributes(self.fields["subform_targets"], {"class": "select single show-tick"})

        # things to do for ALL fields...

        # TODO: DOUBLE-CHECK THAT I SHOULD SET ".initial[key]" and not ".fields[key].initial"
        self.initial["key"] = self.instance.get_key()
        self.initial["category_key"] = self.instance.category.get_key()

        if proxy.is_required():
            # if a property is required by the CIM
            # (then property.reset() will have set the "required" field to True)
            # then don't allow users to change the "is_required" or "is_hidden" fields
            update_field_widget_attributes(self.fields["is_required"], {
                "ng-disabled": "true",
                "readonly": "readonly",
            })
            update_field_widget_attributes(self.fields["is_hidden"], {
                "ng-disabled": "true",
                "readonly": "readonly",
            })

        self.unbootstrap_fields(["is_hidden", "is_required", "is_editable", "is_nillable", "inline_help", ])
        set_field_widget_attributes(self.fields["documentation"], {"rows": 2})

    def get_field_type(self):
        return self.get_current_field_value("field_type")

    def get_proxy(self):
        proxy_id = self.get_current_field_value("proxy")
        return QPropertyProxy.objects.get(pk=proxy_id)

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

    def get_subform_target_choices(self):
        # TODO: I DON'T THINK THIS IS USED ANYMORE; THE TEMPLATES THAT USED TO RELY ON THIS NOW USE PURE NG
        """
        returns a list of tuples of (target_model_customization.key, target_model_customization.name)
        to use to build a nifty widget in bootstrap for launching subform customizers
        :return: list
        """
        property = self.instance
        subform_target_choices = [
            (relationship_subform_customization.get_key(), str(relationship_subform_customization.proxy))
            for relationship_subform_customization in property.relationship_target_model_customizations(manager="allow_unsaved_relationship_target_model_customizations_manager").all()
        ]
        return subform_target_choices


    def get_subform_key(self):

        instance = self.instance
        # TODO: THIS DOESN'T WORK B/C OF MULTIPLE TARGETS

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


# NO LONGER USING FORMSETS... WOOHOO!
#
# class QPropertyCustomizationInlineFormSet(QCustomizationInlineFormSet):
#     pass
#
#
# def QPropertyCustomizationInlineFormSetFactory(*args, **kwargs):
#
#     instance = kwargs.pop("instance", None)
#     initial = kwargs.pop("initial", [])
#     queryset = kwargs.pop("queryset", QPropertyCustomization.objects.none())
#     prefix = kwargs.pop("prefix", None)
#     scope_prefix = kwargs.pop("scope_prefix", None)
#     formset_name = kwargs.pop("formset_name", None)
#
#     form = QPropertyCustomizationForm
#     formset = QPropertyCustomizationInlineFormSet
#
#     kwargs.update({
#         "can_delete": False,
#         "extra": kwargs.pop("extra", 0),
#         "form": form,
#         "formset": formset,
#         "fk_name": "model_customization",   # required in-case there are more than 1 fk's to the parent model
#     })
#     formset = inlineformset_factory(QModelCustomization, QPropertyCustomization, *args, **kwargs)
#     formset.form = staticmethod(curry(form, formset_class=formset))
#     formset.scope_prefix = scope_prefix
#     formset.formset_name = formset_name
#
#     # TODO: NOT SURE I NEED "queryset" W/ AN _INLINE_ FORMSET; INSTANCE SHOULD BE ENOUGH, RIGHT?
#     return formset(instance=instance, initial=initial, queryset=queryset)
