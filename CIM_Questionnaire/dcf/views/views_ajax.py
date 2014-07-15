
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
__date__ ="Jun 17, 2013 2:42:52 PM"

"""
.. module:: views_ajax

Summary of module goes here

"""

from django.template import *
from django.shortcuts import *
from django.http import *
from django.contrib.sites.models    import get_current_site

from django.core.exceptions import ObjectDoesNotExist, FieldError, MultipleObjectsReturned
from django.utils import simplejson as json

import re

from dcf.models import *
from dcf.forms import *
from dcf.utils import *

def add_submodel(request):

    version_number  = request.GET.get('v',None)
    project_name    = request.GET.get('p',None)
    customizer_name = request.GET.get('c',None)
    model_name      = request.GET.get('m',None)
    field_name      = request.GET.get('f',None)
    model_id        = request.GET.get('i',None)
    
    if not (version_number and project_name and customizer_name and model_name and field_name):
        msg = "Insufficient parameters sent to add_submodel"
        return HttpResponse(msg)

    try:
        version = MetadataVersion.objects.get(number=version_number)
    except:
        msg = "Invalid version specified"
        return HttpResponse(msg)

    try:
        model_class = version.getModelClass(model_name)
    except:
        msg = "Invalid model specified"
        return HttpResponse(msg)
    if not model_class:
        msg = "Invalid model specified"
        return HttpResponse(msg)

    metadata_field = model_class.getField(field_name)
    
    # TODO: THE FIX FOR BULK_CREATE FOR SQLITE IS CAUSING CALLS TO CONTENTTYPE TO FAIL
    # SO I AM REWRITING THIS TO USE THE SAVED MODELS FROM THE VERSION
    #target_model_class = metadata_field.getTargetModelClass()
    target_model_class = version.getModelClass(metadata_field.targetModelName.lower())
    qs = target_model_class.objects.all()

    if model_id:
        existing_model = model_class.objects.get(pk=model_id)
        existing_field = getattr(existing_model,field_name)
        qs = qs.exclude(pk__in=existing_field.all())


    class _AddForm(forms.Form):
        models = ModelChoiceField(
            required=True,
            empty_label=None,
            label=target_model_class.getTitle(),
            queryset=qs
        )

        def __init__(self,*args,**kwargs):
            qs = kwargs.pop("queryset",None)
            super(_AddForm,self).__init__(*args,**kwargs)
            self.fields["models"].queryset = qs

    add_form = _AddForm(queryset=qs)

    dict = {
        "STATIC_URL"    : "/static/",
        "form"          : add_form,
    }

    rendered_form = django.template.loader.render_to_string("dcf/dcf_add_submodel.html", dictionary=dict, context_instance=RequestContext(request))
    return HttpResponse(rendered_form,mimetype='text/html')

def get_submodel(request):

    version_number  = request.GET.get('v',None)
    project_name    = request.GET.get('p',None)
    customizer_name = request.GET.get('c',None)
    model_name      = request.GET.get('m',None)
    field_name      = request.GET.get('f',None)
    id_to_get       = request.GET.get('i',None)

    if not (version_number and project_name and customizer_name and model_name and field_name):
        msg = "Insufficient parameters sent to get_submodel"
        return HttpResponse(msg)

    try:
        version = MetadataVersion.objects.get(number=version_number)
    except:
        msg = "Invalid version specified"
        return HttpResponse(msg)

    try:
        model_class = version.getModelClass(model_name)
    except:
        msg = "Invalid model specified"
        return HttpResponse(msg)
    if not model_class:
        msg = "Invalid model specified"
        return HttpResponse(msg)

    metadata_field = model_class.getField(field_name)
    # TODO: THE FIX FOR BULK_CREATE FOR SQLITE IS CAUSING CALLS TO CONTENTTYPE TO FAIL
    # SO I AM REWRITING THIS TO USE THE SAVED MODELS FROM THE VERSION
    #target_model_class = metadata_field.getTargetModelClass()
    target_model_class = version.getModelClass(metadata_field.targetModelName.lower())

    target_model = target_model_class.objects.get(id=id_to_get)

    # can't do this:
    #json_data = JSON_SERIALIZER.serialize([target_model])
    # b/c it will not serialize the fields of any parent models [as per https://docs.djangoproject.com/en/dev/topics/serialization/?from=olddocs#inherited-models]
    # instead I have to manually do this:
    serializer = MetadataSerializer()
    json_data = serializer.serialize([target_model])


    json_data_string = json.dumps(json_data)
    #return HttpResponse(json_data);
    #return HttpResponse([json_data],content_type="application/json; charset=utf-8");
    #return HttpResponse(u'"%s"'%json_data);
    return HttpResponse(json_data_string)

