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
import copy

from Q.questionnaire.forms.forms_base import QForm, QFormSet
from Q.questionnaire.models.models_realizations import QModelRealization, QCategoryRealization, QPropertyRealization
from Q.questionnaire.q_fields import QPropertyTypes, ATOMIC_PROPERTY_MAP, ENUMERATION_OTHER_CHOICE, ENUMERATION_OTHER_PLACEHOLDER, ENUMERATION_OTHER_DOCUMENTATION
from Q.questionnaire.q_utils import QError, set_field_widget_attributes, update_field_widget_attributes, pretty_string, legacy_code
from Q.questionnaire.q_constants import TYPEAHEAD_LIMIT


class QRealizationForm(QForm):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        customization = kwargs.pop("customization", None)
        super(QRealizationForm, self).__init__(*args, **kwargs)
        for field_name in self.fields.keys():
            self.add_custom_potential_errors_to_field(field_name)

        realization = self.instance
        self.is_meta = realization.is_meta
        if customization is None:
            customization = realization.get_default_customization()
        self.customize(customization)

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
            # this bit of indirection ensures the value is not set before the controller has a chance to load the underlying model
            # see comments in "q_ng_editor.js#init_value" for more info
            "ng-init": "init_value('{0}', {1})".format(field_name, json.dumps(value))
        })

    # TODO: HAVING TO USE THIS FN SUCKS AND I DO NOT LIKE IT
    # TODO: I NEED TO COME UP W/ A BETTER WAY TO HANDLE A POTENTIALLY CUSTOMIZED ORDER
    # TODO: HOORAY - I CAME UP W/ A BETTER WAY... JUST SET "order" EXPLICITLY IN "get_new_realizations"
    @legacy_code
    def get_serialized_order(self):
        # the forms in a formset might be rendered in a different order than the natural order of the underlying qs
        # this fn returns the natural order (corresponding to the order of the serialized objects)
        order = self.get_current_field_value("order")
        return order - 1

    def customize(self, customization):
        msg = "{0} must define a custom 'customize' method.".format(self.__class__.__name__)
        raise NotImplementedError(msg)


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

        # TODO: I HAVE ABSOLUTELY NO IDEA WHY I CAN'T JUST CALL "self.customizations[i]"
        # TODO: AND, IN FACT, I COULD DO JUST THAT PRIOR TO WORKING W/ OPTIONAL HIERARCHICAL RELATIONSHIP PROPERTIES
        # TODO: I PASS "customizations" IN THE FORMSETFACTORY IN THE CORRECT ORDER AND I ENSURE THAT THE FORMSET QUERYSET IS IN THAT SAME ORDER
        # TODO: HOWEVER, IN THIS FN, IF i TRY TO CALL "[0]" I DON'T CONSISTENTLY GET THE 0th OBJECT IN THE QUERYSET ?!?
        # additional_default_form_arguments.update({
        #     'customization': self.customizations[i]
        # })
        for customization_order, customization in enumerate(self.customizations):
            if i == customization_order:
                additional_default_form_arguments.update({
                    "customization": customization
                })
                break

        return additional_default_form_arguments

###############
# Model Forms #
###############


class QModelRealizationForm(QRealizationForm):

    class Meta:
        model = QModelRealization
        fields = [
            "order"
        ]

    _hidden_fields = ["order"]
    _model_fields = []
    _other_fields = []

    # yep, that's correct, there are ALMOST NO fields used by this form...
    # (that may change, so the infrastructure is still here just in case)

    # I can still access customizable attributes of a CIM Model by referencing "form.customization" in the template
    # (this is the right approach; the attributes are used in the UI but are not part of a QModelRealization

    @property
    def hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)

    @property
    def model_fields(self):
        return self.get_fields_from_list(self._model_fields)

    @property
    def other_fields(self):
        return self.get_fields_from_list(self._other_fields)

    def clean(self):
        # calling the parent class's clean fun automatically sets a
        # flag that forces unique (and unique_together) validation
        # (although this isn't actually used now that data is routed through DRF)
        super(QModelRealizationForm, self).clean()
        cleaned_data = self.cleaned_data
        return cleaned_data

    # '__init__' takes care of fine-tuning form fields based on general Q logic
    # while 'customize' takes care of fine-tuning form fields based on settings from the corresponding customization

    def __init__(self, *args, **kwargs):
        super(QModelRealizationForm, self).__init__(*args, **kwargs)

    def customize(self, customization):
        proxy = self.instance.proxy
        assert customization.proxy == proxy, "in QModelRealizationForm, customization.proxy doesn't equal instance.proxy"

        self.customization = customization

