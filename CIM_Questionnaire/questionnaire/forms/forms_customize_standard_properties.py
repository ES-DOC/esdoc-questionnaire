####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2014 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"
__date__ = "Dec 01, 2014 3:00:00 PM"

"""
.. module:: forms_customize_standard_properties

forms for customizing standard_properties

"""

import time
from django.forms import CharField, ChoiceField, TextInput
from django.forms.models import inlineformset_factory
from django.utils.functional import curry

from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataModelCustomizer, MetadataStandardCategoryCustomizer, MetadataStandardPropertyCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataStandardPropertyProxy
from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes, MultipleSelectWidget, SingleSelectWidget, EMPTY_CHOICE
from CIM_Questionnaire.questionnaire.forms.forms_customize import MetadataCustomizerForm, MetadataCustomizerInlineFormSet
from CIM_Questionnaire.questionnaire.utils import find_in_sequence, get_initial_data, QuestionnaireError
from CIM_Questionnaire.questionnaire.utils import set_field_widget_attributes, update_field_widget_attributes, model_to_data, get_data_from_form, get_data_from_formset


def create_standard_property_customizer_form_data(model_customizer, standard_property_customizer):

    standard_property_customizer_form_data = get_initial_data(standard_property_customizer,{
        "last_modified": time.strftime("%c"),
    })

    field_type = standard_property_customizer_form_data["field_type"]

    if field_type == MetadataFieldTypes.ATOMIC:
        pass

    elif field_type == MetadataFieldTypes.ENUMERATION:
        current_enumeration_choices = standard_property_customizer_form_data["enumeration_choices"]
        current_enumeration_default = standard_property_customizer_form_data["enumeration_default"]
        if current_enumeration_choices:
            standard_property_customizer_form_data["enumeration_choices"] = current_enumeration_choices.split("|")
        if current_enumeration_default:
            standard_property_customizer_form_data["enumeration_default"] = current_enumeration_default.split("|")

        # BE AWARE THAT CHECKING THIS DICT ITEM (WHOSE VALUE AS A LIST) WON'T GIVE THE FULL LIST
        # APPARENTLY, THIS IS A "FEATURE" AND NOT A "BUG" [https://code.djangoproject.com/ticket/1130]

    elif field_type == MetadataFieldTypes.RELATIONSHIP:
        pass

    else:
        msg = "invalid field type for standard property: '%s'" % field_type
        raise QuestionnaireError(msg)

    standard_category = standard_property_customizer.category
    if standard_category:
        standard_property_customizer_form_data["category"] = standard_category.key
        standard_property_customizer_form_data["category_name"] = standard_category.name

    return standard_property_customizer_form_data


