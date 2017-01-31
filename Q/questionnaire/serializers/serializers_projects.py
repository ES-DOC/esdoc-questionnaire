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


class QProjectSerializer(serializers.ModelSerializer):

    # just use the standard ModelSerializer
    # no need to inherit from QSerializer; no need for recursion
    # ...nothing fancy to see here

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
