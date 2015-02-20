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
.. module:: views_project

Views for the Project Page
"""

import json
from django.forms import *
from django.utils.safestring import SafeString
from django.forms.models import ModelForm, BaseModelFormSet, modelformset_factory
from django.core.urlresolvers import reverse
from django.contrib.sites.models import get_current_site
from django.shortcuts import render_to_response, redirect
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.contrib import messages

from CIM_Questionnaire.questionnaire.models.metadata_project import MetadataProject
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy
from CIM_Questionnaire.questionnaire.models.metadata_version import MetadataVersion
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataModelCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
from CIM_Questionnaire.questionnaire.views.views_error import questionnaire_error
from CIM_Questionnaire.questionnaire.utils import SUPPORTED_DOCUMENTS
from CIM_Questionnaire.questionnaire.utils import set_field_widget_attributes, update_field_widget_attributes, pretty_string
from CIM_Questionnaire.questionnaire import get_version


def questionnaire_project_index(request, project_name=""):

    if not project_name:
        return HttpResponseRedirect(reverse("index"))

    try:
        project = MetadataProject.objects.get(name__iexact=project_name, active=True)
    except MetadataProject.DoesNotExist:
        msg = "Could not find an active project named '%s'." % project_name
        return questionnaire_error(request, msg)

    all_ontologies = MetadataVersion.objects.filter(registered=True).order_by("key")
    all_proxies = MetadataModelProxy.objects.filter(
        stereotype__iexact="document",
        name__iregex=r'(' + '|'.join(SUPPORTED_DOCUMENTS) + ')',
        version__in=all_ontologies,
    )
    all_customizations = MetadataModelCustomizer.objects.filter(
        project=project,
        proxy__in=all_proxies,
    )
    all_models = MetadataModel.objects.filter(
        project=project,
        is_root=True,
        proxy__in=all_proxies
    ).order_by("name")

    class _NewCustomizationForm(forms.Form):
        # ontologies are all registered CIM versions
        ontologies = ModelChoiceField(queryset=all_ontologies, label="Ontolgoy", required=True, empty_label=None)

        # documents are all model proxies belonging to the above ontologies that have the 'document' stereotype
        documents = ModelChoiceField(queryset=all_proxies, label="Document Type", required=True, empty_label=None)

        def __init__(self, *args, **kwargs):
            super(_NewCustomizationForm, self).__init__(*args, **kwargs)
            function_name = "set_options(this,'%s-documents');" % self.prefix
            update_field_widget_attributes(self.fields["ontologies"], {
                "class": "changer",
            })
            set_field_widget_attributes(self.fields["ontologies"], {
                "onchange": function_name,
            })

    class _NewDocumentForm(forms.Form):
        # ontologies are all registered CIM versions that have a default customization for this project
        ontologies = ModelChoiceField(queryset=all_ontologies, label="Ontolgoy", required=True, empty_label=None)

        # documents are all model proxies belonging to the above ontologies that have the 'document' stereotype
        documents = ModelChoiceField(queryset=all_proxies, label="Document Type", required=True, empty_label=None)

        def __init__(self, *args, **kwargs):
            super(_NewDocumentForm, self).__init__(*args, **kwargs)
            function_name = "set_options(this,'%s-documents');" % self.prefix
            update_field_widget_attributes(self.fields["ontologies"], {
                "class": "changer",
            })
            set_field_widget_attributes(self.fields["ontologies"], {
                "onchange": function_name,
            })

    class _ExistingFormset(BaseModelFormSet):

        def find_selected_form(self):
            assert self.is_bound
            for form in self:
                key = u"%s-selected" % form.prefix
                if key in self.data:
                    return form
            return None

    class _ExistingCustomizationForm(ModelForm):
        class Meta:
            model = MetadataModelCustomizer
            fields = ["id", "selected", ]  # not sure why "id" is required, but it is

        selected = BooleanField(initial=False, required=False)

        def __init__(self, *args, **kwargs):
            super(_ExistingCustomizationForm, self).__init__(*args, **kwargs)
            update_field_widget_attributes(self.fields["selected"], {
                "class": "hidden",
            })

        def get_label(self):
            model = self.instance
            assert(model is not None)

            label_string = model.name
            if model.default:
                label_string += "&nbsp;*"
            return SafeString(label_string)

    class _ExistingDocumentForm(ModelForm):
        class Meta:
            model = MetadataModel
            fields = ["id", "selected", ]  # not sure why "id" is required, but it is

        selected = BooleanField(initial=False, required=False)

        def __init__(self, *args, **kwargs):
            super(_ExistingDocumentForm, self).__init__(*args, **kwargs)
            update_field_widget_attributes(self.fields["selected"], {
                "class": "hidden",
            })

        def get_label(self):
            model = self.instance
            assert(model is not None)

            label_string = model.get_label()
            if not label_string:
                label_string = "<i>(no label provided)</i>"
            label_string += "&nbsp;&nbsp;[%s]" % model.document_version
            return SafeString(label_string)

    def _ExistingDocumentFormsetFactory(*args, **kwargs):
        _queryset = kwargs.pop("queryset", None)
        _data = kwargs.pop("data", None)
        _prefix = kwargs.pop("prefix")

        _formset = modelformset_factory(
            MetadataModel,
            form=_ExistingDocumentForm,
            formset=_ExistingFormset,
            extra=0,
            can_delete=False
        )

        if _data:
            return _formset(_data, prefix=_prefix)
        elif _queryset:
            return _formset(queryset=_queryset, prefix=_prefix)

    def _ExistingCustomizationFormsetFactory(*args, **kwargs):
        _queryset = kwargs.pop("queryset", None)
        _data = kwargs.pop("data", None)
        _prefix = kwargs.pop("prefix")

        _formset = modelformset_factory(
            MetadataModelCustomizer,
            form=_ExistingCustomizationForm,
            formset=_ExistingFormset,
            extra=0,
            can_delete=False
        )

        if _data:
            return _formset(_data, prefix=_prefix)
        elif _queryset:
            return _formset(queryset=_queryset, prefix=_prefix)

    # dictionary mapping ontologies (versions) to documents (proxies)
    # (allows for dynamic select binding via JavaScript)
    # (bear in mind, though, that as a dictionary, it is implicitly unsortable)
    # (so there there is a bit of extra JavaScript to get the documents into alphabetical order)
    ontology_document_dict = {
        ontology.pk:
            {document.pk: u"%s" % document
             for document in all_proxies.filter(version=ontology)
             }
        for ontology in all_ontologies
    }

    if request.method == "GET":

        new_customization_form = _NewCustomizationForm(prefix="new_customization")
        existing_customization_formset = _ExistingCustomizationFormsetFactory(queryset=all_customizations, prefix="existing_customization")
        new_document_form = _NewDocumentForm(prefix="new_document")
        existing_document_formset = _ExistingDocumentFormsetFactory(queryset=all_models, prefix="existing_document")

    else:  # request.method == "POST":

        data = request.POST
        new_customization_form = _NewCustomizationForm(data, prefix="new_customization")
        existing_customization_formset = _ExistingCustomizationFormsetFactory(data=data, prefix="existing_customization")
        new_document_form = _NewDocumentForm(data, prefix="new_document")
        existing_document_formset = _ExistingDocumentFormsetFactory(data=data, prefix="existing_document")

        if u"%s-create" % new_customization_form.prefix in data:
            if new_customization_form.is_valid():
                ontology = new_customization_form.cleaned_data["ontologies"]
                document = new_customization_form.cleaned_data["documents"]
                url = reverse("customize_new", kwargs={
                    "project_name": project.name,
                    "version_key": ontology.get_key(),
                    "model_name": document.name.lower(),
                })
                return redirect(url)

        elif u"%s-create" % new_document_form.prefix in data:
            if new_document_form.is_valid():
                ontology = new_document_form.cleaned_data["ontologies"]
                document = new_document_form.cleaned_data["documents"]
                url = reverse("edit_new", kwargs={
                    "project_name": project.name,
                    "version_key": ontology.get_key(),
                    "model_name": document.name.lower(),
                })
                return redirect(url)

        elif u"%s-edit" % existing_document_formset.prefix in data:
            if existing_document_formset.is_valid():
                selected_form = existing_document_formset.find_selected_form()
                document = selected_form.instance
                url = reverse("edit_existing", kwargs={
                    "project_name": project.name,
                    "version_key": document.version.get_key(),
                    "model_name": document.proxy.name.lower(),
                    "model_id": document.pk,
                })
                return redirect(url)

        elif u"%s-view" % existing_document_formset.prefix in data:
            if existing_document_formset.is_valid():
                selected_form = existing_document_formset.find_selected_form()
                document = selected_form.instance
                url = reverse("view_existing", kwargs={
                    "project_name": project.name,
                    "version_key": document.version.get_key(),
                    "model_name": document.proxy.name.lower(),
                    "model_id": document.pk,
                })
                return redirect(url)

        elif u"%s-publish" % existing_document_formset.prefix in data:
            if existing_document_formset.is_valid():
                selected_form = existing_document_formset.find_selected_form()
                document = selected_form.instance
                document.publish()

                published_version = document.get_major_version()
                pretty_label = pretty_string(u"%s" % document)

                msg = u"Successfully published version %s of \"%s.\"" % (published_version, pretty_label)
                messages.add_message(request, messages.SUCCESS, msg)

        elif u"%s-edit" % existing_customization_formset.prefix in data:
            if existing_customization_formset.is_valid():
                selected_form = existing_customization_formset.find_selected_form()
                customization = selected_form.instance
                url = reverse("customize_existing", kwargs={
                    "project_name": project.name,
                    "version_key": customization.version.get_key(),
                    "model_name": customization.proxy.name.lower(),
                    "customizer_name": customization.name,
                })
                return redirect(url)
        else:
            msg = "unknown action"
            messages.add_message(request, messages.ERROR, msg)

    # gather all the extra information required by the template
    _dict = {
        "site": get_current_site(request),
        "project": project,
        "document_options": json.dumps(ontology_document_dict),
        "new_document_form": new_document_form,
        "existing_document_formset": existing_document_formset,
        "new_customization_form": new_customization_form,
        "existing_customization_formset": existing_customization_formset,
        "questionnaire_version": get_version(),
    }

    return render_to_response('questionnaire/questionnaire_project.html', _dict, context_instance=RequestContext(request))
