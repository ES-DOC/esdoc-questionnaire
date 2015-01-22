####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2014 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'ben.koziol'
__date__ = "Dec 01, 2014 3:00:00 PM"

"""
.. module:: test_fields

Tests the custom fields specific to the CIM customizer
"""

from django.db import connection, models
from django.core.management.color import no_style
from django.forms.models import ModelForm

from CIM_Questionnaire.questionnaire.tests.test_base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.forms.forms_base import MetadataForm
from CIM_Questionnaire.questionnaire.utils import APP_LABEL, BIG_STRING, HUGE_STRING, model_to_data, get_data_from_form
from CIM_Questionnaire.questionnaire.fields import *


class FieldModel(models.Model):
    """
    The base class for field-specific models below;
    These classes are just used for testing fields, therefore they shouldn't be in the regular db
    hence I define them here rather than the "models" directory and they are unlisted in INSTALLED_APPLICATIONS
    in order to ensure that they get added and removed from the test db (which is loaded initially via fixtures),
    the create_table and delete_table methods are used in setUp and tearDown below
    (got the idea from http://datahackermd.com/2013/testing-django-fields/)
    """

    class Meta:
        app_label = APP_LABEL
        abstract = True

    @classmethod
    def create_table(cls):
        table_name = cls._meta.db_table
        raw_sql, refs = connection.creation.sql_create_model(cls, no_style(), [])
        sql = u'\n'.join(raw_sql).encode('utf-8')
        cls.delete_table()
        cursor = connection.cursor()
        try:
            cursor.execute(sql)
        finally:
            cursor.close()

    @classmethod
    def delete_table(cls):
        table_name = cls._meta.db_table
        cursor = connection.cursor()
        try:
            cursor.execute('DROP TABLE IF EXISTS %s' % table_name)
        except:
            # Catch anything backend-specific here.
            # (E.g., MySQLdb raises a warning if the table didn't exist.)
            pass
        finally:
            cursor.close()

    def get_form_data(self):
        form_data = model_to_data(
            self,
            exclude=[],
            include={
                "loaded": True,  # here is not the place to test loaded/unloaded forms
            }
        )
        return form_data


######################################################################################
# these next few models & forms are used for testing custom field types              #
# I am testing them in isolation here, away from the complexity of the questionnaire #
# (hence the use of the create/delete fns above and setup/teardown fns below)        #
######################################################################################

class EnumerationFieldModel(FieldModel):

    name = models.CharField(blank=True, null=True, max_length=BIG_STRING, unique=True)
    enumeration_value = EnumerationField(blank=True, null=True)
    enumeration_other_value = models.CharField(max_length=HUGE_STRING, blank=True, null=True)


class EnumerationFieldForm(MetadataForm):

    class Meta:
        model = EnumerationFieldModel

    pass


class CardinalityFieldModel(FieldModel):

    name = models.CharField(blank=True, null=True, max_length=BIG_STRING, unique=True)
    cardinality = CardinalityField(blank=True)


class CardinalityFieldForm(MetadataForm):

    class Meta:
        model = CardinalityFieldModel

    pass


#################################
# now for the actual test class #
#################################

