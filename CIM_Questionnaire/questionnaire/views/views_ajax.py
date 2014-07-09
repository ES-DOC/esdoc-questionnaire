
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
import json

from django.contrib import messages
from django.contrib.sites.models import get_current_site

from django.db.models import get_app, get_model

from django.forms import *  #ModelChoiceField

from django.template.loader import render_to_string
from django.template.context import RequestContext
from django.template.defaultfilters import slugify

from django.http import HttpResponse

from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer, MetadataModelCustomizer, MetadataStandardCategoryCustomizer, MetadataStandardPropertyCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary
from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel, MetadataStandardProperty

from CIM_Questionnaire.questionnaire.forms.forms_customize import create_new_customizer_forms_from_models, create_existing_customizer_forms_from_models, create_customizer_forms_from_data, save_valid_forms
from CIM_Questionnaire.questionnaire.forms.forms_customize import MetadataModelCustomizerForm, MetadataStandardPropertyCustomizerInlineFormSetFactory, MetadataScientificPropertyCustomizerInlineFormSetFactory

from CIM_Questionnaire.questionnaire.forms.forms_edit import create_new_edit_subforms_from_models, create_existing_edit_subforms_from_models, get_data_from_existing_edit_forms

from CIM_Questionnaire.questionnaire.utils import QuestionnaireError, update_field_widget_attributes, set_field_widget_attributes

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
        instance_id = None
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
            instance_id = model_customizer_instance.pk
            status = 200

        else:
            msg = "Failed to save customizer."
            status = 400

    # csrf is needed for AJAX...
    # TODO: although since the addition of the same-origin checking in questionnaire.js this code may be redundant
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
    response["instance_id"] = instance_id
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

