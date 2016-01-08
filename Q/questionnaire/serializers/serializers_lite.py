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

# TODO: THIS ONLY EXISTS FOR v0.15
from Q.questionnaire.models.models_realizations_bak import MetadataModel

# TODO: THIS ONLY EXISTS FOR v0.15
class MetadataModelSerializerLite(serializers.ModelSerializer):
    """
    This serializer is used in the Project Page
    It is just a flat representation of a model
    w/out bothering to recurse through all of the properties
    """

    class Meta:
        model = MetadataModel
        fields = (
            "id", "guid", "created", "modified", "name", "version",
            "description", "ontology", "proxy", "project", "is_document",
            "is_complete", "is_root", "is_published", "is_active",
            "published", "synchronization", "label", "path",
        )

    proxy = serializers.StringRelatedField(read_only=True)
    modified = serializers.SerializerMethodField()  # method_name="get_modified"
    version = serializers.SerializerMethodField()  # method_name="get_version"
    ontology = serializers.SerializerMethodField()  # method_name="get_ontology"
    is_complete = serializers.SerializerMethodField()  # method_name="get_is_complete"
    is_active = serializers.SerializerMethodField()  # method_name="get_is_active"
    published = serializers.SerializerMethodField()  # method_name="get_published"
    synchronization = serializers.SerializerMethodField()  # method_name="get_synchronization"
    label = serializers.SerializerMethodField()  # method_name="get_label"
    path = serializers.SerializerMethodField()  # method_name="get_path"

    def get_modified(self, obj):
        return obj.last_modified

    def get_version(self, obj):
        return obj.document_version

    def get_ontology(self, obj):
        return str(obj.version)

    def get_is_complete(self, obj):
        return obj.is_complete()

    def get_is_active(self, obj):
        return obj.active

    def get_published(self, obj):
        return obj.get_last_publication_date()

    def get_synchronization(self, obj):
        return []

    def get_label(self, obj):
        return obj.get_label()

    def get_path(self, obj):
        """
        returns the URL path to use for this document
        ie: the bit after "verb/" in "http://domain/project/verb/ontology_key/document_type/id"
        :param obj:
        :return:
        """
        # project_name = obj.project.name.lower()
        ontology_key = obj.version.get_key().lower()
        document_type = obj.proxy.name.lower()
        return "%s/%s/%s" % (ontology_key, document_type, obj.pk)


class QModelSerializerLite(serializers.ModelSerializer):
    """
    This serializer is used in the Project Page
    It is just a flat representation of a model
    w/out bothering to recurse through all of the properties
    """

    class Meta:
        model = QModel
        fields = (
            "id", "guid", "created", "modified", "name", "version",
            "description", "ontology", "proxy", "project", "is_document",
            "is_complete", "is_root", "is_published", "is_active", "parent",
            "synchronization", "label", "path",
        )

    # these relationships use StringRelatedField, which means it returns the __unicode__ fn
    ontology = serializers.StringRelatedField(read_only=True)
    proxy = serializers.StringRelatedField(read_only=True)

    label = serializers.SerializerMethodField()  # method_name="get_label"
    path = serializers.SerializerMethodField()  # method_name="get_path"

    synchronization = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="type",
    )

    def get_label(self, obj):
        return obj.get_label()

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
        return "%s/%s/%s" % (ontology_key, document_type, obj.pk)


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
        return "%s/%s/%s" % (ontology_key, document_type, obj.name)
