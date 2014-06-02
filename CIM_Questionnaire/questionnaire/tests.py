####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################
import os
import re
from django.forms import model_to_dict
from django.template.defaultfilters import slugify
from questionnaire.forms import MetadataModelFormSetFactory, \
    MetadataStandardPropertyInlineFormSetFactory, MetadataScientificPropertyInlineFormSetFactory, \
    MetadataScientificPropertyCustomizerInlineFormSetFactory, MetadataStandardPropertyCustomizerInlineFormSetFactory, \
    MetadataModelCustomizerForm
from questionnaire.forms.forms_customize import create_standard_property_customizer_form_data, \
    create_scientific_property_customizer_form_data, create_model_customizer_form_data
from questionnaire.forms.forms_edit import create_model_form_data, create_standard_property_form_data, \
    create_scientific_property_form_data
from questionnaire.models import MetadataProject, MetadataVersion, MetadataModelProxy, \
    MetadataModelCustomizer, MetadataScientificPropertyCustomizer, MetadataModel, MetadataStandardProperty, \
    MetadataScientificProperty, MetadataVocabulary, MetadataScientificCategoryProxy, MetadataScientificPropertyProxy, \
    MetadataComponentProxy, MetadataStandardCategoryProxy, MetadataCategorization, MetadataScientificCategoryCustomizer, \
    MetadataStandardPropertyCustomizer, MetadataStandardCategoryCustomizer
from questionnaire.models.metadata_model import create_models_from_components
from questionnaire.models.metadata_version import UPLOAD_PATH as VERSION_UPLOAD_PATH
from questionnaire.models.metadata_categorization import UPLOAD_PATH as CATEGORIZATION_UPLOAD_PATH
from questionnaire.models.metadata_vocabulary import UPLOAD_PATH as VOCABULARY_UPLOAD_PATH
from django.test import TestCase, Client
from django.test.client import RequestFactory
from questionnaire.utils import DEFAULT_VOCABULARY, find_in_sequence
from questionnaire.views.views_edit import questionnaire_edit_new

__author__="allyn.treshansky"
__date__ ="Dec 9, 2013 4:33:11 PM"


