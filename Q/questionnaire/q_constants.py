####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

"""
.. module:: q_constants

defines a bunch of constants to be used throughout the app
"""

# naughty words...
# (these are stored in an external file and loaded at startup in "apps.py")
PROFANITIES_LIST = []

# pre-defined string lengths...
LIL_STRING = 128
SMALL_STRING = 256
BIG_STRING = 512
HUGE_STRING = 1024

# minimum password length...
PASSWORD_LENGTH = 6

# cannot have projects w/ these names...
# (else the URLs won't make sense)
RESERVED_WORDS = [
    "admin", "static", "site_media",
    "user", "login", "logout", "register",
    "questionnaire", "mindmaps", "metadata",
    "customize", "edit", "view", "help",
    "api", "services",
    "test", "bak",
]

# just use the default cache; don't get fancy...
CACHE_ALIAS = "default"

# where to get help...
QUESTIONNAIRE_EMAIL = "es-doc-support@list.woc.noaa.gov"
QUESTIONNAIRE_CODE_URL = "https://github.com/ES-DOC/esdoc-questionnaire"
QUESTIONNAIRE_HELP_URL = "https://earthsystemcog.org/projects/es-doc-models/doc/questionnaire/works"

# CIM-specific constants...

#: the set of document types recognized by the questionnaire
CIM_DOCUMENT_TYPES = [
    "modelcomponent",
    "statisticalmodelcomponent",
    "experiment",
    "platform",
]

#: the set of valid namespaces that can be used by CIM 1.x
CIM_NAMESPACES = [
    "xsi",
    "gml",
    "xlink",
    "gco",
    "gmd",
]

#: the set of UML stereotypes that can be used by models in CIM 1.x
CIM_MODEL_STEREOTYPES = [
    "document",
]

#: the set of UML stereotypes that can be used by properties in CIM 1.x
CIM_PROPERTY_STEREOTYPES = [
    "attribute",    # should be serialized as an XML attribute rather than element
    "document",     # should be included w/ the "documentProperties" of a model, rather than the "standardProperties"
]

#: the set of document types that can be fully processed (ie: end-to-end) by the questionnaire
SUPPORTED_DOCUMENTS = [
    "modelcomponent",
    "statisticalmodelcomponent",
    "platform",
]