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

from django.contrib import admin

from Q.questionnaire.models.models_proxies import QModelProxy, QCategoryProxy, QPropertyProxy
from Q.questionnaire.models.models_customizations import QModelCustomization, QCategoryCustomization, QPropertyCustomization
from Q.questionnaire.models.models_realizations import QModel, QProperty
from Q.questionnaire.models.models_institutes import QInstitute

# TODO: W/ THE EXCEPTION OF QInstitute, ALL OF THESE CAN BE DELETED ONCE I'M SURE EVERYTHING IS WORKING
# TODO: UNTIL THAT TIME, I MARK THESE MODELS IN THE ADMIN BY PREFACING THEIR "verbose_name_plural" w/ '_'

admin.site.register(QModelProxy)
admin.site.register(QCategoryProxy)
admin.site.register(QPropertyProxy)
admin.site.register(QModelCustomization)
admin.site.register(QCategoryCustomization)
admin.site.register(QPropertyCustomization)
admin.site.register(QModel)
admin.site.register(QProperty)

admin.site.register(QInstitute)

# note the relative imports; this is to prevent loading __init__.py twice
from .admin_categorizations import *
from .admin_ontologies import *
from .admin_projects import *
from .admin_publications import *
from .admin_site import *
