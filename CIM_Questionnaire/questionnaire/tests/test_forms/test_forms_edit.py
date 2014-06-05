from django.template.defaultfilters import slugify
from CIM_Questionnaire.questionnaire.forms.forms_edit import create_model_form_data, create_standard_property_form_data, \
    create_scientific_property_form_data, MetadataModelFormSetFactory, MetadataStandardPropertyInlineFormSetFactory, \
    MetadataScientificPropertyInlineFormSetFactory
from CIM_Questionnaire.questionnaire.models import MetadataProject, MetadataVersion, MetadataModelProxy, \
    MetadataModelCustomizer, MetadataScientificPropertyCustomizer, MetadataModel, MetadataStandardProperty, \
    MetadataScientificProperty
from CIM_Questionnaire.questionnaire.models.metadata_model import create_models_from_components
from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase
from CIM_Questionnaire.questionnaire.utils import DEFAULT_VOCABULARY


class Test(TestQuestionnaireBase):

    # def test_questionnaire_edit_form_get(self):
    #     pass

    def test_questionnaire_edit_form_post(self):
        """Test creation of realizations via form objects."""

        project_name = "test"
        version_name = "test"
        model_name = "modelcomponent"

        project = MetadataProject.objects.get(name=project_name)
        version = MetadataVersion.objects.get(name=version_name)

        model_proxy = MetadataModelProxy.objects.get(version=version,name__iexact=model_name)

        model_customizer = MetadataModelCustomizer.objects.get(project=project,version=version,proxy=model_proxy,default=True)

        vocabularies     = model_customizer.vocabularies.all()
        vocabulary_order = [int(order) for order in model_customizer.vocabulary_order.split(',')]
        vocabularies     = sorted(vocabularies,key=lambda vocabulary: vocabulary_order.index(vocabulary.pk))

        standard_property_customizers = model_customizer.standard_property_customizers.all()
        standard_property_proxies     = sorted(model_proxy.standard_properties.all(),key=lambda proxy: standard_property_customizers.get(proxy=proxy).order)

        scientific_property_customizers = {}
        scientific_property_proxies = {}
        for vocabulary in vocabularies:
            vocabulary_key = slugify(vocabulary.name)
            for component_proxy in vocabulary.component_proxies.all():
                component_key = slugify(component_proxy.name)
                model_key = u"%s_%s" % (vocabulary_key,component_key)
                scientific_property_customizers[model_key] = MetadataScientificPropertyCustomizer.objects.filter(model_customizer=model_customizer,model_key=model_key)
                scientific_property_proxies[model_key] = sorted(component_proxy.scientific_properties.all(),key=lambda proxy: scientific_property_customizers[model_key].get(proxy=proxy).order)

        # setup the models

        model_parameters = {
            "project" : project,
            "version" : version,
            "proxy"   : model_proxy,
        }

        model = MetadataModel(**model_parameters)
        model.is_root = True

        models = []
        models.append(model)
        if model_customizer.model_show_hierarchy:
            model.title           = model_customizer.model_root_component
            model.vocabulary_key  = slugify(DEFAULT_VOCABULARY)
            model.component_key   = slugify(model_customizer.model_root_component)

            for vocabulary in vocabularies:
                model_parameters["vocabulary_key"] = slugify(vocabulary.name)
                components = vocabulary.component_proxies.all()
                if components:
                    # recursively go through the components of each vocabulary
                    # adding corresponding models to the list
                    root_component = components[0].get_root()
                    model_parameters["parent"] = model
                    model_parameters["title"] = u"%s : %s" % (vocabulary.name,root_component.name)
                    create_models_from_components(root_component,model_parameters,models)

        standard_properties = {}
        standard_property_parameters = {}
        scientific_properties = {}
        scientific_property_parameters = {}
        for model in models:
            model.reset(True)
            vocabulary_key  = model.vocabulary_key
            component_key   = model.component_key
            model_key       = u"%s_%s"%(model.vocabulary_key,model.component_key)

            # setup the standard properties
            standard_properties[model_key] = []
            standard_property_parameters["model"] = model
            for standard_property_proxy in standard_property_proxies:
                standard_property_parameters["proxy"] = standard_property_proxy
                standard_property = MetadataStandardProperty(**standard_property_parameters)
                standard_property.reset()
                standard_properties[model_key].append(standard_property)

            # setup the scientific properties
            scientific_properties[model_key] = []
            scientific_property_parameters["model"] = model
            try:
                for scientific_property_proxy in scientific_property_proxies[model_key]:
                    scientific_property_parameters["proxy"] = scientific_property_proxy
                    scientific_property = MetadataScientificProperty(**scientific_property_parameters)
                    scientific_property.reset()
                    scientific_properties[model_key].append(scientific_property)
            except KeyError:
                # if there were no proxies that just means that this component had no properties;
                # that's okay...
                # but be sure to add an empty set of customizers to pass to the create_scientific_property_form_data fn
                scientific_property_customizers[model_key] = []
                pass

        # setup the forms data

        post_data = {}

        models_data = [create_model_form_data(model,model_customizer) for model in models]
        model_formset_prefix = "form"
        for (i,model_data) in enumerate(models_data):
            model_form_prefix = u"%s_%s" % (model_data["vocabulary_key"],model_data["component_key"])
            for key in model_data.keys():
                # EACH FORM IN THE FOMRSET IS GIVEN A DIFFERENT EXPLICIT PREFIX
                # (IN THE _construct_form FN of MetadataModelFormSet)
                # THEREFORE, I DON'T NEED TO INCLUDE THE NUMBER OF THE FORM (i) IN THE KEY
                #model_data[u"%s-%s-%s"%(model_form_prefix,i,key)] = model_data.pop(key)
                model_data[u"%s-%s"%(model_form_prefix,key)] = model_data.pop(key)
        map(lambda model_data: post_data.update(model_data),models_data)
        post_data[u"%s-TOTAL_FORMS"%(model_formset_prefix)] = len(models)
        post_data[u"%s-INITIAL_FORMS"%(model_formset_prefix)] = 0

        for model in models:
            model_key = u"%s_%s" % (model.vocabulary_key,model.component_key)

            standard_properties_data = [
                create_standard_property_form_data(model,standard_property,standard_property_customizer)
                for standard_property,standard_property_customizer in zip(standard_properties[model_key],standard_property_customizers)
            ]
            for (i,standard_property_data) in enumerate(standard_properties_data):
                for key in standard_property_data.keys():
                    standard_property_data[u"%s_standard_properties-%s-%s" % (model_key,i,key)] = standard_property_data.pop(key)
            map(lambda standard_property_data: post_data.update(standard_property_data),standard_properties_data)
            post_data[u"%s_standard_properties-TOTAL_FORMS"%(model_key)] = len(standard_properties[model_key])
            post_data[u"%s_standard_properties-INITIAL_FORMS"%(model_key)] = 0

            scientific_properties_data = [
                create_scientific_property_form_data(model,scientific_property,scientific_property_customizer)
                for scientific_property,scientific_property_customizer in zip(scientific_properties[model_key],scientific_property_customizers[model_key])
            ]
            for (i,scientific_property_data) in enumerate(scientific_properties_data):
                for key in scientific_property_data.keys():
                    scientific_property_data[u"%s_scientific_properties-%s-%s" % (model_key,i,key)] = scientific_property_data.pop(key)
            map(lambda scientific_property_data: post_data.update(scientific_property_data),scientific_properties_data)
            post_data[u"%s_scientific_properties-TOTAL_FORMS"%(model_key)] = len(scientific_properties[model_key])
            post_data[u"%s_scientific_properties-INITIAL_FORMS"%(model_key)] = 0

        # setup the forms

        request_url = u"/%s/customize/%s/%s" % (project_name,version_name,model_name)
        request = self.factory.post(request_url,post_data)
        # fix the POST dictionary (u"None" -> None)
        # TODO: EVENTUALLY SOLVE THIS PROBLEM MORE ELEGANTLY
        for (key,value) in request.POST.iteritems():
            if value == u"None":
                request.POST[key] = None

        model_formset = MetadataModelFormSetFactory(
            request = request,
            prefixes    = [u"%s_%s"%(model.vocabulary_key,model.component_key) for model in models],
            customizer  = model_customizer,
        )
        self.assertEqual(model_formset.is_valid(),True)
        model_instances = model_formset.save(commit=False)

        standard_property_formsets = {}
        scientific_property_formsets = {}
        for model_instance in model_instances:
            model_key = u"%s_%s" % (model_instance.vocabulary_key,model_instance.component_key)

            standard_property_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
                instance    = model_instance,
                prefix      = model_key,
                request     = request,
                customizers = standard_property_customizers
            )
            self.assertEqual(standard_property_formsets[model_key].is_valid(),True)

            scientific_property_formsets[model_key] = MetadataScientificPropertyInlineFormSetFactory(
                instance    = model_instance,
                prefix      = model_key,
                request     = request,
                customizers = scientific_property_customizers[model_key]
            )

        # save the instances

        for model_instance in model_instances:
            model_instance.save()

        for standard_property_formset in standard_property_formsets.values():
            standard_property_instances = standard_property_formset.save(commit=False)
            for standard_property_instance in standard_property_instances:
                standard_property_instance.save()

        for scientific_property_formset in scientific_property_formsets.values():
            scientific_property_instances = scientific_property_formset.save(commit=False)
            for scientific_property_instance in scientific_property_instances:
                scientific_property_instance.save()
