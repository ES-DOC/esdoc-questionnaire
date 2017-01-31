####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from Q.questionnaire.q_utils import serialize_model_to_dict, FuzzyInt
from Q.questionnaire.tests.test_base import TestQBase, create_project, incomplete_test
from Q.questionnaire.models.models_projects import *


class TestQProject(TestQBase):

    def setUp(self):

        # don't do the base setUp...
        # super(TestQOntolgoy, self).setUp()
        pass

    def tearDown(self):

        # don't do the base tearDown...
        # super(TestQOntolgoy, self).tearDown()
        pass

    def test_project_create_groups_and_permissions(self):

        test_project_name = "project"
        test_project_title = "Project"
        test_project_email = "allyn.treshansky@colorado.edu"

        project = create_project(
            name=test_project_name,
            title=test_project_title,
            email=test_project_email,
        )

        test_groups_data = [
            # there is a lil hack here...
            # I don't actually care about ids, but my assertDictEqual fn can ignore nested keys...
            # therefore I set the permission id to a FuzzyInt w/ enough range to handle likely cases...
            {'name': u"{0}_member".format(test_project_name), 'permissions':
                [
                    {'codename': u"view_{0}".format(test_project_name), 'name': u"view {0} instances".format(test_project_name), 'id': FuzzyInt(1, 100)}
                ]
            },
            {'name': u"{0}_admin".format(test_project_name), 'permissions':
                [
                    {'codename': u"customize_{0}".format(test_project_name), 'name': u'customize {0} instances'.format(test_project_name), 'id': FuzzyInt(1, 100)},
                    {'codename': u"edit_{0}".format(test_project_name), 'name': u'edit {0} instances'.format(test_project_name), 'id': FuzzyInt(1, 100)},
                    {'codename': u"view_{0}".format(test_project_name), 'name': u'view {0} instances'.format(test_project_name), 'id': FuzzyInt(1, 100)}
                ]
            },
            {'name': u'{0}_user'.format(test_project_name), 'permissions':
                [
                   {'codename': u'edit_{0}'.format(test_project_name), 'name': u'edit {0} instances'.format(test_project_name), 'id': FuzzyInt(1, 100)},
                   {'codename': u'view_{0}'.format(test_project_name), 'name': u'view {0} instances'.format(test_project_name), 'id': FuzzyInt(1, 100)}
                ]
            },
            {'name': u'{0}_pending'.format(test_project_name), 'permissions':
                [
                   {'codename': u'view_{0}'.format(test_project_name), 'name': u'view {0} instances'.format(test_project_name), 'id': FuzzyInt(1, 100)}
                ]
            }
        ]

        actual_groups_data = [
            serialize_model_to_dict(group, include={
                "permissions": [
                    serialize_model_to_dict(permission, exclude=["content_type"])
                    for permission in group.permissions.all()
                ]
            })
            for group in project.groups.all()
        ]

        for actual_group_data, test_group_data in zip(actual_groups_data, test_groups_data):
            self.assertDictEqual(actual_group_data, test_group_data, excluded_keys=["id"])

    def test_project_delete_groups_and_permissions(self):

        test_project_name = "project"
        test_project_title = "Project"
        test_project_email = "allyn.treshansky@colorado.edu"

        project = create_project(
            name=test_project_name,
            title=test_project_title,
            email=test_project_email,
        )
        self.assertEqual(Group.objects.count(), 4)
        project.delete()
        for group_suffix, permission_prefixes in GROUP_PERMISSIONS.iteritems():
            group_qs = Group.objects.filter(
                name="{0}_{1}".format(test_project_name, group_suffix)
            )
            self.assertQuerysetEqual(group_qs, Group.objects.none())
            for permission_prefix in permission_prefixes:
                permission_qs = Permission.objects.filter(
                    codename="{0}_{1}".format(permission_prefix, project.name)
                )
                self.assertQuerysetEqual(permission_qs, Permission.objects.none())

    def test_project_change_groups_and_permissions(self):
        test_project_name = "project"
        test_project_title = "Project"
        test_project_email = "allyn.treshansky@colorado.edu"

        project = create_project(
            name=test_project_name,
            title=test_project_title,
            email=test_project_email,
        )

        test_project_name = "changed_project"
        project.name = test_project_name
        project.save()

        test_groups_data = [
            # there is a lil hack here...
            # I don't actually care about ids, but my assertDictEqual fn can ignore nested keys...
            # therefore I set the permission id to a FuzzyInt w/ enough range to handle likely cases...
            {'name': u"{0}_member".format(test_project_name), 'permissions':
                [
                    {'codename': u"view_{0}".format(test_project_name),
                     'name': u"view {0} instances".format(test_project_name), 'id': FuzzyInt(1, 100)}
                ]
             },
            {'name': u"{0}_admin".format(test_project_name), 'permissions':
                [
                    {'codename': u"customize_{0}".format(test_project_name),
                     'name': u'customize {0} instances'.format(test_project_name), 'id': FuzzyInt(1, 100)},
                    {'codename': u"edit_{0}".format(test_project_name),
                     'name': u'edit {0} instances'.format(test_project_name), 'id': FuzzyInt(1, 100)},
                    {'codename': u"view_{0}".format(test_project_name),
                     'name': u'view {0} instances'.format(test_project_name), 'id': FuzzyInt(1, 100)}
                ]
             },
            {'name': u'{0}_user'.format(test_project_name), 'permissions':
                [
                    {'codename': u'edit_{0}'.format(test_project_name),
                     'name': u'edit {0} instances'.format(test_project_name), 'id': FuzzyInt(1, 100)},
                    {'codename': u'view_{0}'.format(test_project_name),
                     'name': u'view {0} instances'.format(test_project_name), 'id': FuzzyInt(1, 100)}
                ]
             },
            {'name': u'{0}_pending'.format(test_project_name), 'permissions':
                [
                    {'codename': u'view_{0}'.format(test_project_name),
                     'name': u'view {0} instances'.format(test_project_name), 'id': FuzzyInt(1, 100)}
                ]
             }
        ]

        actual_groups_data = [
            serialize_model_to_dict(group, include={
                "permissions": [
                    serialize_model_to_dict(permission, exclude=["content_type"])
                    for permission in group.permissions.all()
                    ]
            })
            for group in project.groups.all()
            ]

        for actual_group_data, test_group_data in zip(actual_groups_data, test_groups_data):
            self.assertDictEqual(actual_group_data, test_group_data, excluded_keys=["id"])
