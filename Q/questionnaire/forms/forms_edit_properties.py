###################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

from django.forms.widgets import Select, SelectMultiple
from django.forms.fields import BooleanField
from django.forms.models import modelformset_factory, ModelMultipleChoiceField
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils.functional import curry
from djangular.forms.widgets import CheckboxSelectMultiple as DjangularCheckboxSelectMultiple

from Q.questionnaire.forms.forms_edit import QRealizationForm, QRealizationFormSet
from Q.questionnaire.models.models_realizations import QProperty, QModel
from Q.questionnaire.q_fields import QPropertyTypes, ATOMIC_PROPERTY_MAP, ENUMERATION_OTHER_PLACEHOLDER_TEXT, ENUMERATION_OTHER_CHOICE, ENUMERATION_OTHER_DOCUMENTATION
from Q.questionnaire.q_utils import set_field_widget_attributes, update_field_widget_attributes, q_logger
from Q.questionnaire.q_constants import TYPEAHEAD_LIMIT

# TODO: I AM EXCLUDING CERTAIN FIELDS SO THAT THEY DON'T CHANGE THE NG-MODEL
# TODO: I AM DOING THIS FOR ALL QREALIZATIONS
# TODO: DOUBLE-CHECK THAT THIS WORKS
# TODO: (THEY ARE PREFACED BY "##")

