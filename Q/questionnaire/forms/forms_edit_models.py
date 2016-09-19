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


from django.forms import ValidationError

from Q.questionnaire.forms.forms_edit import QRealizationForm
from Q.questionnaire.models.models_realizations import QModel
from Q.questionnaire.q_utils import set_field_widget_attributes, update_field_widget_attributes, pretty_string

# TODO: I AM EXCLUDING CERTAIN FIELDS SO THAT THEY DON'T CHANGE THE NG-MODEL
# TODO: I AM DOING THIS FOR ALL QREALIZATIONS
# TODO: DOUBLE-CHECK THAT THIS WORKS
# TODO: (THEY ARE PREFACED BY "##")

class QModelRealizationForm(QRealizationForm):

    class Meta:
        model = QModel
        fields = [
            # 'id',
            # 'guid',
            # 'created',
            # 'modified',
            'project',
            'ontology',
            'proxy',
            'name',
            'description',
            'is_document',
            'is_root',
            'is_published',
            'is_active',
            # 'is_complete',
            #'synchronization',
            # 'properties',
        ]

    _hidden_fields = ["project", "ontology", "proxy", ]  # "is_complete", ]
    _model_fields = ["description", ]
    _other_fields = []

    def get_hidden_fields(self):
        """
        get fields that are needed to pass to the server, but not for the user to edit
        :return:
        """
        return self.get_fields_from_list(self._hidden_fields)

    def get_model_fields(self):
        """
        get fields that are just for the model itself
        :return:
        """
        return self.get_fields_from_list(self._model_fields)

    def get_other_fields(self):
        """
        get any fields that are leftover
        :return:
        """
        return self.get_fields_from_list(self._other_fields)

    # def __init__(self, *args, **kwargs):
    #     super(QModelRealizationForm, self).__init__(*args, **kwargs)

    def customize(self, customization=None):
        if not customization:
            realization = self.instance
            customization = realization.get_default_customization()
        assert(customization.proxy == self.instance.proxy)

        # customize the QModel Description...
        self.set_default_field_value("description", customization.model_description)

        self.customization = customization

    def clean(self):
        # calling the parent class's clean fun automatically sets a
        # flag that forces unique (and unique_together) validation
        # (although this isn't actually used now that data is routed through the REST API)
        super(QModelRealizationForm, self).clean()
        cleaned_data = self.cleaned_data
        return cleaned_data
