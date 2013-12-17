
####################
#   Django-CIM-Forms
#   Copyright (c) 2012 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Jun 11, 2013 11:39:24 AM"

"""
.. module:: views_view

Summary of module goes here

"""

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, FieldError, MultipleObjectsReturned
from django.core.urlresolvers import reverse
from django.http import *
from django.shortcuts import *

from dcf.utils  import *
from dcf.models import *
from dcf.forms  import *
from dcf.views.views_error import error as dcf_error


def check_parameters(version_number="",project_name="",model_name="",msg=""):

    project         = None
    version         = None
    customizer      = None
    categorization  = None
    vocabularies    = None
    model_class     = None

    # try to get the requested project...
    try:
        project = MetadataProject.objects.get(name__iexact=project_name)
    except ObjectDoesNotExist:
        msg = "Cannot find the project '%s'.  Has it been registered?" % project_name
        return (project,version,customizer,categorization,vocabularies,model_class,msg)

    # try to get the requested version...
    if version_number:
        try:
            version = MetadataVersion.objects.get(name__iexact=METADATA_NAME,number=version_number)
        except ObjectDoesNotExist:
            msg = "Cannot find version '%s_%s'.  Has it been registered?" % (METADATA_NAME,version_number)
            return (project,version,customizer,categorization,vocabularies,model_class,msg)
    else:
        version = project.getDefaultVersion()
        if not version:
            msg = "please specify a version; the '%s' project has no default one." % project.getName()
            return (project,version,customizer,categorization,vocabularies,model_class,msg)

    # try to get the requested model...
    model_class = version.getModelClass(model_name)
    if not model_class:
        msg = "Cannot find the model type '%s' in version '%s'.  Have all model types been registered?" % (model_name, version)
        return (project,version,customizer,categorization,vocabularies,model_class,msg)

    # try to get the default customizer for this project/version/model...
    try:
        customizer = MetadataModelCustomizer.objects.get(project=project,version=version,model=model_name,default=1)
    except MetadataModelCustomizer.DoesNotExist:
        msg = "There is no default customization associated with '%s' for project '%s' at version '%s'" % (model_name,project,version)
        return (project,version,customizer,categorization,vocabularies,model_class,msg)

    # get the default categorization and vocabularies...
    categorizations = version.categorizations.all()
    vocabularies = customizer.vocabularies.all()
    # TODO: THIS IS CLEARLY DUMB,
    # BUT THE RELATEDOBJECTMANAGER IS BEING USED FOR THE TIME WHEN
    # THIS CODE CAN SUPPORT MULTPLE CATEGORIZATIONS
    categorization  = categorizations[0] if categorizations else None
    if not categorization:
        msg = "There is no default categorization associated with version %s." % version
        return (project,version,customizer,categorization,vocabularies,model_class,msg)
    if not vocabularies:
        msg = "There are no default vocabularies associated with customizer %s." % customizer
        return (project,version,customizer,categorization,vocabularies,model_class,msg)

    return (project,version,customizer,categorization,vocabularies,model_class,msg)


def view_existing(request,version_number="",project_name="",model_name="",model_id=""):

    msg = ""

    (project,version,customizer,categorization,vocabularies,model_class,msg) = \
    check_parameters(version_number,project_name,model_name)
    if not all ([project,version,customizer,categorization,vocabularies,model_class]):
        return dcf_error(request,msg)


    # try to get the requested model...    
    try:
        model_instance = model_class.objects.get(pk=model_id)
    except ObjectDoesNotExist:
        msg = "Cannot find the specified model.  Please try again."
        return dcf_error(request,msg)
    if not model_instance.isDocument():
        msg = "The model type '%s' is not an editable metadata document" % (model_class.getTitle())
        return dcf_error(request,msg)

    model_instances                 = {}
    model_forms                     = {}
    scientific_property_formsets    = {}

    model_instances[model_instance.component_name] = model_instance
    for model in model_instance.getAllChildren():
        model_instances[model.component_name] = model
    
    form_class = MetadataFormFactory(model_class,customizer)


    component_list = []
    component_tree = {}
    if customizer.model_root_component:
        component_list.append(customizer.model_root_component)
        component_tree[customizer.model_root_component] = []
    for vocabulary in vocabularies:
        try:
            component_list += vocabulary.getComponentList()
            if customizer.model_root_component:
                component_tree[customizer.model_root_component].append(vocabulary.getComponentTree())
            else:
                component_tree.update(vocabulary.getComponentTree())
            if not any(component_list): # don't need to check component_tree; if it has one it will have the other
                msg = "There is no component hierarchy defined in vocabulary '%s'.  Has it been registered?" % vocabulary
                return dcf_error(request,msg)
        except:
            msg = "There is no component hierarchy defined in vocabulary '%s'.  Has it been registered?" % vocabulary
            return dcf_error(request,msg)

    root_component = component_list[0].lower()

    standard_categories     = customizer.getStandardCategories()
    scientific_categories   = project.categories.all().order_by("order")
    for vocabulary in vocabularies:
        scientific_categories = scientific_categories | vocabulary.categories.all().order_by("order")


    if request.method == "POST":
        # POST just means they clicked "edit"
        edit_existing_url = reverse("edit_existing",kwargs={
               "version_number" : version.number,
               "project_name"   : project,
               "model_name"     : model_name,
               "model_id"       : model_instances[root_component].pk,
        })
        return HttpResponseRedirect(edit_existing_url)
        
    else: # request.method == "GET"

        for component in component_list:
            component_key = component.lower()
            model_forms[component_key] = form_class(
                instance=model_instances[component_key],
                component_name=component_key,
                prefix=component_key,
                request=request
            )
            scientific_properties = model_instances[component_key].getScientificProperties()
            if scientific_properties:
                scientific_property_formsets[component_key] = \
                    MetadataScientificPropertyFormSetFactory(
                        queryset    = scientific_properties,
                        prefix      = component_key + "_scientific_property",
                        request     = request,
                    )


    # gather all the extra information required by the template
    dict = {
        "msg"                           : msg,
        "forms"                         : model_forms,
        "scientific_property_formsets"  : scientific_property_formsets,
        "standard_categories"           : standard_categories,
        "scientific_categories"         : scientific_categories,
        "customizer"                    : customizer,
        "project"                       : project,
        "version"                       : version,
        "vocabularies"                  : vocabularies,
        "model_class"                   : model_class,
        "component_list"                : component_list,
        "component_tree"                : dict_to_html(component_tree),
    }
    
    return render_to_response('dcf/dcf_view.html', dict, context_instance=RequestContext(request))


