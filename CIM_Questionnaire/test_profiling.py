#! /usr/bin/python

__author__ = "allyn.treshansky"
__date__ = "$Jan 15, 2014 15:28:06 PM$"

import os


def update_db(sender, **kwargs):

    from django.conf import settings

    # when the 1st APP tries to sync,
    # check if auth_permission_name is too small;
    # if so, increase the column size
    if kwargs['app'].__name__ == settings.INSTALLED_APPS[0] + ".models":
        from django.contrib.auth.models import Permission
        auth_permission_name = Permission._meta.get_field_by_name("name")[0]
        if auth_permission_name.max_length < 100:
            from django.db import connection
            cursor = connection.cursor()
            cursor.execute("ALTER TABLE auth_permission DROP COLUMN name;")
            cursor.execute("ALTER TABLE auth_permission ADD COLUMN name character varying(100);")


if __name__ == "__main__":

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    # can only import django stuff after DJANGO_SETTINGS_MODULE has been set
    # (also - since this is run outside of server context - the settings module will fail on some imports;
    # hence the try/except block in settings.py for "fixing known django / south / postgres issue")

    from django.db.models.signals import post_syncdb
    post_syncdb.connect(update_db)

    from django.test import runner
    from django.test.utils import setup_test_environment

    class ProfilingTestRunner(runner.DiscoverRunner):

        def __init__(self, *args, **kwargs):
            kwargs["interactive"] = False
            kwargs["verbosity"] = 2
            super(ProfilingTestRunner, self).__init__(**kwargs)

        def setup_databases(self, **kwargs):
            super(ProfilingTestRunner, self).setup_databases(**kwargs)

        def teardown_databases(self, old_config, **kwargs):
            destroy = True
            keepdb = False
            old_names, mirrors = old_config
            for connection, old_name, destroy in old_names:
                if destroy:
                    connection.creation.destroy_test_db(old_name, self.verbosity, keepdb)


    setup_test_environment()

    profiling_test_runner = ProfilingTestRunner()
    profiling_test_runner.setup_databases()

    from CIM_Questionnaire.questionnaire.tests.tests_unit.test_views.test_views_customize import Test as CustomizeTest
    customize_tests = [ "test_validate_view_arguments" ]

    test_suite = profiling_test_runner.TestSuite()
    test_suite = runner.TestSuite()

    for customize_test in customize_tests:
        test_suite.addTest(CustomizeTest(customize_test))

    profiling_test_runner.run(test_suite)

    # cProfile.run(customize_test.test_validate_view_arguments())

    print "done"