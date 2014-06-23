
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
__date__ ="Jan 4, 2014 4:53:16 PM"

"""
.. module:: views_ajax

Summary of module goes here

"""


from django.template.loader import render_to_string
import time

from django.db.models                   import get_app, get_model
from django.forms.models                import modelform_factory
from django.template.loader             import render_to_string
from django.forms                       import *

from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer, MetadataModelCustomizer, MetadataStandardCategoryCustomizer, MetadataStandardPropertyCustomizer
from CIM_Questionnaire.questionnaire.forms.forms_customize import create_new_customizer_forms_from_models, create_existing_customizer_forms_from_models

from questionnaire.utils    import *
from questionnaire.forms    import *
from questionnaire.views    import *

def ajax_customize_subform(request,**kwargs):
    subform_id              = request.GET.get('i',None)
    
    if not subform_id:
        msg = "unable to customize subfrom (no id specified)"
        raise QuestionnaireError(msg)

    property_customizer = MetadataStandardPropertyCustomizer.objects.get(pk=subform_id)
    property_parent     = property_customizer.model_customizer
    property_proxy      = property_customizer.proxy
    model_proxy         = property_proxy.relationship_target_model
    # TODO: IN THE LONG-RUN, I WILL WANT TO ENSURE THAT THE CORRECT SCI PROPS ARE USED HERE
    vocabularies        = property_parent.vocabularies.none() # using none() to avoid dealing w/ sci props
    project             = property_parent.project
    version             = property_parent.version
    prefix              = u"customize_subform_%s_standard_property" % (property_proxy.name)

    customizer_filter_parameters = {
        "project"   : project,
        "version"   : version,
        "proxy"     : model_proxy,
        "name"      : property_parent.name
    }

    try:
        model_customizer = MetadataModelCustomizer.objects.get(**customizer_filter_parameters)

        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(model_customizer,vocabularies)

        new_customizer = False

    except MetadataModelCustomizer.DoesNotExist:

        (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers) = \
            MetadataCustomizer.get_new_customizer_set(project, version, model_proxy, vocabularies)

        new_customizer = True


    if request.method == "GET":

        if new_customizer:

            (model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets) = \
                create_new_customizer_forms_from_models(model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers,vocabularies_to_customize=vocabularies,is_subform=True)

        else:
            (model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets) = \
                create_existing_customizer_forms_from_models(model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers,vocabularies_to_customize=vocabularies,is_subform=True)

        # give all this subform nonesense it's own unique prefix, so the fields aren't confused w/ the parent form fields
        model_customizer_form.prefix = prefix
        standard_property_customizer_formset.prefix = prefix
        for scientific_property_customizer_formsets_dict in scientific_property_customizer_formsets.values():
            for scientific_property_customizer_formset in scientific_property_customizer_formsets_dict.values():
                scientific_property_customizer_formset.prefix = prefix

        status = 200 # return successful response for GET (don't actually process this in the AJAX JQuery call)
        
    else: # request.method == "POST":

        data = request.POST

        if new_customizer:
            model_customizer_form = MetadataModelCustomizerForm(data,all_vocabularies=vocabularies,prefix=prefix)
        else:
            model_customizer_form = MetadataModelCustomizerForm(data,instance=model_customizer,all_vocabularies=vocabularies)

        model_customizer_form_validity = model_customizer_form.is_valid()
        if model_customizer_form_validity:
            model_customizer_instance = model_customizer_form.save(commit=False)
            active_vocabularies       = model_customizer_form.cleaned_data["vocabularies"]
        else:
            active_vocabularies       = MetadataVocabulary.objects.filter(pk__in=model_customizer_form.get_current_field_value("vocabularies"))
        active_vocabulary_keys = [slugify(vocabulary.name) for vocabulary in active_vocabularies]

        validity = [model_customizer_form_validity]

        standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance    = model_customizer_instance if model_customizer_form_validity else model_customizer,
            data        = data,
            categories  = standard_category_customizers,
            prefix      = prefix,
        )

        validity += [standard_property_customizer_formset.is_valid()]

        scientific_property_customizer_formsets = {}
        for vocabulary_key,scientific_property_customizer_dict in scientific_property_customizers.iteritems():
            scientific_property_customizer_formsets[vocabulary_key] = {}
            for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
                model_key = u"%s_%s" % (vocabulary_key,component_key)
                scientific_property_customizer_formsets[vocabulary_key][component_key] = MetadataScientificPropertyCustomizerInlineFormSetFactory(
                    instance    = model_customizer_instance if model_customizer_form_validity else model_customizer,
                    data        = data,
                    prefix      = model_key,
                    categories  = scientific_category_customizers[vocabulary_key][component_key]
                )
                if vocabulary_key in active_vocabulary_keys:
                    validity += [scientific_property_customizer_formsets[vocabulary_key][component_key].is_valid()]

        standard_categories_to_process      = model_customizer_form.standard_categories_to_process

        standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance    = model_customizer,
            request     = request,
            prefix      = prefix,
        )

        validity += [standard_property_customizer_formset.is_valid()]

        if all(validity):

            save_valid_forms(model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets)

            # using Django's built-in messaging framework to pass status messages (as per https://docs.djangoproject.com/en/dev/ref/contrib/messages/)
            messages.add_message(request, messages.SUCCESS, "Successfully saved customizer '%s'." % (model_customizer_instance.name))
            status = 200

        else:
            messages.add_message(request, messages.ERROR, "Failed to save customizer.")
            status = 400

    # gather all the extra information required by the template
    dict = {
        "STATIC_URL"                              : "/static/",
        "site"                                    : get_current_site(request),
        "project"                                 : project,
        "version"                                 : version,
        "model_proxy"                             : model_proxy,
        "parent_customizer"                       : property_parent,
        "model_customizer_form"                   : model_customizer_form,
        "standard_property_customizer_formset"    : standard_property_customizer_formset,
        # scientific properties are not needed for subforms...
        #"scientific_property_customizer_formsets" : scientific_property_customizer_formsets,
        "questionnaire_version"                   : get_version(),
        # some stuff I may need to do b/c of AJAX issues...
        "csrf_token_value"                            : request.COOKIES["csrftoken"],
    }

    rendered_form = render_to_string("questionnaire/questionnaire_customize_subform.html", dictionary=dict, context_instance=RequestContext(request))
    return HttpResponse(rendered_form,content_type='text/html',status=status)

