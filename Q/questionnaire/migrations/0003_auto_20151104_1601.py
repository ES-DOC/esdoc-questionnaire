# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import Q.questionnaire.q_utils


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0002_auto_20151031_0505'),
    ]

    operations = [
        migrations.AddField(
            model_name='qscientificpropertycustomization',
            name='display_extra_description',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='qscientificpropertycustomization',
            name='display_extra_standard_name',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='qscientificpropertycustomization',
            name='display_extra_units',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='qscientificpropertycustomization',
            name='edit_extra_description',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='qscientificpropertycustomization',
            name='edit_extra_standard_name',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='qscientificpropertycustomization',
            name='edit_extra_units',
            field=models.BooleanField(default=False),
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
            model_name='qmodelcustomization',
            name='vocabularies',
            field=models.ManyToManyField(related_name='model_customizer', to='questionnaire.QVocabulary', through='questionnaire.QModelCustomizationVocabulary', blank=True, help_text='<p>These are the CVs that are associated with this document type and project.</p><p>Clicking on <strong>&quot;active&quot;</strong> will enable or disable all of the properties contained within a CV.</p><p>Dragging-and-dropping a CV will change the order in which it appears in the Editor.</p>', verbose_name=b'Vocabularies to include'),
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
            model_name='qscientificcategorycustomization',
            name='name',
            field=models.CharField(help_text=b"Be wary of changing a category's name; doing so deviates from a known controlled vocabulary and could confuse users.", max_length=256),
        ),
        migrations.AlterField(
            model_name='qscientificcategoryproxy',
            name='key',
            field=models.CharField(blank=True, max_length=256, validators=[Q.questionnaire.q_utils.ValidateNoSpaces()]),
        ),
        migrations.AlterField(
            model_name='qstandardcategorycustomization',
            name='name',
            field=models.CharField(help_text=b"Be wary of changing a category's name; doing so deviates from a known controlled vocabulary and could confuse users.", max_length=256),
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
