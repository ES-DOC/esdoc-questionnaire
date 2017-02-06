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
from Q.questionnaire.q_utils import serialize_model_to_dict

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
            'is_displayed',
            'authenticated',
            # these next few fields are not part of the model
            'user_group_name',
            'member_group_name',
            'admin_group_name',
            'users',
            'pending_users',
        ]

    user_group_name = serializers.SerializerMethodField()
    member_group_name = serializers.SerializerMethodField()
    admin_group_name = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()
    pending_users = serializers.SerializerMethodField()

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