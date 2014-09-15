
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
__date__ ="Dec 18, 2013 1:32:37 PM"

"""
.. module:: questionnaire_feed

Summary of module goes here

"""
from django.contrib.syndication.views import Feed, FeedDoesNotExist
from django.utils.feedgenerator import Atom1Feed
from django.http import HttpResponse
from django.core.urlresolvers import reverse

from CIM_Questionnaire.questionnaire.models import MetadataProject, MetadataVersion, MetadataModelProxy, MetadataModel
from CIM_Questionnaire.questionnaire.views.views_error import questionnaire_error

class MetadataFeed(Feed):

    feed_type = Atom1Feed
    link = "/feed/" # (not sure how this is used)
    title_template = "questionnaire/_feed_item_title.html"
    description_template = "questionnaire/_feed_item_description.html"

    def get_object(self, request, project_name=None, version_name=None, model_name=None):

        """
        get_object parses the request sent from urls.py
        it sets some internal variables so that items() knows which models to expose
        """

        self.project = None
        self.version = None
        self.proxy = None
        self.title = "Published CIM Documents"

        # TODO: THIS DOES NOT HANDLE INVALID ARGUMENTS CORRECTLY
        # TODO: SEE http://stackoverflow.com/questions/25817904/django-generate-error-on-atom-feed-request
        # validate the arguments...
        if project_name:
            try:
                self.project = MetadataProject.objects.get(name__iexact=project_name)
            except MetadataProject.DoesNotExist:
                return HttpResponse("hi")
                msg = "Cannot find the <u>project</u> '%s'.  Has it been registered?" % (project_name)
                return questionnaire_error(request, msg)
            if not self.project.active:
                msg = "Project '%s' is inactive." % (project_name)
                return questionnaire_error(request, msg)

            self.title += " project=%s" % (self.project.title)

            if version_name:
                try:
                    self.version = MetadataVersion.objects.get(name__iexact=version_name, registered=True)
                except MetadataVersion.DoesNotExist:
                    msg = "Cannot find the <u>version</u> '%s'.  Has it been registered?" % (version_name)
                    return questionnaire_error(request, msg)

                self.title += ", version=%s" % (self.version.name)

                if model_name:
                    try:
                        self.proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=model_name)
                    except MetadataModelProxy.DoesNotExist:
                        msg = "Cannot find the <u>model</u> '%s' in the <u>version</u> '%s'." % (model_name,version_name)
                        return questionnaire_error(request, msg)
                    if not self.proxy.is_document():
                        msg = "<u>%s</u> is not a recognized document type in the CIM." % model_name
                        return questionnaire_error(request, msg)

                    self.title += ", document_type=%s" % (self.proxy.name.title())


    def items(self):
        """
        returns all published models in the db
        can be restricted by project/version/proxy
        """
        all_items = MetadataModel.objects.filter(is_published=True)
        if self.project:
            all_items = all_items.filter(project=self.project)
            if self.version:
                all_items = all_items.filter(version=self.version)
                if self.proxy:
                    all_items = all_items.filter(proxy=self.proxy)
        return all_items.order_by("-published")

    # using template for finer control over title format (see above)
    # def item_title(self, item):
    #      title_string = u"%s" % (item)
    #      return title_string

    # using template for finer control over description format (see above)
    # def item_description(self, item):
    #     pass

    def item_link(self, item):

        url_args = [
            item.project.name.lower(),  # project
            item.version.name.lower(),  # version
            item.proxy.name.lower(),    # model_type
            item.pk,                    # model_id
        ]
        item_url = reverse("serialize", args=url_args)
        return item_url


#########################
# individual feed items #
#########################


def validate_view_arguments(project_name="", version_name="", model_name="", model_id=-1):
    """
    Ensures that the arguments passed to a view are valid (ie: resolve to active projects, models, versions)
    """

    (validity, project, version, model, msg) = \
        (True, None, None, None, "")

    project_name_lower = project_name.lower()
    version_name_lower = version_name.lower()

    # try to get the project...
    try:
        project = MetadataProject.objects.get(name=project_name_lower)
    except MetadataProject.DoesNotExist:
        msg = "Cannot find the <u>project</u> '%s'.  Has it been registered?" % (project_name)
        validity = False
        return (validity, project, version, model, msg)

    if not project.active:
        msg = "Project '%s' is inactive." % (project_name)
        validity = False
        return (validity, project, version, model, msg)

    # try to get the version...
    try:
        version = MetadataVersion.objects.get(name=version_name_lower, registered=True)
    except MetadataVersion.DoesNotExist:
        msg = "Cannot find the <u>version</u> '%s'.  Has it been registered?" % (version_name)
        validity = False
        return (validity, project, version, model, msg)

    # try to get the model (proxy)...
    try:
        proxy = MetadataModelProxy.objects.get(version=version, name__iexact=model_name)
    except MetadataModelProxy.DoesNotExist:
        msg = "Cannot find the <u>model</u> '%s' in the <u>version</u> '%s'." % (model_name, version_name)
        validity = False
        return (validity, project, version, model, msg)
    if not proxy.is_document():
        msg = "<u>%s</u> is not a recognized document type in the CIM." % model_name
        validity = False
        return (validity, project, version, model, msg)

    # try to get the actual model...
    try:
        model = MetadataModel.objects.get(project=project, version=version, proxy=proxy, pk=model_id)
    except (ValueError, MetadataModel.DoesNotExist):
        msg = "Unable to find specified model."
        validity = False
        return (validity, project, version, model, msg)
    if not model.is_published:
        msg = "This model is not yet published"
        validity = False
        return (validity, project, version, model, msg)

    return (validity, project, version, model, msg)


def questionnaire_serialize(request, project_name=None, version_name=None, model_name=None, model_id=None):

    # validate arguments...
    (validity, project, version, model, msg) = validate_view_arguments(project_name=project_name, version_name=version_name, model_name=model_name, model_id=model_id)
    if not validity:
        return questionnaire_error(request, msg)

    return HttpResponse("hi")
