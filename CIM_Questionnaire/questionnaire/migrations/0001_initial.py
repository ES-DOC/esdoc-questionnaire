# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MetadataSite'
        db.create_table(u'questionnaire_metadatasite', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('site', self.gf('django.db.models.fields.related.OneToOneField')(related_name='metadata_site', unique=True, to=orm['sites.Site'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
        ))
        db.send_create_signal('questionnaire', ['MetadataSite'])

        # Adding model 'MetadataUser'
        db.create_table(u'questionnaire_metadatauser', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='metadata_user', unique=True, to=orm['auth.User'])),
        ))
        db.send_create_signal('questionnaire', ['MetadataUser'])

        # Adding M2M table for field projects on 'MetadataUser'
        m2m_table_name = db.shorten_name(u'questionnaire_metadatauser_projects')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('metadatauser', models.ForeignKey(orm['questionnaire.metadatauser'], null=False)),
            ('metadataproject', models.ForeignKey(orm['questionnaire.metadataproject'], null=False))
        ))
        db.create_unique(m2m_table_name, ['metadatauser_id', 'metadataproject_id'])

        # Adding model 'MetadataOpenIDProvider'
        db.create_table(u'questionnaire_metadataopenidprovider', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('url', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
            ('icon', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('questionnaire', ['MetadataOpenIDProvider'])

        # Adding model 'MetadataProject'
        db.create_table(u'questionnaire_metadataproject', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('authenticated', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True, blank=True)),
        ))
        db.send_create_signal('questionnaire', ['MetadataProject'])

        # Adding M2M table for field providers on 'MetadataProject'
        m2m_table_name = db.shorten_name(u'questionnaire_metadataproject_providers')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('metadataproject', models.ForeignKey(orm['questionnaire.metadataproject'], null=False)),
            ('metadataopenidprovider', models.ForeignKey(orm['questionnaire.metadataopenidprovider'], null=False))
        ))
        db.create_unique(m2m_table_name, ['metadataproject_id', 'metadataopenidprovider_id'])

        # Adding M2M table for field vocabularies on 'MetadataProject'
        m2m_table_name = db.shorten_name(u'questionnaire_metadataproject_vocabularies')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('metadataproject', models.ForeignKey(orm['questionnaire.metadataproject'], null=False)),
            ('metadatavocabulary', models.ForeignKey(orm['questionnaire.metadatavocabulary'], null=False))
        ))
        db.create_unique(m2m_table_name, ['metadataproject_id', 'metadatavocabulary_id'])

        # Adding model 'MetadataModelProxy'
        db.create_table(u'questionnaire_metadatamodelproxy', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('stereotype', self.gf('django.db.models.fields.CharField')(max_length=512, null=True)),
            ('documentation', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('package', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='model_proxies', null=True, to=orm['questionnaire.MetadataVersion'])),
        ))
        db.send_create_signal('questionnaire', ['MetadataModelProxy'])

        # Adding unique constraint on 'MetadataModelProxy', fields ['version', 'name']
        db.create_unique(u'questionnaire_metadatamodelproxy', ['version_id', 'name'])

        # Adding model 'MetadataStandardPropertyProxy'
        db.create_table(u'questionnaire_metadatastandardpropertyproxy', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('documentation', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('field_type', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('model_proxy', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='standard_properties', null=True, to=orm['questionnaire.MetadataModelProxy'])),
            ('atomic_default', self.gf('django.db.models.fields.CharField')(max_length=512, blank=True)),
            ('atomic_type', self.gf('django.db.models.fields.CharField')(default='DEFAULT', max_length=64)),
            ('enumeration_choices', self.gf('django.db.models.fields.CharField')(max_length=1024, blank=True)),
            ('enumeration_open', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('enumeration_multi', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('enumeration_nullable', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('relationship_cardinality', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('relationship_target_name', self.gf('django.db.models.fields.CharField')(max_length=512, blank=True)),
            ('relationship_target_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questionnaire.MetadataModelProxy'], null=True, blank=True)),
        ))
        db.send_create_signal('questionnaire', ['MetadataStandardPropertyProxy'])

        # Adding unique constraint on 'MetadataStandardPropertyProxy', fields ['model_proxy', 'name']
        db.create_unique(u'questionnaire_metadatastandardpropertyproxy', ['model_proxy_id', 'name'])

        # Adding model 'MetadataScientificPropertyProxy'
        db.create_table(u'questionnaire_metadatascientificpropertyproxy', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('documentation', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('field_type', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('component', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='scientific_properties', null=True, to=orm['questionnaire.MetadataComponentProxy'])),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='scientific_properties', null=True, to=orm['questionnaire.MetadataScientificCategoryProxy'])),
            ('choice', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('values', self.gf('django.db.models.fields.CharField')(max_length=1024, blank=True)),
        ))
        db.send_create_signal('questionnaire', ['MetadataScientificPropertyProxy'])

        # Adding unique constraint on 'MetadataScientificPropertyProxy', fields ['component', 'category', 'name']
        db.create_unique(u'questionnaire_metadatascientificpropertyproxy', ['component_id', 'category_id', 'name'])

        # Adding model 'MetadataStandardCategoryProxy'
        db.create_table(u'questionnaire_metadatastandardcategoryproxy', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('categorization', self.gf('django.db.models.fields.related.ForeignKey')(related_name='categories', to=orm['questionnaire.MetadataCategorization'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=512)),
        ))
        db.send_create_signal('questionnaire', ['MetadataStandardCategoryProxy'])

        # Adding unique constraint on 'MetadataStandardCategoryProxy', fields ['categorization', 'name']
        db.create_unique(u'questionnaire_metadatastandardcategoryproxy', ['categorization_id', 'name'])

        # Adding M2M table for field properties on 'MetadataStandardCategoryProxy'
        m2m_table_name = db.shorten_name(u'questionnaire_metadatastandardcategoryproxy_properties')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('metadatastandardcategoryproxy', models.ForeignKey(orm['questionnaire.metadatastandardcategoryproxy'], null=False)),
            ('metadatastandardpropertyproxy', models.ForeignKey(orm['questionnaire.metadatastandardpropertyproxy'], null=False))
        ))
        db.create_unique(m2m_table_name, ['metadatastandardcategoryproxy_id', 'metadatastandardpropertyproxy_id'])

        # Adding model 'MetadataScientificCategoryProxy'
        db.create_table(u'questionnaire_metadatascientificcategoryproxy', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('component', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='categories', null=True, to=orm['questionnaire.MetadataComponentProxy'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=512)),
        ))
        db.send_create_signal('questionnaire', ['MetadataScientificCategoryProxy'])

        # Adding unique constraint on 'MetadataScientificCategoryProxy', fields ['component', 'name']
        db.create_unique(u'questionnaire_metadatascientificcategoryproxy', ['component_id', 'name'])

        # Adding model 'MetadataComponentProxy'
        db.create_table(u'questionnaire_metadatacomponentproxy', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('documentation', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('vocabulary', self.gf('django.db.models.fields.related.ForeignKey')(related_name='component_proxies', null=True, to=orm['questionnaire.MetadataVocabulary'])),
            ('parent', self.gf('mptt.fields.TreeForeignKey')(blank=True, related_name='children', null=True, to=orm['questionnaire.MetadataComponentProxy'])),
            (u'lft', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'rght', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'tree_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'level', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal('questionnaire', ['MetadataComponentProxy'])

        # Adding unique constraint on 'MetadataComponentProxy', fields ['vocabulary', 'name']
        db.create_unique(u'questionnaire_metadatacomponentproxy', ['vocabulary_id', 'name'])

        # Adding model 'MetadataVocabulary'
        db.create_table(u'questionnaire_metadatavocabulary', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
            ('registered', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('document_type', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('questionnaire', ['MetadataVocabulary'])

        # Adding model 'MetadataModelCustomizer'
        db.create_table(u'questionnaire_metadatamodelcustomizer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('proxy', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questionnaire.MetadataModelProxy'], null=True, blank=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='model_customizers', null=True, to=orm['questionnaire.MetadataProject'])),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='model_customizers', null=True, to=orm['questionnaire.MetadataVersion'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('default', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('vocabulary_order', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(max_length=512)),
            ('model_title', self.gf('django.db.models.fields.CharField')(max_length=512, null=True)),
            ('model_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('model_show_all_categories', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('model_show_all_properties', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('model_show_hierarchy', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('model_hierarchy_name', self.gf('django.db.models.fields.CharField')(default='Component Hierarchy', max_length=128)),
            ('model_root_component', self.gf('django.db.models.fields.CharField')(default='RootComponent', max_length=128, blank=True)),
        ))
        db.send_create_signal('questionnaire', ['MetadataModelCustomizer'])

        # Adding unique constraint on 'MetadataModelCustomizer', fields ['name', 'project', 'version', 'proxy']
        db.create_unique(u'questionnaire_metadatamodelcustomizer', ['name', 'project_id', 'version_id', 'proxy_id'])

        # Adding M2M table for field vocabularies on 'MetadataModelCustomizer'
        m2m_table_name = db.shorten_name(u'questionnaire_metadatamodelcustomizer_vocabularies')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('metadatamodelcustomizer', models.ForeignKey(orm['questionnaire.metadatamodelcustomizer'], null=False)),
            ('metadatavocabulary', models.ForeignKey(orm['questionnaire.metadatavocabulary'], null=False))
        ))
        db.create_unique(m2m_table_name, ['metadatamodelcustomizer_id', 'metadatavocabulary_id'])

        # Adding model 'MetadataStandardCategoryCustomizer'
        db.create_table(u'questionnaire_metadatastandardcategorycustomizer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('pending_deletion', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('model_customizer', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='standard_property_category_customizers', null=True, to=orm['questionnaire.MetadataModelCustomizer'])),
            ('proxy', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questionnaire.MetadataStandardCategoryProxy'], null=True, blank=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='model_standard_category_customizers', null=True, to=orm['questionnaire.MetadataProject'])),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='model_standard_category_customizers', null=True, to=orm['questionnaire.MetadataVersion'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('questionnaire', ['MetadataStandardCategoryCustomizer'])

        # Adding unique constraint on 'MetadataStandardCategoryCustomizer', fields ['name', 'project', 'proxy', 'model_customizer']
        db.create_unique(u'questionnaire_metadatastandardcategorycustomizer', ['name', 'project_id', 'proxy_id', 'model_customizer_id'])

        # Adding model 'MetadataScientificCategoryCustomizer'
        db.create_table(u'questionnaire_metadatascientificcategorycustomizer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('pending_deletion', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('model_customizer', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='scientific_property_category_customizers', null=True, to=orm['questionnaire.MetadataModelCustomizer'])),
            ('proxy', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questionnaire.MetadataScientificCategoryProxy'], null=True, blank=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='model_scientific_category_customizers', null=True, to=orm['questionnaire.MetadataProject'])),
            ('vocabulary_key', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('component_key', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('model_key', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('questionnaire', ['MetadataScientificCategoryCustomizer'])

        # Adding unique constraint on 'MetadataScientificCategoryCustomizer', fields ['name', 'project', 'proxy', 'vocabulary_key', 'component_key', 'model_customizer']
        db.create_unique(u'questionnaire_metadatascientificcategorycustomizer', ['name', 'project_id', 'proxy_id', 'vocabulary_key', 'component_key', 'model_customizer_id'])

        # Adding model 'MetadataStandardPropertyCustomizer'
        db.create_table(u'questionnaire_metadatastandardpropertycustomizer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('field_type', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('displayed', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('required', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('editable', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('unique', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('verbose_name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('default_value', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('documentation', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('inline_help', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('proxy', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questionnaire.MetadataStandardPropertyProxy'], null=True, blank=True)),
            ('model_customizer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='standard_property_customizers', null=True, to=orm['questionnaire.MetadataModelCustomizer'])),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='standard_property_customizers', null=True, to=orm['questionnaire.MetadataStandardCategoryCustomizer'])),
            ('category_name', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('inherited', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('atomic_type', self.gf('django.db.models.fields.CharField')(default='DEFAULT', max_length=512, blank=True)),
            ('suggestions', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('enumeration_choices', self.gf('questionnaire.fields.EnumerationField')(null=True, blank=True)),
            ('enumeration_default', self.gf('questionnaire.fields.EnumerationField')(null=True, blank=True)),
            ('enumeration_open', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('enumeration_multi', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('enumeration_nullable', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('relationship_cardinality', self.gf('questionnaire.fields.CardinalityField')(max_length=8, blank=True)),
            ('relationship_show_subform', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('subform_customizer', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='property_customizer', null=True, to=orm['questionnaire.MetadataModelCustomizer'])),
        ))
        db.send_create_signal('questionnaire', ['MetadataStandardPropertyCustomizer'])

        # Adding model 'MetadataScientificPropertyCustomizer'
        db.create_table(u'questionnaire_metadatascientificpropertycustomizer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('field_type', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('displayed', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('required', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('editable', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('unique', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('verbose_name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('default_value', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('documentation', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('inline_help', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('proxy', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questionnaire.MetadataScientificPropertyProxy'], null=True, blank=True)),
            ('model_customizer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='scientific_property_customizers', null=True, to=orm['questionnaire.MetadataModelCustomizer'])),
            ('vocabulary_key', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('component_key', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('model_key', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('is_enumeration', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='scientific_property_customizers', null=True, to=orm['questionnaire.MetadataScientificCategoryCustomizer'])),
            ('category_name', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('atomic_type', self.gf('django.db.models.fields.CharField')(default='DEFAULT', max_length=512, blank=True)),
            ('atomic_default', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('enumeration_choices', self.gf('questionnaire.fields.EnumerationField')(null=True, blank=True)),
            ('enumeration_default', self.gf('questionnaire.fields.EnumerationField')(null=True, blank=True)),
            ('enumeration_open', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('enumeration_multi', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('enumeration_nullable', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('display_extra_standard_name', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('display_extra_description', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('display_extra_units', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('edit_extra_standard_name', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('edit_extra_description', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('edit_extra_units', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('extra_standard_name', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('extra_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('extra_units', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
        ))
        db.send_create_signal('questionnaire', ['MetadataScientificPropertyCustomizer'])

        # Adding model 'MetadataModel'
        db.create_table(u'questionnaire_metadatamodel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parent', self.gf('mptt.fields.TreeForeignKey')(blank=True, related_name='children', null=True, to=orm['questionnaire.MetadataModel'])),
            ('proxy', self.gf('django.db.models.fields.related.ForeignKey')(related_name='models', null=True, to=orm['questionnaire.MetadataModelProxy'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='models', null=True, to=orm['questionnaire.MetadataProject'])),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='models', null=True, to=orm['questionnaire.MetadataVersion'])),
            ('is_document', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('vocabulary_key', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('component_key', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            (u'lft', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'rght', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'tree_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'level', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal('questionnaire', ['MetadataModel'])

        # Adding unique constraint on 'MetadataModel', fields ['proxy', 'project', 'version', 'vocabulary_key', 'component_key']
        db.create_unique(u'questionnaire_metadatamodel', ['proxy_id', 'project_id', 'version_id', 'vocabulary_key', 'component_key'])

        # Adding model 'MetadataStandardProperty'
        db.create_table(u'questionnaire_metadatastandardproperty', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('field_type', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('model', self.gf('django.db.models.fields.related.ForeignKey')(related_name='standard_properties', null=True, to=orm['questionnaire.MetadataModel'])),
            ('proxy', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questionnaire.MetadataStandardPropertyProxy'], null=True, blank=True)),
            ('atomic_value', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True, blank=True)),
            ('enumeration_value', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True, blank=True)),
            ('enumeration_other_value', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True, blank=True)),
            ('relationship_value', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questionnaire.MetadataModel'], null=True, blank=True)),
        ))
        db.send_create_signal('questionnaire', ['MetadataStandardProperty'])

        # Adding model 'MetadataScientificProperty'
        db.create_table(u'questionnaire_metadatascientificproperty', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('field_type', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('model', self.gf('django.db.models.fields.related.ForeignKey')(related_name='scientific_properties', null=True, to=orm['questionnaire.MetadataModel'])),
            ('proxy', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questionnaire.MetadataScientificPropertyProxy'], null=True, blank=True)),
            ('is_enumeration', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('category_key', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('atomic_value', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True, blank=True)),
            ('enumeration_value', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True, blank=True)),
            ('enumeration_other_value', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True, blank=True)),
            ('extra_standard_name', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('extra_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('extra_units', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
        ))
        db.send_create_signal('questionnaire', ['MetadataScientificProperty'])

        # Adding model 'MetadataVersion'
        db.create_table(u'questionnaire_metadataversion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
            ('registered', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('categorization', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='versions', null=True, to=orm['questionnaire.MetadataCategorization'])),
        ))
        db.send_create_signal('questionnaire', ['MetadataVersion'])

        # Adding model 'MetadataCategorization'
        db.create_table(u'questionnaire_metadatacategorization', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
            ('registered', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal('questionnaire', ['MetadataCategorization'])


    def backwards(self, orm):
        # Removing unique constraint on 'MetadataModel', fields ['proxy', 'project', 'version', 'vocabulary_key', 'component_key']
        db.delete_unique(u'questionnaire_metadatamodel', ['proxy_id', 'project_id', 'version_id', 'vocabulary_key', 'component_key'])

        # Removing unique constraint on 'MetadataScientificCategoryCustomizer', fields ['name', 'project', 'proxy', 'vocabulary_key', 'component_key', 'model_customizer']
        db.delete_unique(u'questionnaire_metadatascientificcategorycustomizer', ['name', 'project_id', 'proxy_id', 'vocabulary_key', 'component_key', 'model_customizer_id'])

        # Removing unique constraint on 'MetadataStandardCategoryCustomizer', fields ['name', 'project', 'proxy', 'model_customizer']
        db.delete_unique(u'questionnaire_metadatastandardcategorycustomizer', ['name', 'project_id', 'proxy_id', 'model_customizer_id'])

        # Removing unique constraint on 'MetadataModelCustomizer', fields ['name', 'project', 'version', 'proxy']
        db.delete_unique(u'questionnaire_metadatamodelcustomizer', ['name', 'project_id', 'version_id', 'proxy_id'])

        # Removing unique constraint on 'MetadataComponentProxy', fields ['vocabulary', 'name']
        db.delete_unique(u'questionnaire_metadatacomponentproxy', ['vocabulary_id', 'name'])

        # Removing unique constraint on 'MetadataScientificCategoryProxy', fields ['component', 'name']
        db.delete_unique(u'questionnaire_metadatascientificcategoryproxy', ['component_id', 'name'])

        # Removing unique constraint on 'MetadataStandardCategoryProxy', fields ['categorization', 'name']
        db.delete_unique(u'questionnaire_metadatastandardcategoryproxy', ['categorization_id', 'name'])

        # Removing unique constraint on 'MetadataScientificPropertyProxy', fields ['component', 'category', 'name']
        db.delete_unique(u'questionnaire_metadatascientificpropertyproxy', ['component_id', 'category_id', 'name'])

        # Removing unique constraint on 'MetadataStandardPropertyProxy', fields ['model_proxy', 'name']
        db.delete_unique(u'questionnaire_metadatastandardpropertyproxy', ['model_proxy_id', 'name'])

        # Removing unique constraint on 'MetadataModelProxy', fields ['version', 'name']
        db.delete_unique(u'questionnaire_metadatamodelproxy', ['version_id', 'name'])

        # Deleting model 'MetadataSite'
        db.delete_table(u'questionnaire_metadatasite')

        # Deleting model 'MetadataUser'
        db.delete_table(u'questionnaire_metadatauser')

        # Removing M2M table for field projects on 'MetadataUser'
        db.delete_table(db.shorten_name(u'questionnaire_metadatauser_projects'))

        # Deleting model 'MetadataOpenIDProvider'
        db.delete_table(u'questionnaire_metadataopenidprovider')

        # Deleting model 'MetadataProject'
        db.delete_table(u'questionnaire_metadataproject')

        # Removing M2M table for field providers on 'MetadataProject'
        db.delete_table(db.shorten_name(u'questionnaire_metadataproject_providers'))

        # Removing M2M table for field vocabularies on 'MetadataProject'
        db.delete_table(db.shorten_name(u'questionnaire_metadataproject_vocabularies'))

        # Deleting model 'MetadataModelProxy'
        db.delete_table(u'questionnaire_metadatamodelproxy')

        # Deleting model 'MetadataStandardPropertyProxy'
        db.delete_table(u'questionnaire_metadatastandardpropertyproxy')

        # Deleting model 'MetadataScientificPropertyProxy'
        db.delete_table(u'questionnaire_metadatascientificpropertyproxy')

        # Deleting model 'MetadataStandardCategoryProxy'
        db.delete_table(u'questionnaire_metadatastandardcategoryproxy')

        # Removing M2M table for field properties on 'MetadataStandardCategoryProxy'
        db.delete_table(db.shorten_name(u'questionnaire_metadatastandardcategoryproxy_properties'))

        # Deleting model 'MetadataScientificCategoryProxy'
        db.delete_table(u'questionnaire_metadatascientificcategoryproxy')

        # Deleting model 'MetadataComponentProxy'
        db.delete_table(u'questionnaire_metadatacomponentproxy')

        # Deleting model 'MetadataVocabulary'
        db.delete_table(u'questionnaire_metadatavocabulary')

        # Deleting model 'MetadataModelCustomizer'
        db.delete_table(u'questionnaire_metadatamodelcustomizer')

        # Removing M2M table for field vocabularies on 'MetadataModelCustomizer'
        db.delete_table(db.shorten_name(u'questionnaire_metadatamodelcustomizer_vocabularies'))

        # Deleting model 'MetadataStandardCategoryCustomizer'
        db.delete_table(u'questionnaire_metadatastandardcategorycustomizer')

        # Deleting model 'MetadataScientificCategoryCustomizer'
        db.delete_table(u'questionnaire_metadatascientificcategorycustomizer')

        # Deleting model 'MetadataStandardPropertyCustomizer'
        db.delete_table(u'questionnaire_metadatastandardpropertycustomizer')

        # Deleting model 'MetadataScientificPropertyCustomizer'
        db.delete_table(u'questionnaire_metadatascientificpropertycustomizer')

        # Deleting model 'MetadataModel'
        db.delete_table(u'questionnaire_metadatamodel')

        # Deleting model 'MetadataStandardProperty'
        db.delete_table(u'questionnaire_metadatastandardproperty')

        # Deleting model 'MetadataScientificProperty'
        db.delete_table(u'questionnaire_metadatascientificproperty')

        # Deleting model 'MetadataVersion'
        db.delete_table(u'questionnaire_metadataversion')

        # Deleting model 'MetadataCategorization'
        db.delete_table(u'questionnaire_metadatacategorization')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'questionnaire.metadatacategorization': {
            'Meta': {'object_name': 'MetadataCategorization'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'registered': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'questionnaire.metadatacomponentproxy': {
            'Meta': {'ordering': "['order']", 'unique_together': "(('vocabulary', 'name'),)", 'object_name': 'MetadataComponentProxy'},
            'documentation': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            u'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['questionnaire.MetadataComponentProxy']"}),
            u'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'vocabulary': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'component_proxies'", 'null': 'True', 'to': "orm['questionnaire.MetadataVocabulary']"})
        },
        'questionnaire.metadatamodel': {
            'Meta': {'unique_together': "(('proxy', 'project', 'version', 'vocabulary_key', 'component_key'),)", 'object_name': 'MetadataModel'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'component_key': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_document': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['questionnaire.MetadataModel']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'models'", 'null': 'True', 'to': "orm['questionnaire.MetadataProject']"}),
            'proxy': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'models'", 'null': 'True', 'to': "orm['questionnaire.MetadataModelProxy']"}),
            u'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            u'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'models'", 'null': 'True', 'to': "orm['questionnaire.MetadataVersion']"}),
            'vocabulary_key': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'})
        },
        'questionnaire.metadatamodelcustomizer': {
            'Meta': {'unique_together': "(('name', 'project', 'version', 'proxy'),)", 'object_name': 'MetadataModelCustomizer'},
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'model_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'model_hierarchy_name': ('django.db.models.fields.CharField', [], {'default': "'Component Hierarchy'", 'max_length': '128'}),
            'model_root_component': ('django.db.models.fields.CharField', [], {'default': "'RootComponent'", 'max_length': '128', 'blank': 'True'}),
            'model_show_all_categories': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'model_show_all_properties': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'model_show_hierarchy': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'model_title': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'model_customizers'", 'null': 'True', 'to': "orm['questionnaire.MetadataProject']"}),
            'proxy': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['questionnaire.MetadataModelProxy']", 'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'model_customizers'", 'null': 'True', 'to': "orm['questionnaire.MetadataVersion']"}),
            'vocabularies': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['questionnaire.MetadataVocabulary']", 'null': 'True', 'blank': 'True'}),
            'vocabulary_order': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '512'})
        },
        'questionnaire.metadatamodelproxy': {
            'Meta': {'unique_together': "(('version', 'name'),)", 'object_name': 'MetadataModelProxy'},
            'documentation': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'package': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'stereotype': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'model_proxies'", 'null': 'True', 'to': "orm['questionnaire.MetadataVersion']"})
        },
        'questionnaire.metadataopenidprovider': {
            'Meta': {'object_name': 'MetadataOpenIDProvider'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'})
        },
        'questionnaire.metadataproject': {
            'Meta': {'object_name': 'MetadataProject'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'authenticated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'providers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['questionnaire.MetadataOpenIDProvider']", 'symmetrical': 'False', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'vocabularies': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['questionnaire.MetadataVocabulary']", 'null': 'True', 'blank': 'True'})
        },
        'questionnaire.metadatascientificcategorycustomizer': {
            'Meta': {'ordering': "['order']", 'unique_together': "(('name', 'project', 'proxy', 'vocabulary_key', 'component_key', 'model_customizer'),)", 'object_name': 'MetadataScientificCategoryCustomizer'},
            'component_key': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'model_customizer': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'scientific_property_category_customizers'", 'null': 'True', 'to': "orm['questionnaire.MetadataModelCustomizer']"}),
            'model_key': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'pending_deletion': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'model_scientific_category_customizers'", 'null': 'True', 'to': "orm['questionnaire.MetadataProject']"}),
            'proxy': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['questionnaire.MetadataScientificCategoryProxy']", 'null': 'True', 'blank': 'True'}),
            'vocabulary_key': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'})
        },
        'questionnaire.metadatascientificcategoryproxy': {
            'Meta': {'unique_together': "(('component', 'name'),)", 'object_name': 'MetadataScientificCategoryProxy'},
            'component': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'categories'", 'null': 'True', 'to': "orm['questionnaire.MetadataComponentProxy']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'questionnaire.metadatascientificproperty': {
            'Meta': {'ordering': "['order']", 'object_name': 'MetadataScientificProperty'},
            'atomic_value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'category_key': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'enumeration_other_value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'enumeration_value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'extra_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'extra_standard_name': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'extra_units': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'field_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_enumeration': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'model': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'scientific_properties'", 'null': 'True', 'to': "orm['questionnaire.MetadataModel']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'proxy': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['questionnaire.MetadataScientificPropertyProxy']", 'null': 'True', 'blank': 'True'})
        },
        'questionnaire.metadatascientificpropertycustomizer': {
            'Meta': {'ordering': "['order']", 'object_name': 'MetadataScientificPropertyCustomizer'},
            'atomic_default': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'atomic_type': ('django.db.models.fields.CharField', [], {'default': "'DEFAULT'", 'max_length': '512', 'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'scientific_property_customizers'", 'null': 'True', 'to': "orm['questionnaire.MetadataScientificCategoryCustomizer']"}),
            'category_name': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'component_key': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'default_value': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'display_extra_description': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'display_extra_standard_name': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'display_extra_units': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'displayed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'documentation': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'edit_extra_description': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'edit_extra_standard_name': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'edit_extra_units': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'editable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enumeration_choices': ('questionnaire.fields.EnumerationField', [], {'null': 'True', 'blank': 'True'}),
            'enumeration_default': ('questionnaire.fields.EnumerationField', [], {'null': 'True', 'blank': 'True'}),
            'enumeration_multi': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enumeration_nullable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enumeration_open': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'extra_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'extra_standard_name': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'extra_units': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'field_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inline_help': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_enumeration': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'model_customizer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'scientific_property_customizers'", 'null': 'True', 'to': "orm['questionnaire.MetadataModelCustomizer']"}),
            'model_key': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'proxy': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['questionnaire.MetadataScientificPropertyProxy']", 'null': 'True', 'blank': 'True'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'unique': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'verbose_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'vocabulary_key': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'})
        },
        'questionnaire.metadatascientificpropertyproxy': {
            'Meta': {'unique_together': "(('component', 'category', 'name'),)", 'object_name': 'MetadataScientificPropertyProxy'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'scientific_properties'", 'null': 'True', 'to': "orm['questionnaire.MetadataScientificCategoryProxy']"}),
            'choice': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'component': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'scientific_properties'", 'null': 'True', 'to': "orm['questionnaire.MetadataComponentProxy']"}),
            'documentation': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'field_type': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'values': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'})
        },
        'questionnaire.metadatasite': {
            'Meta': {'object_name': 'MetadataSite'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'metadata_site'", 'unique': 'True', 'to': u"orm['sites.Site']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'})
        },
        'questionnaire.metadatastandardcategorycustomizer': {
            'Meta': {'ordering': "['order']", 'unique_together': "(('name', 'project', 'proxy', 'model_customizer'),)", 'object_name': 'MetadataStandardCategoryCustomizer'},
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'model_customizer': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'standard_property_category_customizers'", 'null': 'True', 'to': "orm['questionnaire.MetadataModelCustomizer']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'pending_deletion': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'model_standard_category_customizers'", 'null': 'True', 'to': "orm['questionnaire.MetadataProject']"}),
            'proxy': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['questionnaire.MetadataStandardCategoryProxy']", 'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'model_standard_category_customizers'", 'null': 'True', 'to': "orm['questionnaire.MetadataVersion']"})
        },
        'questionnaire.metadatastandardcategoryproxy': {
            'Meta': {'unique_together': "(('categorization', 'name'),)", 'object_name': 'MetadataStandardCategoryProxy'},
            'categorization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'categories'", 'to': "orm['questionnaire.MetadataCategorization']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'properties': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'category'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['questionnaire.MetadataStandardPropertyProxy']"})
        },
        'questionnaire.metadatastandardproperty': {
            'Meta': {'ordering': "['order']", 'object_name': 'MetadataStandardProperty'},
            'atomic_value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'enumeration_other_value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'enumeration_value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'field_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'standard_properties'", 'null': 'True', 'to': "orm['questionnaire.MetadataModel']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'proxy': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['questionnaire.MetadataStandardPropertyProxy']", 'null': 'True', 'blank': 'True'}),
            'relationship_value': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['questionnaire.MetadataModel']", 'null': 'True', 'blank': 'True'})
        },
        'questionnaire.metadatastandardpropertycustomizer': {
            'Meta': {'ordering': "['order']", 'object_name': 'MetadataStandardPropertyCustomizer'},
            'atomic_type': ('django.db.models.fields.CharField', [], {'default': "'DEFAULT'", 'max_length': '512', 'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'standard_property_customizers'", 'null': 'True', 'to': "orm['questionnaire.MetadataStandardCategoryCustomizer']"}),
            'category_name': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'default_value': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'displayed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'documentation': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'editable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enumeration_choices': ('questionnaire.fields.EnumerationField', [], {'null': 'True', 'blank': 'True'}),
            'enumeration_default': ('questionnaire.fields.EnumerationField', [], {'null': 'True', 'blank': 'True'}),
            'enumeration_multi': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enumeration_nullable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enumeration_open': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'field_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inherited': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'inline_help': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'model_customizer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'standard_property_customizers'", 'null': 'True', 'to': "orm['questionnaire.MetadataModelCustomizer']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'proxy': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['questionnaire.MetadataStandardPropertyProxy']", 'null': 'True', 'blank': 'True'}),
            'relationship_cardinality': ('questionnaire.fields.CardinalityField', [], {'max_length': '8', 'blank': 'True'}),
            'relationship_show_subform': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'subform_customizer': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'property_customizer'", 'null': 'True', 'to': "orm['questionnaire.MetadataModelCustomizer']"}),
            'suggestions': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'unique': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'verbose_name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'questionnaire.metadatastandardpropertyproxy': {
            'Meta': {'unique_together': "(('model_proxy', 'name'),)", 'object_name': 'MetadataStandardPropertyProxy'},
            'atomic_default': ('django.db.models.fields.CharField', [], {'max_length': '512', 'blank': 'True'}),
            'atomic_type': ('django.db.models.fields.CharField', [], {'default': "'DEFAULT'", 'max_length': '64'}),
            'documentation': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'enumeration_choices': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'enumeration_multi': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enumeration_nullable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enumeration_open': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'field_type': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model_proxy': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'standard_properties'", 'null': 'True', 'to': "orm['questionnaire.MetadataModelProxy']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'relationship_cardinality': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'relationship_target_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['questionnaire.MetadataModelProxy']", 'null': 'True', 'blank': 'True'}),
            'relationship_target_name': ('django.db.models.fields.CharField', [], {'max_length': '512', 'blank': 'True'})
        },
        'questionnaire.metadatauser': {
            'Meta': {'object_name': 'MetadataUser'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'metadata_user'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['questionnaire.MetadataProject']"}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'metadata_user'", 'unique': 'True', 'to': u"orm['auth.User']"})
        },
        'questionnaire.metadataversion': {
            'Meta': {'object_name': 'MetadataVersion'},
            'categorization': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'versions'", 'null': 'True', 'to': "orm['questionnaire.MetadataCategorization']"}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'registered': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'questionnaire.metadatavocabulary': {
            'Meta': {'object_name': 'MetadataVocabulary'},
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'registered': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'sites.site': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'Site', 'db_table': "u'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['questionnaire']