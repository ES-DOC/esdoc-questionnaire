
####################
#   CIM_Questionnaire
#   Copyright (c) 2014 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################


__author__="allyn.treshansky"
__date__ ="Sep 30, 2013 3:04:42 PM"

"""
.. module:: views_customize

views for editing a new or existing CIM Customization

"""

import re
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.exceptions import FieldError, MultipleObjectsReturned
from django.db.models.fields import BooleanField, CharField, TextField
from django.contrib.sites.models import get_current_site
from django.contrib import messages

from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer, MetadataModelCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel
from CIM_Questionnaire.questionnaire.models.metadata_project import MetadataProject
from CIM_Questionnaire.questionnaire.models.metadata_authentication import is_user_of, is_admin_of
from CIM_Questionnaire.questionnaire.forms.forms_customize import create_new_customizer_forms_from_models, create_existing_customizer_forms_from_models, create_customizer_forms_from_data
from CIM_Questionnaire.questionnaire.forms.forms_customize import save_valid_forms
from CIM_Questionnaire.questionnaire.views.views_base import get_key_from_request
from CIM_Questionnaire.questionnaire.views.views_base import validate_view_arguments
from CIM_Questionnaire.questionnaire.views.views_base import get_cached_new_customization_set, get_cached_existing_customization_set
from CIM_Questionnaire.questionnaire.views.views_error import questionnaire_error
from CIM_Questionnaire.questionnaire.views.views_authenticate import questionnaire_join
from CIM_Questionnaire.questionnaire import get_version


