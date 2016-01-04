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
from uuid import UUID as generate_uuid

from Q.questionnaire.serializers.serializers_base import QSerializer, QListSerializer
from Q.questionnaire.models.models_proxies import QComponentProxy


class QComponentProxySerializer(QSerializer):
    """
    serializes ComponentProxies,
    but doesn't deal w/ complexities of saving them;
    this is just used as a nested field on QModelCustomizationVocabularySerializer
    to provde ng w/ info.
    """
    class Meta:
        model = QComponentProxy
        list_serializer_class = QListSerializer
        fields = (
            # 'id',
            'name',
            'order',
            'key',
            'num_properties',
        )

    key = serializers.SerializerMethodField(read_only=True)
    num_properties = serializers.SerializerMethodField(read_only=True)

    def get_key(self, obj):
        return obj.get_key()

    def get_num_properties(self, obj):
        return obj.scientific_property_proxies.count()