class MetadataStandardPropertyCustomizerForm(MetadataCustomizerForm):

    class Meta:
        model = MetadataStandardPropertyCustomizer
        fields = [
            # hidden fields...
            "proxy", "category", "subform_customizer",
            # header fields...
            "name", "category_name", "order", "field_type",
            # common fields...
            "displayed", "required", "editable", "unique", "verbose_name", "documentation", "inline_help", "inherited",
            # atomic fields...
            "atomic_type",  "default_value", "suggestions",
            # enumeration fields...
            "enumeration_choices", "enumeration_default", "enumeration_open", "enumeration_multi", "enumeration_nullable",
            # relationship fields...
            "relationship_cardinality", "relationship_show_subform",
            ]

    category_name = CharField(label="Category", required=False)
    category = ChoiceField(required=False)

    _hidden_fields = ("proxy", "category", "subform_customizer", )
    _header_fields = ("name", "category_name", "field_type", "order", )
    _common_fields = ("displayed", "required", "editable", "unique", "verbose_name", "documentation", "inline_help", "inherited", )
    _atomic_fields = ("atomic_type", "default_value", "suggestions", )
    _enumeration_fields = ("enumeration_choices", "enumeration_default", "enumeration_open", "enumeration_multi", "enumeration_nullable", )
    _relationship_fields = ("relationship_cardinality", "relationship_show_subform", )

    # set of fields that will be the same for all members of a formset;
    # thus I can cache the query (for relationship fields)
    cached_fields = []

    def get_hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)

    def get_header_fields(self):
        return self.get_fields_from_list(self._header_fields)

    def get_atomic_fields(self):
        fields = list(self)

        common_fields = [field for field in fields if field.name in self._common_fields]
        atomic_fields = [field for field in fields if field.name in self._atomic_fields]

        all_fields = common_fields + atomic_fields
        all_fields.sort(key=lambda field: fields.index(field))
        return all_fields

    def get_enumeration_fields(self):
        fields = list(self)

        common_fields = [field for field in fields if field.name in self._common_fields]
        atomic_fields = [field for field in fields if field.name in self._enumeration_fields]

        all_fields = common_fields + atomic_fields
        all_fields.sort(key=lambda field: fields.index(field))
        return all_fields

    def get_relationship_fields(self):
        fields = list(self)

        common_fields = [field for field in fields if field.name in self._common_fields]
        atomic_fields = [field for field in fields if field.name in self._relationship_fields]

        all_fields = common_fields + atomic_fields
        all_fields.sort(key=lambda field: fields.index(field))
        return all_fields

    def __init__(self, *args, **kwargs):
        # category_choices was passed in via curry() in the factory function below
        category_choices = kwargs.pop("category_choices", [])

        super(MetadataStandardPropertyCustomizerForm, self).__init__(*args, **kwargs)

        property_customizer = self.instance
        # this attribute is needed b/c I access it in the customize_template to decide which other templates to include
        self.type = self.get_current_field_value("field_type")

        if property_customizer.pk:
            # ordinarily, this is done in create_standard_property_customizer_form_data above
            # but if this is an existing model, I still need to do this jiggery-pokery someplace
            # not displaying category field for standard_properties (so I should be able to get away w/ not doing this)
            # self.initial["category"] = property_customizer.category.key
            if self.type == MetadataFieldTypes.ENUMERATION:
                current_enumeration_choices = self.get_current_field_value("enumeration_choices")
                current_enumeration_default = self.get_current_field_value("enumeration_default")
                if isinstance(current_enumeration_choices, basestring):
                    self.initial["enumeration_choices"] = current_enumeration_choices.split("|")
                if isinstance(current_enumeration_default, basestring):
                    self.initial["enumeration_default"] = current_enumeration_default.split("|")

        if self.type == MetadataFieldTypes.ATOMIC:
            atomic_type_field = self.fields["atomic_type"]
            # I am re-using the SingleSelectWidget here (originally written for use w/ EnumerationFields)
            # since atomic_type only shows up if this is an ATOMIC field, it cannot be required
            # but when I do display it, I can remove the empty_label and the EMPTY_CHOICE forcing users to make a choice
            atomic_type_field.empty_label = None
            atomic_type_choices = atomic_type_field.choices
            if EMPTY_CHOICE[0] in atomic_type_choices:
                atomic_type_choices.remove(EMPTY_CHOICE[0])
            atomic_type_field.widget = SingleSelectWidget(choices=atomic_type_choices)
            update_field_widget_attributes(atomic_type_field, {"class": "multiselect single selection_required", })

        elif self.type == MetadataFieldTypes.ENUMERATION:
            proxy = MetadataStandardPropertyProxy.objects.get(pk=self.get_current_field_value("proxy"))
            all_enumeration_choices = proxy.enumerate_choices()
            self.fields["enumeration_choices"].set_choices(all_enumeration_choices, multi=True)
            self.fields["enumeration_default"].set_choices(all_enumeration_choices, multi=True)
            # TODO: I CANNOT GET THE MULTISELECT PLUGIN TO WORK W/ THE RESTRICT_OPTIONS FN
            # TODO: TRY AGAIN W/ NEW EnumerationField CLASSES & MINIMAL JAVASCRIPT CODE (SEE TICKET #215)
            # update_field_widget_attributes(self.fields["enumeration_choices"],{"class":"multiselect","onchange":"restrict_options(this,['%s-enumeration_default']);"%(self.prefix)})
            update_field_widget_attributes(self.fields["enumeration_choices"], {"class": "multiselect multiple", })  # NOTE THAT I AM NOT ADDING "enumeration" AS A CLASS
            update_field_widget_attributes(self.fields["enumeration_default"], {"class": "multiselect multiple", })  # THAT'S B/C "enumeration" IS FOR DEALING W/ "NONE" & "OTHER"
                                                                                                                   # THAT HAPPENS IN THE EDITOR, NOT THE CUSTOMIZER

        elif self.type == MetadataFieldTypes.RELATIONSHIP:
            update_field_widget_attributes(self.fields["relationship_show_subform"], {"class": "enabler", "onchange": "enable_customize_subform_button(this);", })
            if not property_customizer.pk:
                update_field_widget_attributes(self.fields["relationship_show_subform"], {"class": "readonly", "readonly": "readonly", })

        else:
            msg = "invalid field type for standard property: '%s'" % self.type
            raise QuestionnaireError(msg)

        self.fields['field_type'].widget = TextInput()  # don't give users a drop-down menu, just present the current field_type (note this is done _before_ updating widget attributes below)
        update_field_widget_attributes(self.fields["name"], {"class": "label", "readonly": "readonly", })
        update_field_widget_attributes(self.fields["category_name"], {"class": "label", "readonly": "readonly", })
        update_field_widget_attributes(self.fields["order"], {"class": "label", "readonly": "readonly", })
        update_field_widget_attributes(self.fields["field_type"], {"class": "label", "readonly": "readonly", })

        set_field_widget_attributes(self.fields["documentation"], {"cols": "60", "rows": "4", })
        set_field_widget_attributes(self.fields["suggestions"], {"cols": "60", "rows": "4", })

        # specify the widths of header fields...
        # (some should use most of the available space, others should just use a fixed size)
        set_field_widget_attributes(self.fields["name"], {"style": "width: 75%;", })
        set_field_widget_attributes(self.fields["category_name"], {"style": "width: 75%;", })
        set_field_widget_attributes(self.fields["field_type"], {"size": "12", })
        set_field_widget_attributes(self.fields["order"], {"size": "4", })

    def clean(self):
        cleaned_data = self.cleaned_data

        # the "category" field is a special case
        # it was working off of _unsaved_ models
        # so there is no pk associated w/ it
        # the form will, however, have stored the name in the "category_name" field
        # I will use that to find the appropriate category to map to in the view
        self.cleaned_data["category"] = None
        try:
            del self.errors["category"]
        except KeyError:
            pass

        # make sure that if a user chose to render a property as a subform, that the subform customizer exists
        if cleaned_data["field_type"] == MetadataFieldTypes.RELATIONSHIP and cleaned_data["relationship_show_subform"]:
            if not cleaned_data["subform_customizer"]:
                msg = u"Failed to associate a subform customizer with this property."
                self._errors["relationship_show_subform"] = self.error_class([msg])
                del cleaned_data["relationship_show_subform"]
                del cleaned_data["subform_customizer"]

        # make sure that if a user specified multiple default values for an enumeration, that it supports multiple values
        if cleaned_data["field_type"] == MetadataFieldTypes.ENUMERATION:
            n_default_values = len(cleaned_data["enumeration_default"])
            if n_default_values > 1 and not cleaned_data["enumeration_multi"]:
                msg = u"You have specified multiple default values without specifying that this property can have multiple values."
                self._errors["enumeration_default"] = self.error_class([msg])
                del cleaned_data["enumeration_default"]

        return cleaned_data


