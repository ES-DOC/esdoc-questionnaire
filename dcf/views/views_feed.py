
####################
#   Django-CIM-Forms
#   Copyright (c) 2012 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Jun 25, 2013 9:17:28 PM"

"""
.. module:: views_feed

Summary of module goes here

"""

from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from django.core.exceptions import ObjectDoesNotExist

from django.template import *
from django.http import *
from django.shortcuts import *


from dcf.models import *
from dcf.views.views_error import error as dcf_error

# NOTE: IN ORDER FOR item_link() TO WORK, THE CURRENT DOMAIN MUST BE REGISTERED IN admin/sites !

def check_feed_parameters(request,project_name="",version_number="",model_name=""):

    # try to get the requested project...
    try:
        project = MetadataProject.objects.get(name__iexact=project_name)
    except ObjectDoesNotExist:
        msg = "Cannot find the project '%s'.  Has it been registered?" % project_name
        return dcf_error(request,msg)

    # try to get the requested version...
    if version_number:
        try:
            version = MetadataVersion.objects.get(name__iexact=METADATA_NAME,number=version_number)
        except ObjectDoesNotExist:
            msg = "Cannot find version '%s_%s'.  Has it been registered?" % (METADATA_NAME,version_number)
            return dcf_error(request,msg)
    else:
        version = project.getDefaultVersion()
        if not version:
            msg = "please specify a version; the '%s' project has no default one." % project.getName()
            return dcf_error(request,msg)


    # try to get the requested model...
    model_class = version.getModelClass(model_name)

    return (project,version,model_class)

class MetadataFeed(Feed):

    feed_type   = Atom1Feed
    title       = "CIM Documents"
    link        = "/feed/"
    subtitle    = "Currently Published CIM Documents"

    project         = None
    version         = None

    model_classes   = []



    def get_object(self,request,project_name="",version_number="",model_name=""):

        (project,version,model_class) = check_feed_parameters(request,project_name,version_number,model_name)

        self.project = project
        self.version = version

        if model_class:
            self.title = "CIM %s Documents for %s" % (model_class.getTitle(), project.getTitle())
            self.model_classes = [model_class]

        else:
            self.title = "CIM Documents for %s" % (project.getTitle())

            self.model_classes = \
                [model_class for model_class in version.getAllModelClasses() if model_class and model_class._is_metadata_document]


    def items(self):
        items = []
        for model_class in self.model_classes:
            potential_items = model_class.objects.filter(published=True)
            if potential_items:
                items += potential_items
        return items

    def item_link(self, item):
        url = "/dcf/feed/%s/%s/%s/%s" % (self.project.name.lower(), item.getName().lower(), self.version.number, item.id)
        return url

    def item_description(self,item):
        try:
            description = item.description
            if len(description):
                return description
            else:
                return ""
        except:
            return ""

    def item_title(self,item):
        try:
            title = u"%s: '%s' (%s)" % (item.getTitle(), item.shortName, item.component_name)
            return title
        except:
            return item.getTitle()

def serialize(request,project_name="",version_number="",model_name="",model_id=""):

    (project,version,model_class) = check_feed_parameters(request,project_name,version_number,model_name)

    # try to get the requested model...
    try:
        model_instance = model_class.objects.get(pk=model_id)
    except ObjectDoesNotExist:
        msg = "Cannot find the specified model.  Please try again."
        return dcf_error(request,msg)
    if not model_instance.isDocument():
        msg = "The model type '%s' is not an editable metadata document" % (model_class.getTitle())
        return dcf_error(request,msg)
    if not model_instance.isPublished():
        msg = "This model has not yet been published."
        return dcf_error(request,msg)
 
    # CIM templates are stored as static files of the version
    # in order for this to work, the static location must be added to TEMPLATE_DIRS in settings.py
    cim_template_path = "%s/xml/%s.xml" % (version.getAppName(),model_class.getName().lower())
    rendered_instance = django.template.loader.render_to_string(cim_template_path, {"model" : model_instance})
    return HttpResponse(rendered_instance, mimetype="text/xml")

