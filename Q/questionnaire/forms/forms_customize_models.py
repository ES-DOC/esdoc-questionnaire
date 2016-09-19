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

from Q.questionnaire.forms.forms_customize import QCustomizationForm
from Q.questionnaire.models.models_customizations import QModelCustomization
from Q.questionnaire.q_utils import set_field_widget_attributes, update_field_widget_attributes, pretty_string, serialize_model_to_dict

# TODO: I AM EXCLUDING CERTAIN FIELDS SO THAT THEY DON'T CHANGE THE NG-MODEL
# TODO: I AM DOING THIS FOR ALL QCUSTOMIZATIONFORMS
# TODO: DOUBLE-CHECK THAT THIS WORKS
# TODO: (THEY ARE PREFACED BY "##")

class QModelCustomizationForm(QCustomizationForm):

    class Meta:
        model = QModelCustomization
        fields = [
            # 'id',
            # 'guid',
            # 'created',
            # 'modified',
            'project',
            'proxy',
            'name',
            'description',
            # 'order',
            'is_default',
            'model_title',
            'model_description',
            'model_show_all_categories',
            # 'synchronization',
            # 'properties',
        ]

    _hidden_fields = ["project", "proxy"]
    _customization_fields = ["name", "description", "is_default"]
    _document_fields = ["model_title", "model_description", "model_show_all_categories"]
    _other_fields = []

    def get_hidden_fields(self):
        """
        get fields that are needed to pass to the server, but not for the user to edit
        :return:
        """
        return self.get_fields_from_list(self._hidden_fields)

    def get_customization_fields(self):
        """
        get fields that are just for the customization itself
        :return:
        """
        return self.get_fields_from_list(self._customization_fields)

    def get_document_fields(self):
        """
        get fields that pertain to the proxy
        :return:
        """
        return self.get_fields_from_list(self._document_fields)

    def get_other_fields(self):
        """
        get any fields that are leftover
        :return:
        """
        return self.get_fields_from_list(self._other_fields)

    def __init__(self, *args, **kwargs):
        super(QModelCustomizationForm, self).__init__(*args, **kwargs)

        # deal w/ customization_fields...
        self.unbootstrap_field("is_default")
        set_field_widget_attributes(self.fields["description"], {"rows": 2})

        # deal w/ document_fields...
        self.unbootstrap_field("model_show_all_categories")
        set_field_widget_attributes(self.fields["model_description"], {"rows": 2})

        # TODO: MAKE SURE THIS LINE IS NOT REPLICATED IN SUBFORMS
        update_field_widget_attributes(self.fields["name"], {
            # notice I'm using ng-blur instead of ng-change
            # ...this is much more efficient
            "ng-blur": "update_names({field_scope})".format(
                field_scope=self.get_qualified_model_field_name("name"),
            ),
        })

    def clean(self):
        # calling the parent class's clean fun automatically sets a
        # flag that forces unique (and unique_together) validation
        # (although this isn't actually used now that data is routed through the REST API)
        super(QModelCustomizationForm, self).clean()
        cleaned_data = self.cleaned_data
        return cleaned_data

    def clean_is_default(self):
        cleaned_data = self.cleaned_data
        is_default = cleaned_data.get("is_default")
        if is_default:
            this_customizer = self.instance
            other_customizers = QModelCustomization.objects.filter(
                project=cleaned_data["project"],
                proxy=cleaned_data["proxy"],
                default=True,
            )
            if this_customizer.pk:
                other_customizers = other_customizers.exclude(pk=this_customizer.pk)
            if other_customizers.count() != 0:
                raise ValidationError("A default customization already exists.  There can be only one default customization per project.")
        return is_default

class QModelCustomizationSubForm(QModelCustomizationForm):
    """
    Just like a normal QModelCustomizationForm
    except I don't display _customization_fields
    """
    pass
