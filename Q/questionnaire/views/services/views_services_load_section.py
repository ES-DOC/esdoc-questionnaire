####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from collections import OrderedDict
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.template.context import RequestContext
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _

from Q.questionnaire.forms.forms_customizations import QModelCustomizationSubForm, QCategoryCustomizationForm, QPropertyCustomizationForm
from Q.questionnaire.forms.forms_realizations import QModelRealizationForm, QCategoryRealizationFormSetFactory, QPropertyRealizationFormSetFactory
from Q.questionnaire.models.models_customizations import get_model_customization_by_key, get_category_customization_by_key, get_property_customization_by_key
from Q.questionnaire.models.models_realizations import get_model_realization_by_key
from Q.questionnaire.views.views_base import get_key_from_request, get_cached_object
from Q.questionnaire.views.services.views_services_base import validate_request
from Q.questionnaire.q_utils import QError
from Q.questionnaire import APP_LABEL


# this code handles the load-on-demand workflow; it is super-cool and slightly complex.
# the Q has so many moving parts, that rendering all the forms and formsets at once would be too slow.
# so at various points in the templates I use the "section" ng directive
# which calls this view the 1st time an ng model's ".display_detail" attribute is set to true
# that directive includes useful info like which type of section/model to retrieve and which specific model to get.
# using that info I can generate forms, render them in a template, and insert the template into the <section> element.

SECTION_MAP = {
    # a map of various useful bits of info needed to create forms;
    # each section includes some info about the model to retrieve,
    # and a dict of context entries to pass to a template.
    "model_customization": {
        "cached_models_key": _("{session_key}_customizations"),
        "get_model_fn": get_model_customization_by_key,
        "template": "_q_section_customize_submodel.html",
        "template_context": {
            "form": {
                "class": QModelCustomizationSubForm,
                "name": _("model_customization_form_{safe_key}"),
                "scope_prefix": _("current_model"),
            }
        }
    },
    "category_customization": {
        "cached_models_key": _("{session_key}_customizations"),
        "get_model_fn": get_category_customization_by_key,
        "template": "_q_section_customize_category.html",
        "template_context": {
            "form": {
                "class": QCategoryCustomizationForm,
                "name": _("category_customization_form_{safe_key}"),
                "scope_prefix": _("current_model.categories[{index}]"),
            }
        }
    },
    "property_customization": {
        "cached_models_key": _("{session_key}_customizations"),
        "get_model_fn": get_property_customization_by_key,
        "template": "_q_section_customize_property.html",
        "template_context": {
            "form": {
                "class": QPropertyCustomizationForm,
                "name": _("property_customization_form_{safe_key}"),
                "scope_prefix": _("current_model.properties[{index}]"),
            }
        }
    },
    "model_realization": {
        "cached_models_key": _("{session_key}_realizations"),
        "get_model_fn": get_model_realization_by_key,
        "template": "_q_section_view_model.html",
        "template_context": {
            "model_form": {
                "class": QModelRealizationForm,
                "name": _("model_form_{safe_key}"),
                "scope_prefix": _("current_model"),
            },
            "properties_formset": {
                "class": QPropertyRealizationFormSetFactory,
                "name": _("property_formset_{safe_key}"),
                "scope_prefix": _("current_model.properties"),
            },
            "categories_formset": {
                "class": QCategoryRealizationFormSetFactory,
                "name": _("category_formset_{safe_key}"),
                "scope_prefix": _("current_model.categories"),
            }
        }
    },
    "submodel_realization": {
        "cached_models_key": _("{session_key}_realizations"),
        "get_model_fn": get_model_realization_by_key,
        "template": "_q_section_view_submodel.html",
        "template_context": {
            "model_form": {
                "class": QModelRealizationForm,
                "name": _("model_form_{safe_key}"),
                "scope_prefix": _("current_model"),
            },
            "properties_formset": {
                "class": QPropertyRealizationFormSetFactory,
                "name": _("property_formset_{safe_key}"),
                "scope_prefix": _("current_model.properties"),
            },
            "categories_formset": {
                "class": QCategoryRealizationFormSetFactory,
                "name": _("category_formset_{safe_key}"),
                "scope_prefix": _("current_model.categories"),
            }
        }
    }
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
    model = get_model_fn(model_key, cached_models)
    if not model:
        raise QError("unable to find instance w/ key='{0}'".format(model_key))

    template_context = {}
    for context_key, context_value in section_info.get("template_context").iteritems():
        form_class = context_value["class"]
        template_context[context_key] = form_class(
            instance=model,
            name=context_value["name"].format(safe_key=model_key.replace('-', '_')),
            scope_prefix=context_value["scope_prefix"].format(index=model_index)
        )

    template = "{0}/sections/{1}".format(APP_LABEL, section_info["template"])
    return render_to_response(template, template_context, context_instance=RequestContext(request))
