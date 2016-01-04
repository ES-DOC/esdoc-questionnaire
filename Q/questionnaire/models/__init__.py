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

# add models for migration here

from Q.questionnaire.models.models_test import QTestModel


from Q.questionnaire.models.models_categorizations import QCategorization
from Q.questionnaire.models.models_ontologies import QOntology
from Q.questionnaire.models.models_customizations import QModelCustomization, QStandardPropertyCustomization, QScientificPropertyCustomization, QModelCustomizationVocabulary
from Q.questionnaire.models.models_realizations import QModel, QStandardProperty, QScientificProperty
from Q.questionnaire.models.models_projects import QProject, QProjectVocabulary
from Q.questionnaire.models.models_proxies import QModelProxy, QStandardPropertyProxy, QStandardCategoryProxy, QScientificCategoryProxy, QComponentProxy
from Q.questionnaire.models.models_publications import QPublication
from Q.questionnaire.models.models_sites import QSite
from Q.questionnaire.models.models_synchronization import QSynchronization
from Q.questionnaire.models.models_users import QUserProfile
from Q.questionnaire.models.models_vocabularies import QVocabulary

from Q.questionnaire.models.models_realizations_bak import MetadataModel, MetadataStandardProperty, MetadataScientificProperty
