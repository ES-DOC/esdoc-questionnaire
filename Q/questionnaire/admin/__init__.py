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

from django.contrib import admin

from Q.questionnaire.models.models_proxies import QModelProxy, QStandardCategoryProxy, QStandardPropertyProxy, QScientificCategoryProxy, QScientificPropertyProxy
from Q.questionnaire.models.models_customizations import QModelCustomization, QModelCustomizationVocabulary, QStandardCategoryCustomization, QStandardPropertyCustomization, QScientificCategoryCustomization, QScientificPropertyCustomization
from Q.questionnaire.models.models_realizations import QModel, QStandardProperty, QScientificProperty
from Q.questionnaire.models.models_synchronization import QSynchronization
from Q.questionnaire.models.models_publications import QPublication

# TODO: W/ THE EXCEPTION OF QPublication, ALL OF THESE CAN BE DELETED ONCE I'M SURE EVERYTHING IS WORKING
# TODO: UNTIL THAT TIME, I MARK THESE MODELS IN THE ADMIN BY PREFACING THEIR "verbose_name_plural" w/ '_'

admin.site.register(QModelProxy)
admin.site.register(QStandardCategoryProxy)
admin.site.register(QStandardPropertyProxy)
admin.site.register(QScientificCategoryProxy)
admin.site.register(QScientificPropertyProxy)

admin.site.register(QModelCustomization)
admin.site.register(QModelCustomizationVocabulary)
admin.site.register(QStandardCategoryCustomization)
admin.site.register(QStandardPropertyCustomization)
admin.site.register(QScientificCategoryCustomization)
admin.site.register(QScientificPropertyCustomization)

admin.site.register(QModel)
admin.site.register(QStandardProperty)
admin.site.register(QScientificProperty)

admin.site.register(QSynchronization)

admin.site.register(QPublication)

# note the relative imports; this is to prevent loading __init__.py twice
from .admin_categorization import *
from .admin_ontologies import *
from .admin_projects import *
from .admin_vocabularies import *
from .admin_site import *
from .admin_user import *
