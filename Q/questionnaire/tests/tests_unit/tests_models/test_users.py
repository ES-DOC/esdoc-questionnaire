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

from Q.questionnaire.tests.test_base import TestQBase
from Q.questionnaire.models.models_projects import QProject
from Q.questionnaire.models.models_users import *

class TestQUser(TestQBase):

    def setUp(self):

        super(TestQUser, self).setUp()
        self.test_project_name = "test_project"
        self.test_project = QProject(
            name=self.test_project_name,
            title=self.test_project_name,
        )
        self.test_project.save()

    def test_pending(self):
        """
        this implicitly tests is_pending_of, add_pending_permissions, remove_pending_permissions, and add_group
        :return:
        """
        user_profile = self.test_user.profile
        self.assertFalse(user_profile.is_pending_of(self.test_project))
        user_profile.add_pending_permissions(self.test_project)
        self.assertTrue(user_profile.is_pending_of(self.test_project))
        user_profile.remove_pending_permissions(self.test_project)
        self.assertFalse(user_profile.is_pending_of(self.test_project))

    def test_member(self):
        """
        this implicitly tests is_member_of, add_member_permissions, remove_member_permissions, and add_group
        :return:
        """
        user_profile = self.test_user.profile
        self.assertFalse(user_profile.is_member_of(self.test_project))
        user_profile.add_member_permissions(self.test_project)
        self.assertTrue(user_profile.is_member_of(self.test_project))
        user_profile.remove_member_permissions(self.test_project)
        self.assertFalse(user_profile.is_member_of(self.test_project))

    def test_user(self):
        """
        this implicitly tests is_user_of, add_user_permissions, remove_user_permissions, and add_group
        :return:
        """
        user_profile = self.test_user.profile
        self.assertFalse(user_profile.is_user_of(self.test_project))
        user_profile.add_user_permissions(self.test_project)
        self.assertTrue(user_profile.is_user_of(self.test_project))
        user_profile.remove_user_permissions(self.test_project)
        self.assertFalse(user_profile.is_user_of(self.test_project))

    def test_admin(self):
        """
        this implicitly tests is_admin_of, add_admin_permissions, remove_admin_permissions, and add_group
        :return:
        """
        user_profile = self.test_user.profile
        self.assertFalse(user_profile.is_admin_of(self.test_project))
        user_profile.add_admin_permissions(self.test_project)
        self.assertTrue(user_profile.is_admin_of(self.test_project))
        user_profile.remove_admin_permissions(self.test_project)
        self.assertFalse(user_profile.is_admin_of(self.test_project))

    def test_join_project(self):
        user_profile = self.test_user.profile

        self.assertFalse(user_profile.is_pending_of(self.test_project))
        self.assertFalse(user_profile.is_member_of(self.test_project))
        self.assertFalse(user_profile.is_user_of(self.test_project))
        self.assertFalse(user_profile.is_admin_of(self.test_project))

        user_profile.join_project(self.test_project)

        self.assertFalse(user_profile.is_pending_of(self.test_project))
        self.assertTrue(user_profile.is_member_of(self.test_project))
        self.assertTrue(user_profile.is_user_of(self.test_project))
        self.assertFalse(user_profile.is_admin_of(self.test_project))

    def test_leave_project(self):
        user_profile = self.test_user.profile

        self.assertFalse(user_profile.is_pending_of(self.test_project))
        self.assertFalse(user_profile.is_member_of(self.test_project))
        self.assertFalse(user_profile.is_user_of(self.test_project))
        self.assertFalse(user_profile.is_admin_of(self.test_project))

        user_profile.join_project(self.test_project)
        user_profile.leave_project(self.test_project)

        self.assertFalse(user_profile.is_pending_of(self.test_project))
        self.assertFalse(user_profile.is_member_of(self.test_project))
        self.assertFalse(user_profile.is_user_of(self.test_project))
        self.assertFalse(user_profile.is_admin_of(self.test_project))

    def test_project_join_request_permission_set(self):
        user_profile = self.test_user.profile

        self.assertFalse(user_profile.is_pending_of(self.test_project))
        self.assertFalse(user_profile.is_member_of(self.test_project))
        self.assertFalse(user_profile.is_user_of(self.test_project))
        self.assertFalse(user_profile.is_admin_of(self.test_project))

        project_join_request(self.test_project, self.test_user)

        self.assertTrue(user_profile.is_pending_of(self.test_project))

    def test_project_join_request_email_sent(self):

        from django.core.mail import outbox

        pre_request_message_len = len(outbox)

        project_join_request(self.test_project, self.test_user)

        post_request_message_len = len(outbox)

        self.assertEqual(pre_request_message_len, post_request_message_len - 1)

        message = outbox.pop()

        self.assertEqual(message.subject, "ES-DOC Questionnaire project join request")
        self.assertIn(self.test_user.username, message.body)
        self.assertIn(self.test_project.name, message.body)

