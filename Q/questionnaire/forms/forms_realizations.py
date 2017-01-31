####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.forms import ValidationError, CharField
from Q.questionnaire.forms.forms_base import QForm, QFormSet
from Q.questionnaire.models.models_customizations import QModelCustomization, QCategoryCustomization, QPropertyCustomization
from Q.questionnaire.q_fields import QPropertyTypes
from Q.questionnaire.q_utils import QError, set_field_widget_attributes, update_field_widget_attributes, pretty_string


class QCustomizationForm(QForm):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(QCustomizationForm, self).__init__(*args, **kwargs)
        for field_name in self.fields.keys():
            self.add_custom_potential_errors_to_field(field_name)

        self.is_meta = self.instance.is_meta

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
class QCustomizationFormSet(QFormSet):
    pass

###############
# Model Forms #
###############


class QModelCustomizationForm(QCustomizationForm):

    class Meta:
        model = QModelCustomization
        # only including fields that actually get rendered
        # everything else is handled by DRF
        fields = [
            'name',
            'documentation',
            'is_default',
            'model_title',
            'model_description',
            'model_show_empty_categories',
        ]

    _hidden_fields = []
    _customization_fields = ["name", "documentation", "is_default"]
    _document_fields = ["model_title", "model_description", "model_show_empty_categories"]
    _other_fields = []

    @property
    def hidden_fields(self):
        """
        get fields that are needed to pass to the server, but not for the user to edit
        :return:
        """
        return self.get_fields_from_list(self._hidden_fields)

    @property
    def customization_fields(self):
        """
        get fields that are just for the customization itself
        :return:
        """
        return self.get_fields_from_list(self._customization_fields)

    @property
    def document_fields(self):
        """
        get fields that pertain to the proxy
        :return:
        """
        return self.get_fields_from_list(self._document_fields)

    @property
    def other_fields(self):
        """
        get any fields that are leftover
        :return:
        """
        return self.get_fields_from_list(self._other_fields)

    def __init__(self, *args, **kwargs):
        super(QModelCustomizationForm, self).__init__(*args, **kwargs)

        # deal w/ customization_fields...
        self.unbootstrap_field("is_default")
        self.add_server_errors_to_field("name")
        self.add_server_errors_to_field("is_default")
        set_field_widget_attributes(self.fields["documentation"], {"rows": 2})

        # deal w/ document_fields...
        self.unbootstrap_field("model_show_empty_categories")
        set_field_widget_attributes(self.fields["model_description"], {"rows": 2})

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
        # (although this isn't actually used now that data is routed through DRF)
        super(QModelCustomizationForm, self).clean()
        cleaned_data = self.cleaned_data
        return cleaned_data

    def clean_is_default(self):
        # as above, this isn't actually used b/c validation is routed through DRF
        cleaned_data = self.cleaned_data
        is_default = cleaned_data.get("is_default")
        if is_default:
            other_customizers = QModelCustomization.objects.filter(
                project=cleaned_data["project"],
                proxy=cleaned_data["proxy"],
                default=True,
            )
            if self.is_existing:
                other_customizers = other_customizers.exclude(pk=self.instance.pk)
            if other_customizers.count() != 0:
                raise ValidationError("A default customization already exists.  There can be only one default customization per project.")
        return is_default


class QModelCustomizationSubForm(QModelCustomizationForm):
    """
    Just like a normal QModelCustomizationForm
    except I don't display _customization_fields
    """

    _customization_fields = []


##################
# Category Forms #
##################


class QCategoryCustomizationForm(QCustomizationForm):
    class Meta:
        model = QCategoryCustomization
        fields = [
            'name',
            'category_title',
            'category_description',
            'is_hidden',
            'order',
        ]

    _hidden_fields = ["name"]
    _category_fields = ["category_title", "category_description", "is_hidden", "order"]
    _other_fields = []

    @property
    def hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)

    @property
    def category_fields(self):
        return self.get_fields_from_list(self._category_fields)

    @property
    def other_fields(self):
        return self.get_fields_from_list(self._other_fields)

    def __init__(self, *args, **kwargs):
        super(QCategoryCustomizationForm, self).__init__(*args, **kwargs)
        self.unbootstrap_field("is_hidden")
        update_field_widget_attributes(self.fields["category_title"], {"class": "form-control form-control-small"})
        update_field_widget_attributes(self.fields["category_description"], {"class": "form-control form-control-small"})
        set_field_widget_attributes(self.fields["category_description"], {"rows": 2})
        update_field_widget_attributes(self.fields["order"], {"ng-disabled": "true", "disabled": "disabled"})