class MetadataTest(TestCase):

    # built-in fn takes qs & list, which is confusing
    # this is a more intuitive fn
    # (see https://djangosnippets.org/snippets/2013/)
    def assertQuerysetEqual(self, qs1, qs2):
        pk = lambda o: o.pk
        return self.assertEqual(
            list(sorted(qs1, key=pk)),
            list(sorted(qs2, key=pk))
        )


    def get_questionnaire_edit_forms(self,project_name,version_name,model_name):

        project = MetadataProject.objects.get(name__iexact=project_name)
        version = MetadataVersion.objects.get(name__iexact=version_name,registered=True)
        model_proxy = MetadataModelProxy.objects.get(version=version,name__iexact=model_name)

        model_customizer = MetadataModelCustomizer.objects.get(project=project,version=version,proxy=model_proxy,default=True)

        vocabularies     = model_customizer.vocabularies.all()
        vocabulary_order = [int(order) for order in model_customizer.vocabulary_order.split(',')]
        vocabularies     = sorted(vocabularies,key=lambda vocabulary: vocabulary_order.index(vocabulary.pk))

        standard_property_customizers   = model_customizer.standard_property_customizers.all()
        standard_property_proxies = sorted(model_proxy.standard_properties.all(),key=lambda proxy: standard_property_customizers.get(proxy=proxy).order)
        scientific_property_customizers = {}
        scientific_property_proxies = {}
        for vocabulary in vocabularies:
            vocabulary_key = slugify(vocabulary.name)
            for component_proxy in vocabulary.component_proxies.all():
                component_key = slugify(component_proxy.name)
                model_key = u"%s_%s" % (vocabulary_key,component_key)
                scientific_property_customizers[model_key] = MetadataScientificPropertyCustomizer.objects.filter(model_customizer=model_customizer,model_key=model_key)
                scientific_property_proxies[model_key] = sorted(component_proxy.scientific_properties.all(),key=lambda proxy: scientific_property_customizers[model_key].get(proxy=proxy).order)

        # setup the model(s)...

        model_parameters = {
            "project" : project,
            "version" : version,
            "proxy"   : model_proxy,
        }

        # here is the "root" model
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
                    root_component = components[0].get_root()
                    model_parameters["parent"] = model
                    model_parameters["title"] = u"%s : %s" % (vocabulary.name,root_component.name)
                    create_models_from_components(root_component,model_parameters,models)

        standard_properties     = {}
        standard_property_parameters = {}
        scientific_properties   = {}
        scientific_property_parameters = {}

        for model in models:
            model.reset(True)
            vocabulary_key  = model.vocabulary_key
            component_key   = model.component_key
            model_key       = u"%s_%s"%(model.vocabulary_key,model.component_key)

            # setup the standard properties...
            standard_properties[model_key] = []
            standard_property_parameters["model"] = model
            for standard_property_proxy in standard_property_proxies:
                standard_property_parameters["proxy"] = standard_property_proxy
                standard_property = MetadataStandardProperty(**standard_property_parameters)
                standard_property.reset()
                standard_properties[model_key].append(standard_property)

            # setup the scientific properties...
            scientific_properties[model_key] = []
            scientific_property_parameters["model"] = model
            try:
                for scientific_property_proxy in scientific_property_proxies[model_key]:
                    scientific_property_parameters["proxy"] = scientific_property_proxy
                    scientific_property = MetadataScientificProperty(**scientific_property_parameters)
                    scientific_property.reset()
                    scientific_properties[model_key].append(scientific_property)
            except KeyError:
                # there were no scientific properties associated w/ this component (or, rather, no components associated w/ this vocabulary)
                # that's okay
                # but be sure to add an empty set of customizers to pass to the create_scientific_property_form_data fn
                scientific_property_customizers[model_key] = []

        # passed to formset factories below to make sure the prefixes match up
        model_keys = [u"%s_%s" % (model.vocabulary_key,model.component_key) for model in models]

        models_data = [create_model_form_data(model,model_customizer) for model in models]

        model_formset = MetadataModelFormSetFactory(
            initial     = models_data,
            extra       = len(models_data),
            prefixes    = model_keys,
            customizer  = model_customizer,
        )

        standard_properties_formsets = {}
        scientific_properties_formsets = {}
        for model in models:
            model_key = u"%s_%s" % (model.vocabulary_key,model.component_key)

            standard_properties_data = [
                create_standard_property_form_data(model,standard_property,standard_property_customizer)
                for standard_property,standard_property_customizer in zip(standard_properties[model_key],standard_property_customizers)
                if standard_property_customizer.displayed
            ]

            standard_properties_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
                instance    = model,
                prefix      = model_key,
                initial     = standard_properties_data,
                extra       = len(standard_properties_data),
                customizers = standard_property_customizers,
            )

            scientific_properties_data = [
                create_scientific_property_form_data(model,scientific_property,scientific_property_customizer)
                for scientific_property,scientific_property_customizer in zip(scientific_properties[model_key],scientific_property_customizers[model_key])
                if scientific_property_customizer.displayed
            ]

            scientific_properties_formsets[model_key] = MetadataScientificPropertyInlineFormSetFactory(
                instance    = model,
                prefix      = model_key,
                initial     = scientific_properties_data,
                extra       = len(scientific_properties_data),
                customizers = scientific_property_customizers[model_key],
            )

        return (model_formset,standard_properties_formsets,scientific_properties_formsets)


    def create_customizer_from_forms(self,project_name,model_name,version_name,customizer_name):

        project = MetadataProject.objects.get(name=project_name)
        version = MetadataVersion.objects.get(name=version_name)

        model_proxy = MetadataModelProxy.objects.get(version=version,name__iexact=model_name)

        # TODO: A FUTURE VERSION OF THIS SHOULD TAKE VOCABULARY_NAMES AS AN ARGUMENT
        # SO THAT WE CAN TEST WHEN ONLY SOME (OR NONE) OF THE VOCABS ARE USED
        vocabularies = project.vocabularies.filter(document_type__iexact=model_name)

        # setup the model customizer
        model_customizer = MetadataModelCustomizer(name=customizer_name,project=project,version=version,proxy=model_proxy)
        model_customizer.reset()

        # setup the standard category customizers
        standard_category_customizers = []
        for standard_category_proxy in version.categorization.categories.all():
            standard_category_customizer = MetadataStandardCategoryCustomizer(
                proxy = standard_category_proxy,
                model_customizer = model_customizer,
            )
            standard_category_customizer.reset()
            standard_category_customizers.append(standard_category_customizer)

        # setup the standard property customizers
        standard_property_customizers = []
        for standard_property_proxy in model_proxy.standard_properties.all():
            standard_property_customizer = MetadataStandardPropertyCustomizer(
                model_customizer    = model_customizer,
                proxy               = standard_property_proxy,
                category            = find_in_sequence(lambda category: category.proxy.has_property(standard_property_proxy),standard_category_customizers),
            )
            standard_property_customizer.reset()
            standard_property_customizers.append(standard_property_customizer)

        # setup the scientific category & property customizers
        scientific_category_customizers = {}
        scientific_property_customizers = {}
        for vocabulary in vocabularies:
            vocabulary_key = slugify(vocabulary.name)
            scientific_category_customizers[vocabulary_key] = {}
            scientific_property_customizers[vocabulary_key] = {}
            for component in vocabulary.component_proxies.all():
                component_key = slugify(component.name)
                model_key = u"%s_%s" % (vocabulary_key,component_key)
                scientific_category_customizers[vocabulary_key][component_key] = []
                scientific_property_customizers[vocabulary_key][component_key] = []
                for property in component.scientific_properties.all():
                    if property.category:
                        if property.category.key not in [category.key for category in scientific_category_customizers[vocabulary_key][component_key]]:
                            scientific_category_customizer = MetadataScientificCategoryCustomizer(
                                model_customizer=model_customizer,
                                proxy=property.category,
                                vocabulary_key=vocabulary_key,
                                component_key=component_key,
                                model_key=model_key
                            )
                            scientific_category_customizer.reset()
                            scientific_category_customizers[vocabulary_key][component_key].append(scientific_category_customizer)
                    else:
                        scientific_category_customizer = None

                    scientific_property_customizer = MetadataScientificPropertyCustomizer(
                        model_customizer    = model_customizer,
                        proxy               = property,
                        vocabulary_key      = vocabulary_key,
                        component_key       = component_key,
                        model_key           = model_key,
                        category            = scientific_category_customizer,
                    )
                    scientific_property_customizer.reset()
                    scientific_property_customizers[vocabulary_key][component_key].append(scientific_property_customizer)


        # setup the forms data
        post_data = {}

        model_customizer_data = create_model_customizer_form_data(model_customizer,standard_category_customizers,scientific_category_customizers,vocabularies=vocabularies)
        post_data.update(model_customizer_data)

        standard_property_prefix = "standard_property"
        standard_property_customizers_data = [create_standard_property_customizer_form_data(model_customizer,standard_property_customizer) for standard_property_customizer in standard_property_customizers]
        for (i,standard_property_customizer_data) in enumerate(standard_property_customizers_data):
            for key in standard_property_customizer_data.keys():
                standard_property_customizer_data[u"%s-%s-%s"%(standard_property_prefix,i,key)] = standard_property_customizer_data.pop(key)
        map(lambda standard_property_customizer_data: post_data.update(standard_property_customizer_data),standard_property_customizers_data)
        post_data[u"%s-TOTAL_FORMS"%(standard_property_prefix)] = len(standard_property_customizers)
        post_data[u"%s-INITIAL_FORMS"%(standard_property_prefix)] = 0

        for vocabulary_key,component_dictionary in scientific_property_customizers.iteritems():
            for component_key,scientific_property_list in component_dictionary.iteritems():
                scientific_property_prefix = u"%s_%s" % (vocabulary_key,component_key)
                scientific_property_customizers_data = [create_scientific_property_customizer_form_data(model_customizer,scientific_property_customizer) for scientific_property_customizer in scientific_property_customizers[vocabulary_key][component_key]]
                for (i,scientific_property_customizer_data) in enumerate(scientific_property_customizers_data):
                    for key in scientific_property_customizer_data.keys():
                        scientific_property_customizer_data[u"%s-%s-%s" % (scientific_property_prefix,i,key)] = scientific_property_customizer_data.pop(key)
                map(lambda scientific_property_customizer_data: post_data.update(scientific_property_customizer_data),scientific_property_customizers_data)
                post_data[u"%s-TOTAL_FORMS"%(scientific_property_prefix)] = len(scientific_property_customizers[vocabulary_key][component_key])
                post_data[u"%s-INITIAL_FORMS"%(scientific_property_prefix)] = 0

        # setup/save the forms

        request_url = u"/%s/customize/%s/%s" % (project_name,version_name,model_name)
        request = self.factory.post(request_url,post_data)
        # fix the POST dictionary (u"None" -> None)
        # TODO: EVENTUALLY SOLVE THIS PROBLEM MORE ELEGANTLY
        for (key,value) in request.POST.iteritems():
            if value == u"None":
                request.POST[key] = None

        #model_customizer_form = create_model_customizer_form(model_customizer,request=request)
        model_customizer_form = MetadataModelCustomizerForm(request.POST,all_vocabularies=vocabularies)

        self.assertEqual(model_customizer_form.is_valid(),True)

        active_vocabularies                 = model_customizer_form.cleaned_data["vocabularies"]
        standard_categories_to_process      = model_customizer_form.standard_categories_to_process
        scientific_categories_to_process    = model_customizer_form.scientific_categories_to_process

        model_customizer_instance = model_customizer_form.save(commit=False)

        standard_property_customizers_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance    = model_customizer_instance,
            request     = request,
            categories  = [(category.key,category.name) for category in standard_category_customizers],
        )
        scientific_property_customizer_formsets = {}
        for vocabulary_key,component_dictionary in scientific_property_customizers.iteritems():
            scientific_property_customizer_formsets[vocabulary_key] = {}
            for component_key,scientific_property_customizer_list in component_dictionary.iteritems():
                scientific_property_prefix = u"%s_%s" % (vocabulary_key,component_key)
                scientific_property_category_customizers = [scientific_property_customizer.category for scientific_property_customizer in scientific_property_customizer_list]
                scientific_property_customizer_formsets[vocabulary_key][component_key] = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                    instance    = model_customizer_instance,
                    request     = request,
                    prefix      = scientific_property_prefix,
                    categories  = [(category.key,category.name) for category in scientific_property_category_customizers]
                )


        self.assertEqual(standard_property_customizers_formset.is_valid(),True)

        for vocabulary in active_vocabularies:
            vocabulary_key = slugify(vocabulary.name)
            for component_key,scientific_property_customizer_formset in scientific_property_customizer_formsets[vocabulary_key].iteritems():
                self.assertEqual(scientific_property_customizer_formsets[vocabulary_key][component_key].is_valid(),True)

        # save the instances

        model_customizer_instance.save()
        model_customizer_form.save_m2m()

        active_standard_categories = []
        for standard_category_to_process in standard_categories_to_process:
            standard_category_customizer = standard_category_to_process.object
            if standard_category_customizer.pending_deletion:
                standard_category_to_process.delete()
            else:
                standard_category_customizer.model_customizer = model_customizer_instance
                standard_category_to_process.save()
                active_standard_categories.append(standard_category_customizer)

        standard_property_customizer_instances = standard_property_customizers_formset.save(commit=False)
        for standard_property_customizer_instance in standard_property_customizer_instances:
            category_key = slugify(standard_property_customizer_instance.category_name)
            category = find_in_sequence(lambda category: category.key==category_key,active_standard_categories)
            standard_property_customizer_instance.category = category
            standard_property_customizer_instance.save()

        active_scientific_categories = {}
        for (vocabulary_key,component_dictionary) in scientific_categories_to_process.iteritems():
            active_scientific_categories[vocabulary_key] = {}
            for (component_key,scientific_categories_to_process) in component_dictionary.iteritems():
                active_scientific_categories[vocabulary_key][component_key] = []
                for scientific_category_to_process in scientific_categories_to_process:
                    scientific_category_customizer = scientific_category_to_process.object
                    if scientific_category_customizer.pending_deletion:
                        scientific_category_to_process.delete()
                    else:
                        scientific_category_customizer.model_customizer = model_customizer_instance
                        scientific_category_customizer.component_key    = component_key
                        scientific_category_customizer.vocabulary_key   = vocabulary_key
                        scientific_category_customizer.model_key        = u"%s_%s" % (vocabulary_key,component_key)
                        scientific_category_to_process.save()
                        active_scientific_categories[vocabulary_key][component_key].append(scientific_category_customizer)

        for (vocabulary_key,component_dictionary) in scientific_property_customizer_formsets.iteritems():
            if find_in_sequence(lambda vocabulary: slugify(vocabulary.name)==vocabulary_key,active_vocabularies):
                for (component_key,scientific_property_customizer_formset) in component_dictionary.iteritems():
                    scientific_property_customizer_instances = scientific_property_customizer_formset.save(commit=False)
                    for scientific_property_customizer_instance in scientific_property_customizer_instances:
                        category_key = slugify(scientific_property_customizer_instance.category_name)
                        category = find_in_sequence(lambda category: category.key==category_key,active_scientific_categories[vocabulary_key][component_key])
                        scientific_property_customizer_instance.category = category
                        scientific_property_customizer_instance.save()

        # check that the customizers are bound to the correct proxies...
        self.assertEqual(model_customizer_instance.proxy,model_proxy)
        for standard_property_instance in model_customizer_instance.standard_property_customizers.all():
            self.assertEqual(standard_property_instance.name,standard_property_instance.proxy.name)
        for scientific_property_instance in model_customizer_instance.scientific_property_customizers.all():
            self.assertEqual(scientific_property_instance.name,scientific_property_instance.proxy.name)

        return model_customizer_instance

    def create_customizer_from_db(self,project_name,model_name,version_name,customizer_name):

        project = MetadataProject.objects.get(name=project_name)
        version = MetadataVersion.objects.get(name=version_name)

        model_proxy = MetadataModelProxy.objects.get(version=version,name__iexact=model_name)

        # TODO: A FUTURE VERSION OF THIS SHOULD TAKE VOCABULARY_NAMES AS AN ARGUMENT
        # SO THAT WE CAN TEST WHEN ONLY SOME (OR NONE) OF THE VOCABS ARE USED
        vocabularies = project.vocabularies.filter(document_type__iexact=model_name)

        # setup the model customizer
        model_customizer = MetadataModelCustomizer(name=customizer_name,project=project,version=version,proxy=model_proxy)
        model_customizer.reset()
        model_customizer.save()
        # TODO: FACTOR THESE NEXT 3 LINES OUT OF THE FORM INIT METHOD
        model_customizer.vocabularies = vocabularies
        model_customizer.vocabulary_order = ",".join([str(vocabulary.pk) for vocabulary in vocabularies])
        model_customizer.save()

        # setup the standard category customizers
        standard_category_customizers = []
        for standard_category_proxy in version.categorization.categories.all():
            standard_category_customizer = MetadataStandardCategoryCustomizer(
                proxy = standard_category_proxy,
                model_customizer = model_customizer,
            )
            standard_category_customizer.reset()
            standard_category_customizer.save()
            standard_category_customizers.append(standard_category_customizer)

        # setup the standard property customizers
        for standard_property_proxy in model_proxy.standard_properties.all():
            standard_property_customizer = MetadataStandardPropertyCustomizer(
                model_customizer    = model_customizer,
                proxy               = standard_property_proxy,
                category            = find_in_sequence(lambda category: category.proxy.has_property(standard_property_proxy),standard_category_customizers),
            )

            standard_property_customizer.reset()
            standard_property_customizer.save()

        # create scientific category & property customizers
        for vocabulary in vocabularies:
            vocabulary_key = slugify(vocabulary.name)
            for component in vocabulary.component_proxies.all():
                component_key = slugify(component.name)
                model_key = u"%s_%s" % (vocabulary_key,component_key)
                for property in component.scientific_properties.all():
                    if property.category:
                        (scientific_category_customizer,created) = MetadataScientificCategoryCustomizer.objects.get_or_create(
                            model_customizer=model_customizer,
                            proxy=property.category,
                            vocabulary_key=vocabulary_key,
                            component_key=component_key,
                            model_key=u"%s_%s" % (vocabulary_key,component_key)
                        )
                        if created:
                            scientific_category_customizer.reset()
                            scientific_category_customizer.save()
                    else:
                        scientific_category_customizer = None

                    scientific_property_customizer = MetadataScientificPropertyCustomizer(
                        model_customizer    = model_customizer,
                        proxy               = property,
                        vocabulary_key      = vocabulary_key,
                        component_key       = component_key,
                        model_key           = model_key,
                        category = scientific_category_customizer,
                    )
                    scientific_property_customizer.reset()
                    scientific_property_customizer.save()

        return model_customizer

    def create_model_realization(self,project_name,version_name,model_name):

        project = MetadataProject.objects.get(name__iexact=project_name,active=True)
        version = MetadataVersion.objects.get(name__iexact=version_name,registered=True)
        model_proxy = MetadataModelProxy.objects.get(version=version,name__iexact=model_name)

        self.assertEqual(model_proxy.is_document(),True)

        model_customizer = MetadataModelCustomizer.objects.get(project=project,version=version,proxy=model_proxy,default=True)

        vocabularies = model_customizer.vocabularies.all()

        standard_property_customizers = model_customizer.standard_property_customizers.all().order_by("category__order","order")
        standard_property_proxies = [standard_property_customizer.proxy for standard_property_customizer in standard_property_customizers]

        scientific_property_customizers = {}
        scientific_property_proxies = {}
        for vocabulary in vocabularies:
            vocabulary_key = slugify(vocabulary.name)
            for component_proxy in vocabulary.component_proxies.all():
                component_key = slugify(component_proxy.name)
                model_key = u"%s_%s" % (vocabulary_key, component_key)
                scientific_property_customizers[model_key] = MetadataScientificPropertyCustomizer.objects.filter(model_customizer=model_customizer, model_key=model_key).order_by("category__order","order")
                scientific_property_proxies[model_key] = [scientific_property_customizer.proxy for scientific_property_customizer in scientific_property_customizers[model_key]]

        model_parameters = {
            "project": project,
            "version": version,
            "proxy": model_proxy,
        }

        model = MetadataModel(**model_parameters)
        model.is_root = True

        models = []
        models.append(model)
        if model_customizer.model_show_hierarchy:
            model.title = model_customizer.model_root_component
            model.vocabulary_key = slugify(DEFAULT_VOCABULARY)
            model.component_key = slugify(model_customizer.model_root_component)

            for vocabulary in vocabularies:
                model_parameters["vocabulary_key"] = slugify(vocabulary.name)
                components = vocabulary.component_proxies.all()
                if components:
                    # recursively go through the components of each vocabulary
                    # adding corresponding models to the list
                    root_component = components[0].get_root()
                    model_parameters["parent"] = model
                    model_parameters["title"] = u"%s : %s" % (vocabulary.name, root_component.name)
                    create_models_from_components(root_component, model_parameters, models)

        standard_properties = {}
        standard_property_parameters = {}
        scientific_properties = {}
        scientific_property_parameters = { }
        for model in models:
            model.reset(True)

            model_key = u"%s_%s" % (model.vocabulary_key, model.component_key)

            # setup the standard properties...
            standard_properties[model_key] = []
            standard_property_parameters["model"] = model
            for standard_property_proxy in standard_property_proxies:
                standard_property_parameters["proxy"] = standard_property_proxy
                standard_property = MetadataStandardProperty(**standard_property_parameters)
                standard_property.reset()
                standard_properties[model_key].append(standard_property)

            # setup the scientific properties...
            scientific_properties[model_key] = []
            scientific_property_parameters["model"] = model
            try:
                for scientific_property_proxy in scientific_property_proxies[model_key]:
                    scientific_property_parameters["proxy"] = scientific_property_proxy
                    scientific_property = MetadataScientificProperty(**scientific_property_parameters)
                    scientific_property.reset()
                    scientific_properties[model_key].append(scientific_property)
            except KeyError:
                # there were no scientific properties associated w/ this component (or, rather, no components associated w/ this vocabulary)
                # that's okay
                scientific_property_customizers[model_key] = []
                pass

        return (models,standard_properties,scientific_properties)

    def create_model_realization_from_forms(self,project_name,version_name,model_name):

        project = MetadataProject.objects.get(name__iexact=project_name,active=True)
        version = MetadataVersion.objects.get(name__iexact=version_name,registered=True)
        model_proxy = MetadataModelProxy.objects.get(version=version,name__iexact=model_name)

        (models,standard_properties,scientific_properties) = self.create_model_realization(project_name, version_name, model_name)
        
        model_keys = [u"%s_%s" % (model.vocabulary_key, model.component_key) for model in models]

        model_customizer = MetadataModelCustomizer.objects.get(project=project,version=version,proxy=model_proxy,default=True)
        standard_property_customizers = model_customizer.standard_property_customizers.all().order_by("category__order","order")
        scientific_property_customizers = {}

        for model in models:
            model_key = u"%s_%s" % (model.vocabulary_key, model.component_key)
            scientific_property_customizers[model_key] = MetadataScientificPropertyCustomizer.objects.filter(model_customizer=model_customizer, model_key=model_key).order_by("category__order","order")

        post_data = {}

        models_data = [create_model_form_data(model, model_customizer) for model in models]
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

        for i, model in enumerate(models):

            model_key = u"%s_%s" % (model.vocabulary_key, model.component_key)

            standard_properties_data = [
                create_standard_property_form_data(model, standard_property, standard_property_customizer)
                for standard_property, standard_property_customizer in
                zip(standard_properties[model_key], standard_property_customizers)
                if standard_property_customizer.displayed
            ]
            for (i,standard_property_data) in enumerate(standard_properties_data):
                for key in standard_property_data.keys():
                    standard_property_data[u"%s_standard_properties-%s-%s" % (model_key,i,key)] = standard_property_data.pop(key)
            map(lambda standard_property_data: post_data.update(standard_property_data),standard_properties_data)
            post_data[u"%s_standard_properties-TOTAL_FORMS"%(model_key)] = len(standard_properties[model_key])
            post_data[u"%s_standard_properties-INITIAL_FORMS"%(model_key)] = 0

            scientific_properties_data = [
                create_scientific_property_form_data(model, scientific_property, scientific_property_customizer)
                for scientific_property, scientific_property_customizer in
                zip(scientific_properties[model_key], scientific_property_customizers[model_key])
                if scientific_property_customizer.displayed
            ]
            for (i,scientific_property_data) in enumerate(scientific_properties_data):
                for key in scientific_property_data.keys():
                    scientific_property_data[u"%s_scientific_properties-%s-%s" % (model_key,i,key)] = scientific_property_data.pop(key)
            map(lambda scientific_property_data: post_data.update(scientific_property_data),scientific_properties_data)
            post_data[u"%s_scientific_properties-TOTAL_FORMS"%(model_key)] = len(scientific_properties[model_key])
            post_data[u"%s_scientific_properties-INITIAL_FORMS"%(model_key)] = 0


        request_url = u"/%s/edit/%s/%s" % (project_name,version_name,model_name)
        request = self.factory.post(request_url,post_data)
        # fix the POST dictionary (u"None" -> None)
        # TODO: EVENTUALLY SOLVE THIS PROBLEM MORE ELEGANTLY
        for (key,value) in request.POST.iteritems():
            if value == u"None":
                request.POST[key] = None

        model_formset = MetadataModelFormSetFactory(
            request=request,
            prefixes=model_keys,
            customizer=model_customizer,
        )

        self.assertEqual(model_formset.is_valid(),True)
        model_instances = model_formset.save(commit=True)

        for i,model in enumerate(models):

            model_key = u"%s_%s" % (model.vocabulary_key, model.component_key)

            standard_properties_formset = MetadataStandardPropertyInlineFormSetFactory(
                instance=model_instances[i],
                prefix=model_key,
                request=request,
                customizers=standard_property_customizers,
            )

            self.assertEqual(standard_properties_formset.is_valid(),True)
            standard_properties_formset.save(commit=True)

            scientific_properties_formset = MetadataScientificPropertyInlineFormSetFactory(
                instance=model_instances[i],
                prefix=model_key,
                request=request,
                customizers=scientific_property_customizers[model_key],
            )

            self.assertEqual(scientific_properties_formset.is_valid(),True)
            scientific_properties_formset.save(commit=True)

        return model_instances[0]

    def create_model_realization_from_db(self,project_name,version_name,model_name):

        project = MetadataProject.objects.get(name__iexact=project_name,active=True)
        version = MetadataVersion.objects.get(name__iexact=version_name,registered=True)
        model_proxy = MetadataModelProxy.objects.get(version=version,name__iexact=model_name)

        (models,standard_properties,scientific_properties) = self.create_model_realization(project_name, version_name, model_name)

        for model in models:
            model.save()

            model_key = u"%s_%s" % (model.vocabulary_key, model.component_key)

            for standard_property in standard_properties[model_key]:
                standard_property.model = model
                standard_property.save()

            for scientific_property in scientific_properties[model_key]:
                scientific_property.model = model
                scientific_property.save()

        return models[0]

    def setUp(self):
        # request factory for all tests
        self.factory = RequestFactory()
        # client for all test
        self.client = Client()

        # ensure that there is no categorized metadata before a new one is loaded
        qs = MetadataCategorization.objects.all()
        self.assertEqual(len(qs),0)

        # create a categorization
        test_categorization_name = "test_categorization.xml"
        test_categorization = MetadataCategorization(name="test",file=os.path.join(CATEGORIZATION_UPLOAD_PATH,test_categorization_name))
        test_categorization.save()

        # ensure the categorization is saved to the database
        qs = MetadataCategorization.objects.all()
        self.assertEqual(len(qs),1)

        # create a version
        test_version_name = "test_version.xml"
        test_version = MetadataVersion(name="test",file=os.path.join(VERSION_UPLOAD_PATH,test_version_name))
        test_version.categorization = test_categorization   # associate the "test" categorization w/ the "test" version
        test_version.save()

        # create a vocabulary
        test_vocabulary_name = "test_vocabulary.xml"
        test_vocabulary = MetadataVocabulary(name="test",file=os.path.join(VOCABULARY_UPLOAD_PATH,test_vocabulary_name))
        test_vocabulary.document_type = "modelcomponent"
        test_vocabulary.save()

        # create a project
        test_project = MetadataProject(name="test",title="Test")
        test_project.save()

        # register a version
        self.assertEqual(test_version.registered,False)
        test_version.register()
        test_version.save()
        self.assertEqual(test_version.registered,True)

        # register a categorization        
        self.assertEqual(test_categorization.registered,False)
        test_categorization.register()
        test_categorization.save()
        self.assertEqual(test_categorization.registered,True)

        # register a vocabulary
        self.assertEqual(test_vocabulary.registered,False)
        test_vocabulary.register()
        test_vocabulary.save()
        self.assertEqual(test_vocabulary.registered,True)

        # setup a project w/ a vocabulary
        test_project.vocabularies.add(test_vocabulary)
        test_project.save()

        # create a default customizer
        test_customizer = self.create_customizer_from_forms("test","modelcomponent","test","test")
        test_customizer.default = True
        test_customizer.save()

        self.version = test_version
        self.categorization = test_categorization
        self.vocabulary = test_vocabulary
        self.project = test_project
        self.customizer = test_customizer

    def tearDown(self):
        pass