def ajax_customize_category(request,category_id="",**kwargs):

    category_name           = request.GET.get('n',None)
    category_key            = request.GET.get('k',None)
    category_description    = request.GET.get('d',None)
    category_order          = request.GET.get('o',None)
    category_class          = request.GET.get('m',None)

    if not category_class:
        msg = "unable to determine type of category (no class specified)"
        raise QuestionnaireError(msg)

    (category_app_name,category_model_name) = category_class.split(".")
    
    print category_class
    print category_app_name
    print category_model_name
    category_model = get_model(category_app_name,category_model_name)

    if not category_model:
        msg = "Unable to determine type of category (invalid class specified)"
        raise QuestionnaireError(msg)

    if category_model == MetadataStandardCategoryCustomizer:
        category_form_class = MetadataStandardCategoryCustomizerForm
    elif category_model == MetadataScientificCategoryCustomizer:
        category_form_class = MetadataScientificCategoryCustomizerForm
    else:
        msg = "Invalid type of category specified."
        raise QuestionnaireError(msg)
    
    temp_category = category_model(
        name            = category_name,
        key             = category_key,
        description     = category_description,
        order           = category_order,
    )

    category_form = category_form_class(instance=temp_category)

    dict = {
        "form"          : category_form,
        "questionnaire_version" : get_version(),
    }
    
    rendered_form = render_to_string("questionnaire/questionnaire_category.html", dictionary=dict, context_instance=RequestContext(request))
    return HttpResponse(rendered_form,content_type='text/html')
