__author__="allyn.treshansky"
__date__ ="$Oct 14, 2013 4:56:40 PM$"


from django.db.models       import Q

from mptt.models            import MPTTModel, TreeForeignKey

from questionnaire.utils    import *

from metadata_site             import MetadataSite
from metadata_authentication   import MetadataUser, MetadataOpenIDProvider as MetadataProvider
from metadata_project          import MetadataProject
from metadata_proxy            import MetadataModelProxy, MetadataStandardPropertyProxy, MetadataScientificPropertyProxy, MetadataStandardCategoryProxy, MetadataScientificCategoryProxy, MetadataComponentProxy
from metadata_vocabulary       import MetadataVocabulary
from metadata_customizer       import MetadataModelCustomizer, MetadataStandardPropertyCustomizer, MetadataScientificPropertyCustomizer, MetadataStandardCategoryCustomizer, MetadataScientificCategoryCustomizer
from metadata_model            import MetadataModel, MetadataStandardProperty, MetadataScientificProperty
from metadata_version          import MetadataVersion
from metadata_categorization   import MetadataCategorization


####from django.db.models.signals import post_syncdb
#####import questionnaire.models as questionnaire_models
####
####
####def update_db(app, created_models, verbosity, **kwargs):
####    print "I AM HERE"
####    # Do stuff...
####
####post_syncdb.connect(update_db, sender=[])#questionnaire_models)
####
