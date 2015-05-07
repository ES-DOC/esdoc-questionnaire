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
.. module:: views_base

Functions common to all views.
"""

from uuid import uuid4
from django.core.cache import get_cache
from CIM_Questionnaire.questionnaire.models import MetadataProject, MetadataVersion, MetadataCustomizer, MetadataModelCustomizer, MetadataModelProxy, MetadataModel


def validate_view_arguments(project_name="", model_name="", version_key=""):
    """
    Ensures that the arguments passed to a view are valid.
    (ie: resolve them to active projects, model proxies, & versions)
    :param project_name: the name of the project being requested
    :param model_name: the name of the model proxy being requested
    :param version_key: the key (name + version) of the version being requested
    :return: a tuple of project, model, version + a flag indicating whether or not the arguments were valid and a msg describing any validity errors
    """

    (validity, project, version, model_proxy, msg) = \
        (True, None, None, None, "")

    # try to get the project...
    project_name_lower = project_name.lower()
    try:
        project = MetadataProject.objects.get(name=project_name_lower)
    except MetadataProject.DoesNotExist:
        msg = "Cannot find the <u>project</u> '%s'.  Has it been registered?" % project_name
        validity = False
        return (validity, project, version, model_proxy, msg)
    if not project.active:
        msg = "Project '%s' is inactive." % project_name
        validity = False
        return (validity, project, version, model_proxy, msg)

    # try to get the version...
    try:
        version = MetadataVersion.objects.get(key=version_key, registered=True)
    except MetadataVersion.DoesNotExist:
        msg = "Cannot find the <u>version</u> '%s'.  Has it been registered?" % version_key
        validity = False
        return (validity, project, version, model_proxy, msg)
    if version.categorization is None:
        msg = "The <u>version</u> '%s' has no categorization associated with it." % (version)
        validity = False
        return (validity, project, version, model_proxy, msg)

    # try to get the model (proxy)...
    try:
        model_proxy = MetadataModelProxy.objects.get(version=version, name__iexact=model_name)
    except MetadataModelProxy.DoesNotExist:
        msg = "Cannot find the <u>model</u> '%s' in the <u>version</u> '%s'." % (model_name, version)
        validity = False
        return (validity, project, version, model_proxy, msg)
    if not model_proxy.is_document():
        msg = "<u>%s</u> is not a recognized document type in the CIM." % model_name
        validity = False
        return (validity, project, version, model_proxy, msg)

    return validity, project, version, model_proxy, msg


def validate_view_authentication(project, user):
    # TODO!!
    pass


def get_cached_new_customization_set(instance_key, project, ontolgoy, proxy, vocabularies):

    cache = get_cache("default")
    cached_customizer_set_key = u"%s_customizer_set" % instance_key

    customizer_set = cache.get(cached_customizer_set_key)

    if not customizer_set:

        (model_customizer, standard_category_customizers, standard_property_customizers, scientific_category_customizers, scientific_property_customizers) = \
            MetadataCustomizer.get_new_customizer_set(project, ontolgoy, proxy, vocabularies)

        customizer_set = {
            "model_customizer": model_customizer,
            "standard_category_customizers": standard_category_customizers,
            "standard_property_customizers": standard_property_customizers,
            "scientific_category_customizers": scientific_category_customizers,
            "scientific_property_customizers": scientific_property_customizers,
        }

        cache.set(cached_customizer_set_key, customizer_set)

    return customizer_set


def get_cached_existing_customization_set(session_id, model_customizer, vocabularies):
    """

    :param session_id:
    :param model_customizer:
    :param vocabularies:
    :return:
    """

    cache = get_cache("default")
    cached_customizer_set_key = u"%s_customizer_set" % session_id

    customizer_set = cache.get(cached_customizer_set_key)

    if not customizer_set:

        (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
            MetadataCustomizer.get_existing_customizer_set(model_customizer, vocabularies)

        customizer_set = {
            "model_customizer": model_customizer,
            "standard_category_customizers": standard_category_customizers,
            "standard_property_customizers": standard_property_customizers,
            # this has been moved into the edit & view since this fn is used by the customizer views as well
            # "scientific_category_customizers": get_joined_keys_dict(nested_scientific_category_customizers),
            # "scientific_property_customizers": get_joined_keys_dict(nested_scientific_property_customizers),
            "scientific_category_customizers": nested_scientific_category_customizers,
            "scientific_property_customizers": nested_scientific_property_customizers,
        }

        cache.set(cached_customizer_set_key, customizer_set)

    return customizer_set


def get_cached_proxy_set(session_id, customizer_set):
    """

    :param session_id:
    :param customizer_set:
    :return:
    """

    cache = get_cache("default")
    cached_proxy_set_key = u"%s_proxy_set" % session_id

    proxy_set = cache.get(cached_proxy_set_key)

    if not proxy_set:

        model_proxy = customizer_set["model_customizer"].proxy
        standard_property_proxies = [standard_property_customizer.proxy for standard_property_customizer in customizer_set["standard_property_customizers"]]
        scientific_property_proxies = {key: [spc.proxy for spc in value] for key, value in customizer_set["scientific_property_customizers"].items()}

        proxy_set = {
            "model_proxy": model_proxy,
            "standard_property_proxies": standard_property_proxies,
            "scientific_property_proxies": scientific_property_proxies,
        }

        cache.set(cached_proxy_set_key, proxy_set)

    return proxy_set


def get_cached_new_realization_set(session_id, customizer_set, proxy_set, vocabularies):
    """

    :param session_id:
    :param customizer_set:
    :param proxy_set:
    :param vocabularies:
    :return:
    """

    cache = get_cache("default")
    cached_realization_set_key = u"%s_realization_set" % session_id

    realization_set = cache.get(cached_realization_set_key)

    if not realization_set:

        project = customizer_set["model_customizer"].project
        version = proxy_set["model_proxy"].version

        # TODO: DON'T LIKE HAVING TO PASS MODEL_CUSTOMIZER, SINCE I WANT ALL CUSTOMIZATION FUNCTIONALITY TO BE FORM-SPECIFIC
        # TODO: BUT I HAVE TO SET THE ROOT VOCAB & COMPONENT KEY IN THIS FN
        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_new_realization_set(project, version, proxy_set["model_proxy"], proxy_set["standard_property_proxies"], proxy_set["scientific_property_proxies"], customizer_set["model_customizer"], vocabularies)

        realization_set = {
            "models": models,
            "standard_properties": standard_properties,
            "scientific_properties": scientific_properties,
        }

        cache.set(cached_realization_set_key, realization_set)

    return realization_set


def get_cached_existing_realization_set(session_id, realizations, customizer_set, proxy_set, vocabularies):
    """

    :param session_id:
    :param customizer_set:
    :param proxy_set:
    :param vocabularies:
    :return:
    """

    cache = get_cache("default")
    cached_realization_set_key = u"%s_realization_set" % session_id

    realization_set = cache.get(cached_realization_set_key)

    if not realization_set:

        # TODO: DON'T LIKE HAVING TO PASS MODEL_CUSTOMIZER, SINCE I WANT ALL CUSTOMIZATION FUNCTIONALITY TO BE FORM-SPECIFIC
        # TODO: BUT I HAVE TO SET THE ROOT VOCAB & COMPONENT KEY IN THIS FN
        (models, standard_properties, scientific_properties) = \
            MetadataModel.get_existing_realization_set(realizations, customizer_set["model_customizer"], vocabularies=vocabularies)

        realization_set = {
            "models": models,
            "standard_properties": standard_properties,
            "scientific_properties": scientific_properties,
        }

        cache.set(cached_realization_set_key, realization_set)

    return realization_set


def get_key_from_request(request):
    """
    generates a unique key to use throughout a GET/AJAX/PUT workflow instance
    :param request:
    :return:
    """

    if not request.is_ajax():
        if request.method == "GET":
            # a normal GET resets the key
            key = str(uuid4())
        else:
            # a normal POST should have the key in the datadict
            key = request.POST["instance_key"]
    else:
        if request.method == "GET":
            # an AJAX GET should have passed the key as a parameter
            key = request.GET["instance_key"]
        else:
            # an AJAX POST should have the key in the datadict
            key = request.POST["instance_key"]

    return key
