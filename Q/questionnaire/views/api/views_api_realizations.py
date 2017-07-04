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

from Q.questionnaire.models.models_realizations import QModelRealization, serialize_realizations, set_version
from Q.questionnaire.models.models_users import is_admin_of, is_member_of, is_user_of
from Q.questionnaire.serializers.serializers_realizations import QModelRealizationSerializer
from Q.questionnaire.views.api.views_api_base import BetterBooleanFilter
from Q.questionnaire.views.views_base import get_key_from_request, get_cached_object
from Q.questionnaire.q_utils import QError

# the API views for realizations only need to deal w/ QModelRealization
# b/c all of the other types of realizations are handled implicitly in the creation of a QModelRealizationSerializer


class QModelRealizationFilter(FilterSet):

    class Meta:
        model = QModelRealization
        fields = [
            'id',
            'guid',
            'created',
            'modified',
            'project',
            'proxy',
            'version',
            'is_document',
            'is_root',
            'is_complete',
            'is_published',
        ]

    is_document = BetterBooleanFilter(name="is_document")
    is_root = BetterBooleanFilter(name="is_root")
    is_complete = BetterBooleanFilter(name="is_complete")
    is_published = BetterBooleanFilter(name="is_published")

    @classmethod
    def get_field_names(cls):
        """
        Simple way to make sure that _all_ filtered fields
        are available to the views below
        """
        return tuple(cls.Meta.fields)


class QRealizationPermission(permissions.BasePermission):
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

        # but every other request requires project admin permissions
        current_user = request.user
        return current_user.is_authenticated() and is_user_of(current_user, project)


class QModelRealizationList(APIView):
    """
    List existing models, or create a new model.
    """

    permission_classes = [QRealizationPermission]

    def get(self, request, format=None):
        assert request.method == "GET"
        models = QModelRealization.objects.all()
        serializer = QModelRealizationSerializer(models, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request, format=None):
        assert request.method == "POST"
        serializer = QModelRealizationSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            model_realization = serializer.save()
            # TODO: ALL OF THIS LOOPING AROUND AND DB HITTING IS INEFFICIENT; CAN I DO THIS ON THE SERIALIZED DATA INSTEAD?
            model_realization.version += "0.1"  # a successful save means we ought to increment the document version
            set_version(model_realization, model_realization.version)
            msg = "Successfully saved document (version {0}.{1}).".format(
                model_realization.get_version_major(),
                model_realization.get_version_minor(),
            )
            messages.add_message(request._request, messages.SUCCESS, msg)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QModelRealizationDetail(APIView):
    """
    retrieve, update or delete an existing model instance.
    """

    def get_object(self, pk):
        try:
            return QModelRealization.objects.get(id=pk)
        except QModelRealization.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        assert request.method == "GET"
        model = self.get_object(pk)
        serializer = QModelRealizationSerializer(model, context={"request": request})
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        assert request.method == "PUT"
        model = self.get_object(pk)
        serializer = QModelRealizationSerializer(model, data=request.data, context={"request": request})

        if serializer.is_valid():
            model_realization = serializer.save()
            # TODO: ALL OF THIS LOOPING AROUND AND DB HITTING IS INEFFICIENT; CAN I DO THIS ON THE SERIALIZED DATA INSTEAD?
            model_realization.version += "0.1"  # a successful save means we ought to increment the document version
            set_version(model_realization, model_realization.version)
            msg = "Successfully saved document (version {0}.{1}).".format(
                model_realization.get_version_major(),
                model_realization.get_version_minor(),
            )
            messages.add_message(request._request, messages.SUCCESS, msg)
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        assert request.method == "DELETE"

        model = self.get_object(pk)
        model.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


# this is a one-off view for getting the cached realizations as JSON from the session store
# it doesn't go through the usual DRF serializer creation workflow
# (see the comments in "questionnaire.models.models_realizations.serialize_customizations" for more info)
# TODO: IS THERE ANY WAY TO GET THIS WORKING W/ THE USUAL DRF SERIALIZER CREATION WORKFLOW ?
@api_view()
def get_cached_realizations(request):
    assert request.method == "GET"
    try:
        session_key = get_key_from_request(request)
        cached_realizations_key = "{0}_realizations".format(session_key)
        realizations = get_cached_object(request.session, cached_realizations_key)
    except QError:
        # ** THIS SECTION JUST EXISTS FOR DEBUGGING **
        import ipdb; ipdb.set_trace()
        session_key = "461dafef-5f63-46de-a41f-5b3d2493fe3f"
        cached_realizations_key = "{0}_realizations".format(session_key)
        realizations = get_cached_object(request.session, cached_realizations_key)

    serialized_realizations = serialize_realizations(realizations)
    return Response(serialized_realizations)
