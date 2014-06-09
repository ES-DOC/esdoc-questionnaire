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
from django.contrib import messages

from django.contrib.sites.models import get_current_site
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.template.defaultfilters import slugify

from questionnaire import get_version
from questionnaire.models import MetadataProject, MetadataVersion, MetadataModelProxy, \
    MetadataModelCustomizer, MetadataScientificPropertyCustomizer, MetadataModel, MetadataStandardProperty, \
    MetadataScientificProperty
from questionnaire.utils import DEFAULT_VOCABULARY
from questionnaire.models.metadata_model import create_models_from_components, find_model_by_key
from questionnaire.forms.forms_edit import create_model_form_data, create_standard_property_form_data, \
    create_scientific_property_form_data, \
    MetadataModelFormSetFactory, MetadataStandardPropertyInlineFormSetFactory, \
    MetadataScientificPropertyInlineFormSetFactory

__author__ = "allyn.treshansky"
__date__ = "Sep 30, 2013 3:04:42 PM"


def questionnaire_edit_new(request, project_name="", model_name="", version_name="", **kwargs):
    ##todo: remove local import statement
    from questionnaire.views.views_error import questionnaire_error

    # try to get the project...
    try:
        project = MetadataProject.objects.get(name__iexact=project_name)
    except MetadataProject.DoesNotExist:
        msg = "Cannot find the <u>project</u> '%s'.  Has it been registered?" % project_name
        return questionnaire_error(request, msg)
    if not project.active:
        msg = "Project '%s' is inactive." % project_name
        return questionnaire_error(request, msg)

    # check authentication...
    # (not using "@login_required" b/c some projects ignore authentication)
    if project.authenticated:
        current_user = request.user
        if not current_user.is_authenticated():
            return redirect('/login/?next=%s' % (request.path))
        if not (request.user.is_superuser or request.user.metadata_user.is_user_of(project)):
            msg = "User '%s' does not have editing permission for project '%s'." % (request.user, project_name)
            if project.email:
                msg += "<br/>Please <a href='mailto:%s'>contact</a> the project for support." % (project.email)
            return questionnaire_error(request, msg)

    # try to get the version...
    try:
        version = MetadataVersion.objects.get(name__iexact=version_name, registered=True)
    except MetadataVersion.DoesNotExist:
        msg = "Cannot find the <u>version</u> '%s'.  Has it been registered?" % version_name
        return questionnaire_error(request, msg)

    # try to get the model (proxy)...
    try:
        model_proxy = MetadataModelProxy.objects.get(version=version, name__iexact=model_name)
    except MetadataModelProxy.DoesNotExist:
        msg = "Cannot find the <u>model</u> '%s' in the <u>version</u> '%s'." % (model_name, version_name)
        return questionnaire_error(request, msg)
    if not model_proxy.is_document():
        msg = "<u>%s</u> is not a recognized document type in the CIM." % model_name
        return questionnaire_error(request, msg)

    # try to get the default model customizer for this project/version/proxy combination...
    try:
        model_customizer = MetadataModelCustomizer.objects.get(project=project, version=version, proxy=model_proxy,
                                                               default=True)
    except MetadataModelCustomizer.DoesNotExist:
        msg = "There is no default customization associated with this project/model/version."
        return questionnaire_error(request, msg)

    # getting the vocabularies into the right order is a 2-step process
    # b/c vocabularies do not have an "order" attribute (since they can be used by multiple projects/customizations),
    # but the model_customizer does record the desired order of active vocabularies (as a comma-separated list)
    vocabularies = model_customizer.vocabularies.all()
    vocabulary_order = [int(order) for order in model_customizer.vocabulary_order.split(',')]
    vocabularies = sorted(vocabularies, key=lambda vocabulary: vocabulary_order.index(vocabulary.pk))

    # now try to get the default property customizers for this project/version/proxy combination...
    # (also get the proxies b/c I'll need them when setting up properties below)

    standard_property_customizers = model_customizer.standard_property_customizers.all().order_by("category__order","order")
    standard_property_proxies = [standard_property_customizer.proxy for standard_property_customizer in standard_property_customizers]

    ##TODO: remove assert statement
    pc_standard = model_customizer.standard_property_customizers.all()
    pc_scientific = model_customizer.scientific_property_customizers.all()
    for pc in [pc_standard, pc_scientific]:
        for row in pc:
            assert row.name == row.proxy.name

    scientific_property_customizers = {}
    scientific_property_proxies = {}
    for vocabulary in vocabularies:
        vocabulary_key = slugify(vocabulary.name)
        for component_proxy in vocabulary.component_proxies.all():
            component_key = slugify(component_proxy.name)
            model_key = u"%s_%s" % (vocabulary_key, component_key)
            scientific_property_customizers[model_key] = MetadataScientificPropertyCustomizer.objects.filter(model_customizer=model_customizer, model_key=model_key).order_by("category__order", "order")
            scientific_property_proxies[model_key] = [scientific_property_customizer.proxy for scientific_property_customizer in scientific_property_customizers[model_key]]
            # TODO: AT THIS POINT I HAVE DISCOVERED THAT THE CUSTOMIZERS ARE NOT ASSOCIATED W/ THE CORRECT PROXIES
            # THIS IS AN ISSUE W/ THE CUSTOMIZE VIEW

    # TODO: move this assert logic to the customize view (and to a test)
    for scientific_property_customizers_qs in scientific_property_customizers.values():
        for spc in scientific_property_customizers_qs:
            assert spc.name == spc.proxy.name
            
