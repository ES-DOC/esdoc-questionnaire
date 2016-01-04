####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

"""
silly script to make sure that I'll be able to call all of the real scripts in the current environment
"""

import os

try:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Q.settings")
except:
    print("unable to load Django")

try:
    from Q.questionnaire.models import *
except:
    print("unable to load Questionnaire")

print("successfully loaded Django & Questionnaire")