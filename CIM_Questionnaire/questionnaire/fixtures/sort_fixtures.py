####################
#   CIM_Questionnaire
#   Copyright (c) 2014 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Jan 23, 2014 10:19:02 AM"

"""
.. module:: sort_fixtures

stand-alone script to sort fixtures, so that models are listed in the correct order
this is required b/c of a known bug in Django [see https://code.djangoproject.com/ticket/6726]
"""

import os
import sys

rel = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

# a bit of hackery to get this to run outside of the manage.py script
# (this lets me keep it local to fixtures)
sys.path.append(rel("../.."))  # note the fixtures directory is 2 sub-directories below the project settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
# now I can do Django & Questionnaire stuff...

import getopt
import json
from django.db.models import get_app, get_models
from CIM_Questionnaire.questionnaire import APP_LABEL
from CIM_Questionnaire.questionnaire.models import *


def usage():
    """
    print usage instructions
    :return: usage string
    """
    print u"usage: %s -f <fixture file> [> <new fixture file]" % sys.argv[0]

##############################
# parse command-line options #
##############################

fixture_file = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'f:')
except getopt.GetoptError as err:
    print err
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

############################################
# get the active models in the application #
############################################

app = get_app(APP_LABEL)
models = get_models(app)

# order models so that users, sites, versions, categorizations, vocabularies, projects, & projectvocabularies are 1st
# (the order of the remaining models don't matter)
order = [models.index(model) for model in
         [
         MetadataUser,
         MetadataSite,
         MetadataVersion,
         MetadataCategorization,
         MetadataVocabulary,
         MetadataProject,
         MetadataProjectVocabulary,
         MetadataModelProxy,
         MetadataStandardCategoryProxy,
         MetadataScientificCategoryProxy,
         MetadataStandardPropertyProxy,
         MetadataScientificPropertyProxy,
         MetadataComponentProxy,
         MetadataModelCustomizer,
         MetadataStandardCategoryCustomizer,
         MetadataScientificCategoryCustomizer,
         MetadataStandardPropertyCustomizer,
         MetadataScientificPropertyCustomizer,
         MetadataModelCustomizerVocabulary,
         MetadataModel,
         MetadataStandardProperty,
         MetadataScientificProperty,
         MetadataModelSerialization,
         MetadataOpenIDProvider,  # this model is not actually being used
         ]]

ordered_model_keys = [models[i]._meta.db_table.replace('_', '.') for i in order]

#################
# reorder stuff #
#################

new_fixture = []
for model_key in ordered_model_keys:
    new_fixture += [model for model in fixture if model["model"] == model_key]

# make sure that no models were missed
assert(len(new_fixture) == len(fixture))

################
# output stuff #
################

print json.dumps(new_fixture, indent=4)




