# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import Q.questionnaire.q_utils


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0002_auto_20170201_0630'),
    ]

    operations = [
        migrations.AlterField(
            model_name='qcategorycustomization',
            name='category_title',
            field=models.CharField(max_length=64, verbose_name=b'Title', validators=[Q.questionnaire.q_utils.ValidateNoProfanities()]),
        ),
        migrations.AlterField(
            model_name='qcategorycustomization',
            name='name',
            field=models.CharField(help_text=b'A unique name for this customization.  Only alphanumeric characters are allowed.', max_length=128, verbose_name=b'Customization Name', validators=[Q.questionnaire.q_utils.ValidateNoBadChars(), Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoReservedWords(), Q.questionnaire.q_utils.ValidateNoProfanities()]),
        ),
        migrations.AlterField(
            model_name='qcategoryproxy',
            name='cim_id',
            field=models.CharField(blank=True, max_length=256, null=True, help_text='A unique, CIM-specific, identifier.  This is distinct from the automatically-generated key.  It is required for distinguishing specialized objects of the same class.', validators=[Q.questionnaire.q_utils.ValidateNoSpaces()]),
        ),
        migrations.AlterField(
            model_name='qmodelcustomization',
            name='name',
            field=models.CharField(help_text=b'A unique name for this customization.  Only alphanumeric characters are allowed.', max_length=128, verbose_name=b'Customization Name', validators=[Q.questionnaire.q_utils.ValidateNoBadChars(), Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoReservedWords(), Q.questionnaire.q_utils.ValidateNoProfanities()]),
        ),
        migrations.AlterField(
            model_name='qmodelproxy',
            name='cim_id',
            field=models.CharField(blank=True, max_length=256, null=True, help_text='A unique, CIM-specific, identifier.  This is distinct from the automatically-generated key.  It is required for distinguishing specialized objects of the same class.', validators=[Q.questionnaire.q_utils.ValidateNoSpaces()]),
        ),
        migrations.AlterField(
            model_name='qontology',
            name='name',
            field=models.CharField(max_length=512, validators=[Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoBadChars()]),
        ),
        migrations.AlterField(
            model_name='qproject',
            name='name',
            field=models.CharField(unique=True, max_length=128, validators=[Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoBadChars(), Q.questionnaire.q_utils.ValidateNoReservedWords(), Q.questionnaire.q_utils.ValidateNoProfanities()]),
        ),
        migrations.AlterField(
            model_name='qpropertycustomization',
            name='name',
            field=models.CharField(help_text=b'A unique name for this customization.  Only alphanumeric characters are allowed.', max_length=128, verbose_name=b'Customization Name', validators=[Q.questionnaire.q_utils.ValidateNoBadChars(), Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoReservedWords(), Q.questionnaire.q_utils.ValidateNoProfanities()]),
        ),
        migrations.AlterField(
            model_name='qpropertycustomization',
            name='property_title',
            field=models.CharField(max_length=128, validators=[Q.questionnaire.q_utils.ValidateNoProfanities()]),
        ),
        migrations.AlterField(
            model_name='qpropertyproxy',
            name='cim_id',
            field=models.CharField(blank=True, max_length=256, null=True, help_text='A unique, CIM-specific, identifier.  This is distinct from the automatically-generated key.  It is required for distinguishing specialized objects of the same class.', validators=[Q.questionnaire.q_utils.ValidateNoSpaces()]),
        ),
        migrations.AlterUniqueTogether(
            name='qcategoryproxy',
            unique_together=set([('model_proxy', 'name', 'cim_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='qpropertyproxy',
            unique_together=set([]),
        ),
    ]
