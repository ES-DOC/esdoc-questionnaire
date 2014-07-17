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

from django.contrib.auth.models import User

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase

from CIM_Questionnaire.questionnaire.models.metadata_authentication import MetadataUser, get_metadata_user


class TestMetadataUser(TestQuestionnaireBase):


    def setUp(self):

        super(TestMetadataUser,self).setUp()

        new_user = User.objects.create_user("new", "a@b.com", "new")
        new_metadata_user = get_metadata_user(new_user)
        self.assertIsNotNone(new_metadata_user)
        self.metadata_user = new_metadata_user


    # MetadataUser creation testing is happening implicitly in setUp above
    #def test_create_user(self):
    #    pass


    def test_delete_user(self):

        metadata_user_pk = self.metadata_user.pk
        self.metadata_user.user.delete()

        self.assertRaises(MetadataUser.DoesNotExist, MetadataUser.objects.get, pk=metadata_user_pk )

    def test_join_project(self):
        test_user = self.metadata_user
        test_project = self.project

        self.assertEqual(len(test_user.projects.all()),0)
        self.assertEqual(test_user.is_member_of(test_project),False)
        self.assertEqual(test_user.is_user_of(test_project),False)
        self.assertEqual(test_user.is_admin_of(test_project),False)

        test_user.join_project(test_project)

        self.assertEqual(len(test_user.projects.all()),1)
        self.assertEqual(test_user.is_member_of(test_project),True)
        self.assertEqual(test_user.is_user_of(test_project),False)
        self.assertEqual(test_user.is_admin_of(test_project),False)


    def test_leave_project(self):

        test_user = self.metadata_user
        test_project = self.project

        test_user.join_project(test_project)
        test_user.leave_project(test_project)

        self.assertEqual(len(test_user.projects.all()),0)
        self.assertEqual(test_user.is_member_of(test_project),False)
        self.assertEqual(test_user.is_user_of(test_project),False)
        self.assertEqual(test_user.is_admin_of(test_project),False)

    def test_add_group(self):

        test_user = self.metadata_user
        test_project = self.project

        test_user.join_project(test_project)
        for group in test_project.get_all_groups():
            test_user.add_group(group)

        self.assertEqual(test_user.is_member_of(test_project),True)
        self.assertEqual(test_user.is_user_of(test_project),True)
        self.assertEqual(test_user.is_admin_of(test_project),True)

    def test_remove_group(self):

        test_user = self.metadata_user
        test_project = self.project

        test_user.join_project(test_project)
        for group in test_project.get_all_groups():
            test_user.remove_group(group)

        # somewhat counter-intuitively you cannot leave a project by removing that project's "default" group
        # everyone belongs to the "default" group
        self.assertEqual(test_user.is_member_of(test_project),True)
        self.assertEqual(test_user.is_user_of(test_project),False)
        self.assertEqual(test_user.is_admin_of(test_project),False)

    def test_add_user_privileges(self):

        test_user = self.metadata_user
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

        test_user = self.metadata_user
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

        test_user = self.metadata_user
        test_project = self.project

        test_user.join_project(test_project)
        test_user.add_user_privileges(test_project)
        test_user.remove_user_privileges(test_project)

        self.assertEqual(test_user.is_member_of(test_project),True)
        self.assertEqual(test_user.is_user_of(test_project),False)
        self.assertEqual(test_user.is_admin_of(test_project),False)


    def test_remove_admin_privileges(self):

        test_user = self.metadata_user
        test_project = self.project

        test_user.join_project(test_project)
        test_user.add_admin_privileges(test_project)
        test_user.remove_admin_privileges(test_project)

        self.assertEqual(test_user.is_member_of(test_project),True)
        self.assertEqual(test_user.is_user_of(test_project),False)
        self.assertEqual(test_user.is_admin_of(test_project),False)

    # TODO: test that as User group membership changes in the admin those changes get propagated to the corresponding MetadataUser
    # (see save_formset() fn in "admin_authentication.py")