class MetadataStandardPropertyCustomizerInlineFormSet(MetadataCustomizerInlineFormSet):
    pass


def MetadataStandardPropertyCustomizerInlineFormSetFactory(*args,**kwargs):
    _prefix = kwargs.pop("prefix", "standard_property")
    _data = kwargs.pop("data", None)
    _initial = kwargs.pop("initial", [])
    _instance = kwargs.pop("instance")
    _categories = kwargs.pop("categories", [])
    _queryset = kwargs.pop("queryset", MetadataStandardPropertyCustomizer.objects.none())
    new_kwargs = {
        "can_delete": False,
        "extra": kwargs.pop("extra", 0),
        "formset": MetadataStandardPropertyCustomizerInlineFormSet,
        "form": MetadataStandardPropertyCustomizerForm,
        "fk_name": "model_customizer"  # required in-case there are more than 1 fk's to "metadatamodelcustomizer"; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)

    # using curry() to pass arguments to the individual formsets
    # in this case, the set of choices for scientific categories
    _formset = inlineformset_factory(MetadataModelCustomizer, MetadataStandardPropertyCustomizer, *args, **new_kwargs)
    _formset.form = staticmethod(curry(MetadataStandardPropertyCustomizerForm, category_choices=_categories))
    if _initial:
        _formset.number_of_properties = len(_initial)
    elif _queryset:
        _formset.number_of_properties = len(_queryset)
    elif _data:
        _formset.number_of_properties = int(_data[u"%s-TOTAL_FORMS" % _prefix])
    else:
        _formset.number_of_properties = 0

    if _data:
        return _formset(_data, instance=_instance, prefix=_prefix)

    return _formset(queryset=_queryset, initial=_initial, instance=_instance, prefix=_prefix)