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

from Q.questionnaire.views.views_help import q_help
from Q.questionnaire.views.views_errors import q_404, q_500  # note: "q_error" is only used internally
from Q.questionnaire.views.views_index import q_index
from Q.questionnaire.views.views_project import q_project
from Q.questionnaire.views.views_customizations import q_customize_new, q_customize_existing
from Q.questionnaire.views.views_realizations_bak import q_edit_new, q_edit_existing, q_view_new, q_view_existing
from Q.questionnaire.views.views_users import q_user, q_login, q_logout, q_register, q_password
from Q.questionnaire.views.views_test import q_test
