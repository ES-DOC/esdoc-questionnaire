# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'MetadataModelCustomizer.model_root_component'
        db.add_column('dcf_metadatamodelcustomizer', 'model_root_component', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True), keep_default=False)

        # Adding M2M table for field vocabularies on 'MetadataModelCustomizer'
        db.create_table('dcf_metadatamodelcustomizer_vocabularies', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('metadatamodelcustomizer', models.ForeignKey(orm['dcf.metadatamodelcustomizer'], null=False)),
            ('metadatavocabulary', models.ForeignKey(orm['dcf.metadatavocabulary'], null=False))
        ))
        db.create_unique('dcf_metadatamodelcustomizer_vocabularies', ['metadatamodelcustomizer_id', 'metadatavocabulary_id'])


    def backwards(self, orm):
        
        # Deleting field 'MetadataModelCustomizer.model_root_component'
        db.delete_column('dcf_metadatamodelcustomizer', 'model_root_component')

        # Removing M2M table for field vocabularies on 'MetadataModelCustomizer'
        db.delete_table('dcf_metadatamodelcustomizer_vocabularies')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'dcf.metadatacategorization': {
            'Meta': {'object_name': 'MetadataCategorization'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'categorizations'", 'blank': 'True', 'to': "orm['dcf.MetadataVersion']"})
        },
        'dcf.metadatamodelcustomizer': {
            'Meta': {'unique_together': "(('project', 'version', 'model', 'name'),)", 'object_name': 'MetadataModelCustomizer'},
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'deecfa7e-886d-4aa8-8bdf-e11bb1811429'", 'unique': 'True', 'max_length': '64'}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'model_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'model_nested': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'model_root_component': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'model_show_all_categories': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'model_show_all_properties': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'model_title': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataProject']"}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataVersion']"}),
            'vocabularies': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['dcf.MetadataVocabulary']", 'null': 'True', 'blank': 'True'})
        },
        'dcf.metadatamodelproxy': {
            'Meta': {'object_name': 'MetadataModelProxy'},
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'1062e58e-6530-49bf-918c-90428f9b0554'", 'unique': 'True', 'max_length': '64'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'model_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'model_title': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataVersion']"})
        },
        'dcf.metadataproject': {
            'Meta': {'object_name': 'MetadataProject'},
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'87c7707d-ef93-4f70-bef9-d514d8aae0b4'", 'unique': 'True', 'max_length': '64'}),
            'default_version': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'project'", 'null': 'True', 'to': "orm['dcf.MetadataVersion']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'restriction_customize': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'restriction_edit': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '400'})
        },
        'dcf.metadataproperty': {
            'Meta': {'object_name': 'MetadataProperty'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataScientificCategory']", 'null': 'True', 'blank': 'True'}),
            'choice': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'component_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'customizer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataScientificPropertyCustomizer']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_name': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'model_content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'model_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'property_enumeration': ('dcf.fields.MetadataEnumerationField', [], {'max_length': '1200', 'null': 'True', 'blank': 'True'}),
            'property_freetext': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'standard_name': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'})
        },
        'dcf.metadatascientificcategory': {
            'Meta': {'unique_together': "(('vocabulary', 'component_name', 'name'),)", 'object_name': 'MetadataScientificCategory'},
            'component_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'categories'", 'null': 'True', 'to': "orm['dcf.MetadataProject']"}),
            'remove': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'vocabulary': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'categories'", 'null': 'True', 'to': "orm['dcf.MetadataVocabulary']"})
        },
        'dcf.metadatascientificpropertycustomizer': {
            'Meta': {'object_name': 'MetadataScientificPropertyCustomizer'},
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'3b40f141-73ee-4d1b-9f75-0a59a48137de'", 'unique': 'True', 'max_length': '64'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataScientificCategory']", 'null': 'True', 'blank': 'True'}),
            'choice': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'component_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'default_value': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'displayed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'documentation': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'edit_extra_attributes': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'editable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'multi': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'nullable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'open': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'scientific_property_customizers'", 'null': 'True', 'to': "orm['dcf.MetadataModelCustomizer']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataProject']"}),
            'proxy': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'customizer'", 'blank': 'True', 'to': "orm['dcf.MetadataScientificPropertyProxy']"}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'show_extra_attributes': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'standard_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'suggestions': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'unique': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'value': ('dcf.fields.EnumerationField', [], {'null': 'True', 'blank': 'True'}),
            'value_choices': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'value_default': ('dcf.fields.EnumerationField', [], {'null': 'True', 'blank': 'True'}),
            'value_format': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'value_units': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'verbose_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataVersion']"}),
            'vocabulary': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataVocabulary']", 'null': 'True', 'blank': 'True'})
        },
        'dcf.metadatascientificpropertyproxy': {
            'Meta': {'unique_together': "(('model_name', 'component_name', 'name', 'category'),)", 'object_name': 'MetadataScientificPropertyProxy'},
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'4a2a3a1c-1068-4608-b664-0c4f93787efe'", 'unique': 'True', 'max_length': '64'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataScientificCategory']", 'null': 'True', 'blank': 'True'}),
            'choice': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'component_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'default_value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'documentation': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'editable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'model_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'standard_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'unique': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'verbose_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'vocabulary': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataVocabulary']", 'null': 'True', 'blank': 'True'})
        },
        'dcf.metadatascientificpropertyproxyvalue': {
            'Meta': {'object_name': 'MetadataScientificPropertyProxyValue'},
            'format': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'property': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'values'", 'to': "orm['dcf.MetadataScientificPropertyProxy']"}),
            'units': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'dcf.metadatastandardcategory': {
            'Meta': {'unique_together': "(('categorization', 'name'),)", 'object_name': 'MetadataStandardCategory'},
            'categorization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'categories'", 'to': "orm['dcf.MetadataCategorization']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'remove': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'dcf.metadatastandardpropertycustomizer': {
            'Meta': {'object_name': 'MetadataStandardPropertyCustomizer'},
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'fc23e8ac-fb33-4e53-81d6-59c44c8b9c77'", 'unique': 'True', 'max_length': '64'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataStandardCategory']", 'null': 'True', 'blank': 'True'}),
            'customize_subform': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'default_value': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'displayed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'documentation': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'editable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enumeration_choices': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'enumeration_default': ('dcf.fields.EnumerationField', [], {'null': 'True', 'blank': 'True'}),
            'enumeration_multi': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enumeration_nullable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enumeration_open': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enumeration_values': ('dcf.fields.EnumerationField', [], {'null': 'True', 'blank': 'True'}),
            'field_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'standard_property_customizers'", 'null': 'True', 'to': "orm['dcf.MetadataModelCustomizer']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataProject']"}),
            'proxy': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'customizer'", 'blank': 'True', 'to': "orm['dcf.MetadataStandardPropertyProxy']"}),
            'relationship_cardinality': ('dcf.fields.CardinalityField', [], {'max_length': '8', 'blank': 'True'}),
            'relationship_source_model': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'relationship_target_model': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'subform_customizer': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'property_customizer'", 'null': 'True', 'to': "orm['dcf.MetadataModelCustomizer']"}),
            'suggestions': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'unique': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'verbose_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataVersion']"})
        },
        'dcf.metadatastandardpropertyproxy': {
            'Meta': {'unique_together': "(('version', 'model_name', 'name'),)", 'object_name': 'MetadataStandardPropertyProxy'},
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'935a4399-d1c4-4c60-a5cf-9213aba5a4c3'", 'unique': 'True', 'max_length': '64'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataStandardCategory']", 'null': 'True', 'blank': 'True'}),
            'default_value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'documentation': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'editable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enumeration_choices': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'enumeration_multi': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enumeration_nullable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enumeration_open': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'field_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'relationship_source_model': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'relationship_target_model': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'unique': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'verbose_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataVersion']"})
        },
        'dcf.metadataversion': {
            'Meta': {'object_name': 'MetadataVersion'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'models': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'dcf.metadatavocabulary': {
            'Meta': {'object_name': 'MetadataVocabulary'},
            'component_list': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'component_tree': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'vocabularies'", 'null': 'True', 'to': "orm['dcf.MetadataProject']"})
        }
    }

    complete_apps = ['dcf']
