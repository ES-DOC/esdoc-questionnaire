
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
.. module:: views_api

Summary of module goes here

"""

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import render_to_response

from django.template.context import RequestContext

from CIM_Questionnaire.questionnaire.forms.forms_edit import create_new_edit_forms_from_models
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer, MetadataModelCustomizer, MetadataStandardPropertyCustomizer, MetadataScientificPropertyCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
from CIM_Questionnaire.questionnaire.models.metadata_project import MetadataProject
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataModelProxy, MetadataComponentProxy, MetadataStandardCategoryProxy, MetadataScientificCategoryProxy, MetadataStandardPropertyProxy, MetadataScientificPropertyProxy
from CIM_Questionnaire.questionnaire.models.metadata_version import MetadataVersion
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary
from CIM_Questionnaire.questionnaire.views.views_error import questionnaire_error
from CIM_Questionnaire.questionnaire.utils import get_joined_keys_dict, get_form_by_prefix
from CIM_Questionnaire.questionnaire.utils import DEFAULT_VOCABULARY_KEY, DEFAULT_COMPONENT_KEY

STANDARD_PROPERTY_TYPE = "standard_properties"
SCIENTIFIC_PROPERTY_TYPE = "scientific_properties"
VALID_PROPERTY_TYPES = [ STANDARD_PROPERTY_TYPE, SCIENTIFIC_PROPERTY_TYPE ]

def validate_section_key(section_key):

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

    (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg ) = \
        (True, None, None, None, None, None, None, None, "")

    section_keys = section_key.split('|')

    # try to get the version...
    try:
        version_key = section_keys[0]
        version = MetadataVersion.objects.get(key=version_key, registered=True)
    except IndexError:
        msg = "Invalid section key; did not specify version"
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg )
    except MetadataVersion.DoesNotExist:
        msg = "Invalid section key; unable to find a registered version w/ key=%s" % version_key
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg )

    # try to get the model proxy...
    try:
        model_proxy_key = section_keys[1]
        model_proxy = MetadataModelProxy.objects.get(version=version, name__iexact=model_proxy_key)
    except IndexError:
        msg = "Invalid section key; did not specify model"
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg )
    except MetadataModelProxy.DoesNotExist:
        msg = "Invalid section key; unable to find a model w/ name=%s" % model_proxy_key
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg )

    # try to get the vocabulary...
    try:
        vocabulary_key = section_keys[2]
        vocabulary = MetadataVocabulary.objects.get(guid=vocabulary_key)
    except IndexError:
        msg = "Invalid section key; did not specify vocabulary"
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg )
    except MetadataVocabulary.DoesNotExist:
        if vocabulary_key == DEFAULT_VOCABULARY_KEY:
            vocabulary = None
        else:
            msg = "Invalid section key; unable to find a vocabulary w/ guid=%s" % vocabulary_key
            validity = False
            return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg )

    # try to get the component_proxy...
    try:
        component_proxy_key = section_keys[3]
        component_proxy = MetadataComponentProxy.objects.get(guid=component_proxy_key, vocabulary=vocabulary)
    except IndexError:
        msg = "Invalid section key; did not specify component"
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg )
    except MetadataComponentProxy.DoesNotExist:
        if component_proxy_key == DEFAULT_COMPONENT_KEY and vocabulary_key == DEFAULT_VOCABULARY_KEY:
            component = None
        else:
            msg = "Invalid section key; unable to find a component w/ key=%s" % component_proxy_key
            validity = False
            return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg )

    # from this point on the keys don't need to be present (so I can just return on IndexError)

    # try to get the property type...
    try:
        property_type = section_keys[4]
        if property_type not in VALID_PROPERTY_TYPES:
            msg = "Invalid section key; must specify a property type from %s" % ", ".join(VALID_PROPERTY_TYPES)
            validity = False
            return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg )
    except IndexError:
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg )

    # try to get the category_proxy...
    try:
        category_proxy_key = section_keys[5]
        if property_type == STANDARD_PROPERTY_TYPE:
            category_proxy = MetadataStandardCategoryProxy.objects.get(key=category_proxy_key, categorization=version.categorization)
        else: # property_type == SCIENTIFIC_PROPERTY_TYPES
            # scientific properties can only come from CVs, so I am sure that there will be a component
            category_proxy = MetadataScientificCategoryProxy.objects.get(key=category_proxy_key, component=component_proxy)
    except IndexError:
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg )
    except MetadataStandardCategoryProxy.DoesNotExist:
            msg = "Invalid section key; cannot find a standard property category w/ key=%s from version %s" % (category_proxy_key, version)
            validity = False
            return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg )
    except MetadataScientificCategoryProxy.DoesNotExist:
            msg = "Invalid section key; cannot find a scientific property category w/ key=%s from component %s" % (category_proxy_key, component_proxy)
            validity = False
            return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg )

    # try to get the property_proxy...
    try:
        property_proxy_key = section_keys[6]
        if property_type == STANDARD_PROPERTY_TYPE:
            property_proxy = MetadataStandardPropertyProxy.objects.get(name__iexact=property_proxy_key, model_proxy=model_proxy, category=category_proxy)
        else: # property_type == SCIENTIFIC_PROPERTY_TYPE
            property_proxy = MetadataScientificPropertyProxy.objects.get(name__iexact=property_proxy_key, component=component_proxy, category=category_proxy)
    except IndexError:
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg )
    except MetadataStandardPropertyProxy.DoesNotExist:
        msg = "Invalid section key; cannot find a standard property w/ name=%s from model %s with category %s" % (property_proxy_key, model_proxy, category_proxy)
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg )
    except MetadataScientificPropertyProxy.DoesNotExist:
        msg = "Invalid section key; cannot find a scientific property w/ name=%s from component %s with category %s" % (property_proxy_key, model_proxy, category_proxy)
        validity = False
        return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg )

    # TODO: DEAL W/ SUBFORMS IN SECTION_KEY

    return (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg )

# TODO: GET THIS TO WORK W/ CACHED PICKLED INSTANCE OF FORMS RATHER THAN RE-CREATING THEM EACH TIME

def api_get_form_section(request, project_name, section_key, **kwargs):

    # try to get the project...
    try:
        project = MetadataProject.objects.get(name=project_name.lower())
    except MetadataProject.DoesNotExist:
        msg = "Cannot find the <u>project</u> '%s'.  Has it been registered?" % (project_name)
        return questionnaire_error(request, msg)
    if not project.active:
        msg = "Project '%s' is inactive." % (project_name)
        return questionnaire_error(request,msg)

    # get all the other necessary elements by parsing the section_key
    (validity, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy, msg ) = \
        validate_section_key(section_key)
    if not validity:
        return questionnaire_error(request,msg)

    # get the customizers...
    try:
        model_customizer = MetadataModelCustomizer.objects.get(project=project, version=version, proxy=model_proxy, default=True)
    except MetadataModelCustomizer.DoesNotExist:
        msg = "There is no default customization associated with this project/model/version."
        return questionnaire_error(request, msg)
    # okay, I know that I may have only specified 1 or 0 vocabularies
    # but for now I still need to recreate the forms in their entirety (meaning all vocabularies)
    # later, when I cache things, I can do away with this extra complexity
    vocabularies = model_customizer.vocabularies.all()
    # if vocabulary:
    #     vocabularies = [vocabulary]
    # else:
    #     vocabularies = []

    (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(model_customizer, vocabularies)
    standard_property_proxies = [standard_property_customizer.proxy for standard_property_customizer in standard_property_customizers]
    scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)
    scientific_property_proxies = { key : [spc.proxy for spc in value] for key,value in  scientific_property_customizers.items() }

    # TODO: USE EITHER CACHED MODELS OR CACHED FORMS
    # TODO: CACHED FORMS DO NOT PICKLE OUT-OF-THE-BOX
    # TODO: CAN CACHE MODELS BUT DON'T KNOW ENOUGH ABOUT SESSIONS TO GET THE CORRECT MODELS BACK FROM THE CACHE ON A SUBSEQUENT VIEW

    # TODO: HANDLE THE CASE FOR EXISTING MODELS...
    (models, standard_properties, scientific_properties) = \
        MetadataModel.get_new_realization_set(project, version, model_proxy, standard_property_proxies, scientific_property_proxies, model_customizer, vocabularies)

    (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
        create_new_edit_forms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers)

    msg = "<i>you asked for:</i>" \
          "<table border='1'>" \
            "<tr><td>project</td><td>%s</td></tr>" \
            "<tr><td>version</td><td>%s</td></tr>" \
            "<tr><td>model</td><td>%s</td></tr>" \
            "<tr><td>vocabulary</td><td>%s</td></tr>" \
            "<tr><td>component</td><td>%s</td></tr>" \
            "<tr><td>property_type</td><td>%s</td></tr>" \
            "<tr><td>category</td><td>%s</td></tr>" \
            "<tr><td>property</td><td>%s</td></tr>" \
          "</table>" % (project, version, model_proxy, vocabulary, component_proxy, property_type, category_proxy, property_proxy)


    # TODO: JUST PASS THESE THINGS IN AS NEEDED FOR THE DIFFERENT SECTIONS ACCORDING TO THE BIG IF/ELSE BLOCK BELOW
    # now get some things that were previously computed in the master template
    # or in loops that I need to recreate for the individual sections
    section_keys = section_key.split('|')
    model_key = u"%s_%s" % (section_keys[2], section_keys[3])
    model_form = get_form_by_prefix(model_formset, model_key)
    standard_property_formset = standard_properties_formsets[model_key]
    scientific_property_formset = scientific_properties_formsets[model_key]
    active_standard_categories_and_properties = model_customizer.get_active_standard_categories_and_properties
    active_scientific_categories_and_properties = model_customizer.get_active_scientific_categories_and_properties_by_key(model_key)

    dict = {
        "vocabularies": vocabularies,
        "model_customizer" : model_customizer,
        "model_formset": model_formset,
        "standard_properties_formsets": standard_properties_formsets,
        "scientific_properties_formsets": scientific_properties_formsets,
        "section_parameters" : {
            "model_form" : model_form,
            "standard_property_formset" : standard_property_formset,
            "scientific_property_formset" : scientific_property_formset,
            "active_standard_categories_and_properties" : active_standard_categories_and_properties,
            "active_scientific_categories_and_properties" : active_scientific_categories_and_properties,
        },
     }


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

    if property_proxy:
        if property_type == STANDARD_PROPERTY_TYPE:
            section_template = "_section_standard_property.html"
        else: # property_type == SCIENTIFIC_PROPERTY_TYPE:
            section_template = "_section_scientific_property.html"
    elif category_proxy:
        if property_type == STANDARD_PROPERTY_TYPE:
            section_template = "_section_standard_category.html"
        else: # property_type == SCIENTIFIC_PROPERTY_TYPE:
            section_template = "_section_scientific_category.html"
    elif property_type:
        if property_type == STANDARD_PROPERTY_TYPE:
            section_template = "_section_all_standard_categories.html"
        else: # property_type == SCIENTIFIC_PROPERTY_TYPE:
            section_template = "_section_all_scientific_categories.html"
    # elif component_proxy and vocabulary:
    else: # the only other section is the entire component; do I need to distinguish between a CV component and the default component?
        section_template = "_section_component.html"


    # TODO: add information in the dict to work out which property, etc. to get

    template = "questionnaire/api/" + section_template
    #rendered_section = render_to_string(template, dictionary=dict, context_instance=RequestContext(request))

    return render_to_response(template, dict, context_instance=RequestContext(request))

    return HttpResponse(rendered_form)

# NOTE TO SELF:
# FOR TESTING model_key of Atmosphere->AtmosKeyProperties is "9edc2293-76bb-42b6-a392-babadb1d6def_744281fb-226d-43e8-a0d9-54c01878dd0f"