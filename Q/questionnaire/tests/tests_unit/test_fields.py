####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

"""
.. module:: test_utils

Tests for utilities
"""

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction

from Q.questionnaire import APP_LABEL
from Q.questionnaire.tests.test_base import TestQBase, TestModel, TEST_FILE_PATH, incomplete_test
from Q.questionnaire.q_constants import *
from Q.questionnaire.q_fields import *


###############################
# some constants & helper fns #
###############################

UPLOAD_DIR = "tests"
UPLOAD_PATH = os.path.join(APP_LABEL, UPLOAD_DIR)  # this will be concatenated w/ MEDIA_ROOT by FileField



def get_file_path(file=None):
    if file:
        return os.path.join(settings.MEDIA_ROOT, UPLOAD_PATH, file.name)
    else:
        return os.path.join(settings.MEDIA_ROOT, UPLOAD_PATH)


def get_test_json_schema():
    with open(os.path.join(TEST_FILE_PATH, "test_json_schema.schema.json"), 'r') as file:
        test_json_schema = json.load(file)
    file.closed
    return test_json_schema

#########################################
# a silly set of models to use w/ tests #
#########################################


class TestFileFieldsModel(TestModel):
    name = models.CharField(blank=True, max_length=BIG_STRING, unique=True)
    file = QFileField(blank=True, upload_to=UPLOAD_PATH)


class TestJSONFieldsModel(TestModel):
    name = models.CharField(blank=True, max_length=BIG_STRING, unique=True)
    json = QJSONField(blank=True, null=True, schema=get_test_json_schema)


class TestVersionFieldsModel(TestModel):
    name = models.CharField(blank=True, max_length=BIG_STRING, unique=True)
    version = QVersionField(blank=True, null=True)


class TestUnsavedFieldsModelParent(TestModel):

    name = models.CharField(blank=True, max_length=BIG_STRING, unique=True)


class TestUnsavedFieldsModelChild(TestModel):

    class _TestUnsavedChildrenManager(QUnsavedRelatedManager):
        field_name = "parent"

    objects = models.Manager()
    allow_unsaved_children_manager = _TestUnsavedChildrenManager()

    name = models.CharField(blank=True, max_length=BIG_STRING, unique=True)
    parent = models.ForeignKey("TestUnsavedFieldsModelParent", blank=True, null=True, related_name="children")

