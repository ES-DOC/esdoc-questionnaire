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
.. module:: forms_project

Form classes & functions for the Project Page
"""

from django.forms import *
from django.utils.safestring import SafeString
from django.forms.models import ModelForm, BaseModelFormSet, modelformset_factory

from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy
from CIM_Questionnaire.questionnaire.models.metadata_version import MetadataVersion
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataModelCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
from CIM_Questionnaire.questionnaire.utils import QuestionnaireError
from CIM_Questionnaire.questionnaire.utils import set_field_widget_attributes, update_field_widget_attributes


class NewModelForm(forms.Form):

    # ontologies are all registered CIM versions
    ontologies = ModelChoiceField(queryset=MetadataVersion.objects.none(), label="Ontolgoy", required=True, empty_label=None)

    # documents are all model proxies belonging to the above ontologies that have the 'document' stereotype
    documents = ModelChoiceField(queryset=MetadataModelProxy.objects.none(), label="Document Type", required=True, empty_label=None)

    def __init__(self, *args, **kwargs):
        ontologies_qs = kwargs.pop("ontologies", None)
        documents_qs = kwargs.pop("documents", None)

        super(NewModelForm, self).__init__(*args, **kwargs)

        ontologies_field = self.fields["ontologies"]
        documents_field = self.fields["documents"]
        if ontologies_qs is not None:
            ontologies_field.queryset = ontologies_qs
        if documents_qs is not None:
            documents_field.queryset = documents_qs
        function_name = "set_options(this,'%s-documents');" % self.prefix
        update_field_widget_attributes(ontologies_field, {"class": "changer", })
        set_field_widget_attributes(ontologies_field, {"onchange": function_name, })


class ExistingModelForm(ModelForm):

    selected = BooleanField(initial=False, required=False)

    def __init__(self, *args, **kwargs):
        super(ExistingModelForm, self).__init__(*args, **kwargs)
        update_field_widget_attributes(self.fields["selected"], {"class": "hidden", })


class ExistingDocumentForm(ExistingModelForm):

    class Meta:
        model = MetadataModel
        fields = ["id", "selected", ]  # not sure why "id" is explicitly required, but it is

    def get_label(self):

        model = self.instance
        assert model is not None

        label_string = model.get_label()
        if not label_string:
            label_string = "<i>(no label provided)</i>"
        label_string += "&nbsp;&nbsp;[%s]" % model.document_version

        return SafeString(label_string)


class ExistingCustomizationForm(ExistingModelForm):

    class Meta:
        model = MetadataModelCustomizer
        fields = ["id", "selected", ]  # not sure why "id" is required, but it is

    def get_label(self):

        model = self.instance
        assert model is not None

        label_string = model.name
        if model.default:
            label_string += "&nbsp;*"

        return SafeString(label_string)


class ExistingModelFormSet(BaseModelFormSet):

    def find_selected_form(self):
        assert self.is_bound
        for form in self:
            key = u"%s-selected" % form.prefix
            if key in self.data:
                return form
        return None


def ExistingModelFormSetFactory(*args, **kwargs):
    _model = kwargs.pop("model", None)
    _queryset = kwargs.pop("queryset", None)
    _data = kwargs.pop("data", None)
    _prefix = kwargs.pop("prefix", None)

    if _queryset is None and _data is None:  # can't just check if they're True, b/c empty querysets & dictionaries will return False
        raise QuestionnaireError("Must specify either a queryset or a data dictionary to create a fomset")

    if _model == MetadataModel:
        model_form = ExistingDocumentForm
    elif _model == MetadataModelCustomizer:
        model_form = ExistingCustomizationForm
    else:
        raise QuestionnaireError("Must specify either a MetadataModel or a MetadataModelCustomizer to create a formset")

    _formset = modelformset_factory(
        _model,
        extra=0,
        form=model_form,
        formset=ExistingModelFormSet,
    )

    if _data:
        return _formset(_data, prefix=_prefix)
    elif _queryset:
        return _formset(queryset=_queryset, prefix=_prefix)
