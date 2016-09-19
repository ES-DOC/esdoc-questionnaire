####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
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

from Q.questionnaire.forms.forms_customize_models import QModelCustomizationSubForm
from Q.questionnaire.forms.forms_customize_categories import QCategoryCustomizationForm
from Q.questionnaire.forms.forms_customize_properties import QPropertyCustomizationForm
from Q.questionnaire.forms.forms_edit_models import QModelRealizationForm
from Q.questionnaire.forms.forms_edit_properties import QPropertyRealizationFormSetFactory
from Q.questionnaire.models.models_customizations import get_model_customization_by_fn, get_category_customization_by_fn, get_property_customization_by_fn
from Q.questionnaire.models.models_realizations import get_model_realization_by_fn
from Q.questionnaire.views.views_base import get_key_from_request, get_cached_object
from Q.questionnaire.views.services.views_services_base import validate_request
from Q.questionnaire.q_utils import QError
from Q.questionnaire import APP_LABEL


# this code handles the load-on-demand workflow; it is super-cool and slightly complex.
# the idea is that the Q app has so many moving parts,
# that rendering all of the forms and formsets at once would be too slow,
# so at various points in the templates I use the custom "section" ng directive
# to call this view the 1st time some ng model's ".display_detail" attribute is "true",
# that directive (and hence this view) includes the type of section/model to retrieve and which model to get
# using that info I can generate the correct form, render the section template, and insert that template back into the <section> element.

SECTION_MAP = {
    # a map of various useful bits of info needed to (re)create forms...
    "subform_customization": {
        "cached_models_key": _("{session_key}_customizations"),
        "get_model_fn": get_model_customization_by_fn,
        "form_class": QModelCustomizationSubForm,
        "form_name": _("model_customization_form_{safe_key}"),
        "form_scope_prefix": _("current_model"),  # notice there is no kwarg passed to the string
        "template": "_q_section_customize_subform.html",
    },
    "category_customization": {
        "cached_models_key": _("{session_key}_customizations"),
        "get_model_fn": get_category_customization_by_fn,
        "form_class": QCategoryCustomizationForm,
        "form_name": _("category_customization_form_{safe_key}"),
        "form_scope_prefix": _("current_model.categories[{index}]"),
        "template": "_q_section_customize_category.html",
    },
    "property_customization": {
        "cached_models_key": _("{session_key}_customizations"),
        "get_model_fn": get_property_customization_by_fn,
        "form_class": QPropertyCustomizationForm,
        "form_name": _("property_customization_form_{safe_key}"),
        "form_scope_prefix": _("current_model.properties[{index}]"),
        "template": "_q_section_customize_property.html",
    },
    "model_realization": {
        "cached_models_key": _("{session_key}_realizations"),
        "get_model_fn": get_model_realization_by_fn,
        "form_class": QModelRealizationForm,
        "form_name": _("model_form_{safe_key}"),
        "form_scope_prefix": _("current_model"),  # notice there is no kwarg passed to the string
        "template": "_q_section_view_model.html",
        # models & properties are handled at the same time for realizations...
        "formset_class": QPropertyRealizationFormSetFactory,
        "formset_name": _("property_formset_{safe_key}"),
        "formset_scope_prefix": _("current_model.properties"),
    },
}


def q_load_section(request, section_type=None):
    valid_request, msg = validate_request(request)
    if not valid_request:
        return HttpResponseForbidden(msg)
    try:
        section_info = SECTION_MAP[section_type]
    except KeyError:
        msg = "I don't know how to render a section w/ type '{0}'".format(section_type)
        return HttpResponseBadRequest(msg)

    model_index = request.POST.get("index")
    model_key = request.POST.get("key")
    model_scope = request.POST.get("scope")

    session_key = get_key_from_request(request)
    cached_models_key = section_info["cached_models_key"].format(session_key=session_key)

    cached_models = get_cached_object(request.session, cached_models_key)
    if not cached_models:
        msg = "unable to locate cached_models"
        raise QError(msg)

    get_model_fn = section_info["get_model_fn"]
    model = get_model_fn(
        lambda c: c.get_key() == model_key,
        cached_models
    )
    if not model:
        raise QError("unable to find model w/ key='{0}'".format(model_key))

    model_form_class = section_info["form_class"]
    model_form = model_form_class(
        instance=model,
        form_name=section_info["form_name"].format(safe_key=model_key.replace('-', '_')),
        scope_prefix=section_info["form_scope_prefix"].format(index=model_index),
    )
    formset_class = section_info.get("formset_class", None)
    if formset_class:
        formset = formset_class(
            instance=model,
            formset_name=section_info["formset_name"].format(safe_key=model_key.replace('-', '_')),
            scope_prefix=section_info["formset_scope_prefix"].format(index=model_index),
        )
    else:
        formset = None

    template = "{0}/sections/{1}".format(APP_LABEL, section_info["template"])
    _dict = {
        "form": model_form,
        "formset": formset,
    }
    return render_to_response(template, _dict, context_instance=RequestContext(request))
