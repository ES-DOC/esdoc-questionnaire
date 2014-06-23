from django.template.defaultfilters import slugify

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase

from CIM_Questionnaire.questionnaire.models import MetadataModelProxy
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer
from CIM_Questionnaire.questionnaire.forms.forms_customize import create_model_customizer_form_data, create_standard_property_customizer_form_data, create_scientific_property_customizer_form_data
from CIM_Questionnaire.questionnaire.forms.forms_customize import create_new_customizer_forms_from_models, create_existing_customizer_forms_from_models, create_customizer_forms_from_data
from CIM_Questionnaire.questionnaire.forms.forms_customize import get_data_from_customizer_forms
from CIM_Questionnaire.questionnaire.forms.forms_customize import MetadataModelCustomizerForm, MetadataStandardPropertyCustomizerInlineFormSetFactory, MetadataScientificPropertyCustomizerInlineFormSetFactory

from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes
from CIM_Questionnaire.questionnaire.utils import JSON_SERIALIZER

class Test(TestQuestionnaireBase):

    def test_create_model_customizer_form_data(self):
        """Test creation of initial form data for model_customizer form."""

        vocabularies = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(self.customizer,vocabularies)

        model_customizer_data = create_model_customizer_form_data(model_customizer,standard_category_customizers,scientific_category_customizers)

        # TODO: ENSURE model_customizer_data CORRESPONDS TO EXPECTED VALUES

    def test_create_standard_property_customizer_form_data(self):
        """Test creation of initial form data for standard_customizer formset."""

        vocabularies = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(self.customizer,vocabularies)

        standard_property_customizers_data = [
            create_standard_property_customizer_form_data(model_customizer,standard_property_customizer)
            for standard_property_customizer in standard_property_customizers
        ]

        # TODO: ENSURE standard_property_customizers_data CORRESPONDS TO EXPECTED VALUES

    def test_create_scientific_property_customizer_form_data(self):
        """Test creation of initial form data for standard_customizer formset."""

        vocabularies = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(self.customizer,vocabularies)

        scientific_property_customizers_data = {}
        for vocabulary_key,scientific_property_customizer_dict in scientific_property_customizers.iteritems():
            scientific_property_customizers_data[vocabulary_key] = {}
            for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
                scientific_property_customizers_data[vocabulary_key][component_key] = [
                    create_scientific_property_customizer_form_data(model_customizer,scientific_property_customizer)
                    for scientific_property_customizer in scientific_property_customizers[vocabulary_key][component_key]
                ]

        # TODO: ENSURE scientific_property_customizers_data CORRESPONDS TO EXPECTED VALUES


    def test_new_model_customizer_form(self):
        """Test creation of model customizer form (using new customizers)"""

        test_model_name = "modelcomponent"
        model_proxy_to_be_customized = MetadataModelProxy.objects.get(version=self.version,name__iexact=test_model_name)
        vocabularies_to_be_customized = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_new_customizer_set(self.project,self.version,model_proxy_to_be_customized,vocabularies_to_be_customized)

        self.assertEqual(model_customizer.proxy,model_proxy_to_be_customized)

        (model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets) = \
            create_new_customizer_forms_from_models(model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers,vocabularies_to_customize=vocabularies_to_be_customized)

        # now the form is created; test away...

        self.assertEqual(model_customizer.name,model_customizer_form.get_current_field_value("name"))
        self.assertEqual(model_customizer.description,model_customizer_form.get_current_field_value("description"))
        self.assertEqual(model_customizer.default,model_customizer_form.get_current_field_value("default"))
        self.assertEqual(model_customizer.model_title,model_customizer_form.get_current_field_value("model_title"))
        self.assertEqual(model_customizer.model_description,model_customizer_form.get_current_field_value("model_description"))
        self.assertEqual(model_customizer.model_show_all_categories,model_customizer_form.get_current_field_value("model_show_all_categories"))
        self.assertEqual(model_customizer.model_show_all_properties,model_customizer_form.get_current_field_value("model_show_all_properties"))
        self.assertEqual(model_customizer.model_show_hierarchy,model_customizer_form.get_current_field_value("model_show_hierarchy"))
        self.assertEqual(model_customizer.model_hierarchy_name,model_customizer_form.get_current_field_value("model_hierarchy_name"))
        self.assertEqual(model_customizer.model_root_component,model_customizer_form.get_current_field_value("model_root_component"))

        # fk fields are compared via primary keys
        self.assertEqual(model_customizer.proxy.pk,model_customizer_form.get_current_field_value("proxy"))
        self.assertEqual(model_customizer.project.pk,model_customizer_form.get_current_field_value("project"))
        self.assertEqual(model_customizer.version.pk,model_customizer_form.get_current_field_value("version"))

        # m2m fields do not yet exist on the instance
        self.assertItemsEqual(vocabularies_to_be_customized,model_customizer_form.get_current_field_value("vocabularies"))
        self.assertEqual(",".join(map(str,[vocabulary.pk for vocabulary in vocabularies_to_be_customized])),model_customizer_form.get_current_field_value("vocabulary_order")) # (and this is set in the get_new_customizer fn above)
        self.assertEqual(vocabularies_to_be_customized,model_customizer_form.fields["vocabularies"].queryset)

        # these fields are added in the forms...
        self.assertEqual(JSON_SERIALIZER.serialize(standard_category_customizers),model_customizer_form.get_current_field_value("standard_categories_content"))
        self.assertEqual("|".join([standard_category.name for standard_category in standard_category_customizers]),model_customizer_form.get_current_field_value("standard_categories_tags"))
        for vocabulary_key,scientific_category_customizer_dict in scientific_category_customizers.iteritems():
            for component_key,scientific_category_customizer_list in scientific_category_customizer_dict.iteritems():
                scientific_categories_content_field_name = u"%s_%s_scientific_categories_content" % (vocabulary_key,component_key)
                scientific_categories_tags_field_name = u"%s_%s_scientific_categories_tags" % (vocabulary_key,component_key)
                self.assertEqual(JSON_SERIALIZER.serialize(scientific_category_customizer_list),model_customizer_form.get_current_field_value(scientific_categories_content_field_name))
                self.assertEqual("|".join([scientific_category.name for scientific_category in scientific_category_customizer_list]),model_customizer_form.get_current_field_value(scientific_categories_tags_field_name))


    def test_existing_model_customizer_form(self):
        """Test creation of model customizer form (using existing customizers)"""

        test_model_name = "modelcomponent"
        model_proxy_to_be_customized = MetadataModelProxy.objects.get(version=self.version,name__iexact=test_model_name)
        vocabularies_to_be_customized = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(self.customizer,vocabularies_to_be_customized)

        self.assertEqual(model_customizer.proxy,model_proxy_to_be_customized)

        (model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets) = \
            create_existing_customizer_forms_from_models(model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers,vocabularies_to_customize=vocabularies_to_be_customized,is_subform=True)

        # now the form is created; test away...

        model_customizer_to_test = model_customizer_form.instance

        self.assertEqual(model_customizer_to_test.name,model_customizer_form.get_current_field_value("name"))
        self.assertEqual(model_customizer_to_test.description,model_customizer_form.get_current_field_value("description"))
        self.assertEqual(model_customizer_to_test.default,model_customizer_form.get_current_field_value("default"))
        self.assertEqual(model_customizer_to_test.model_title,model_customizer_form.get_current_field_value("model_title"))
        self.assertEqual(model_customizer_to_test.model_description,model_customizer_form.get_current_field_value("model_description"))
        self.assertEqual(model_customizer_to_test.get_field("model_show_all_categories").default,model_customizer_form.get_current_field_value("model_show_all_categories"))
        self.assertEqual(model_customizer_to_test.get_field("model_show_all_properties").default,model_customizer_form.get_current_field_value("model_show_all_properties"))
        self.assertEqual(model_customizer_to_test.get_field("model_show_hierarchy").default,model_customizer_form.get_current_field_value("model_show_hierarchy"))
        self.assertEqual(model_customizer_to_test.get_field("model_hierarchy_name").default,model_customizer_form.get_current_field_value("model_hierarchy_name"))
        self.assertEqual(model_customizer_to_test.get_field("model_root_component").default,model_customizer_form.get_current_field_value("model_root_component"))


        # fk fields are compared via primary keys
        self.assertEqual(model_customizer_to_test.proxy.pk,model_customizer_form.get_current_field_value("proxy"))
        self.assertEqual(model_customizer_to_test.project.pk,model_customizer_form.get_current_field_value("project"))
        self.assertEqual(model_customizer_to_test.version.pk,model_customizer_form.get_current_field_value("version"))

        # m2m fields do not yet exist on the instance
        self.assertItemsEqual(vocabularies_to_be_customized,model_customizer_form.get_current_field_value("vocabularies"))
        self.assertEqual(",".join(map(str,[vocabulary.pk for vocabulary in vocabularies_to_be_customized])),model_customizer_form.get_current_field_value("vocabulary_order")) # (and this is set in the get_new_customizer fn above)
        self.assertEqual(vocabularies_to_be_customized,model_customizer_form.fields["vocabularies"].queryset)

        # these fields are added in the forms...
        self.assertEqual(JSON_SERIALIZER.serialize(standard_category_customizers),model_customizer_form.get_current_field_value("standard_categories_content"))
        self.assertEqual("|".join([standard_category.name for standard_category in standard_category_customizers]),model_customizer_form.get_current_field_value("standard_categories_tags"))
        for vocabulary_key,scientific_category_customizer_dict in scientific_category_customizers.iteritems():
            for component_key,scientific_category_customizer_list in scientific_category_customizer_dict.iteritems():
                scientific_categories_content_field_name = u"%s_%s_scientific_categories_content" % (vocabulary_key,component_key)
                scientific_categories_tags_field_name = u"%s_%s_scientific_categories_tags" % (vocabulary_key,component_key)
                self.assertEqual(JSON_SERIALIZER.serialize(scientific_category_customizer_list),model_customizer_form.get_current_field_value(scientific_categories_content_field_name))
                self.assertEqual("|".join([scientific_category.name for scientific_category in scientific_category_customizer_list]),model_customizer_form.get_current_field_value(scientific_categories_tags_field_name))


    def test_new_standard_property_customizer_formset(self):
        """Test creation of standard property customizer formsets (using new customizers)"""

        test_model_name = "modelcomponent"
        model_proxy_to_be_customized = MetadataModelProxy.objects.get(version=self.version,name__iexact=test_model_name)
        vocabularies_to_be_customized = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_new_customizer_set(self.project,self.version,model_proxy_to_be_customized,vocabularies_to_be_customized)

        self.assertEqual(model_customizer.proxy,model_proxy_to_be_customized)

        (model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets) = \
            create_new_customizer_forms_from_models(model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers,vocabularies_to_customize=vocabularies_to_be_customized)

        # now the formset is created; test away...

        for standard_property_customizer,standard_property_customizer_form in zip(standard_property_customizers,standard_property_customizer_formset):

            field_type = standard_property_customizer_form.get_current_field_value("field_type")
            self.assertEqual(field_type,standard_property_customizer_form.type)
            self.assertEqual(field_type in MetadataFieldTypes,True)

            self.assertEqual(standard_property_customizer.field_type,field_type)
            self.assertEqual(standard_property_customizer.name,standard_property_customizer_form.get_current_field_value("name"))
            self.assertEqual(standard_property_customizer.order,standard_property_customizer_form.get_current_field_value("order"))
            self.assertEqual(standard_property_customizer.displayed,standard_property_customizer_form.get_current_field_value("displayed"))
            self.assertEqual(standard_property_customizer.required,standard_property_customizer_form.get_current_field_value("required"))
            self.assertEqual(standard_property_customizer.editable,standard_property_customizer_form.get_current_field_value("editable"))
            self.assertEqual(standard_property_customizer.unique,standard_property_customizer_form.get_current_field_value("unique"))
            self.assertEqual(standard_property_customizer.verbose_name,standard_property_customizer_form.get_current_field_value("verbose_name"))
            self.assertEqual(standard_property_customizer.default_value,standard_property_customizer_form.get_current_field_value("default_value"))
            self.assertEqual(standard_property_customizer.documentation,standard_property_customizer_form.get_current_field_value("documentation"))
            self.assertEqual(standard_property_customizer.inline_help,standard_property_customizer_form.get_current_field_value("inline_help"))
            self.assertEqual(standard_property_customizer.category_name,standard_property_customizer_form.get_current_field_value("category_name"))
            self.assertEqual(standard_property_customizer.inherited,standard_property_customizer_form.get_current_field_value("inherited"))

            # fk fields are compared via primary keys
            self.assertEqual(standard_property_customizer.proxy.pk,standard_property_customizer_form.get_current_field_value("proxy"))

            # don't actually have to check this for _standard_ properties (since it's not displayed I never bother changing it in the form's __init__ fn)
            ## and the category field is a one-off (changed from a fk to a charfield)
            #self.assertEqual(standard_property_customizer.category.key,standard_property_customizer_form.get_current_field_value("category"))

            if field_type == MetadataFieldTypes.ATOMIC:
                self.assertEqual(standard_property_customizer.atomic_type,standard_property_customizer_form.get_current_field_value("atomic_type"))
                self.assertEqual(standard_property_customizer.suggestions,standard_property_customizer_form.get_current_field_value("suggestions"))

            elif field_type == MetadataFieldTypes.ENUMERATION:
                current_enumeration_choices = standard_property_customizer.enumeration_choices
                if current_enumeration_choices:
                    current_enumeration_choices = current_enumeration_choices.split("|")
                current_enumeration_default = standard_property_customizer.enumeration_default
                if current_enumeration_default:
                    current_enumeration_default = current_enumeration_default.split("|")
                self.assertEqual(current_enumeration_choices,standard_property_customizer_form.get_current_field_value("enumeration_choices"))
                self.assertEqual(current_enumeration_default,standard_property_customizer_form.get_current_field_value("enumeration_default"))
                self.assertEqual(standard_property_customizer.enumeration_open,standard_property_customizer_form.get_current_field_value("enumeration_open"))
                self.assertEqual(standard_property_customizer.enumeration_multi,standard_property_customizer_form.get_current_field_value("enumeration_multi"))
                self.assertEqual(standard_property_customizer.enumeration_nullable,standard_property_customizer_form.get_current_field_value("enumeration_nullable"))


            elif field_type == MetadataFieldTypes.RELATIONSHIP:
                show_subform_widget_attrs = standard_property_customizer_form.fields["relationship_show_subform"].widget.attrs
                self.assertEqual(show_subform_widget_attrs["readonly"],"readonly")
                self.assertEqual("readonly" in show_subform_widget_attrs["class"],True)
                self.assertEqual(standard_property_customizer.relationship_cardinality,standard_property_customizer_form.get_current_field_value("relationship_cardinality"))
                self.assertEqual(standard_property_customizer.relationship_show_subform,standard_property_customizer_form.get_current_field_value("relationship_show_subform"))
                self.assertIsNone(standard_property_customizer_form.get_current_field_value("subform_customizer"))

            else:
                self.assertEqual(True,False,msg="Invalid field_type used for StandardProperty")


    def test_existing_standard_property_customizer_formset(self):
        """Test creation of standard property customizer formsets (using existing customizers)"""

        test_model_name = "modelcomponent"
        model_proxy_to_be_customized = MetadataModelProxy.objects.get(version=self.version,name__iexact=test_model_name)
        vocabularies_to_be_customized = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(self.customizer,vocabularies_to_be_customized)

        self.assertEqual(model_customizer.proxy,model_proxy_to_be_customized)

        (model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets) = \
            create_existing_customizer_forms_from_models(model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers,vocabularies_to_customize=vocabularies_to_be_customized,is_subform=True)

        # now the formset is created; test away...

        for standard_property_customizer_form in standard_property_customizer_formset:

            standard_property_customizer = standard_property_customizer_form.instance

            field_type = standard_property_customizer_form.get_current_field_value("field_type")
            self.assertEqual(field_type,standard_property_customizer_form.type)
            self.assertEqual(field_type in MetadataFieldTypes,True)

            self.assertEqual(standard_property_customizer.field_type,field_type)
            self.assertEqual(standard_property_customizer.name,standard_property_customizer_form.get_current_field_value("name"))
            self.assertEqual(standard_property_customizer.order,standard_property_customizer_form.get_current_field_value("order"))
            self.assertEqual(standard_property_customizer.displayed,standard_property_customizer_form.get_current_field_value("displayed"))
            self.assertEqual(standard_property_customizer.required,standard_property_customizer_form.get_current_field_value("required"))
            self.assertEqual(standard_property_customizer.editable,standard_property_customizer_form.get_current_field_value("editable"))
            self.assertEqual(standard_property_customizer.unique,standard_property_customizer_form.get_current_field_value("unique"))
            self.assertEqual(standard_property_customizer.verbose_name,standard_property_customizer_form.get_current_field_value("verbose_name"))
            self.assertEqual(standard_property_customizer.default_value,standard_property_customizer_form.get_current_field_value("default_value"))
            self.assertEqual(standard_property_customizer.documentation,standard_property_customizer_form.get_current_field_value("documentation"))
            self.assertEqual(standard_property_customizer.inline_help,standard_property_customizer_form.get_current_field_value("inline_help"))
            self.assertEqual(standard_property_customizer.category_name,standard_property_customizer_form.get_current_field_value("category_name"))
            self.assertEqual(standard_property_customizer.inherited,standard_property_customizer_form.get_current_field_value("inherited"))

            # fk fields are compared via primary keys
            self.assertEqual(standard_property_customizer.proxy.pk,standard_property_customizer_form.get_current_field_value("proxy"))

            # don't actually have to check this for _standard_ properties (since it's not displayed I never bother changing it in the form's __init__ fn)
            ## and the category field is a one-off (changed from a fk to a charfield)
            #self.assertEqual(standard_property_customizer.category.key,standard_property_customizer_form.get_current_field_value("category"))

            if field_type == MetadataFieldTypes.ATOMIC:
                self.assertEqual(standard_property_customizer.atomic_type,standard_property_customizer_form.get_current_field_value("atomic_type"))
                self.assertEqual(standard_property_customizer.suggestions,standard_property_customizer_form.get_current_field_value("suggestions"))

            elif field_type == MetadataFieldTypes.ENUMERATION:
                current_enumeration_choices = standard_property_customizer.enumeration_choices
                if current_enumeration_choices:
                    current_enumeration_choices = current_enumeration_choices.split("|")
                current_enumeration_default = standard_property_customizer.enumeration_default
                if current_enumeration_default:
                    current_enumeration_default = current_enumeration_default.split("|")
                self.assertEqual(current_enumeration_choices,standard_property_customizer_form.get_current_field_value("enumeration_choices"))
                self.assertEqual(current_enumeration_default,standard_property_customizer_form.get_current_field_value("enumeration_default"))
                self.assertEqual(standard_property_customizer.enumeration_open,standard_property_customizer_form.get_current_field_value("enumeration_open"))
                self.assertEqual(standard_property_customizer.enumeration_multi,standard_property_customizer_form.get_current_field_value("enumeration_multi"))
                self.assertEqual(standard_property_customizer.enumeration_nullable,standard_property_customizer_form.get_current_field_value("enumeration_nullable"))


            elif field_type == MetadataFieldTypes.RELATIONSHIP:
                show_subform_widget_attrs = standard_property_customizer_form.fields["relationship_show_subform"].widget.attrs
                self.assertEqual("readonly" in show_subform_widget_attrs,False)
                self.assertEqual("readonly" in show_subform_widget_attrs["class"],False)
                self.assertEqual(standard_property_customizer.relationship_cardinality,standard_property_customizer_form.get_current_field_value("relationship_cardinality"))
                self.assertEqual(standard_property_customizer.relationship_show_subform,standard_property_customizer_form.get_current_field_value("relationship_show_subform"))

            else:
                self.assertEqual(True,False,msg="Invalid field_type used for StandardProperty")


    def test_new_scientific_property_customizer_formsets(self):
        """Test creation of scientific property customizer formsets (using new customizers)"""

        test_model_name = "modelcomponent"
        model_proxy_to_be_customized = MetadataModelProxy.objects.get(version=self.version,name__iexact=test_model_name)
        vocabularies_to_be_customized = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_new_customizer_set(self.project,self.version,model_proxy_to_be_customized,vocabularies_to_be_customized)

        self.assertEqual(model_customizer.proxy,model_proxy_to_be_customized)

        (model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets) = \
            create_new_customizer_forms_from_models(model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers,vocabularies_to_customize=vocabularies_to_be_customized)

        # now the formsets are created; test away...

        for vocabulary_key,scientific_property_customizer_formset_dict in scientific_property_customizer_formsets.iteritems():
            for component_key,scientific_property_customizer_formset in scientific_property_customizer_formset_dict.iteritems():
                for scientific_property_customizer,scientific_property_customizer_form in zip(scientific_property_customizers[vocabulary_key][component_key],scientific_property_customizer_formset):

                    field_type = scientific_property_customizer_form.get_current_field_value("field_type")
                    is_enumeration = scientific_property_customizer_form.get_current_field_value("is_enumeration")
                    self.assertEqual(field_type,MetadataFieldTypes.PROPERTY.getType())

                    self.assertEqual(scientific_property_customizer.category_name,scientific_property_customizer_form.get_current_field_value("category_name"))
                    self.assertEqual(scientific_property_customizer.order,scientific_property_customizer_form.get_current_field_value("order"))
                    self.assertEqual(scientific_property_customizer.vocabulary_key,scientific_property_customizer_form.get_current_field_value("vocabulary_key"))
                    self.assertEqual(scientific_property_customizer.component_key,scientific_property_customizer_form.get_current_field_value("component_key"))
                    self.assertEqual(scientific_property_customizer.model_key,scientific_property_customizer_form.get_current_field_value("model_key"))
                    self.assertEqual(scientific_property_customizer.displayed,scientific_property_customizer_form.get_current_field_value("displayed"))
                    self.assertEqual(scientific_property_customizer.required,scientific_property_customizer_form.get_current_field_value("required"))
                    self.assertEqual(scientific_property_customizer.editable,scientific_property_customizer_form.get_current_field_value("editable"))
                    self.assertEqual(scientific_property_customizer.unique,scientific_property_customizer_form.get_current_field_value("unique"))
                    self.assertEqual(scientific_property_customizer.verbose_name,scientific_property_customizer_form.get_current_field_value("verbose_name"))
                    self.assertEqual(scientific_property_customizer.default_value,scientific_property_customizer_form.get_current_field_value("default_value"))
                    self.assertEqual(scientific_property_customizer.documentation,scientific_property_customizer_form.get_current_field_value("documentation"))
                    self.assertEqual(scientific_property_customizer.inline_help,scientific_property_customizer_form.get_current_field_value("inline_help"))
                    self.assertEqual(scientific_property_customizer.display_extra_standard_name,scientific_property_customizer_form.get_current_field_value("display_extra_standard_name"))
                    self.assertEqual(scientific_property_customizer.edit_extra_standard_name,scientific_property_customizer_form.get_current_field_value("edit_extra_standard_name"))
                    self.assertEqual(scientific_property_customizer.extra_standard_name,scientific_property_customizer_form.get_current_field_value("extra_standard_name"))
                    self.assertEqual(scientific_property_customizer.display_extra_description,scientific_property_customizer_form.get_current_field_value("display_extra_description"))
                    self.assertEqual(scientific_property_customizer.edit_extra_description,scientific_property_customizer_form.get_current_field_value("edit_extra_description"))
                    self.assertEqual(scientific_property_customizer.extra_description,scientific_property_customizer_form.get_current_field_value("extra_description"))
                    self.assertEqual(scientific_property_customizer.display_extra_units,scientific_property_customizer_form.get_current_field_value("display_extra_units"))
                    self.assertEqual(scientific_property_customizer.edit_extra_units,scientific_property_customizer_form.get_current_field_value("edit_extra_units"))
                    self.assertEqual(scientific_property_customizer.extra_units,scientific_property_customizer_form.get_current_field_value("extra_units"))

                    # fk fields are compared via primary keys
                    self.assertEqual(scientific_property_customizer.proxy.pk,scientific_property_customizer_form.get_current_field_value("proxy"))

                    # and the category field is a one-off (changed from a fk to a charfield)
                    self.assertEqual(scientific_property_customizer.category.key,scientific_property_customizer_form.get_current_field_value("category"))

                    if not is_enumeration:
                        # atomic fields will only be set to something useful if is_enumeration is false

                        self.assertEqual(scientific_property_customizer.atomic_type,scientific_property_customizer_form.get_current_field_value("atomic_type"))
                        self.assertEqual(scientific_property_customizer.atomic_default,scientific_property_customizer_form.get_current_field_value("atomic_default"))

                    else:
                        # enumeration fields will only be set to something useful if is_enumeration is false
                        current_enumeration_choices = scientific_property_customizer.enumeration_choices
                        if current_enumeration_choices:
                            current_enumeration_choices = current_enumeration_choices.split("|")
                        current_enumeration_default = scientific_property_customizer.enumeration_default
                        if current_enumeration_default:
                            current_enumeration_default = current_enumeration_default.split("|")

                        self.assertEqual(current_enumeration_choices,scientific_property_customizer_form.get_current_field_value("enumeration_choices"))
                        self.assertEqual(current_enumeration_default,scientific_property_customizer_form.get_current_field_value("enumeration_default"))
                        self.assertEqual(scientific_property_customizer.enumeration_open,scientific_property_customizer_form.get_current_field_value("enumeration_open"))
                        self.assertEqual(scientific_property_customizer.enumeration_multi,scientific_property_customizer_form.get_current_field_value("enumeration_multi"))
                        self.assertEqual(scientific_property_customizer.enumeration_nullable,scientific_property_customizer_form.get_current_field_value("enumeration_nullable"))

                        all_enumeration_choices = scientific_property_customizer.proxy.enumerate_choices()
                        self.assertEqual(all_enumeration_choices,scientific_property_customizer_form.fields["enumeration_choices"].choices)
                        self.assertEqual(all_enumeration_choices,scientific_property_customizer_form.fields["enumeration_choices"].widget.choices)
                        self.assertEqual(all_enumeration_choices,scientific_property_customizer_form.fields["enumeration_default"].choices)
                        self.assertEqual(all_enumeration_choices,scientific_property_customizer_form.fields["enumeration_default"].widget.choices)


    def test_existing_scientific_property_customizer_formsets(self):
        """Test creation of scientific property customizer formsets (using existing customizers)"""

        test_model_name = "modelcomponent"
        model_proxy_to_be_customized = MetadataModelProxy.objects.get(version=self.version,name__iexact=test_model_name)
        vocabularies_to_be_customized = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(self.customizer,vocabularies_to_be_customized)

        self.assertEqual(model_customizer.proxy,model_proxy_to_be_customized)

        (model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets) = \
            create_existing_customizer_forms_from_models(model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers,vocabularies_to_customize=vocabularies_to_be_customized,is_subform=True)

        # now the formsets are created; test away...

        for vocabulary_key,scientific_property_customizer_formset_dict in scientific_property_customizer_formsets.iteritems():
            for component_key,scientific_property_customizer_formset in scientific_property_customizer_formset_dict.iteritems():
                for scientific_property_customizer_form in scientific_property_customizer_formset:

                    # ensure the form has the correct field values based on the corresponding scientific_property_customizer
                    scientific_property_customizer = scientific_property_customizer_form.instance

                    field_type = scientific_property_customizer.field_type
                    is_enumeration = scientific_property_customizer.is_enumeration
                    self.assertEqual(field_type,MetadataFieldTypes.PROPERTY.getType())

                    self.assertEqual(scientific_property_customizer.field_type,scientific_property_customizer_form.get_current_field_value("field_type"))
                    self.assertEqual(scientific_property_customizer.is_enumeration,scientific_property_customizer_form.get_current_field_value("is_enumeration"))

                    self.assertEqual(scientific_property_customizer.name,scientific_property_customizer_form.get_current_field_value("name"))
                    self.assertEqual(scientific_property_customizer.category_name,scientific_property_customizer_form.get_current_field_value("category_name"))
                    self.assertEqual(scientific_property_customizer.order,scientific_property_customizer_form.get_current_field_value("order"))
                    self.assertEqual(scientific_property_customizer.vocabulary_key,scientific_property_customizer_form.get_current_field_value("vocabulary_key"))
                    self.assertEqual(scientific_property_customizer.component_key,scientific_property_customizer_form.get_current_field_value("component_key"))
                    self.assertEqual(scientific_property_customizer.model_key,scientific_property_customizer_form.get_current_field_value("model_key"))
                    self.assertEqual(scientific_property_customizer.displayed,scientific_property_customizer_form.get_current_field_value("displayed"))
                    self.assertEqual(scientific_property_customizer.required,scientific_property_customizer_form.get_current_field_value("required"))
                    self.assertEqual(scientific_property_customizer.editable,scientific_property_customizer_form.get_current_field_value("editable"))
                    self.assertEqual(scientific_property_customizer.unique,scientific_property_customizer_form.get_current_field_value("unique"))
                    self.assertEqual(scientific_property_customizer.verbose_name,scientific_property_customizer_form.get_current_field_value("verbose_name"))
                    self.assertEqual(scientific_property_customizer.default_value,scientific_property_customizer_form.get_current_field_value("default_value"))
                    self.assertEqual(scientific_property_customizer.documentation,scientific_property_customizer_form.get_current_field_value("documentation"))
                    self.assertEqual(scientific_property_customizer.inline_help,scientific_property_customizer_form.get_current_field_value("inline_help"))
                    self.assertEqual(scientific_property_customizer.display_extra_standard_name,scientific_property_customizer_form.get_current_field_value("display_extra_standard_name"))
                    self.assertEqual(scientific_property_customizer.edit_extra_standard_name,scientific_property_customizer_form.get_current_field_value("edit_extra_standard_name"))
                    self.assertEqual(scientific_property_customizer.extra_standard_name,scientific_property_customizer_form.get_current_field_value("extra_standard_name"))
                    self.assertEqual(scientific_property_customizer.display_extra_description,scientific_property_customizer_form.get_current_field_value("display_extra_description"))
                    self.assertEqual(scientific_property_customizer.edit_extra_description,scientific_property_customizer_form.get_current_field_value("edit_extra_description"))
                    self.assertEqual(scientific_property_customizer.extra_description,scientific_property_customizer_form.get_current_field_value("extra_description"))
                    self.assertEqual(scientific_property_customizer.display_extra_units,scientific_property_customizer_form.get_current_field_value("display_extra_units"))
                    self.assertEqual(scientific_property_customizer.edit_extra_units,scientific_property_customizer_form.get_current_field_value("edit_extra_units"))
                    self.assertEqual(scientific_property_customizer.extra_units,scientific_property_customizer_form.get_current_field_value("extra_units"))

                    # fk fields are compared via primary keys
                    self.assertEqual(scientific_property_customizer.proxy.pk,scientific_property_customizer_form.get_current_field_value("proxy"))

                    # and the category field is a one-off (changed from a fk to a charfield)
                    self.assertEqual(scientific_property_customizer.category.key,scientific_property_customizer_form.get_current_field_value("category"))

                    if not is_enumeration:
                        # atomic fields will only be set to something useful if is_enumeration is false

                        self.assertEqual(scientific_property_customizer.atomic_type,scientific_property_customizer_form.get_current_field_value("atomic_type"))
                        self.assertEqual(scientific_property_customizer.atomic_default,scientific_property_customizer_form.get_current_field_value("atomic_default"))

                    else:
                        # enumeration fields will only be set to something useful if is_enumeration is false
                        current_enumeration_choices = scientific_property_customizer.enumeration_choices
                        if current_enumeration_choices:
                            current_enumeration_choices = current_enumeration_choices.split("|")
                        current_enumeration_default = scientific_property_customizer.enumeration_default
                        if current_enumeration_default:
                            current_enumeration_default = current_enumeration_default.split("|")
                        self.assertEqual(current_enumeration_choices,scientific_property_customizer_form.get_current_field_value("enumeration_choices"))
                        self.assertEqual(current_enumeration_default,scientific_property_customizer_form.get_current_field_value("enumeration_default"))
                        self.assertEqual(scientific_property_customizer.enumeration_open,scientific_property_customizer_form.get_current_field_value("enumeration_open"))
                        self.assertEqual(scientific_property_customizer.enumeration_multi,scientific_property_customizer_form.get_current_field_value("enumeration_multi"))
                        self.assertEqual(scientific_property_customizer.enumeration_nullable,scientific_property_customizer_form.get_current_field_value("enumeration_nullable"))

                        all_enumeration_choices = scientific_property_customizer.proxy.enumerate_choices()
                        self.assertEqual(all_enumeration_choices,scientific_property_customizer_form.fields["enumeration_choices"].choices)
                        self.assertEqual(all_enumeration_choices,scientific_property_customizer_form.fields["enumeration_choices"].widget.choices)
                        self.assertEqual(all_enumeration_choices,scientific_property_customizer_form.fields["enumeration_default"].choices)
                        self.assertEqual(all_enumeration_choices,scientific_property_customizer_form.fields["enumeration_default"].widget.choices)

    def test_new_customizer_forms_validity(self):
        """Test creation of scientific property customizer formsets (using new customizers)"""

        test_model_name = "modelcomponent"
        model_proxy_to_be_customized = MetadataModelProxy.objects.get(version=self.version,name__iexact=test_model_name)
        vocabularies_to_be_customized = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_new_customizer_set(self.project,self.version,model_proxy_to_be_customized,vocabularies_to_be_customized)

        self.assertEqual(model_customizer.proxy,model_proxy_to_be_customized)

        (model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets) = \
            create_new_customizer_forms_from_models(model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers,vocabularies_to_customize=vocabularies_to_be_customized)

        data = get_data_from_customizer_forms(model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets)
        # add some one-off entries that would normally be done in the interface...
        model_customizer_form_prefix = model_customizer_form.prefix
        if model_customizer_form_prefix:
            data[model_customizer_form_prefix + "-name"] = "new_test_customizer"
            data[model_customizer_form_prefix + "-vocabularies"] = [vocabulary.pk for vocabulary in model_customizer_form.get_current_field_value("vocabularies")]
        else:
            data["name"] = "new_test_customizer"
            data["vocabularies"] = [vocabulary.pk for vocabulary in model_customizer_form.get_current_field_value("vocabularies")]

        # now pass that data back to the forms as if a POST ocurred

        (validity,model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets) = \
            create_customizer_forms_from_data(data,model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers,vocabularies_to_customize=vocabularies_to_be_customized)

        import ipdb; ipdb.set_trace()

