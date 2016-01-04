####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from Q.questionnaire.signals.signals_customizations import post_save_modelcustomizationvocabulary_handler, post_delete_modelcustomizationvocabulary_handler
from Q.questionnaire.signals.signals_ontologies import registered_ontology_handler
from Q.questionnaire.signals.signals_categorizations import registered_categorization_handler
from Q.questionnaire.signals.signals_projects import post_save_project_handler, post_delete_project_handler, post_save_projectvocabulary_handler, post_delete_projectvocabulary_handler
from Q.questionnaire.signals.signals_sites import post_save_site_handler
from Q.questionnaire.signals.signals_users import post_save_user_handler, post_delete_profile_handler