def ajax_select_realization(request,**kwargs):

    # I can get all of the info I need (version/proxy/project) from the customizer
    # and it will allow me to customize the resultant form as well
    # (I still need to check for existing properties (using property_id) to exclude items from the queryset below)
    customizer_id = request.GET.get('c', None)
    standard_property_id = request.GET.get("s", None)
    prefix = request.GET.get("p",None)
    n_forms = int(request.GET.get("n","0"))
    if n_forms > 0:
        n_forms -= 1    # don't forget to take into account the current form being added (it has already been created in the DOM)
    if not customizer_id and prefix:
        msg = "unable to select realization (no customizer id or form prefix specified)"
        raise QuestionnaireError(msg)
    if standard_property_id:
        standard_property = MetadataStandardProperty.objects.get(pk=standard_property_id)
        realizations_to_exclude = standard_property.relationship_value.all().values_list("id", flat=True)
    else:
        # property has not been saved yet
        standard_property = None
        realizations_to_exclude = []

    parent_standard_property_customizer = MetadataStandardPropertyCustomizer.objects.get(pk=customizer_id)
    assert(parent_standard_property_customizer.relationship_show_subform)
    realization_customizer = parent_standard_property_customizer.subform_customizer


    realization_parameters = {
        "project" : realization_customizer.project,
        "proxy"   : realization_customizer.proxy,
    }
    realization_qs = MetadataModel.objects.filter(**realization_parameters).exclude(id__in=realizations_to_exclude)

    class _RealizationSelectForm(forms.Form):
        realizations = ModelChoiceField(queryset=realization_qs,label=realization_customizer.model_title, required=True)

        def __init__(self, *args, **kwargs):
            super(_RealizationSelectForm,self).__init__(*args, **kwargs)
            update_field_widget_attributes(self.fields["realizations"], {"class" : "multiselect"})
            update_field_widget_attributes(self.fields["realizations"], {"class" : "required"})

    if request.method == "GET":

        form = _RealizationSelectForm()

        msg = None
        status = 200 # return successful response for GET (don't actually process this in the AJAX JQuery call)


    else: # request.method == "POST"

        data = request.POST
        form = _RealizationSelectForm(data)

        if form.is_valid():

            status = 200
            msg = None

            realization = form.cleaned_data["realizations"]
            realizations = MetadataModel.objects.filter(pk__in=[realization.pk])    # I have to pass an actual queryset (not a list) to formset constructors or else all hell will break loose

            # get the full customizer set for this project/version/proxy combination...
            (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
                MetadataCustomizer.get_existing_customizer_set(realization_customizer,MetadataVocabulary.objects.none())
            scientific_property_customizers = {}
            for vocabulary_key,scientific_property_customizer_dict in nested_scientific_property_customizers.iteritems():
                for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
                    model_key = u"%s_%s" % (vocabulary_key, component_key)
                    # I have to restructure this; in the customizer views it makes sense to store these as a dictionary of dictionary
                    # but here, they should only be one level deep (hence the use of "nested_" above
                    scientific_property_customizers[model_key] = scientific_property_customizer_list

            # get the full realization set...
            (models, standard_properties, scientific_properties) = \
                MetadataModel.get_existing_realization_set(realizations, model_customizer, standard_property_customizers)

            # clean it up a bit based on properties that have been customized not to be displayed
            for model in models:
                model_key = model.get_model_key()
                standard_property_list = standard_properties[model_key]
                standard_properties_to_remove = []
                for standard_property, standard_property_customizer in zip(standard_property_list,standard_property_customizers):
                    if not standard_property_customizer.displayed:
                        # this list is actually a queryset, so remove doesn't work
                        #standard_property_list.remove(standard_property)
                        # instead, I have to use exclude
                        standard_properties_to_remove.append(standard_property.pk)
                standard_property_list.exclude(id__in=standard_properties_to_remove)
                # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
                if model_key not in scientific_property_customizers:
                    scientific_property_customizers[model_key] = []
                scientific_property_list = scientific_properties[model_key]
                scientific_properties_to_remove = []
                for scientific_property, scientific_property_customizer in zip(scientific_property_list,scientific_property_customizers[model_key]):
                    if not scientific_property_customizer.displayed:
                        # (as above) this list is actually a queryset, so remove doesn't work
                        #scientific_property_list.remove(scientific_property)
                        # instead, I have to use exclude
                        scientific_properties_to_remove.append(scientific_property.pk)
                scientific_property_list.exclude(id__in=scientific_properties_to_remove)

            subform_min, subform_max = [int(val) if val != "*" else val for val in parent_standard_property_customizer.relationship_cardinality.split("|")]

            (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
                create_existing_edit_subforms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix=prefix, subform_min=subform_min, subform_max=subform_max, increment_prefix=n_forms)

            data = get_data_from_existing_edit_forms(model_formset,standard_properties_formsets,scientific_properties_formsets)

            # no need to use the management form, since I'm only ever adding a single form
            fields_to_remove_from_data = [u"%s-%s" % (model_formset.prefix,field_key) for field_key in model_formset.management_form.fields.keys()]
            for field_to_remove_from_data in fields_to_remove_from_data:
                if field_to_remove_from_data in data:
                    data.pop(field_to_remove_from_data)
            # but do need to pass the prefix to make sure that js updates all added fields appropriately
            adjusted_prefix = model_formset.forms[0].prefix
            data["prefix"] = adjusted_prefix

            # finally return a JSON version of all of the fields used in this subform
            json_data = json.dumps(data)
            response = HttpResponse(json_data,content_type="text/html",status=status)
            return response


        else:
            msg = u"Error selecting %s" % (realization_customizer.model_title)
            # okay, I'm overloading things a bit here
            # the problem is that if I actually send a "400" code, then AJAX (correctly) interprets that as an error
            # and all sorts of problems ensure
            # instead I can still treat it as a success - albeit a "202" success where "The request has been accepted for processing, but the processing has not been completed." [http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html]
            # then in the success handler of the AJAX call, I can just check for status_code != 200
            status = 202

    # csrf is needed for AJAX...
    # TODO: although since the addition of the same-origin checking in questionnaire.js this code may be redundant
    try:
        csrf_token_value = request.COOKIES["csrftoken"]
    except KeyError:
        # (though it will be missing on calls from w/in testing framework)
        csrf_token_value = None

    dict = {
        "STATIC_URL" : "/static/",
        "site" : get_current_site(request),
        "csrf_token_value" : csrf_token_value,
        "form" : form,
        "questionnaire_version" : get_version(),
    }

    rendered_form = render_to_string("questionnaire/questionnaire_select_realization.html", dictionary=dict, context_instance=RequestContext(request))
    response = HttpResponse(rendered_form,content_type='text/html',status=status)
    response["msg"] = msg

    return response
