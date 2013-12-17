
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
__date__ ="Dec 5, 2013 2:16:31 PM"

"""
.. module:: views_test

Summary of module goes here

"""

from questionnaire.views import *

@login_required
#@permission_required('test')
def test(request):
    print request.user
    return render_to_response('questionnaire/questionnaire_test.html', {}, context_instance=RequestContext(request))
