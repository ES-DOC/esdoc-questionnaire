
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
__date__ ="Feb 1, 2013 4:45:10 PM"

"""
.. module:: views_error

Summary of module goes here

"""

from django.template import *
from django.shortcuts import *
from django.http import *

from dcf.utils import *

def error(request,error_msg="",status_code=400):

    print error_msg

    template    = loader.get_template('dcf/dcf_error.html')
    context     = RequestContext(request,{"error_msg":error_msg,"status_code":status_code})
    response    = HttpResponse(template.render(context),status=status_code)

    return response