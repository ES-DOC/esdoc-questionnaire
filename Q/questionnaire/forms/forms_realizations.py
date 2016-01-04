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

from django.forms.models import ModelForm, BaseModelFormSet, BaseInlineFormSet
from djangular.forms import NgModelFormMixin

from Q.questionnaire.models.models_realizations import QModel

class QModelForm(NgModelFormMixin, ModelForm):

    class Meta:
        model = QModel
        fields = ("id", "guid", "created", "modified", "version", "is_document", "is_root", "is_published", )

    def __init__(self, *args, **kwargs):
        super(QModelForm, self).__init__(*args, **kwargs)

