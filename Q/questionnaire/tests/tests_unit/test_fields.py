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


class TestFileFieldsModel(TestModel):
    name = models.CharField(blank=True, max_length=BIG_STRING, unique=True)
    file = QFileField(blank=True, upload_to=UPLOAD_PATH)


class TestCardinalityFieldsModel(TestModel):
    name = models.CharField(blank=True, max_length=BIG_STRING, unique=True)
    cardinality = QCardinalityField(blank=True)


class TestVersionFieldsModel(TestModel):
    name = models.CharField(blank=True, max_length=BIG_STRING, unique=True)
    version = QVersionField(blank=True, null=True)


class TestEnumerationFieldsModel(TestModel):
    name = models.CharField(blank=True, max_length=BIG_STRING, unique=True)
    enumeration = QEnumerationField(blank=True, null=True)


class TestUnsavedFieldsModelOne(TestModel):

    class TestUnsavedFieldsModelOneRelatedManger(QUnsavedRelatedManager):
        def get_unsaved_related_field_name(self):
            field = TestUnsavedFieldsModelOne._meta.get_field_by_name("link_to_testunsavedfieldsmodeltwo")[0]
            related_field_name = field.related.name
            unsaved_related_field_name = "_unsaved_{0}".format(related_field_name)
            return unsaved_related_field_name

    objects = models.Manager()
    test_manager = TestUnsavedFieldsModelOneRelatedManger()

    name = models.CharField(blank=True, max_length=BIG_STRING, unique=True)
    link_to_testunsavedfieldsmodeltwo = models.ForeignKey("TestUnsavedFieldsModelTwo", blank=True, null=True, related_name="link_to_testunsavedfieldsmodelone")

    def __unicode__(self):
        return u"%s" % self.name


