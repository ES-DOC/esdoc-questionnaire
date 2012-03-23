# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ModelComponent'
        db.create_table('django_cim_forms_modelcomponent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('guid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64, blank=True)),
            ('documentID', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('shortName', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('longName', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('license', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=25, blank=True)),
            ('releaseDate', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('django_cim_forms', ['ModelComponent'])


    def backwards(self, orm):
        
        # Deleting model 'ModelComponent'
        db.delete_table('django_cim_forms_modelcomponent')


    models = {
        'django_cim_forms.modelcomponent': {
            'Meta': {'object_name': 'ModelComponent'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'documentID': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'guid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'longName': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'releaseDate': ('django.db.models.fields.DateField', [], {}),
            'shortName': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'})
        }
    }

    complete_apps = ['django_cim_forms']
