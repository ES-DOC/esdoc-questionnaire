
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

from questionnaire.utils    import *
from questionnaire.models   import *
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
    project             = property_parent.project
    version             = property_parent.version

    customizer_filter_parameters = {
        "project"   : project,
        "version"   : version,
        "proxy"     : model_proxy,
        "name"      : property_parent.name
    }
    try:
        model_customizer = MetadataModelCustomizer.objects.get(**customizer_filter_parameters)
        model_customizer.default = property_parent.default
        standard_property_category_customizers = model_customizer.standard_property_category_customizers.all()
        standard_property_customizers = model_customizer.standard_property_customizers.all()
        new_customizer   = False

    except MetadataModelCustomizer.DoesNotExist:
        model_customizer = MetadataModelCustomizer(**customizer_filter_parameters)
        model_customizer.default = property_parent.default
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
        new_customizer   = True

    if request.method == "GET":
        model_customizer_form = MetadataModelCustomizerForm(instance=model_customizer,is_subform=True)

        if new_customizer:
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
        else:
            standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
                instance    = model_customizer,
                request     = request,
                categories  = [(category.key,category.name) for category in standard_property_category_customizers]
            )
    else: # request.method == "POST":
        pass


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
    return HttpResponse(rendered_form,mimetype='text/html')

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
    return HttpResponse(rendered_form,mimetype='text/html')