class Test(TestQuestionnaireBase):

    field_models = {
        "enumeration_field_model": EnumerationFieldModel,
        "cardinality_field_model": CardinalityFieldModel,
    }

    def setUp(self):
        create_fn_name = "create_table"
        for model_name, model_class in self.field_models.iteritems():
            try:
                model_create_fn = getattr(model_class, create_fn_name)
                model_create_fn()
            except AttributeError:
                msg = "%s has no %s method" % (model_name, create_fn_name)
                raise TypeError(msg)
        super(Test, self).setUp()

    def tearDown(self):
        delete_fn_name = "create_table"
        for model_name, model_class in self.field_models.iteritems():
            try:
                model_delete_fn = getattr(model_class, delete_fn_name)
                model_delete_fn()
            except AttributeError:
                msg = "%s has no %s method" % (model_name, delete_fn_name)
                raise TypeError(msg)

        super(Test, self).tearDown()

    ######################################
    # ...and now for the actual tests... #
    ######################################

    def test_enumeration_field(self):

        enumeration_field_model = EnumerationFieldModel(name="test")

        pass

    def test_cardinality_field(self):

        cardinality_name = "cardinality_test"

        cardinality_0_to_1 = [u"0", u"1"]  # valid cardinality
        cardinality_0_to_many = [u"0", u"*"]  # valid cardinality
        cardinality_5_to_1 = [u"5", u"1"]  # invalid cardinality; working through forms should catch it
        cardinality_100_to_foo = [u"100", u"foo"]  # invalid cardinality; working through forms should catch it
        cardinality_none = [None, None]  # invalid cardinality; working through forms should catch it

        # testing creation of cardinality fields through forms rather than models

        cardinality_field_model = CardinalityFieldModel(name=",".join(cardinality_0_to_1), cardinality=cardinality_0_to_1)
        cardinality_form_data = cardinality_field_model.get_form_data()
        cardinality_form = CardinalityFieldForm(initial=cardinality_form_data, prefix=cardinality_name)
        post_data = get_data_from_form(cardinality_form)
        cardinality_form = CardinalityFieldForm(data=post_data, initial=cardinality_form_data, prefix=cardinality_name)
        validity = cardinality_form.is_valid(loaded=cardinality_form.get_current_field_value("loaded"))
        self.assertTrue(validity)
        cardinality_field_model = cardinality_form.save()
        self.assertEqual(cardinality_field_model.cardinality.split("|"), cardinality_0_to_1)

        cardinality_field_model = CardinalityFieldModel(name=",".join(cardinality_0_to_many), cardinality=cardinality_0_to_many)
        cardinality_form_data = cardinality_field_model.get_form_data()
        cardinality_form = CardinalityFieldForm(initial=cardinality_form_data, prefix=cardinality_name)
        post_data = get_data_from_form(cardinality_form)
        cardinality_form = CardinalityFieldForm(data=post_data, initial=cardinality_form_data, prefix=cardinality_name)
        validity = cardinality_form.is_valid(loaded=cardinality_form.get_current_field_value("loaded"))
        self.assertTrue(validity)
        cardinality_field_model = cardinality_form.save()
        self.assertEqual(cardinality_field_model.cardinality.split("|"), cardinality_0_to_many)

        cardinality_field_model = CardinalityFieldModel(name=",".join(cardinality_5_to_1), cardinality=cardinality_5_to_1)
        cardinality_form_data = cardinality_field_model.get_form_data()
        cardinality_form = CardinalityFieldForm(initial=cardinality_form_data, prefix=cardinality_name)
        post_data = get_data_from_form(cardinality_form)
        cardinality_form = CardinalityFieldForm(data=post_data, initial=cardinality_form_data, prefix=cardinality_name)
        validity = cardinality_form.is_valid(loaded=cardinality_form.get_current_field_value("loaded"))
        self.assertFalse(validity)

        cardinality_field_model = CardinalityFieldModel(name=",".join(cardinality_100_to_foo), cardinality=cardinality_100_to_foo)
        cardinality_form_data = cardinality_field_model.get_form_data()
        cardinality_form = CardinalityFieldForm(initial=cardinality_form_data, prefix=cardinality_name)
        post_data = get_data_from_form(cardinality_form)
        cardinality_form = CardinalityFieldForm(data=post_data, initial=cardinality_form_data, prefix=cardinality_name)
        validity = cardinality_form.is_valid(loaded=cardinality_form.get_current_field_value("loaded"))
        self.assertFalse(validity)

        import ipdb; ipdb.set_trace()
        cardinality_field_model = CardinalityFieldModel(name="cardinality_none")  # cardinality=cardinality_none
        cardinality_form_data = cardinality_field_model.get_form_data()
        cardinality_form = CardinalityFieldForm(initial=cardinality_form_data, prefix=cardinality_name)
        post_data = get_data_from_form(cardinality_form)
        cardinality_form = CardinalityFieldForm(data=post_data, initial=cardinality_form_data, prefix=cardinality_name)
        validity = cardinality_form.is_valid(loaded=cardinality_form.get_current_field_value("loaded"))
        self.assertFalse(validity)
