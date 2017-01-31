####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

from django.template import RequestContext
# from django.core.cache import caches
from uuid import uuid4

from Q.questionnaire.models.models_projects import QProject
from Q.questionnaire.models.models_ontologies import QOntology
from Q.questionnaire.models.models_proxies import QModelProxy
from Q.questionnaire.q_utils import QError


def add_parameters_to_context(request, context=None):
    """
    adds the GET parameters to a context for use in templates
    this is useful for maintaining state during GET/PUT cycles
    (for example, when storing the "next" parameter)
    :param request:
    :param context:
    :return:
    """
    if not context:
        context = RequestContext(request)

    context.update(request.GET.copy())

    return context


def validate_view_arguments(project_name=None, ontology_key=None, document_type=None):
    """
    Ensures that the arguments passed to a view are valid.
    :return: a tuple of project, ontology, proxy + a flag indicating whether or not the arguments were valid and a msg describing any validity errors
    """

    validity, project, ontology, proxy, msg = \
        True, None, None, None, ""

    # try to get the project...
    try:
        project = QProject.objects.get(name=project_name)
    except QProject.DoesNotExist:
        msg = "Cannot find the project '{0}'.  Has it been registered?".format(project_name)
        validity = False
        return validity, project, ontology, proxy, msg
    if not project.is_active:
        msg = "Project '{0}' is inactive.".format(project_name)
        validity = False
        return validity, project, ontology, proxy, msg

    # try to get the ontology...
    try:
        # this bit allows underspecification of the ontology version...
        ontology = QOntology.objects.has_key(ontology_key).get(is_registered=True)
    except QOntology.DoesNotExist:
        msg = "Cannot find the ontology '{0}'.  Has it been registered?".format(ontology_key)
        validity = False
        return validity, project, ontology, proxy, msg
    if ontology not in project.ontologies.all():
        msg = "The ontology '{0}' is not associated with the project '{1}'.".format(ontology, project)
        validity = False
        return validity, project, ontology, proxy, msg

    # try to get the proxy...
    try:
        proxy = QModelProxy.objects.get(ontology=ontology, name__iexact=document_type)
    except QModelProxy.DoesNotExist:
        msg = "Cannot find the document type '{0}' in the ontology '{1}'.".format(document_type, ontology)
        validity = False
        return validity, project, ontology, proxy, msg
    if not proxy.is_document:
        msg = "'{0}' is not a recognized document type in the ontology.".format(document_type)
        validity = False
        return validity, project, ontology, proxy, msg

    # whew, we made it...
    return validity, project, ontology, proxy, msg


def get_key_from_request(request):
    """
    generates a unique key to use throughout a GET/POST/AJAX workflow
    :param request:
    :return:
    """

    if not request.is_ajax():
        if request.method == "GET":
            # a normal GET resets the key
            key = str(uuid4())
        else:
            # a normal POST should have the key in the datadict
            key = request.POST["session_key"]
    else:
        if request.method == "GET":
            # an AJAX GET should have passed the key as a parameter
            key = request.GET["session_key"]
        else:
            # an AJAX POST should have the key in the datadict
            key = request.POST["session_key"]

    return key


# by the way, the reason I am using explicit caching
# instead of the built-in Django session store
# is that the items I need to store are unique by view
# afaik, sessions are unique per site/visitor
# so if a user is customizing something and then tries editing that something
# I want 2x the entries in the cache to treat them differently
# instead of potentially overwriting the cache on the new page load

# NEVERMIND - I can use built-in Django session store
# as long as the keys represent separate views

# TODO: FIGURE OUT THE MOST EFFICIENT WAY OF CACHING

def get_or_create_cached_object(session, obj_key, fn, *args, **kwargs):
    """
    looks for a specific key in the cache;
    if it can't be found, generates a new object and stores it in the cache
    (for the next time)
    :param key: key for object in cache
    :param fn: fn to call to generate object if it is not found in the cache
    :param args: args for fn
    :param kwargs: kwargs for fn
    :return:
    """

    # cache = caches["default"]
    # obj = cache.get(obj_key)
    obj = session.get(obj_key)
    if not obj:
        obj = fn(*args, **kwargs)
        # cache.set(obj_key, obj)
        session[obj_key] = obj
    return obj


def get_cached_object(session, obj_key):
    """
    looks for a specific key in the cache;
    (for the next time)
    :param session: session where object is stored
    :param key: key for object in cache
    :return:
    """
    # cache = caches["default"]
    # obj = cache.getg(obj_key)
    obj = session.get(obj_key)
    if not obj:
        msg = "Unable to locate object in cache."
        raise QError(msg)
    return obj
