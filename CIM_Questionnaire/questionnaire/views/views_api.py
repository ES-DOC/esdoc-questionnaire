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
from CIM_Questionnaire.questionnaire.forms.forms_customize import create_new_customizer_forms_from_models, create_existing_customizer_forms_from_models
from CIM_Questionnaire.questionnaire.forms.forms_edit import create_new_edit_forms_from_models, create_existing_edit_forms_from_models
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataModelCustomizer, MetadataStandardPropertyCustomizer, MetadataScientificPropertyCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
from CIM_Questionnaire.questionnaire.models.metadata_project import MetadataProject
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy, MetadataComponentProxy, MetadataStandardCategoryProxy, MetadataScientificCategoryProxy, MetadataStandardPropertyProxy, MetadataScientificPropertyProxy
from CIM_Questionnaire.questionnaire.models.metadata_version import MetadataVersion
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary
from CIM_Questionnaire.questionnaire.views.views_base import get_key_from_request
from CIM_Questionnaire.questionnaire.views.views_base import get_cached_new_customization_set, get_cached_existing_customization_set, get_cached_proxy_set, get_cached_new_realization_set, get_cached_existing_realization_set
from CIM_Questionnaire.questionnaire.views.views_inheritance import get_cached_inheritance_data
from CIM_Questionnaire.questionnaire.views.views_error import questionnaire_error
from CIM_Questionnaire.questionnaire.utils import get_form_by_prefix, get_joined_keys_dict
from CIM_Questionnaire.questionnaire.utils import DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY

STANDARD_PROPERTY_TYPE = "standard_properties"
SCIENTIFIC_PROPERTY_TYPE = "scientific_properties"
VALID_PROPERTY_TYPES = [STANDARD_PROPERTY_TYPE, SCIENTIFIC_PROPERTY_TYPE, ]

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
        version = MetadataVersion.objects.get(key=version_key, registered=True)
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
        model_proxy = MetadataModelProxy.objects.get(version=version, name__iexact=model_proxy_key)
    except IndexError:
        msg = "Invalid section key; did not specify model"
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)
    except MetadataModelProxy.DoesNotExist:
        msg = "Invalid section key; unable to find a model w/ name=%s" % model_proxy_key
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)

    # try to get the vocabulary...
    try:
        vocabulary_key = section_keys[2]
        vocabulary = MetadataVocabulary.objects.get(guid=vocabulary_key)
    except IndexError:
        msg = "Invalid section key; did not specify vocabulary"
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)
    except MetadataVocabulary.DoesNotExist:
        if vocabulary_key == DEFAULT_VOCABULARY_KEY:
            vocabulary = None
        else:
            msg = "Invalid section key; unable to find a vocabulary w/ guid=%s" % vocabulary_key
            validity = False
            return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)

    # try to get the component_proxy...
    try:
        component_proxy_key = section_keys[3]
        component_proxy = MetadataComponentProxy.objects.get(guid=component_proxy_key, vocabulary=vocabulary)
    except IndexError:
        msg = "Invalid section key; did not specify component"
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg)
    except MetadataComponentProxy.DoesNotExist:
        if component_proxy_key == DEFAULT_COMPONENT_KEY and vocabulary_key == DEFAULT_VOCABULARY_KEY:
            component = None
        else:
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


