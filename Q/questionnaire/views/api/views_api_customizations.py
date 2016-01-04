####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'


from django.http import Http404
from django.contrib import messages

from rest_framework import generics, filters, renderers, viewsets, status, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from django_filters import FilterSet

from Q.questionnaire.models.models_customizations import QModelCustomization, serialize_customization_set
from Q.questionnaire.serializers.serializers_customizations_models import QModelCustomizationSerializer
from Q.questionnaire.models.models_users import is_admin_of

from Q.questionnaire.views.api.views_api_base import BetterBooleanFilter
from Q.questionnaire.views.views_base import get_key_from_request, get_cached_object

from Q.questionnaire.q_fields import allow_unsaved_fk
from Q.questionnaire.q_utils import QError

class QModelCustomizationFilter(FilterSet):

    class Meta:
        model = QModelCustomization
        fields = [
            'id',
            'guid',
            'created',
            'modified',
            'name',
            'description',
            'is_default',
            'ontology',
            'proxy',
            'project',
            'vocabularies',
            'model_title',
            'model_description',
            'model_show_all_categories',
            'model_show_hierarchy',
            'model_hierarchy_name',
            'model_root_component',
        ]

    is_default = BetterBooleanFilter(name="is_default")

    @classmethod
    def get_field_names(cls):
        """
        Simple way to make sure that _all_ filtered fields
        are available to the views below
        """
        return tuple(cls.Meta.fields)

class QCustomizationPermission(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # anybody can submit GET, HEAD, or OPTIONS requests
        if request.method in permissions.SAFE_METHODS:
            return True

        project = obj.project
        if not project.authenticated:
            return True

        # every other request requires project admin permissions
        current_user = request.user
        return current_user.is_authenticated() and is_admin_of(current_user, project)


class QModelCustomizationList(APIView):
    """
    List models, or create a new model.
    """

    permission_classes = [QCustomizationPermission]

    def get(self, request, format=None):
        assert request.method == "GET"
        models = QModelCustomization.objects.all()
        serializer = QModelCustomizationSerializer(models, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request, format=None):
        assert request.method == "POST"
        serializer = QModelCustomizationSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            # if I am POSTing new data, then I have created a new customization set,
            # which means, implicitly, that the set  will have a new name
            # which means that I will redirect to a new page ("www.domain.com/~/new_name)
            # so use Django's messaging framework to add the success message;
            # this will automatically get rendered upon the new page load
            msg = "Successfully saved customization."
            messages.add_message(request._request, messages.SUCCESS, msg)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QModelCustomizationDetail(APIView):
    """
    Retrieve, update or delete a model instance.
    """

    def get_object(self, pk):
        try:
            return QModelCustomization.objects.get(id=pk)
        except QModelCustomization.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        assert request.method == "GET"
        model = self.get_object(pk)
        serializer = QModelCustomizationSerializer(model, context={"request": request})
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        assert request.method == "PUT"
        model = self.get_object(pk)
        old_customization_name = model.name
        serializer = QModelCustomizationSerializer(model, data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            model.refresh_from_db()
            if old_customization_name != model.name:
                # as above, if I've changed the name I will reload the page
                # this msg automatically get rendered upon the new page load
                msg = "Successfully saved customization."
                messages.add_message(request._request, messages.SUCCESS, msg)
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        assert request.method == "DELETE"

        model = self.get_object(pk)
        model.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


# this is a one-off view for getting the cached customization_set as JSON from the session store
# it doesn't go through the usual DRF serializer creation workflow
# b/c all of the m2m fields could be unsaved and that would cause loads of problems down the line
# (see the comments in "serialize_customization_set" for more info)
# TODO: GET THIS WORKING W/ THE USUAL DRF SERIALIZER CREATION WORKFLOW (REQUIRES SOMETHING LIKE "allow_unsaved_fk")
@api_view()
def get_cached_customization(request):
    assert request.method == "GET"

    try:
        session_key = get_key_from_request(request)
        cached_customization_set_key = "{0}_customization_set".format(session_key)
        customization_set = get_cached_object(request.session, cached_customization_set_key)
    except QError:
        # TODO: THIS SECTION JUST EXISTS FOR DEBUGGING
        session_key = "bf505bfb-42b4-46c7-bca0-d5774bc518e3"
        cached_customization_set_key = "{0}_customization_set".format(session_key)
        customization_set = get_cached_object(request.session, cached_customization_set_key)

    serialized_customization_set = serialize_customization_set(customization_set)
    return Response(serialized_customization_set)
