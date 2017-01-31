####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################


"""
WSGI config for Q project.

It exposes the WSGI callable as a module-level variable named ``application``.

It also has some added code to cope w/ virtual environments

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
import sys
import site
from ConfigParser import SafeConfigParser, NoSectionError

rel = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

CONF_PATH = os.path.join(os.path.expanduser('~'), '.config', 'esdoc-questionnaire.conf')
parser = SafeConfigParser()
parser.read(CONF_PATH)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Q.settings")

# ensure that Apache & Django use the same Q configuration file
assert os.path.basename(CONF_PATH) in open(rel("settings.py")).read()

try:
    # if I am using mod_wsgi w/ a virtualenv
    # then make sure to activate the environment prior to running the application
    VIRTUALENV_PATH = parser.get('virtualenv', 'path')
    site.addsitedir(VIRTUALENV_PATH + '/lib/python2.7/site-packages')
    activate_this = os.path.expanduser(VIRTUALENV_PATH + '/bin/activate_this.py')
    execfile(activate_this, dict(__file__=activate_this))
except NoSectionError:
    pass

# workspace = os.path.dirname(rel('.'))
# sys.path.append(workspace)
sys.path = [
    rel('..'),
    rel('.'),
] + sys.path

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
