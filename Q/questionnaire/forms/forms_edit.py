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

# from djangular.forms import NgModelForm, NgModelFormMixin, NgFormValidationMixin

import json

from django.forms import ValidationError
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import curry

from Q.questionnaire.forms.forms_base import QForm, QFormSet
from Q.questionnaire.q_utils import set_field_widget_attributes, update_field_widget_attributes, pretty_string, serialize_model_to_dict

# note: the same forms are used for "viewing" & "editing"

class QRealizationForm(QForm):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        customization = kwargs.pop("customization", None)
        super(QRealizationForm, self).__init__(*args, **kwargs)

        for field_name in self.fields.keys():
            # TODO: 'add_custom_potential_errors_to_field' CHECKS IF THESE ARE "REAL"
            # TODO: (ie: PART OF THE MODEL AND NOT FORM-ONLY) FIELDS; IT MIGHT BE BETTER TO
            # TODO: DO THAT CHECK HERE AND SAVE EFFORT
            self.add_custom_potential_errors_to_field(field_name)

        self.customize(customization=customization)

    def set_default_field_value(self, field_name, value):
        """
        updates the initial value of a form field,
        both on the form itself and on the ng model it is bound to
        :param field_name: name of field to update
        :param value: value to set
        :return: None
        """

        field = self.fields[field_name]
        field.initial = value

        # TODO: ANOTHER WAY TO GET INITIAL DATA FROM THE CUSTOMIZATION
        # TODO: IS TO ADD SOMETHING LIKE: "ng-init='{{form.get_initial_data|jsonify|safe}}'"
        # TODO: TO THE TEMPLATE (THE RESULT NEEDS TO BE MASSAGED A BIT TO USE QUALIFIED NAMES,
        # TODO: I'M NOT SURE WHICH APPROACH IS BETTER; FOR NOW I'M DOING IT EXPLICITLY HERE

        update_field_widget_attributes(field, {
            # notice I am calling the "init_value" fn, rather than just specifying "field_name=value" in ng-init
            # this bit of indirection ensures the property is loaded by the controller before setting its value
            # see comments in "q_ng_editor.js#init_value" for more info
            "ng-init": "init_value('{0}', {1})".format(field_name, json.dumps(value))
        })

    def validate_unique(self):
        model_realization = self.instance
        try:
            model_realization.validate_unique()
        except ValidationError as e:
            # if there is a validation error then apply that error to the individual fields
            # so it shows up in the form and is rendered nicely
            unique_together_fields_list = model_realization.get_unique_together()
            for unique_together_fields in unique_together_fields_list:
                if any(field.lower() in " ".join(e.messages).lower() for field in unique_together_fields):
                    msg = [u'An instance with this {0} already exists.'.format(
                        " / ".join([pretty_string(utf) for utf in unique_together_fields])
                        )
                    ]
                    for unique_together_field in unique_together_fields:
                        self.errors[unique_together_field] = msg

class QRealizationFormSet(QFormSet):

    def __init__(self, *args, **kwargs):
        customizations = kwargs.pop("customizations", None)
        super(QRealizationFormSet, self).__init__(*args, **kwargs)
        self.customizations = customizations

    def add_default_form_arguments(self, i):
        """
        adds realization ng-specific kwargs to the child form class
        (called by "_construct_form")
        in this case, I am adding a customization
        :param i: index of form to be constructed
        :return: kwarg dict
        """
        additional_default_form_arguments = super(QRealizationFormSet, self).add_default_form_arguments(i)
        additional_default_form_arguments.update({
            'customization': self.customizations[i]
        })
        return additional_default_form_arguments
