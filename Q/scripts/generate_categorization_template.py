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
stand-alone script to generate a categorization template from a QXML file
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

from lxml import etree as et
import argparse
import datetime

from Q.questionnaire.q_utils import QError, xpath_fix
from Q.questionnaire.q_fields import QNillableTypes

# get args...

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', help='QXML file to parse', required=True)
args = vars(parser.parse_args())

qxml_file = args["file"]

if not os.path.isfile(qxml_file):
    msg = "unable to locate '{0}'".format(qxml_file)
    raise QError(msg)

with open(qxml_file, "r") as f:
    qxml_content = et.parse(f)
f.closed

# do stuff...

root_node = et.Element("categorization")
comment_node = et.Comment(
    " created by generate_categorization_template at {0} ".format(
        datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    )
)
categories_node = et.Element("categories")
categories_node.text = str(QNillableTypes.TEMPLATE)
models_node = et.Element("models")
root_node.append(comment_node)
root_node.append(categories_node)
root_node.append(models_node)

for model in xpath_fix(qxml_content, "//classes/class[@stereotype='document']"):
    model_node = et.Element("model")
    model_name_node = et.Element("name")
    model_name_node.text = xpath_fix(model, "name/text()")[0]
    model_fields_node = et.Element("fields")
    for field in xpath_fix(model, "attributes/attribute"):
        field_node = et.Element("field")
        field_name_node = et.Element("name")
        field_name_node.text = xpath_fix(field, "name/text()")[0]
        field_category_node = et.Element("category_key")
        field_category_node.text = str(QNillableTypes.TEMPLATE)
        field_node.append(field_name_node)
        field_node.append(field_category_node)
        model_fields_node.append(field_node)
    model_node.append(model_name_node)
    model_node.append(model_fields_node)
    models_node.append(model_node)

categories_content = et.tostring(root_node, pretty_print=True)
print(categories_content)

