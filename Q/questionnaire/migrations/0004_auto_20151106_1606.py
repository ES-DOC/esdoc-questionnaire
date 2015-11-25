# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import Q.questionnaire.q_utils


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0003_auto_20151104_1601'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='snippet',
            name='owner',
        ),
        migrations.DeleteModel(
            name='Task',
        ),
        migrations.AlterModelOptions(
            name='qcomponentproxy',
            options={'ordering': ('order',), 'verbose_name': 'Questionnaire Component Proxy', 'verbose_name_plural': '_Questionnaire Proxies: Components'},
        ),
        migrations.AlterModelOptions(
            name='qmodel',
            options={'ordering': ('created',), 'verbose_name': 'Questionnaire Model Realization', 'verbose_name_plural': '_Questionnaire Realizations: Models'},
        ),
        migrations.AlterModelOptions(
            name='qmodelcustomization',
            options={'verbose_name': 'Questionnaire Model Customization', 'verbose_name_plural': '_Questionnaire Customizations: Models'},
        ),
        migrations.AlterModelOptions(
            name='qmodelcustomizationvocabulary',
            options={'ordering': ['order'], 'verbose_name': 'Questionnaire Vocabulary Customization', 'verbose_name_plural': '_Questionnaire Customizations: Vocabularies'},
        ),
        migrations.AlterModelOptions(
            name='qmodelproxy',
            options={'ordering': ('order',), 'verbose_name': 'Questionnaire Model Proxy', 'verbose_name_plural': '_Questionnaire Proxies: Models'},
        ),
        migrations.AlterModelOptions(
            name='qscientificcategorycustomization',
            options={'verbose_name': 'Questionnaire Scientific Category Customization', 'verbose_name_plural': '_Questionnaire Customizations: Scientific Categories'},
        ),
        migrations.AlterModelOptions(
            name='qscientificcategoryproxy',
            options={'ordering': ('order',), 'verbose_name': 'Questionnaire Scientific Category Proxy', 'verbose_name_plural': '_Questionnaire Proxies: Scientific Categories'},
        ),
        migrations.AlterModelOptions(
            name='qscientificproperty',
            options={'verbose_name': 'Questionnaire Scientific Property Realization', 'verbose_name_plural': '_Questionnaire Realizations: Scientific Properties'},
        ),
        migrations.AlterModelOptions(
            name='qscientificpropertycustomization',
            options={'ordering': ['order'], 'verbose_name': 'Questionnaire Scientific Property Customization', 'verbose_name_plural': '_Questionnaire Customizations: Scientific Properties'},
        ),
        migrations.AlterModelOptions(
            name='qscientificpropertyproxy',
            options={'ordering': ('order',), 'verbose_name': 'Questionnaire Scientific Property Proxies', 'verbose_name_plural': '_Questionnaire Proxies: Scientific Properties'},
        ),
        migrations.AlterModelOptions(
            name='qstandardcategorycustomization',
            options={'verbose_name': 'Questionnaire Standard Category Customization', 'verbose_name_plural': '_Questionnaire Customizations: Standard Categories'},
        ),
        migrations.AlterModelOptions(
            name='qstandardcategoryproxy',
            options={'ordering': ('order',), 'verbose_name': 'Questionnaire Standard Category Proxy', 'verbose_name_plural': '_Questionnaire Proxies: Standard Categories'},
        ),
        migrations.AlterModelOptions(
            name='qstandardproperty',
            options={'verbose_name': 'Questionnaire Standard Property Realization', 'verbose_name_plural': '_Questionnaire Realizations: Standard Properties'},
        ),
        migrations.AlterModelOptions(
            name='qstandardpropertycustomization',
            options={'ordering': ['order'], 'verbose_name': 'Questionnaire Standard Property Customization', 'verbose_name_plural': '_Questionnaire Customizations: Standard Properties'},
        ),
        migrations.AlterModelOptions(
            name='qstandardpropertyproxy',
            options={'ordering': ('order',), 'verbose_name': 'Questionnaire Standard Property Proxy', 'verbose_name_plural': '_Questionnaire Proxies: Standard Properties'},
        ),
        migrations.AlterModelOptions(
            name='qsynchronization',
            options={'verbose_name': 'Questionnaire (Un)Synchronization Type', 'verbose_name_plural': 'Questionnaire (Un)Synchronization Types'},
        ),
        migrations.RenameField(
            model_name='qstandardpropertycustomization',
            old_name='relationship_subform_customizer',
            new_name='relationship_subform_customization',
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
            model_name='qstandardpropertycustomization',
            name='relationship_show_subform',
            field=models.BooleanField(default=False, help_text=b'Checking this will cause the property to be rendered as a nested subform within the parent form; All properties of this model will be available to view and edit in that subform.                                          Unchecking it will cause the attribute to be rendered as a simple <em>reference</em> widget.', verbose_name="Should this property be rendered in its own subform?<div class='documentation'>Note that a relationship to another CIM Document cannot use subforms.</div>"),
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
        migrations.DeleteModel(
            name='Snippet',
        ),
    ]
