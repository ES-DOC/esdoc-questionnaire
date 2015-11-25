####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"

"""
.. module:: __init__

init module for "mindmaps" application.
deals w/ version info and other stuff.
"""

###########################
# what is the app called? #
###########################

APP_LABEL = "mindmaps"

####################################
# what version is the app/project? #
####################################

__version_info__ = {
    'major': 1,
    'minor': 0,
    'patch': 0,
}


def get_version():
    version = ".".join(str(value) for value in __version_info__.values())
    return version


__version__ = get_version()
