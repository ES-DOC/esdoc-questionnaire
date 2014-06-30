import os
from django.template.defaultfilters import slugify
from django.test import RequestFactory, Client, TestCase
from CIM_Questionnaire.questionnaire.forms.forms_customize import create_model_customizer_form_data, \
    create_standard_property_customizer_form_data, create_scientific_property_customizer_form_data, \
    MetadataModelCustomizerForm, MetadataStandardPropertyCustomizerInlineFormSetFactory, \
    MetadataScientificPropertyCustomizerInlineFormSetFactory
from CIM_Questionnaire.questionnaire.forms.forms_edit import create_model_form_data, MetadataModelFormSetFactory, \
    create_standard_property_form_data, MetadataStandardPropertyInlineFormSetFactory, \
    create_scientific_property_form_data, MetadataScientificPropertyInlineFormSetFactory
from CIM_Questionnaire.questionnaire.models import MetadataProject, MetadataVersion, MetadataModelProxy, \
    MetadataCustomizer, MetadataModelCustomizer, MetadataScientificPropertyCustomizer, MetadataModel, \
    MetadataStandardProperty, MetadataScientificProperty, MetadataStandardCategoryCustomizer, \
    MetadataStandardPropertyCustomizer, MetadataScientificCategoryCustomizer, MetadataCategorization, MetadataVocabulary

from CIM_Questionnaire.questionnaire.models.metadata_model import create_models_from_components
from CIM_Questionnaire.questionnaire.utils import DEFAULT_VOCABULARY, find_in_sequence, assert_no_string_nones
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import UPLOAD_PATH as VOCABULARY_UPLOAD_PATH
from CIM_Questionnaire.questionnaire.models.metadata_version import UPLOAD_PATH as VERSION_UPLOAD_PATH
from CIM_Questionnaire.questionnaire.models.metadata_categorization import UPLOAD_PATH as CATEGORIZATION_UPLOAD_PATH

class TestQuestionnaireBase(TestCase):

    def setUp(self):

        # request factory for all tests
        self.factory = RequestFactory()
        # client for all tests (this is better-suited for testing views b/c, among other things, it has sessions, cookies, etc.)
        self.client = Client(enforce_csrf_checks=True)

        # ensure that there are no categorizations before a new one is loaded
        qs = MetadataCategorization.objects.all()
        self.assertEqual(len(qs),0)

        # create a categorization
        test_categorization_name = "test_categorization.xml"
        test_categorization = MetadataCategorization(name="test",file=os.path.join(CATEGORIZATION_UPLOAD_PATH,test_categorization_name))
        test_categorization.save()

        # ensure the categorization is saved to the database
        qs = MetadataCategorization.objects.all()
        self.assertEqual(len(qs),1)

        # ensure that there are no versions before a new one is loaded
        qs = MetadataVersion.objects.all()
        self.assertEqual(len(qs),0)

        # create a version
        test_version_name = "test_version.xml"
        test_version = MetadataVersion(name="test",file=os.path.join(VERSION_UPLOAD_PATH,test_version_name))
        test_version.categorization = test_categorization   # associate the "test" categorization w/ the "test" version
        test_version.save()

        # ensure the version is saved to the database
        qs = MetadataVersion.objects.all()
        self.assertEqual(len(qs),1)

        # ensure that there are no categorizations before a new one is loaded
        qs = MetadataVocabulary.objects.all()
        self.assertEqual(len(qs),0)

        # create a vocabulary
        test_vocabulary_name = "test_vocabulary.xml"
        test_vocabulary = MetadataVocabulary(name="test",file=os.path.join(VOCABULARY_UPLOAD_PATH,test_vocabulary_name))
        test_vocabulary.document_type = "modelcomponent"
        test_vocabulary.save()

        # ensure the version is saved to the database
        qs = MetadataVocabulary.objects.all()
        self.assertEqual(len(qs),1)

        # ensure that there are no projects before a new one is loaded
        qs = MetadataProject.objects.all()
        self.assertEqual(len(qs),0)

        # create a project
        test_project = MetadataProject(name="test",title="Test")
        test_project.save()

        # ensure the project is saved to the database
        qs = MetadataProject.objects.all()
        self.assertEqual(len(qs),1)

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

        # ensure that there are no customizers before a new one is loaded
        qs = MetadataModelCustomizer.objects.all()
        self.assertEqual(len(qs),0)

        # create a default customizer set
        # (note, other customizers w/ other features will be used throughout the testing suite;
        # this is just the default one where customizers need to exist for other functionallity to be tested)
        test_model_name = "modelcomponent"
        model_proxy_to_be_customized = MetadataModelProxy.objects.get(version=test_version,name__iexact=test_model_name)
        vocabularies_to_be_customized = test_project.vocabularies.filter(document_type__iexact=test_model_name)
        (test_model_customizer,test_standard_category_customizers,test_standard_property_customizers,test_scientific_category_customizers,test_scientific_property_customizers) = \
            MetadataCustomizer.get_new_customizer_set(test_project, test_version, model_proxy_to_be_customized, vocabularies_to_be_customized)
        test_model_customizer.name = "test"
        test_model_customizer.default = True
        MetadataCustomizer.save_customizer_set(test_model_customizer,test_standard_category_customizers,test_standard_property_customizers,test_scientific_category_customizers,test_scientific_property_customizers)

        # ensure the customizer set is saved to the database
        qs = MetadataModelCustomizer.objects.all()
        self.assertEqual(len(qs),1)

        self.version        = test_version
        self.categorization = test_categorization
        self.vocabulary     = test_vocabulary
        self.project        = test_project
        self.customizer     = test_model_customizer

    def assertQuerysetEqual(self, qs1, qs2):
        """Tests that two django querysets are equal"""
        # the built-in TestCase method takes a qs and a list, which is confusing
        # this is more intuitive (see https://djangosnippets.org/snippets/2013/)

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
                for scientific_property_proxy in component.scientific_properties.all():
                    scientific_category_proxy = scientific_property_proxy.category
                    if scientific_category_proxy:
                        scientific_category_key = scientific_category_proxy.key
                        if scientific_category_key in [scientific_category.key for scientific_category in scientific_category_customizers[vocabulary_key][model_key]]:
                            scientific_category_customizer = find_category_by_key(category_key,scientific_category_customizers[vocabulary_key][component_key])
                        else:
                            scientific_category_customizer = MetadataScientificCategoryCustomizer(
                                model_customizer=model_customizer,
                                proxy=scientific_category_proxy,
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

    def create_model_realization_from_view(self,project_name,version_name,model_name):

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

        assert_no_string_nones(post_data)
        request_url = u"/%s/edit/%s/%s/" % (project_name,version_name,model_name)
        response = self.client.post(request_url,post_data)

        self.assertEqual(response.status_code,302)
        self.assertNotEqual(len(MetadataModel.objects.all()),0)

        session_variables = response.client.session
        root_model_id = session_variables["root_model_id"]
        self.assertNotEqual(root_model_id,None)

        root_model = MetadataModel.objects.get(pk=root_model_id)

        return root_model


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
