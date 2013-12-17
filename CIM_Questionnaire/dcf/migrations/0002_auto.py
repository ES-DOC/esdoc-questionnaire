# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding M2M table for field projects on 'MetadataVocabulary'
        m2m_table_name = db.shorten_name(u'dcf_metadatavocabulary_projects')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('metadatavocabulary', models.ForeignKey(orm['dcf.metadatavocabulary'], null=False)),
            ('metadataproject', models.ForeignKey(orm['dcf.metadataproject'], null=False))
        ))
        db.create_unique(m2m_table_name, ['metadatavocabulary_id', 'metadataproject_id'])


    def backwards(self, orm):
        # Removing M2M table for field projects on 'MetadataVocabulary'
        db.delete_table(db.shorten_name(u'dcf_metadatavocabulary_projects'))


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'dcf.metadatacategorization': {
            'Meta': {'object_name': 'MetadataCategorization'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'categorizations'", 'blank': 'True', 'to': "orm['dcf.MetadataVersion']"})
        },
        'dcf.metadatamodelcustomizer': {
            'Meta': {'unique_together': "(('project', 'version', 'model', 'name'),)", 'object_name': 'MetadataModelCustomizer'},
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'56749119-aa32-4f4c-8493-8fe041321aad'", 'unique': 'True', 'max_length': '64'}),
            'default': ('django.db.models.fields.BooleanField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'0b59e106-2a4d-41c7-b268-c5fc538ab894'", 'unique': 'True', 'max_length': '64'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'model_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'model_title': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataVersion']"})
        },
        'dcf.metadataproject': {
            'Meta': {'object_name': 'MetadataProject'},
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'478be9cf-9128-4280-92c3-d878cc5208df'", 'unique': 'True', 'max_length': '64'}),
            'default_version': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'project'", 'null': 'True', 'to': "orm['dcf.MetadataVersion']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'restriction_customize': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'restriction_edit': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '400'})
        },
        'dcf.metadataproperty': {
            'Meta': {'object_name': 'MetadataProperty'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataScientificCategory']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'choice': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'component_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'customizer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataScientificPropertyCustomizer']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_name': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'model_content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
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
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'categories'", 'null': 'True', 'to': "orm['dcf.MetadataProject']"}),
            'remove': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'vocabulary': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'categories'", 'null': 'True', 'to': "orm['dcf.MetadataVocabulary']"})
        },
        'dcf.metadatascientificpropertycustomizer': {
            'Meta': {'ordering': "['order']", 'object_name': 'MetadataScientificPropertyCustomizer'},
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'5b9579ca-519f-42fd-a67f-af4cb5350eca'", 'unique': 'True', 'max_length': '64'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataScientificCategory']", 'null': 'True', 'blank': 'True'}),
            'choice': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'component_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'default_value': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'displayed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'documentation': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'edit_extra_attributes': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'editable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'5794314d-da77-4f81-ba8d-fd8b34af8394'", 'unique': 'True', 'max_length': '64'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataScientificCategory']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'choice': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'component_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'default_value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'documentation': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'editable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'property': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'values'", 'to': "orm['dcf.MetadataScientificPropertyProxy']"}),
            'units': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'dcf.metadatastandardcategory': {
            'Meta': {'unique_together': "(('categorization', 'name'),)", 'object_name': 'MetadataStandardCategory'},
            'categorization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'categories'", 'to': "orm['dcf.MetadataCategorization']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'remove': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'dcf.metadatastandardpropertycustomizer': {
            'Meta': {'ordering': "['order']", 'object_name': 'MetadataStandardPropertyCustomizer'},
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'eb3313b9-94b5-4acd-b029-b57899d80d71'", 'unique': 'True', 'max_length': '64'}),
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
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'3217455b-9515-4b16-9435-80ec8011558a'", 'unique': 'True', 'max_length': '64'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataStandardCategory']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'default_value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'documentation': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'editable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enumeration_choices': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'enumeration_multi': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enumeration_nullable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enumeration_open': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'field_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'vocabularies'", 'null': 'True', 'to': "orm['dcf.MetadataProject']"}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'vocabularies_new'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['dcf.MetadataProject']"})
        }
    }

    complete_apps = ['dcf']