####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################


from Q.questionnaire.tests.test_base import TestQBase, incomplete_test
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

    def test_project_create_groups(self):

        import ipdb; ipdb.set_trace()
        test_project = QProject(

        )
