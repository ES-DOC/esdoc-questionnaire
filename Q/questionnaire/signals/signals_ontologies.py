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

from Q.questionnaire.models.models_ontologies import registered_ontology_signal

def registered_ontology_handler(sender, **kwargs):
    """
    fn that gets called when an ontology is registered;
    it will route the signal to the appropriate customizations and/or realizations
    :param sender:
    :param kwargs:
    :return:
    """
    ontology = sender
    model_customization = kwargs.pop("customization", None)
    model_realization = kwargs.pop("realization", None)

    if model_customization:
        model_customization.updated_ontology()

    if model_realization:
        model_realization.updated_ontology()

# connect the signal to the handler (note how dispatch_uuid prevents this code from being run multiple times)...
registered_ontology_signal.connect(registered_ontology_handler, dispatch_uid="registered_ontology_handler")


