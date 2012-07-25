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

    ModelClass = None
    app_name = ""
    model_name = ""

    def getTitle(self):
        title = "CIM Metadata Feed for %ss" % self.ModelClass.getTitle()
        return title
    
    def __init__(self):
        super(MetadataFeed,self).__init__()

    def items(self):
        return self.ModelClass.objects.order_by("-created")

    def item_link(self, item):
        url = "/metadata/xml/%s/%s/%s" % (self.app_name,self.model_name,item.id)
        return url

    def item_description(self, item):
        description = item.description
        if len(description):
            return "<p><b>Description:</b> %s</p><p><b>Creation Date:</b> %s</p>" % (description,item.created)
        return "<p>%s</p><p><b>Creation Date:</b> %s</p>" % (item,item.created)

    def get_object(self, request, app_name, model_name):
        self.app_name = app_name.lower()
        self.model_name = model_name.lower()
        
        try:
            ModelType  = ContentType.objects.get(app_label=app_name.lower(),model=model_name.lower())
        except ObjectDoesNotExist:
            msg = "invalid model type '%s' in application '%s'" % (model_name, app_name)
            return HttpResponseBadRequest(msg)
        
        self.ModelClass = ModelType.model_class()
        self.title = self.getTitle()
        
        return self.ModelClass.objects.order_by("-created")


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