def customize_category(request):

    category_key            = request.GET.get('k',None)
    category_name           = request.GET.get('n',None)
    category_component_name = request.GET.get('c',None)
    category_description    = request.GET.get('d',None)
    category_order          = request.GET.get('o',None)

    if not (category_key and category_name and category_component_name):
        msg = "Insufficient parameters sent to edit_scientific_category"
        return HttpResponse(msg)

    category = MetadataScientificCategory(
        # I don't actually care about getting/saving this in the db
        # I'll do that when I save the customize form
        key            = category_key,
        name           = category_name,
        component_name = category_component_name,
        description    = category_description,
        order          = category_order,
    )

    category_form = MetadataScientificCategoryForm(instance=category)

    dict = {
        "STATIC_URL"    : "/static/",
        "form"          : category_form,
        "component"     : category.component_name,
    }

    rendered_form = django.template.loader.render_to_string("dcf/dcf_category.html", dictionary=dict, context_instance=RequestContext(request))
    return HttpResponse(rendered_form,mimetype='text/html')



def customize_subform(request):

    field_name      = request.GET.get('f',None)
    version_number  = request.GET.get('v',None)
    project_name    = request.GET.get('p',None)
    model_name      = request.GET.get('m',None)
    customizer_name = request.GET.get('c',None)

    msg = ""

    if not (field_name and version_number and project_name and model_name and customizer_name):
        msg = "Insufficient parameters sent to customize_subform"
        print msg
        return HttpResponse(msg)
    
    # try to get the requested project...
    try:
        project = MetadataProject.objects.get(name__iexact=project_name)
    except ObjectDoesNotExist:
        msg = "Cannot find the project '%s'.  Has it been registered?" % project_name
        print msg
        return HttpResponse(msg)

    # try to get the requested version...
    if version_number:
        try:
            version = MetadataVersion.objects.get(name__iexact=METADATA_NAME,number=version_number)
        except ObjectDoesNotExist:
            msg = "Cannot find version '%s'.  Has it been registered?" % (version_number)
            print msg
            return HttpResponse(msg)
    else:
        version = project.getDefaultVersion()
        if not version:
            msg = "please specify a %s version; the %s project has no default one." % (METADATA_NAME,project)
            print msg
            return HttpResponse(msg)

    # try to get the requested model (class)...
    model_class = version.getModelClass(model_name)
    if not model_class:
        msg = "Cannot find the model type '%s' in version '%s'.  Have all model types been loaded?" % (model_name, version)
        print msg
        return HttpResponse(msg)

    # get the default categorization and vocabulary...
    categorizations = version.categorizations.all()
    vocabularies = project.vocabularies.all()
    # TODO: THIS IS CLEARLY DUMB,
    # BUT THE RELATEDOBJECTMANAGER IS BEING USED FOR THE TIME WHEN
    # THIS CODE CAN SUPPORT MULTPLE CATEGORIZATIONS
    categorization  = categorizations[0] if categorizations else None
    vocabulary  = vocabularies[0] if vocabularies else None
    if not categorization:
        msg = "There is no default categorization associated with version %s." % version
        print msg
        return dcf_error(request,msg)
    if not vocabulary:
        msg = "There is no default vocabulary associated with project %s." % project
        print msg
        return dcf_error(request,msg)

    # try to get the existing customizers...
    try:
        model_customizer = MetadataModelCustomizer.objects.get(project=project,version=version,model__iexact=model_name,name=customizer_name)
    except MetadataModelCustomizer.DoesNotExist:
        msg = "There is no default customization associated with '%s'" % (model_name)
        print msg
        return HttpResponse(msg)
    property_customizer = model_customizer.getStandardPropertyCustomizers().get(name=field_name)

    # and get the model this property points to (the one we want to customize)...
    (target_model_app,target_model_name) = property_customizer.relationship_target_model.split(".")
    target_model_name = target_model_name.lower()