##################
# Category Forms #
##################


class QCategoryRealizationForm(QRealizationForm):

    class Meta:
        model = QCategoryRealization
        fields = [
            'is_complete',
            'order',
            'category_value',
        ]

    _hidden_fields = ["is_complete", "order"]
    _category_fields = ["category_value"]
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
        super(QCategoryRealizationForm, self).__init__(*args, **kwargs)

    def clean(self):
        # calling the parent class's clean fun automatically sets a
        # flag that forces unique (and unique_together) validation
        # (although this isn't actually used now that data is routed through DRF)
        super(QCategoryRealizationForm, self).clean()
        cleaned_data = self.cleaned_data
        return cleaned_data

    # '__init__' takes care of fine-tuning form fields based on general Q logic
    # while 'customize' takes care of fine-tuning form fields based on settings from the corresponding customization

    def __init__(self, *args, **kwargs):
        super(QCategoryRealizationForm, self).__init__(*args, **kwargs)
        # TODO: SHOULD THIS BE DEFERRED FROM DJANGO TO NG?  IT IS GUI LOGIC, BUT STILL THIS SEEMS KIND OF MESSY
        # TODO: (ONE REASON NOT TO MOVE IT TO NG IS THAT I WANT TO CHECK IF I SHOULD RENDER A CATEGORY/PROPERTY _BEFORE_ I DEFINE THE CORRESPONDING NG CONTROLLER)
        self.properties_keys = self.instance.get_properties_keys()
        self.category_key = self.instance.key

    def customize(self, customization):

        proxy = self.instance.proxy
        assert customization.proxy == proxy, "in QCategoryRealizationForm, customization.proxy doesn't equal instance.proxy"

        # customize form...
        self.is_hidden = customization.is_hidden

        # customize fields...
        category_field = self.fields["category_value"]
        category_field.label = customization.category_title
        category_field.help_text = customization.category_description


class QCategoryRealizationFormSet(QRealizationFormSet):
    def add_default_form_arguments(self, i):
        """
        adds property realization ng-specific kwargs to the child form class
        (called by "_construct_form")
        in this case, I am changing the scope_prefix
        :param i: index of form to be constructed
        :return: kwarg dict
        """
        additional_default_form_arguments = super(QCategoryRealizationFormSet, self).add_default_form_arguments(i)

        additional_default_form_arguments.update({
            # this may seem counter-intuitive; you would expect scope_prefix to be something like "current_model.properties[i]"
            # but b/c a local ng controller is created for _each_ form in the formset, that property is actually bound to a JavaScript variable called "current_model"
            # so I reset the scope_prefix here accordingly...
            'scope_prefix': "current_model",
        })
        return additional_default_form_arguments


def QCategoryRealizationFormSetFactory(*args, **kwargs):

    # even though this is a formset and not an inline_formset, I still pass "instance" instead of "queryset"
    instance = kwargs.pop("instance")
    queryset = instance.categories(manager="allow_unsaved_categories_manager").all()

    formset_name = kwargs.pop("name", None)
    scope_prefix = kwargs.pop("scope_prefix", None)
    prefix = kwargs.pop("prefix", formset_name)

    kwargs.update({
        "can_delete": False,
        "can_order": False,
        "extra": kwargs.pop("extra", 0),
        "form": QCategoryRealizationForm,
        "formset": QCategoryRealizationFormSet,
    })
    formset = modelformset_factory(QCategoryRealization, **kwargs)
    formset.formset_name = formset_name
    formset.scope_prefix = scope_prefix

    customizations = instance.get_default_customization().category_customizations.all()
    customized_proxy_order = list(customizations.values_list("proxy", flat=True))
    ordered_queryset = sorted(
        queryset,
        key=lambda p: customized_proxy_order.index(p.proxy.pk)
    )

    return formset(
        prefix=prefix,
        queryset=ordered_queryset,
        customizations=customizations,
    )


