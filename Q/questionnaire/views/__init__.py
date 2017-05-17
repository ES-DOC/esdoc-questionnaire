####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from Q.questionnaire.views.views_customizations import q_customize_new, q_customize_existing
from Q.questionnaire.views.views_errors import q_error, q_500, q_404
from Q.questionnaire.views.views_index import q_index, q_test
from Q.questionnaire.views.views_projects import q_project, q_project_customize, q_project_manage
from Q.questionnaire.views.views_realizations import q_edit_new, q_edit_existing, q_view_new, q_view_existing, q_get_existing
from Q.questionnaire.views.views_users import q_profile
