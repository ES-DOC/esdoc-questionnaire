
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


from django import forms
from django.forms import *

from questionnaire.views  import *
from questionnaire.models import *
from questionnaire.utils  import get_version

def questionnaire_index(request):
    """The default view for the CIM Questionnaire.  Provides a choice of active projects to visit."""
    active_projects = MetadataProject.objects.filter(active=True)

    class _IndexForm(forms.Form):
        class Meta:
            fields  = ("projects",)

        projects = ModelChoiceField(queryset=active_projects,label="Active Metadata Projects",required=True)
        projects.help_text = "This is a list of all projects that have registered as 'active' with the CIM Questionnaire."

        #def __init__(self,*args,**kwargs):
        #    super(_IndexForm,self).__init__(*args,**kwargs)

    if request.method == "POST":
        form = _IndexForm(request.POST)
        if form.is_valid():
            project             = form.cleaned_data["projects"]
            project_index_url   = reverse("project_index",kwargs={
                "project_name"      : project.name,
            })
            return HttpResponseRedirect(project_index_url)

    else: # request.method == "GET":
        form = _IndexForm()
      
    # gather all the extra information required by the template
    dict = {
        "site"                  : get_current_site(request),
        "form"                  : form,
        "questionnaire_version" : get_version(),
    }

    return render_to_response('questionnaire/questionnaire_index.html', dict, context_instance=RequestContext(request))


def questionnaire_project_index(request,project_name=""):

    if not project_name:
        return HttpResponseRedirect(reverse("index"))

    try:
        project = MetadataProject.objects.get(name__iexact=project_name,active=True)
    except MetadataProject.DoesNotExist:
        msg = "Could not find an active project named '%s'." % (project_name)
        return error(request,msg)

    all_versions = MetadataVersion.objects.filter(registered=True)
    all_proxies = MetadataModelProxy.objects.filter(stereotype__iexact="document",version__in=all_versions)
    all_customizers = MetadataModelCustomizer.objects.filter(project=project,proxy__in=all_proxies)
    all_models = MetadataModel.objects.filter(project=project,is_root=True,proxy__in=all_proxies,is_document=True)
    
    class _AdminIndexForm(forms.Form):

        versions        = ModelChoiceField(queryset=all_versions,label="Metadata Version",required=True)
        proxies         = ModelChoiceField(queryset=all_proxies,label="Metadata Model Type",required=True)
        customizations  = ModelChoiceField(queryset=all_customizers,label="Form Customization",required=False)
        customizations.help_text = "If this field is left blank, a <i>new</i> customization will be created."

    class _UserIndexForm(forms.Form):

        versions        = ModelChoiceField(queryset=all_versions,label="Metadata Version",required=True)
        proxies         = ModelChoiceField(queryset=all_proxies,label="Metadata Model Type",required=True)
        models          = ModelChoiceField(queryset=all_models,label="Metadata Model",required=False)
        models.help_text = "If this field is left blank, a <i>new</i> model will be created."

    class _DefaultIndexForm(forms.Form):

        versions        = ModelChoiceField(queryset=all_versions,label="Metadata Version",required=True)
        proxies         = ModelChoiceField(queryset=all_proxies,label="Metadata Model Type",required=True)
        models          = ModelChoiceField(queryset=all_models,label="Metadata Model",required=True)

    # TODO: SETUP ENABLERS

    if request.method == "GET":

        admin_form   = _AdminIndexForm(prefix="admin")
        user_form    = _UserIndexForm(prefix="user")
        default_form = _DefaultIndexForm(prefix="default")

    else: # requst.method == "POST"

        admin_form   = _AdminIndexForm(request.POST,prefix="admin")
        user_form    = _UserIndexForm(request.POST,prefix="user")
        default_form = _DefaultIndexForm(request.POST,prefix="default")

        if "admin_submit" in request.POST:
            # TODO: WHY ARE THESE LINES NEEDED IF THE CORRESPONDING "is_valid()" FN NEVER GETS CALLED?
            remove_form_errors(user_form)
            remove_form_errors(default_form)
            if admin_form.is_valid():
                version = admin_form.cleaned_data["versions"]
                proxy = admin_form.cleaned_data["proxies"]
                customization = admin_form.cleaned_data["customizations"]
                if customization:
                    url = "/%s/customize/%s/%s?name=%s" % (project_name,version.name,proxy.name,customization.name)
                else:
                    url = "/%s/customize/%s/%s" % (project_name,version.name,proxy.name)
                return redirect(url)
            
        elif "user_submit" in request.POST:
            # TODO: WHY ARE THESE LINES NEEDED IF THE CORRESPONDING "is_valid()" FN NEVER GETS CALLED?
            remove_form_errors(admin_form)
            remove_form_errors(default_form)
            if user_form.is_valid():
                version = user_form.cleaned_data["versions"]
                proxy = user_form.cleaned_data["proxies"]
                model = user_form.cleaned_data["models"]
                if model:
                    url = "/%s/edit/%s/%s/%s" % (project_name,version.name,proxy.name,model.pk)
                else:
                    url = "/%s/edit/%s/%s" % (project_name,version.name,proxy.name)
                return redirect(url)

        elif "default_submit" in request.POST:
            # TODO: WHY ARE THESE LINES NEEDED IF THE CORRESPONDING "is_valid()" FN NEVER GETS CALLED?
            remove_form_errors(admin_form)
            remove_form_errors(user_form)
            if default_form.is_valid():
                version = default_form.cleaned_data["versions"]
                proxy = default_form.cleaned_data["proxies"]
                model = default_form.cleaned_data["models"]
                url = "/%s/view/%s/%s/%s" % (project_name,version.name,proxy.name,model.pk)
                return redirect(url)

        else:
            msg = "unknown action recieved."
            messages.add_message(request, messages.ERROR, msg)
        

    # gather all the extra information required by the template
    dict = {
        "site"          : get_current_site(request),
        "project"       : project,
        "admin_form"    : admin_form,
        "user_form"     : user_form,
        "default_form"  : default_form,
        "questionnaire_version" : get_version(),
    }


    return render_to_response('questionnaire/questionnaire_project_index.html', dict, context_instance=RequestContext(request))
