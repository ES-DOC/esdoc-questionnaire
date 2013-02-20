
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
__date__ ="Feb 1, 2013 4:33:04 PM"

"""
.. module:: views_test

Summary of module goes here

"""

from django.template import *
from django.shortcuts import *
from django.http import *

from dcf.utils import *

def test(request,version_name="",project_name="",model_name=""):

#    categorization = MetadataCategorization.objects.get(pk=1)
#    print categorization
#
#    newCategory = MetadataAttributeCategory()
#    print newCategory.getGUID()
#    newCategory.save()
#    newCategory = MetadataPropertyCategory()
#    print newCategory.getGUID()
#    newCategory.save()
#    newCategory = MetadataPropertyCategory()
#    print newCategory.getGUID()
#    newCategory.save()
#    attributeCategories = MetadataAttributeCategory.objects.all()
#    print attributeCategories
#
#    propertyCategories = MetadataPropertyCategory.objects.all()
#    print propertyCategories
#
#    print "BEFORE: %s" % categorization.getCategories()
#    categorization.addCategories(attributeCategories)
#    print "ADDED ATTRIBUTES %s" % categorization.getCategories()
#    categorization.addCategory(propertyCategories[0])
#    print "ADDED PROPERTY %s" % categorization.getCategories()
#
#    print "JUST GET ONE: %s" % categorization.getPropertyCategories()
#

    template = loader.get_template("dcf/glisaclimate.html")
    context = RequestContext(request,{})
    response = HttpResponse(template.render(context))
    return response
