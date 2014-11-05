
####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Jan 23, 2014 10:18:29 AM"

"""
.. module:: admin_authentication

Summary of module goes here

"""


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from CIM_Questionnaire.questionnaire.models.metadata_authentication import MetadataUser, MetadataOpenIDProvider

class MetadataUserInline(admin.StackedInline):
    model = MetadataUser
    can_delete = False

class MetadataAdmin(UserAdmin):
    inlines = (MetadataUserInline, )

    # this took a while to figure out...
    # I want to update the group membership of a user based on which projects they belong to, but...
    # 1) the save method on metadata_user gets called before the save_m2m method of the inlineform here (so the contents of 'projects' would be invalid)
    # 2) there is a known Django bug in the m2m_changed signal
    # so I do it here after save_m2m has been called
    # (see models/metadata_authentication.py for more info)
    def save_formset(self,request,form,formset,change):
        try:
            # since this is based off a one-to-one field, there will only ever be a single form in the formset
            metadata_user = formset.save(commit=False)[0]
        except IndexError:
            # ...except for the case where the admin has not yet been assocated w/ a metadata_user
            return
        metadata_user.save()
        old_projects = set(metadata_user.projects.all())
        formset.save_m2m()
        new_projects = set(metadata_user.projects.all())

        for project in old_projects.difference(new_projects):
            metadata_user.leave_project(project)
        for project in new_projects.difference(old_projects):
            metadata_user.join_project(project)

admin.site.unregister(User)
admin.site.register(User, MetadataAdmin)

class MetadataOpenIDProviderAdmin(admin.ModelAdmin):
    fields = ('name','title','url','icon','image_tag','active')
    readonly_fields = ('image_tag',)


admin.site.register(MetadataOpenIDProvider, MetadataOpenIDProviderAdmin)
