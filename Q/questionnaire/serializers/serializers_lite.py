####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from rest_framework import serializers

from Q.questionnaire.models.models_projects import QProject
from Q.questionnaire.models.models_customizations import QModelCustomization
from Q.questionnaire.models.models_realizations import QModelRealization
from Q.questionnaire.serializers.serializers_base import QVersionSerializerField


class QProjectSerializerLite(serializers.ModelSerializer):
    """
    This serializer is used in the Project Page
    It is really simple; hence the name "lite"
    """

    class Meta:
        model = QProject
        fields = (
            'id',
            'name',
            'title',
            'description',
            'email',
            'url',
            'is_active',
            'is_displayed',
            'is_legacy',
            'authenticated',
            'ontologies',
        )


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
            "id", "key", "created", "modified",
            "name", "documentation", "project", "proxy_title", "proxy_name", "is_default",
            "path", "ontology", "synchronization",
        )

    proxy_title = serializers.SerializerMethodField()
    proxy_name = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()  # method_name="get_path"
    ontology = serializers.SerializerMethodField()  # method_name="get_ontology"
    synchronization = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="type",
    )

    def get_proxy_name(self, obj):
        return obj.proxy.name

    def get_proxy_title(self, obj):
        return str(obj.proxy)

    def get_path(self, obj):
        """
        returns the URL path to use for this document
        ie: the bit after "verb/" in "http://domain/project/verb/ontology_key/document_type/id"
        :param obj:
        :return:
        """
        # project_name = obj.project.name.lower()
        ontology_key = obj.proxy.ontology.key
        document_type = obj.proxy.name.lower()
        path = "{0}/{1}/{2}".format(
            ontology_key,
            document_type,
            obj.name,
        )
        return path

    def get_ontology(self, obj):
        return str(obj.proxy.ontology)


class QModelRealizationSerializerLite(serializers.ModelSerializer):
    """
    This serializer is used in the Project Page
    It is just a flat representation of a realization
    w/out bothering to recurse through all of the properties
    hence the name "lite"
    """

    class Meta:
        model = QModelRealization
        fields = (
            "id", "key", "created", "modified",
            "project", "proxy_title", "proxy_name", "label", "is_complete", "is_published", "is_root", "version", "is_active",
            "last_published", "path", "ontology", "synchronization",
        )

    proxy_title = serializers.SerializerMethodField()
    proxy_name = serializers.SerializerMethodField()
    version = QVersionSerializerField()
    last_published = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()
    ontology = serializers.SerializerMethodField()

    synchronization = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="type",
    )

    def get_proxy_name(self, obj):
        return obj.proxy.name

    def get_proxy_title(self, obj):
        return str(obj.proxy)

    def get_last_published(self, obj):
        if obj.is_published:
            last_publication = obj.publications.order_by("modified").last()
            return last_publication.modified
        return None

    def get_path(self, obj):
        """
        returns the URL path to use for this document
        ie: the bit after "verb/" in "http://domain/project/verb/ontology_key/document_type/id"
        :param obj:
        :return:
        """
        # project_name = obj.project.name.lower()
        ontology_key = obj.proxy.ontology.key
        document_type = obj.proxy.name.lower()
        path = "{0}/{1}/{2}".format(
            ontology_key,
            document_type,
            obj.id,
        )
        return path

    def get_ontology(self, obj):
        return str(obj.proxy.ontology)
