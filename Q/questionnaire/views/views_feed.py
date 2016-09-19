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

from Q.questionnaire.models import QProject, QOntology, QModelProxy, QModel, QPublication
from Q.questionnaire.views.views_errors import q_error


def validate_view_arguments(project_name=None, ontology_key=None, document_type=None):

    validity, project, ontology, proxy, msg = \
        True, None, None, None, ""

    if project_name:
        # try to get the project...
        try:
            project = QProject.objects.get(name=project_name)
        except QProject.DoesNotExist:
            msg = "Cannot find the project '{0}'.  Has it been registered?".format(project_name)
            validity = False
            return validity, project, ontology, proxy, msg
        if not project.is_active:
            msg = "Project '{0}' is inactive.".format(project_name)
            validity = False
            return validity, project, ontology, proxy, msg

    if ontology_key:
        # try to get the ontology...
        try:
            # this bit allows underspecification of the ontology version...
            ontology = QOntology.objects.filter_by_key(ontology_key).get(is_registered=True)
        except QOntology.DoesNotExist:
            msg = "Cannot find the ontology '{0}'.  Has it been registered?".format(ontology_key)
            validity = False
            return validity, project, ontology, proxy, msg
        if ontology not in project.ontologies.all():
            msg = "The ontology '{0}' is not associated with the project '{1}'.".format(ontology, project)
            validity = False
            return validity, project, ontology, proxy, msg

    if document_type:
        # try to get the proxy...
        try:
            proxy = QModelProxy.objects.get(ontology=ontology, name__iexact=document_type)
        except QModelProxy.DoesNotExist:
            msg = "Cannot find the document type '{0}' in the ontology '{1}'.".format(document_type, ontology)
            validity = False
            return validity, project, ontology, proxy, msg
        if not proxy.is_document():
            msg = "'{0}' is not a recognized document type in the ontology.".format(document_type)
            validity = False
            return validity, project, ontology, proxy, msg

    # whew, we made it...
    return validity, project, ontology, proxy, msg


class QFeed(Feed):

    feed_type = Atom1Feed
    link = "/feed/"  # not sure how this is used
    title_template = "questionnaire/feed/_q_feed_item_title.html"
    description_template = "questionnaire/feed/_q_feed_item_description.html"

    def get_object(self, request, project_name=None, ontology_key=None, document_type=None):
        """
        get_object parses the request sent from urls.py
        it also sets some internal variables so that items() knows which models to expose
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
        publications = QModel.objects.published_documents()
        if self.project:
            publications = publications.filter(project=self.project)
            if self.ontology:
                publications = publications.filter(ontology=self.ontology)
                if self.proxy:
                    publications = publications.filter(proxy=self.proxy)

        return QPublication.objects.filter(model__in=publications).order_by("-created")

        # TODO: STOP USING TEMPLATES; HARD-CODE THIS
        # using template for finer control over title format (see above)
        # def item_title(self, item):
        #      title_string = u"%s" % (item)
        #      return title_string

        # TODO: STOP USING TEMPLATES; HARD-CODE THIS
        # using template for finer control over description format (see above)
        # def item_description(self, item):
        #     pass
