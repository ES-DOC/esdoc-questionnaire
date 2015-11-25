####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"

"""
stand-alone script to sort fixtures, so that models are listed in the correct order
this is required b/c of a known bug in Django [see https://code.djangoproject.com/ticket/6726]
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

import getopt
import json

from django.db.models import get_app, get_models

from Q.questionnaire import APP_LABEL
from Q.questionnaire.models import *


def usage():
    """
    print usage instructions
    :return: usage string
    """
    print(u"usage: %s -f <fixture file> [> <new fixture file]" % sys.argv[0])

##############################
# parse command-line options #
##############################

fixture_file = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'f:')
except getopt.GetoptError as err:
    print(err)
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-h':
        usage()
        sys.exit(2)
    elif o == '-f':
        fixture_file = rel(a)
    else:
        usage()
        sys.exit(2)

if not fixture_file:
    usage()
    sys.exit(2)

with open(fixture_file, "r") as f:
  fixture = json.load(f)
f.closed

###################
# some helper fns #
###################

def get_model_key(model):
    """
    given a model, returns its full Python path
    (used to identify models in the fixture)
    """
    return model._meta.db_table.replace('_', '.')

############################################
# get the active models in the application #
############################################

app = get_app(APP_LABEL)
models = get_models(app)

# order questionnaire models so that users, sites, ontologies, categorizations, vocabularies, projects, projectvocabularies & synchronizations, are 1st
# the order of the remaining models doesn't matter
models_to_order = [
    QUserProfile,
    QSite,
    QOntology,
    QCategorization,
    QVocabulary,
    QProject,
    QProjectVocabulary,
    QSynchronization,
]

# explicitly get any Users & Sites 1st...
# then get ordered models from the questionnaire...
# then get remaining models from the questionnaire...
ordered_model_keys = ["auth.user", "sites.site", ] + \
    [get_model_key(m) for m in models_to_order] + \
    [get_model_key(m) for m in models if m not in models_to_order]

#################
# reorder stuff #
#################

ordered_fixture = []
for model_key in ordered_model_keys:
    ordered_fixture += [m for m in fixture if m.get("model") == model_key]

# make sure that no models were missed
assert(len(ordered_fixture) == len(fixture))

################
# output stuff #
################

print(json.dumps(ordered_fixture, indent=4))





