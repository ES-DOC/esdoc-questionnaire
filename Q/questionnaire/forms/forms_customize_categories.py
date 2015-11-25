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

from django.forms import CharField, BooleanField, UUIDField
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import curry

from Q.questionnaire.forms.forms_customize import  QCustomizationForm, QCustomizationInlineFormSet
from Q.questionnaire.models.models_customizations import QModelCustomization, QStandardCategoryCustomization, QScientificCategoryCustomization
from Q.questionnaire.q_utils import set_field_widget_attributes, update_field_widget_attributes, pretty_string, serialize_model_to_dict

# TODO: I AM EXCLUDING CERTAIN FIELDS SO THAT THEY DON'T CHANGE THE NG-MODEL
# TODO: I AM DOING THIS FOR ALL QCUSTOMIZATIONFORMS
# TODO: DOUBLE-CHECK THAT THIS WORKS
# TODO: (THEY ARE PREFACED BY "##")

class QStandardCategoryCustomizationForm(QCustomizationForm):
    class Meta:
        model = QStandardCategoryCustomization
        fields = [
            'id',
            'name',
            'description',
            'order',
            'model_customization',
            'proxy',
            'key',
            'display_properties',
            'display_detail',
        ]

    display_properties = BooleanField(initial=True)
    display_detail = BooleanField(initial=False)
    key = UUIDField()

    _category_fields = ["name", "description", "order",]

    def __init__(self, *args, **kwargs):
        super(QStandardCategoryCustomizationForm, self).__init__(*args, **kwargs)
        if not self.instance.pk:
            # I don't need to reset the key b/c "get_new_customization_forms" passes it in via initial
            pass
        else:
            # TODO: DOUBLE-CHECK THAT I SHOULD SET ".initial[key]" and not ".fields[key].initial"
            # self.fields["key"].initial = self.instance.get_key()
            self.initial["key"] = self.instance.get_key()
        set_field_widget_attributes(self.fields["description"], {"rows": 2})
        update_field_widget_attributes(self.fields["order"], {"ng-disabled": "true"})

    def get_category_fields(self):
        """
        get only those fields that can be customized
        :return:
        """
        return self.get_fields_from_list(self._category_fields)

class QStandardCategoryCustomizationInlineFormSet(QCustomizationInlineFormSet):

    label = _(
        "Available Categories"
    )
    help_text = _(
        'These categories will appear as tabs within the Editor.'
        'The tab order can be changed by dragging and dropping the above widgets.'
        'Additionally, each category can be customized by clicking the "pencil/edit" icon.'
        'Clicking elsewhere on a category widget will toggle the visibility of all properties belonging to that category.'
        'Use the "View All" button above to display properties from all categories.'
    )


def QStandardCategoryCustomizationInlineFormSetFactory(*args, **kwargs):

    instance = kwargs.pop("instance", None)
    initial = kwargs.pop("initial", [])
    queryset = kwargs.pop("queryset", QStandardCategoryCustomization.objects.none())
    prefix = kwargs.pop("prefix", None)
    scope_prefix = kwargs.pop("scope_prefix", None)
    formset_name = kwargs.pop("formset_name", None)

    form = QStandardCategoryCustomizationForm
    formset = QStandardCategoryCustomizationInlineFormSet

    kwargs.update({
        "can_delete": False,
        "extra": kwargs.pop("extra", 0),
        "form": form,
        "formset": formset,
    })
    formset = inlineformset_factory(QModelCustomization, QStandardCategoryCustomization, *args, **kwargs)
    formset.form = staticmethod(curry(form, formset_class=formset))
    formset.scope_prefix = scope_prefix
    formset.formset_name = formset_name

    # TODO: NOT SURE I NEED "queryset" W/ AN _INLINE_ FORMSET; INSTANCE SHOULD BE ENOUGH, RIGHT?
    return formset(instance=instance, initial=initial, queryset=queryset)


class QScientificCategoryCustomizationForm(QCustomizationForm):
    class Meta:
        model = QScientificCategoryCustomization
        fields = [
            'id',
            'name',
            'description',
            'order',
            'model_customization',
            'vocabulary_key',
            'component_key',
            'proxy',
            'key',
            'display_properties',
            'display_detail',
        ]

    display_properties = BooleanField(initial=True)
    display_detail = BooleanField(initial=False)
    key = UUIDField()

    _category_fields = ["name", "description", "order",]

    def __init__(self, *args, **kwargs):
        super(QScientificCategoryCustomizationForm, self).__init__(*args, **kwargs)
        if not self.instance.pk:
            # I don't need to reset the key b/c "get_new_customization_forms" passes it in via initial
            pass
        else:
            # TODO: DOUBLE-CHECK THAT I SHOULD SET ".initial[key]" and not ".fields[key].initial"
            # self.fields["key"].initial = self.instance.get_key()
            self.initial["key"] = self.instance.get_key()
        set_field_widget_attributes(self.fields["description"], {"rows": 2})
        update_field_widget_attributes(self.fields["order"], {"ng-disabled": "true"})

    def get_category_fields(self):
        """
        get only those fields that can be customized
        :return:
        """
        return self.get_fields_from_list(self._category_fields)


class QScientificCategoryCustomizationInlineFormSet(QCustomizationInlineFormSet):

    label = _(
        "Available Categories"
    )
    help_text = _(
        'These categories will appear as tabs within the Editor.'
        'The tab order can be changed by dragging and dropping the above widgets.'
        'Additionally, each category can be customized by clicking the "pencil/edit" icon.'
        'Clicking elsewhere on a category widget will toggle the visibility of all properties belonging to that category.'
        'Use the "View All" button above to display properties from all categories.'
    )


def QScientificCategoryCustomizationInlineFormSetFactory(*args, **kwargs):

    instance = kwargs.pop("instance", None)
    initial = kwargs.pop("initial", [])
    queryset = kwargs.pop("queryset", QScientificCategoryCustomization.objects.none())
    prefix = kwargs.pop("prefix", None)
    scope_prefix = kwargs.pop("scope_prefix", None)
    formset_name = kwargs.pop("formset_name", None)

    form = QScientificCategoryCustomizationForm
    formset = QScientificCategoryCustomizationInlineFormSet

    kwargs.update({
        "can_delete": False,
        "extra": kwargs.pop("extra", 0),
        "form": form,
        "formset": formset,
    })
    formset = inlineformset_factory(QModelCustomization, QScientificCategoryCustomization, *args, **kwargs)
    formset.form = staticmethod(curry(form, formset_class=formset))
    formset.scope_prefix = scope_prefix
    formset.formset_name = formset_name

    # TODO: NOT SURE I NEED "queryset" W/ AN _INLINE_ FORMSET; INSTANCE SHOULD BE ENOUGH, RIGHT?
    return formset(instance=instance, initial=initial, queryset=queryset)
