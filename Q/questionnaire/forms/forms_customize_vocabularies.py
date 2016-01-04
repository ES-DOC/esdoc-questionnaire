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

# from djangular.forms import NgModelForm, NgModelFormMixin, NgFormValidationMixin

from django.forms import ValidationError, CharField, BooleanField, UUIDField
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import curry

from Q.questionnaire.forms.forms_customize import QCustomizationForm, QCustomizationInlineFormSet
from Q.questionnaire.models.models_customizations import QModelCustomization, QModelCustomizationVocabulary, QStandardCategoryCustomization
from Q.questionnaire.models.models_proxies import QComponentProxy
from Q.questionnaire.models.models_vocabularies import QVocabulary
from Q.questionnaire.q_utils import set_field_widget_attributes, update_field_widget_attributes, pretty_string, serialize_model_to_dict

# TODO: I AM EXCLUDING CERTAIN FIELDS SO THAT THEY DON'T CHANGE THE NG-MODEL
# TODO: I AM DOING THIS FOR ALL QCUSTOMIZATIONFORMS
# TODO: DOUBLE-CHECK THAT THIS WORKS
# TODO: (THEY ARE PREFACED BY "##")

class QModelCustomizationVocabularyForm(QCustomizationForm):
    class Meta:
        model = QModelCustomizationVocabulary
        fields = [
            'id',
            'model_customization',
            'vocabulary',
            'order',
            'active',
            'display_detail',
            'vocabulary_name',
            'vocabulary_key',
        ]

    display_detail = BooleanField()
    vocabulary_name = CharField(required=False)
    vocabulary_key = UUIDField()

    def __init__(self, *args, **kwargs):
        super(QModelCustomizationVocabularyForm, self).__init__(*args, **kwargs)
        if not self.instance.pk:
            # I don't need to reset the key b/c "get_new_customization_forms" passes it in via initial
            pass
        else:
            self.initial["vocabulary_key"] = self.instance.get_key()
        self.unbootstrap_field("active")

    def get_initial_data(self):
        """
        overriding this so that I can include components data to pass to serializer
        this is not part of the form
        TODO: IN THE LONG-TERM, SHOULD I DO THIS ALL IN THE SERIALIZER?
        :return:
        """
        initial_data = super(QModelCustomizationVocabularyForm, self).get_initial_data()
        vocabulary_id = self.get_current_field_value("vocabulary")
        vocabulary = QVocabulary.objects.get(pk=vocabulary_id)
        initial_data.update({
            "components": [
                {
                    "name": component_proxy.name,
                    "order": component_proxy.order,
                    "key": component_proxy.get_key(),
                    "num_properties": component_proxy.scientific_property_proxies.count(),
                }
                for component_proxy in vocabulary.component_proxies.all()
            ]
        })
        return initial_data

class QModelCustomizationVocabularyInlineFormSet(QCustomizationInlineFormSet):

    pass


def QModelCustomizationVocabularyFormSetFactory(*args, **kwargs):

    instance = kwargs.pop("instance", None)
    initial = kwargs.pop("initial", [])
    queryset = kwargs.pop("queryset", QModelCustomizationVocabulary.objects.none())
    prefix = kwargs.pop("prefix", None)
    scope_prefix = kwargs.pop("scope_prefix", None)
    formset_name = kwargs.pop("formset_name", None)

    form = QModelCustomizationVocabularyForm
    formset = QModelCustomizationVocabularyInlineFormSet

    kwargs.update({
        "can_delete": False,
        "extra": kwargs.pop("extra", 0),
        "form": form,
        "formset": formset,
    })
    formset = inlineformset_factory(QModelCustomization, QModelCustomizationVocabulary, *args, **kwargs)
    formset.form = staticmethod(curry(form, formset_class=formset))
    formset.scope_prefix = scope_prefix
    formset.formset_name = formset_name

    # TODO: NOT SURE I NEED "queryset" W/ AN _INLINE_ FORMSET; INSTANCE SHOULD BE ENOUGH, RIGHT?
    return formset(instance=instance, initial=initial, queryset=queryset)


