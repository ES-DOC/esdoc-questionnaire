__author__ = 'allyn.treshansky'


from Q.questionnaire.views.views_index import q_index
from Q.questionnaire.views.views_errors import q_404, q_500  # note: "q_error" is only used internally; no need to import it here
from Q.questionnaire.views.views_project import q_project
from Q.questionnaire.views.views_customizations import q_customize_new, q_customize_existing
from Q.questionnaire.views.views_realizations import q_edit_new, q_edit_existing, q_view_new, q_view_existing
from Q.questionnaire.views.views_users import q_user, q_login, q_logout, q_password, q_register

