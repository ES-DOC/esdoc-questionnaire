####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
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
# THESE ARE NOW DEFINED EXTERNALLY
# QUESTIONNAIRE_EMAIL =
# QUESTIONNAIRE_CODE_URL =
# QUESTIONNAIRE_HELP_URL =

# CIM-specific constants...

# valid reasons to leave a property value blank reasons (taken from seeGrid)

NIL_PREFIX = "nil"
NIL_REASONS = [

    "Inapplicable",  # there is no value
    "Missing",  # the correct value is not readily available to the sender of this data. Furthermore, a correct value may not exist
    "Template",  # the value will be available later
    "Unknown",  # the correct value is not known to, and not computable by, the sender of this data. However, a correct value probably exists
    "Withheld",  # the value is not divulged
]

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
SUPPORTED_DOCUMENTS = {
    "CIM1": [
        "modelcomponent",
        "statisticalmodelcomponent",
        "platform",
    ],
    "CIM2": [
        # "Conformance",
        # "Temporal_Constraint",
        "Simulation",
        "Ensemble",
        # "Party",
        # "Domain_Properties",
        # "Scientific_Domain",
        # "Output_Temporal_Requirement",
        # "Performance",
        # "Project",
        # "Multi_Time_Ensemble",
        # "Ensemble_Requirement",
        # "Uber_Ensemble",
        # "Multi_Ensemble",
        # "Machine",
        "Model",
        # "Numerical_Experiment",
        # "Numerical_Requirement",
        "Downscaling",
        # "Simulation_Plan",
        # "Dataset",
        # "Forcing_Constraint",
    ],
}