def validate_customize_section_key(section_key):

    # section_key format is:
    # [ <version_key> |
    #   <model_key> |
    #   <vocabulary_key> |
    #   <component_key> |
    # ]

    (validity, version, model_proxy, vocabulary, component_proxy, msg) = \
        (True, None, None, None, None, "")

    section_keys = section_key.split('|')

    # try to get the version...
    try:
        version_key = section_keys[0]
        version = MetadataVersion.objects.get(key=version_key, registered=True)
    except IndexError:
        msg = "Invalid section key; did not specify version"
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, msg)
    except MetadataVersion.DoesNotExist:
        msg = "Invalid section key; unable to find a registered version w/ key=%s" % version_key
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, msg)

    # try to get the model proxy...
    try:
        model_proxy_key = section_keys[1]
        model_proxy = MetadataModelProxy.objects.get(version=version, name__iexact=model_proxy_key)
    except IndexError:
        msg = "Invalid section key; did not specify model"
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, msg)
    except MetadataModelProxy.DoesNotExist:
        msg = "Invalid section key; unable to find a model w/ name=%s" % model_proxy_key
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, msg)

    # try to get the vocabulary...
    try:
        vocabulary_key = section_keys[2]
        vocabulary = MetadataVocabulary.objects.get(guid=vocabulary_key)
    except IndexError:
        msg = "Invalid section key; did not specify vocabulary"
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, msg)
    except MetadataVocabulary.DoesNotExist:
        msg = "Invalid section key; unable to find a vocabulary w/ guid=%s" % vocabulary_key
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, msg)

    # from this point on the keys don't need to be present
    # (so I can just return on IndexError)

    # try to get the component_proxy...
    try:
        component_proxy_key = section_keys[3]
        component_proxy = MetadataComponentProxy.objects.get(guid=component_proxy_key, vocabulary=vocabulary)
    except IndexError:
        return (validity, version, model_proxy, vocabulary, component_proxy, msg)
    except MetadataComponentProxy.DoesNotExist:
        msg = "Invalid section key; unable to find a component w/ key=%s" % component_proxy_key
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, msg)

    return (validity, version, model_proxy, vocabulary, component_proxy, msg)


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
    if not project.active:
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
        model_customizer = MetadataModelCustomizer.objects.get(project=project, version=version, proxy=model_proxy, default=True)
    except MetadataModelCustomizer.DoesNotExist:
        msg = "There is no default customization associated with this project/model/version."
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, model_customizer, vocabularies, msg)
    vocabularies = model_customizer.get_active_sorted_vocabularies()

    return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, model_customizer, vocabularies, msg)


def validate_customize_view_arguments(project_name, section_key):

    (validity, project, version, model_proxy, vocabulary, component_proxy, msg) = \
        (True, None, None, None, None, None, "")

    # try to get the project...
    try:
        project = MetadataProject.objects.get(name=project_name.lower())
    except MetadataProject.DoesNotExist:
        msg = "Cannot find the <u>project</u> '%s'.  Has it been registered?" % project_name
        validity = False
        return (validity, project, version, model_proxy, vocabulary, component_proxy, msg)
    if not project.active:
        msg = "Project '%s' is inactive." % project_name
        validity = False
        return (validity, project, version, model_proxy, vocabulary, component_proxy, msg)

    # get all the other necessary elements by parsing the section_key
    (validity, version, model_proxy, vocabulary, component_proxy, msg) = \
        validate_customize_section_key(section_key)
    if not validity:
        return (validity, project, version, model_proxy, vocabulary, component_proxy, msg)

    return (validity, project, version, model_proxy, vocabulary, component_proxy, msg)


def get_edit_section_template_path(property_proxy, property_type, category_proxy):

    section_template_path = "questionnaire/api/"

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


def get_customize_section_template_path(vocabulary, component):

    section_template_path = "questionnaire/api/"

    if vocabulary:
        section_template = "_section_customize_vocabulary.html"
    if component:
        section_template = "_section_customize_vocabulary_component.html"

    return section_template_path + section_template