def questionnaire_customize_new(request, project_name="", model_name="", version_key="", **kwargs):

    # validate the arguments...
    (validity, project, version, model_proxy, msg) = validate_view_arguments(project_name=project_name, model_name=model_name, version_key=version_key)
    if not validity:
        return questionnaire_error(request,msg)
    request.session["checked_arguments"] = True

    # get the relevant vocabularies...
    vocabularies = project.vocabularies.filter(document_type__iexact=model_name)

    # check authentication...
    # (not using "@login_required" b/c some projects ignore authentication)
    if project.authenticated:
        current_user = request.user
        if not current_user.is_authenticated():
            return redirect('/login/?next=%s' % request.path)
        if not (request.user.is_superuser or request.user.metadata_user.is_admin_of(project)):
            return questionnaire_join(request, project, ["default", "user", "admin"])

    customizer_parameters = {
        "project": project,
        "version": version,
        "proxy": model_proxy,
    }
    initial_parameter_length = len(customizer_parameters)

    # check if the user added any parameters to the request...
    request_parameters = request.GET.copy()
    request_parameters.pop("profile", None)
    for (key, value) in request_parameters.iteritems():
        value = re.sub('[\"\']', '', value)  # strip out any quotes
        field_type = type(MetadataModelCustomizer.get_field(key))
        if field_type == BooleanField:
            # special case for boolean fields
            if value.lower() == "true" or value == "1":
                customizer_parameters[key] = True
            elif value.lower() == "false" or value == "0":
                customizer_parameters[key] = False
            else:
                customizer_parameters[key] = value
        elif field_type == CharField or field_type == TextField:
            # this ensures that the filter is case-insenstive for strings            
            # bear in mind that if I ever change to using get_or_create, the filter will _have_ to be case-sensitive
            # see https://code.djangoproject.com/ticket/7789 for more info
            customizer_parameters[key+"__iexact"] = value
        else:
            customizer_parameters[key] = value
    if len(customizer_parameters) > initial_parameter_length:
        # if there were (extra) filter parameters passed
        # then try to get the customizer w/ those parameters
        try:
            existing_model_customizer_instance = MetadataModelCustomizer.objects.get(**customizer_parameters)
            customize_existing_url = reverse("customize_existing", kwargs={
                "project_name": project_name,
                "model_name": model_name,
                "version_key": version_key,
                "customizer_name": existing_model_customizer_instance.name,
            })
            return HttpResponseRedirect(customize_existing_url)
        except FieldError:
            # raise an error if some of the filter parameters were invalid
            msg = "Unable to find a MetadataModelCustomizer with the following parameters: %s" \
                  % ", ".join([u'%s=%s' % (key, value) for (key, value) in customizer_parameters.iteritems()])
            return questionnaire_error(request, msg)
        except MultipleObjectsReturned:
            # raise an error if those filter params weren't enough to uniquely identify a customizer
            msg = "Unable to find a <i>single</i> MetadataModelCustomizer with the following parameters: %s" \
                  % ", ".join([u'%s=%s' % (key, value) for (key, value) in customizer_parameters.iteritems()])
            return questionnaire_error(request, msg)
        except MetadataModelCustomizer.DoesNotExist:
            # raise an error if there was no matching query
            msg = "Unable to find any MetadataModelCustomizer with the following parameters: %s" \
                  % ", ".join([u'%s=%s' % (key, value) for (key, value) in customizer_parameters.iteritems()])
            return questionnaire_error(request, msg)

    # get (or set) items from the cache...
    instance_key = get_key_from_request(request)
    customizer_set = get_cached_new_customization_set(instance_key, project, version, model_proxy, vocabularies)

    # now build the forms...
    if request.method == "GET":

        (model_customizer_form, standard_category_customizer_formset, standard_property_customizer_formset, scientific_category_customizer_formsets, scientific_property_customizer_formsets, model_customizer_vocabularies_formset) = \
            create_new_customizer_forms_from_models(customizer_set["model_customizer"], customizer_set["standard_category_customizers"], customizer_set["standard_property_customizers"], customizer_set["scientific_category_customizers"], customizer_set["scientific_property_customizers"], vocabularies_to_customize=vocabularies)

    else:  # request.method == "POST"

        data = request.POST.copy()  # sometimes I need to alter the data for unloaded forms;
                                    # this cannot be done on the original (immutable) QueryDict

        (validity, model_customizer_form, standard_category_customizer_formset, standard_property_customizer_formset, scientific_category_customizer_formsets, scientific_property_customizer_formsets, model_customizer_vocabularies_formset) = \
            create_customizer_forms_from_data(
                data,
                customizer_set["model_customizer"],
                customizer_set["standard_category_customizers"],
                customizer_set["standard_property_customizers"],
                customizer_set["scientific_category_customizers"],
                customizer_set["scientific_property_customizers"],
                vocabularies_to_customize=vocabularies
            )

        if all(validity):
            model_customizer_instance = save_valid_forms(
                model_customizer_form,
                standard_category_customizer_formset,
                standard_property_customizer_formset,
                scientific_category_customizer_formsets,
                scientific_property_customizer_formsets,
                model_customizer_vocabularies_formset
            )

            # this is used for other fns that might need to know what the view returns
            # (such as those in the testing framework)
            request.session["model_id"] = model_customizer_instance.pk

            messages.add_message(request, messages.SUCCESS, "Successfully saved customizer '%s'." % (model_customizer_instance.name))
            customize_existing_url = reverse("customize_existing", kwargs={
                "project_name": project_name,
                "model_name": model_name,
                "version_key": version_key,
                "customizer_name": model_customizer_instance.name,
            })
            return HttpResponseRedirect(customize_existing_url)

        else:

            messages.add_message(request, messages.ERROR, "Failed to save customization.")

    _dict = {
        "site": get_current_site(request),
        "project": project,
        "version": version,
        "vocabularies": vocabularies,
        "model_proxy": model_proxy,
        "model_customizer_form": model_customizer_form,
        "model_customizer_vocabularies_formset": model_customizer_vocabularies_formset,
        "standard_category_customizer_formset": standard_category_customizer_formset,
        "standard_property_customizer_formset": standard_property_customizer_formset,
        "scientific_category_customizer_formsets": scientific_category_customizer_formsets,
        "scientific_property_customizer_formsets": scientific_property_customizer_formsets,
        "questionnaire_version": get_version(),
        "instance_key": instance_key,
        "get_section_view_name": u"get_new_customize_form_section",
        "can_view": False,  # only customizers that have been saved and are default can be viewed
    }

    return render_to_response('questionnaire/questionnaire_customize.html', _dict, context_instance=RequestContext(request))


