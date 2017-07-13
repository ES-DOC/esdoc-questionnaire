####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

import os
from celery import Celery
from django.conf import settings

# use Q project settings for Celery...
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

# setup celery app for project...
app = Celery(settings.PROJECT_LABEL)
app.config_from_object('django.conf:settings', namespace='CELERY')

# autodiscover all "tasks.py" modules w/in INSTALLED_APPS...
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
