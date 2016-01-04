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

from django.contrib.auth.models import Group, Permission

from Q.questionnaire.tests.test_base import TestQBase
from Q.questionnaire.models.models_projects import QProject, GROUP_PERMISSIONS

class TestQProject(TestQBase):

    def setUp(self):

        super(TestQProject, self).setUp()
        self.test_project_name = "test_project"
        self.test_project = QProject(
            name=self.test_project_name,
            title=self.test_project_name,
        )
        self.test_project.save()

    def test_project_groups_created(self):
        """
        test that the correct groups and permissions exist after creating a project
        :return:
        """

        for group_suffix, permission_prefixes in GROUP_PERMISSIONS.iteritems():
            group = self.test_project.get_group(group_suffix)
            self.assertIsNotNone(group.pk)
            for permission_prefix in permission_prefixes:
                permission = self.test_project.get_permission(permission_prefix)
                self.assertIsNotNone(permission.pk)
                self.assertIn(permission, group.permissions.all())

    def test_project_groups_deleted(self):
        """
        test that the correct groups and permissions no longer exist after deleting a project
        :return:
        """

        self.test_project.delete()

        project_groups = Group.objects.filter(name__startswith=self.test_project_name)
        self.assertEqual(0, len(project_groups))
        project_permissions = Permission.objects.filter(codename__endswith=self.test_project_name)
        self.assertEqual(0, len(project_permissions))

    def test_project_queryset(self):
        """
        tests that my custom queryset manager works as expected
        :return:
        """

        self.test_project.is_active = True
        self.test_project.save()
        self.assertIn(self.test_project, QProject.objects.active_projects())

        self.test_project.is_active = False
        self.test_project.save()
        self.assertNotIn(self.test_project, QProject.objects.active_projects())

    def test_get_pending_users(self):

        self.assertNotIn(self.test_user, self.test_project.get_pending_users())

        self.test_user.profile.add_pending_permissions(self.test_project)

        self.assertIn(self.test_user, self.test_project.get_pending_users())

    def test_get_member_users(self):

        self.assertNotIn(self.test_user, self.test_project.get_member_users())

        self.test_user.profile.add_member_permissions(self.test_project)

        self.assertIn(self.test_user, self.test_project.get_member_users())

    def test_get_user_users(self):

        self.assertNotIn(self.test_user, self.test_project.get_user_users())

        self.test_user.profile.add_user_permissions(self.test_project)

        self.assertIn(self.test_user, self.test_project.get_user_users())

    def test_get_admin_users(self):

        self.assertNotIn(self.test_user, self.test_project.get_admin_users())

        self.test_user.profile.add_admin_permissions(self.test_project)

        self.assertIn(self.test_user, self.test_project.get_admin_users())