class MetadataVersionTest(MetadataTest):

    def test_setUp(self):
        qs = MetadataCategorization.objects.all()
        self.assertEqual(len(qs),1)

    def test_register_models(self):

        models = MetadataModelProxy.objects.all()

        excluded_fields = ["id","version"]
        serialized_models = [model_to_dict(model,exclude=excluded_fields) for model in models]

        to_test = [{'order': 0, 'documentation': u'blah', 'name': u'modelcomponent', 'stereotype': u'document', 'package': None}, {'order': 1, 'documentation': u'blah', 'name': u'gridspec', 'stereotype': u'document', 'package': None}]

        # test that the models have the expected standard fields
        for s,t in zip(serialized_models,to_test):
            self.assertDictEqual(s,t)

        # test that they have the expected foreignkeys
        for model in models:
            self.assertEqual(model.version,self.version)

    def test_register_standard_properties(self):

        models = MetadataModelProxy.objects.all()

        to_test = [
            [
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'shortName', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 0, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'TEXT'},
            ],
            [
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'shortName', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 0, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'DEFAULT'},
                {'field_type': u'ENUMERATION', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'type', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'one|two|three', 'documentation': u'', 'order': 1, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'TEXT'},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'longName', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 2, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'TEXT'},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'description', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 3, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'TEXT'},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'purpose', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 4, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'TEXT'},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'license', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 5, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'TEXT'},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'timing', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 6, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'TEXT'},
                {'field_type': u'RELATIONSHIP', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'grid', 'enumeration_multi': False, 'relationship_target_name': u'gridspec', 'enumeration_choices': u'', 'documentation': u'', 'order': 7, 'enumeration_open': False, 'relationship_cardinality': u'0|*', 'atomic_type': u'TEXT'}
            ]
        ]

        excluded_fields = ["id","model_proxy","relationship_target_model"]

        for model,standard_properties_to_test in zip(models,to_test):
            standard_properties = model.standard_properties.all()
            serialized_standard_properties = [model_to_dict(standard_property,exclude=excluded_fields) for standard_property in standard_properties]

            # test that the properties have the expected standard fields
            for serialized_standard_property,standard_property_to_test in zip(serialized_standard_properties,standard_properties_to_test):
                self.assertDictEqual(serialized_standard_property,standard_property_to_test)

            for standard_property in standard_properties:
                self.assertEqual(standard_property.model_proxy,model)

                if standard_property.relationship_target_model or standard_property.relationship_target_name:
                    self.assertEqual(standard_property.relationship_target_model.name,standard_property.relationship_target_name)


