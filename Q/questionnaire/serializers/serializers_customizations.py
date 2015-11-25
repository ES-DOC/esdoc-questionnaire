####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

"""
.. module:: serializers_customizations

DRF Serializers for customization classes

"""


from Q.questionnaire.serializers.serializers_base import QSerializer, QListSerializer


class QCustomizationSerializer(QSerializer):
    pass


class QCustomizationListSerializer(QListSerializer):
    pass
