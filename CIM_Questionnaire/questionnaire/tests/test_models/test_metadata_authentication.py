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


from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.models.metadata_authentication import MetadataUser
from CIM_Questionnaire.questionnaire.models.metadata_project import MetadataProject
from django.contrib.auth.models import User

class TestMetadataUser(TestQuestionnaireBase):

    def setUp(self):

        super(TestMetadataUser,self).setUp()

        # MetadataUser is created automatically after a regular user is created in Django
        # (except for the Django Administrator User)
        test_user = User.objects.create_user("test","test@test.com","test")
        metadata_user = test_user.metadata_user

        self.assertEqual(test_user.is_superuser,False)
        self.assertIsNotNone(metadata_user,msg="MetadataUser not created after User.save() method")

        self.user = metadata_user


    def test_join_project(self):
        test_user = self.user
        test_project = self.project

        self.assertEqual(len(test_user.projects.all()),0)
        self.assertEqual(test_user.is_member_of(test_project),False)
        self.assertEqual(test_user.is_user_of(test_project),False)
        self.assertEqual(test_user.is_admin_of(test_project),False)

        test_user.join_project(test_project)

        self.assertEqual(len(self.user.projects.all()),1)
        self.assertEqual(test_user.is_member_of(test_project),True)
        self.assertEqual(test_user.is_user_of(test_project),False)
        self.assertEqual(test_user.is_admin_of(test_project),False)


    def test_leave_project(self):

        test_user = self.user
        test_project = self.project

        test_user.join_project(test_project)
        test_user.leave_project(test_project)

        self.assertEqual(len(test_user.projects.all()),0)
        self.assertEqual(test_user.is_member_of(test_project),False)
        self.assertEqual(test_user.is_user_of(test_project),False)
        self.assertEqual(test_user.is_admin_of(test_project),False)

    def test_add_group(self):

        test_user = self.user
        test_project = self.project

        test_user.join_project(test_project)
        for group in test_project.get_all_groups():
            test_user.add_group(group)

        self.assertEqual(test_user.is_member_of(test_project),True)
        self.assertEqual(test_user.is_user_of(test_project),True)
        self.assertEqual(test_user.is_admin_of(test_project),True)

    def test_remove_group(self):

        test_user = self.user
        test_project = self.project

        test_user.join_project(test_project)
        for group in test_project.get_all_groups():
            test_user.remove_group(group)

        # somewhat counter-intuitively you cannot leave a project by removing that project's "default" group
        self.assertEqual(test_user.is_member_of(test_project),True)
        self.assertEqual(test_user.is_user_of(test_project),False)
        self.assertEqual(test_user.is_admin_of(test_project),False)

    def test_add_user_privileges(self):

        test_user = self.user
        test_project = self.project

        test_user.join_project(test_project)

        self.assertEqual(test_user.is_member_of(test_project),True)
        self.assertEqual(test_user.is_user_of(test_project),False)
        self.assertEqual(test_user.is_admin_of(test_project),False)

        test_user.add_user_privileges(test_project)

        self.assertEqual(test_user.is_member_of(test_project),True)
        self.assertEqual(test_user.is_user_of(test_project),True)
        self.assertEqual(test_user.is_admin_of(test_project),False)

    def test_add_admin_privileges(self):

        test_user = self.user
        test_project = self.project

        test_user.join_project(test_project)

        self.assertEqual(test_user.is_member_of(test_project),True)
        self.assertEqual(test_user.is_user_of(test_project),False)
        self.assertEqual(test_user.is_admin_of(test_project),False)

        test_user.add_admin_privileges(test_project)

        self.assertEqual(test_user.is_member_of(test_project),True)
        self.assertEqual(test_user.is_user_of(test_project),False)
        self.assertEqual(test_user.is_admin_of(test_project),True)

    def test_remove_user_privileges(self):

        test_user = self.user
        test_project = self.project

        test_user.join_project(test_project)
        test_user.add_user_privileges(test_project)
        test_user.remove_user_privileges(test_project)

        self.assertEqual(test_user.is_member_of(test_project),True)
        self.assertEqual(test_user.is_user_of(test_project),False)
        self.assertEqual(test_user.is_admin_of(test_project),False)


    def test_remove_admin_privileges(self):

        test_user = self.user
        test_project = self.project

        test_user.join_project(test_project)
        test_user.add_admin_privileges(test_project)
        test_user.remove_admin_privileges(test_project)

        self.assertEqual(test_user.is_member_of(test_project),True)
        self.assertEqual(test_user.is_user_of(test_project),False)
        self.assertEqual(test_user.is_admin_of(test_project),False)

    def test_user_post_save(self):
        """Tests the User post-save signal triggers the appropriate adding/removing of groups (and hence privileges)"""

        test_user = self.user
        test_project = self.project

        test_django_user = self.user.user

        test_user.join_project(test_project)

        for group in test_project.get_all_groups():
            test_django_user.groups.add(group)

        self.assertEqual(test_user.is_member_of(test_project),True)
        self.assertEqual(test_user.is_user_of(test_project),True)
        self.assertEqual(test_user.is_admin_of(test_project),True)

        for group in test_project.get_all_groups():
            test_django_user.groups.remove(group)

        self.assertEqual(test_user.is_member_of(test_project),True)
        self.assertEqual(test_user.is_user_of(test_project),False)
        self.assertEqual(test_user.is_admin_of(test_project),False)
