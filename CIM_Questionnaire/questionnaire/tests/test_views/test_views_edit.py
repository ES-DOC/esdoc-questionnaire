import re
from CIM_Questionnaire.questionnaire.models import MetadataModel
from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.views.views_edit import questionnaire_edit_new


class Test(TestQuestionnaireBase):

    def get_request_url(self):
        """Return a URL suitable for client and factory testing."""

        project_name = "test"
        version_name = "test"
        model_name = "modelcomponent"

        request_url = u"/%s/edit/%s/%s/" % (project_name,version_name,model_name)
        return request_url

    def test_questionnaire_edit_new_get(self):
        project_name = "test"
        version_name = "test"
        model_name = "modelcomponent"

        request_url = u"/%s/edit/%s/%s/" % (project_name,version_name,model_name)
        response = self.client.get(request_url)

        self.assertEqual(response.status_code,200)

    def test_questionnaire_edit_new_post(self):
        project_name = "test"
        version_name = "test"
        model_name = "modelcomponent"

        (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            self.get_questionnaire_edit_forms(project_name, version_name, model_name)

        post_data = {}

        # get data from model_formset
        for (i,model_form) in enumerate(model_formset.forms):
            for key,value in model_form.initial.iteritems():
                # only use fields that would be displayed in the template...
                if key in model_form._header_fields or key in model_form._hidden_fields:
                    post_data[u"%s-%s" % (model_form.prefix,key)] = value
        for key,value in model_formset.management_form.initial.iteritems():
            post_data[u"%s-%s"%(model_formset.prefix,key)] = value

        # get data from standard_properties_formsets
        for form_prefix,standard_properties_formset in standard_properties_formsets.iteritems():
            for (i,standard_property_form) in enumerate(standard_properties_formset):
                customizer = standard_property_form.customizer
                for key,value in standard_property_form.initial.iteritems():
                    # only use fields that would be displayed in the template...
                    if key in standard_property_form._hidden_fields or key==standard_property_form.get_value_field_name() or (customizer.enumeration_open and key=="enumeration_other_value"):
                        post_data[u"%s-%s" % (standard_property_form.prefix,key)] = value
            for key,value in standard_properties_formset.management_form.initial.iteritems():
                post_data[u"%s-%s"%(standard_properties_formset.prefix,key)] = value

        # get data from scientific_properties_formsets
        for form_prefix,scientific_properties_formset in scientific_properties_formsets.iteritems():
            for (i,scientific_property_form) in enumerate(scientific_properties_formset):
                for key,value in scientific_property_form.initial.iteritems():
                    # only use fields that would be displayed in the template...
                    # TODO: DEAL W/ "property_extra_fields"
                    if key in scientific_property_form._hidden_fields or key==scientific_property_form.get_value_field_name() or (customizer.enumeration_open and key=="enumeration_other_value"):
                       post_data[u"%s-%s" % (scientific_property_form.prefix,key)] = value
            for key,value in scientific_properties_formset.management_form.initial.iteritems():
                post_data[u"%s-%s"%(scientific_properties_formset.prefix,key)] = value


        request_url = u"/%s/edit/%s/%s/" % (project_name,version_name,model_name)
        response = self.client.post(request_url,post_data)

        self.assertEqual(response.status_code,302)

        post_content = response.content

        expr = "test_atmoshorizontaldomain_scientific_properties-[0-9]-is_enumeration"

        ## ensure data is actually saved to the database
        mm = MetadataModel.objects.all()
        ## the test controlled vocabulary has 12 components plus the parent component
        self.assertEqual(len(mm), 13)
        ## the test version of the CIM has defined 8 standard properties
        for obj in mm:
            self.assertEqual(len(obj.standard_properties.all()), 8)
        self.assertEqual(mm[7].standard_properties.all()[3].name, u'description')
        ## these are the counts of scientific properties associated with each component of the metadata models
        self.assertEqual([len(m.scientific_properties.all()) for m in mm],
                         [0, 0, 3, 4, 6, 10, 10, 8, 10, 13, 7, 12, 13])
        self.assertEqual([m.component_key for m in mm], [u'rootcomponent', u'atmosphere', u'atmoskeyproperties', u'topofatmosinsolation', u'atmosspaceconfiguration', u'atmoshorizontaldomain', u'atmosdynamicalcore', u'atmosadvection', u'atmosradiation', u'atmosconvectturbulcloud', u'atmoscloudscheme', u'cloudsimulator', u'atmosorographyandwaves'])
        self.assertEqual(mm[8].scientific_properties.all()[5].name, u'AerosolTypes')

    def test_questionnaire_edit_new_with_existing_realizations_from_db(self):

        project_name = "test"
        version_name = "test"
        model_name = "modelcomponent"

        model_realization1 = self.create_model_realization_from_db(project_name,version_name,model_name)
        self.assertEqual(len(MetadataModel.objects.all()),13)
        model_realizations1 = model_realization1.get_descendants(include_self=True)
        self.assertEqual(len(model_realizations1),13)

        model_realization2 = self.create_model_realization_from_db(project_name,version_name,model_name)
        self.assertEqual(len(MetadataModel.objects.all()),26)
        model_realizations2 = model_realization2.get_descendants(include_self=True)
        self.assertEqual(len(model_realizations2),13)

    def test_questionnaire_edit_new_with_existing_realizations_from_forms(self):

        project_name = "test"
        version_name = "test"
        model_name = "modelcomponent"

        model_realization1 = self.create_model_realization_from_forms(project_name,version_name,model_name)
        self.assertEqual(len(MetadataModel.objects.all()),13)
        model_realizations1 = model_realization1.get_descendants(include_self=True)
        self.assertEqual(len(model_realizations1),13)

        model_realization2 = self.create_model_realization_from_forms(project_name,version_name,model_name)
        self.assertEqual(len(MetadataModel.objects.all()),26)
        model_realizations2 = model_realization2.get_descendants(include_self=True)
        self.assertEqual(len(model_realizations2),13)

    def test_questionnaire_edit_new_with_existing_realizations_from_view(self):

        project_name = "test"
        version_name = "test"
        model_name = "modelcomponent"

        model_realization1 = self.create_model_realization_from_view(project_name,version_name,model_name)
        self.assertEqual(len(MetadataModel.objects.all()),13)
        model_realizations1 = model_realization1.get_descendants(include_self=True)
        self.assertEqual(len(model_realizations1),13)

        model_realization2 = self.create_model_realization_from_view(project_name,version_name,model_name)
        self.assertEqual(len(MetadataModel.objects.all()),26)
        model_realizations2 = model_realization2.get_descendants(include_self=True)
        self.assertEqual(len(model_realizations2),13)
