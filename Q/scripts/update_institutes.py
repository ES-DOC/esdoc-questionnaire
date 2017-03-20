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
stand-alone script to download and update institute fixtures from https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_institution_id.json
"""

import django
import sys
import os

__author__ = "allyn.treshansky"

rel = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

# a bit of hackery to get this to run outside of the manage.py script
sys.path.append(rel(".."))  # note that "/scripts" is 1 directory below the project settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()

# now I can do Django & Questionnaire stuff...

import urllib2
import json

from django.contrib.contenttypes.models import ContentType
from Q.questionnaire.models.models_institutes import QInstitute

fixture = []
qinstitute_content_type = ContentType.objects.get_for_model(QInstitute)
qinstutute_fixture_type = "{0}.{1}".format(qinstitute_content_type.app_label, qinstitute_content_type.model)

URL = "https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_institution_id.json"
response = urllib2.urlopen(URL)
content = json.loads(response.read())

institutes = content["institution_id"]
sorted_institutes = institutes.items()
sorted_institutes.sort(key=lambda institute: institute[1])

for index, (name, description) in enumerate(sorted_institutes, start=1):
    fixture.append({
        "fields": {
            "is_active": True,
            "name": name,
            "description": description
        },
        "model": qinstutute_fixture_type,
        "pk": index
    })

print(json.dumps(fixture, indent=4))
