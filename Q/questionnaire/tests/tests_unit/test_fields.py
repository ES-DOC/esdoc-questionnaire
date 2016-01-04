####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"

"""
.. module:: test_utils

Tests for utilities
"""

from django.db import models, transaction
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from Q.questionnaire import APP_LABEL
from Q.questionnaire.tests.test_base import TestQBase, TestModel, incomplete_test
from Q.questionnaire.q_constants import *
from Q.questionnaire.q_fields import *


###################################################
# a silly set of models and forms to use w/ tests #
###################################################

UPLOAD_DIR = "tests"
UPLOAD_PATH = os.path.join(APP_LABEL, UPLOAD_DIR)  # this will be concatenated w/ MEDIA_ROOT by FileField

class TestFieldsModel(TestModel):

    name = models.CharField(blank=True, max_length=BIG_STRING, unique=True)
    file = QFileField(blank=True, upload_to=UPLOAD_PATH)
    cardinality = QCardinalityField(blank=True)
    version = QVersionField(blank=True, null=True)

    def __unicode__(self):
        return u"%s" % self.name

TEST_MODELS = {
    "test_fields_model": TestFieldsModel,
}


##############################
# the actual test base class #
##############################

class Test(TestQBase):

    def setUp(self):
        # setup the test models into the test db...
        for model_name, model_class in TEST_MODELS.iteritems():
            create_fn_name = model_class.create_fn_name
            try:
                model_create_fn = getattr(model_class, create_fn_name)
            except AttributeError:
                msg = "%s has no %s method" % (model_name, create_fn_name)
                raise TypeError(msg)
            with transaction.atomic():
                model_create_fn()

        # make sure the UPLOAD_TO directory is clean...
        self.test_file_dir = self.get_file_path()
        self.assertEqual(len(os.listdir(self.test_file_dir)), 0)

        # don't need questionnaire infrastructure...
        # super(Test, self).setUp()

    def tearDown(self):
        # setup the test models into the test db...
        for model_name, model_class in TEST_MODELS.iteritems():
            delete_fn_name = model_class.delete_fn_name
            try:
                model_delete_fn = getattr(model_class, delete_fn_name)
            except AttributeError:
                msg = "%s has no %s method" % (model_name, delete_fn_name)
                raise TypeError(msg)
            with transaction.atomic():
                model_delete_fn()

        # clean the UPLOAD_TO directory...
        for test_file_name in os.listdir(self.test_file_dir):
            os.unlink(os.path.join(self.test_file_dir,test_file_name))
        self.assertEqual(len(os.listdir(self.test_file_dir)), 0)

        # don't need questionnaire infrastructure...
        # super(Test, self).tearDown()

    ###################
    # test file field #
    ###################

    def get_file_path(self, file=None):
        if file:
            return os.path.join(settings.MEDIA_ROOT, UPLOAD_PATH, file.name)
        else:
            return os.path.join(settings.MEDIA_ROOT, UPLOAD_PATH)

    def test_qfilefield_creation(self):

        # ensure correct storage method and help text are set

        test_file_content = "test file"
        test_file = SimpleUploadedFile("test", test_file_content)

        test_field_model = TestFieldsModel(name="test", file=test_file)
        test_field_model.save()
        self.assertTrue(os.path.isfile(self.get_file_path(test_file)))

        test_file_field = test_field_model.file
        self.assertTrue(isinstance(test_file_field.storage, OverwriteStorage))
        self.assertEqual(test_file_field.field.help_text, QFileField.default_help_text)

    def test_qfilefield_deletion(self):

        # files should be deleted when no other class instances are using them

        test_file_content = "test file"
        test_file = SimpleUploadedFile("test", test_file_content)

        test_field_model_1 = TestFieldsModel(name="one", file=test_file)
        test_field_model_2 = TestFieldsModel(name="two", file=test_file)
        test_field_model_1.save()
        test_field_model_2.save()
        self.assertTrue(os.path.isfile(self.get_file_path(test_file)))

        # deleting the 1st model shouldn't delete the file
        # (b/c the 2nd model is still using it)
        test_field_model_1.delete()
        self.assertTrue(os.path.isfile(self.get_file_path(test_file)))

        # deleting the 2nd model should delete the file
        # (b/c no other models are still using it)
        test_field_model_2.delete()
        self.assertFalse(os.path.isfile(self.get_file_path(test_file)))

    def test_overwrite_storage(self):

        # files w/ different names should co-exist
        # files w/ same names should be overwritten
        test_file_1_content = "test file one"
        test_file_2_content = "test file two"
        test_file_3_content = "test file three"
        test_file_1 = SimpleUploadedFile("same_name", test_file_1_content)
        test_file_2 = SimpleUploadedFile("different_name", test_file_2_content)
        test_file_3 = SimpleUploadedFile("same_name", test_file_3_content)

        # begin w/ an empty directory...
        test_file_dir = self.get_file_path()
        self.assertEqual(len(os.listdir(test_file_dir)), 0)
        test_field_model = TestFieldsModel()

        # assign test_file_1;
        # the file should be copied to the correct path
        test_field_model.file = test_file_1
        test_field_model.save()
        self.assertTrue(os.path.isfile(self.get_file_path(test_file_1)))
        self.assertEqual(len(os.listdir(test_file_dir)), 1)
        self.assertEqual(test_field_model.file.read(), test_file_1_content)

        # assign test_file_2;
        # the file should be copied to the correct path
        # but the previous file should still exist
        test_field_model.file = test_file_2
        test_field_model.save()
        self.assertTrue(os.path.isfile(self.get_file_path(test_file_2)))
        self.assertEqual(len(os.listdir(test_file_dir)), 2)
        self.assertEqual(test_field_model.file.read(), test_file_2_content)

        # assign test_file_3;
        # the file should be copied to the correct path
        # and should replace the existing file w/ the same name
        test_field_model.file = test_file_3
        test_field_model.save()
        self.assertTrue(os.path.isfile(self.get_file_path(test_file_3)))
        self.assertEqual(len(os.listdir(test_file_dir)), 2)
        self.assertEqual(test_field_model.file.read(), test_file_3_content)

    ##########################
    # test cardinality field #
    ##########################

    def test_qcardinalityfield(self):

        default_min, default_max = QCardinalityField.default_value.split("|")

        test_field_model = TestFieldsModel(name="test")
        test_field_model.save()

        _min = test_field_model.get_cardinality_min()
        _max = test_field_model.get_cardinality_max()
        self.assertEqual(_min, default_min)
        self.assertEqual(_max, default_max)

        test_field_model.set_cardinality_min(1)
        test_field_model.set_cardinality_max("*")
        test_field_model.save()

        _min = test_field_model.get_cardinality_min()
        _max = test_field_model.get_cardinality_max()
        self.assertEqual(_min, u"1")
        self.assertEqual(_max, u"*")

    ######################
    # test version field #
    ######################

    def test_version_field(self):

        test_field_model = TestFieldsModel(name="test")
        test_field_model.version = "1.5"
        test_field_model.save()
        test_field_model.refresh_from_db()

        self.assertEqual(test_field_model.version.string, "1.5.0")
        self.assertEqual(test_field_model.version.major(), 1)
        self.assertEqual(test_field_model.version.minor(), 5)
        self.assertEqual(test_field_model.version.patch(), 0)
        self.assertTrue(test_field_model.version == "1.5")
        self.assertTrue(test_field_model.version > "0.5")
        self.assertTrue(test_field_model.version >= "1.5")
        self.assertTrue(test_field_model.version < "1.50")
        self.assertTrue(test_field_model.version <= "2.5")

        with self.assertRaises(ValueError):
            test_field_model.version = "not a version"
            test_field_model.save()

        with self.assertRaises(NotImplementedError):
            test_field_model.version = "1.2.3.4"
            test_field_model.save()