TEST_MODELS = {
    "test_file_fields_model": TestFileFieldsModel,
    "test_json_fields_model": TestJSONFieldsModel,
    "test_version_fields_model": TestVersionFieldsModel,
    "test_unsaved_fields_model_parent": TestUnsavedFieldsModelParent,
    "test_unsaved_fields_model_child": TestUnsavedFieldsModelChild,
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
        self.test_file_dir = get_file_path()
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
            os.unlink(os.path.join(self.test_file_dir, test_file_name))
        self.assertEqual(len(os.listdir(self.test_file_dir)), 0)

        # don't need questionnaire infrastructure...
        # super(Test, self).tearDown()

    #######################
    # test unsaved fields #
    #######################

    # ordinary code would be something like: test.model_parent.add(*[test_model_child1, test_model_child2,])
    # but Django balks at relationships between unsaved models
    # so just checking that my custom code can handle unsaved models
    # (it doesn't actually have to write to the db, it just needs to store the correct relationships in memory)

    def test_unsaved_manager_with_unsaved_models(self):

        parent_model = TestUnsavedFieldsModelParent(name="parent")
        child_model1 = TestUnsavedFieldsModelChild(name="child1")
        child_model2 = TestUnsavedFieldsModelChild(name="child2")

        # test all & count...
        self.assertListEqual(parent_model.children(manager="allow_unsaved_children_manager").all(), [])
        self.assertEqual(parent_model.children(manager="allow_unsaved_children_manager").count(), 0)

        # test adding...
        parent_model.children(manager="allow_unsaved_children_manager").add_potentially_unsaved(*[child_model1, child_model2])
        self.assertListEqual(parent_model.children(manager="allow_unsaved_children_manager").all(), [child_model1, child_model2])
        self.assertEqual(parent_model.children(manager="allow_unsaved_children_manager").count(), 2)

        # test (unchainable) filtering...
        child_model_list = parent_model.children(manager="allow_unsaved_children_manager").filter_potentially_unsaved(name="child1")
        no_model_list = parent_model.children(manager="allow_unsaved_children_manager").filter_potentially_unsaved(name="no name")
        self.assertEqual(len(child_model_list), 1)
        self.assertEqual(len(no_model_list), 0)
        with self.assertRaises(AttributeError):
            child_model_list.filter(name="child1")

        # test ordering...
        reversed_child_model_list = parent_model.children(manager="allow_unsaved_children_manager").order_by("name", reverse=True)
        self.assertListEqual(reversed_child_model_list, [child_model2, child_model1])

        # test removing...
        parent_model.children(manager="allow_unsaved_children_manager").remove_potentially_unsaved(child_model1)
        self.assertListEqual(parent_model.children(manager="allow_unsaved_children_manager").all(), [child_model2])

        # test getting...
        child_model = parent_model.children(manager="allow_unsaved_children_manager").get(name="child2")
        with self.assertRaises(ObjectDoesNotExist):
            parent_model.children(manager="allow_unsaved_children_manager").get(name="no name")
        self.assertEqual(child_model, child_model2)

        # test caching...
        self.assertEqual(id(child_model), id(child_model2))

    def test_unsaved_manager_with_saved_models(self):
        parent_model = TestUnsavedFieldsModelParent(name="parent")
        child_model1 = TestUnsavedFieldsModelChild(name="child1")
        child_model2 = TestUnsavedFieldsModelChild(name="child2")

        parent_model.save()
        child_model1.save()
        child_model2.save()
        parent_model.children.add(child_model1)

        # test all & count...
        self.assertListEqual(parent_model.children(manager="allow_unsaved_children_manager").all(), [child_model1])
        self.assertEqual(parent_model.children(manager="allow_unsaved_children_manager").count(), 1)

        # test adding...
        parent_model.children(manager="allow_unsaved_children_manager").add_potentially_unsaved(*[child_model1, child_model2])
        self.assertListEqual(parent_model.children(manager="allow_unsaved_children_manager").all(), [child_model1, child_model2])
        self.assertEqual(parent_model.children(manager="allow_unsaved_children_manager").count(), 2)

        # test (unchainable) filtering...
        child_model_list = parent_model.children(manager="allow_unsaved_children_manager").filter_potentially_unsaved(name="child1")
        no_model_list = parent_model.children(manager="allow_unsaved_children_manager").filter_potentially_unsaved(name="no name")
        self.assertEqual(len(child_model_list), 1)
        self.assertEqual(len(no_model_list), 0)
        with self.assertRaises(AttributeError):
            child_model_list.filter(name="child1")

        # test ordering...
        reversed_child_model_list = parent_model.children(manager="allow_unsaved_children_manager").order_by("name", reverse=True)
        self.assertListEqual(reversed_child_model_list, [child_model2, child_model1])

        # test removing...
        parent_model.children(manager="allow_unsaved_children_manager").remove_potentially_unsaved(child_model1)
        self.assertListEqual(parent_model.children(manager="allow_unsaved_children_manager").all(), [child_model2])

        # test getting...
        child_model = parent_model.children(manager="allow_unsaved_children_manager").get(name="child2")
        with self.assertRaises(ObjectDoesNotExist):
            parent_model.children(manager="allow_unsaved_children_manager").get(name="no name")
        self.assertEqual(child_model, child_model2)

        # test caching...
        self.assertEqual(id(child_model), id(child_model2))

    def test_unsaved_manager_with_mixed_models(self):
        parent_model = TestUnsavedFieldsModelParent(name="parent")
        child_model1 = TestUnsavedFieldsModelChild(name="child1")
        child_model2 = TestUnsavedFieldsModelChild(name="child2")

        child_model1.save()
        child_model2.save()

        # test all & count...
        self.assertListEqual(parent_model.children(manager="allow_unsaved_children_manager").all(), [])
        self.assertEqual(parent_model.children(manager="allow_unsaved_children_manager").count(), 0)

        # test adding...
        parent_model.children(manager="allow_unsaved_children_manager").add_potentially_unsaved(
            *[child_model1, child_model2])
        self.assertListEqual(parent_model.children(manager="allow_unsaved_children_manager").all(),
                             [child_model1, child_model2])
        self.assertEqual(parent_model.children(manager="allow_unsaved_children_manager").count(), 2)

        # test (unchainable) filtering...
        child_model_list = parent_model.children(manager="allow_unsaved_children_manager").filter_potentially_unsaved(
            name="child1")
        no_model_list = parent_model.children(manager="allow_unsaved_children_manager").filter_potentially_unsaved(
            name="no name")
        self.assertEqual(len(child_model_list), 1)
        self.assertEqual(len(no_model_list), 0)
        with self.assertRaises(AttributeError):
            child_model_list.filter(name="child1")

        # test ordering...
        reversed_child_model_list = parent_model.children(manager="allow_unsaved_children_manager").order_by("name",
                                                                                                             reverse=True)
        self.assertListEqual(reversed_child_model_list, [child_model2, child_model1])

        # test removing...
        parent_model.children(manager="allow_unsaved_children_manager").remove_potentially_unsaved(child_model1)
        self.assertListEqual(parent_model.children(manager="allow_unsaved_children_manager").all(), [child_model2])

        # test getting...
        child_model = parent_model.children(manager="allow_unsaved_children_manager").get(name="child2")
        with self.assertRaises(ObjectDoesNotExist):
            parent_model.children(manager="allow_unsaved_children_manager").get(name="no name")
        self.assertEqual(child_model, child_model2)

        # test caching...
        self.assertEqual(id(child_model), id(child_model2))

    ##############
    # QJSONField #
    ##############

    def test_json_field(self):
        test_json_fields_model = TestJSONFieldsModel(
            name="test"
        )

        valid_json = {
            "name": "test",
            "documentation": "some documentation"
        }
        invalid_json = {
            "invalid_field": "test"
        }
        test_json_fields_model.json = valid_json
        test_json_fields_model.save()
        self.assertDictEqual(test_json_fields_model.json, valid_json)
        with self.assertRaises(ValidationError):
            test_json_fields_model.json = invalid_json
            test_json_fields_model.save()

    ##############
    # QFileField #
    ##############

    def test_qfilefield_creation(self):

        # ensure correct storage method and help text are set

        test_file_content = "test file"
        test_file = SimpleUploadedFile("test", test_file_content)

        test_file_field_model = TestFileFieldsModel(name="test", file=test_file)
        test_file_field_model.save()
        self.assertTrue(os.path.isfile(get_file_path(test_file)))

        test_file_field = test_file_field_model.file
        self.assertTrue(isinstance(test_file_field.storage, OverwriteStorage))
        self.assertEqual(test_file_field.field.help_text, QFileField.default_help_text)

    def test_qfilefield_deletion(self):

        # files should be deleted when no other class instances are using them

        test_file_content = "test file"
        test_file = SimpleUploadedFile("test", test_file_content)

        test_file_field_model_1 = TestFileFieldsModel(name="one", file=test_file)
        test_file_field_model_2 = TestFileFieldsModel(name="two", file=test_file)
        test_file_field_model_1.save()
        test_file_field_model_2.save()
        self.assertTrue(os.path.isfile(get_file_path(test_file)))

        # deleting the 1st model shouldn't delete the file
        # (b/c the 2nd model is still using it)
        test_file_field_model_1.delete()
        self.assertTrue(os.path.isfile(get_file_path(test_file)))

        # deleting the 2nd model should delete the file
        # (b/c no other models are still using it)
        test_file_field_model_2.delete()
        self.assertFalse(os.path.isfile(get_file_path(test_file)))

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
        test_file_dir = get_file_path()
        self.assertEqual(len(os.listdir(test_file_dir)), 0)
        test_file_field_model = TestFileFieldsModel()

        # assign test_file_1;
        # the file should be copied to the correct path
        test_file_field_model.file = test_file_1
        test_file_field_model.save()
        self.assertTrue(os.path.isfile(get_file_path(test_file_1)))
        self.assertEqual(len(os.listdir(test_file_dir)), 1)
        self.assertEqual(test_file_field_model.file.read(), test_file_1_content)

        # assign test_file_2;
        # the file should be copied to the correct path
        # but the previous file should still exist
        test_file_field_model.file = test_file_2
        test_file_field_model.save()
        self.assertTrue(os.path.isfile(get_file_path(test_file_2)))
        self.assertEqual(len(os.listdir(test_file_dir)), 2)
        self.assertEqual(test_file_field_model.file.read(), test_file_2_content)

        # assign test_file_3;
        # the file should be copied to the correct path
        # and should replace the existing file w/ the same name
        test_file_field_model.file = test_file_3
        test_file_field_model.save()
        self.assertTrue(os.path.isfile(get_file_path(test_file_3)))
        self.assertEqual(len(os.listdir(test_file_dir)), 2)
        self.assertEqual(test_file_field_model.file.read(), test_file_3_content)

    #################
    # QVersionField #
    #################

    def test_version_field(self):

        test_version_field_model = TestVersionFieldsModel(name="test")
        test_version_field_model.version = "1.5"
        test_version_field_model.save()
        test_version_field_model.refresh_from_db()

        self.assertEqual(test_version_field_model.version.string, "1.5.0")
        self.assertEqual(test_version_field_model.version.major(), 1)
        self.assertEqual(test_version_field_model.version.minor(), 5)
        self.assertEqual(test_version_field_model.version.patch(), 0)
        self.assertTrue(test_version_field_model.version == "1.5")
        self.assertTrue(test_version_field_model.version > "0.5")
        self.assertTrue(test_version_field_model.version >= "1.5")
        self.assertTrue(test_version_field_model.version < "1.50")
        self.assertTrue(test_version_field_model.version <= "2.5")

        with self.assertRaises(ValueError):
            test_version_field_model.version = "not a version"
            test_version_field_model.save()

        with self.assertRaises(NotImplementedError):
            test_version_field_model.version = "1.2.3.4"
            test_version_field_model.save()

    def test_version_field_contribute_to_class(self):
        test_version_field_model = TestVersionFieldsModel(name="test")
        test_version_field_model.version = "1.2.3"
        test_version_field_model.save()
        test_version_field_model.refresh_from_db()

        major = test_version_field_model.get_version_major()
        self.assertEqual(major, 1)

        minor = test_version_field_model.get_version_minor()
        self.assertEqual(minor, 2)

        patch = test_version_field_model.get_version_patch()
        self.assertEqual(patch, 3)

    def test_version_field_underspecified(self):
        test_version_field_model = TestVersionFieldsModel(name="test")
        test_version_field_model.version = "1.2"
        test_version_field_model.save()
        test_version_field_model.refresh_from_db()

        fully_specified_version = Version("1.2.0")
        self.assertEqual(fully_specified_version, test_version_field_model.version)

        patch = test_version_field_model.get_version_patch()
        self.assertEqual(patch, 0)
