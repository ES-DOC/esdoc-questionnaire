
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
# import os
# from django.conf import settings
from django.contrib.syndication.views import Feed, FeedDoesNotExist
from django.utils.feedgenerator import Atom1Feed
from django.http import HttpResponse
from django.core.urlresolvers import reverse

from CIM_Questionnaire.questionnaire.models import MetadataProject, MetadataVersion, MetadataModelProxy, MetadataModel, MetadataModelSerialization
from CIM_Questionnaire.questionnaire.views.views_error import questionnaire_error

class MetadataFeed(Feed):

    feed_type = Atom1Feed
    link = "/feed/" # (not sure how this is used)
    title_template = "questionnaire/feed/_item_title.html"
    description_template = "questionnaire/feed/_item_description.html"

    def get_object(self, request, project_name=None, version_key=None, model_name=None):

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

            if version_key:
                try:
                    self.version = MetadataVersion.objects.get(key=version_key, registered=True)
                except MetadataVersion.DoesNotExist:
                    msg = "Cannot find the <u>version</u> '%s'.  Has it been registered?" % (version_key)
                    return questionnaire_error(request, msg)

                self.title += ", version=%s" % (self.version.name)

                if model_name:
                    try:
                        self.proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=model_name)
                    except MetadataModelProxy.DoesNotExist:
                        msg = "Cannot find the <u>model</u> '%s' in the <u>version</u> '%s'." % (model_name,self.version)
                        return questionnaire_error(request, msg)
                    if not self.proxy.is_document():
                        msg = "<u>%s</u> is not a recognized document type in the CIM." % model_name
                        return questionnaire_error(request, msg)

                    self.title += ", document_type=%s" % (self.proxy.name.title())


    def items(self):
        """
        returns all serializations for all published models in the db
        can be restricted by project/version/proxy
        """
        all_models = MetadataModel.objects.filter(is_published=True)
        if self.project:
            all_models = all_models.filter(project=self.project)
            if self.version:
                all_models = all_models.filter(version=self.version)
                if self.proxy:
                    all_models = all_models.filter(proxy=self.proxy)

        return MetadataModelSerialization.objects.filter(model__in=all_models).order_by("-publication_date")

    # using template for finer control over title format (see above)
    # def item_title(self, item):
    #      title_string = u"%s" % (item)
    #      return title_string

    # using template for finer control over description format (see above)
    # def item_description(self, item):
    #     pass

    def item_link(self, item):
        model = item.model
        url_args = [
            model.project.name.lower(),  # project
            model.version.get_key(),  # version
            model.proxy.name.lower(),    # model_type
            item.name,                  # serialization_name
            item.version,   # serialization_version
        ]
        item_url = reverse("serialize_specific_version", args=url_args)
        return item_url


#########################
# individual feed items #
#########################


def validate_view_arguments(project_name="", version_key="", model_name="", model_guid=None, model_version=None):
    """
    Ensures that the arguments passed to a view are valid (ie: resolve to active projects, models, versions)
    """

    (validity, project, version, model, msg) = \
        (True, None, None, None, "")

    project_name_lower = project_name.lower()

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
        version = MetadataVersion.objects.get(key=version_key, registered=True)
    except MetadataVersion.DoesNotExist:
        msg = "Cannot find the <u>version</u> '%s'.  Has it been registered?" % (version_key)
        validity = False
        return (validity, project, version, model, msg)

    # try to get the model (proxy)...
    try:
        proxy = MetadataModelProxy.objects.get(version=version, name__iexact=model_name)
    except MetadataModelProxy.DoesNotExist:
        msg = "Cannot find the <u>model</u> '%s' in the <u>version</u> '%s'." % (model_name, version)
        validity = False
        return (validity, project, version, model, msg)
    if not proxy.is_document():
        msg = "<u>%s</u> is not a recognized document type in the CIM." % model_name
        validity = False
        return (validity, project, version, model, msg)

    # try to get the actual model...
    try:
        model = MetadataModel.objects.get(project=project, version=version, proxy=proxy, guid=model_guid)
    except (ValueError, MetadataModel.DoesNotExist):
        msg = "Unable to find specified model."
        validity = False
        return (validity, project, version, model, msg)
    if not model.is_published:
        msg = "This model is not yet published"
        validity = False
        return (validity, project, version, model, msg)
    if model_version:
        try:
            MetadataModelSerialization.objects.get(model=model, version=model_version)
        except MetadataModelSerialization.DoesNotExist:
            msg = "Unable to find model published at version %s" % (model_version)
            validity = False
            return (validity, project, version, model, msg)

    return (validity, project, version, model, msg)


# NO LONGER SERIALIZING TO FILE
# INSTEAD SERIALIZING TO MODEL (MetadataModelSerialization) AND GENERATING ON-DEMAND
# SO THAT ATOM FEED CAN LIST ALL SERIALIZATIONS (ie: ALL VERSIONS) IN THE DB
# def questionnaire_serialize(request, project_name=None, version_name=None, model_name=None, model_guid=None, model_version=None):
#
#     # validate arguments...
#     # (if this view is invoked from the above feed, these checks are superfluous)
#     # (but if a user accesses this view directly, they are needed)
#     (validity, project, version, model, msg) = validate_view_arguments(project_name=project_name, version_name=version_name, model_name=model_name, model_guid=model_guid, model_version=model_version)
#     if not validity:
#         return questionnaire_error(request, msg)
#
#     serialized_model_path = os.path.join(settings.MEDIA_ROOT,"questionnaire/feed",model.project.name.lower(),model.version.name.lower(),model.proxy.name.lower())
#     if model_version:
#         serialized_model_path += u"/%s_%s.xml" % (model_guid, model_version)
#     else:
#         serialized_model_path += u"/%s_%s.xml" % (model_guid, model.get_major_version())
#
#     if not os.path.exists(serialized_model_path):
#         msg = "Unable to locate serialized file: %s" % (serialized_model_path)
#         return questionnaire_error(request, msg)
#
#     with open(serialized_model_path, "r") as file:
#         serialized_model = file.read()
#
#     return HttpResponse(serialized_model, content_type="text/xml")


def questionnaire_serialize(request, project_name=None, version_key=None, model_name=None, model_guid=None, model_version=None):

    # validate arguments...
    # (if this view is invoked from the above feed, these checks are superfluous)
    # (but if a user accesses this view directly, they are needed)
    (validity, project, version, model, msg) = validate_view_arguments(project_name=project_name, version_key=version_key, model_name=model_name, model_guid=model_guid, model_version=model_version)
    if not validity:
        return questionnaire_error(request, msg)

    serializations = MetadataModelSerialization.objects.filter(model=model).order_by("-version")

    if model_version:
        serialization = serializations.get(version=model_version)
    else:
        serialization = serializations[0]

    return HttpResponse(serialization.content, content_type="text/xml")
