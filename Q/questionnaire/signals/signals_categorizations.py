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

from Q.questionnaire.models.models_categorizations import registered_categorization_signal

def registered_categorization_handler(sender, **kwargs):
    """
    fn that gets called when a categorization is registered;
    it will route the signal to the appropriate customizations and/or realizations
    :param sender:
    :param kwargs:
    :return:
    """
    categorization = sender
    model_customization = kwargs.pop("customization", None)
    model_realization = kwargs.pop("realization", None)

    if model_customization:
        model_customization.updated_categorization()

    if model_realization:
        model_realization.updated_categorization()

# connect the signal to the handler (note how dispatch_uuid prevents this code from being run multiple times)...
registered_categorization_signal.connect(registered_categorization_handler, dispatch_uid="registered_categorization_handler")


