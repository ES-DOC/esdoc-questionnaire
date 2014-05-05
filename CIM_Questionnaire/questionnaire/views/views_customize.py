
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

__author__="allyn.treshansky"
__date__ ="Sep 30, 2013 3:04:42 PM"

"""
.. module:: views_customize

Summary of module goes here

"""
import time


from django.core.exceptions  import FieldError, MultipleObjectsReturned
from django.db.models.fields import *

from questionnaire.utils    import *
from questionnaire.models   import *
from questionnaire.forms    import *
from questionnaire.views    import *


def questionnaire_customize_new(request,project_name="",model_name="",version_name="",**kwargs):

    # try to get the project...
    try:
        project = MetadataProject.objects.get(name__iexact=project_name)
    except MetadataProject.DoesNotExist:
        msg = "Cannot find the <u>project</u> '%s'.  Has it been registered?" % (project_name)
        return error(request,msg)

    if not project.active:
        msg = "Project '%s' is inactive." % (project_name)
        return error(request,msg)

    # check authentication...
    # (not using @login_required b/c some projects ignore authentication)
    if project.authenticated:
        current_user = request.user
        if not current_user.is_authenticated():
            return redirect('/login/?next=%s'%(request.path))
        if not (request.user.is_superuser or request.user.metadata_user.is_admin_of(project)):
            msg = "User '%s' does not have permission to edit customizations for project '%s'." % (request.user,project_name)
            if project.email:
                msg += "<br/>Please <a href='mailto:%s'>contact</a> the project for support." % (project.email)
            return error(request,msg)

    # try to get the version...
    try:
        version = MetadataVersion.objects.get(name__iexact=version_name,registered=True)
    except MetadataVersion.DoesNotExist:
        msg = "Cannot find the <u>version</u> '%s'.  Has it been registered?" % (version_name)
        return error(request,msg)

    # try to get the model (proxy)...
    try:
        model_proxy = MetadataModelProxy.objects.get(version=version,name__iexact=model_name)
    except MetadataModelProxy.DoesNotExist:
        msg = "Cannot find the <u>model</u> '%s' in the <u>version</u> '%s'." % (model_name,version_name)
        return error(request,msg)

    # try to get relevant vocabularies...
    vocabularies = project.vocabularies.filter(document_type__iexact=model_name)

    customizer_filter_parameters = {
        "project" : project,
        "version" : version,
        "proxy"   : model_proxy,
    }
    INITIAL_PARAMETER_LENGTH=len(customizer_filter_parameters)

    # check if the user added any parameters to the request
    for (key,value) in request.GET.iteritems():
        value = re.sub('[\"\']','',value) # strip out any quotes
        field_type = type(MetadataModelCustomizer.get_field(key))
        if field_type == BooleanField:
            # special case for boolean fields
            if value.lower()=="true" or value=="1":
                customizer_filter_parameters[key] = True
            elif value.lower()=="false" or value=="0":
                customizer_filter_parameters[key] = False
            else:
                customizer_filter_parameters[key] = value
        elif field_type == CharField or field_type == TextField:
            # this ensures that the filter is case-insenstive for strings            
            # bear in mind that if I ever change to using get_or_create, the filter will have to be case-sensitive
            # see https://code.djangoproject.com/ticket/7789 for more info
            customizer_filter_parameters[key+"__iexact"] = value
        else:
            customizer_filter_parameters[key] = value        
    if len(customizer_filter_parameters) > INITIAL_PARAMETER_LENGTH:
        # if there were (extra) filter parameters passed
        # then try to get the customizer w/ those parameters
        try:
            existing_model_customizer_instance = MetadataModelCustomizer.objects.get(**customizer_filter_parameters)
            customize_existing_url = reverse("customize_existing",kwargs={
                "project_name"      : project_name,
                "model_name"        : model_name,
                "version_name"      : version_name,
                "customizer_name"   : existing_model_customizer_instance.name,
            })
            return HttpResponseRedirect(customize_existing_url)
        except FieldError:
            # raise an error if some of the filter parameters were invalid
            msg = "Unable to find a MetadataModelCustomizer with the following parameters: %s" % (", ").join([u'%s=%s'%(key,value) for (key,value) in customizer_filter_parameters.iteritems()])
            return error(request,msg)
        except MultipleObjectsReturned:
            # raise an error if those filter params weren't enough to uniquely identify a customizer
            msg = "Unable to find a <i>single</i> MetadataModelCustomizer with the following parameters: %s" % (", ").join([u'%s=%s'%(key,value) for (key,value) in customizer_filter_parameters.iteritems()])
            return error(request,msg)
        except MetadataModelCustomizer.DoesNotExist:
            # raise an error if there was no matching query
            msg = "Unable to find any MetadataModelCustomizer with the following parameters: %s" % (", ").join([u'%s=%s'%(key,value) for (key,value) in customizer_filter_parameters.iteritems()])
            return error(request,msg)

    model_customizer    = MetadataModelCustomizer(**customizer_filter_parameters)
    model_customizer.reset()

    standard_property_category_customizers  = [MetadataStandardCategoryCustomizer(proxy=standard_category_proxy,model_customizer=model_customizer) for standard_category_proxy in version.categorization.categories.all()]
    for standard_property_category_customizer in standard_property_category_customizers:
        standard_property_category_customizer.reset()

    standard_property_customizers = []
    for standard_property_proxy in model_proxy.standard_properties.all():
        standard_property_customizer = MetadataStandardPropertyCustomizer(
            model_customizer    = model_customizer,
            proxy               = standard_property_proxy,
            category            = find_in_sequence(lambda category: category.proxy.has_property(standard_property_proxy),standard_property_category_customizers),
        )
        standard_property_customizer.reset()
        standard_property_customizers.append(standard_property_customizer)

    scientific_property_customizers = {}
    for vocabulary in vocabularies:
        vocabulary_key = slugify(vocabulary.name)
        scientific_property_customizers[vocabulary] = {}
        for component_proxy in vocabulary.component_proxies.all():
            component_key = slugify(component_proxy.name)
            model_key = u"%s_%s" % (vocabulary_key,component_key)
            scientific_property_customizers[vocabulary][component_proxy] = []
            for property_proxy in component_proxy.scientific_properties.all():
                scientific_property_customizer = MetadataScientificPropertyCustomizer(
                    model_customizer    = model_customizer,
                    proxy               = property_proxy,
                    vocabulary_key      = vocabulary_key,
                    component_key       = component_key,
                    model_key           = model_key,
                )
                proxy_category = property_proxy.category
                if proxy_category:
                    scientific_category_customizer = MetadataScientificCategoryCustomizer(model_customizer=model_customizer,proxy=proxy_category,vocabulary_key=vocabulary_key,component_key=component_key,model_key=model_key)
                    scientific_category_customizer.reset()
                    scientific_property_customizer.category = scientific_category_customizer
                scientific_property_customizer.reset()
                scientific_property_customizers[vocabulary][component_proxy].append(scientific_property_customizer)

    if request.method == "GET":

        model_customizer_form = MetadataModelCustomizerForm(instance=model_customizer)

        initial_standard_property_customizer_formset_data = [
            get_initial_data(standard_property_customizer,{
                # TODO: WHICH FK or M2M FIELDS DO I HAVE TO ADD HERE?
                # (don't need to pass in model_customizer, b/c I'm using an "inline" formset?)
                "proxy"             : standard_property_customizer.proxy,
                "model_customizer"  : standard_property_customizer.model_customizer,
                "category"          : standard_property_customizer.category,
                "last_modified"     : time.strftime("%c"),
            })
            for standard_property_customizer in standard_property_customizers
        ]
        standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance    = model_customizer,
            request     = request,
            initial     = initial_standard_property_customizer_formset_data,
            extra       = len(initial_standard_property_customizer_formset_data),
            categories  = [(category.key,category.name) for category in standard_property_category_customizers]
        )
        
        scientific_property_customizer_formsets = {}
        for (vocabulary,component_dictionary) in scientific_property_customizers.iteritems():
            vocabulary_key = slugify(vocabulary.name)
            scientific_property_customizer_formsets[vocabulary_key] = {}
            for (component,property_list) in component_dictionary.iteritems():
                component_key = slugify(component.name)
                initial_scientific_property_customizer_formset_data = [
                    get_initial_data(scientific_property_customizer,{
                        "proxy"             : scientific_property_customizer.proxy,
                        "model_customizer"  : scientific_property_customizer.model_customizer,
                        "category"          : scientific_property_customizer.category,
                        "last_modified"     : time.strftime("%c"),
                    })
                    for scientific_property_customizer in property_list
                ]
                scientific_property_customizer_formsets[vocabulary_key][component_key] = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                    instance    = model_customizer,
                    request     = request,
                    prefix      = u"%s_%s" % (vocabulary_key,component_key),
                    initial     = initial_scientific_property_customizer_formset_data,
                    extra       = len(initial_scientific_property_customizer_formset_data),
                    categories  = [(category.key,category.name) for category in component.categories.all()]
                )

    else: # request.method == "POST"
        
        validity = []

        model_customizer_form = MetadataModelCustomizerForm(request.POST,instance=model_customizer)

        validity += [model_customizer_form.is_valid()]

        # at this point I know which vocabularies were selected
        # and I have lists of categories to save (once the model_customizer itself has been saved)
        active_vocabularies                 = model_customizer_form.cleaned_data["vocabularies"]
        standard_categories_to_process      = model_customizer_form.standard_categories_to_process
        scientific_categories_to_process    = model_customizer_form.scientific_categories_to_process

        standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance    = model_customizer,
            request     = request,
        )

        validity += [standard_property_customizer_formset.is_valid()]

        scientific_property_customizer_formsets = {}
        for (vocabulary,component_dictionary) in scientific_property_customizers.iteritems():
            vocabulary_key = slugify(vocabulary.name)
            scientific_property_customizer_formsets[vocabulary_key] = {}
            for (component_proxy,property_list) in component_dictionary.iteritems():
                component_key = slugify(component_proxy.name)
                scientific_property_customizer_formsets[vocabulary_key][component_key] = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                    instance    = model_customizer,
                    request     = request,
                    prefix      = u"%s_%s" % (vocabulary_key,component_key),
                    # TODO: UPDATE THIS W/ FORM CONTENT
                    categories  = [(category.key,category.name) for category in component_proxy.categories.all()]
                )
                if vocabulary in active_vocabularies:
                    validity += [scientific_property_customizer_formsets[vocabulary_key][component_key].is_valid()]

        if all(validity):
            
            # save the model customizer...
            model_customizer_instance = model_customizer_form.save(commit=False)
            model_customizer_instance.save()
            model_customizer_form.save_m2m()

            # save (or delete) the category customizers...
            active_standard_categories = []
            for standard_category_to_process in standard_categories_to_process:
                standard_category_customizer = standard_category_to_process.object
                if standard_category_customizer.pending_deletion:
                    standard_category_to_process.delete()
                else:
                    standard_category_customizer.model_customizer = model_customizer_instance
                    standard_category_to_process.save()
                    active_standard_categories.append(standard_category_customizer)

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

            # save the standard property customizers...
            standard_property_customizer_instances = standard_property_customizer_formset.save(commit=False)
            for standard_property_customizer_instance in standard_property_customizer_instances:
                category_key = slugify(standard_property_customizer_instance.category_name)
                category = find_in_sequence(lambda category: category.key==category_key,active_standard_categories)
                standard_property_customizer_instance.category = category
                standard_property_customizer_instance.save()

            # save the scientific property customizers...
            for (vocabulary_key,component_dictionary) in scientific_property_customizer_formsets.iteritems():
                if find_in_sequence(lambda vocabulary: slugify(vocabulary.name)==vocabulary_key,active_vocabularies):
                    for (component_key,scientific_property_customizer_formset) in component_dictionary.iteritems():
                        scientific_property_customizer_instances = scientific_property_customizer_formset.save(commit=False)
                        for scientific_property_customizer_instance in scientific_property_customizer_instances:
                            category_key = slugify(scientific_property_customizer_instance.category_name)
                            category = find_in_sequence(lambda category: category.key==category_key,active_scientific_categories[vocabulary_key][component_key])
                            scientific_property_customizer_instance.category = category
                            scientific_property_customizer_instance.save()

            # using Django's built-in messaging framework to pass status messages (as per https://docs.djangoproject.com/en/dev/ref/contrib/messages/)
            messages.add_message(request, messages.SUCCESS, "Successfully saved customizer '%s'." % (model_customizer_instance.name))
            customize_existing_url = reverse("customize_existing",kwargs={
                "project_name"      : project_name,
                "model_name"        : model_name,
                "version_name"      : version_name,
                "customizer_name"   : model_customizer_instance.name,
            })
            return HttpResponseRedirect(customize_existing_url)

        else:

            print "model_customizer_form.errors: %s" % (model_customizer_form.errors)
            print "standard_property_customizer_formset.non_form_errors: %s" % (standard_property_customizer_formset.non_form_errors())
            for form in standard_property_customizer_formset:
                print "standard_property_customizer_form.errors: (%s:%s) %s" % (form.instance.name,form.type,form.errors)
                
            messages.add_message(request, messages.ERROR, "Failed to save customizer.")

    dict = {
        "site"                                    : get_current_site(request),
        "project"                                 : project,
        "version"                                 : version,
        "vocabularies"                            : vocabularies,
        "model_proxy"                             : model_proxy,
        "model_customizer_form"                   : model_customizer_form,
        "standard_property_customizer_formset"    : standard_property_customizer_formset,
        "scientific_property_customizer_formsets" : scientific_property_customizer_formsets,
        "questionnaire_version"                   : get_version(),
    }

    return render_to_response('questionnaire/questionnaire_customize.html', dict, context_instance=RequestContext(request))


