
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
__date__ ="Sep 30, 2013 3:04:42 PM"

"""
.. module:: views

Summary of module goes here

"""

import openid.store.filestore
import openid.consumer.consumer

from django.forms import *

from questionnaire.views import *

def login(request):

    class _OpenIdForm(forms.Form):
        class Meta:
            pass

        url = CharField(max_length=64,required=True)

        def __init__(self,*args,**kwargs):
            super(_OpenIdForm,self).__init__(*args,**kwargs)

    form = _OpenIdForm()

    if request.method == 'POST':
        pass
    else:
        pass

    return render_to_response('questionnaire/openid/login.html', {"form":form}, context_instance=RequestContext(request))


def process(request):

    return render_to_response('questionnaire/questionnaire_login.html', {}, context_instance=RequestContext(request))
