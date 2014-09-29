#    Django-CIM-Forms
#    Copyright (c) 2012 CoG. All rights reserved.
#
#    Developed by: Earth System CoG
#    University of Colorado, Boulder
#    http://cires.colorado.edu/
#
#    This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].

from django.contrib.syndication.views import Feed, FeedDoesNotExist
from django.utils.feedgenerator import Atom1Feed

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from django.utils.functional import curry

from django.template import *
from django.shortcuts import *
from django.http import *

from models import *


class MetadataFeed(Feed):
    feed_type = Atom1Feed
    title = "CIM Metadata Documents" # default title; ought to be replaced below
    link = "/feed/" # not certain how this is used; doesn't seem relevant

    app_name = ""
    model_type = ""
    ModelClasses = []

    def getTitle(self):
        return "CIM Metadata Documents for %s" % self.app_name.capitalize()

    def __init__(self):
        super(MetadataFeed,self).__init__()

    def items(self):
        items = []
        for ModelClass in self.ModelClasses:
            items += ModelClass.objects.all()#order_by("-created")
        for item in items:
            print item.created
        # TODO: why doesn't this comparator seem to work?
        return sorted(items,cmp=lambda item1,item2: (item1.created > item2.created))

    def item_link(self, item):
        url = "/metadata/xml/%s/%s/%s" % (self.app_name,item.getName().lower(),item.id)
        return url

    def item_description(self, item):
        # TODO: should I return the document type in the description?
        description = item.description
        if len(description):
            return "<p><b>Creation Date:&nbsp;</b>%s</p><p><b>Description:&nbsp;</b>%s</p>" % (item.created,description)
        return "<p><b>Creation Date:&nbsp;</b>%s</p>" % (item.created)

    def get_object(self, request, app_name, model_type="all"):
        self.app_name = app_name.lower()
        self.model_type = model_type.lower()

        try:
            PossibleClasses = [
                possibleClass for possibleClass in
                [contentType.model_class() for contentType in ContentType.objects.filter(app_label=self.app_name)]
                if issubclass(possibleClass,MetadataModel)# and not issubclass(possibleClass,MetadataProperty)
            ]
        except ObjectDoesNotExist:
            msg = "invalid model type '%s' in application '%s'" % (model_type, app_name)
            return HttpResponseBadRequest(msg)

        # TODO: this makes no distinction between different CIM versions (1.5 is hard-coded)
        if model_type != "all":
            try:
                ModelTypeClass = ContentType.objects.get(app_label="cim_1_5",model=self.model_type).model_class()
            except ObjectDoesNotExist:
                msg = "invalid model type '%s' in application '%s'" % (model_type, "cim_1_5")
                return HttpResponseBadRequest(msg)
            self.ModelClasses = [possibleClass for possibleClass in PossibleClasses if issubclass(possibleClass,ModelTypeClass) and possibleClass._isCIMDocument]
        else:
            self.ModelClasses = [possibleClass for possibleClass in PossibleClasses if possibleClass._isCIMDocument]

        self.title = self.getTitle()


# don't need to wrap feed in a view; I can pass parameters to the get_object() fn
#def generic_feed_view(request, model_name, app_name="django_cim_forms", model_id=None):
#    # get the model & form...
#    try:
#        ModelType  = ContentType.objects.get(app_label=app_name.lower(),model=model_name.lower())
#    except ObjectDoesNotExist:
#        msg = "invalid model type '%s' in application '%s'" % (model_name, app_name)
#        return HttpResponseBadRequest(msg)
#
#    return MetadataFeed()