class MetadataCategorizationTest(MetadataTest):

    def test_register_standard_categories(self):

        categories = MetadataStandardCategoryProxy.objects.all()

        excluded_fields = ["id","categorization","properties"]
        serialized_categories = [model_to_dict(category,exclude=excluded_fields) for category in categories]

        categories_to_test = [
            {'name': u'Document Properties', 'key': u'document-properties', 'order': 1, 'description': u''},
            {'name': u'Basic Properties', 'key': u'basic-properties', 'order': 2, 'description': u''},
            {'name': u'Component Description', 'key': u'component-description', 'order': 3, 'description': u''},
        ]


        # test that the categories have the expected standard fields
        for s,t in zip(serialized_categories,categories_to_test):
            self.assertDictEqual(s,t)

        # test that they have the expected foreignkeys
        for category in categories:
            self.assertEqual(category.categorization,self.categorization)
            # TODO: TEST THAT "PROPETIES" M2M FIELD IS AS EXPECTED

class MetadataVocabularyTest(MetadataTest):

    def test_register_components(self):
        components = MetadataComponentProxy.objects.all()

        excluded_fields = ["vocabulary","parent","id"]
        serialized_components = [model_to_dict(component,exclude=excluded_fields) for component in components]

        components_to_test = [
            {'order': 1, 'documentation': u'Definition of component type Atmosphere required', 'name': u'atmosphere'},
            {'order': 2, 'documentation': u'Definition of component type AtmosKeyProperties required', 'name': u'atmoskeyproperties'},
            {'order': 3, 'documentation': u'Definition of component type TopOfAtmosInsolation required', 'name': u'topofatmosinsolation'},
            {'order': 4, 'documentation': u'Definition of component type AtmosSpaceConfiguration required', 'name': u'atmosspaceconfiguration'},
            {'order': 5, 'documentation': u'Definition of component type AtmosHorizontalDomain required', 'name': u'atmoshorizontaldomain'},
            {'order': 6, 'documentation': u'Definition of component type AtmosDynamicalCore required', 'name': u'atmosdynamicalcore'},
            {'order': 7, 'documentation': u'Definition of component type AtmosAdvection required', 'name': u'atmosadvection'},
            {'order': 8, 'documentation': u'Definition of component type AtmosRadiation required', 'name': u'atmosradiation'},
            {'order': 9, 'documentation': u'Definition of component type AtmosConvectTurbulCloud required', 'name': u'atmosconvectturbulcloud'},
            {'order': 10, 'documentation': u'Definition of component type AtmosCloudScheme required', 'name': u'atmoscloudscheme'},
            {'order': 11, 'documentation': u'Definition of component type CloudSimulator required', 'name': u'cloudsimulator'},
            {'order': 12, 'documentation': u'Definition of component type AtmosOrographyAndWaves required', 'name': u'atmosorographyandwaves'}
        ]

        # test that the components have the expected standard fields
        for s,t in zip(serialized_components,components_to_test):
            self.assertDictEqual(s,t)

        # test that they have the expected foreignkeys
        for component in components:
            self.assertEqual(component.vocabulary,self.vocabulary)
            # TODO: TEST THAT "PARENT" FK FIELD IS AS EXPECTED

    def test_register_scientific_properties(self):
        properties = MetadataScientificPropertyProxy.objects.all().order_by("component__order","category__order","order")

        excluded_fields = ["id","category","component"]
        serialized_properties = [model_to_dict(property,exclude=excluded_fields) for property in properties]

        properties_to_test = [
            {'field_type': None, 'name': u'ModelFamily', 'documentation': u'Type of atmospheric model.', 'choice': u'XOR', 'values': u'AGCM|ARCM|other|N/A', 'order': 0}, {'field_type': None, 'name': u'BasicApproximations', 'documentation': u'Basic fluid dynamics approximations made in the atmospheric model.', 'choice': u'OR', 'values': u'primitive equations|non-hydrostatic|anelastic|Boussinesq|hydrostatic|quasi-hydrostatic|other|N/A', 'order': 1}, {'field_type': None, 'name': u'VolcanoesImplementation', 'documentation': u'How the volcanoes effect is modeled in the atmophere.', 'choice': u'XOR', 'values': u'none|via high frequency solar contant anomaly|via stratospheric aerosols optical thickness|other|N/A', 'order': 2}, {'field_type': None, 'name': u'ImpactOnOzone', 'documentation': u'Impact of TOA radiation on stratospheric ozone.', 'choice': u'XOR', 'values': u'yes|no', 'order': 0}, {'field_type': None, 'name': u'Type', 'documentation': u'Time adaptation of the solar constant.', 'choice': u'XOR', 'values': u'fixed|transient|other|N/A', 'order': 0}, {'field_type': None, 'name': u'Type', 'documentation': u'Time adaptation of the orbital parameters.', 'choice': u'XOR', 'values': u'fixed|transient|other|N/A', 'order': 0}, {'field_type': None, 'name': u'ComputationMethod', 'documentation': u'Method for computing orbital parameters.', 'choice': u'XOR', 'values': u'Berger 1978|Laskar 2004|other|N/A', 'order': 1}, {'field_type': None, 'name': u'OrographyType', 'documentation': u'Time adaptation of the orography.', 'choice': u'XOR', 'values': u'present-day|modified|other|N/A', 'order': 0}, {'field_type': None, 'name': u'VerticalCoordinateSystem', 'documentation': u'vertical coordinate system.', 'choice': u'XOR', 'values': u'fixed pressure surfaces|pressure height|geometric height|hybrid sigma-pressure layers|hybrid floating Lagrangian|isentropic|sigma|other|N/A', 'order': 0}, {'field_type': None, 'name': u'TopModelLevel', 'documentation': u'Level at top of the atmosphere.', 'choice': u'keyboard', 'values': u'', 'order': 1}, {'field_type': None, 'name': u'NumberOfLevels', 'documentation': u'Total number of vertical levels.', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'NumberOfLevelsBellow850hPa', 'documentation': u'Number of vertical levels bellow 850 hPa.', 'choice': u'keyboard', 'values': u'', 'order': 3}, {'field_type': None, 'name': u'NumberOfLevelsAbove200hPa', 'documentation': u'Number of vertical levels above 200 hPa.', 'choice': u'keyboard', 'values': u'', 'order': 4}, {'field_type': None, 'name': u'GridType', 'documentation': u'Geometry type of the horizontal grid.', 'choice': u'XOR', 'values': u'latitude-longitude retangular|latitude-longitude|reduced gaussian|other|N/A', 'order': 0}, {'field_type': None, 'name': u'PoleSingularityTreatment', 'documentation': u'Method used to deal with the pole singularities.', 'choice': u'XOR', 'values': u'filter|pole rotation|artificial island|none|other|N/A', 'order': 1}, {'field_type': None, 'name': u'MeanZonalResolution', 'documentation': u'Mean zonal resolution.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'MeanMeridionalResolution', 'documentation': u'Mean meridional resolution.', 'choice': u'keyboard', 'values': u'', 'order': 1}, {'field_type': None, 'name': u'EquatorMeridionalRefinement', 'documentation': u'Resolution at equator.', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'SpecialRefinement', 'documentation': u'Description of any other special gid refinement (location, resolution).', 'choice': u'keyboard', 'values': u'', 'order': 3}, {'field_type': None, 'name': u'LatMin', 'documentation': u'Southern boundary of the geographical domain.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'LatMax', 'documentation': u'Northern boundary of the geographical domain.', 'choice': u'keyboard', 'values': u'', 'order': 1}, {'field_type': None, 'name': u'LonMin', 'documentation': u'Western boundary of the geographical domain.', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'LonMax', 'documentation': u'Eastern boundary of the geographical domain.', 'choice': u'keyboard', 'values': u'', 'order': 3}, {'field_type': None, 'name': u'ListOfPrognosticVariables', 'documentation': u'List of the prognostic variables of the model.', 'choice': u'OR', 'values': u'surface pressure|wind components|divergence/curl|temperature|potential temperature|total water|vapour/solid/liquid|total water moments|clouds|radiation|other|N/A', 'order': 0}, {'field_type': None, 'name': u'TopBoundaryCondition', 'documentation': u'Type of boundary layer at top of the model.', 'choice': u'XOR', 'values': u'sponge layer|radiation boundary condition|other|N/A', 'order': 1}, {'field_type': None, 'name': u'HeatTreatmentAtTop', 'documentation': u'Description of any specific treatment of heat at top of the model.', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'WindTreatmentAtTop', 'documentation': u'Description of any specific treatment of wind at top of the model.', 'choice': u'keyboard', 'values': u'', 'order': 3}, {'field_type': None, 'name': u'LateralBoundaryCondition', 'documentation': u'Type of lateral boundary condition (only if the model is a RCM).', 'choice': u'XOR', 'values': u'sponge layer|radiation boundary condition|none|other|N/A', 'order': 4}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of time stepping scheme.', 'choice': u'XOR', 'values': u'Adam Bashford|Explicit|Implicit|Semi-Implicit|LeapFrog|Multi-step|Runge Kutta fifth order|Runge Kutta second order|Runge Kutta third order|other|N/A', 'order': 0}, {'field_type': None, 'name': u'TimeStep', 'documentation': u'Time step of the model.', 'choice': u'keyboard', 'values': u'', 'order': 1}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of horizontal discretization scheme.', 'choice': u'XOR', 'values': u'spectral|fixed grid|other|N/A', 'order': 0}, {'field_type': None, 'name': u'SchemeName', 'documentation': u'commonly used name of the horizontal diffusion scheme.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'SchemeMethod', 'documentation': u'Numerical method used by horizontal diffusion scheme.', 'choice': u'XOR', 'values': u'iterated Laplacian|other|N/A', 'order': 1}, {'field_type': None, 'name': u'SchemeName', 'documentation': u'Commonly used name for tracers advection scheme.', 'choice': u'XOR', 'values': u'Prather|other|N/A', 'order': 0}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of numerical scheme used for advection of tracers.', 'choice': u'XOR', 'values': u'Eulerian|Lagrangian|semi-Lagrangian|mass-conserving|mass-conserving / finite volume (Lin-Rood)|other|N/A', 'order': 1}, {'field_type': None, 'name': u'ConservedQuantities', 'documentation': u'Quantities conserved trought tracers advection scheme.', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'ConservationMethod', 'documentation': u'Method used to ensure conservation in tracers advection scheme.', 'choice': u'OR', 'values': u'conservation fixer|other|N/A', 'order': 3}, {'field_type': None, 'name': u'SchemeName', 'documentation': u'Commonly used name for momentum advection scheme.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of numerical scheme used for advection of momentum.', 'choice': u'XOR', 'values': u'Eulerian|Lagrangian|Semi-Lagrangian|Mass-conserving|Mass-conserving / Finite volume (Lin-Rood)|other|N/A', 'order': 1}, {'field_type': None, 'name': u'ConservedQuantities', 'documentation': u'Quantities conserved trought momentum advection scheme.', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'ConservationMethod', 'documentation': u'Method used to ensure conservation in momentum advection scheme.', 'choice': u'OR', 'values': u'conservation fixer|other|N/A', 'order': 3}, {'field_type': None, 'name': u'TimeStep', 'documentation': u'Time step of the radiative scheme.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'AerosolTypes', 'documentation': u'Types of aerosols whose radiative effect is taken into account in the atmospheric model.', 'choice': u'OR', 'values': u'sulphate|nitrate|sea salt|dust|ice|organic|BC (black carbon / soot)|SOA (secondary organic aerosols)|POM (particulate organic matter)|polar stratospheric ice|NAT (nitric acid trihydrate)|NAD (nitric acid dihydrate)|STS (supercooled ternary solution aerosol particule)|other|N/A', 'order': 1}, {'field_type': None, 'name': u'GHG-Types', 'documentation': u'GHG whose radiative effect is taken into account in the atmospheric model.', 'choice': u'OR', 'values': u'CO2|CH4|N2O|CFC|H2O|O3|other|N/A', 'order': 2}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of scheme used for longwave radiation parametrisation.', 'choice': u'XOR', 'values': u'Wide-band model|Wide-band (Morcrette)|K-correlated|K-correlated (RRTM)|other|N/A', 'order': 0}, {'field_type': None, 'name': u'SchemeMethod', 'documentation': u'Method for the radiative transfert calculations used in the longwave scheme.', 'choice': u'XOR', 'values': u'Two-stream|Layer interaction|other|N/A', 'order': 1}, {'field_type': None, 'name': u'NumberOfSpectralIntervals', 'documentation': u'Number of spectral interval of the longwave radiation scheme.', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of scheme used for shortwave radiation parametrization.', 'choice': u'XOR', 'values': u'Wide-band model|Wide-band model (Fouquart)|other|N/A', 'order': 0}, {'field_type': None, 'name': u'NumberOfSpectralIntervals', 'documentation': u'Number of spectral intervals of the short radiation scheme.', 'choice': u'keyboard', 'values': u'', 'order': 1}, {'field_type': None, 'name': u'ice', 'documentation': u'Radiative properties of ice cristals in clouds.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'liquid', 'documentation': u'Radiative properties of cloud droplets.', 'choice': u'keyboard', 'values': u'', 'order': 1}, {'field_type': None, 'name': u'SchemeName', 'documentation': u'Commonly used name for boundary layer tubulence scheme.', 'choice': u'XOR', 'values': u'Mellor-Yamada|other|N/A', 'order': 0}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of scheme used for parametrization of turbulence in the boundary layer.', 'choice': u'XOR', 'values': u'TKE prognostic|TKE diagnostic|TKE coupled with water|Vertical profile of Kz|other|N/A', 'order': 1}, {'field_type': None, 'name': u'CounterGradient', 'documentation': u'Application of a counter-gradient term for calculation of the vertical turbulent heat fluxes in case of slighlty stable layer.', 'choice': u'XOR', 'values': u'yes|no', 'order': 2}, {'field_type': None, 'name': u'SchemeName', 'documentation': u'Commonly used name for deep convection scheme.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of scheme used for parametrization of deep convection.', 'choice': u'XOR', 'values': u'Mass-flux|Adjustment|other|N/A', 'order': 1}, {'field_type': None, 'name': u'Processes', 'documentation': u'Physical processes taken into account in the parametrization of the deep convection.', 'choice': u'OR', 'values': u'vertical momentum transport|convective momentum transport (CMT)|penetrative convection effects included|representation of updrafts and downdrafts|radiative effects of anvils|entrainment|detrainment|other|N/A', 'order': 2}, {'field_type': None, 'name': u'Method', 'documentation': u'Method used for parametrization of shallow convection.', 'choice': u'XOR', 'values': u'same as deep (unified)|included in Boundary Layer Turbulence|separated|other|N/A', 'order': 0}, {'field_type': None, 'name': u'SchemeName', 'documentation': u'Commonly used name for mid-level convection scheme.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of scheme used for parametrization of mid-level convection.', 'choice': u'XOR', 'values': u'mass-flux|other|N/A', 'order': 1}, {'field_type': None, 'name': u'SchemeName', 'documentation': u'Commonly used name of the large scale precipitation parametrization scheme.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'PrecipitatingHydrometeors', 'documentation': u'Precipitating hydrometeors in the large scale precipitation scheme.', 'choice': u'OR', 'values': u'liquid rain|snow|hail|graupel|cats & dogs|other|N/A', 'order': 1}, {'field_type': None, 'name': u'SchemeName', 'documentation': u'Commonly used name of the microphysics parametrization scheme.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'Processes', 'documentation': u'Description of the microphysics processes that are taken into account in the microphysics scheme.', 'choice': u'OR', 'values': u'mixed phase|cloud droplets|cloud ice|ice nucleation|water vapour deposition|effect of raindrops|effect of snow|effect of graupel|other|N/A', 'order': 1}, {'field_type': None, 'name': u'SeparatedCloudTreatment', 'documentation': u'Different cloud schemes for the different types of clouds (convective, stratiform and bondary layer clouds).', 'choice': u'XOR', 'values': u'yes|no', 'order': 0}, {'field_type': None, 'name': u'CloudOverlap', 'documentation': u'Method for taking into account overlapping of cloud layers.', 'choice': u'XOR', 'values': u'random|none|other|N/A', 'order': 1}, {'field_type': None, 'name': u'Processes', 'documentation': u'Cloud processes included in the cloud scheme (e.g. entrainment, detrainment, bulk cloud, etc.).', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'Type', 'documentation': u'Approach used for cloud water content and fractional cloud cover.', 'choice': u'XOR', 'values': u'prognostic|diagnostic|other|N/A', 'order': 0}, {'field_type': None, 'name': u'FunctionName', 'documentation': u'Commonly used name of the probability density function (PDF) representing distribution of water vapor within a grid box.', 'choice': u'keyboard', 'values': u'', 'order': 1}, {'field_type': None, 'name': u'FunctionOrder', 'documentation': u'Order of the function (PDF) used to represent subgrid scale water vapor distribution.', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'CouplingWithConvection', 'documentation': u'Cloud formation coupled with convection. ', 'choice': u'XOR', 'values': u'coupled with deep|coupled with shallow|coupled with deep and shallow|not coupled with convection|other|N/A', 'order': 3}, {'field_type': None, 'name': u'COSPRunConfiguration', 'documentation': u'Method used to run the CFMIP Observational Simulator Package.', 'choice': u'XOR', 'values': u'inline|offline|none|other|N/A', 'order': 0}, {'field_type': None, 'name': u'NumberOfGridpoints', 'documentation': u'Number of gridpoints used. ', 'choice': u'keyboard', 'values': u'', 'order': 1}, {'field_type': None, 'name': u'NumberOfColumns', 'documentation': u'Number of subcolumns used. ', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'NumberOfLevels', 'documentation': u'Number of model levels used. ', 'choice': u'keyboard', 'values': u'', 'order': 3}, {'field_type': None, 'name': u'RadarFrequency', 'documentation': u'CloudSat radar frequency.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'RadarType', 'documentation': u'Type of radar - surface or spaceborne?', 'choice': u'XOR', 'values': u'surface|spaceborne|other|N/A', 'order': 1}, {'field_type': None, 'name': u'UseGasAbsorption', 'documentation': u'Include gaseous absorption?', 'choice': u'XOR', 'values': u'yes|no', 'order': 2}, {'field_type': None, 'name': u'UseEffectiveRadius', 'documentation': u'Is effective radius used by the radar simulator?', 'choice': u'XOR', 'values': u'yes|no', 'order': 3}, {'field_type': None, 'name': u'LidarIceType', 'documentation': u'Ice particle shape in lidar calculations.', 'choice': u'XOR', 'values': u'Ice spheres|Ice non-spherical|other|N/A', 'order': 0}, {'field_type': None, 'name': u'Overlap', 'documentation': u'Overlap type.', 'choice': u'XOR', 'values': u'max|random|max / random|other|N/A', 'order': 1}, {'field_type': None, 'name': u'TopHeight', 'documentation': u'Cloud top height management. e.g. adjusted using both a computed infrared brightness temperature and visible optical depth to adjust cloud top pressure. ', 'choice': u'XOR', 'values': u'no adjustment|IR brightness|IR brightness and visible optical depth|other|N/A', 'order': 0}, {'field_type': None, 'name': u'TopHeightDirection', 'documentation': u'\nDirection for finding the radiance determined cloud-top pressure.  \nAtmosphere pressure level with interpolated temperature equal to the radiance determined cloud-top pressure.', 'choice': u'XOR', 'values': u'lowest altitude level|highest altitude level|other|N/A', 'order': 1}, {'field_type': None, 'name': u'SpongeLayer', 'documentation': u'Sponge layer in the upper layers in order to avoid gravitywaves reflection at top.', 'choice': u'XOR', 'values': u'none|other|N/A', 'order': 0}, {'field_type': None, 'name': u'Background', 'documentation': u'Background distribution of waves (???).', 'choice': u'XOR', 'values': u'none|other|N/A', 'order': 1}, {'field_type': None, 'name': u'SubGridScaleOrography', 'documentation': u'Subgrid scale orography effects taken into account.', 'choice': u'OR', 'values': u'effect on drag|effect on lifting|other|N/A', 'order': 2}, {'field_type': None, 'name': u'SourceMechanisms', 'documentation': u'Physical mechanisms generating orographic gravity waves.', 'choice': u'OR', 'values': u'linear mountain waves|hydraulic jump|envelope orography|statistical sub-grid scale variance|other|N/A', 'order': 0}, {'field_type': None, 'name': u'CalculationMethod', 'documentation': u'Calculation method for orographic gravity waves.', 'choice': u'OR', 'values': u'non-linear calculation|more than two cardinal directions|other|N/A', 'order': 1}, {'field_type': None, 'name': u'PropagationScheme', 'documentation': u'Type of propagation scheme for orographic gravity waves.', 'choice': u'XOR', 'values': u'linear theory|non-linear theory|other|N/A', 'order': 2}, {'field_type': None, 'name': u'DissipationScheme', 'documentation': u'Type of dissipation scheme for orographic gravity waves.', 'choice': u'XOR', 'values': u'total wave|single wave|spectral|linear|other|N/A', 'order': 3}, {'field_type': None, 'name': u'PropagationScheme', 'documentation': u'Type of propagation scheme for convective gravity waves.', 'choice': u'XOR', 'values': u'linear theory|non-linear theory|other|N/A', 'order': 0}, {'field_type': None, 'name': u'DissipationScheme', 'documentation': u'Type of dissipation scheme for convective gravity waves.', 'choice': u'XOR', 'values': u'total Wave|single wave|spectral|linear|other|N/A', 'order': 1}, {'field_type': None, 'name': u'SourceMechanisms', 'documentation': u'Physical mechanisms generating non-orographic gravity waves.', 'choice': u'OR', 'values': u'convection|precipitation|background spectrum|other|N/A', 'order': 0}, {'field_type': None, 'name': u'CalculationMethod', 'documentation': u'Calculation method for non-orographic gravity waves.', 'choice': u'OR', 'values': u'spatially dependent|temporally dependent|other|N/A', 'order': 1}, {'field_type': None, 'name': u'PropagationScheme', 'documentation': u'Type of propagation scheme for non-orographic gravity waves.', 'choice': u'XOR', 'values': u'linear theory|non-linear theory|other|N/A', 'order': 2}, {'field_type': None, 'name': u'DissipationScheme', 'documentation': u'Type of dissipation scheme for non-orographic gravity waves.', 'choice': u'XOR', 'values': u'total wave|single wave|spectral|linear|other|N/A', 'order': 3}
        ]

        # test that the components have the expected standard fields
        for s,t in zip(serialized_properties,properties_to_test):
            self.assertDictEqual(s,t)

        # TODO: TEST THAT "category" & "component" FIELDS ARE AS EXPECTED

    def test_register_scientific_categories(self):

        categories = MetadataScientificCategoryProxy.objects.all().order_by("component__order","order")

        excluded_fields = ["id","vocabulary","properties","component"]
        serialized_categories = [model_to_dict(category,exclude=excluded_fields) for category in categories]

        categories_to_test = [
            {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0}, {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0}, {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0}, {'key': u'solarconstant', 'description': None, 'name': u'SolarConstant', 'order': 1}, {'key': u'orbitalparameters', 'description': None, 'name': u'OrbitalParameters', 'order': 2}, {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0}, {'key': u'orography', 'description': None, 'name': u'Orography', 'order': 1}, {'key': u'verticaldomain', 'description': None, 'name': u'VerticalDomain', 'order': 2}, {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0}, {'key': u'grid', 'description': None, 'name': u'Grid', 'order': 1}, {'key': u'resolution', 'description': None, 'name': u'Resolution', 'order': 2}, {'key': u'extent', 'description': None, 'name': u'Extent', 'order': 3}, {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0}, {'key': u'timesteppingframework', 'description': None, 'name': u'TimeSteppingFramework', 'order': 1}, {'key': u'horizontaldiscretization', 'description': None, 'name': u'HorizontalDiscretization', 'order': 2}, {'key': u'horizontaldiffusion', 'description': None, 'name': u'HorizontalDiffusion', 'order': 3}, {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0}, {'key': u'tracers', 'description': None, 'name': u'Tracers', 'order': 1}, {'key': u'momentum', 'description': None, 'name': u'Momentum', 'order': 2}, {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0}, {'key': u'longwave', 'description': None, 'name': u'Longwave', 'order': 1}, {'key': u'shortwave', 'description': None, 'name': u'Shortwave', 'order': 2}, {'key': u'cloudradiativeproperties', 'description': None, 'name': u'CloudRadiativeProperties', 'order': 3}, {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0}, {'key': u'boundarylayerturbulence', 'description': None, 'name': u'BoundaryLayerTurbulence', 'order': 1}, {'key': u'deepconvection', 'description': None, 'name': u'DeepConvection', 'order': 2}, {'key': u'shallowconvection', 'description': None, 'name': u'ShallowConvection', 'order': 3}, {'key': u'otherconvection', 'description': None, 'name': u'OtherConvection', 'order': 4}, {'key': u'largescaleprecipitation', 'description': None, 'name': u'LargeScalePrecipitation', 'order': 5}, {'key': u'microphysics', 'description': None, 'name': u'Microphysics', 'order': 6}, {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0}, {'key': u'cloudschemeattributes', 'description': None, 'name': u'CloudSchemeAttributes', 'order': 1}, {'key': u'subgridscalewaterdistribution', 'description': None, 'name': u'SubGridScaleWaterDistribution', 'order': 2}, {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0}, {'key': u'cospattributes', 'description': None, 'name': u'COSPAttributes', 'order': 1}, {'key': u'inputsradar', 'description': None, 'name': u'InputsRadar', 'order': 2}, {'key': u'inputslidar', 'description': None, 'name': u'InputsLidar', 'order': 3}, {'key': u'isscpattributes', 'description': None, 'name': u'ISSCPAttributes', 'order': 4}, {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0}, {'key': u'orographicgravitywaves', 'description': None, 'name': u'OrographicGravityWaves', 'order': 1}, {'key': u'convectivegravitywaves', 'description': None, 'name': u'ConvectiveGravityWaves', 'order': 2}, {'key': u'non-orographicgravitywaves', 'description': None, 'name': u'Non-OrographicGravityWaves', 'order': 3}
        ]

        # test that the categories have the expected standard fields
        for s,t in zip(serialized_categories,categories_to_test):
            self.assertDictEqual(s,t)


