####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"


from django.contrib.syndication.views import Feed, FeedDoesNotExist
from django.utils.feedgenerator import Atom1Feed
from django.http import HttpResponse
from django.core.urlresolvers import reverse

from Q.questionnaire.models import QProject, QOntology, MetadataModel, QPublication
from Q.questionnaire.views.views_base import validate_view_arguments
from Q.questionnaire.views.views_errors import q_error


class QFeed(Feed):

    feed_type = Atom1Feed
    link = "/feed/"  # (not sure how this is used)
    title_template = "questionnaire/feed/_item_title.html"
    description_template = "questionnaire/feed/_item_description.html"

    def get_object(self, request, project_name=None, ontology_key=None, document_type=None):
        """
        get_object parses the request sent from urls.py
        it sets some internal variables so that items() knows which models to expose
        """

        # TODO: THIS DOES NOT HANDLE INVALID ARGUMENTS CORRECTLY
        # TODO: SEE http://stackoverflow.com/questions/25817904/django-generate-error-on-atom-feed-request
        # check the arguments...
        validity, self.project, self.ontology, self.proxy, msg = validate_view_arguments(
            project_name=project_name,
            ontology_key=ontology_key,
            document_type=document_type
        )
        if not validity:
            return q_error(request, msg)

        self.title = "Published CIM Documents"
        if self.project:
            self.title += " project={0}".format(self.project.title)
            if self.ontology:
                self.title += ", ontology={0}".format(self.ontology)
                if self.proxy:
                    self.title += ", document_type={0}".format(self.proxy.name.title())

    def items(self):
        """
        returns all serializations for all published models in the db
        can be restricted by project/version/proxy
        """
        all_published_models = MetadataModel.objects.filter(is_published=True)
        if self.project:
            all_published_models = all_published_models.filter(project=self.project)
            if self.ontology:
                all_published_models = all_published_models.filter(version=self.ontology)
                if self.proxy:
                    all_published_models = all_published_models.filter(proxy=self.proxy)

        return QPublication.objects.filter(model__in=all_published_models).order_by("-created")

    # TODO: STOP USING TEMPLATES; HARD-CODE THIS
    # using template for finer control over title format (see above)
    # def item_title(self, item):
    #      title_string = u"%s" % (item)
    #      return title_string

    # TODO: STOP USING TEMPLATES; HARD-CODE THIS
    # using template for finer control over description format (see above)
    # def item_description(self, item):
    #     pass

    def item_link(self, item):
        model = item.model
        url_args = [
            model.project.name.lower(),  # project
            model.version.get_key(),  # version
            model.proxy.name.lower(),  # model_type
            item.name,  # serialization_name
            item.version,  # serialization_version
        ]
        item_url = reverse("publication_version", args=url_args)
        return item_url


#########################
# single feed instances #
#########################

def q_publication(request, project_name=None, ontology_key=None, document_type=None, guid=None, version=None):

    # validate arguments...
    # (if this view is invoked from the above feed, these checks are superfluous)
    # (but if a user accesses this view directly, they are needed)
    validity, project, ontology, proxy, msg = validate_view_arguments(
        project_name=project_name,
        ontology_key=ontology_key,
        document_type=document_type
    )
    if not validity:
        return q_error(request, msg)

    # try to get the actual model...
    try:
        model = MetadataModel.objects.get(
            project=project,
            version=ontology,
            proxy=proxy,
            guid=guid,
        )
    except (ValueError, MetadataModel.DoesNotExist):
        msg = "Unable to find specified model."
        return q_error(request, msg)
    if not model.is_published:
        msg = "This model is not yet published"
        return q_error(request, msg)

    publications = QPublication.objects.filter(model=model).order_by("-version")
    if version:
        try:
            publication = publications.get(version=version)
        except QPublication.DoesNotExist:
            msg = "Unable to find model published at version {0}".format(version)
            return q_error(request, msg)
    else:
        publication = publications[0]

    return HttpResponse(publication.content, content_type="text/xml")