class QPropertyRealizationForm(QRealizationForm):

    class Meta:
        model = QProperty
        fields = [
            # 'id',
            # 'guid',
            # 'created',
            # 'modified',
            'proxy',
            'name',
            'order',
            'field_type',
            # 'cardinality',
            'atomic_value',
            'enumeration_value',
            'enumeration_other_value',
            'relationship_values',
            'is_nil',
            'nil_reason',
            'is_complete',
            'is_required',
        ]

    _hidden_fields = ["proxy", "name", "order", "field_type", ]  # "cardinality", "is_complete", "is_required", ]
    _atomic_fields = ["atomic_value", "is_nil", "nil_reason", ]
    _enumeration_fields = ["enumeration_value", "enumeration_other_value", "is_nil", "nil_reason", ]
    _relationship_fields = ["relationship_values", "is_nil", "nil_reason", ]
    _other_fields = []

    # this is a reverse field, so I need to define it explicitly here
    relationship_values = ModelMultipleChoiceField(queryset=QModel.objects.none())

    # this is a computed field; it is not part of the underlying QPropertyRealization
    # however, it is also computed on the QPropertyRealizationSerializer (based on the proxy during the "reset" fn)
    # and can be overwritten in this form during the "customize" fn
    is_required = BooleanField(required=False, label="Is required")

    def get_hidden_fields(self):
        """
        get fields that are needed to pass to the server, but no
        :return:
        """
        return self.get_fields_from_list(self._hidden_fields)

    def get_atomic_fields(self):
        return self.get_fields_from_list(self._atomic_fields)

    def get_enumeration_fields(self):
        return self.get_fields_from_list(self._enumeration_fields)

    def get_relationship_fields(self):
        return self.get_fields_from_list(self._relationship_fields)

    def get_other_fields(self):
        """
        get any fields that are leftover
        :return:
        """
        return self.get_fields_from_list(self._other_fields)

    # '__init__' takes care of fine-tuning form fields based on general Q logic
    # while 'customize' takes care of fine-tuning form fields based on settings from the corresponding customization

    def __init__(self, *args, **kwargs):
        super(QPropertyRealizationForm, self).__init__(*args, **kwargs)

        is_nil_field = self.fields["is_nil"]
        self.unbootstrap_field("is_nil")
        is_nil_field.help_text = mark_safe(_(
            "<p>Some properties can be intentionally left blank, provided there is a valid reason for doing so.</p>"
            "<p>Checking this box will reveal a drop-down menu allowing a reason to be specified.</p>"
            "<p>If a reason is specified, then any value on the left will be ignored during publication.</p>"))

        # nil_reason_field = self.fields["nil_reason"]
        # nil_reason_field.label = mark_safe(_(
        #     "Why is there no value for this property?"
        # ))
        # nil_reason_field.widget = RadioSelect(choices=nil_reason_field.choices)
        # update_field_widget_attributes(nil_reason_field, {
        #     "class": "form-control-auto"
        # })

        proxy = self.instance.proxy
        field_type = self.get_current_field_value("field_type")

        if field_type == QPropertyTypes.ATOMIC:
            # I was under the impression that b/c QForm form inherits from Bootstrap3ModelForm,
            # all fields would automatically have class="form-control" set
            # (it seems to be the case for customization forms)
            # but, apparently, I was mistaken so I do it explicitly here
            update_field_widget_attributes(self.fields["atomic_value"], {
                "class": "form-control",
            })

        elif field_type == QPropertyTypes.ENUMERATION:
            ### I AM RIGHT HERE JUST BEFORE SPEAKING TO SYLVIA
            ### THIS IS OVERWRITING WHAT CUSTOMIZE HAD SET
            ### HUH? WHY IS CUSTOMIZE RUNNING BEFORE __INIT__ ?!?
            # import ipdb; ipdb.set_trace()
            enumeration_value_field = self.fields["enumeration_value"]
            enumeration_value_field.set_complete_choices(proxy.enumeration)
            enumeration_value_field.set_cardinality(proxy.get_cardinality_min(), proxy.get_cardinality_max())

            enumeration_value_field.add_complete_choice(ENUMERATION_OTHER_CHOICE, documentation=ENUMERATION_OTHER_DOCUMENTATION)

    def customize(self, customization=None):
        if not customization:
            realization = self.instance
            customization = realization.get_default_customization()
        assert(customization.proxy == self.instance.proxy)

        value_field = self.get_value_field()
        field_type = self.get_current_field_value("field_type")
        is_new = self.is_new()

        # customize stuff...
        self.is_hidden = customization.is_hidden
        self.inline_help = customization.inline_help
        self.is_nillable = customization.is_nillable
        self.is_required = customization.is_required
        self.set_default_field_value("is_required", self.is_required)

        if field_type == QPropertyTypes.ATOMIC:
            atomic_type = customization.atomic_type

            update_field_widget_attributes(value_field, {
                "class": atomic_type.lower(),
            })

            atomic_widget_class = ATOMIC_PROPERTY_MAP[atomic_type][0]
            atomic_widget_args = ATOMIC_PROPERTY_MAP[atomic_type][1]
            value_field.widget = atomic_widget_class(**atomic_widget_args)

            if is_new:
                atomic_default = customization.atomic_default
                if atomic_default:
                    self.set_default_field_value("atomic_value", atomic_default)
                    self.set_default_field_value("is_complete", True)

            atomic_suggestions = customization.atomic_suggestions.split('|')
            if atomic_suggestions:
                set_field_widget_attributes(value_field, {
                    "uib-typeahead": "option for option in [{0}] | filter:$viewValue | limitTo:{1}".format(
                        ",".join(["'{0}'".format(mark_safe(suggestion)) for suggestion in atomic_suggestions]),
                        TYPEAHEAD_LIMIT
                    )
                })

            if atomic_type == 'DATETIME':
                msg = "dealing w/ a datetime... beware"
                q_logger.warn(msg)
                pass

            if self.is_required:
                update_field_widget_attributes(value_field, {
                    "ng-blur": "update_property_completion()",  # ng-blur waits until focus is lost (rather than firing for every single in-progress change)
                })
            else:
                self.set_default_field_value("is_complete", True)


        elif field_type == QPropertyTypes.ENUMERATION:
            enumeration_value_field = self.fields["enumeration_value"]
            enumeration_other_value_field = self.fields["enumeration_other_value"]
            if customization.enumeration_open:
                enumeration_value_field.add_complete_choice(ENUMERATION_OTHER_CHOICE, documentation=ENUMERATION_OTHER_DOCUMENTATION)
            # bootstrap will make sure that this widget behaves appropriately
            # depending on whether it is really "multiple" or not
            enumeration_value_field.widget = DjangularCheckboxSelectMultiple(choices=enumeration_value_field.choices)
            # if enumeration_value_field.is_multiple:
            #     enumeration_value_field.widget = SelectMultiple(choices=enumeration_value_field.choices)
            # else:
            #     enumeration_value_field.widget = Select(choices=enumeration_value_field.choices)

            set_field_widget_attributes(enumeration_other_value_field, {
                "placeholder": ENUMERATION_OTHER_PLACEHOLDER_TEXT,
                "ng-show": "value_in_array('{0}', current_model.enumeration_value)".format(ENUMERATION_OTHER_CHOICE[0]),
            })
            update_field_widget_attributes(enumeration_other_value_field, {
                "ng-disabled": "current_model.is_nil"
            })

            if self.is_required:
                update_field_widget_attributes(enumeration_value_field, {
                    "ng-blur": "update_property_completion()",
                })
                update_field_widget_attributes(enumeration_other_value_field, {
                    "ng-blur": "update_property_completion()",
                })
            else:
                self.set_default_field_value("is_complete", True)


        else:  # field_type == QPropertyTypes.RELATIONSHIP
            self.use_subforms = customization.use_subforms()
            self.use_references = customization.use_references()
            if not self.is_required:
                self.set_default_field_value("is_complete", True)

        value_field.help_text = customization.documentation
        value_field.label = customization.property_title
        value_field.required = customization.is_required
        if not customization.is_editable:
            update_field_widget_attributes(value_field, {
                "ng-disabled": "true",
                "readonly": "readonly",
            })
            update_field_widget_attributes(self.fields["is_nil"], {
                "ng-disabled": "true",
                "readonly": "readonly",
            })
            update_field_widget_attributes(self.fields["nil_reason"], {
                "ng-disabled": "true",
                "readonly": "readonly",
            })
        update_field_widget_attributes(value_field, {
            "ng-disabled": "current_model.is_nil"
        })

        self.customization = customization

    def clean(self):
        # calling the parent class's clean fun automatically sets a
        # flag that forces unique (and unique_together) validation
        # (although this isn't actually used now that data is routed through the REST API)
        super(QPropertyRealizationForm, self).clean()
        cleaned_data = self.cleaned_data
        return cleaned_data

    def get_field_type(self):
        return self.get_current_field_value("field_type")

    def get_value_field(self):
        field_type = self.get_field_type()
        if field_type == QPropertyTypes.ATOMIC:
            return self.fields["atomic_value"]
        elif field_type == QPropertyTypes.ENUMERATION:
            return self.fields["enumeration_value"]
        else:  # field_type == QPropertyTypes.RELATIONSHIP
            return self.fields["relationship_values"]

    # TODO: HAVING TO USE THIS FN SUCKS
    # TODO: I DO NOT LIKE IT
    # TODO: I NEED TO COME UP W/ A BETTER WAY TO HANDLE A POTENTIALLY CUSTOMIZED ORDER
    def get_serialized_order(self):
        # the forms in a formset might be rendered in a different order than the natural order of the underlying qs
        # this fn returns the natural order (corresponding to the order of the serialized objects)
        order = self.get_current_field_value("order")
        return order - 1

    def is_multiple(self):
        return self.instance.is_multiple()

    def is_single(self):
        return self.instance.is_single()


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
            # but b/c a local ng controller is created for each form in the formset, that property is actually bound to "current_model"
            # so I reset the scope_prefix here
            'scope_prefix': "current_model",
        })
        return additional_default_form_arguments