#TODO: assert statment to make sure customizers / proxies / realizations all match up w/ one another
#TODO: will have to include _all_ properties in the forms (and just hide them in the template) so that they are there when I save things

    # note that the proxies need to be sorted according to the customizers (which are ordered by default),
    # so that when I pass an iterator of customizers to the formsets, they will match the underlying form that is created for each property

    model_parameters = {
        "project": project,
        "version": version,
        "proxy": model_proxy,
    }
    INITIAL_PARAMETER_LENGTH = len(model_parameters)
    # TODO: check if the user added any parameters to the request; if so, pass those parameters to "questionnaire_edit_existing()"
    # TODO: HAVE TO DO THIS DIFFERENTLY THAN CUSTOMIZERS (see "views_customize.py"), SINCE FIELDS ARE FKS TO PROPERTIES

    # setup the model(s)...

    # here is the "root" model
    model = MetadataModel(**model_parameters)
    model.is_root = True

    # it has to go in a list in-case it is part of a hierarchy
    # (the formsets assume a hierarchy; if not, it will just be a formset w/ 1 form)
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

    model_parent_dictionary = {}
    for model in models:
        if model.parent:
            model_parent_dictionary[model.get_model_key()] = model.parent.get_model_key()
        else:
            model_parent_dictionary[model.get_model_key()] = None
            
    standard_properties = {}
    standard_property_parameters = {
        # in theory, constant kwargs would go here
        # it just so happens that standardproperties don't have any
    }
    scientific_properties = {}
    scientific_property_parameters = {
        # in theory, constant kwargs would go here
        # it just so happens that scientificproperties don't have any
    }
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
            # but be sure to add an empty set of customizers to pass to the create_scientific_property_form_data fn
            scientific_property_customizers[model_key] = []
            pass

    # passed to formset factories below to make sure the prefixes match up
    model_keys = [u"%s_%s" % (model.vocabulary_key, model.component_key) for model in models]
    
    if request.method == "GET":

        models_data = [create_model_form_data(model, model_customizer) for model in models]
        model_formset = MetadataModelFormSetFactory(
            request=request,
            initial=models_data,
            extra=len(models_data),
            prefixes=model_keys,
            customizer=model_customizer,
        )

        standard_properties_formsets = {}
        scientific_properties_formsets = {}
        for model in models:
            model_key = u"%s_%s" % (model.vocabulary_key, model.component_key)

            standard_properties_data = [
                create_standard_property_form_data(model, standard_property, standard_property_customizer)
                for standard_property, standard_property_customizer in
                zip(standard_properties[model_key], standard_property_customizers)
                if standard_property_customizer.displayed
            ]

            standard_properties_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
                instance=model,
                prefix=model_key,
                request=request,
                initial=standard_properties_data,
                extra=len(standard_properties_data),
                customizers=standard_property_customizers,
            )

            scientific_properties_data = [
                create_scientific_property_form_data(model, scientific_property, scientific_property_customizer)
                for scientific_property, scientific_property_customizer in
                zip(scientific_properties[model_key], scientific_property_customizers[model_key])
                if scientific_property_customizer.displayed
            ]

            assert(len(scientific_properties_data)==len(scientific_properties[model_key]))

            scientific_properties_formsets[model_key] = MetadataScientificPropertyInlineFormSetFactory(
                instance=model,
                prefix=model_key,
                request=request,
                initial=scientific_properties_data,
                extra=len(scientific_properties_data),
                customizers=scientific_property_customizers[model_key],
            )


        
        request.session["checked_arguments"] = False
        request.session["root_model_id"] = None

    else: # request.method == "POST":

        validity = []

        # so in the POST, I don't have to initialize the models & properties
        # I can go directly to creating the forms based on teh request data

        model_formset = MetadataModelFormSetFactory(
            request=request,
            prefixes=model_keys,
            customizer=model_customizer,
        )

        
        model_formset_validity = model_formset.is_valid()
        if model_formset_validity:
            model_instances = model_formset.save(commit=False)

        validity += [model_formset_validity]

        standard_properties_formsets = {}
        scientific_properties_formsets = {}
        for (i, model_key) in enumerate(model_keys):
            standard_properties_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
                instance=model_instances[i] if model_formset_validity else models[i],
                prefix=model_key,
                request=request,
                customizers=standard_property_customizers,
            )

            validity += [standard_properties_formsets[model_key].is_valid()]

            scientific_properties_formsets[model_key] = MetadataScientificPropertyInlineFormSetFactory(
                instance=model_instances[i] if model_formset_validity else models[i],
                prefix=model_key,
                request=request,
                customizers=scientific_property_customizers[model_key],
            )

            validity += [scientific_properties_formsets[model_key].is_valid()]

        request.session["checked_arguments"] = True
        
        if all(validity):

            
            for model_instance in model_instances:
                model_parent_key = model_parent_dictionary[model_instance.get_model_key()]
                if model_parent_key:
                    model_instance.parent = find_model_by_key(model_parent_key,model_instances)
                model_instance.save()
            root_model_id = model_instances[0].pk

            for standard_property_formset in standard_properties_formsets.values():
                standard_property_instances = standard_property_formset.save(commit=False)
                for standard_property_instance in standard_property_instances:
                    standard_property_instance.save()

            for scientific_property_formset in scientific_properties_formsets.values():
                scientific_property_instances = scientific_property_formset.save(commit=False)
                for scientific_property_instance in scientific_property_instances:
                    scientific_property_instance.save()

            # this is used for other fns that might need to know what the view returns
            # (such as those in the testing framework)
            request.session["root_model_id"] = root_model_id
            
            # using Django's built-in messaging framework to pass status messages (as per https://docs.djangoproject.com/en/dev/ref/contrib/messages/)
            messages.add_message(request, messages.SUCCESS, "Successfully saved model instances")
            edit_existing_url = reverse("edit_existing",kwargs={
                "project_name"      : project_name,
                "model_name"        : model_name,
                "version_name"      : version_name,
                "model_id"          : root_model_id,
            })
            return HttpResponseRedirect(edit_existing_url)

        else:

            # using Django's built-in messaging framework to pass status messages (as per https://docs.djangoproject.com/en/dev/ref/contrib/messages/)
            messages.add_message(request, messages.ERROR, "Error saving model instances")

    dict = {
        "site": get_current_site(request),  # provide a special message if this is not the production site
        "project": project,  # used for generating URLs in the footer, and in the title
        "version": version,  # used for generating URLs in the footer
        "model_proxy": model_proxy,  # used for generating URLs in the footer
        "vocabularies": vocabularies,
        "model_customizer": model_customizer,
        "model_formset": model_formset,
        "standard_properties_formsets": standard_properties_formsets,
        "scientific_properties_formsets": scientific_properties_formsets,
        "questionnaire_version": get_version(),  # used in the footer
        "can_publish": False,  # only models that have already been saved can be published
    }

    response = render_to_response('questionnaire/questionnaire_edit.html', dict,
                                  context_instance=RequestContext(request))

    return response


