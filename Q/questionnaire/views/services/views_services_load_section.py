####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"

from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.template.context import RequestContext
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _

from Q.questionnaire.views.views_base import get_key_from_request, get_cached_object
from Q.questionnaire.views.services.views_services_base import validate_request
from Q.questionnaire.forms.forms_customize_models import QModelCustomizationSubForm
from Q.questionnaire.forms.forms_customize_categories import QStandardCategoryCustomizationForm, QScientificCategoryCustomizationForm
from Q.questionnaire.forms.forms_customize_properties import QStandardPropertyCustomizationForm, QScientificPropertyCustomizationForm
from Q.questionnaire.models.models_customizations import get_related_model_customizations, get_related_standard_property_customizations
from Q.questionnaire.q_utils import QError, find_in_sequence
from Q.questionnaire import APP_LABEL


# this code handles the load-on-demand workflow; it is super-cool and slightly complicated.
# the idea is that the questionnaire app has so many moving parts,
# that rendering all of the forms and formsets at once would be too slow,
# so at various points in the templates (usually w/in accordions) I use the custom "section" ng directive
# to call this django view the 1st time some ng model's ".display_detail" attribute is "true",
# that directive (and hence this view) includes the type of section/model to retrieve and which model to get
# using that info I can generate the correct form, render the section template as a string, and insert that string back into <section> element


SECTION_MAP = {
    # a map of various useful bits of info needed to (re)create forms...
    "standard_category_customization": {
        "cached_models_set_key": _("{session_key}_customization_set"),
        "cached_models_key": "standard_category_customizations",
        "form_class": QStandardCategoryCustomizationForm,
        # TODO: CONSIDER USING "key" INSTEAD OF INDEX FOR THESE STRINGS
        "form_name": _("model_customization_standard_category_form_{index}"),
        "form_prefix": _("standard_categories_{index}"),
        "form_scope_prefix": _("model_customization.standard_categories[{index}]"),
        "template": "_q_section_customize_category.html",
    },
    "standard_property_customization": {
        "cached_models_set_key": _("{session_key}_customization_set"),
        "cached_models_key": "standard_property_customizations",
        "form_class": QStandardPropertyCustomizationForm,
        # TODO: CONSIDER USING "key" INSTEAD OF INDEX FOR THESE STRINGS
        "form_name": _("model_customization_standard_property_form_{index}"),
        "form_prefix": _("standard_properties_{index}"),
        "form_scope_prefix": _("model_customization.standard_properties[{index}]"),
        "template": "_q_section_customize_standard_property.html",
    },
    "scientific_category_customization": {
        "cached_models_set_key": _("{session_key}_customization_set"),
        "cached_models_key": "scientific_category_customizations",
        "form_class": QScientificCategoryCustomizationForm,
        # TODO: CONSIDER USING "key" INSTEAD OF INDEX FOR THESE STRINGS
        "form_name": _("model_customization_scientific_category_form_{index}"),
        "form_prefix": _("scientific_categories_{index}"),
        "form_scope_prefix": _("model_customization.scientific_categories[{index}]"),
        "template": "_q_section_customize_category.html",
    },
    "scientific_property_customization": {
        "cached_models_set_key": _("{session_key}_customization_set"),
        "cached_models_key": "scientific_property_customizations",
        "form_class": QScientificPropertyCustomizationForm,
        # TODO: CONSIDER USING "key" INSTEAD OF INDEX FOR THESE STRINGS
        "form_name": _("model_customization_scientific_property_form_{index}"),
        "form_prefix": _("scientific_properties_{index}"),
        "form_scope_prefix": _("model_customization.scientific_properties[{index}]"),
        "template": "_q_section_customize_scientific_property.html",
    },
}


