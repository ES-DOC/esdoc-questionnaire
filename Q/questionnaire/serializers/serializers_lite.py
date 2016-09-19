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

from rest_framework import serializers
from Q.questionnaire.models.models_realizations import QModel
from Q.questionnaire.models.models_customizations import QModelCustomization


class QModelCustomizationSerializerLite(serializers.ModelSerializer):
    """
    This serializer is used in the Project Page
    It is just a flat representation of a customization
    w/out bothering to recurse through all of the properties
    hence the name "lite"
    """

    class Meta:
        model = QModelCustomization
        fields = (
            "id", "guid", "created", "modified", "name",
            "description", "ontology", "proxy", "project", "is_default",
            "synchronization", "path",
        )

    # these relationships use StringRelatedField, which means it returns the __unicode__ fn
    ontology = serializers.StringRelatedField(read_only=True)
    proxy = serializers.StringRelatedField(read_only=True)

    synchronization = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="type",
    )

    path = serializers.SerializerMethodField()  # method_name="get_path"

    def get_path(self, obj):
        """
        returns the URL path to use for this document
        ie: the bit after "verb/" in "http://domain/project/verb/ontology_key/document_type/id"
        :param obj:
        :return:
        """
        # project_name = obj.project.name.lower()
        ontology_key = obj.ontology.get_key().lower()
        document_type = obj.proxy.name.lower()
        path = "{0}/{1}/{2}".format(
            ontology_key,
            document_type,
            obj.name,
        )
        return path


class QModelRealizationSerializerLite(serializers.ModelSerializer):
    """
    This serializer is used in the Project Page
    It is just a flat representation of a realization
    w/out bothering to recurse through all of the properties
    hence the name "lite"
    """

    class Meta:
        model = QModel
        fields = (
            "id", "guid", "created", "modified", "is_published", "is_complete", "is_active",
            "description", "version", "ontology", "proxy", "project",
            "synchronization", "path",
        )

    # these relationships use StringRelatedField, which means it returns the __unicode__ fn
    ontology = serializers.StringRelatedField(read_only=True)
    proxy = serializers.StringRelatedField(read_only=True)

    version = serializers.SerializerMethodField(read_only=True)  # name="get_version"

    synchronization = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="type",
    )

    path = serializers.SerializerMethodField()  # method_name="get_path"
    # is_complete = serializers.SerializerMethodField()  # method_name="get_is_complete"

    def get_version(self, obj):
        """
        returns a nicely formated version field to display on the project page
        (recall that for documents, I only care about major & minor versions - not patch versions)
        :param obj:
        :return:
        """
        if not obj.version:
            return None
        return "{0}.{1}".format(
            obj.get_version_major(),
            obj.get_version_minor(),
        )

    def get_path(self, obj):
        """
        returns the URL path to use for this document
        ie: the bit after "verb/" in "http://domain/project/verb/ontology_key/document_type/id"
        :param obj:
        :return:
        """
        # project_name = obj.project.name.lower()
        ontology_key = obj.ontology.get_key().lower()
        document_type = obj.proxy.name.lower()
        path = "{0}/{1}/{2}".format(
            ontology_key,
            document_type,
            obj.id,
        )
        return path

    # def get_is_complete(self, obj):
    #     """
    #     returns whether or not the obj is complete;
    #     only complete objects can be published
    #     :param obj:
    #     :return:
    #     """
    #     # strictly speaking, this fn is not needed b/c DRF is clever enough
    #     # to call a fn w/ the same name as a corresponding serialization field name
    #     # ...but I am pedantic
    #     return obj.is_complete()