def questionnaire_edit_existing(request, project_name="", model_name="", version_name="", model_id="", **kwargs):
    ##todo: remove local import statement
    from questionnaire.views.views_error import questionnaire_error
    
    # try to get the project...
    try:
        project = MetadataProject.objects.get(name__iexact=project_name)
    except MetadataProject.DoesNotExist:
        msg = "Cannot find the <u>project</u> '%s'.  Has it been registered?" % (project_name)
        return questionnaire_error(request, msg)

    if not project.active:
        msg = "Project '%s' is inactive." % (project_name)
        return questionnaire_error(request, msg)

    # check authentication...
    # (not using @login_required b/c some projects ignore authentication)
    if project.authenticated:
        current_user = request.user
        if not current_user.is_authenticated():
            return redirect('/login/?next=%s' % (request.path))
        if not (request.user.is_superuser or request.user.metadata_user.is_user_of(project)):
            msg = "User '%s' does not have editing permission for project '%s'." % (request.user, project_name)
            if project.email:
                msg += "<br/>Please <a href='mailto:%s'>contact</a> the project for support." % (project.email)
            return questionnaire_error(request, msg)

    # try to get the version...
    try:
        version = MetadataVersion.objects.get(name__iexact=version_name, registered=True)
    except MetadataVersion.DoesNotExist:
        msg = "Cannot find the <u>version</u> '%s'.  Has it been registered?" % (version_name)
        return questionnaire_error(request, msg)

    # try to get the proxy...
    try:
        model_proxy = MetadataModelProxy.objects.get(version=version, name__iexact=model_name)
    except MetadataModelProxy.DoesNotExist:
        msg = "Cannot find the <u>model</u> '%s' in the <u>version</u> '%s'." % (model_name, version_name)
        return questionnaire_error(request, msg)
    if not model_proxy.is_document():
        msg = "<u>%s</u> is not a recognized document type in the CIM." % model_name
        return questionnaire_error(request, msg)

    # try to get the default model customizer for this project/version/proxy combination...
    try:
        model_customizer = MetadataModelCustomizer.objects.get(project=project, version=version, proxy=model_proxy, default=True)
    except MetadataModelCustomizer.DoesNotExist:
        msg = "There is no default customization associated with this project/model/version."
        return questionnaire_error(request, msg)

    # try to get the requested model...
    try:
        model = MetadataModel.objects.get(pk=model_id,name__iexact=model_name,project=project,version=version,proxy=model_proxy)
    except MetadataModel.DoesNotExist:
        msg = "Cannot find the specified model.  Please try again."
        return questionnaire_error(request,msg)
    root_model_id = model.pk
    models = model.get_descendants(include_self=True)

    model_keys = [model.get_model_key() for model in models]

    # getting the vocabularies into the right order is a 2-step process
    # b/c vocabularies do not have an "order" attribute (since they can be used by multiple projects/customizations),
    # but the model_customizer does record the desired order of active vocabularies (as a comma-separated list)
    vocabularies = model_customizer.vocabularies.all()
    vocabulary_order = [int(order) for order in model_customizer.vocabulary_order.split(',')]
    vocabularies = sorted(vocabularies, key=lambda vocabulary: vocabulary_order.index(vocabulary.pk))

    standard_property_customizers = model_customizer.standard_property_customizers.all().order_by("category__order","order")
    standard_properties = {
        model.get_model_key() : model.standard_properties.all()
        for model in models
    }
    for model_key,standard_property_list in standard_properties.iteritems():
        for standard_property, standard_property_customizer in zip(standard_property_list,standard_property_customizers):
            if not standard_property_customizer.displayed:
                standard_properties.remove(standard_property)
           
    scientific_property_customizers = {
        model.get_model_key() : model_customizer.scientific_property_customizers.filter(model_key=model.get_model_key()).order_by("category__order","order")
        for model in models
    }
    scientific_properties = {
        model.get_model_key() : model.scientific_properties.all()
        for model in models
    }

    for model_key in model_keys:
        standard_property_list = standard_properties[model_key]
        for standard_property, standard_property_customizer in zip(standard_property_list,standard_property_customizers):
            if not standard_property_customizer.displayed:
                standard_property_list.remove(standard_property)
        scientific_property_list = scientific_properties[model_key]
        for scientific_property, scientific_property_customizer in zip(scientific_property_list,scientific_property_customizers[model_key]):
            if not scientific_property_customizer.displayed:
                scientific_property_list.remove(scientific_property)

    # this is used for other fns that might need to know what the view returns
    # (such as those in the testing framework)
    request.session["root_model_id"] = root_model_id

    if request.method == "GET":

        model_formset = MetadataModelFormSetFactory(
            request = request,
            queryset = models,
            prefixes = model_keys,
            customizer = model_customizer,
        )

        standard_properties_formsets = {}
        scientific_properties_formsets = {}

        for model in models:

            model_key = model.get_model_key()
            
            standard_properties_formsets[model_key] = MetadataStandardPropertyInlineFormSetFactory(
                instance=model,
                prefix=model_key,
                request=request,
                queryset=standard_properties[model_key],
                customizers=standard_property_customizers,
            )

            scientific_properties_formsets[model_key] = MetadataScientificPropertyInlineFormSetFactory(
                instance=model,
                prefix=model_key,
                request=request,
                queryset=scientific_properties[model_key],
                customizers=scientific_property_customizers[model_key],
            )

        request.session["checked_arguments"] = False

    else: # request.method == "POST":

        request.session["checked_arguments"] = True
        pass

    # gather all the extra information required by the template
    dict = {
        "site": get_current_site(request),  # provide a special message if this is not the production site
        "project": project,  # used for generating URLs in the footer, and in the title
        "version": version,  # used for generating URLs in the footer
        "model_proxy": model_proxy,  # used for generating URLs in the footer
        "vocabularies": vocabularies,
        "model_customizer": model_customizer,
        "model_formset": model_formset,
        "standard_properties_formsets": standard_properties_formsets,
        "scientific_properties_formsets": scientific_properties_formsets,
        "questionnaire_version": get_version(),  # used in the footer
        "can_publish": True,  # only models that have already been saved can be published
    }

    return render_to_response('questionnaire/questionnaire_edit.html', dict, context_instance=RequestContext(request))


def questionnaire_edit_help(request):
    # gather all the extra information required by the template
    dict = {
        "site": get_current_site(request),
        "questionnaire_version": get_version(),
    }

    return render_to_response('questionnaire/questionnaire_edit_instructions.html', dict,
                              context_instance=RequestContext(request))