class MetadataProjectTest(MetadataTest):

    def test_create_project(self):

        projects = MetadataProject.objects.all()

        excluded_fields = ["id","providers","vocabularies"]
        serialized_projects = [model_to_dict(project,exclude=excluded_fields) for project in projects]

        projects_to_test = [
            {'authenticated': False, 'description': u'', 'title': u'Test', 'url': u'', 'active': True, 'email': None, 'name': u'test'}
        ]

        # test that the projects have the expected standard fields
        for s,t in zip(serialized_projects,projects_to_test):
            self.assertDictEqual(s,t)

        # test that they have the expected foreignkeys
        vocabularies = MetadataVocabulary.objects.all()
        for project in projects:
            self.assertQuerysetEqual(project.vocabularies.all(),vocabularies)

class MetadataCustomizerTest(MetadataTest):

    def test_customizer_proxy_join_from_database(self):
        """Test customizers and proxies are properly joined."""

        model_customizers = MetadataModelCustomizer.objects.all()
        for mc in model_customizers:
            pc_standard = mc.standard_property_customizers.all()
            pc_scientific = mc.scientific_property_customizers.all()
            for pc in [pc_standard, pc_scientific]:
                for row in pc:
                    self.assertEqual(row.name, row.proxy.name)

    def test_create_model_customizer(self):

        model_customizers = MetadataModelCustomizer.objects.all()

        excluded_fields = ["id","vocabularies","project","version","proxy","vocabulary_order"]
        serialized_model_customizers = [model_to_dict(model_customizer,exclude=excluded_fields) for model_customizer in model_customizers]

        customizers_to_test = [
            {'model_root_component': u'RootComponent', 'description': u'', 'model_show_hierarchy': True, 'default': True, 'model_title': u'modelcomponent', 'model_show_all_properties': True, 'model_show_all_categories': False, 'model_description': u'blah', 'model_hierarchy_name': u'Component Hierarchy', 'name': u'test'}
        ]

        # test that the projects have the expected standard fields
        for s,t in zip(serialized_model_customizers,customizers_to_test):
            self.assertDictEqual(s,t)


