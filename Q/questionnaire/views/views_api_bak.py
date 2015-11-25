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
.. module:: views_api

Views for RESTful API.
These are accessed from AJAX
"""


from django.shortcuts import render_to_response
from django.template.context import RequestContext
from uuid import UUID as generate_uuid
from collections import OrderedDict

from Q.questionnaire.forms.bak.forms_base_bak import get_form_by_prefix
from Q.questionnaire.forms.bak.forms_edit_bak import create_new_edit_forms_from_models, create_existing_edit_forms_from_models
from Q.questionnaire.models.models_customizations import QModelCustomization as MetadataModelCustomizer, QStandardPropertyCustomization as MetadataStandardPropertyCustomizer, QScientificPropertyCustomization as MetadataScientificPropertyCustomizer, get_existing_customization_set
from Q.questionnaire.models.models_realizations_bak import MetadataModel, get_new_realization_set, get_existing_realization_set
from Q.questionnaire.models.models_projects import QProject as MetadataProject
from Q.questionnaire.models.models_proxies import QModelProxy as MetadataModelProxy, QComponentProxy as MetadataComponentProxy, QStandardCategoryProxy as MetadataStandardCategoryProxy, QScientificCategoryProxy as MetadataScientificCategoryProxy, QStandardPropertyProxy as MetadataStandardPropertyProxy, QScientificPropertyProxy as MetadataScientificPropertyProxy, get_existing_proxy_set
from Q.questionnaire.models.models_ontologies import QOntology as MetadataVersion
from Q.questionnaire.models.models_vocabularies import QVocabulary as MetadataVocabulary, DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY
from Q.questionnaire.views.views_base import get_key_from_request, get_or_create_cached_object
from Q.questionnaire.views.views_realizations_bak import convert_customization_set, convert_proxy_set
from Q.questionnaire.views.views_inheritance_bak import get_cached_inheritance_data
from Q.questionnaire.views.views_errors import q_error as questionnaire_error
from Q.questionnaire.q_utils import get_joined_keys_dict

STANDARD_PROPERTY_TYPE = "standard_properties"
SCIENTIFIC_PROPERTY_TYPE = "scientific_properties"
VALID_PROPERTY_TYPES = [STANDARD_PROPERTY_TYPE, SCIENTIFIC_PROPERTY_TYPE, ]



def get_vocabulary_key_from_model_key(model_key):
    split_key = model_key.split('_')
    n_splits = len(split_key)
    return "_".join(split_key[:(n_splits/2)])


def get_component_key_from_model_key(model_key):
    split_key = model_key.split('_')
    n_splits = len(split_key)
    return "_".join(split_key[(n_splits/2):])


def get_active_standard_categories(model_customization):
    if model_customization.model_show_all_categories:
        return model_customization.standard_category_customizations.all()
    else:
        # exclude categories for which there are no corresponding properties
        return model_customization.standard_category_customizations.filter(standard_properties__displayed=True).distinct()

def get_active_standard_properties(model_customization):
    return model_customization.standard_properties.filter(displayed=True)

def get_active_standard_properties_for_category(model_customization, category):
    return model_customization.standard_properties.filter(displayed=True, category=category)

def get_active_standard_categories_and_properties(model_customization):
    categories_and_properties = OrderedDict()
    active_standard_categories = get_active_standard_categories(model_customization)
    for category in active_standard_categories:
        categories_and_properties[category] = get_active_standard_properties_for_category(model_customization, category)
    return categories_and_properties

def get_active_scientific_categories_by_key(model_customization, model_key):
    vocabulary_key = get_vocabulary_key_from_model_key(model_key)
    component_key = get_component_key_from_model_key(model_key)
    if vocabulary_key == DEFAULT_VOCABULARY_KEY and component_key == DEFAULT_COMPONENT_KEY:
        return []
    if model_customization.model_show_all_categories:
        return model_customization.scientific_category_customizations.filter(vocabulary_key=generate_uuid(vocabulary_key), component_key=generate_uuid(component_key))
    else:
        return model_customization.scientific_category_customizations.filter(vocabulary_key=generate_uuid(vocabulary_key), component_key=generate_uuid(component_key), scientific_properties__displayed=True).distinct()

def get_active_scientific_properties_by_key(model_customization,model_key):
    return model_customization.scientific_property_customizers.filter(model_key=model_key, displayed=True)

def get_active_scientific_properties_for_category(model_customization, category):
    return model_customization.scientific_properties.filter(displayed=True, category=category)

def get_active_scientific_categories_and_properties_by_key(model_customization, model_key):
    categories_and_properties = OrderedDict()
    for category in get_active_scientific_categories_by_key(model_customization, model_key):
        categories_and_properties[category] = get_active_scientific_properties_for_category(model_customization, category)
    return categories_and_properties

# TODO: GET ALL THESE FNS TO WORK W/ CACHED INSTANCE OF FORMS RATHER THAN RE-CREATING THEM EACH TIME


def validate_edit_section_key(section_key):

    # section_key format is:
    # [ <version_key> |
    #   <model_key> |
    #   <vocabulary_key> |
    #   <component_key> |
    #   'standard_properties" or "scientific_properties"
    #   <category_key> |
    #   <property_key> |
    #
    # ]

    (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg) = \
        (True, None, None, None, None, None, None, None, "")

    section_keys = section_key.split('|')

    # try to get the version...
    try:
        version_key = section_keys[0]
        version = MetadataVersion.objects.get(key=version_key, is_registered=True)
    except IndexError:
        msg = "Invalid section key; did not specify version"
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)
    except MetadataVersion.DoesNotExist:
        msg = "Invalid section key; unable to find a registered version w/ key=%s" % version_key
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)

    # try to get the model proxy...
    try:
        model_proxy_key = section_keys[1]
        model_proxy = MetadataModelProxy.objects.get(ontology=version, name__iexact=model_proxy_key)
    except IndexError:
        msg = "Invalid section key; did not specify model"
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)
    except MetadataModelProxy.DoesNotExist:
        msg = "Invalid section key; unable to find a model w/ name=%s" % model_proxy_key
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)

    # try to get the vocabulary...
    vocabulary_key = section_keys[2]
    if not vocabulary_key:
        msg = "Invalid section key; did not specify vocabulary"
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)
    if vocabulary_key == DEFAULT_VOCABULARY_KEY:
        vocabulary = None
    else:
        try:
            vocabulary = MetadataVocabulary.objects.get(guid=generate_uuid(vocabulary_key))
        except MetadataVocabulary.DoesNotExist:
            msg = "Invalid section key; unable to find a vocabulary w/ guid=%s" % vocabulary_key
            validity = False
            return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)

    # try to get the component_proxy...
    component_proxy_key = section_keys[3]
    if not component_proxy_key:
        msg = "Invalid section key; did not specify component"
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)
    if component_proxy_key == DEFAULT_COMPONENT_KEY:
        component_proxy = None
    else:
        try:
            component_proxy = MetadataComponentProxy.objects.get(guid=generate_uuid(component_proxy_key), vocabulary=vocabulary)
        except MetadataComponentProxy.DoesNotExist:
            msg = "Invalid section key; unable to find a component w/ key=%s" % component_proxy_key
            validity = False
            return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)

    # from this point on the keys don't need to be present
    # (so I can just return on IndexError)

    # try to get the property type...
    try:
        property_type = section_keys[4]
        if property_type not in VALID_PROPERTY_TYPES:
            msg = "Invalid section key; must specify a property type from %s" % ", ".join(VALID_PROPERTY_TYPES)
            validity = False
            return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)
    except IndexError:
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)

    # try to get the category_proxy...
    try:
        category_proxy_key = section_keys[5]
        if property_type == STANDARD_PROPERTY_TYPE:
            category_proxy = MetadataStandardCategoryProxy.objects.get(key=category_proxy_key, categorization=version.categorization)
        else:  # property_type == SCIENTIFIC_PROPERTY_TYPES
            # scientific properties can only come from CVs, so I am sure that there will be a component
            category_proxy = MetadataScientificCategoryProxy.objects.get(key=category_proxy_key, component=component_proxy)
    except IndexError:
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)
    except MetadataStandardCategoryProxy.DoesNotExist:
            msg = "Invalid section key; cannot find a standard property category w/ key=%s from version %s" % (category_proxy_key, version)
            validity = False
            return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)
    except MetadataScientificCategoryProxy.DoesNotExist:
            msg = "Invalid section key; cannot find a scientific property category w/ key=%s from component %s" % (category_proxy_key, component_proxy)
            validity = False
            return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)

    # try to get the property_proxy...
    try:
        property_proxy_key = section_keys[6]
        if property_type == STANDARD_PROPERTY_TYPE:
            property_proxy = MetadataStandardPropertyProxy.objects.get(name__iexact=property_proxy_key, model_proxy=model_proxy, category=category_proxy)
        else:  # property_type == SCIENTIFIC_PROPERTY_TYPE
            property_proxy = MetadataScientificPropertyProxy.objects.get(name__iexact=property_proxy_key, component=component_proxy, category=category_proxy)
    except IndexError:
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)
    except MetadataStandardPropertyProxy.DoesNotExist:
        msg = "Invalid section key; cannot find a standard property w/ name=%s from model %s with category %s" % (property_proxy_key, model_proxy, category_proxy)
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)
    except MetadataScientificPropertyProxy.DoesNotExist:
        msg = "Invalid section key; cannot find a scientific property w/ name=%s from component %s with category %s" % (property_proxy_key, model_proxy, category_proxy)
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)

    # TODO: DEAL W/ SUBFORMS IN SECTION_KEY

    return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)


def validate_edit_view_arguments(project_name, section_key):

    (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, model_customizer, vocabularies, msg) = \
        (True, None, None, None, None, None, None, None, None, [], "")

    # try to get the project...
    try:
        project = MetadataProject.objects.get(name=project_name.lower())
    except MetadataProject.DoesNotExist:
        msg = "Cannot find the <u>project</u> '%s'.  Has it been registered?" % project_name
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, model_customizer, vocabularies, msg)
    if not project.is_active:
        msg = "Project '%s' is inactive." % project_name
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, model_customizer, vocabularies, msg)

    # get all the other necessary elements by parsing the section_key
    (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg) = \
        validate_edit_section_key(section_key)
    if not validity:
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, model_customizer, vocabularies, msg)

    # finally get the vocabularies...
    # (okay, I know that I may have only specified 1 or 0 vocabularies
    # but for now I still need to recreate the forms in their entirety - meaning all vocabularies)
    try:
        model_customizer = MetadataModelCustomizer.objects.get(project=project, ontology=version, proxy=model_proxy, is_default=True)
    except MetadataModelCustomizer.DoesNotExist:
        msg = "There is no default customization associated with this project/model/version."
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, model_customizer, vocabularies, msg)
    vocabularies = model_customizer.get_active_vocabularies()

    return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, model_customizer, vocabularies, msg)


def get_edit_section_template_path(property_proxy, property_type, category_proxy):

    section_template_path = "questionnaire/bak/"

    if property_proxy:
        if property_type == STANDARD_PROPERTY_TYPE:
            section_template = "_section_standard_property.html"
        else:  # property_type == SCIENTIFIC_PROPERTY_TYPE:
            section_template = "_section_scientific_property.html"
    elif category_proxy:
        if property_type == STANDARD_PROPERTY_TYPE:
            section_template = "_section_standard_category.html"
        else:  # property_type == SCIENTIFIC_PROPERTY_TYPE:
            section_template = "_section_scientific_category.html"
    elif property_type:
        if property_type == STANDARD_PROPERTY_TYPE:
            section_template = "_section_all_standard_categories.html"
        else:  # property_type == SCIENTIFIC_PROPERTY_TYPE:
            section_template = "_section_all_scientific_categories.html"
    # elif component_proxy and vocabulary:
    else:  # the only other section is the entire component; do I need to distinguish between a CV component and the default component?
        section_template = "_section_component.html"
    # TODO: add information in the dict to work out which property, etc. to get

    return section_template_path + section_template


def api_get_new_edit_form_section(request, project_name, section_key, **kwargs):

    # check the arguments to the view,
    # and parse the section key
    (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, model_customizer, vocabularies, msg) = \
        validate_edit_view_arguments(project_name, section_key)
    if not validity:
        return questionnaire_error(request, msg)

    # get (or set) models from the cache...
    session_key = get_key_from_request(request)
    cached_customization_set_key = "{0}_customization_set".format(session_key)
    cached_proxy_set_key = "{0}_proxy_set".format(session_key)
    cached_realization_set_key = "{0}_realization_set".format(session_key)
    customization_set = get_or_create_cached_object(request.session, cached_customization_set_key,
        get_existing_customization_set,
        **{
            "project": model_customizer.project,
            "ontology": version,
            "proxy": model_customizer.proxy,
            "customization_name": model_customizer.name,
        }
    )
    customization_set = convert_customization_set(customization_set)
    customization_set["scientific_category_customizers"] = get_joined_keys_dict(customization_set["scientific_category_customizers"])
    customization_set["scientific_property_customizers"] = get_joined_keys_dict(customization_set["scientific_property_customizers"])
    proxy_set = get_or_create_cached_object(request.session, cached_proxy_set_key,
        get_existing_proxy_set,
        **{
            "ontology": version,
            "proxy": model_proxy,
            "vocabularies": vocabularies,
        }
    )
    proxy_set = convert_proxy_set(proxy_set)
    realization_set = get_or_create_cached_object(request.session, cached_realization_set_key,
        get_new_realization_set,
        **{
            "project": model_customizer.project,
            "ontology": version,
            "model_proxy": proxy_set["model_proxy"],
            "standard_property_proxies": proxy_set["standard_property_proxies"],
            "scientific_property_proxies": proxy_set["scientific_property_proxies"],
            "model_customizer": customization_set["model_customizer"],
            "vocabularies": vocabularies,
        }
    )
    inheritance_data = get_cached_inheritance_data(session_key)

    # now create the formsets...
    (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
        create_new_edit_forms_from_models(
            realization_set["models"], customization_set["model_customizer"],
            realization_set["standard_properties"], customization_set["standard_property_customizers"],
            realization_set["scientific_properties"], customization_set["scientific_property_customizers"],
            inheritance_data=inheritance_data,
        )

    # now get some things that were previously computed in the master template
    # or in loops that I need to recreate for the individual sections
    section_keys = section_key.split('|')
    model_key = u"%s_%s" % (section_keys[2], section_keys[3])
    _dict = {
        "vocabularies": vocabularies,
        "model_customizer": model_customizer,
        "model_formset": model_formset,
        "standard_properties_formsets": standard_properties_formsets,
        "scientific_properties_formsets": scientific_properties_formsets,
        "section_parameters": {
            "model_form": get_form_by_prefix(model_formset, model_key),
            "standard_property_formset": standard_properties_formsets[model_key],
            "scientific_property_formset": scientific_properties_formsets[model_key],
            "active_standard_categories_and_properties": get_active_standard_categories_and_properties(customization_set["model_customizer"]),
            "active_scientific_categories_and_properties": get_active_scientific_categories_and_properties_by_key(customization_set["model_customizer"], model_key),
        },
    }

    template = get_edit_section_template_path(property_proxy, property_type, category_proxy)
    return render_to_response(template, _dict, context_instance=RequestContext(request))


def api_get_existing_edit_form_section(request, project_name, section_key, model_id, **kwargs):

    # check the arguments to the view,
    # and parse the section key
    (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, model_customizer, vocabularies, msg) = \
        validate_edit_view_arguments(project_name, section_key)
    if not validity:
        return questionnaire_error(request, msg)

    # and check requested model(s)...
    # (even though this view may return a small section for a single model,
    # the full set of models is needed to re-create the forms properly)
    try:
        root_model = MetadataModel.objects.get(pk=model_id)
    except MetadataModel.DoesNotExist:
        msg = "Cannot find the specified model.  Please try again."
        return questionnaire_error(request, msg)
    if not root_model.is_root:
        # TODO: DEAL W/ THIS USE-CASE
        msg = "Currently only root models can be viewed.  Please try again."
        return questionnaire_error(request, msg)

    # get (or set) models from the cache...
    session_key = get_key_from_request(request)
    cached_customization_set_key = "{0}_customization_set".format(session_key)
    cached_proxy_set_key = "{0}_proxy_set".format(session_key)
    cached_realization_set_key = "{0}_realization_set".format(session_key)
    customization_set = get_or_create_cached_object(request.session, cached_customization_set_key,
        get_existing_customization_set,
        **{
            "project": model_customizer.project,
            "ontology": version,
            "proxy": model_customizer.proxy,
            "customization_name": model_customizer.name,
        }
    )
    customization_set = convert_customization_set(customization_set)
    customization_set["scientific_category_customizers"] = get_joined_keys_dict(customization_set["scientific_category_customizers"])
    customization_set["scientific_property_customizers"] = get_joined_keys_dict(customization_set["scientific_property_customizers"])
    proxy_set = get_or_create_cached_object(request.session, cached_proxy_set_key,
        get_existing_proxy_set,
        **{
            "ontology": version,
            "proxy": model_proxy,
            "vocabularies": vocabularies,
        }
    )
    proxy_set = convert_proxy_set(proxy_set)
    realization_set = get_or_create_cached_object(request.session, cached_realization_set_key,
        get_existing_realization_set,
        **{
            "models": root_model.get_descendants(include_self=True),
            "model_customizer": customization_set["model_customizer"],
            "vocabularies": vocabularies,
        }
    )
    inheritance_data = get_cached_inheritance_data(session_key)

    # now create the formsets...
    (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
        create_existing_edit_forms_from_models(
            realization_set["models"], customization_set["model_customizer"],
            realization_set["standard_properties"], customization_set["standard_property_customizers"],
            realization_set["scientific_properties"], customization_set["scientific_property_customizers"],
            inheritance_data=inheritance_data
        )

    # now get some things that were previously computed in the master template
    # or in loops that I need to recreate for the individual sections
    section_keys = section_key.split('|')
    model_key = u"%s_%s" % (section_keys[2], section_keys[3])
    _dict = {
        "vocabularies": vocabularies,
        "model_customizer": model_customizer,
        "model_formset": model_formset,
        "standard_properties_formsets": standard_properties_formsets,
        "scientific_properties_formsets": scientific_properties_formsets,
        "section_parameters": {
            "model_form": get_form_by_prefix(model_formset, model_key),
            "standard_property_formset": standard_properties_formsets[model_key],
            "scientific_property_formset": scientific_properties_formsets[model_key],
            "active_standard_categories_and_properties": get_active_standard_categories_and_properties(customization_set["model_customizer"]),
            "active_scientific_categories_and_properties": get_active_scientific_categories_and_properties_by_key(customization_set["model_customizer"], model_key),
        },
    }

    template = get_edit_section_template_path(property_proxy, property_type, category_proxy)
    return render_to_response(template, _dict, context_instance=RequestContext(request))
