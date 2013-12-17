__author__="allyn.treshansky"
__date__ ="$Sep 30, 2013 3:11:26 PM$"

from django.template    import *
from django.shortcuts   import *
from django.http        import *

from profiling          import encode_profile as profile
from profiling          import profile_memory as profile_memory

from django.contrib.auth.decorators import login_required, permission_required

from views_error        import error
from views_help         import help
from views_index        import index
from views_login        import login
from views_openid       import login as oid_login, process as oid_process

from views_test         import test