# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import Q.questionnaire.q_utils


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0008_auto_20160809_1358'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='qpropertycustomization',
            options={'ordering': ('order',), 'verbose_name': '_Questionnaire Property Customization', 'verbose_name_plural': '_Questionnaire Property Customization'},
        ),
        migrations.AlterField(
            model_name='qcategorycustomization',
            name='category_title',
            field=models.CharField(max_length=64, validators=[Q.questionnaire.q_utils.ValidateNoProfanities()]),
        ),
        migrations.AlterField(
            model_name='qcategorycustomization',
            name='name',
            field=models.CharField(help_text=b'A unique name for this customization.  Spaces or the following characters are not allowed: "\\, /, <, >, %, #, %, {, }, [, ], $, |".', max_length=128, verbose_name=b'Customization Name', validators=[Q.questionnaire.q_utils.ValidateNoBadChars(), Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoReservedWords(), Q.questionnaire.q_utils.ValidateNoProfanities()]),
        ),
        migrations.AlterField(
            model_name='qmodelcustomization',
            name='name',
            field=models.CharField(help_text=b'A unique name for this customization.  Spaces or the following characters are not allowed: "\\, /, <, >, %, #, %, {, }, [, ], $, |".', max_length=128, verbose_name=b'Customization Name', validators=[Q.questionnaire.q_utils.ValidateNoBadChars(), Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoReservedWords(), Q.questionnaire.q_utils.ValidateNoProfanities()]),
        ),
        migrations.AlterField(
            model_name='qmodelthing',
            name='name',
            field=models.CharField(max_length=128, verbose_name=b'Customization Name', validators=[Q.questionnaire.q_utils.ValidateNoBadChars(), Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoReservedWords(), Q.questionnaire.q_utils.ValidateNoProfanities()]),
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
            model_name='qpropertycustomization',
            name='atomic_suggestions',
            field=models.TextField(blank=True, help_text=b'Please enter a "|" separated list of words or phrases.  (These suggestions will only take effect for text fields.)', null=True, verbose_name=b'Are there any suggestions you would like to offer as auto-completion options?', validators=[Q.questionnaire.q_utils.ValidateNoBadSuggestionChars()]),
        ),
        migrations.AlterField(
            model_name='qpropertycustomization',
            name='atomic_type',
            field=models.CharField(default=b'DEFAULT', help_text=b'By default, all fields are rendered as strings.  However, a field can be customized to accept longer snippets of text, dates, email addresses, etc.', max_length=512, verbose_name=b'How should this field be rendered?', choices=[(b'DEFAULT', b'Character Field (default)'), (b'BOOLEAN', b'Boolean Field'), (b'DATE', b'Date Field'), (b'DATETIME', b'Date Time Field'), (b'DECIMAL', b'Decimal Field'), (b'EMAIL', b'Email Field'), (b'INTEGER', b'Integer Field'), (b'TEXT', b'Text Field (large block of text as opposed to a small string)'), (b'TIME', b'Time Field'), (b'URL', b'URL Field')]),
        ),
        migrations.AlterField(
            model_name='qpropertycustomization',
            name='name',
            field=models.CharField(help_text=b'A unique name for this customization.  Spaces or the following characters are not allowed: "\\, /, <, >, %, #, %, {, }, [, ], $, |".', max_length=128, verbose_name=b'Customization Name', validators=[Q.questionnaire.q_utils.ValidateNoBadChars(), Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoReservedWords(), Q.questionnaire.q_utils.ValidateNoProfanities()]),
        ),
        migrations.AlterField(
            model_name='qpropertycustomization',
            name='property_title',
            field=models.CharField(max_length=128, validators=[Q.questionnaire.q_utils.ValidateNoProfanities()]),
        ),
        migrations.AlterField(
            model_name='qpropertyproxy',
            name='atomic_type',
            field=models.CharField(default=b'DEFAULT', max_length=256, choices=[(b'DEFAULT', b'Character Field (default)'), (b'BOOLEAN', b'Boolean Field'), (b'DATE', b'Date Field'), (b'DATETIME', b'Date Time Field'), (b'DECIMAL', b'Decimal Field'), (b'EMAIL', b'Email Field'), (b'INTEGER', b'Integer Field'), (b'TEXT', b'Text Field (large block of text as opposed to a small string)'), (b'TIME', b'Time Field'), (b'URL', b'URL Field')]),
        ),
        migrations.AlterField(
            model_name='qpropertything',
            name='name',
            field=models.CharField(max_length=128, verbose_name=b'Customization Name', validators=[Q.questionnaire.q_utils.ValidateNoBadChars(), Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoReservedWords(), Q.questionnaire.q_utils.ValidateNoProfanities()]),
        ),
        migrations.AlterField(
            model_name='qpropertything',
            name='property_title',
            field=models.CharField(max_length=128, validators=[Q.questionnaire.q_utils.ValidateNoProfanities()]),
        ),
    ]
