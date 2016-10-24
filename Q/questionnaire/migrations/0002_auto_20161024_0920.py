# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import Q.questionnaire.q_utils


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='qmodelthing',
            name='ontology',
        ),
        migrations.RemoveField(
            model_name='qmodelthing',
            name='project',
        ),
        migrations.RemoveField(
            model_name='qmodelthing',
            name='proxy',
        ),
        migrations.RemoveField(
            model_name='qmodelthing',
            name='relationship_source_property_customization',
        ),
        migrations.RemoveField(
            model_name='qpropertything',
            name='model_customization',
        ),
        migrations.RemoveField(
            model_name='qpropertything',
            name='proxy',
        ),
        migrations.AddField(
            model_name='qproject',
            name='is_legacy',
            field=models.BooleanField(default=False, help_text=b"A legacy project is one that still uses CIM1 and requests must therefore be routed through the legacy site.  Do not check this unless you really know what you're doing."),
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
            model_name='qontology',
            name='name',
            field=models.CharField(max_length=128, validators=[Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoBadChars()]),
        ),
        migrations.AlterField(
            model_name='qproject',
            name='is_active',
            field=models.BooleanField(default=True, help_text=b'A project that is not active cannot be used'),
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
            name='name',
            field=models.CharField(help_text=b'A unique name for this customization.  Spaces or the following characters are not allowed: "\\, /, <, >, %, #, %, {, }, [, ], $, |".', max_length=128, verbose_name=b'Customization Name', validators=[Q.questionnaire.q_utils.ValidateNoBadChars(), Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoReservedWords(), Q.questionnaire.q_utils.ValidateNoProfanities()]),
        ),
        migrations.AlterField(
            model_name='qpropertycustomization',
            name='property_title',
            field=models.CharField(max_length=128, validators=[Q.questionnaire.q_utils.ValidateNoProfanities()]),
        ),
        migrations.DeleteModel(
            name='QModelThing',
        ),
        migrations.DeleteModel(
            name='QPropertyThing',
        ),
    ]