def QPropertyRealizationFormSetFactory(*args, **kwargs):

    # even though this is a formset and not an inline_formset,
    # I still pass "instance" instead of "queryset"
    # b/c at the time of calling this factory it is hard to work out which field of instance will return the qs
    # and, anyway, doing it explicitly here allows me to use a custom manager
    instance = kwargs.pop("instance")
    queryset = instance.properties(manager="allow_unsaved_properties_manager").all()

    scope_prefix = kwargs.pop("scope_prefix", None)
    formset_name = kwargs.pop("formset_name", None)
    prefix = kwargs.pop("prefix", formset_name)

    kwargs.update({
        "can_delete": False,
        "can_order": False,
        "extra": kwargs.pop("extra", 0),
        "form": QPropertyRealizationForm,
        "formset": QPropertyRealizationFormSet,
    })
    formset = modelformset_factory(QProperty, **kwargs)
    formset.formset_name = formset_name
    formset.scope_prefix = scope_prefix

    # TODO: IS THE REALLY THE BEST WAY TO DEAL W/ THE ORDER OF PROPERTIES?
    # TODO: IT SEEMS INEFFICIENT (PLUS IT'S BEING DONE OUTSIDE OF THE "customize" FN)
    customizations = instance.get_default_customization().property_customizations.all()
    customized_proxy_order = list(customizations.values_list("proxy", flat=True))
    ordered_queryset = sorted(
        queryset,
        key=lambda p: customized_proxy_order.index(p.proxy.pk)
    )

    # property_customizations = instance.get_customization().property_customizations.all()
    # formset.form = staticmethod(curry(QPropertyRealizationForm, customizations=property_customizations))

    return formset(
        prefix=prefix,
        queryset=ordered_queryset,
        customizations=customizations,
    )
