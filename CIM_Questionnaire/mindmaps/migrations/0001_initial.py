# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MindMapSource'
        db.create_table(u'mindmaps_mindmapsource', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'mindmaps', ['MindMapSource'])

        # Adding model 'MindMapDomain'
        db.create_table(u'mindmaps_mindmapdomain', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('domain', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(related_name='domains', to=orm['mindmaps.MindMapSource'])),
        ))
        db.send_create_signal(u'mindmaps', ['MindMapDomain'])


    def backwards(self, orm):
        # Deleting model 'MindMapSource'
        db.delete_table(u'mindmaps_mindmapsource')

        # Deleting model 'MindMapDomain'
        db.delete_table(u'mindmaps_mindmapdomain')


    models = {
        u'mindmaps.mindmapdomain': {
            'Meta': {'object_name': 'MindMapDomain'},
            'domain': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'domains'", 'to': u"orm['mindmaps.MindMapSource']"})
        },
        u'mindmaps.mindmapsource': {
            'Meta': {'object_name': 'MindMapSource'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        }
    }

    complete_apps = ['mindmaps']