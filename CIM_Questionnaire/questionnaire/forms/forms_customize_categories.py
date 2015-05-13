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
.. module:: forms_customize_standard_categories

forms for customizing standard_categories

"""

import time
from django.forms import CharField
from django.forms.models import modelformset_factory, inlineformset_factory
from django.forms.util import ErrorList
from django.forms.formsets import DELETION_FIELD_NAME
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from CIM_Questionnaire.questionnaire.forms.forms_customize import MetadataCustomizerForm, MetadataCustomizerFormSet, MetadataCustomizerInlineFormSet
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataModelCustomizer, MetadataStandardCategoryCustomizer, MetadataScientificCategoryCustomizer
from CIM_Questionnaire.questionnaire.utils import model_to_data, update_field_widget_attributes, set_field_widget_attributes, EnumeratedType, EnumeratedTypeList


###########################
# code to help w/ tagging #
###########################

class TagType(EnumeratedType):
    pass

TagTypes = EnumeratedTypeList([
    TagType("STANDARD", "standard_categories"),
    TagType("SCIENTIFIC", "scientific_categories"),
])


class TagField(CharField):

    def __init__(self, *args, **kwargs):
        _type = kwargs.pop("type")
        kwargs.update({
            "label": "Available Categories",
            "required": False,
        })
        super(TagField, self).__init__(*args, **kwargs)
        self.type = _type

    def render(self):
        """
        allows me to render the underlying widget
        (since it's not done automatically b/c this field exists outside of any form)
        :return: HTML representation of tag
        """
        return self.widget.render(self.type.getName(), self.initial)


############################
# now for the actual forms #
############################

NEW_CATEGORY_NAME = "new category"


def create_standard_category_customizer_form_data(model_customizer, standard_category_customizer):

    standard_category_customizer_form_data = model_to_data(
        standard_category_customizer,
        exclude=[],
        include={
            "last_modified": time.strftime("%c"),
            "loaded": True,  # standard_category_forms are always loaded
        }
    )

    return standard_category_customizer_form_data


def create_scientific_category_customizer_form_data(model_customizer, scientific_category_customizer):

    scientific_category_customizer_form_data = model_to_data(
        scientific_category_customizer,
        exclude=[],
        include={
            DELETION_FIELD_NAME: False,
            "last_modified": time.strftime("%c"),
            "loaded": False,  # in addition to being unloaded until get_form_section renders the form, a category_form remains unloaded until it is edited via AJAX
        }
    )

    return scientific_category_customizer_form_data


def save_valid_categories_formset(categories_formset):

    category_instances = []
    for category_instance in categories_formset.save(commit=False):
        # TODO: UNLOADED INLINE_FORMSETS ARE NOT SAVING THE FK FIELD APPROPRIATELY
        # THIS MAKES NO SENSE, B/C THE INDIVIDUAL INSTANCES DO HAVE THE "model" FIELD SET
        # BUT THAT CORRESPONDING MetadataModel HAS NO VALUES FOR "standard_properties"
        # RE-SETTING IT AND RE-SAVING IT SEEMS TO DO THE TRICK
        fk_field_name = categories_formset.fk.name
        fk_model = getattr(category_instance, fk_field_name)
        setattr(category_instance, fk_field_name, fk_model)

        # TODO: THIS CAN BE REMOVED ONCE ISSUE #318 IS FIXED
        msg = _("The project this category is bound to does not match the project of the parent customization."
                "  (See issue #318.)"
                )
        parent_project = category_instance.model_customizer.project
        category_project = category_instance.project
        assert category_project == parent_project, msg

        category_instance.save()

        category_instances.append(category_instance)

    return category_instances


class MetadataCategoryCustomizerForm(MetadataCustomizerForm):

    class Meta:
        abstract = True

    def get_hidden_fields(self):
        return self.get_fields_from_list(self._hidden_fields)

    def get_customizer_fields(self):
        return self.get_fields_from_list(self._customizer_fields)

    def clean(self):
        """
        ensure that the key is based on the name
        and ensure that the name of a new category has been changed
        :return:
        """
        super(MetadataCategoryCustomizerForm, self).clean()
        cleaned_data = self.cleaned_data

        cleaned_data["key"] = slugify(cleaned_data["name"])
        # ideally I would also change "self.data" w/ the updated key
        # however, "self.data" is immutable
        # since I need the updated key value to pass back to the template via AJAX
        # I use the "existing_data" argument to the "get_data_from_form" fn in the AJAX view

        if cleaned_data["name"] == NEW_CATEGORY_NAME:
            self._errors["name"] = ErrorList()
            self._errors["name"].append("Please change the name.")

        # TODO: THIS CAN BE REMOVED ONCE ISSUE #318 IS FIXED
        try:
            msg = _("The project this category is bound to does not match the project of the parent customization."
                    "  (See issue #318.)"
                    )
            parent_project = cleaned_data["model_customizer"].project
            category_project = cleaned_data["project"]
            assert category_project == parent_project, msg
        except KeyError:
            pass

        return cleaned_data


class MetadataCategoryCustomizerFormSet(MetadataCustomizerFormSet):

    def __init__(self, *args, **kwargs):
        _type = kwargs.pop("type")
        super(MetadataCategoryCustomizerFormSet, self).__init__(*args, **kwargs)

        category_names = [
            category_form.get_current_field_value("name")
            for category_form in self.forms
        ]

        tags = TagField(
            type=_type,
            initial="|".join(category_names),
            help_text=_(
                "This widget contains the standard set of categories associated with this CIM ontology."
                "If this set is unsuitable, or empty, then the categorization should be updated."
                "Please contact your project administrator."
            ),
        )
        update_field_widget_attributes(tags, {"class": "tags", })

        self.tags = tags

    def get_number_of_forms(self):
        # you might think this number will be off in case extra categories were added or deleted
        # but this only gets called when re-creating the management form in-case it is unloaded
        # (in which case nothing could have been added or deleted; hence the term "_initial_" in the variable below)
        # if it is loaded, then the management form will already exist w/ correct values in self.data
        return self.number_of_initial_forms


class MetadataCategoryCustomizerInlineFormSet(MetadataCustomizerInlineFormSet):

    def __init__(self, *args, **kwargs):
        _type = kwargs.pop("type")
        super(MetadataCategoryCustomizerInlineFormSet, self).__init__(*args, **kwargs)

        category_names = [
            category_form.get_current_field_value("name")
            for category_form in self.forms
        ]

        tags = TagField(
            type=_type,
            initial="|".join(category_names),
            help_text=_(
                "This widget contains the standard set of categories associated with this CIM ontology."
                "If this set is unsuitable, or empty, then the categorization should be updated."
                "Please contact your project administrator."
            ),
        )
        update_field_widget_attributes(tags, {"class": "tags", })

        self.tags = tags

    def get_number_of_forms(self):
        # you might think this number will be off in case extra categories were added or deleted
        # but this only gets called when re-creating the management form in-case it is unloaded
        # (in which case nothing could have been added or deleted; hence the term "_initial_" in the variable below)
        # if it is loaded, then the management form will already exist w/ correct values in self.data
        return self.number_of_initial_forms


class MetadataStandardCategoryCustomizerForm(MetadataCategoryCustomizerForm):

    class Meta:
        model = MetadataStandardCategoryCustomizer
        fields = [
            # hidden fields...
            "key", "proxy", "project", "version", "order",
            # customizer fields...
            "name", "description",
        ]

    _hidden_fields = ("key", "proxy", "project", "version", "order", )
    _customizer_fields = ("name", "description", )

    def __init__(self, *args, **kwargs):
        super(MetadataStandardCategoryCustomizerForm, self).__init__(*args, **kwargs)
        set_field_widget_attributes(self.fields["name"], {"readonly": "readonly", "class": "readonly", })  # don't allow users to change the name of standard categories
        set_field_widget_attributes(self.fields["description"], {"cols": "40", "rows": "4", })
        self.load()  # just always load a standard category customizer


def MetadataStandardCategoryCustomizerFormSetFactory(*args,**kwargs):
    _prefix = kwargs.pop("prefix", "standard_categories")
    _data = kwargs.pop("data", None)
    _initial = kwargs.pop("initial", [])
    _queryset = kwargs.pop("queryset", MetadataStandardCategoryCustomizer.objects.none())
    new_kwargs = {
        "can_delete": False,
        "extra": kwargs.pop("extra", 0),
        "formset": MetadataCategoryCustomizerFormSet,
        "form": MetadataStandardCategoryCustomizerForm,
    }
    new_kwargs.update(kwargs)

    _formset = modelformset_factory(MetadataStandardCategoryCustomizer, *args, **new_kwargs)
    _type = TagTypes.STANDARD

    if _initial:
        _formset.number_of_initial_forms = len(_initial)
    elif _queryset:
        _formset.number_of_initial_forms = len(_queryset)
    elif _data:
        _formset.number_of_initial_forms = int(_data[u"%s-TOTAL_FORMS" % _prefix])
    else:
        _formset.number_of_initial_forms = 0

    if _data:
        return _formset(_data, initial=_initial, prefix=_prefix, type=_type)

    return _formset(queryset=_queryset, initial=_initial, prefix=_prefix, type=_type)


def MetadataStandardCategoryCustomizerInlineFormSetFactory(*args, **kwargs):

    _prefix = kwargs.pop("prefix", "standard_categories")
    _data = kwargs.pop("data", None)
    _initial = kwargs.pop("initial", None)
    _instance = kwargs.pop("instance")
    _queryset = kwargs.pop("queryset", MetadataStandardCategoryCustomizer.objects.none())
    new_kwargs = {
        "can_delete": False,
        "extra": kwargs.pop("extra", 0),
        "formset": MetadataCategoryCustomizerInlineFormSet,
        "form": MetadataStandardCategoryCustomizerForm,
        "fk_name": "model_customizer"  # required in-case there are more than 1 fk's to "metadatamodelcustomizer"; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)

    _formset = inlineformset_factory(MetadataModelCustomizer, MetadataStandardCategoryCustomizer, *args, **new_kwargs)
    _type = TagTypes.STANDARD

    if _initial is not None:
        _formset.number_of_initial_forms = len(_initial)
    elif _queryset:
        _formset.number_of_initial_forms = len(_queryset)
    elif _data:
        _formset.number_of_initial_forms = int(_data[u"%s-TOTAL_FORMS" % _prefix])
    else:
        _formset.number_of_initial_forms = 0

    if _data:
        return _formset(_data, instance=_instance, initial=_initial, prefix=_prefix, type=_type)

    return _formset(queryset=_queryset, instance=_instance, initial=_initial, prefix=_prefix, type=_type)


class MetadataScientificCategoryCustomizerForm(MetadataCategoryCustomizerForm):

    class Meta:
        model = MetadataScientificCategoryCustomizer
        fields = [
            # hidden fields...
            "key", "proxy", "project", "vocabulary_key", "component_key", "order",
            # customizer fields...
            "name", "description",
        ]

    _hidden_fields = ("key", "proxy", "project", "vocabulary_key", "component_key", "order", )
    _customizer_fields = ("name", "description", )

    def __init__(self, *args, **kwargs):
        super(MetadataScientificCategoryCustomizerForm, self).__init__(*args, **kwargs)
        set_field_widget_attributes(self.fields["description"], {"cols": "40", "rows": "4", })
        # update_field_widget_attributes(self.fields["name"], {"readonly": "readonly", "class": "readonly", })


def MetadataScientificCategoryCustomizerFormSetFactory(*args, **kwargs):
    _prefix = kwargs.pop("prefix", "scientific_categories")
    _data = kwargs.pop("data", None)
    _initial = kwargs.pop("initial", None)
    _queryset = kwargs.pop("queryset", MetadataScientificCategoryCustomizer.objects.none())
    new_kwargs = {
        "can_delete": True,
        "extra": kwargs.pop("extra", 0),
        "formset": MetadataCategoryCustomizerFormSet,
        "form": MetadataScientificCategoryCustomizerForm,
    }
    new_kwargs.update(kwargs)

    _formset = modelformset_factory(MetadataScientificCategoryCustomizer, *args, **new_kwargs)
    _type = TagTypes.SCIENTIFIC

    if _initial is not None:
        _formset.number_of_initial_forms = len(_initial)
    elif _queryset:
        _formset.number_of_initial_forms = len(_queryset)
    elif _data:
        _formset.number_of_initial_forms = int(_data[u"%s-TOTAL_FORMS" % _prefix])
    else:
        _formset.number_of_initial_forms = 0

    if _data:
        return _formset(_data, initial=_initial, prefix=_prefix, type=_type)

    return _formset(queryset=_queryset, initial=_initial, prefix=_prefix, type=_type)


def MetadataScientificCategoryCustomizerInlineFormSetFactory(*args, **kwargs):

    _prefix = kwargs.pop("prefix", "scientific_categories")
    _data = kwargs.pop("data", None)
    _initial = kwargs.pop("initial", None)
    _instance = kwargs.pop("instance")
    _queryset = kwargs.pop("queryset", MetadataStandardCategoryCustomizer.objects.none())
    new_kwargs = {
        "can_delete": True,
        "extra": kwargs.pop("extra", 0),
        "formset": MetadataCategoryCustomizerInlineFormSet,
        "form": MetadataScientificCategoryCustomizerForm,
        "fk_name": "model_customizer"  # required in-case there are more than 1 fk's to "metadatamodelcustomizer"; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)

    _formset = inlineformset_factory(MetadataModelCustomizer, MetadataScientificCategoryCustomizer, *args, **new_kwargs)
    _type = TagTypes.SCIENTIFIC

    if _initial is not None:
        _formset.number_of_initial_forms = len(_initial)
    elif _queryset:
        _formset.number_of_initial_forms = len(_queryset)
    elif _data:
        _formset.number_of_initial_forms = int(_data[u"%s-TOTAL_FORMS" % _prefix])
    else:
        _formset.number_of_initial_forms = 0

    if _data:
        return _formset(_data, instance=_instance, initial=_initial, prefix=_prefix, type=_type)

    return _formset(queryset=_queryset, instance=_instance, initial=_initial, prefix=_prefix, type=_type)