def questionnaire_customize_existing(request,project_name="",model_name="",version_name="",customizer_name="",**kwargs):

    # try to get the project...
    try:
        project = MetadataProject.objects.get(name__iexact=project_name)
    except MetadataProject.DoesNotExist:
        msg = "Cannot find the <u>project</u> '%s'.  Has it been registered?" % (project_name)
        return error(request,msg)

    if not project.active:
        msg = "Project '%s' is inactive." % (project_name)
        return error(request,msg)

    # check authentication...
    # (not using @login_required b/c some projects ignore authentication)
    if project.authenticated:
        current_user = request.user
        if not current_user.is_authenticated():
            return redirect('/login/?next=%s'%(request.path))
        if not (request.user.is_superuser or request.user.metadata_user.is_admin_of(project)):
            msg = "User '%s' does not have permission to edit customizations for project '%s'." % (request.user,project_name)
            if project.email:
                msg += "<br/>Please <a href='mailto:%s'>contact</a> the project for support." % (project.email)
            return error(request,msg)

    # try to get the version...
    try:
        version = MetadataVersion.objects.get(name__iexact=version_name,registered=True)
    except MetadataVersion.DoesNotExist:
        msg = "Cannot find the <u>version</u> '%s'.  Has it been registered?" % (version_name)
        return error(request,msg)

    # try to get the model (proxy)...
    try:
        model_proxy = MetadataModelProxy.objects.get(version=version,name__iexact=model_name)
    except MetadataModelProxy.DoesNotExist:
        msg = "Cannot find the <u>model</u> '%s' in the <u>version</u> '%s'." % (model_name,version_name)
        return error(request,msg)

    # try to get the customizer...
    try:
        model_customizer = MetadataModelCustomizer.objects.get(name__iexact=customizer_name,proxy=model_proxy,project=project,version=version)
    except MetadataModelCustomizer.DoesNotExist:
        msg = "Cannot find the <u>customizer</u> '%s' for that project/version/model combination" % (customizer_name)
        return error(request,msg)

    # and the associated standard properties & categories...
    standard_property_customizers = model_customizer.standard_property_customizers.all()
    standard_property_category_customizers = model_customizer.standard_property_category_customizers.all()

    # and the associated scientific properties & categories...
    scientific_property_customizers = {}
    for scientific_property_customizer in model_customizer.scientific_property_customizers.all():
        vocabulary_key = scientific_property_customizer.vocabulary_key
        component_key  = scientific_property_customizer.component_key
        if not vocabulary_key in scientific_property_customizers:
            scientific_property_customizers[vocabulary_key] = {}
        if not component_key in scientific_property_customizers[vocabulary_key]:
            scientific_property_customizers[vocabulary_key][component_key] = []
        scientific_property_customizers[vocabulary_key][component_key].append(scientific_property_customizer)
    scientific_property_category_customizers = model_customizer.scientific_property_category_customizers.all()


    if request.method == "GET":

        model_customizer_form = MetadataModelCustomizerForm(instance=model_customizer)

        standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance    = model_customizer,
            request     = request,
            categories  = [(category.key,category.name) for category in standard_property_category_customizers]
        )

        scientific_property_customizer_formsets = {}
        for (vocabulary_key,component_dictionary) in scientific_property_customizers.iteritems():            
            if not vocabulary_key in scientific_property_customizer_formsets:
                scientific_property_customizer_formsets[vocabulary_key] = {}
            for (component_key,property_list) in scientific_property_customizers[vocabulary_key].iteritems():
                scientific_property_customizer_formsets[vocabulary_key][component_key] = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                    instance = model_customizer,
                    request  = request,
                    prefix   = u"%s_%s" % (vocabulary_key,component_key),
                    # TODO: IS THIS THE MOST EFFICIENT WAY TO GET THE PROPERTIES?
                    queryset = MetadataScientificPropertyCustomizer.objects.filter(pk__in=[property.pk for property in property_list]),
                    categories = [(category.key,category.name) for category in scientific_property_category_customizers.filter(vocabulary_key=vocabulary_key,component_key=component_key)]
                )
        
    else: # request.method == "POST":

        validity = []

        model_customizer_form = MetadataModelCustomizerForm(request.POST,instance=model_customizer)

        validity += [model_customizer_form.is_valid()]

        # at this point I know which vocabularies were selected
        # and I have lists of categories to save (once the model_customizer itself has been saved)
        active_vocabularies                 = model_customizer_form.cleaned_data["vocabularies"]
        active_vocabulary_keys              = [slugify(vocabulary.name) for vocabulary in active_vocabularies]
        standard_categories_to_process      = model_customizer_form.standard_categories_to_process
        scientific_categories_to_process    = model_customizer_form.scientific_categories_to_process
        
        standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance    = model_customizer,
            request     = request,
            categories  = [(category.key,category.name) for category in standard_property_category_customizers]
        )

        validity += [standard_property_customizer_formset.is_valid()]

        scientific_property_customizer_formsets = {}
        for (vocabulary_key,component_dictionary) in scientific_property_customizers.iteritems():
            if not vocabulary_key in scientific_property_customizer_formsets:
                scientific_property_customizer_formsets[vocabulary_key] = {}
            for (component_key,property_list) in scientific_property_customizers[vocabulary_key].iteritems():
                scientific_property_customizer_formsets[vocabulary_key][component_key] = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                    instance    = model_customizer,
                    request     = request,
                    prefix      = u"%s_%s" % (vocabulary_key,component_key),
                    # TODO: IS THIS THE MOST EFFICIENT WAY TO GET THE PROPERTIES?
                    queryset = MetadataScientificPropertyCustomizer.objects.filter(pk__in=[property.pk for property in property_list]),
                    categories  = [(category.key,category.name) for category in scientific_property_category_customizers.filter(vocabulary_key=vocabulary_key,component_key=component_key)]
                )
                if vocabulary_key in active_vocabulary_keys:
                    validity += [scientific_property_customizer_formsets[vocabulary_key][component_key].is_valid()]

        if all(validity):

            # save the model customizer...
            model_customizer_instance = model_customizer_form.save(commit=False)
            model_customizer_instance.save()
            model_customizer_form.save_m2m()

            # save (or delete) the category customizers...
            active_standard_categories = []
            for standard_category_to_process in standard_categories_to_process:
                standard_category_customizer = standard_category_to_process.object
                if standard_category_customizer.pending_deletion:
                    standard_category_to_process.delete()
                else:
                    standard_category_customizer.model_customizer = model_customizer_instance
                    standard_category_to_process.save()
                    active_standard_categories.append(standard_category_customizer)

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
                            scientific_category_customizer.component_key = component_key
                            scientific_category_customizer.vocabulary_key = vocabulary_key
                            scientific_category_to_process.save()
                            active_scientific_categories[vocabulary_key][component_key].append(scientific_category_customizer)
            
            # save the standard property customizers...
            standard_property_customizer_instances = standard_property_customizer_formset.save(commit=False)
            for standard_property_customizer_instance in standard_property_customizer_instances:
                category_key = slugify(standard_property_customizer_instance.category_name)
                category = find_in_sequence(lambda category: category.key==category_key,active_standard_categories)
                standard_property_customizer_instance.category = category
                standard_property_customizer_instance.save()

            # save the scientific property customizers...
            for (vocabulary_key,component_dictionary) in scientific_property_customizer_formsets.iteritems():
                if find_in_sequence(lambda vocabulary: slugify(vocabulary.name)==vocabulary_key,active_vocabularies):
                    for (component_key,scientific_property_customizer_formset) in component_dictionary.iteritems():
                        scientific_property_customizer_instances = scientific_property_customizer_formset.save(commit=False)
                        for scientific_property_customizer_instance in scientific_property_customizer_instances:
                            category_key = slugify(scientific_property_customizer_instance.category_name)
                            category = find_in_sequence(lambda category: category.key==category_key,active_scientific_categories[vocabulary_key][component_key])
                            scientific_property_customizer_instance.category = category
                            scientific_property_customizer_instance.save()

            # using Django's built-in messaging framework to pass status messages (as per https://docs.djangoproject.com/en/dev/ref/contrib/messages/)
            messages.add_message(request, messages.SUCCESS, "Successfully saved customizer '%s'." % (model_customizer_instance.name))

        else:

            messages.add_message(request, messages.ERROR, "Failed to save customizer.")

    # gather all the extra information required by the template
    dict = {
        "site"                                    : get_current_site(request),
        "project"                                 : project,
        "version"                                 : version,
        "vocabularies"                            : project.vocabularies.filter(document_type__iexact=model_name),
        "model_proxy"                             : model_proxy,
        "model_customizer_form"                   : model_customizer_form,
        "standard_property_customizer_formset"    : standard_property_customizer_formset,
        "scientific_property_customizer_formsets" : scientific_property_customizer_formsets,
        "questionnaire_version"                   : get_version(),
    }

    return render_to_response('questionnaire/questionnaire_customize.html', dict, context_instance=RequestContext(request))


def questionnaire_customize_help(request):

    # gather all the extra information required by the template
    dict = {
        "site"                          : get_current_site(request),
        "questionnaire_version"         : get_version(),
    }

    return render_to_response('questionnaire/questionnaire_customize_instructions.html', dict, context_instance=RequestContext(request))
