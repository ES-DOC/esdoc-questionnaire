
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
.. module:: views_view

Summary of module goes here

"""

from django.contrib.sites.models import get_current_site
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext


from CIM_Questionnaire.questionnaire.models.metadata_project import MetadataProject
from CIM_Questionnaire.questionnaire.models.metadata_version import MetadataVersion
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer, MetadataModelCustomizer, MetadataStandardPropertyCustomizer, MetadataScientificPropertyCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel, MetadataStandardProperty, MetadataScientificProperty

from CIM_Questionnaire.questionnaire.forms.forms_edit import create_new_edit_forms_from_models, create_existing_edit_forms_from_models, create_edit_forms_from_data, save_valid_forms

from CIM_Questionnaire.questionnaire.views.views_edit import validate_view_arguments
from CIM_Questionnaire.questionnaire.views.views_error import questionnaire_error
from CIM_Questionnaire.questionnaire.views import *

from CIM_Questionnaire.questionnaire import get_version


def questionnaire_view_existing(request, project_name="", model_name="", version_name="", model_id="", **kwargs):

    # validate the arguments...
    (validity,project,version,model_proxy,model_customizer,msg) = validate_view_arguments(project_name=project_name,model_name=model_name,version_name=version_name)
    if not validity:
        return error(request,msg)
    request.session["checked_arguments"] = True

    # don't check authentication

    # try to get the requested model...
    try:
        model = MetadataModel.objects.get(pk=model_id,name__iexact=model_name,project=project,version=version,proxy=model_proxy)
    except MetadataModel.DoesNotExist:
        msg = "Cannot find the specified model.  Please try again."
        return questionnaire_error(request,msg)
    if not model.is_root:
        # TODO: DEAL W/ THIS USE-CASE
        msg = "Currently only root models can be viewed.  Please try again."
        return questionnaire_error(request,msg)
    models = model.get_descendants(include_self=True)

    # getting the vocabularies into the right order is a 2-step process
    # b/c vocabularies do not have an "order" attribute (since they can be used by multiple projects/customizations),
    # but the model_customizer does record the desired order of active vocabularies (as a comma-separated list)
    vocabularies = model_customizer.vocabularies.all()
    vocabulary_order = [int(order) for order in model_customizer.vocabulary_order.split(',')]
    vocabularies = sorted(vocabularies, key=lambda vocabulary: vocabulary_order.index(vocabulary.pk))

    # now try to get the default customizer set for this project/version/proxy combination...

    (model_customizer,standard_category_customizers,standard_property_customizers,nested_scientific_category_customizers,nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(model_customizer,vocabularies)

    scientific_property_customizers = {}
    for vocabulary_key,scientific_property_customizer_dict in nested_scientific_property_customizers.iteritems():
        for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
            model_key = u"%s_%s" % (vocabulary_key, component_key)
            # I have to restructure this; in the customizer views it makes sense to store these as a dictionary of dictionary
            # but here, they should only be one level deep (hence the use of "nested_" above
            scientific_property_customizers[model_key] = scientific_property_customizer_list

    # create the realization set
    (models, standard_properties, scientific_properties) = \
        MetadataModel.get_existing_realization_set(models, model_customizer, vocabularies=vocabularies)

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

    model_parent_dictionary = {}
    for model in models:
        if model.parent:
            model_parent_dictionary[model.get_model_key()] = model.parent.get_model_key()
        else:
            model_parent_dictionary[model.get_model_key()] = None


    # this is used for other fns that might need to know what the view returns
    # (such as those in the testing framework)
    assert(len(models)>0)
    root_model_id = models[0].get_root().pk
    request.session["root_model_id"] = root_model_id

    if request.method == "GET" or request.method == "POST": # IN THE VIEW YOU CAN'T SEND A POST, SO JUST IGNORE IT


        (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
            create_existing_edit_forms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers)

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

    return render_to_response('questionnaire/questionnaire_view.html', dict, context_instance=RequestContext(request))


def questionnaire_view_help(request):

    # gather all the extra information required by the template
    dict = {
        "site"                          : get_current_site(request),
        "questionnaire_version"         : get_version(),
    }

    return render_to_response('questionnaire/questionnaire_edit_instructions.html', dict, context_instance=RequestContext(request))