##################
# Property Forms #
##################


class QPropertyRealizationForm(QRealizationForm):

    class Meta:
        model = QPropertyRealization
        fields = [
            'is_complete',
            'order',
            'field_type',
            'is_nil',
            'nil_reason',
            'atomic_value',
            'enumeration_value',
            'enumeration_other_value',
            'relationship_values',
            'relationship_references',
        ]

    # this is a reverse field, so I need to define it explicitly here
    relationship_values = ModelMultipleChoiceField(queryset=QModelRealization.objects.none())

    _hidden_fields = ["is_complete", "field_type", "order"]
    _atomic_fields = ["is_nil", "nil_reason", "atomic_value"]
    _enumeration_fields = ["is_nil", "nil_reason", "enumeration_value", "enumeration_other_value"]
    _relationship_fields = ["is_nil", "nil_reason", "relationship_values", "relationship_references"]
    _other_fields = []

    @property
    def hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)

    @property
    def atomic_fields(self):
        return self.get_fields_from_list(self._atomic_fields)

    @property
    def enumeration_fields(self):
        return self.get_fields_from_list(self._enumeration_fields)

    @property
    def relationship_fields(self):
        return self.get_fields_from_list(self._relationship_fields)

    @property
    def other_fields(self):
        return self.get_fields_from_list(self._other_fields)

    def __init__(self, *args, **kwargs):
        super(QModelRealizationForm, self).__init__(*args, **kwargs)

    def clean(self):
        # calling the parent class's clean fun automatically sets a
        # flag that forces unique (and unique_together) validation
        # (although this isn't actually used now that data is routed through DRF)
        super(QModelRealizationForm, self).clean()
        cleaned_data = self.cleaned_data
        return cleaned_data

    def get_field_type(self):
        return self.get_current_field_value("field_type")

    @property
    def value_field(self):
        field_type = self.get_field_type()
        if field_type == QPropertyTypes.ATOMIC:
            return self.fields["atomic_value"]
        elif field_type == QPropertyTypes.ENUMERATION:
            return self.fields["enumeration_value"]
        else:  # field_type == QPropertyTypes.RELATIONSHIP
            return self.fields["relationship_values"]

    # '__init__' takes care of fine-tuning form fields based on general Q logic
    # while 'customize' takes care of fine-tuning form fields based on settings from the corresponding customization

    def __init__(self, *args, **kwargs):
        super(QPropertyRealizationForm, self).__init__(*args, **kwargs)

        field_type = self.get_current_field_value("field_type")
        proxy = self.instance.proxy

        is_nil_field = self.fields["is_nil"]
        self.unbootstrap_field("is_nil")
        is_nil_field.help_text = mark_safe(
            _(
                "<p>Some properties can be intentionally left blank, provided there is a valid reason for doing so.</p>"
                "<p>Checking this box will reveal a drop-down menu allowing a reason to be specified.</p>"
                "<p>If a reason is specified, then any value on the left will be ignored during publication.</p>"
            )
        )

        if field_type == QPropertyTypes.ATOMIC:
            atomic_value_field = self.fields["atomic_value"]
            set_field_widget_attributes(atomic_value_field, {
                "ng-disabled": "current_model.is_nil"
            })

        elif field_type == QPropertyTypes.ENUMERATION:
            enumeration_value_field = self.fields["enumeration_value"]
            enumeration_other_field = self.fields["enumeration_other_value"]
            # TODO: "complete_choices", "is_multiple", etc. OUGHT TO HAVE BEEN SETUP IN "QPropertyRealization.__init__"
            # TODO: BUT NOT ALL OF THOSE ATTRIBUTES RETAIN THE VALUES SETUP THERE; I'M NOT SURE WHY ?!?
            # TODO: THIS SECTION JUST REPEATS THAT CODE ALMOST VERBATIM FOR THE QEnumerationFormField...
            enumeration_choices = copy.copy(proxy.enumeration_choices)  # make a copy of the value so that "update" below doesn't modify the original
            if proxy.enumeration_is_open:
                enumeration_choices.append({
                    "value": ENUMERATION_OTHER_CHOICE,
                    "documentation": ENUMERATION_OTHER_DOCUMENTATION,
                    "order": len(enumeration_choices) + 1,
                })
            enumeration_value_field._complete_choices = enumeration_choices
            enumeration_value_field._is_multiple = proxy.is_multiple
            set_field_widget_attributes(enumeration_other_field, {
                "placeholder": ENUMERATION_OTHER_PLACEHOLDER,
                "ng-show": "value_in_array('{0}', current_model.enumeration_value)".format(ENUMERATION_OTHER_CHOICE)
            })
            set_field_widget_attributes(enumeration_value_field, {
                "ng-disabled": "current_model.is_nil"
            })
            set_field_widget_attributes(enumeration_other_field, {
                "ng-disabled": "current_model.is_nil"
            })

        else:  # field_type == QPropertyTypes.RELATIONSHIP:
            pass

        self.is_multiple = proxy.is_multiple
        # TODO: SHOULD THIS BE DEFERRED FROM DJANGO TO NG?  IT IS GUI LOGIC, BUT STILL THIS SEEMS KIND OF MESSY
        # TODO: (ONE REASON NOT TO MOVE IT TO NG IS THAT I WANT TO CHECK IF I SHOULD RENDER A CATEGORY/PROPERTY _BEFORE_ I DEFINE THE CORRESPONDING NG CONTROLLER)
        self.category_key = self.instance.category_key
        self.property_key = self.instance.key

    def customize(self, customization):

        field_type = self.get_current_field_value("field_type")
        proxy = self.instance.proxy
        assert customization.proxy == proxy, "in QPropertyRealizationForm, customization.proxy doesn't equal instance.proxy"

        # customize form...
        self.inline_help = customization.inline_help
        self.is_nillable = customization.is_nillable
        self.is_required = customization.is_required
        self.is_hidden = customization.is_hidden
        self.is_editable = customization.is_editable
        self.is_hierarchical = customization.relationship_is_hierarchical
        self.render = not (self.is_hidden or self.is_hierarchical)  # tells the template whether or not I plan on rendering the form

        # customize fields...
        self.value_field.help_text = customization.property_description
        self.value_field.label = customization.property_title
        self.value_field.required = customization.is_required
        self.value_field.editable = customization.is_editable

        if not customization.is_editable:
            set_field_widget_attributes(self.value_field, {
                "ng-disabled": "true",
                "readonly": "readonly",
            })
            set_field_widget_attributes(self.fields["is_nil"], {
                "ng-disabled": "true",
                "readonly": "readonly",
            })
            set_field_widget_attributes(self.fields["nil_reason"], {
                "ng-disabled": "true",
                "readonly": "readonly",
            })

        # more in-depth customization...

        if field_type == QPropertyTypes.ATOMIC:
            atomic_value_field = self.fields["atomic_value"]
            existing_widget_attrs = atomic_value_field.widget.attrs
            custom_widget_class, custom_widget_args = ATOMIC_PROPERTY_MAP[customization.atomic_type]
            atomic_value_field.widget = custom_widget_class(custom_widget_args)
            update_field_widget_attributes(atomic_value_field, existing_widget_attrs)
            if self.instance.is_new:
                default_values = customization.default_values
                if default_values:
                    # TODO: WILL NEED TO REWRITE THIS TO COPE W/ "cardinality_max" > 1 FOR ATOMIC FIELDS
                    # TODO: (IN THAT CASE, I SHOULD PROBABLY MAKE "atomic_value" A QJSONField
                    assert len(default_values) == 1, "need to rewrite this to cope w/ 'cardinality_max' > 1 for atomic fields"
                    self.set_default_field_value("atomic_value", default_values[0])
                    self.set_default_field_value("is_complete", True)
                if customization.is_required:
                    update_field_widget_attributes(atomic_value_field, {
                        "ng-blur": "update_property_completion()",
                    })
                else:
                    self.set_default_field_value("is_complete", True)

            if customization.atomic_suggestions:
                atomic_suggestions_list = customization.atomic_suggestions.split('|')
                set_field_widget_attributes(atomic_value_field, {
                    "uib-typeahead": "option for option in [{0}] | filter:$viewValue | limitTo:{1}".format(
                        ",".join(["'{0}'".format(mark_safe(suggestion)) for suggestion in atomic_suggestions_list]),
                        TYPEAHEAD_LIMIT
                    )
                })

        elif field_type == QPropertyTypes.ENUMERATION:
            enumeration_value_field = self.fields["enumeration_value"]
            enumeration_other_value_field = self.fields["enumeration_other_value"]
            if customization.is_required:
                update_field_widget_attributes(enumeration_value_field, {
                    "ng-blur": "update_property_completion()",
                })
                update_field_widget_attributes(enumeration_other_value_field, {
                    "ng-blur": "update_property_completion()",
                })
            else:
                self.set_default_field_value("is_complete", True)
                update_field_widget_attributes(enumeration_other_value_field, {
                    "ng-blur": "update_property_completion()",
                })

        else:  # field_type == QPropertyTypes.RELATIONSHIP
            if not customization.relationship_is_hierarchical:
                # only have to render non-hierarchical relationships in a property form...
                self.use_subforms = customization.use_subforms
                self.use_references = customization.use_references
                self.cardinality_min = customization.cardinality_min
                self.cardinality_max = customization.cardinality_max
            if not customization.is_required:
                self.set_default_field_value("is_complete", True)

        self.customization = customization


