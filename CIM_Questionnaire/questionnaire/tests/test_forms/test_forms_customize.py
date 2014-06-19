from django.template.defaultfilters import slugify

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.models import MetadataModelProxy
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer
from CIM_Questionnaire.questionnaire.forms.forms_customize import create_model_customizer_form_data, create_standard_property_customizer_form_data, create_scientific_property_customizer_form_data
from CIM_Questionnaire.questionnaire.forms.forms_customize import MetadataModelCustomizerForm, MetadataStandardPropertyCustomizerInlineFormSetFactory, MetadataScientificPropertyCustomizerInlineFormSetFactory
from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes

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

    def test_new_model_customizer_forms(self):
        """Test creation of model customizer form (using new customizers)"""

        test_model_name = "modelcomponent"
        model_proxy_to_be_customized = MetadataModelProxy.objects.get(version=self.version,name__iexact=test_model_name)
        vocabularies_to_be_customized = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_new_customizer_set(self.project,self.version,model_proxy_to_be_customized,vocabularies_to_be_customized)

        self.assertEqual(model_customizer.proxy,model_proxy_to_be_customized)


        model_customizer_data = create_model_customizer_form_data(model_customizer,standard_category_customizers,scientific_category_customizers,vocabularies=vocabularies_to_be_customized)
        model_customizer_form = MetadataModelCustomizerForm(initial=model_customizer_data,all_vocabularies=vocabularies_to_be_customized)

        # now the form is created; test away...

        # I AM HERE


    def test_new_standard_property_customizer_formset(self):
        """Test creation of standard property customizer formsets (using new customizers)"""

        test_model_name = "modelcomponent"
        model_proxy_to_be_customized = MetadataModelProxy.objects.get(version=self.version,name__iexact=test_model_name)
        vocabularies_to_be_customized = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_new_customizer_set(self.project,self.version,model_proxy_to_be_customized,vocabularies_to_be_customized)

        self.assertEqual(model_customizer.proxy,model_proxy_to_be_customized)

        standard_property_customizers_data = [
            create_standard_property_customizer_form_data(model_customizer,standard_property_customizer)
            for standard_property_customizer in standard_property_customizers
        ]
        standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance    = model_customizer,
            initial     = standard_property_customizers_data,
            extra       = len(standard_property_customizers_data),
            categories  = standard_category_customizers,
        )

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

        standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance    = model_customizer,
            queryset    = standard_property_customizers,
            # don't pass extra; w/ existing (queryset) models, extra ought to be 0
            #extra       = len(standard_property_customizers),
        )

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

        scientific_property_customizer_formsets = {}
        for vocabulary_key,scientific_property_customizer_dict in scientific_property_customizers.iteritems():
            scientific_property_customizer_formsets[vocabulary_key] = {}
            for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
                scientific_property_customizers_data = [
                    create_scientific_property_customizer_form_data(model_customizer,scientific_property_customizer)
                    for scientific_property_customizer in scientific_property_customizers[vocabulary_key][component_key]
                ]
                scientific_property_customizer_formsets[vocabulary_key][component_key] = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                    instance    = model_customizer,
                    initial     = scientific_property_customizers_data,
                    extra       = len(scientific_property_customizers_data),
                    prefix      = u"%s_%s" % (vocabulary_key,component_key),
                    categories  = scientific_category_customizers[vocabulary_key][component_key],
                )

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

        scientific_property_customizer_formsets = {}
        for vocabulary_key,scientific_property_customizer_dict in scientific_property_customizers.iteritems():
            scientific_property_customizer_formsets[vocabulary_key] = {}
            for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
                scientific_property_customizer_formsets[vocabulary_key][component_key] = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                    instance    = model_customizer,
                    queryset    = scientific_property_customizer_list,
                    # don't pass extra; w/ existing (queryset) models, extra ought to be 0
                    #extra       = len(scientific_property_customizer_list),
                    prefix      = u"%s_%s" % (vocabulary_key,component_key),
                    categories  = scientific_category_customizers[vocabulary_key][component_key],
                )

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
