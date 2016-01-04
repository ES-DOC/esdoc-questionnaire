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

from Q.questionnaire.models.models_projects import QProject

class QProjectSerializer(serializers.ModelSerializer):

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
            'authenticated',
            'vocabularies',
        )
