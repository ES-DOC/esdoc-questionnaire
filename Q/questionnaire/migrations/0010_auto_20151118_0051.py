# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mptt.fields
import Q.questionnaire.q_utils
import Q.questionnaire.q_fields_bak


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0009_auto_20151118_0041'),
    ]

    operations = [
        migrations.CreateModel(
            name='MetadataModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(null=True, editable=False, blank=True)),
                ('guid', models.CharField(max_length=128, unique=True, null=True, editable=False, blank=True)),
                ('document_version', models.CharField(default=b'0.0', max_length=128)),
                ('is_document', models.BooleanField(default=False)),
                ('is_root', models.BooleanField(default=False)),
                ('is_published', models.BooleanField(default=False)),
                ('vocabulary_key', models.CharField(max_length=512, null=True, blank=True)),
                ('component_key', models.CharField(max_length=512, null=True, blank=True)),
                ('title', models.CharField(max_length=512, null=True, blank=True)),
                ('active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=1024, null=True, blank=True)),
                ('order', models.PositiveIntegerField(null=True, blank=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', blank=True, to='questionnaire.MetadataModel', null=True)),
            ],
            options={
                'abstract': False,
                'verbose_name': '(DISABLE ADMIN ACCESS SOON) Metadata Model',
                'verbose_name_plural': '(DISABLE ADMIN ACCESS SOON) Metadata Models',
            },
        ),
        migrations.CreateModel(
            name='MetadataScientificProperty',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('order', models.PositiveIntegerField(null=True, blank=True)),
                ('field_type', models.CharField(blank=True, max_length=64, choices=[(b'ATOMIC', b'Atomic'), (b'RELATIONSHIP', b'Relationship'), (b'ENUMERATION', b'Enumeration'), (b'PROPERTY', b'Property')])),
                ('is_label', models.BooleanField(default=False)),
                ('is_enumeration', models.BooleanField(default=False)),
                ('category_key', models.CharField(max_length=512, null=True, blank=True)),
                ('atomic_value', models.CharField(max_length=1024, null=True, blank=True)),
                ('enumeration_value', Q.questionnaire.q_fields_bak.EnumerationField(null=True, blank=True)),
                ('enumeration_other_value', models.CharField(max_length=1024, null=True, blank=True)),
                ('extra_standard_name', models.CharField(max_length=512, null=True, blank=True)),
                ('extra_description', models.TextField(null=True, blank=True)),
                ('extra_units', models.CharField(max_length=512, null=True, blank=True)),
                ('model', models.ForeignKey(related_name='scientific_properties', to='questionnaire.MetadataModel', null=True)),
                ('proxy', models.ForeignKey(blank=True, to='questionnaire.QScientificPropertyProxy', null=True)),
            ],
            options={
                'ordering': ['order'],
                'abstract': False,
                'verbose_name': '(DISABLE ADMIN ACCESS SOON) Metadata Scientific Property',
                'verbose_name_plural': '(DISABLE ADMIN ACCESS SOON) Metadata Scientific Properties',
            },
        ),
        migrations.CreateModel(
            name='MetadataStandardProperty',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('order', models.PositiveIntegerField(null=True, blank=True)),
                ('field_type', models.CharField(blank=True, max_length=64, choices=[(b'ATOMIC', b'Atomic'), (b'RELATIONSHIP', b'Relationship'), (b'ENUMERATION', b'Enumeration'), (b'PROPERTY', b'Property')])),
                ('is_label', models.BooleanField(default=False)),
                ('atomic_value', models.CharField(max_length=1024, null=True, blank=True)),
                ('enumeration_value', Q.questionnaire.q_fields_bak.EnumerationField(null=True, blank=True)),
                ('enumeration_other_value', models.CharField(max_length=1024, null=True, blank=True)),
                ('relationship_reference', Q.questionnaire.q_fields_bak.ListField(null=True, blank=True)),
                ('model', models.ForeignKey(related_name='standard_properties', to='questionnaire.MetadataModel', null=True)),
                ('proxy', models.ForeignKey(blank=True, to='questionnaire.QStandardPropertyProxy', null=True)),
                ('relationship_value', models.ManyToManyField(to='questionnaire.MetadataModel', null=True, blank=True)),
            ],
            options={
                'ordering': ['order'],
                'abstract': False,
                'verbose_name': '(DISABLE ADMIN ACCESS SOON) Metadata Standard Property',
                'verbose_name_plural': '(DISABLE ADMIN ACCESS SOON) Metadata Standard Properties',
            },
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
            model_name='qtestmodel',
            name='name',
            field=models.CharField(unique=True, max_length=128, validators=[Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoBadChars(), Q.questionnaire.q_utils.ValidateNoReservedWords()]),
        ),
        migrations.AlterField(
            model_name='qvocabulary',
            name='name',
            field=models.CharField(max_length=128, validators=[Q.questionnaire.q_utils.ValidateNoSpaces(), Q.questionnaire.q_utils.ValidateNoBadChars()]),
        ),
        migrations.AddField(
            model_name='metadatamodel',
            name='project',
            field=models.ForeignKey(related_name='models_bak', blank=True, to='questionnaire.QProject', null=True),
        ),
        migrations.AddField(
            model_name='metadatamodel',
            name='proxy',
            field=models.ForeignKey(related_name='models_bak', to='questionnaire.QModelProxy', null=True),
        ),
        migrations.AddField(
            model_name='metadatamodel',
            name='version',
            field=models.ForeignKey(related_name='models_bak', to='questionnaire.QOntology', null=True),
        ),
    ]
