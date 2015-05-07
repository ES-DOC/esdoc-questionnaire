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
.. module:: forms_customize_vocabulary

classes for the forms relating to the MetadataModelCustomizerVocabulary "through" model

"""

from django.forms.widgets import TextInput
from django.forms.models import ModelForm, BaseInlineFormSet
from django.forms.models import inlineformset_factory

from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataModelCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataModelCustomizerVocabulary
from CIM_Questionnaire.questionnaire.fields import MULTIPLECHOICEFIELD_HELP_TEXT
from CIM_Questionnaire.questionnaire.utils import update_field_widget_attributes, model_to_data

# notice that MetadataModelCustomizerVocabulary doesn't inherit from MetadataForm
# and does not concern itself w/ any of the confusing-isms of the load-on-demand paradigm


def create_model_customizer_vocabulary_form_data(model_customizer, vocabulary, order):

    model_customizer_vocabulary = MetadataModelCustomizerVocabulary(
        model_customizer=model_customizer,
        vocabulary=vocabulary,
        vocabulary_key=vocabulary.get_key(),
        order=order,
    )

    model_customizer_vocabulary_form_data = \
        model_to_data(
            model_customizer_vocabulary,
            exclude=["model_customizer, "],  # no need to pass model_customizer, this is handled by being an "inline" formset
            include={
                "active": True,
            }
        )

    return model_customizer_vocabulary_form_data


class MetadataModelCustomizerVocabularyWidget(TextInput):
    """
    replace the vocabulary ModelChoiceInput w/ this custom widget
    behaves like a TextInput (so no drop-down),
    but rather than display the value (pk), it displayes the label
    (this doesn't warrant an entire custom form field, just this special render fn)
    (and then some cleverness in the form's "clean" fn)
    """

    def render(self, name, value, attrs=None):
        if not isinstance(value, basestring):
            # when dealing w/ a new form, there will be an integer
            # when loading from data, there will be a string (based on the previous rendering)
            vocabulary = MetadataVocabulary.objects.get(pk=value)
            value = vocabulary.get_label()
        return super(MetadataModelCustomizerVocabularyWidget, self).render(name, value, attrs)


class MetadataModelCustomizerVocabularyForm(ModelForm):

    class Meta:
        model = MetadataModelCustomizerVocabulary
        fields = ["id", "active", "vocabulary", "order", "vocabulary_key"]

    def __init__(self, *args, **kwargs):

        super(MetadataModelCustomizerVocabularyForm, self).__init__(*args, **kwargs)

        active_field = self.fields["active"]
        vocabulary_field = self.fields["vocabulary"]
        order_field = self.fields["order"]
        key_field = self.fields["vocabulary_key"]

        vocabulary_field.widget = MetadataModelCustomizerVocabularyWidget()

        update_field_widget_attributes(active_field, {"class": "active"})
        update_field_widget_attributes(vocabulary_field, {"class": "vocabulary label", "readonly": "readonly"})
        update_field_widget_attributes(order_field, {"class": "order label", "readonly": "readonly"})
        update_field_widget_attributes(key_field, {"class": "key hidden"})

    def clean(self):
        """
        b/c I replaced the "vocabulary" field widget w/ a MetadataModelCustomizerVocabularyWidget,
        it no longer returns the pk, so the form cannot find the vocabulary
        this fixes that (at the cost of one db hit)
        :return: cleaned_data dictionary
        """

        super(MetadataModelCustomizerVocabularyForm, self).clean()

        vocabulary_label = self.data[u"%s-vocabulary" % self.prefix]
        vocabulary = MetadataVocabulary.get_vocabulary_by_label(vocabulary_label)

        self.cleaned_data["vocabulary"] = vocabulary

        # in addition to getting the value right,
        # I also have to remove any errors that might have been previously raised
        # that is b/c validation happens on the underyling form field before the form
        # and that validation checks the value against the queryset
        self._errors.pop("vocabulary")

        return self.cleaned_data


class MetadataModelCustomizerVocabularyInlineFormSet(BaseInlineFormSet):

    def __init__(self, *args, **kwargs):
        super(MetadataModelCustomizerVocabularyInlineFormSet, self).__init__(*args, **kwargs)

        # be able to access the underlying field for the m2m relationship
        # (this is needed to get things like labels & help_text in the template)
        fk_model = self.fk.related.parent_model
        self.inline_field = fk_model.get_field("sorted_vocabularies")

        # THIS IS A RIDICULOUS HACK...
        # DJANGO ADDS SOME TEXT TO M2M FIELD'S HELP ("django.forms.models.ModelMultipleChoiceField#__init__")
        # I HAVE TO MANUALLY REMOVE IT HERE
        # TODO: THIS SHOULD BE FIXED IN FUTURE VERSIONS OF DJANGO
        old_help_text = unicode(self.inline_field.help_text)
        new_help_text = old_help_text.replace(MULTIPLECHOICEFIELD_HELP_TEXT, "")
        self.inline_field.help_text = new_help_text

    # THIS IS CONFUSING TOO...
    # THE NATURAL ORDER OF MetadataModelCustomizerVocabulary IS SPECIFIED BY ITS "order" FIELD
    # THAT CAN BE MANIPULATED BY THE GUI AND THE UNDERLYING MODELS ARE SAVED APPROPRIATELY
    # HOWEVER, THE UNDERLYING MODELS ARE SAVED _AFTER_ DATA IS LOADED INTO THESE FORMS
    # THE ORDER OF FORMS IN THAT DATA REFLECTS THE ORDER OF FORMS _BEFORE_ ANYTHING IS SAVED
    # TO GET AROUND THIS, I EXPLICITLY SORT THE FORMS IN THE NEXT 2 FNS (NOTICE THAT I CHECK DATA 1ST)

    def __iter__(self):
        """Yields the forms in the order they should be rendered"""
        _forms = list(self.forms)
        try:
            _forms.sort(key=lambda x: x.data["%s-order" % x.prefix])
        except KeyError:
            _forms.sort(key=lambda x: x.initial["order"])
        return iter(_forms)

    def __getitem__(self, index):
        """Returns the form at the given index, based on the rendering order"""
        _forms = list(self.forms)
        try:
            _forms.sort(key=lambda x: x.data["%s-order" % x.prefix])
        except KeyError:
            _forms.sort(key=lambda x: x.initial["order"])
        return _forms[index]

    def label(self):
        if self.inline_field:
            return self.inline_field.verbose_name
        return None

    def help_text(self):
        if self.inline_field:
            return self.inline_field.help_text
        return None

    def get_active_forms(self):

        assert self.is_bound

        active_forms = []
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            form_prefix = form.prefix
            active_key = u"%s-active" % form_prefix
            active = self.data.get(active_key, False)
            if active in [u"on", u"True", True]:
                active_forms.append(form)

        return active_forms


def MetadataModelCustomizerVocabularyFormSetFactory(*args, **kwargs):

    prefix = "model_customizer_vocabulary"

    _data = kwargs.pop("data", None)
    _initial = kwargs.pop("initial", [])
    _instance = kwargs.pop("instance")
    _queryset = kwargs.pop("queryset", None)
    new_kwargs = {
        "can_delete": False,
        "extra": kwargs.pop("extra", 0),
        "formset": MetadataModelCustomizerVocabularyInlineFormSet,
        "form": MetadataModelCustomizerVocabularyForm,
    }
    new_kwargs.update(kwargs)

    _formset = inlineformset_factory(MetadataModelCustomizer, MetadataModelCustomizer.sorted_vocabularies.through, *args, **new_kwargs)

    if _data:
        return _formset(_data, instance=_instance, prefix=prefix)
    elif _queryset:
        return _formset(queryset=_queryset, instance=_instance, prefix=prefix)
    else:
        return _formset(initial=_initial, instance=_instance, prefix=prefix)