def q_load_section(request, section_type=None):
    valid_request, msg = validate_request(request)
    if not valid_request:
        return HttpResponseForbidden(msg)

    if section_type not in SECTION_MAP:
        msg = "I don't know how to render a section w/ type '{0}'".format(section_type)
        return HttpResponseBadRequest(msg)
    section_info = SECTION_MAP[section_type]

    model_index = request.POST.get("index")
    model_key = request.POST.get("key")

    session_key = get_key_from_request(request)

    cached_models_set_key = section_info["cached_models_set_key"].format(session_key=session_key)
    cached_models_key = section_info["cached_models_key"].format(session_key=session_key)

    cached_models_set = get_cached_object(request.session, cached_models_set_key)
    if not cached_models_set:
        msg = "unable to locate cached_models_set"
        raise QError(msg)
    cached_models = cached_models_set[cached_models_key]

    model = find_in_sequence(lambda m: m.get_key() == model_key, cached_models)
    if not model:
        raise QError("unable to find model w/ key='{0}'".format(model_key))
    # cached_models, in the case of an existing model, is a queryset not a list
    # so the call to "index" won't work; that's ok though, I pass index in as a parameter above
    # model_index = cached_models.index(model)

    model_form_class = section_info["form_class"]

    model_form = model_form_class(
        instance=model,
        form_name=section_info["form_name"].format(index=model_index),
        prefix=section_info["form_prefix"].format(index=model_index),
        scope_prefix=section_info["form_scope_prefix"].format(index=model_index),
    )
    template = "{0}/sections/{1}".format(APP_LABEL, section_info["template"])
    _dict = {
        "form": model_form,
    }
    return render_to_response(template, _dict, context_instance=RequestContext(request))


SUBFORM_SECTION_MAP = {
    # a map of various useful bits of info needed to (re)create forms...
    "subform_customization": {
        "cached_models_set_key": _("{session_key}_customization_set"),
        "related_models_fn": get_related_model_customizations,
        "form_class": QModelCustomizationSubForm,
        "form_name": _("subform_model_customization_form_{key}"),
        "form_scope_prefix": _("{parent_scope}.relationship_subform_customization"),
        "template": "_q_section_customize_subform.html",
    },
    "subform_standard_property_customization": {
        "cached_models_set_key": _("{session_key}_customization_set"),
        "related_models_fn": get_related_standard_property_customizations,
        "form_class": QStandardPropertyCustomizationForm,
        "form_name": _("subform_standard_property_customization_form_{key}"),
        "form_scope_prefix": _("{parent_scope}.standard_properties[{index}]"),
        "template": "_q_section_customize_standard_property.html",
    }

}

# TODO: THIS FN CAN BE CONSOLIDATED W/ THE ABOVE FN

def q_load_subform_section(request, section_type=None):

    valid_request, msg = validate_request(request)
    if not valid_request:
        return HttpResponseForbidden(msg)

    if section_type not in SUBFORM_SECTION_MAP:
        msg = "I don't know how to render a subform section w/ type '{0}'".format(section_type)
        return HttpResponseBadRequest(msg)
    section_info = SUBFORM_SECTION_MAP[section_type]

    model_key = request.POST.get("key")
    model_index = request.POST.get("index")
    model_scope = request.POST.get("scope")

    session_key = get_key_from_request(request)

    cached_models_set_key = section_info["cached_models_set_key"].format(session_key=session_key)

    cached_models_set = get_cached_object(request.session, cached_models_set_key)
    if not cached_models_set:
        msg = "unable to locate cached_models_set"
        raise QError(msg)

    # I am forced to use this bit of indirection in-case the models in question are unsaved
    related_model_fn = section_info["related_models_fn"]
    related_models = related_model_fn(cached_models_set)

    model = find_in_sequence(lambda m: m.get_key() == model_key, related_models)
    if not model:
        raise QError("unable to find model w/ key='{0}'".format(model_key))

    model_form_class = section_info["form_class"]

    model_form = model_form_class(
        instance=model,
        form_name=section_info["form_name"].format(key=model_key.replace('-', '_')),
        # prefix=section_info["form_prefix"].format(index=model_index),
        scope_prefix=section_info["form_scope_prefix"].format(parent_scope=model_scope, index=model_index),
    )

    template = "{0}/sections/{1}".format(APP_LABEL, section_info["template"])
    _dict = {
        "proxy": model.proxy,
        "customization": model,
        "scope": section_info["form_scope_prefix"].format(parent_scope=model_scope, index=model_index),
        "form": model_form,
    }
    return render_to_response(template, _dict, context_instance=RequestContext(request))