##################
# Property Forms #
##################


class QPropertyCustomizationForm(QCustomizationForm):
    class Meta:
        model = QPropertyCustomization
        fields = [
            "name",
            "property_title",
            "property_description",
            "cardinality",
            "is_required",
            "is_hidden",
            "is_editable",
            "is_nillable",
            "inline_help",
            "default_values",
            "order",
            "field_type",
            "atomic_type",
            "atomic_suggestions",
            "enumeration_is_open",
            # "enumeration_choices",
            # "relationship_target_model_customizations",
            "relationship_show_subforms",
        ]

    _hidden_fields = ["name", "order", "field_type"]
    _common_fields = ["property_title", "property_description", "cardinality", "is_required", "is_hidden", "is_editable", "is_nillable", "inline_help"]
    _atomic_fields = ["atomic_type", "atomic_suggestions", "default_values"]
    _enumeration_fields = ["enumeration_is_open", "default_values"]  # "enumeration_choices"
    _relationship_fields = ["relationship_show_subforms"]
    _other_fields = []

    # cardinality is not a model field, but it exists in the serialization and I include it here just to be informative
    cardinality = CharField(label="Cardinality", required=False)

    @property
    def hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)

    @property
    def atomic_fields(self):
        return self.get_fields_from_list(self._common_fields + self._atomic_fields)

    @property
    def enumeration_fields(self):
        return self.get_fields_from_list(self._common_fields + self._enumeration_fields)

    @property
    def relationship_fields(self):
        return self.get_fields_from_list(self._common_fields + self._relationship_fields)

    @property
    def other_fields(self):
        return self.get_fields_from_list(self._other_fields)

    @property
    def fields_for_type(self):
        field_type = self.get_current_field_value("field_type")
        if field_type == QPropertyTypes.ATOMIC:
            return self.atomic_fields
        elif field_type == QPropertyTypes.ENUMERATION:
            return self.enumeration_fields
        else:  # field_type == QPropertyTypes.RELATIONSHIP
            return self.relationship_fields

    def __init__(self, *args, **kwargs):
        super(QPropertyCustomizationForm, self).__init__(*args, **kwargs)

        set_field_widget_attributes(self.fields["property_description"], {"rows": 2})
        set_field_widget_attributes(self.fields["cardinality"], {"readonly": True, "ng-disabled": "true"})
        update_field_widget_attributes(self.fields["cardinality"], {"class": "form-control-auto"})
        self.unbootstrap_fields(["inline_help", "is_required", "is_hidden", "is_editable", "is_nillable"])

        field_type = self.get_current_field_value("field_type")
        if field_type == QPropertyTypes.ATOMIC:
            update_field_widget_attributes(self.fields["atomic_type"], {"class": "select single show-tick"})
            set_field_widget_attributes(self.fields["atomic_suggestions"], {"rows": 2})
            set_field_widget_attributes(self.fields["default_values"], {"rows": 2})
        elif field_type == QPropertyTypes.ENUMERATION:
            set_field_widget_attributes(self.fields["default_values"], {"rows": 2})
            self.unbootstrap_fields(["enumeration_is_open"])
        elif field_type == QPropertyTypes.RELATIONSHIP:
            update_field_widget_attributes(self.fields["relationship_show_subforms"], {"readonly": True, "ng-disabled": "true"})
            self.unbootstrap_fields(["relationship_show_subforms"])
        else:
            msg = "Unknown field type: {0}".format(field_type)
            raise QError(msg)

        if self.instance.proxy.is_required:
            update_field_widget_attributes(self.fields["is_required"], {"readonly": True, "ng-disabled": "true"})

        if self.instance.has_specialized_values:
            update_field_widget_attributes(self.fields["default_values"], {"readonly": True, "ng-disabled": "true"})
            update_field_widget_attributes(self.fields["is_editable"], {"readonly": True, "ng-disabled": "true"})
