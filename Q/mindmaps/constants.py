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

# list of mindmaps to present to users
# prevents them having to know the precise URLs, just to make their life a little bit easier
# assumes that the URL domains are registered as a known mindmap_source

MINDMAP_PROJECTS = {
    "cmip6": {
        "realms": [
            {
                "name": "ocean",
                "mindmap": "https://raw.githubusercontent.com/ES-DOC/cmip6-specializations-ocean/master/_ocean.mm"
            },
            {
                "name": "seaice",
                "mindmap": "https://raw.githubusercontent.com/ES-DOC/cmip6-specializations-seaice/master/_seaice.mm"
            }
        ]
    }
}