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
.. module:: forms_customize_scientific_properties

forms for customizing scientific_properties

"""

import time
from collections import OrderedDict
from django.forms import CharField, ChoiceField
from django.forms.models import inlineformset_factory
from django.utils.functional import curry

from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataModelCustomizer, MetadataScientificCategoryCustomizer, MetadataScientificPropertyCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataScientificPropertyProxy
from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes, MultipleSelectWidget, SingleSelectWidget, EMPTY_CHOICE
from CIM_Questionnaire.questionnaire.forms.forms_customize import MetadataCustomizerForm, MetadataCustomizerInlineFormSet
from CIM_Questionnaire.questionnaire.utils import set_field_widget_attributes, update_field_widget_attributes, model_to_data


def create_scientific_property_customizer_form_data(model_customizer, scientific_property_customizer):

    scientific_property_customizer_form_data = model_to_data(
        scientific_property_customizer,
        exclude=["model", ],  # no need to pass model, since this is handled by virtue of being an inline_formset
        include={
            "last_modified": time.strftime("%c"),
            "loaded": False,  # finally, scientific_property_customizer forms use the load-on-demand paradigm
        }
    )

    if scientific_property_customizer.is_enumeration:
        # enumeration fields
        current_enumeration_choices = scientific_property_customizer_form_data["enumeration_choices"]
        current_enumeration_default = scientific_property_customizer_form_data["enumeration_default"]
        if current_enumeration_choices:
            scientific_property_customizer_form_data["enumeration_choices"] = current_enumeration_choices.split("|")
        if current_enumeration_default:
            scientific_property_customizer_form_data["enumeration_default"] = current_enumeration_default.split("|")

    # BE AWARE THAT CHECKING THIS DICT ITEM (WHOSE VALUE AS A LIST) WON'T GIVE THE FULL LIST
    # APPARENTLY, THIS IS A "FEATURE" AND NOT A "BUG" [https://code.djangoproject.com/ticket/1130]

    else:
        # atomic fields...
        pass

    scientific_category = scientific_property_customizer.category
    if scientific_category:
        scientific_property_customizer_form_data["category"] = scientific_category.key
        scientific_property_customizer_form_data["category_name"] = scientific_category.name

    return scientific_property_customizer_form_data


class MetadataScientificPropertyCustomizerForm(MetadataCustomizerForm):

    class Meta:
        model = MetadataScientificPropertyCustomizer
        fields = [
            # hidden fields...
            "field_type", "proxy", "is_enumeration", "vocabulary_key", "component_key", "model_key",
            # header fields..., TextInput, TextInput
            "name", "category_name", "order",
            # common fields...
            "category", "displayed", "required", "editable", "unique", "verbose_name", "default_value", "documentation", "inline_help",
            # keyboard fields...
            "atomic_type", "atomic_default",
            # enumeration fields...
            "enumeration_choices", "enumeration_default", "enumeration_open", "enumeration_multi", "enumeration_nullable",
            # extra fields..
            "display_extra_standard_name", "edit_extra_standard_name", "extra_standard_name", "display_extra_description", "edit_extra_description", "extra_description", "display_extra_units", "edit_extra_units", "extra_units",
            ]

    category_name = CharField(label="Category", required=False)
    category = ChoiceField(required=False)  # changing from the default fk field (ModelChoiceField)
                                            # since I'm potentially dealing w/ _unsaved_ category_customizers

    _hidden_fields = ("field_type", "proxy", "is_enumeration", "vocabulary_key", "component_key", "model_key", )
    _header_fields = ("name", "category_name", "order", )
    _common_fields = ("category", "displayed", "required", "editable", "unique", "verbose_name", "documentation", "inline_help", "suggestions", )
    _keyboard_fields = ("atomic_type", "atomic_default", )
    _enumeration_fields = ("enumeration_choices", "enumeration_default", "enumeration_open", "enumeration_multi", "enumeration_nullable", )

    _extra_fields = ("display_extra_standard_name", "edit_extra_standard_name", "extra_standard_name", "display_extra_description", "edit_extra_description", "extra_description", "display_extra_units", "edit_extra_units", "extra_units", )

    # set of fields that will be the same for all members of a formset;
    # thus I can cache the query (mostly for relationship fields)
    cached_fields = ["field_type"]

    def get_hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)

    def get_header_fields(self):
        return self.get_fields_from_list(self._header_fields)

    def get_keyboard_fields(self):
        fields = list(self)

        common_fields = [field for field in fields if field.name in self._common_fields]
        keyboard_fields = [field for field in fields if field.name in self._keyboard_fields]

        all_fields = common_fields + keyboard_fields
        all_fields.sort(key=lambda field: fields.index(field))
        return all_fields

    def get_enumeration_fields(self):
        fields = list(self)

        common_fields = [field for field in fields if field.name in self._common_fields]
        enumeration_fields = [field for field in fields if field.name in self._enumeration_fields]

        all_fields = common_fields + enumeration_fields
        all_fields.sort(key=lambda field: fields.index(field))
        return all_fields

    def get_fields(self):
        is_enumeration = self.get_current_field_value("is_enumeration",False)
        if is_enumeration:
            return self.get_enumeration_fields()
        else:
            return self.get_keyboard_fields()
        
    def get_extra_fields(self):
        return self.get_fields_from_list(self._extra_fields)

    def get_extra_fieldsets(self):
        fields = self.get_extra_fields()
        fieldsets = OrderedDict()
        fieldsets["Standard Name"] = [field for field in fields if "standard_name" in field.name]
        fieldsets["Description"] = [field for field in fields if "description" in field.name]
        fieldsets["Scientific Units"] = [field for field in fields if "units" in field.name]
        return fieldsets

    def __init__(self, *args, **kwargs):
        # category_choices was passed in via curry() in the factory function below
        category_choices = kwargs.pop("category_choices", [])

        super(MetadataScientificPropertyCustomizerForm,self).__init__(*args, **kwargs)

        property_customizer = self.instance
        is_enumeration = self.get_current_field_value("is_enumeration", False)

        self.fields["category"].choices = EMPTY_CHOICE + [(category.key, category.name) for category in category_choices]
        update_field_widget_attributes(self.fields["category"], {"class": "multiselect single", "onchange": "copy_value(this,'%s-category_name');" % self.prefix, })

        if property_customizer.pk:
            # ordinarily, this is done in create_scientific_property_customizer_form_data above
            # but if this is an existing model, I still need to do this jiggery-pokery someplace
            if property_customizer.category:
                self.initial["category"] = property_customizer.category.key
            if is_enumeration:
                current_enumeration_choices = self.get_current_field_value("enumeration_choices")
                current_enumeration_default = self.get_current_field_value("enumeration_default")
                if isinstance(current_enumeration_choices, basestring):
                    self.initial["enumeration_choices"] = current_enumeration_choices.split("|")
                if isinstance(current_enumeration_default, basestring):
                    self.initial["enumeration_default"] = current_enumeration_default.split("|")

        # this attribute ("type") is needed b/c I can access it in the customize template
        if not is_enumeration:
            self.type = MetadataFieldTypes.ATOMIC
            # I am re-using the SingleSelectWidget here (originally written for use w/ EnumerationFields)
            # since atomic_type only shows up if this is an ATOMIC field, it cannot be required
            # but when I do display it, I can remove the empty_label and the EMPTY_CHOICE forcing users to make a choice
            atomic_type_field = self.fields["atomic_type"]
            atomic_type_field.empty_label = None
            atomic_type_choices = atomic_type_field.choices
            if EMPTY_CHOICE[0] in atomic_type_choices:
                atomic_type_choices.remove(EMPTY_CHOICE[0])
            atomic_type_field.widget = SingleSelectWidget(choices=atomic_type_choices)
            update_field_widget_attributes(atomic_type_field, {"class": "multiselect single selection_required", })

        else:
            self.type = MetadataFieldTypes.ENUMERATION
            proxy = MetadataScientificPropertyProxy.objects.get(pk=self.get_current_field_value("proxy"))
            all_enumeration_choices = proxy.enumerate_choices()
            self.fields["enumeration_choices"].set_choices(all_enumeration_choices, multi=True)
            self.fields["enumeration_default"].set_choices(all_enumeration_choices, multi=True)
            # TODO: I CANNOT GET THE MULTISELECT PLUGIN TO WORK W/ THE RESTRICT_OPTIONS FN
            # TODO: TRY AGAIN W/ NEW EnumerationField CLASSES & MINIMAL JAVASCRIPT CODE (SEE TICKET #215)
            # update_field_widget_attributes(self.fields["enumeration_choices"],{"class":"multiselect","onchange":"restrict_options(this,['%s-enumeration_default']);"%(self.prefix)})
            update_field_widget_attributes(self.fields["enumeration_choices"], {"class": "multiselect multiple", })  # NOTE THAT I AM NOT ADDING "enumeration" AS A CLASS
            update_field_widget_attributes(self.fields["enumeration_default"], {"class": "multiselect multiple", })  # THAT'S B/C "enumeration" IS FOR DEALING W/ "NONE" & "OTHER"
                                                                                                                     # THAT HAPPENS IN THE EDITOR, NOT THE CUSTOMIZER

        update_field_widget_attributes(self.fields["name"], {"class": "label", "readonly": "readonly", })
        update_field_widget_attributes(self.fields["category_name"], {"class": "label", "readonly": "readonly", })
        update_field_widget_attributes(self.fields["order"], {"class": "label fixed_width", "readonly": "readonly", })

        set_field_widget_attributes(self.fields["documentation"], {"cols": "60", "rows": "4", })
        set_field_widget_attributes(self.fields["extra_description"], {"rows": "4", })

        # specify the widths of header fields...
        # (strings should use most of the available space, integers should just use a fixed size of 4)
        set_field_widget_attributes(self.fields["name"], {"style": "width: 75%;", })
        set_field_widget_attributes(self.fields["category_name"], {"style": "width: 75%;", })
        set_field_widget_attributes(self.fields["order"], {"size": "4", })

    def clean(self):
        cleaned_data = self.cleaned_data

        # the "category" field is a special case
        # it was working off of _unsaved_ models
        # so there is no pk associated w/ it
        # the form will, however, have stored the name in the "category_name" field
        # I will use that to find the appropriate category to map to in the view
        try:
            self.cleaned_data["category"] = None
            del self.errors["category"]
        except KeyError:
            pass

        # make sure that if a user specified multiple default values for an enumeration, that it supports multiple values
        if cleaned_data["is_enumeration"] == True:
            n_default_values = len(cleaned_data["enumeration_default"])
            if n_default_values > 1 and not cleaned_data["enumeration_multi"]:
                msg = u"You have specified multiple default values without specifying that this property can have multiple values."
                self._errors["enumeration_default"] = self.error_class([msg])
                del cleaned_data["enumeration_default"]

        return cleaned_data


class MetadataScientificPropertyCustomizerInlineFormSet(MetadataCustomizerInlineFormSet):

    def get_number_of_forms(self):
        return self.number_of_properties


def MetadataScientificPropertyCustomizerInlineFormSetFactory(*args, **kwargs):
    _prefix = kwargs.pop("prefix", "scientific_property")
    _data = kwargs.pop("data", None)
    _initial = kwargs.pop("initial", None)
    _instance = kwargs.pop("instance")
    _categories = kwargs.pop("categories", [])
    _queryset = kwargs.pop("queryset", MetadataScientificPropertyCustomizer.objects.none())
    new_kwargs = {
        "can_delete": False,
        "extra": kwargs.pop("extra", 0),
        "formset": MetadataScientificPropertyCustomizerInlineFormSet,
        "form": MetadataScientificPropertyCustomizerForm,
        "fk_name": "model_customizer"  # required in-case there are more than 1 fk's to "metadatamodelcustomizer"; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)

    # using curry() to pass arguments to the individual formsets
    _formset = inlineformset_factory(MetadataModelCustomizer, MetadataScientificPropertyCustomizer, *args, **new_kwargs)
    _formset.form = staticmethod(curry(MetadataScientificPropertyCustomizerForm, category_choices=_categories))

    if _initial is not None:
        _formset.number_of_properties = len(_initial)
    elif _queryset:
        _formset.number_of_properties = len(_queryset)
    elif _data:
        _formset.number_of_properties = int(_data[u"%s-TOTAL_FORMS" % _prefix])
    else:
        _formset.number_of_properties = 0

    if _data:
        return _formset(_data, initial=_initial, instance=_instance, prefix=_prefix)

    return _formset(queryset=_queryset, initial=_initial, instance=_instance, prefix=_prefix)