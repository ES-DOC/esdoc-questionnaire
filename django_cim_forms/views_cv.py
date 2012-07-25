#    Django-CIM-Forms
#    Copyright (c) 2012 CoG. All rights reserved.
#
#    Developed by: Earth System CoG
#    University of Colorado, Boulder
#    http://cires.colorado.edu/
#
#    This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].

from lxml import etree as et

from django.template import *
from django.shortcuts import *
from django.http import *

import os
rel = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

et_parser = et.XMLParser(remove_blank_text=True)

from django_cim_forms.helpers import *

def detail(request,cv_name):
    cv_filename = cv_name + ".xml"
    cv_filepath = rel('cv/') + cv_filename
    cv_query = request.GET.get('q')

    try:
        cv_text = open(cv_filepath, "rb").read()
        if cv_query:
            return run_xpath(cv_text,cv_query.rstrip('\"').lstrip('\"'))
        return HttpResponse(cv_text, mimetype="text/xml")
    except:
        msg = "error retrieving cv: ", cv_name
        return HttpResponseBadRequest(msg)

################################################
# evaluate an xpath expression on a cv         #
# (the expression is passed via HTTP GET above #
################################################

def run_xpath(cv_text,cv_query):
    cv_tree = et.fromstring(cv_text,et_parser)
    try:
        results = et.Element("results")
        for node in cv_tree.xpath(cv_query):
            results.append(node)
        return HttpResponse(et.tostring(results,pretty_print=True),mimetype="text/xml")
    except:# XPathSyntaxError, e:
        msg = "error evaluating xpath expression: " % cv_query
        return HttpResponseBadRequest(msg)

