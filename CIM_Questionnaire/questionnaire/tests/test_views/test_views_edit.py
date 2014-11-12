import re

from django.core.urlresolvers import reverse
from django.contrib import messages

from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.views.views_edit import validate_view_arguments, questionnaire_edit_new, questionnaire_edit_existing, questionnaire_edit_help

from CIM_Questionnaire.questionnaire.forms.forms_edit import get_data_from_edit_forms

from CIM_Questionnaire.questionnaire.utils import FuzzyInt, model_to_data, find_in_sequence, get_form_by_field

class Test(TestQuestionnaireBase):

    def test_validate_view_arguments(self):

        kwargs = {
            "project_name" : self.project.name.lower(),
            "version_key" : self.version.get_key(),
            "model_name" : self.model_realization.name.lower(),
        }

        (validity,project,version,model_proxy,model_customizer,msg) = validate_view_arguments(**kwargs)
        self.assertEqual(validity,True)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"project_name":"invalid"})
        (validity,project,version,model_proxy,model_customizer,msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity,False)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"version_key":"invalid"})
        (validity,project,version,model_proxy,model_customizer,msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity,False)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"model_name":"invalid"})
        (validity,project,version,model_proxy,model_customizer,msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity,False)

        invalid_kwargs = kwargs.copy()
        invalid_kwargs.update({"model_name":"responsibleparty"})    # valid classname, but not a document
        (validity,project,version,model_proxy,model_customizer,msg) = validate_view_arguments(**invalid_kwargs)
        self.assertEqual(validity,False)


    def test_questionnaire_edit_help_get(self):

        # wrap all view tests w/ a check for num db hits
        # (django testing framework adds ~15 hits of setup code)
        query_limit = FuzzyInt(0,20)
        with self.assertNumQueries(query_limit):
            request_url = reverse("edit_help")
            response = self.client.get(request_url)

        self.assertEqual(response.status_code,200)

    def test_questionnaire_edit_new_with_subforms_added_subforms(self):

        test_document_type = "modelcomponent"

        test_proxy = MetadataModelProxy.objects.get(version=self.version, name__iexact=test_document_type)

        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)

        properties_with_subforms=[ "author", "contact", ]

        test_customizer = self.create_customizer_set_with_subforms(self.project, self.version, test_proxy, properties_with_subforms=properties_with_subforms)
        self.model_customizer.default = False
        self.model_customizer.save()
        test_customizer.default = True
        test_customizer.save()

        request_url = reverse("edit_new", kwargs = {
            "project_name" : self.project,
            "version_key" : self.version.get_key(),
            "model_name" : test_document_type,
        })

        response = self.client.get(request_url, follow=True)
        context = response.context

        self.assertEqual(response.status_code, 200)

        model_formset = context["model_formset"]
        standard_properties_formsets = context["standard_properties_formsets"]
        scientific_properties_formsets = context["scientific_properties_formsets"]

        original_data = get_data_from_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets, simulate_post=True)

        properties_to_add_subforms_to = ["contact"]
        root_component_key = model_formset.forms[0].prefix
        original_data_with_added_subforms = self.add_subform_to_post_data(original_data, standard_properties_formsets[root_component_key], properties_to_add_subform_to=properties_to_add_subforms_to)

        response = self.client.post(request_url, data=original_data_with_added_subforms, follow=True)
        context = response.context
        session_variables = self.client.session

        self.assertEqual(response.status_code, 200)
        self.assertIn("root_model_id", session_variables)

        model_formset = context["model_formset"]
        standard_properties_formsets = context["standard_properties_formsets"]
        scientific_properties_formsets = context["scientific_properties_formsets"]

        model_id = session_variables["root_model_id"]
        model = MetadataModel.objects.get(pk=model_id)

        # EXPLICITLY TESTING THAT DB HAS THE ADDITIONAL SUBFORM:
        test_submodel_standard_properties_data = [
            {'field_type': u'ATOMIC',       'enumeration_other_value': u'Please enter a custom value', 'name': u'individualName',   'enumeration_value': u'', 'relationship_value': [], 'is_label': True,   'order': 0, 'atomic_value': u''},
            {'field_type': u'RELATIONSHIP', 'enumeration_other_value': u'Please enter a custom value', 'name': u'contactInfo',      'enumeration_value': u'', 'relationship_value': [], 'is_label': False,  'order': 1, 'atomic_value': u''},
        ]
        standard_properties = model.standard_properties.all()
        standard_property_to_test = find_in_sequence(lambda property: property.name in properties_to_add_subforms_to, standard_properties)
        submodels_to_test = standard_property_to_test.relationship_value.all()
        self.assertEqual(len(submodels_to_test), 2)
        for submodel_to_test in submodels_to_test:
            submodel_standard_properties_data = [model_to_data(sp) for sp in submodel_to_test.standard_properties.all()]
            for actual_standard_property_data, test_standard_property_data in zip(submodel_standard_properties_data, test_submodel_standard_properties_data):
                self.assertDictEqual(actual_standard_property_data, test_standard_property_data, excluded_keys=["id", "model", "proxy"])

        # EXPLICITLY TEST THAT FORMS HAVE ADDITIONAL SUBFORM:
        standard_property_form_to_test = get_form_by_field(standard_properties_formsets[root_component_key], "name", properties_to_add_subforms_to[0] )
        self.assertEqual(len(standard_property_form_to_test.get_current_field_value("relationship_value")), 2)

        (subform_customizer, model_subformset, standard_properties_subformsets, scientific_properties_subformsets) = \
            standard_property_form_to_test.get_subform_tuple()

        # AHA! FOUND THE PROBLEM; NEWLY-ADDED ITEMS DO NOT HAVE APPROPRIATE PREFIXES!!!
        # LOOK AT THE KEYS OF standard_properties_subformsets
        # AND CHECK THE PREFIXES OF INDIVIDUAL FORMS
        self.assertEqual(subform_customizer.name, test_customizer.name)


    def test_questionnaire_edit_new_no_component_hierarchy(self):

        test_document_type = "modelcomponent"

        test_vocabularies = self.project.vocabularies.filter(document_type__iexact=test_document_type)

        self.model_customizer.model_show_hierarchy = False
        self.model_customizer.vocabularies = test_vocabularies  # going through forms automatically adds relevant vocabularies when creating a customizer
        self.model_customizer.save()                            # just add them manually here since I'm testing something else

        request_url = reverse("edit_new", kwargs = {
            "project_name" : self.project,
            "version_key" : self.version.get_key(),
            "model_name" : test_document_type,
        })

        response = self.client.get(request_url, follow=True)
        context = response.context

        self.assertEqual(response.status_code, 200)

        n_model_forms = len(context["model_formset"].forms)
        n_components = len(self.vocabulary.component_proxies.all())

        # if model_show_hierarchy was set to True
        # then I would expect n_model_forms to be greater than n_components
        self.assertEqual(n_model_forms, n_components)