class QPropertyRealizationFormSet(QRealizationFormSet):

    def add_default_form_arguments(self, i):
        """
        adds property realization ng-specific kwargs to the child form class
        (called by "_construct_form")
        in this case, I am changing the scope_prefix
        :param i: index of form to be constructed
        :return: kwarg dict
        """
        additional_default_form_arguments = super(QPropertyRealizationFormSet, self).add_default_form_arguments(i)

        additional_default_form_arguments.update({
            # this may seem counter-intuitive; you would expect scope_prefix to be something like "current_model.properties[i]"
            # but b/c a local ng controller is created for _each_ form in the formset, that property is actually bound to a JavaScript variable called "current_model"
            # so I reset the scope_prefix here accordingly...
            'scope_prefix': "current_model",
        })
        return additional_default_form_arguments


def QPropertyRealizationFormSetFactory(*args, **kwargs):
    # even though this is a formset and not an inline_formset, I still pass "instance" instead of "queryset"
    instance = kwargs.pop("instance")
    # TODO: I SHOULD ONLY DEAL W/ NON-HIERARCHICAL PROPERTIES; BUT THIS WILL MESS UP THE INDEXING FOR THE ng-model ATTRIBUTE...
    # queryset = instance.properties(manager="allow_unsaved_properties_manager").filter_potentially_unsaved(is_hierarchical=False)
    queryset = instance.properties(manager="allow_unsaved_properties_manager").all()

    formset_name = kwargs.pop("name", None)
    scope_prefix = kwargs.pop("scope_prefix", None)
    prefix = kwargs.pop("prefix", formset_name)

    kwargs.update({
        "can_delete": False,
        "can_order": False,
        "extra": kwargs.pop("extra", 0),
        "form": QPropertyRealizationForm,
        "formset": QPropertyRealizationFormSet,
    })
    formset = modelformset_factory(QPropertyRealization, **kwargs)
    formset.formset_name = formset_name
    formset.scope_prefix = scope_prefix

    # TODO: I SHOULD ONLY DEAL W/ NON-HIERARCHICAL PROPERTIES; BUT THIS WILL MESS UP THE INDEXING FOR THE ng-model ATTRIBUTE...
    # customizations = instance.get_default_customization().property_customizations.filter(relationship_is_hierarchical=False)
    customizations = instance.get_default_customization().property_customizations.all()
    customized_proxy_order = list(customizations.values_list("proxy", flat=True))
    ordered_queryset = sorted(
        queryset,
        key=lambda p: customized_proxy_order.index(p.proxy.pk)
    )

    return formset(
        prefix=prefix,
        queryset=ordered_queryset,
        customizations=customizations,
    )
