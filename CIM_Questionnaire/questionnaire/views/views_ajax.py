
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


import time

from django.contrib import messages
from django.contrib.sites.models import get_current_site

from django.db.models import get_app, get_model

from django.template.loader import render_to_string
from django.template.context import RequestContext
from django.template.defaultfilters import slugify

from django.http import HttpResponse

from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer, MetadataModelCustomizer, MetadataStandardCategoryCustomizer, MetadataStandardPropertyCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary

from CIM_Questionnaire.questionnaire.forms.forms_customize import create_new_customizer_forms_from_models, create_existing_customizer_forms_from_models, create_customizer_forms_from_data, save_valid_forms
from CIM_Questionnaire.questionnaire.forms.forms_customize import MetadataModelCustomizerForm, MetadataStandardPropertyCustomizerInlineFormSetFactory, MetadataScientificPropertyCustomizerInlineFormSetFactory

from CIM_Questionnaire.questionnaire.utils import QuestionnaireError

from CIM_Questionnaire.questionnaire import get_version

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
    subform_prefix      = u"customize_subform_%s" % (property_proxy.name)

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
        model_customizer.name = property_parent.name

        new_customizer = True

    if request.method == "GET":

        if new_customizer:

            (model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets) = \
                create_new_customizer_forms_from_models(model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers,vocabularies_to_customize=vocabularies,is_subform=True)

        else:
            (model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets) = \
                create_existing_customizer_forms_from_models(model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers,vocabularies_to_customize=vocabularies,is_subform=True)

        # give all this subform nonesense it's own unique prefix, so the fields aren't confused w/ the parent form fields
        model_customizer_form.prefix = subform_prefix
        standard_property_customizer_formset.prefix = u"%s-%s" % (standard_property_customizer_formset.prefix, subform_prefix)
        for scientific_property_customizer_formsets_dict in scientific_property_customizer_formsets.values():
            for scientific_property_customizer_formset in scientific_property_customizer_formsets_dict.values():
                scientific_property_customizer_formset.prefix = u"%s-%s" % (scientific_property_customizer_formset.prefix, subform_prefix)

        msg = None
        status = 200 # return successful response for GET (don't actually process this in the AJAX JQuery call)


    else: # request.method == "POST":

        data = request.POST

        (validity, model_customizer_form, standard_property_customizer_formset, scientific_property_customizer_formsets) = \
            create_customizer_forms_from_data(data,model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers,vocabularies_to_customize=vocabularies,is_subform=True,subform_prefix=subform_prefix)

        if all(validity):
            model_customizer_instance = save_valid_forms(model_customizer_form,standard_property_customizer_formset,scientific_property_customizer_formsets)
            # not using Django's built-in messaging framework to pass status messages;
            # (don't want it to interfere w/ messages on main form)
            # instead, using header fields
            msg =  "Successfully saved customizer '%s' for %s." % (model_customizer_instance.name,property_customizer.name)
            status = 200

        else:
            msg = "Failed to save customizer."
            status = 400

    # csrf is needed for AJAX...
    try:
        csrf_token_value = request.COOKIES["csrftoken"]
    except KeyError:
        # (though it will be missing on calls from w/in testing framework)
        csrf_token_value = None

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
        "csrf_token_value"                        : csrf_token_value,
    }

    rendered_form = render_to_string("questionnaire/questionnaire_customize_subform.html", dictionary=dict, context_instance=RequestContext(request))
    response = HttpResponse(rendered_form,content_type='text/html',status=status)
    response["msg"] = msg
    return response

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
