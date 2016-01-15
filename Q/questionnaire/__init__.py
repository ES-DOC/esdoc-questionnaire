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
.. module:: __init__

init module for "questionnaire" application.
deals w/ version info and other stuff.
"""

import logging

###########################
# what is the app called? #
###########################

APP_LABEL = "questionnaire"
default_app_config = 'questionnaire.apps.QConfig'

#########################
# where do messages go? #
#########################

q_logger = logging.getLogger(APP_LABEL)

####################################
# what version is the app/project? #
####################################

__version_info__ = {
    'major': 0.16,
    'minor': 0,
    'patch': 0,
}


def get_version():
    version = ".".join(str(value) for value in __version_info__.values())
    return version


__version__ = get_version()
