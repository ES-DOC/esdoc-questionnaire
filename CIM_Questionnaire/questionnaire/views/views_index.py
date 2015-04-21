
####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Sep 30, 2013 3:04:42 PM"

"""
.. module:: views

Summary of module goes here

"""

from django.forms import *
from django.core.urlresolvers import reverse
from django.contrib.sites.models import get_current_site
from django.shortcuts import render_to_response, redirect
from django.http import HttpResponseRedirect
from django.template import RequestContext

from CIM_Questionnaire.questionnaire.models.metadata_project import MetadataProject
from CIM_Questionnaire.questionnaire.fields import SingleSelectWidget
from CIM_Questionnaire.questionnaire.utils import update_field_widget_attributes
from CIM_Questionnaire.questionnaire import get_version


def questionnaire_index(request):
    """The default view for the CIM Questionnaire.  Provides a choice of active projects to visit."""
    active_projects = MetadataProject.objects.filter(active=True)

    class _IndexForm(forms.Form):
        class Meta:
            fields = ("projects", )

        projects = ModelChoiceField(queryset=active_projects, label="Active Metadata Projects", required=True)
        projects.help_text = "This is a list of all projects that have registered as 'active' with the CIM Questionnaire."

        def __init__(self, *args, **kwargs):
            super(_IndexForm, self).__init__(*args, **kwargs)
            projects_field = self.fields["projects"]
            projects_field.empty_label = None
            projects_field.widget = SingleSelectWidget(choices=projects_field.choices)
            update_field_widget_attributes(projects_field, {"class": "multiselect single selection_required start_open", })

    if request.method == "POST":
        form = _IndexForm(request.POST)
        if form.is_valid():
            project = form.cleaned_data["projects"]
            project_index_url = reverse("project_index", kwargs={
                "project_name": project.name,
            })
            return HttpResponseRedirect(project_index_url)

    else:  # request.method == "GET":
        form = _IndexForm()
      
    # gather all the extra information required by the template
    _dict = {
        "site": get_current_site(request),
        "form": form,
        "questionnaire_version": get_version(),
    }

    return render_to_response('questionnaire/questionnaire_index.html', _dict, context_instance=RequestContext(request))
