# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MetadataProperty'
        db.create_table(u'dcf_metadataproperty', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dcf.MetadataScientificCategory'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('customizer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dcf.MetadataScientificPropertyCustomizer'], null=True, blank=True)),
            ('component_name', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('property_enumeration', self.gf('dcf.fields.MetadataEnumerationField')(max_length=1200, null=True, blank=True)),
            ('property_freetext', self.gf('django.db.models.fields.CharField')(max_length=400, blank=True)),
            ('choice', self.gf('django.db.models.fields.CharField')(max_length=400, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=400, blank=True)),
            ('long_name', self.gf('django.db.models.fields.CharField')(max_length=400, blank=True)),
            ('standard_name', self.gf('django.db.models.fields.CharField')(max_length=400, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('model_content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('model_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('dcf', ['MetadataProperty'])

        # Adding model 'MetadataModelProxy'
        db.create_table(u'dcf_metadatamodelproxy', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_guid', self.gf('django.db.models.fields.CharField')(default='913bcf12-f1b6-4b39-a986-b1a23ed11a70', unique=True, max_length=64)),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dcf.MetadataVersion'])),
            ('model_name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('document_type', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('model_title', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('model_description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('dcf', ['MetadataModelProxy'])

        # Adding model 'MetadataStandardPropertyProxy'
        db.create_table(u'dcf_metadatastandardpropertyproxy', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_guid', self.gf('django.db.models.fields.CharField')(default='2391472f-b065-4335-b28c-60c9e7346153', unique=True, max_length=64)),
            ('model_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('required', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('editable', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('unique', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('verbose_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('documentation', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('default_value', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dcf.MetadataVersion'])),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dcf.MetadataStandardCategory'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('field_type', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('enumeration_choices', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('enumeration_open', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('enumeration_multi', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('enumeration_nullable', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('relationship_target_model', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('relationship_source_model', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
        ))
        db.send_create_signal('dcf', ['MetadataStandardPropertyProxy'])

        # Adding unique constraint on 'MetadataStandardPropertyProxy', fields ['version', 'model_name', 'name']
        db.create_unique(u'dcf_metadatastandardpropertyproxy', ['version_id', 'model_name', 'name'])

        # Adding model 'MetadataScientificPropertyProxy'
        db.create_table(u'dcf_metadatascientificpropertyproxy', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_guid', self.gf('django.db.models.fields.CharField')(default='29ecb442-c729-4318-a62c-cb826e8e1078', unique=True, max_length=64)),
            ('model_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('required', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('editable', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('unique', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('verbose_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('documentation', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('default_value', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('vocabulary', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dcf.MetadataVocabulary'], null=True, blank=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dcf.MetadataScientificCategory'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('component_name', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('choice', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('standard_name', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('long_name', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(max_length=64, null=True, blank=True)),
        ))
        db.send_create_signal('dcf', ['MetadataScientificPropertyProxy'])

        # Adding unique constraint on 'MetadataScientificPropertyProxy', fields ['model_name', 'component_name', 'name', 'category']
        db.create_unique(u'dcf_metadatascientificpropertyproxy', ['model_name', 'component_name', 'name', 'category_id'])

        # Adding model 'MetadataScientificPropertyProxyValue'
        db.create_table(u'dcf_metadatascientificpropertyproxyvalue', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('property', self.gf('django.db.models.fields.related.ForeignKey')(related_name='values', to=orm['dcf.MetadataScientificPropertyProxy'])),
            ('format', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('units', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=400, null=True, blank=True)),
        ))
        db.send_create_signal('dcf', ['MetadataScientificPropertyProxyValue'])

        # Adding model 'MetadataModelCustomizer'
        db.create_table(u'dcf_metadatamodelcustomizer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_guid', self.gf('django.db.models.fields.CharField')(default='4d514250-a645-4153-9360-0cdde3dc915a', unique=True, max_length=64)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dcf.MetadataProject'])),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dcf.MetadataVersion'])),
            ('model', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('default', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('model_title', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('model_description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('model_show_all_categories', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('model_show_all_properties', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('model_nested', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('model_root_component', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('dcf', ['MetadataModelCustomizer'])

        # Adding unique constraint on 'MetadataModelCustomizer', fields ['project', 'version', 'model', 'name']
        db.create_unique(u'dcf_metadatamodelcustomizer', ['project_id', 'version_id', 'model', 'name'])

        # Adding M2M table for field vocabularies on 'MetadataModelCustomizer'
        m2m_table_name = db.shorten_name(u'dcf_metadatamodelcustomizer_vocabularies')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('metadatamodelcustomizer', models.ForeignKey(orm['dcf.metadatamodelcustomizer'], null=False)),
            ('metadatavocabulary', models.ForeignKey(orm['dcf.metadatavocabulary'], null=False))
        ))
        db.create_unique(m2m_table_name, ['metadatamodelcustomizer_id', 'metadatavocabulary_id'])

        # Adding model 'MetadataStandardPropertyCustomizer'
        db.create_table(u'dcf_metadatastandardpropertycustomizer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_guid', self.gf('django.db.models.fields.CharField')(default='6dece7c8-967b-4dc4-8aba-eb5133fc3176', unique=True, max_length=64)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dcf.MetadataProject'])),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dcf.MetadataVersion'])),
            ('model', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('displayed', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('required', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('editable', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('unique', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('verbose_name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('default_value', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('documentation', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('suggestions', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='standard_property_customizers', null=True, to=orm['dcf.MetadataModelCustomizer'])),
            ('proxy', self.gf('django.db.models.fields.related.ForeignKey')(related_name='customizer', blank=True, to=orm['dcf.MetadataStandardPropertyProxy'])),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dcf.MetadataStandardCategory'], null=True, blank=True)),
            ('field_type', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('enumeration_values', self.gf('dcf.fields.EnumerationField')(null=True, blank=True)),
            ('enumeration_default', self.gf('dcf.fields.EnumerationField')(null=True, blank=True)),
            ('enumeration_choices', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('enumeration_open', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('enumeration_multi', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('enumeration_nullable', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('relationship_target_model', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('relationship_source_model', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('relationship_cardinality', self.gf('dcf.fields.CardinalityField')(max_length=8, blank=True)),
            ('customize_subform', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('subform_customizer', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='property_customizer', null=True, to=orm['dcf.MetadataModelCustomizer'])),
        ))
        db.send_create_signal('dcf', ['MetadataStandardPropertyCustomizer'])

        # Adding model 'MetadataScientificPropertyCustomizer'
        db.create_table(u'dcf_metadatascientificpropertycustomizer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_guid', self.gf('django.db.models.fields.CharField')(default='652e93d6-e154-414a-a7d7-df28faee8e1f', unique=True, max_length=64)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dcf.MetadataProject'])),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dcf.MetadataVersion'])),
            ('model', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('displayed', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('required', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('editable', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('unique', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('verbose_name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('default_value', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('documentation', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('suggestions', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='scientific_property_customizers', null=True, to=orm['dcf.MetadataModelCustomizer'])),
            ('proxy', self.gf('django.db.models.fields.related.ForeignKey')(related_name='customizer', blank=True, to=orm['dcf.MetadataScientificPropertyProxy'])),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dcf.MetadataScientificCategory'], null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('component_name', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('vocabulary', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dcf.MetadataVocabulary'], null=True, blank=True)),
            ('choice', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('open', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('multi', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('nullable', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('show_extra_attributes', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('edit_extra_attributes', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('standard_name', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('long_name', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(max_length=64, null=True, blank=True)),
            ('value', self.gf('dcf.fields.EnumerationField')(null=True, blank=True)),
            ('value_default', self.gf('dcf.fields.EnumerationField')(null=True, blank=True)),
            ('value_choices', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('value_format', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('value_units', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal('dcf', ['MetadataScientificPropertyCustomizer'])

        # Adding model 'MetadataCategorization'
        db.create_table(u'dcf_metadatacategorization', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='categorizations', blank=True, to=orm['dcf.MetadataVersion'])),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True, null=True, blank=True)),
        ))
        db.send_create_signal('dcf', ['MetadataCategorization'])

        # Adding model 'MetadataStandardCategory'
        db.create_table(u'dcf_metadatastandardcategory', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('remove', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('categorization', self.gf('django.db.models.fields.related.ForeignKey')(related_name='categories', to=orm['dcf.MetadataCategorization'])),
        ))
        db.send_create_signal('dcf', ['MetadataStandardCategory'])

        # Adding unique constraint on 'MetadataStandardCategory', fields ['categorization', 'name']
        db.create_unique(u'dcf_metadatastandardcategory', ['categorization_id', 'name'])

        # Adding model 'MetadataScientificCategory'
        db.create_table(u'dcf_metadatascientificcategory', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('remove', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('vocabulary', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='categories', null=True, to=orm['dcf.MetadataVocabulary'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='categories', null=True, to=orm['dcf.MetadataProject'])),
            ('component_name', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
        ))
        db.send_create_signal('dcf', ['MetadataScientificCategory'])

        # Adding unique constraint on 'MetadataScientificCategory', fields ['vocabulary', 'component_name', 'name']
        db.create_unique(u'dcf_metadatascientificcategory', ['vocabulary_id', 'component_name', 'name'])

        # Adding model 'MetadataVocabulary'
        db.create_table(u'dcf_metadatavocabulary', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='vocabularies', null=True, to=orm['dcf.MetadataProject'])),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True, null=True, blank=True)),
            ('document_type', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('component_tree', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('component_list', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('dcf', ['MetadataVocabulary'])

        # Adding model 'MetadataVersion'
        db.create_table(u'dcf_metadataversion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('models', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('dcf', ['MetadataVersion'])

        # Adding model 'MetadataProject'
        db.create_table(u'dcf_metadataproject', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_guid', self.gf('django.db.models.fields.CharField')(default='452172b8-4f27-406a-8c72-edcef017959d', unique=True, max_length=64)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('default_version', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='project', null=True, to=orm['dcf.MetadataVersion'])),
            ('restriction_customize', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('restriction_edit', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
        ))
        db.send_create_signal('dcf', ['MetadataProject'])


    def backwards(self, orm):
        # Removing unique constraint on 'MetadataScientificCategory', fields ['vocabulary', 'component_name', 'name']
        db.delete_unique(u'dcf_metadatascientificcategory', ['vocabulary_id', 'component_name', 'name'])

        # Removing unique constraint on 'MetadataStandardCategory', fields ['categorization', 'name']
        db.delete_unique(u'dcf_metadatastandardcategory', ['categorization_id', 'name'])

        # Removing unique constraint on 'MetadataModelCustomizer', fields ['project', 'version', 'model', 'name']
        db.delete_unique(u'dcf_metadatamodelcustomizer', ['project_id', 'version_id', 'model', 'name'])

        # Removing unique constraint on 'MetadataScientificPropertyProxy', fields ['model_name', 'component_name', 'name', 'category']
        db.delete_unique(u'dcf_metadatascientificpropertyproxy', ['model_name', 'component_name', 'name', 'category_id'])

        # Removing unique constraint on 'MetadataStandardPropertyProxy', fields ['version', 'model_name', 'name']
        db.delete_unique(u'dcf_metadatastandardpropertyproxy', ['version_id', 'model_name', 'name'])

        # Deleting model 'MetadataProperty'
        db.delete_table(u'dcf_metadataproperty')

        # Deleting model 'MetadataModelProxy'
        db.delete_table(u'dcf_metadatamodelproxy')

        # Deleting model 'MetadataStandardPropertyProxy'
        db.delete_table(u'dcf_metadatastandardpropertyproxy')

        # Deleting model 'MetadataScientificPropertyProxy'
        db.delete_table(u'dcf_metadatascientificpropertyproxy')

        # Deleting model 'MetadataScientificPropertyProxyValue'
        db.delete_table(u'dcf_metadatascientificpropertyproxyvalue')

        # Deleting model 'MetadataModelCustomizer'
        db.delete_table(u'dcf_metadatamodelcustomizer')

        # Removing M2M table for field vocabularies on 'MetadataModelCustomizer'
        db.delete_table(db.shorten_name(u'dcf_metadatamodelcustomizer_vocabularies'))

        # Deleting model 'MetadataStandardPropertyCustomizer'
        db.delete_table(u'dcf_metadatastandardpropertycustomizer')

        # Deleting model 'MetadataScientificPropertyCustomizer'
        db.delete_table(u'dcf_metadatascientificpropertycustomizer')

        # Deleting model 'MetadataCategorization'
        db.delete_table(u'dcf_metadatacategorization')

        # Deleting model 'MetadataStandardCategory'
        db.delete_table(u'dcf_metadatastandardcategory')

        # Deleting model 'MetadataScientificCategory'
        db.delete_table(u'dcf_metadatascientificcategory')

        # Deleting model 'MetadataVocabulary'
        db.delete_table(u'dcf_metadatavocabulary')

        # Deleting model 'MetadataVersion'
        db.delete_table(u'dcf_metadataversion')

        # Deleting model 'MetadataProject'
        db.delete_table(u'dcf_metadataproject')


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
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'656afa02-0d92-42c8-b20e-10cf19ea1a51'", 'unique': 'True', 'max_length': '64'}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'92b0515e-fe4d-47ac-aeee-31ce899b67c0'", 'unique': 'True', 'max_length': '64'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'model_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'model_title': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dcf.MetadataVersion']"})
        },
        'dcf.metadataproject': {
            'Meta': {'object_name': 'MetadataProject'},
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'e6165bec-d2b7-4065-b061-0fef8132fe95'", 'unique': 'True', 'max_length': '64'}),
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
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'aed5da4d-16ae-491c-acc7-f5429ab9a1ad'", 'unique': 'True', 'max_length': '64'}),
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
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'e34a4bb1-7ed8-47cc-960a-e97e7c4fe777'", 'unique': 'True', 'max_length': '64'}),
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
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'c3db4ab5-b6b3-44a4-97d9-579f9655bd8f'", 'unique': 'True', 'max_length': '64'}),
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
            '_guid': ('django.db.models.fields.CharField', [], {'default': "'de5e070f-470c-4ef7-8050-8c8cd3d9133c'", 'unique': 'True', 'max_length': '64'}),
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
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'vocabularies'", 'null': 'True', 'to': "orm['dcf.MetadataProject']"})
        }
    }

    complete_apps = ['dcf']