class TestUnsavedFieldsModelTwo(TestModel):

    objects = models.Manager()

    name = models.CharField(blank=True, max_length=BIG_STRING, unique=True)
    # link_to_testunsavedfieldsmodelone = models.ManyToOneRel("TestUnsavedFieldsModelTwo", blank=True, null=True)

    def __unicode__(self):
        return u"%s" % self.name


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
    "test_cardinality_fields_model": TestCardinalityFieldsModel,
    "test_version_fields_model": TestVersionFieldsModel,
    "test_enumeration_fields_model": TestEnumerationFieldsModel,
    "test_unsaved_fields_model_one": TestUnsavedFieldsModelOne,
    "test_unsaved_fields_model_two": TestUnsavedFieldsModelTwo,
    "test_unsaved_fields_model_parent": TestUnsavedFieldsModelParent,
    "test_unsaved_fields_models_child": TestUnsavedFieldsModelChild,
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

    #######################
    # test unsaved fields #
    #######################

    # ordinary code would be something like: test.model_parent.add(*[test_model_child1, test_model_child2,])
    # but Django balks at relationships between unsaved models
    # so just checking that my custom code can handle unsaved models
    # (it doesn't actually have to write to the db, it just needs to store the correct relationships in memory)

    def test_m2m_manager_unsaved(self):

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

    def test_m2m_manager_saved(self):
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

    def test_m2m_manager_mixed(self):
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

    # def test_unsaved_fk_field(self):
    #     test_model_one = TestUnsavedFieldsModelOne(name="one")
    #     test_model_two = TestUnsavedFieldsModelTwo(name="two")
    #
    #     with self.assertRaises(ValueError):
    #         test_model_one.link_to_testunsavedfieldsmodeltwo = test_model_two
    #
    #     with allow_unsaved_fk(TestUnsavedFieldsModelOne, ["link_to_testunsavedfieldsmodeltwo"]):
    #         test_model_one.link_to_testunsavedfieldsmodeltwo = test_model_two
    #         self.assertEqual(test_model_one.link_to_testunsavedfieldsmodeltwo, test_model_two)

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

        test_file_field_model = TestFileFieldsModel(name="test", file=test_file)
        test_file_field_model.save()
        self.assertTrue(os.path.isfile(self.get_file_path(test_file)))

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
        self.assertTrue(os.path.isfile(self.get_file_path(test_file)))

        # deleting the 1st model shouldn't delete the file
        # (b/c the 2nd model is still using it)
        test_file_field_model_1.delete()
        self.assertTrue(os.path.isfile(self.get_file_path(test_file)))

        # deleting the 2nd model should delete the file
        # (b/c no other models are still using it)
        test_file_field_model_2.delete()
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
        test_file_field_model = TestFileFieldsModel()

        # assign test_file_1;
        # the file should be copied to the correct path
        test_file_field_model.file = test_file_1
        test_file_field_model.save()
        self.assertTrue(os.path.isfile(self.get_file_path(test_file_1)))
        self.assertEqual(len(os.listdir(test_file_dir)), 1)
        self.assertEqual(test_file_field_model.file.read(), test_file_1_content)

        # assign test_file_2;
        # the file should be copied to the correct path
        # but the previous file should still exist
        test_file_field_model.file = test_file_2
        test_file_field_model.save()
        self.assertTrue(os.path.isfile(self.get_file_path(test_file_2)))
        self.assertEqual(len(os.listdir(test_file_dir)), 2)
        self.assertEqual(test_file_field_model.file.read(), test_file_2_content)

        # assign test_file_3;
        # the file should be copied to the correct path
        # and should replace the existing file w/ the same name
        test_file_field_model.file = test_file_3
        test_file_field_model.save()
        self.assertTrue(os.path.isfile(self.get_file_path(test_file_3)))
        self.assertEqual(len(os.listdir(test_file_dir)), 2)
        self.assertEqual(test_file_field_model.file.read(), test_file_3_content)

    ##########################
    # test cardinality field #
    ##########################

    def test_qcardinalityfield(self):

        default_min, default_max = QCardinalityField.default_value.split("|")

        test_cardinality_field_model = TestCardinalityFieldsModel(name="test")
        test_cardinality_field_model.save()

        _min = test_cardinality_field_model.get_cardinality_min()
        _max = test_cardinality_field_model.get_cardinality_max()
        self.assertEqual(_min, default_min)
        self.assertEqual(_max, default_max)

        test_cardinality_field_model.set_cardinality_min(1)
        test_cardinality_field_model.set_cardinality_max("*")
        test_cardinality_field_model.save()

        _min = test_cardinality_field_model.get_cardinality_min()
        _max = test_cardinality_field_model.get_cardinality_max()
        self.assertEqual(_min, u"1")
        self.assertEqual(_max, u"*")

    ######################
    # test version field #
    ######################

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

    # # ##########################
    # # # test enumeration field #
    # # ##########################
    # #
    # # def test_enumeration_field(self):
    # #
    # #     test_enumeration = [
    # #         {"order": 3, "value": u"three", "documentation": None},
    # #         {"order": 2, "value": u"two", "documentation": u"The second thing."},
    # #         {"order": 1, "value": u"one", "documentation": u"The first thing."},
    # #     ]
    # #
    # #     test_enumeration_field_model = TestEnumeartionFieldsModel(name="test")
    # #     test_enumeration_field_model.enumeration = test_enumeration
    # #     test_enumeration_field_model.save()
    # #     test_enumeration_field_model.refresh_from_db()
    # #
    # #     test_enumeration_members = test_enumeration_field_model.get_enumeration_members()
    # #
    # #     self.assertDictEqual(test_enumeration_members[0], test_enumeration[2])
    # #     self.assertDictEqual(test_enumeration_members[1], test_enumeration[1])
    # #     self.assertDictEqual(test_enumeration_members[2], test_enumeration[0])
    # #
    # #     with self.assertRaises(ValidationError):
    # #         test_enumeration_field_model.enumeration = [{"invalid": "stuff"}, ]
    # #         test_enumeration_field_model.save()
    # #         test_enumeration_field_model.refresh_from_db()
