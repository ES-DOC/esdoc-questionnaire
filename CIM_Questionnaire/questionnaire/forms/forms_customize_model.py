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
.. module:: forms_customize_model

classes for CIM Questionnaire model customizer form creation & manipulation
"""

import time
from django.core import serializers
from django.forms import CharField, Textarea
from django.forms import ValidationError
from django.forms.formsets import TOTAL_FORM_COUNT
from django.forms.util import ErrorList

from CIM_Questionnaire.questionnaire.forms.forms_customize import MetadataCustomizerForm
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataModelCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary
from CIM_Questionnaire.questionnaire.utils import JSON_SERIALIZER
from CIM_Questionnaire.questionnaire.utils import model_to_data
from CIM_Questionnaire.questionnaire.utils import set_field_widget_attributes, update_field_widget_attributes


def create_model_customizer_form_data(model_customizer, standard_category_customizers, scientific_category_customizers, vocabularies=[]):

    model_customizer_form_data = model_to_data(
        model_customizer,
        exclude=[],
        include={
            "last_modified": time.strftime("%c"),
            "loaded": True,  # model_customizer forms are always loaded (only scientific_property forms aren't)
        }
    )

    return model_customizer_form_data


class MetadataAbstractModelCustomizerForm(MetadataCustomizerForm):

    class Meta:
        abstract = True

    def get_hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)

    def get_customizer_fields(self):
        return self.get_fields_from_list(self._customizer_fields)

    def get_document_fields(self):
        return self.get_fields_from_list(self._document_fields)

    def validate_unique(self):
        model_customizer = self.instance
        try:
            model_customizer.validate_unique()
        except ValidationError, e:
            # if there is a validation error then apply that error to the individual fields
            # so it shows up in the form and is rendered nicely via JQuery
            unique_together_fields_list = model_customizer.get_unique_together()
            for unique_together_fields in unique_together_fields_list:
                if any(field.lower() in " ".join(e.messages).lower() for field in unique_together_fields):
                    msg = "Customizer with this %s already exists" % (", ".join(unique_together_fields))
                    for unique_together_field in unique_together_fields:
                        self.errors[unique_together_field] = msg


class MetadataModelCustomizerForm(MetadataAbstractModelCustomizerForm):

    class Meta:
        model = MetadataModelCustomizer
        
        fields = [
            # hidden fields...
            "proxy", "project", "version",
            # customizer fields...
            "name", "description", "default",
            # document fields...
            "model_title", "model_description", "model_show_all_categories", "model_show_hierarchy", "model_hierarchy_name", "model_root_component",
        ]

    _hidden_fields = ("proxy", "project", "version", )
    _customizer_fields = ("name", "description", "default", )
    _document_fields = ("model_title", "model_description", "model_show_all_categories", "model_show_hierarchy", "model_hierarchy_name", "model_root_component",)

    def __init__(self, *args, **kwargs):
        all_vocabularies = kwargs.pop("all_vocabularies", [])

        super(MetadataModelCustomizerForm, self).__init__(*args, **kwargs)

        update_field_widget_attributes(self.fields["model_show_hierarchy"], {"class": "enabler", })
        set_field_widget_attributes(self.fields["model_show_hierarchy"], {"onchange": "enable(this,'true',['model_root_component']);", })
        set_field_widget_attributes(self.fields["description"], {"cols": "60", "rows": "4", })
        set_field_widget_attributes(self.fields["model_description"], {"cols": "60", "rows": "4", })

    def clean_default(self):
        cleaned_data = self.cleaned_data
        default = cleaned_data.get("default")
        if default:
            other_customizer_filter_kwargs = {
                "default": True,
                "proxy": cleaned_data["proxy"],
                "project": cleaned_data["project"],
                "version": cleaned_data["version"],
            }
            other_customizers = MetadataModelCustomizer.objects.filter(**other_customizer_filter_kwargs)
            this_customizer = self.instance
            if this_customizer.pk:
                other_customizers = other_customizers.exclude(pk=this_customizer.pk)
            if other_customizers.count() != 0:
                raise ValidationError("A default customization already exists.  There can be only one default customization per project.")
        return default

    def clean(self):
        # calling the parent class's clean fun automatically sets a
        # flag that forces unique (and unique_together) validation
        super(MetadataModelCustomizerForm, self).clean()
        cleaned_data = self.cleaned_data

        # this is very non-standard...
        # but some of the validity of this form depends upon fields in the related model_customizer_vocabulary_formset
        # one solution is to pass info from that formset (or the formset itself) into the __init__ fn of this form
        # (as described here: http://stackoverflow.com/a/7059992)
        # but there are too many cross-form dependencies b/c it is an _inline_ formset
        # so I get the required info from "data" here (before the formset has been cleaned)
        # - there is no way to generate invalid data on that formset; the interface doesn't allow it, so this is safe -

        vocabularies = []
        active_vocabularies = []
        model_customizer_vocabulary_prefix = "model_customizer_vocabulary"
        model_customizer_vocabulary_data = {
            k: v for k, v in self.data.items()
            if k.startswith(model_customizer_vocabulary_prefix)
            }
        n_model_customizer_vocabularies = int(model_customizer_vocabulary_data[u"%s-%s" % (model_customizer_vocabulary_prefix, TOTAL_FORM_COUNT)])
        for i in range(0, n_model_customizer_vocabularies):
            vocabulary_label_key = u"%s-%s-vocabulary" % (model_customizer_vocabulary_prefix, i)
            vocabulary_active_key = u"%s-%s-active" % (model_customizer_vocabulary_prefix, i)
            vocabulary_label = model_customizer_vocabulary_data.get(vocabulary_label_key, "")
            vocabulary_active = model_customizer_vocabulary_data.get(vocabulary_active_key, False)
            vocabulary = MetadataVocabulary.get_vocabulary_by_label(vocabulary_label)
            vocabularies.append(vocabulary)
            if vocabulary_active in [u"on", u"True", True]:
                active_vocabularies.append(vocabulary)

        # ...here endeth the very non-standard bit

        # ensure that if you want to show a root component that you have named it
        # and if you don't, that you aren't using multiple CVs
        model_show_hierarchy = cleaned_data["model_show_hierarchy"]
        if model_show_hierarchy:
            model_root_component_name = cleaned_data["model_root_component"]
            if not model_root_component_name:
                self._errors["model_root_component"] = ErrorList()
                self._errors["model_root_component"].append("You must specify a root component name, since you chose to display the full component hierarchy within a root component.")
        elif len(active_vocabularies) > 1:
            self._errors["model_show_hierarchy"] = ErrorList()
            self._errors["model_show_hierarchy"].append("There must be a root component when using multiple CVs")

        return cleaned_data


class MetadataModelCustomizerSubForm(MetadataAbstractModelCustomizerForm):

    class Meta:
        model = MetadataModelCustomizer

        fields = [
            # hidden fields...
            "proxy", "project", "version", "name",
            # customizer fields...
            # document fields...
            "model_title", "model_description", "model_show_all_categories",
        ]

    _hidden_fields = ("proxy", "project", "version", "name", )
    _customizer_fields = ()
    _document_fields = ("model_title", "model_description", "model_show_all_categories", )

    def __init__(self, *args, **kwargs):
        all_vocabularies = kwargs.pop("all_vocabularies", [])

        super(MetadataModelCustomizerSubForm, self).__init__(*args, **kwargs)

        set_field_widget_attributes(self.fields["model_description"], {"cols": "60", "rows": "4", })