def api_get_new_edit_form_section(request, project_name, section_key, **kwargs):

    # check the arguments to the view,
    # and parse the section key
    (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, model_customizer, vocabularies, msg) = \
        validate_edit_view_arguments(project_name, section_key)
    if not validity:
        return questionnaire_error(request, msg)

    # get (or set) models from the cache...
    instance_key = get_key_from_request(request)
    customizer_set = get_cached_existing_customization_set(instance_key, model_customizer, vocabularies)
    # flatten the scientific properties...
    customizer_set["scientific_category_customizers"] = get_joined_keys_dict(customizer_set["scientific_category_customizers"])
    customizer_set["scientific_property_customizers"] = get_joined_keys_dict(customizer_set["scientific_property_customizers"])
    proxy_set = get_cached_proxy_set(instance_key, customizer_set)
    realization_set = get_cached_new_realization_set(instance_key, customizer_set, proxy_set, vocabularies)

    inheritance_data = get_cached_inheritance_data(instance_key)

    # now create the formsets...
    (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
        create_new_edit_forms_from_models(realization_set["models"], customizer_set["model_customizer"], realization_set["standard_properties"], customizer_set["standard_property_customizers"], realization_set["scientific_properties"], customizer_set["scientific_property_customizers"], inheritance_data=inheritance_data)

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
            "active_standard_categories_and_properties": customizer_set["model_customizer"].get_active_standard_categories_and_properties,
            "active_scientific_categories_and_properties": customizer_set["model_customizer"].get_active_scientific_categories_and_properties_by_key(model_key),
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
    instance_key = get_key_from_request(request)
    customizer_set = get_cached_existing_customization_set(instance_key, model_customizer, vocabularies)
    # flatten the scientific properties...
    customizer_set["scientific_category_customizers"] = get_joined_keys_dict(customizer_set["scientific_category_customizers"])
    customizer_set["scientific_property_customizers"] = get_joined_keys_dict(customizer_set["scientific_property_customizers"])
    proxy_set = get_cached_proxy_set(instance_key, customizer_set)
    realization_set = get_cached_existing_realization_set(instance_key, root_model.get_descendants(include_self=True), customizer_set, proxy_set, vocabularies)

    inheritance_data = get_cached_inheritance_data(instance_key)

    # now create the formsets...
    (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
        create_existing_edit_forms_from_models(realization_set["models"], customizer_set["model_customizer"], realization_set["standard_properties"], customizer_set["standard_property_customizers"], realization_set["scientific_properties"], customizer_set["scientific_property_customizers"], inheritance_data=inheritance_data)

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
            "active_standard_categories_and_properties": customizer_set["model_customizer"].get_active_standard_categories_and_properties,
            "active_scientific_categories_and_properties": customizer_set["model_customizer"].get_active_scientific_categories_and_properties_by_key(model_key),
        },
    }

    template = get_edit_section_template_path(property_proxy, property_type, category_proxy)
    return render_to_response(template, _dict, context_instance=RequestContext(request))


def api_get_new_customize_form_section(request, project_name, section_key, **kwargs):

    # check the arguments to the view,
    # and parse the section key
    (validity, project, version, model_proxy, vocabulary, component_proxy, msg) = \
        validate_customize_view_arguments(project_name, section_key)
    if not validity:
        return questionnaire_error(request, msg)

    # get the relevant vocabularies...
    vocabularies = project.vocabularies.filter(document_type__iexact=model_proxy.name)

    # get (or set) models from the cache...
    instance_key = get_key_from_request(request)
    customizer_set = get_cached_new_customization_set(instance_key, project, version, model_proxy, vocabularies)

    (model_customizer_form, standard_property_customizer_formset, scientific_property_customizer_formsets, model_customizer_vocabularies_formset) = \
        create_new_customizer_forms_from_models(customizer_set["model_customizer"], customizer_set["standard_category_customizers"], customizer_set["standard_property_customizers"], customizer_set["scientific_category_customizers"], customizer_set["scientific_property_customizers"], vocabularies_to_customize=vocabularies)

    # now get some things that were previously computed in the master template
    # or in loops that I need to recreate for the individual sections
    if component_proxy:
        formsets = scientific_property_customizer_formsets[vocabulary.get_key()]
        formset = formsets[component_proxy.get_key()]
    else:
        # the actual property formset is not needed for the top-level vocabulary section
        formset = None
    _dict = {
        # "vocabularies": vocabularies,
        "model_customizer_form": model_customizer_form,
        # "standard_property_customizer_formset": standard_property_customizer_formset,
        # "scientific_property_customizer_formsets": scientific_property_customizer_formsets,
        "section_parameters": {
            "version": version,
            "model_proxy": model_proxy,
            "vocabulary": vocabulary,
            "component": component_proxy,
            "formset": formset,
        },
    }

    template = get_customize_section_template_path(vocabulary, component_proxy)
    return render_to_response(template, _dict, context_instance=RequestContext(request))
