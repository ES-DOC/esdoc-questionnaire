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

from functools import wraps

def disable_for_fixtures(signal_handler):
    """
    Decorator that turns off signal handlers when loading fixture data.
    This is particularly useful for models w/ 1to1 relationship fields,
    b/c those automatically created related models will have some pk that I can't know in advance in the fixture -
    this decorator lets me load all models via the fixture w/out any automatic signal code getting in the way
    [this excellent idea came from: http://stackoverflow.com/questions/15624817/have-loaddata-ignore-or-disable-post-save-signals]
    """

    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        if kwargs.get('raw'):
            return
        signal_handler(*args, **kwargs)

    return wrapper
