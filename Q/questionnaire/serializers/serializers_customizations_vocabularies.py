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

"""
.. module:: serializers_customizations_vocabularies

DRF Serializers for customization classes

"""

from rest_framework import serializers

from Q.questionnaire.serializers.serializers_customizations import QCustomizationSerializer, QCustomizationListSerializer
from Q.questionnaire.serializers.serializers_proxies import QComponentProxySerializer
from Q.questionnaire.models.models_customizations import QModelCustomizationVocabulary


class QModelCustomizationVocabularySerializer(QCustomizationSerializer):
    class Meta:
        model = QModelCustomizationVocabulary
        list_serializer_class = QCustomizationListSerializer
        fields = (
            'id',
            'model_customization',
            'vocabulary',
            'order',
            'active',
            # these next 4 fields are not part of the model
            # but they are used to facilitate ng interactivity on the client
            'display_detail',
            'vocabulary_name',
            'vocabulary_key',
            'components',
        )

    # even though 'model_customization' is a required field of the QModelCustomizationVocabulary model,
    # it cannot possibly be set before the parent model_customization itself has been saved;
    # so I set 'allow_null' to True here...
    model_customization = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    display_detail = serializers.SerializerMethodField(read_only=True)  # name="get_display_detail"

    vocabulary_name = serializers.SerializerMethodField(read_only=True)  # method_name="get_vocabulary_name"

    vocabulary_key = serializers.SerializerMethodField(read_only=False)  # method_name="get_vocabulary_key"

    components = QComponentProxySerializer(many=True, read_only=True, required=False, source="vocabulary.component_proxies")

    def get_display_detail(self, obj):
        # this controls whether the corresponding vocabulary tab should be displayed
        # setting it so that the 1st vocabulary is displayed
        return obj.order == 1

    def get_vocabulary_name(self, obj):
        return "{0}".format(obj.vocabulary)

    def get_vocabulary_key(self, obj):
        return obj.vocabulary.get_key()

    def create(self, validated_data):
        # import ipdb; ipdb.set_trace()
        return super(QModelCustomizationVocabularySerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        # import ipdb; ipdb.set_trace()
        return super(QModelCustomizationVocabularySerializer, self).update(instance, validated_data)

    def to_internal_value(self, data):
        # note: this comment is no longer true!
        # """
        # This overrides the base ModelSerializer.to_internal_value() fn which was returning an OrderedDict
        # The follow-on fns expected to be working w/ actual instances rather than dicts
        # :param data: the raw data dictionary for this serialization's underlying model
        # :return: an instance of the underlying model
        # """
        # internal_data = dict(super(QModelCustomizationVocabularySerializer, self).to_internal_value(data))
        # try:
        #     vocabulary_customization = QModelCustomizationVocabulary.objects.get(pk=data.pop("id", None))
        #     for key, value in internal_data.iteritems():
        #         setattr(vocabulary_customization, key, value)
        # except QModelCustomizationVocabulary.DoesNotExist:
        #     vocabulary_customization = QModelCustomizationVocabulary(**internal_data)
        # return vocabulary_customization
        data.pop("components", None)
        internal_value = super(QModelCustomizationVocabularySerializer, self).to_internal_value(data)
        # no need to update guid b/c QModelCustomizationVocabulary does not have a guid (it is just a "through model")
        # internal_value.update({
        #     "guid": generate_uuid(data.get("key"))
        # })
        pk = data.get("id")
        if pk:
            internal_value.update({
                "id": pk,  # put id back so that update/create will work for QListSerializer
            })
        return internal_value


