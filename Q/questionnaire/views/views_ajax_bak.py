####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2014 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"
__date__ = "Dec 01, 2014 3:00:00 PM"

"""
.. module:: views_edit

views for AJAX
eventually, these will be replaced w/ the views in "views_api.py"
"""


import json
from django.http import HttpResponse

from Q.questionnaire.models.models_customizations import QStandardPropertyCustomization, get_existing_customization_set
from Q.questionnaire.models.models_proxies import get_existing_proxy_set
from Q.questionnaire.models.models_realizations_bak import MetadataStandardProperty, get_new_subrealization_set
from Q.questionnaire.forms.bak.forms_edit_bak import create_new_edit_subforms_from_models, get_data_from_existing_edit_forms
from Q.questionnaire.views.views_realizations_bak import convert_customization_set, convert_proxy_set, get_rid_of_non_displayed_subitems
from Q.questionnaire.q_utils import QError, get_joined_keys_dict

# NEW CODE!
# DOESN'T LET USERS SELECT EXISTING REALIZATIONS
# JUST RETURNS FORM DATA FOR A NEW REALIZATION
# DONE FOR v0.14.0.0
# WILL BE RENDERED OBSOLETE ONCE ANGULAR & REST ARE IN-PLACE

def ajax_select_realization(request, **kwargs):

    # I can get all of the info I need (version/proxy/project) from the customizer
    # (I still need to check for existing properties (using property_id) to exclude items from the queryset below)
    customizer_id = request.GET.get('c', None)
    standard_property_id = request.GET.get("s", None)
    prefix = request.GET.get("p", None)
    parent_vocabulary_key = request.GET.get("p_v_k", "")
    parent_component_key = request.GET.get("p_c_k", "")
    n_forms = int(request.GET.get("n", "0"))
    realizations_to_exclude = request.GET.get("e", [])
    if realizations_to_exclude:
        realizations_to_exclude = realizations_to_exclude.split(",")
    if n_forms > 0:
        n_forms -= 1    # don't forget to take into account the current form being added (it has already been created in the DOM)
    if not customizer_id and prefix:
        msg = "unable to select realization (no customizer id or form prefix specified)"
        raise QError(msg)
    if standard_property_id:
        standard_property = MetadataStandardProperty.objects.get(pk=standard_property_id)

    parent_standard_property_customizer = QStandardPropertyCustomization.objects.get(pk=customizer_id)
    assert parent_standard_property_customizer.relationship_show_subform
    realization_customizer = parent_standard_property_customizer.relationship_subform_customization

    vocabularies = realization_customizer.get_active_vocabularies()

    realization_parameters = {
        "project": realization_customizer.project,
        "proxy": realization_customizer.proxy,
    }

    status = 200

    customization_set = get_existing_customization_set(
        project=realization_customizer.project,
        ontology=realization_customizer.ontology,
        proxy=realization_customizer.proxy,
        customization_name=realization_customizer.name,
        customization_id=realization_customizer.pk,
    )
    customization_set = convert_customization_set(customization_set)
    customization_set["scientific_category_customizers"] = get_joined_keys_dict(customization_set["scientific_category_customizers"])
    customization_set["scientific_property_customizers"] = get_joined_keys_dict(customization_set["scientific_property_customizers"])
    proxy_set = get_existing_proxy_set(
        ontology=realization_customizer.ontology,
        proxy=realization_customizer.proxy,
        vocabularies=vocabularies,
    )
    proxy_set = convert_proxy_set(proxy_set)
    realization_set = get_new_subrealization_set(
        realization_customizer.project, realization_customizer.ontology, realization_customizer.proxy,
        proxy_set["standard_property_proxies"], proxy_set["scientific_property_proxies"],
        customization_set["model_customizer"], vocabularies,
        parent_vocabulary_key, parent_component_key,
    )

    get_rid_of_non_displayed_subitems(realization_set, proxy_set, customization_set)

    subform_min = int(parent_standard_property_customizer.get_cardinality_min())
    subform_max = parent_standard_property_customizer.get_cardinality_max()
    if subform_max != "*":
        subform_max = int(subform_max)

    (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
        create_new_edit_subforms_from_models(
            realization_set["models"], customization_set["model_customizer"],
            realization_set["standard_properties"], customization_set["standard_property_customizers"],
            realization_set["scientific_properties"], customization_set["scientific_property_customizers"],
            subform_prefix=prefix, subform_min=subform_min, subform_max=subform_max, increment_prefix=n_forms,
        )

    # b/c I will only be in this function if I clicked add/replace from w/in a loaded subform,
    # these forms must also be loaded (so that I can update things appropriately)
    # by default most forms have "loaded" set to "False" and then JS sets the loaded field at some point
    # but this situation is different
    for model_form in model_formset.forms:
        model_form.load()
    for standard_property_formset in standard_properties_formsets.values():
        for standard_property_form in standard_property_formset:
            standard_property_form.load()
    for scientific_propery_formset in scientific_properties_formsets.values():
        for scientific_propery_form in scientific_propery_formset:
            scientific_propery_form.load()

    # get the data that will be used to populate the form...
    data = get_data_from_existing_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets)

    # now clean it up a bit...

    # no need to use the management form, since I'm only ever adding a single form
    fields_to_remove_from_data = [u"%s-%s" % (model_formset.prefix, field_key) for field_key in model_formset.management_form.fields.keys()]
    for field_to_remove_from_data in fields_to_remove_from_data:
        if field_to_remove_from_data in data:
            data.pop(field_to_remove_from_data)

    # but do need to pass the prefix to make sure that js updates all added fields appropriately
    adjusted_prefix = model_formset.forms[0].prefix
    data["prefix"] = adjusted_prefix
    data["label"] = u"%s" % realization_set["models"][0].get_label()

    # ...okay, I'm done cleaning up the data

    # finally return a JSON version of all of the fields used in this subform
    json_data = json.dumps(data)
    response = HttpResponse(json_data, content_type="text/html", status=status)
    return response

    # # (also get the proxies b/c I'll need them when setting up new properties below)
    # standard_property_proxies = [standard_property_customizer.proxy for standard_property_customizer in standard_property_customizers]
    # scientific_property_proxies = {}
    # scientific_property_customizers = {}
    # for vocabulary_key,scientific_property_customizer_dict in nested_scientific_property_customizers.iteritems():
    #     for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
    #         model_key = u"%s_%s" % (vocabulary_key, component_key)
    #         # I have to restructure this; in the customizer views it makes sense to store these as a dictionary of dictionary
    #         # but here, they should only be one level deep (hence the use of "nested_" above
    #         scientific_property_customizers[model_key] = scientific_property_customizer_list
    #         scientific_property_proxies[model_key] = [scientific_property_customizer.proxy for scientific_property_customizer in scientific_property_customizer_list]
    #
    # # get the full realization set
    # (models, standard_properties, scientific_properties) = \
    #     MetadataModel.get_new_subrealization_set(model_customizer.project, model_customizer.version, model_customizer.proxy, standard_property_proxies, scientific_property_proxies, model_customizer, MetadataVocabulary.objects.none(), parent_vocabulary_key, parent_component_key)
    #
    # # clean it up a bit based on properties that have been customized not to be displayed
    # for i, model in enumerate(models):
    #
    #     model_key = model.get_model_key()
    #     submodel_key = model.get_model_key() + "-%s" % i
    #
    #     standard_property_list = standard_properties[submodel_key]
    #     standard_properties_to_remove = []
    #     for standard_property, standard_property_customizer in zip(standard_property_list,standard_property_customizers):
    #         if not standard_property_customizer.displayed:
    #             standard_properties_to_remove.append(standard_property)
    #     # this list might actually be a queryset, so remove doesn't work
    #     # instead, I have to use exclude
    #     if standard_properties_to_remove:
    #         standard_properties_to_remove_names = [sp.name for sp in standard_properties_to_remove]
    #         standard_property_list = [sp for sp in standard_property_list if sp.name not in standard_properties_to_remove_names]
    #         # for sp in standard_properties_to_remove:
    #         #     standard_property_list.remove(sp)
    #
    #     # TODO: JUST A LIL HACK UNTIL I CAN FIGURE OUT WHERE TO SETUP THIS LOGIC
    #     if submodel_key not in scientific_property_customizers:
    #         scientific_property_customizers[submodel_key] = []
    #
    #     scientific_property_list = scientific_properties[submodel_key]
    #     scientific_properties_to_remove = []
    #     for scientific_property, scientific_property_customizer in zip(scientific_property_list,scientific_property_customizers[submodel_key]):
    #         if not scientific_property_customizer.displayed:
    #             scientific_properties_to_remove.append(scientific_property)
    #     # (as above) this list might actually be a queryset, so remove doesn't work
    #     # instead, I have to use exclude
    #     if scientific_properties_to_remove:
    #         scientific_properties_to_remove_names = [sp.name for sp in scientific_properties_to_remove]
    #         scientific_property_list = [sp for sp in scientific_property_list if sp.name not in scientific_properties_to_remove_names]
    #
    # subform_min, subform_max = [int(val) if val != "*" else val for val in parent_standard_property_customizer.relationship_cardinality.split("|")]
    #
    # (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
    #     create_new_edit_subforms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix=prefix, subform_min=subform_min, subform_max=subform_max, increment_prefix=n_forms)
    #
    # # b/c I will only be in this function if I clicked add/replace from w/in a loaded subform,
    # # these forms must also be loaded (so that I can update things appropriately)
    # # by default most forms have "loaded" set to "False" and then JS sets the loaded field at some point
    # # but this situation is different
    # for model_form in model_formset.forms:
    #     model_form.load()
    # for standard_property_formset in standard_properties_formsets.values():
    #     for standard_property_form in standard_property_formset:
    #         standard_property_form.load()
    # for scientific_propery_formset in scientific_properties_formsets.values():
    #     for scientific_propery_form in scientific_propery_formset:
    #         scientific_propery_form.load()
    #
    # # get the data that will be used to populate the form...
    # data = get_data_from_existing_edit_forms(model_formset, standard_properties_formsets, scientific_properties_formsets)
    #
    # # now clean it up a bit...
    #
    # # no need to use the management form, since I'm only ever adding a single form
    # fields_to_remove_from_data = [u"%s-%s" % (model_formset.prefix, field_key) for field_key in model_formset.management_form.fields.keys()]
    # for field_to_remove_from_data in fields_to_remove_from_data:
    #     if field_to_remove_from_data in data:
    #         data.pop(field_to_remove_from_data)
    #
    # # but do need to pass the prefix to make sure that js updates all added fields appropriately
    # adjusted_prefix = model_formset.forms[0].prefix
    # data["prefix"] = adjusted_prefix
    # data["label"] = u"%s" % models[0].get_label()
    #
    # # ...okay, I'm done cleaning up the data
    #
    # # finally return a JSON version of all of the fields used in this subform
    # json_data = json.dumps(data)
    # response = HttpResponse(json_data, content_type="text/html", status=status)
    # return response
    #
    #
