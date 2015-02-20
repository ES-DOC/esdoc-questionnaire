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
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.contrib.sites.models import get_current_site
from django.shortcuts import render_to_response, redirect
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.contrib import messages
from django.conf import settings

from CIM_Questionnaire.questionnaire.forms.forms_project import NewModelForm, ExistingModelFormSetFactory
from CIM_Questionnaire.questionnaire.models.metadata_authentication import is_user_of, is_member_of, is_admin_of
from CIM_Questionnaire.questionnaire.models.metadata_project import MetadataProject
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy
from CIM_Questionnaire.questionnaire.models.metadata_version import MetadataVersion
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataModelCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
from CIM_Questionnaire.questionnaire.views.views_error import questionnaire_error
from CIM_Questionnaire.questionnaire.utils import SUPPORTED_DOCUMENTS, pretty_string
from CIM_Questionnaire.questionnaire import get_version


def questionnaire_project_index(request, project_name=""):

    if not project_name:
        return HttpResponseRedirect(reverse("index"))

    try:
        project = MetadataProject.objects.get(name__iexact=project_name, active=True)
    except MetadataProject.DoesNotExist:
        msg = "Could not find an active project named '%s'." % project_name
        return questionnaire_error(request, msg)

    # work out user roles...
    current_user = request.user
    can_customize = is_admin_of(current_user, project) or not project.authenticated
    can_edit = is_user_of(current_user, project) or not project.authenticated
    can_view = True
    can_join = not is_member_of(current_user, project) and current_user.is_authenticated()

    # get the querysets...
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

    # dictionary mapping ontologies (versions) to documents (proxies); this allows for dynamic drop-down menus via JS
    # (bear in mind, b/c it is implicitly unsortable, there is some extra JS required to alphabetize the documents)
    ontology_document_dict = {
        ontology.pk:
            {document.pk: u"%s" % document
             for document in all_proxies.filter(version=ontology)
             }
        for ontology in all_ontologies
    }

    site = get_current_site(request)

    if request.method == "GET":

        new_customization_form = NewModelForm(ontologies=all_ontologies, documents=all_proxies, prefix="new_customization")
        existing_customization_formset = ExistingModelFormSetFactory(model=MetadataModelCustomizer, queryset=all_customizations, prefix="existing_customization")
        new_document_form = NewModelForm(ontologies=all_ontologies, documents=all_proxies, prefix="new_document")
        existing_document_formset = ExistingModelFormSetFactory(model=MetadataModel, queryset=all_models, prefix="existing_document")

    else:  # request.method == "POST":

        data = request.POST
        new_customization_form = NewModelForm(data, ontologies=all_ontologies, documents=all_proxies, prefix="new_customization")
        existing_customization_formset = ExistingModelFormSetFactory(model=MetadataModelCustomizer, data=data, prefix="existing_customization")
        new_document_form = NewModelForm(data, ontologies=all_ontologies, documents=all_proxies, prefix="new_document")
        existing_document_formset = ExistingModelFormSetFactory(model=MetadataModel, data=data, prefix="existing_document")

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

        elif "project_join" in data:
            requested_permissions = ["default", "user", ]
            mail_content = "User '%s' wants to join project '%s' with the following permissions: %s.\n(Request sent from site: %s.)" % \
                (current_user.username, project.name, ", ".join([u"'%s'" % permission for permission in requested_permissions]), site.name)
            mail_from = settings.EMAIL_HOST_USER
            mail_to = [settings.EMAIL_HOST_USER, ]

            try:
                send_mail("ES-DOC Questionnaire project join request", mail_content, mail_from, mail_to, fail_silently=False)
                messages.add_message(request, messages.SUCCESS, "Successfully sent request.")
            except:
                messages.add_message(request, messages.ERROR, "Unable to send request.")

        else:
            msg = "unknown action"
            messages.add_message(request, messages.ERROR, msg)

    # gather all the extra information required by the template
    _dict = {
        "questionnaire_version": get_version(),
        "site": site,
        "project": project,
        "can_join": can_join,
        "can_view": can_view,
        "can_edit": can_edit,
        "can_customize": can_customize,
        "document_options": json.dumps(ontology_document_dict),
        "new_document_form": new_document_form,
        "existing_document_formset": existing_document_formset,
        "new_customization_form": new_customization_form,
        "existing_customization_formset": existing_customization_formset,
    }

    return render_to_response('questionnaire/questionnaire_project.html', _dict, context_instance=RequestContext(request))
