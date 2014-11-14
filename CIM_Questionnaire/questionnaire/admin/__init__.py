__author__="allyn.treshansky"
__date__ ="$Jan 23, 2014 10:13:32 AM$"

from django.contrib import admin
from django.forms   import *

from admin_authentication  import *
from admin_sites           import *
from admin_projects        import *
from admin_versions        import *
from admin_categorizations import *
from admin_vocabularies    import *
from admin_serialization   import *

from CIM_Questionnaire.questionnaire.models import MetadataModelProxy, MetadataComponentProxy, MetadataStandardPropertyProxy, MetadataScientificPropertyProxy, MetadataStandardCategoryProxy, MetadataScientificCategoryProxy
from CIM_Questionnaire.questionnaire.models import MetadataModelCustomizer, MetadataStandardCategoryCustomizer, MetadataStandardPropertyCustomizer, MetadataScientificPropertyCustomizer, MetadataScientificCategoryCustomizer
from CIM_Questionnaire.questionnaire.models import MetadataModel, MetadataStandardProperty, MetadataScientificProperty

# TODO: DISABLE ADMIN ACCESS TO THESE CLASSES ONCE PROJECT IS OUT OF BETA
admin.site.register(MetadataModelProxy)
admin.site.register(MetadataComponentProxy)
admin.site.register(MetadataStandardPropertyProxy)
admin.site.register(MetadataScientificPropertyProxy)
admin.site.register(MetadataStandardCategoryProxy)
admin.site.register(MetadataScientificCategoryProxy)
admin.site.register(MetadataModelCustomizer)
admin.site.register(MetadataStandardCategoryCustomizer)
admin.site.register(MetadataStandardPropertyCustomizer)
admin.site.register(MetadataScientificPropertyCustomizer)
admin.site.register(MetadataScientificCategoryCustomizer)
admin.site.register(MetadataModel)
admin.site.register(MetadataStandardProperty)
admin.site.register(MetadataScientificProperty)
