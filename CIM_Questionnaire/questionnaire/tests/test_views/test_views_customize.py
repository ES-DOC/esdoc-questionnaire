__author__ = 'ben.koziol'

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase

from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy

from CIM_Questionnaire.questionnaire.forms.forms_customize import create_model_customizer_form_data, create_standard_property_customizer_form_data, create_scientific_property_customizer_form_data
from CIM_Questionnaire.questionnaire.forms.forms_customize import MetadataModelCustomizerForm, MetadataStandardPropertyCustomizerInlineFormSetFactory, MetadataScientificPropertyCustomizerInlineFormSetFactory
from CIM_Questionnaire.questionnaire.views.views_customize import questionnaire_customize_new, questionnaire_customize_existing, questionnaire_customize_help
from CIM_Questionnaire.questionnaire.views.views_customize import validate_view_arguments

from CIM_Questionnaire.questionnaire.utils import QuestionnaireError

class Test(TestQuestionnaireBase):

    def get_request_url(self,project_name="test",version_name="test",model_name="test"):
        """Return a URL suitable for client and factory testing."""

        request_url = u"/%s/customize/%s/%s/" % (project_name,version_name,model_name)
        return request_url

    def test_validate_view_arguments(self):

        kwargs = {
            "project_name" : "test",
            "version_name" : "test",
            "model_name" : "modelcomponent",
        }

        validate_view_arguments(**kwargs)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"project_name":"invalid"})
        invalid_response = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(invalid_response.status_code,400)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"version_name":"invalid"})
        invalid_response = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(invalid_response.status_code,400)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"model_name":"invalid"})
        invalid_response = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(invalid_response.status_code,400)


    def test_questionnaire_customize_help_get(self):

        request_url = u"/customize/help"
        response = self.client.get(request_url)

        self.assertEqual(response.status_code,200)


    def test_questionnaire_customize_help_post(self):

        request_url = u"/customize/help"
        response = self.client.post(request_url,{})

        self.assertEqual(response.status_code,200)

    def test_questionnaire_customize_new_get(self):

        project_name = "test"
        version_name = "test"
        model_name = "modelcomponent"

        request_url = self.get_request_url(project_name=project_name,version_name=version_name,model_name=model_name)
        response = self.client.get(request_url)

        self.assertEqual(response.status_code,200)

    def test_questionnaire_customize_new_post(self):

        test_model_name = "modelcomponent"
        model_proxy_to_be_customized = MetadataModelProxy.objects.get(version=self.version,name__iexact=test_model_name)
        vocabularies_to_be_customized = self.project.vocabularies.filter(document_type__iexact=self.customizer.proxy.name)
        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_new_customizer_set(self.project,self.version,model_proxy_to_be_customized,vocabularies_to_be_customized)

        self.assertEqual(model_customizer.proxy,model_proxy_to_be_customized)

        additional_model_customizer_test_parameters = {
            "name" : "new_test",
            "default" : False,
        }
        model_customizer_data = create_model_customizer_form_data(model_customizer,standard_category_customizers,scientific_category_customizers,vocabularies=vocabularies_to_be_customized)
        model_customizer_data.update(additional_model_customizer_test_parameters)
        model_customizer_form = MetadataModelCustomizerForm(initial=model_customizer_data,all_vocabularies=vocabularies_to_be_customized)

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

        post_data = {}

        for field_name,field in model_customizer_form.fields.iteritems():
            # the model_customizer_form has no prefix!
            #field_key = u"%s-%s" % (model_customizer_form.prefix,field_name)
            field_key = u"%s" % (field_name)
            field_value = model_customizer_form.initial[field_name]
            post_data[field_key] = field_value
        # this is a one-off; the template uses pks for select widgets...
        post_data["vocabularies"] = [vocabulary.pk for vocabulary in model_customizer_form.get_current_field_value("vocabularies")]

        for standard_property_customizer_form in standard_property_customizer_formset:
            for field_name,field in standard_property_customizer_form.fields.iteritems():
                field_key = u"%s-%s" % (standard_property_customizer_form.prefix,field_name)
                field_value = standard_property_customizer_form.initial[field_name]
                post_data[field_key] = field_value
        post_data[u"%s-TOTAL_FORMS"%(standard_property_customizer_formset.prefix)] = standard_property_customizer_formset.number_of_properties
        post_data[u"%s-INITIAL_FORMS"%(standard_property_customizer_formset.prefix)] = standard_property_customizer_formset.extra

        for vocabulary_key,scientific_property_customizer_formset_dict in scientific_property_customizer_formsets.iteritems():
            for component_key,scientific_property_customizer_formset in scientific_property_customizer_formset_dict.iteritems():
                for scientific_property_customizer_form in scientific_property_customizer_formset:
                    for field_name,field in scientific_property_customizer_form.fields.iteritems():
                        field_key = u"%s-%s" % (scientific_property_customizer_form.prefix,field_name)
                        field_value = scientific_property_customizer_form.initial[field_name]
                        post_data[field_key] = field_value
            post_data[u"%s-TOTAL_FORMS"%(scientific_property_customizer_formset.prefix)] = scientific_property_customizer_formset.number_of_properties
            post_data[u"%s-INITIAL_FORMS"%(scientific_property_customizer_formset.prefix)] = scientific_property_customizer_formset.extra

        import ipdb; ipdb.set_trace()
        request_url = self.get_request_url(project_name=self.project.name,version_name=self.version.name,model_name=test_model_name)
        response = self.client.post(request_url,post_data)

        import ipdb; ipdb.set_trace()