def questionnaire_customize_existing(request, project_name="", model_name="", version_key="", customizer_name="", **kwargs):

    # validate the arguments...
    (validity, project, version, model_proxy, msg) = validate_view_arguments(project_name=project_name, model_name=model_name, version_key=version_key)
    if not validity:
        return questionnaire_error(request,msg)
    request.session["checked_arguments"] = True

    # check authentication...
    # (not using "@login_required" b/c some projects ignore authentication)
    if project.authenticated:
        current_user = request.user
        if not current_user.is_authenticated():
            return redirect('/login/?next=%s' % request.path)
        if not (request.user.is_superuser or request.user.metadata_user.is_admin_of(project)):
            return questionnaire_join(request, project, ["default", "user", "admin"])

    # try to get the specified customization...
    try:
        model_customizer = MetadataModelCustomizer.objects.get(name__iexact=customizer_name, proxy=model_proxy, project=project, version=version)
        initial_model_customizer_name = model_customizer.name
        vocabularies = model_customizer.get_sorted_vocabularies()
    except MetadataModelCustomizer.DoesNotExist:
        msg = "Cannot find the <u>customizer</u> '%s' for that project/version/model combination" % customizer_name
        return questionnaire_error(request, msg)

    # get (or set) items from the cache...
    instance_key = get_key_from_request(request)
    customizer_set = get_cached_existing_customization_set(instance_key, model_customizer, vocabularies)

    # now build the forms...
    if request.method == "GET":

        (model_customizer_form, standard_category_customizer_formset, standard_property_customizer_formset, scientific_category_cusstomizer_formsets, scientific_property_customizer_formsets, model_customizer_vocabularies_formset) = \
            create_existing_customizer_forms_from_models(customizer_set["model_customizer"], customizer_set["standard_category_customizers"], customizer_set["standard_property_customizers"], customizer_set["scientific_category_customizers"], customizer_set["scientific_property_customizers"], vocabularies_to_customize=vocabularies)

    else:  # request.method == "POST":

        data = request.POST.copy()  # sometimes I need to alter the data for unloaded forms;
                                    # this cannot be done on the original (immutable) QueryDict

        (validity, model_customizer_form, standard_category_customizer_formset, standard_property_customizer_formset, scientific_category_cusstomizer_formsets, scientific_property_customizer_formsets, model_customizer_vocabularies_formset) = \
            create_customizer_forms_from_data(
                data,
                customizer_set["model_customizer"],
                customizer_set["standard_category_customizers"],
                customizer_set["standard_property_customizers"],
                customizer_set["scientific_category_customizers"],
                customizer_set["scientific_property_customizers"],
                vocabularies_to_customize=vocabularies
            )

        if all(validity):

            model_customizer_instance = save_valid_forms(
                model_customizer_form,
                standard_category_customizer_formset,
                standard_property_customizer_formset,
                scientific_category_cusstomizer_formsets,
                scientific_property_customizer_formsets,
                model_customizer_vocabularies_formset
            )
            current_model_customizer_name = model_customizer_instance.name
            if initial_model_customizer_name != current_model_customizer_name:
                model_customizer_instance.rename(current_model_customizer_name)

            # if there are existing instances which will use this customization,
            # I need to check to see if they require new bits
            # (eventually, I plan on changing the way this works; see #210, #242, #278)
            if model_customizer_instance.default:
                existing_realizations = MetadataModel.objects.filter(
                    project=model_customizer_instance.project,
                    proxy=model_customizer_instance.proxy,
                    is_document=True,
                )
                for existing_realization in existing_realizations:
                    existing_realization.update(model_customizer_instance)

            # this is used for other fns that might need to know what the view returns
            # (such as those in the testing framework)
            request.session["model_id"] = model_customizer_instance.pk

            messages.add_message(request, messages.SUCCESS, "Successfully saved customizer '%s'." % (model_customizer_instance.name))

        else:

            messages.add_message(request, messages.ERROR, "Failed to save customization.")

    # gather all the extra information required by the template
    _dict = {
        "site": get_current_site(request),
        "project": project,
        "version": version,
        "vocabularies": vocabularies,
        "model_proxy": model_proxy,
        "model_customizer_form": model_customizer_form,
        "model_customizer_vocabularies_formset": model_customizer_vocabularies_formset,
        "standard_category_customizer_formset": standard_category_customizer_formset,
        "standard_property_customizer_formset": standard_property_customizer_formset,
        "scientific_category_customizer_formsets": scientific_category_cusstomizer_formsets,
        "scientific_property_customizer_formsets": scientific_property_customizer_formsets,
        "questionnaire_version": get_version(),
        "instance_key": instance_key,
        "get_section_view_name": u"get_existing_customize_form_section/%s" % model_customizer.name,
        "can_view": model_customizer.default,  # only customizers that have been saved and are default can be viewed
    }

    return render_to_response('questionnaire/questionnaire_customize.html', _dict, context_instance=RequestContext(request))


def questionnaire_customize_help(request):

    active_projects = MetadataProject.objects.filter(active=True)
    current_user = request.user
    can_edit = any([is_user_of(current_user, project) for project in active_projects])
    can_customize = any([is_admin_of(current_user, project) for project in active_projects])

    # gather all the extra information required by the template
    _dict = {
        "site": get_current_site(request),
        "can_edit": can_edit,
        "can_customize": can_customize,
        "questionnaire_version": get_version(),
    }

    return render_to_response('questionnaire/questionnaire_help_customize.html', _dict, context_instance=RequestContext(request))
