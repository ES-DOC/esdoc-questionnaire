#    Django-CIM-Forms
#    Copyright (c) 2012 CoG. All rights reserved.
#
#    Developed by: Earth System CoG
#    University of Colorado, Boulder
#    http://cires.colorado.edu/
#
#    This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].

import os

from lxml import etree as et

from django.template import *
from django.shortcuts import *
from django.http import *

from django_cim_forms.helpers import *


def _get_cv_filepath(cv_name):
    """Returns cv filepath dervied from cv name."""
    path = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(path, 'cv')
    path = os.path.join(path, cv_name + ".xml")

    return path


def _run_xpath(cv_text, cv_query):
    """Evaluates a cv xpath expression."""
    try:
        cv = et.fromstring(cv_text, et.XMLParser(remove_blank_text=True))
        cv = cv.xpath(cv_query, smart_strings=False)
        cv = reduce(lambda results, item : results.append(item), cv, et.Element("results"))
        return HttpResponse(et.tostring(cv, pretty_print=True), mimetype="text/xml")        
    except:# XPathSyntaxError, e:
        return HttpResponseBadRequest("error evaluating xpath expression: {0}.".format(cv_query))


def detail(request, cv_name):
    try:
        with open(_get_cv_filepath(cv_name), "rb") as cv:
            cv_text = cv.read()
            cv_query = request.GET.get('q')
            if cv_query:
                cv_query = cv_query.rstrip('\"').lstrip('\"')
                return _run_xpath(cv_text, cv_query)
            else:
                return HttpResponse(cv_text, mimetype="text/xml")
    except:
        return HttpResponseBadRequest("error retrieving cv: {0}".format(cv_name))