###class MetadataCustomizeViewTest(MetadataTest):
###
###    def test_questionnaire_customize_new(self):
###        project_name = "test"
###        version_name = "test"
###        model_name = "modelcomponent"
###        request_url = "/%s/customize/%s/%s/" % (project_name,version_name,model_name)
###
###
###
###        request = self.factory.get(request_url)
###        response = customize_new(request)
###        self.assertEqual(response.status_code,200)
###

class MetadataEditingFormTest(MetadataTest):

    # def test_questionnaire_edit_form_get(self):
    #     pass


    def test_questionnaire_edit_form_post(self):
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


class MetadataEditingViewTest(MetadataTest):

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

        request_url = u"/%s/edit/%s/%s" % (project_name,version_name,model_name)
        request = self.factory.get(request_url)

        response = questionnaire_edit_new(request,project_name=project_name,version_name=version_name,model_name=model_name)
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


        request_url = u"/%s/edit/%s/%s" % (project_name,version_name,model_name)
        post_request = self.factory.post(request_url,post_data)
        post_response = questionnaire_edit_new(post_request,project_name=project_name,version_name=version_name,model_name=model_name)

        self.assertEqual(post_response.status_code,200)

        post_content = post_response.content

        expr = "test_atmoshorizontaldomain_scientific_properties-[0-9]-is_enumeration"
        fall = re.findall(expr, post_content)

        self.assertEqual(len(fall),20)

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

        model_realization2 = self.create_model_realization_from_db(project_name,version_name,model_name)
        self.assertEqual(len(MetadataModel.objects.all()),26)

    def test_questionnaire_edit_new_with_existing_realizations_from_forms(self):

        project_name = "test"
        version_name = "test"
        model_name = "modelcomponent"

        model_realization1 = self.create_model_realization_from_forms(project_name,version_name,model_name)
        self.assertEqual(len(MetadataModel.objects.all()),13)

        model_realization2 = self.create_model_realization_from_forms(project_name,version_name,model_name)
        self.assertEqual(len(MetadataModel.objects.all()),26)
        