####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from Q.questionnaire.models.models_users import QUserProfile

__author__ = 'allyn.treshansky'


class QUserInline(admin.StackedInline):
    model = QUserProfile
    can_delete = False
    verbose_name = "Questionnaire Profile"


class QUserAdmin(UserAdmin):
    inlines = (QUserInline, )

    # this took a while to figure out...
    # I want to update the group membership of a user based on which projects they belong to, but...
    # 1) the save method on QUserProfile gets called before the save_m2m method of the inlineform here
    #    (so the contents of 'projects' would be invalid)
    # 2) there is a known Django bug in the m2m_changed signal
    # ...so I do it here after save_m2m has been called
    def save_formset(self, request, form, formset, change):
        try:
            # since this is based on a 1-to-1 field, there will only ever be a single form in the formset...
            user_profile = formset.save(commit=False)[0]
        except IndexError:
            # ...except for the case where the site admin user may not yet have been associated w/ a QUserProfile
            return

        user_profile.save()
        old_projects = set(user_profile.projects.all())
        formset.save_m2m()
        new_projects = set(user_profile.projects.all())

        for project in old_projects.difference(new_projects):
            user_profile.leave_project(project)
        for project in new_projects.difference(old_projects):
            user_profile.join_project(project)

# when db is 1st setup, built-in User may be registered before Q classes
try:
    admin.site.register(User, QUserAdmin)
except AlreadyRegistered:
    admin.site.unregister(User)
    admin.site.register(User, QUserAdmin)
