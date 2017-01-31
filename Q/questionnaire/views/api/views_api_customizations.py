####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.contrib import messages
from django_filters import FilterSet
from django.http import Http404
from rest_framework import status, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from Q.questionnaire.models.models_customizations import QModelCustomization, serialize_customizations
from Q.questionnaire.models.models_users import is_admin_of, is_member_of, is_user_of
from Q.questionnaire.serializers.serializers_customizations import QModelCustomizationSerializer
from Q.questionnaire.views.api.views_api_base import BetterBooleanFilter
from Q.questionnaire.views.views_base import get_key_from_request, get_cached_object
from Q.questionnaire.q_utils import QError

# the API views for customizations only need to deal w/ QModelCustomization
# b/c all of the other types of customizations are handled implicitly in the creation of a QModelCustomizationSerializer


class QModelCustomizationFilter(FilterSet):

    class Meta:
        model = QModelCustomization
        fields = [
            'id',
            'name',
            'documentation',
            'is_default',
            'proxy',
            'project',
            'model_title',
            'model_description',
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

        # anybody can manipulate objects in a non-authenticated project
        project = obj.project
        if not project.authenticated:
            return True

        # but every other situation requires project admin permissions
        current_user = request.user
        return current_user.is_authenticated() and is_admin_of(current_user, project)


class QModelCustomizationList(APIView):
    """
    List existing models, or create a new model.
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
            model_customization = serializer.save()
            # if I am POSTing new data, then I have created a new set of customizations,
            # which means, implicitly, that they will have a new name
            # which means that I will redirect to a new page ("www.domain.com/~/new_name)
            # so use Django's messaging framework to add the success message;
            # this will automatically get rendered upon the new page load
            msg = "Successfully saved customization '{0}'.".format(model_customization.name)
            messages.add_message(request._request, messages.SUCCESS, msg)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QModelCustomizationDetail(APIView):
    """
    retrieve, update or delete an existing model instance.
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
        serializer = QModelCustomizationSerializer(model, data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            model.refresh_from_db()
            # unlike above, use Django's messaging framework regardless of whether the customization name changed
            # If it changed, it will be rendered upon the new page load;
            # if not, it will be rendered by the call to "check_msg" in "CustomizerController.submit_customization"
            msg = "Successfully saved customization '{0}'.".format(model.name)
            messages.add_message(request._request, messages.SUCCESS, msg)
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        assert request.method == "DELETE"

        model = self.get_object(pk)
        model.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


# this is a one-off view for getting the cached customizations as JSON from the session store
# it doesn't go through the usual DRF serializer creation workflow
# (see the comments in "questionnaire.models.models_customizations.serialize_customizations" for more info)
# TODO: IS THERE ANY WAY TO GET THIS WORKING W/ THE USUAL DRF SERIALIZER CREATION WORKFLOW ?
@api_view()
def get_cached_customizations(request):
    assert request.method == "GET"
    try:
        session_key = get_key_from_request(request)
        cached_customizations_key = "{0}_customizations".format(session_key)
        customizations = get_cached_object(request.session, cached_customizations_key)
    except QError:
        # ** THIS SECTION JUST EXISTS FOR DEBUGGING ** #
        import ipdb; ipdb.set_trace()
        session_key = "dee65324-7b03-4850-b246-28f3a72dd0df"
        cached_customizations_key = "{0}_customizations".format(session_key)
        customizations = get_cached_object(request.session, cached_customizations_key)

    serialized_customizations = serialize_customizations(customizations)
    return Response(serialized_customizations)
