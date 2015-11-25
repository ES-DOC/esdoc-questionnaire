# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MindMapDomain',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('domain', models.URLField()),
            ],
            options={
                'verbose_name': 'MindMap Domain',
                'verbose_name_plural': 'MindMap Domains',
            },
        ),
        migrations.CreateModel(
            name='MindMapSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=64)),
                ('enabled', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'MindMap Source',
                'verbose_name_plural': 'MindMap Sources',
            },
        ),
        migrations.AddField(
            model_name='mindmapdomain',
            name='source',
            field=models.ForeignKey(related_name='domains', to='mindmaps.MindMapSource'),
        ),
    ]
