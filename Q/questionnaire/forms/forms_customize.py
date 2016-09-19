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

from Q.questionnaire.forms.forms_base import QForm
from Q.questionnaire.q_utils import set_field_widget_attributes, update_field_widget_attributes, pretty_string


class QCustomizationForm(QForm):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(QCustomizationForm, self).__init__(*args, **kwargs)
        for field_name in self.fields.keys():
            # TODO: 'add_custom_potential_errors_to_field' CHECKS IF THESE ARE "REAL"
            # TODO: (ie: PART OF THE MODEL AND NOT FORM-ONLY) FIELDS; IT MIGHT BE BETTER TO
            # TODO: DO THAT CHECK HERE AND SAVE EFFORT
            self.add_custom_potential_errors_to_field(field_name)

    def validate_unique(self):
        model_customization = self.instance
        try:
            model_customization.validate_unique()
        except ValidationError as e:
            # if there is a validation error then apply that error to the individual fields
            # so it shows up in the form and is rendered nicely
            unique_together_fields_list = model_customization.get_unique_together()
            for unique_together_fields in unique_together_fields_list:
                if any(field.lower() in " ".join(e.messages).lower() for field in unique_together_fields):
                    msg = [u'An instance with this {0} already exists.'.format(
                        " / ".join([pretty_string(utf) for utf in unique_together_fields])
                        )
                    ]
                    for unique_together_field in unique_together_fields:
                        self.errors[unique_together_field] = msg

# FORMSETS ARE NO LONGER BEING USED... HOORAY!
# class QCustomizationFormSet(QFormSet):
#     pass

