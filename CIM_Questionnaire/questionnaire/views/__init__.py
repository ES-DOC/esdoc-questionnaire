__author__="allyn.treshansky"
__date__ ="$Sep 30, 2013 3:11:26 PM$"

from django.template    import *
from django.shortcuts   import *
from django.http        import *

from django.core.urlresolvers   import reverse
from django.contrib             import messages
from django.contrib.messages    import get_messages

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.sites.models    import get_current_site

from profiling          import encode_profile as profile
from profiling          import profile_memory as profile_memory

from django.views.decorators.debug import sensitive_post_parameters

from views_error        import questionnaire_error as error
from views_help         import questionnaire_help  as help
from views_ajax         import ajax_customize_category, ajax_customize_subform
from views_index        import questionnaire_index as index, questionnaire_project_index as project_index
from views_authenticate import questionnaire_login as login, questionnaire_logout as logout, questionnaire_user as user, questionnaire_register as register
from views_openid       import login as oid_login, process as oid_process
from views_customize    import questionnaire_customize_new as customize_new, questionnaire_customize_existing as customize_existing, questionnaire_customize_help as customize_help

from views_test         import test