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
.. module:: serializers_realizations

DRF Serializers for realizations classes

"""

from Q.questionnaire.serializers.serializers_base import QSerializer, QListSerializer, QManagedRelatedField

class QRealizationSerializer(QSerializer):
    pass

class QRealizationListSerializer(QListSerializer):
    pass

class QRealizationManagedRelatedField(QManagedRelatedField):
    class Meta:
        list_serializer_class = QRealizationListSerializer
