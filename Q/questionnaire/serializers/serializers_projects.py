####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.contrib.auth.models import User
from itertools import chain
from rest_framework import serializers

from Q.questionnaire.models.models_projects import QProject

# just using the standard ModleSerializer for these classes
# no need to inherit from QSerializer; no need for recursion
# ...nothing fancy to see here


class QProjectUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "groups",
            # "is_user",
            # "is_member",
            # "is_admin",
        ]

    groups = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    # is_user = serializers.SerializerMethodField()
    # is_member = serializers.SerializerMethodField()
    # is_admin = serializers.SerializerMethodField()


class QProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = QProject
        fields = [
            'id',
            'name',
            'title',
            'description',
            'email',
            'url',
            'ontologies',
            'is_displayed',
            'authenticated',
            # these next few fields are not part of the model
            'user_group_name',
            'member_group_name',
            'admin_group_name',
            'users',
            'pending_users',
        ]

    ontologies = serializers.SerializerMethodField()

    user_group_name = serializers.SerializerMethodField()
    member_group_name = serializers.SerializerMethodField()
    admin_group_name = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()
    pending_users = serializers.SerializerMethodField()

    def get_ontologies(self, obj):
        return [
            {
                "name": o.key,
                "documentation": o.documentation
            }
            for o in obj.ontologies.all()
        ]

    def get_user_group_name(self, obj):
        return "{0}_{1}".format(obj.name, "user")

    def get_member_group_name(self, obj):
        return "{0}_{1}".format(obj.name, "member")

    def get_admin_group_name(self, obj):
        return "{0}_{1}".format(obj.name, "admin")

    def get_users(self, obj):
        member_users = obj.get_member_users()
        admin_users = obj.get_admin_users()
        users = set(chain(member_users, admin_users))
        serialized_users = [
            QProjectUserSerializer(user).data
            for user in users
        ]
        return serialized_users

    def get_pending_users(self, obj):
        serialized_pending_users = [
            QProjectUserSerializer(user).data
            for user in obj.get_pending_users()
        ]
        return serialized_pending_users

from Q.questionnaire.models.models_proxies import QModelProxy
from Q.questionnaire.q_constants import SUPPORTED_DOCUMENTS_TEST_MAP
import copy


class QProjectTestDocumentTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = QModelProxy
        fields = [
            'name',
            'ontology',
            'key',
            'title',
            'type',
            'category',
            'is_active',
        ]

    ontology = serializers.SlugRelatedField(read_only=True, slug_field="key")
    title = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    def get_title(self, obj):
        document_type_key = obj.cim_id.rsplit('.')[-1]
        return SUPPORTED_DOCUMENTS_TEST_MAP[document_type_key].get("title")

    def get_type(self, obj):
        document_type_key = obj.cim_id.rsplit('.')[-1]
        return SUPPORTED_DOCUMENTS_TEST_MAP[document_type_key].get("type")

    def get_category(self, obj):
        document_type_key = obj.cim_id.rsplit('.')[-1]
        return SUPPORTED_DOCUMENTS_TEST_MAP[document_type_key].get("category")

    def get_is_active(self, obj):
        # if I have found a model_proxy to serialize, then it is, by definition, active
        # (even though it may not have been customized yet... there is error-handling in "q_dit" to cope w/ that situation)
        return True

    def to_representation(self, instance):
        # when serializing a DocumentType, remove category info completely for anything w/out a category
        # (this will ensure it does not get rendered in an <optgroup> element by the "ng-options" directive
        data_dict = super(QProjectTestDocumentTypeSerializer, self).to_representation(instance)
        if data_dict.get("category") is None:
            data_dict.pop("category")
        return data_dict


class QProjectTestSerializer(serializers.ModelSerializer):

    class Meta:
        model = QProject
        fields = [
            'id',
            'name',
            'title',
            'description',
            'email',
            'url',
            'is_displayed',
            'authenticated',
            'document_types',
        ]

    document_types = serializers.SerializerMethodField()

    # THIS (SIMPLE) FN ONLY RETURNS ACTIVE DOCUMENT_TYPES
    # def get_document_types(self, obj):
    #     document_types = []
    #     for ontology in obj.ontologies.all():
    #         for model_proxy in ontology.model_proxies.filter(name__in=SUPPORTED_DOCUMENTS_TEST_MAP.keys()):
    #             document_types.append(QProjectTestDocumentTypeSerializer(model_proxy).data)
    #     return document_types

    # THIS (COMPLEX) FN RETURNS ALL DOCUMENT_TYPES
    def get_document_types(self, obj):
        document_types = []
        model_proxies = QModelProxy.objects.filter(ontology__in=obj.ontologies.all(), is_document=True)
        for document_type_name, document_type_value in copy.deepcopy(SUPPORTED_DOCUMENTS_TEST_MAP).items():
            try:
                # here is a regex which matches anything followed by a dot followed by the document_type_name
                model_proxy = model_proxies.get(cim_id__regex=r"^.*\.{0}$".format(document_type_name))
                document_types.append(QProjectTestDocumentTypeSerializer(model_proxy).data)
            except QModelProxy.DoesNotExist:
                if document_type_value.get("category") is None:
                    document_type_value.pop("category")
                document_types.append(document_type_value)
        return document_types
