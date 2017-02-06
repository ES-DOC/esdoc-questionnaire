####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.forms import ValidationError, ModelMultipleChoiceField
from django.forms.models import modelformset_factory
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
import json

from Q.questionnaire.forms.forms_base import QForm, QFormSet
from Q.questionnaire.models.models_projects import QProject, QProjectOntology
from Q.questionnaire.q_utils import set_field_widget_attributes, update_field_widget_attributes, pretty_string


class QProjectForm(QForm):
    class Meta:
        model = QProject
        fields = [
            "name",
            "title",
            "description",
            "email",
            "url",
            "ontologies",
            # "is_displayed",
            # "authenticated",
        ]

    _project_fields = ["name", "title", "description", "email", "url"]
    _hidden_fields = []
    _other_fields = []

    def __init__(self, *args, **kwargs):
        super(QProjectForm, self).__init__(*args, **kwargs)
        for field in self.fields.itervalues():
            update_field_widget_attributes(field, {"class": "form-control form-control-md"})
        set_field_widget_attributes(self.fields["name"], {"readonly": True, "ng-disabled": "true"})
        set_field_widget_attributes(self.fields["description"], {"rows": 2})
        
    @property
    def project_fields(self):
        return self.get_fields_from_list(self._project_fields)

    @property
    def hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)

    @property
    def other_fields(self):
        return self.get_fields_from_list(self._other_fields)

    def validate_unique(self):
        project = self.instance
        try:
            project.validate_unique()
        except ValidationError as e:
            # if there is a validation error then apply that error to the individual fields
            # so it shows up in the form and is rendered nicely
            unique_together_fields_list = project.get_unique_together()
            for unique_together_fields in unique_together_fields_list:
                if any(field.lower() in " ".join(e.messages).lower() for field in unique_together_fields):
                    msg = [u'An instance with this {0} already exists.'.format(
                        " / ".join([pretty_string(utf) for utf in unique_together_fields])
                    )
                    ]
                    for unique_together_field in unique_together_fields:
                        self.errors[unique_together_field] = msg

    def clean(self):
        # calling the parent class's clean fun automatically sets a
        # flag that forces unique (and unique_together) validation
        # (although this isn't actually used now that data is routed through DRF)
        super(QProjectForm, self).clean()
        cleaned_data = self.cleaned_data
        return cleaned_data
