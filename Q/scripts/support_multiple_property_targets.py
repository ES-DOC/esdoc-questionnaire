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

"""
stand-alone script to convert proxies/customizations/realizations from only supporting a single relationship target
to supporing multiple relationship targets
"""

import django
import sys
import os

rel = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

# a bit of hackery to get this to run outside of the manage.py script
sys.path.append(rel(".."))  # note that "/scripts" is 1 directory below the project settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()
# now I can do Django & Questionnaire stuff...

from Q.questionnaire.models import *
from Q.questionnaire.q_fields import QPropertyTypes

# deal w/ proxies...
standard_property_proxies = QStandardPropertyProxy.objects.all()
for standard_property_proxy in standard_property_proxies:
    if standard_property_proxy.field_type == QPropertyTypes.RELATIONSHIP:
        single_relationship_target_name = standard_property_proxy.relationship_target_name
        if not standard_property_proxy.relationship_target_names:  # works for None or an empty string
            multiple_relationship_target_names = [single_relationship_target_name]
        else:
            multiple_relationship_target_names = standard_property_proxy.relationship_target_names.split('|')
            if single_relationship_target_name not in multiple_relationship_target_names:
                multiple_relationship_target_names.append(single_relationship_target_name)
        standard_property_proxy.relationship_target_names = "|".join(multiple_relationship_target_names)
        standard_property_proxy.reset()
        standard_property_proxy.save()


# TODO: deal w/ customizations...

# TODO: deal w/ realizations...