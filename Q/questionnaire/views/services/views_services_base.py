####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################


def validate_request(request, valid_methods=["POST"]):

    validity = True
    msg = None

    if not request.is_ajax():
        msg = "Attempt to call service view outside of AJAX."
        validity = False

    method = request.method
    if method not in valid_methods:
        msg = "Attempt to call service view with '{0}' method".format(method)
        validity = False

    return validity, msg