#    target_model_class = version.getModelClass(target_model_name)

    #target_model_type   = ContentType.objects.get(app_label=target_model_app,model=target_model_name)
    #target_model_class  = target_model_type.model_class()
    target_model_class  = version.getModelClass(target_model_name)
    target_model_proxy  = MetadataModelProxy.objects.get(version=version,model_name=target_model_name)

    # so now that we know the target class and the customizer name, lets see if we can find a model customizer for it
    created = False
    try:
        target_model_customizer = MetadataModelCustomizer.objects.get(
            project=project,
            version=version,
            model=target_model_name,
            name=customizer_name
        )
    except MetadataModelCustomizer.DoesNotExist:
        target_model_customizer = MetadataModelCustomizer(
            project=project,
            version=version,
            model=target_model_name,
            name=customizer_name
        )
        target_model_customizer.reset(target_model_proxy)
        created = True

    if request.method == "POST":
        
        validity = []
        model_customizer_form = MetadataModelCustomizerForm( \
            request.POST,
            instance=target_model_customizer,
            initial = {
                "project"                       : project,
                "version"                       : version,
                "model"                         : target_model_name,
                "categorization"                : categorization,
                "vocabularies"                  : [vocabulary],
                "prefix"                        : "customize_subform",
            }
        )
        standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
            instance=target_model_customizer,
            prefix = "customize_subform",
            request=request
        )

        validity += [model_customizer_form.is_valid()]
        validity += [standard_property_customizer_formset.is_valid()]

        
        if all(validity):

            target_model_customizer_instance = model_customizer_form.save()
            standard_property_customizer_instances = standard_property_customizer_formset.save(commit=False)
            for standard_property_customizer_instance in standard_property_customizer_instances:
                standard_property_customizer_instance.setParent(target_model_customizer_instance)
                standard_property_customizer_instance.save()

            return HttpResponse("success")
            #json_target_model_customizer = json.dumps({"pk":target_model_customizer.pk,"unicode":u'%s'%target_model_customizer})
            #return HttpResponse(json_target_model_customizer,mimetype='application/json')

        else:

            msg = "Unable to save the customization.  Please review the form and try again."


    else: # request.method == "GET":

        model_customizer_form = MetadataModelCustomizerForm( \
            instance=target_model_customizer,
            initial = {
                "project"                       : project,
                "version"                       : version,
                "model"                         : target_model_name,
                "categorization"                : categorization,
                "vocabularies"                  : [vocabulary],
                "prefix"                        : "customize_subform",
            }
        )

        if created:

            standard_property_customizers = []
            standard_property_proxies   = MetadataStandardPropertyProxy.objects.filter(version=version,model_name=target_model_name)
            for standard_property_proxy in standard_property_proxies:
                standard_property_customizer = MetadataStandardPropertyCustomizer(project=project,version=version,model=target_model_name)
                standard_property_customizer.reset(standard_property_proxy)
                standard_property_customizers.append(standard_property_customizer)

            initial_standard_property_customizer_data = [
                get_initial_data(standard_property_customizer,{
                    "project"   : project,
                    "version"   : version,
                    "model"     : target_model_name,
                    "category"  : standard_property_customizer.category,
                    "proxy"     : standard_property_customizer.proxy,
                })
                for standard_property_customizer in standard_property_customizers
            ]
            standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
                instance=target_model_customizer,
                initial=initial_standard_property_customizer_data,
                extra=len(initial_standard_property_customizer_data),
                prefix="customize_subform",
                request=request,
            )

            # TODO: NOT CURRENTLY BOTHERING W/ SCIENTIFIC PROPERTIES OF SUBFORMS

        else:

            # using an existing customization (no need to deal w/ proxies)

            standard_property_customizer_formset = MetadataStandardPropertyCustomizerInlineFormSetFactory(
                instance    = target_model_customizer,
                prefix = "customize_subform",
                request     = request,
                
            )

            # TODO: NOT CURRENTLY BOTHERING W/ SCIENTIFIC PROPERTIES OF SUBFORMS

    
    # gather all the extra information required by the template
    dict = {
        "STATIC_URL"                                  : "/static/",
        "msg"                                         : msg,
        "model_customizer_form"                       : model_customizer_form,
        "standard_property_customizer_formset"        : standard_property_customizer_formset,
        #"scientific_property_customizer_formset"      : scientific_property_customizer_formset,
        "project"                                     : project,
        "version"                                     : version,
        "target_model_class"                          : target_model_class,
        "parent_model_class"                          : model_class,
        "parent_property_name"                        : field_name,
        # some stuff I may need to do b/c of AJAX issues...
        "csrf_token_value"                            : request.COOKIES["csrftoken"],
        "field_name"                                  : field_name,
    }

    
    rendered_form = django.template.loader.render_to_string("dcf/dcf_customize_subform.html", dictionary=dict, context_instance=RequestContext(request))
    return HttpResponse(rendered_form,mimetype='text/html')

