# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import Q.questionnaire.q_utils


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0006_auto_20160120_2240'),
    ]

    operations = [
        migrations.AddField(
            model_name='qstandardpropertyproxy',
            name='relationship_target_models',
            field=models.ManyToManyField(related_name='+', to='questionnaire.QModelProxy', blank=True),
        ),
        migrations.AddField(
            model_name='qstandardpropertyproxy',
            name='relationship_target_names',
            field=models.TextField(default=b''),
        ),
        migrations.AlterField(
            model_name='qmodelcustomization',
            name='model_root_component',
            field=models.CharField(default=b'RootComponent', max_length=128, verbose_name=b'Name of the root component', blank=True, validators=[Q.questionnaire.q_utils.ValidateNoSpaces()]),
        ),
        migrations.AlterField(
            model_name='qmodelcustomization',
            name='name',
            field=models.CharField(help_text=b'A unique name for this customization.  Spaces or the following characters are not allowed: "\\, /, <, >, %, #, %, {, }, [, ], $, |".', max_length=128, verbose_name=b'Customization Name', validators=[Q.questionnaire.q_utils.ValidateNoBadChars(), Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoReservedWords(), Q.questionnaire.q_utils.ValidateNoProfanities()]),
        ),
        migrations.AlterField(
            model_name='qontology',
            name='description',
            field=models.TextField(help_text=b'This may be overwritten by any descriptive text found in the QXML file.', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='qontology',
            name='name',
            field=models.CharField(max_length=128, validators=[Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoBadChars()]),
        ),
        migrations.AlterField(
            model_name='qproject',
            name='name',
            field=models.CharField(unique=True, max_length=128, validators=[Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoBadChars(), Q.questionnaire.q_utils.ValidateNoReservedWords()]),
        ),
        migrations.AlterField(
            model_name='qscientificcategoryproxy',
            name='key',
            field=models.CharField(blank=True, max_length=256, validators=[Q.questionnaire.q_utils.ValidateNoSpaces()]),
        ),
        migrations.AlterField(
            model_name='qstandardcategoryproxy',
            name='key',
            field=models.CharField(blank=True, max_length=256, validators=[Q.questionnaire.q_utils.ValidateNoSpaces()]),
        ),
        migrations.AlterField(
            model_name='qtestmodel',
            name='name',
            field=models.CharField(unique=True, max_length=128, validators=[Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoBadChars(), Q.questionnaire.q_utils.ValidateNoReservedWords()]),
        ),
        migrations.AlterField(
            model_name='qvocabulary',
            name='name',
            field=models.CharField(max_length=128, validators=[Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoBadChars()]),
        ),
    ]
