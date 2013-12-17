from django.contrib import admin

from django_cim_forms.admin import PropertyAdmin

from models import *

admin.site.register(DycoreScientificProperties_cv)
admin.site.register(DycoreScientificProperty,PropertyAdmin) # the PropertyAdmin provides a hook for the delete_danglers action
admin.site.register(DycoreModel)
