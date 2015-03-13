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
.. module:: forms_edit_standard_properties

classes for CIM Questionnaire standard_property edit form creation & manipulation
"""

import time
from django.utils.functional import curry
from django.forms.models import inlineformset_factory
from collections import OrderedDict

from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes, MetadataAtomicFieldTypes, CachedModelChoiceField
from CIM_Questionnaire.questionnaire.fields import METADATA_ATOMICFIELD_MAP, EMPTY_CHOICE, NULL_CHOICE, OTHER_CHOICE
from CIM_Questionnaire.questionnaire.forms.forms_edit import MetadataEditingForm, MetadataEditingInlineFormSet
from CIM_Questionnaire.questionnaire.forms.forms_edit import save_valid_subforms
from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataCustomizer
from CIM_Questionnaire.questionnaire.models.metadata_model import MetadataModel, MetadataStandardProperty
from CIM_Questionnaire.questionnaire.models.metadata_proxy import MetadataStandardPropertyProxy
from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary
from CIM_Questionnaire.questionnaire.views.views_inheritance import set_cached_inheritance_data
from CIM_Questionnaire.questionnaire.utils import QuestionnaireError
from CIM_Questionnaire.questionnaire.utils import get_initial_data, model_to_data, find_in_sequence, update_field_widget_attributes, set_field_widget_attributes, get_joined_keys_dict


def create_standard_property_form_data(model, standard_property, standard_property_customizer=None):

    standard_property_form_data = model_to_data(
        standard_property,
        exclude=["model", ],  # no need to pass model, since this is handled by virtue of being an "inline" formset
        include={
            "last_modified": time.strftime("%c"),
            "loaded": False,
        }
    )

    if standard_property_customizer:

        field_type = standard_property_form_data["field_type"]

        if field_type == MetadataFieldTypes.ATOMIC:
            value_field_name = "atomic_value"
            if standard_property_customizer.default_value:
                standard_property_form_data[value_field_name] = standard_property_customizer.default_value

        elif field_type == MetadataFieldTypes.ENUMERATION:
            value_field_name = "enumeration_value"
            is_multi = standard_property_customizer.enumeration_multi
            current_enumeration_value = standard_property_form_data[value_field_name]
            default_enumeration_value = standard_property_customizer.enumeration_default
            if current_enumeration_value:
                if is_multi:
                    standard_property_form_data[value_field_name] = current_enumeration_value.split("|")
                else:
                    standard_property_form_data[value_field_name] = current_enumeration_value
            elif default_enumeration_value:
                if is_multi:
                    standard_property_form_data[value_field_name] = default_enumeration_value.split("|")
                else:
                    standard_property_form_data[value_field_name] = default_enumeration_value

        elif field_type == MetadataFieldTypes.RELATIONSHIP:
            value_field_name = "relationship_value"
            pass

        else:
            msg = "invalid field type for standard property: %s" % (field_type)
            raise QuestionnaireError(msg)

        # further customization is done in the customize() fn below

    return standard_property_form_data


def save_valid_standard_properties_formset(standard_properties_formset):
    # using zip here is the only way that I managed to get saving to work
    # I have to save via the inlineformset (so that the inline fk gets saved appropriately)
    # but I also need access to the underlying form so I can check certain customization details

    standard_property_instances = []
    for standard_property_instance, standard_property_form in zip(standard_properties_formset.save(commit=True),standard_properties_formset.forms):
        assert(standard_property_instance.name == standard_property_form.get_current_field_value("name"))
        if standard_property_instance.field_type == MetadataFieldTypes.RELATIONSHIP and standard_property_form.customizer.relationship_show_subform:

            (subform_customizer, model_subformset, standard_properties_subformsets, scientific_properties_subformsets) = \
                standard_property_form.get_subform_tuple()

            for model_subform in model_subformset.forms:
                property_key = model_subform.prefix

                subform_has_changed = any([
                    # don't bother checking model_subformset - if the properties have changed, I'll be saving it regardless
                    #model_subform.has_changed(),
                    any([form.has_changed() for form in standard_properties_subformsets[property_key]]),
                    any([form.has_changed() for form in scientific_properties_subformsets[property_key]]),
                ])

                if model_subformset._should_delete_form(model_subform):
                    # I am assuming that if this form is not bound to an existing instance
                    # that passing it to remove will have no effect
                    standard_property_instance.relationship_value.remove(model_subform.instance)

                elif subform_has_changed:
                    subform_model_instance = save_valid_subforms(model_subform,standard_properties_subformsets[property_key], scientific_properties_subformsets[property_key])
                    standard_property_instance.relationship_value.add(subform_model_instance)
                # TODO: FOR SOME REASON, relationship_value IS EMPTY AT THE START OF THIS FN
                # SO WHAT SHOULD I DO IF THE FORM HASN'T CHANGED (currently it seems to always be returning True)?
                # SHOULD I ADD THE FOLLOWING SORT OF CODE?
                # else:
                #     standard_property_instance.relationship_value.add(model_subform.instance)

            # standard_property_instance.save()  # I'm saving below in all cases; no need to do this twice

        # TODO: UNLOADED INLINE_FORMSETS ARE NOT SAVING THE FK FIELD APPROPRIATELY
        # THIS MAKES NO SENSE, B/C THE INDIVIDUAL INSTANCES DO HAVE THE "model" FIELD SET
        # BUT THAT CORRESPONDING MetadataModel HAS NO VALUES FOR "standard_properties"
        # RE-SETTING IT AND RE-SAVING IT SEEMS TO DO THE TRICK
        fk_field_name = standard_properties_formset.fk.name
        fk_model = getattr(standard_property_instance, fk_field_name)
        setattr(standard_property_instance, fk_field_name, fk_model)
        standard_property_instance.save()

        standard_property_instances.append(standard_property_instance)

    return standard_property_instances


class MetadataAbstractStandardPropertyForm(MetadataEditingForm):

    class Meta:
        abstract = True

    cached_fields = []
    _value_fields = ["atomic_value", "enumeration_value", "enumeration_other_value", "relationship_value", ]
    _hidden_fields = ["proxy", "field_type", "name", "order", "is_label", "id", ]

    # TODO: FILTER THESE BY PROJECT & VERSION?
    proxy = CachedModelChoiceField(queryset=MetadataStandardPropertyProxy.objects.all())

    def __init__(self, *args, **kwargs):

        # customizers and parent were passed in via curry in the factory functions below
        customizers = kwargs.pop("customizers", None)
        parent = kwargs.pop("parent", None)
        inheritance_data = kwargs.pop("inheritance_data", None)

        # RIGHT, THIS CAUSED AN AWFUL LOT OF CONFUSION
        # THE CALL TO super() CAN TAKE A "customizer" ARGUMENT
        # BUT I CAN ONLY FIND THAT CUSTOMIZER BY MATCHING IT AGAINST THE VALUE OF "proxy"
        # THAT REQUIRES CALLING get_current_field_value() WHICH CHECKS THE PREFIX OF A FORM
        # BUT THAT PREFIX - AND SOME OTHER THINGS TOO - IS ONLY SET FROM DEEP W/IN THE __init__ FN
        # OF A BASE CLASS; SO I CALL super FIRST W/OUT A "customizer" ARGUMENT AND THEN CUSTOMIZE
        # AT THE END OF THIS __init__ FN

        super(MetadataAbstractStandardPropertyForm, self).__init__(*args, **kwargs)
        self.parent = parent

        if customizers:
            proxy_pk = int(self.get_current_field_value("proxy"))
            customizer = find_in_sequence(lambda c: c.proxy.pk == proxy_pk, customizers)
            assert(customizer.name == self.get_current_field_value("name"))  # this is new code; just make sure it works
        else:
            customizer = None

        field_type = self.get_current_field_value("field_type")

        if self.instance.pk and field_type == MetadataFieldTypes.ENUMERATION:
            # ordinarily, this is done in create_standard_property_form_data above
            # but if this is an existing model, I still need to do this jiggery-pokery someplace
            current_enumeration_value = self.get_current_field_value("enumeration_value")
            if isinstance(current_enumeration_value, basestring) and customizer.enumeration_multi:
                self.initial["enumeration_value"] = current_enumeration_value.split("|")

        if field_type == MetadataFieldTypes.ATOMIC:
            pass

        elif field_type == MetadataFieldTypes.ENUMERATION:
            update_field_widget_attributes(self.fields["enumeration_value"], {"class": "multiselect"})
            update_field_widget_attributes(self.fields["enumeration_other_value"], {"class": "other"})

        elif field_type == MetadataFieldTypes.RELATIONSHIP:
            # TODO: FILTER BY PROJECT AS WELL
            proxy = MetadataStandardPropertyProxy.objects.select_related("relationship_target_model").get(pk=proxy_pk)
            self.fields["relationship_value"].queryset = MetadataModel.objects.filter(proxy=proxy.relationship_target_model)
            self.subform_tuple = (None,)    # I should only ever access this once it's been setup in customize()
                                            # hence the assert statements in get_subform_tuple()

        else:
            msg = "invalid field type for standard property: '%s'." % (field_type)
            raise QuestionnaireError(msg)

        if self.get_current_field_value("is_label", False):
            # TODO: THERE IS AN EXISTING CLASS CALLED "label"
            # TODO: BUT REALLY I OUGHT TO CHANGE THAT TO SOMETHING LIKE "title" OR "header" AND USE "label" HERE
            value_field_name = self.get_value_field_name()
            update_field_widget_attributes(self.fields[value_field_name], {"class": "is_label"})

        if customizer:
            # HUH, WHY AM I CALLING THIS EXPLICITLY HERE, WHEN IT OUGHT TO BE CALLED AUTOMATICALLY IN super() ABOVE?
            # B/C customizer IS NOT PASSED TO super() B/C IT NEEDS TO BE FOUND BASED ON THE CURRENT PROXY
            # WHICH GETS RETURNED BY get_current_field_value()
            # WHICH HAS TO HAVE THIS FORM MOSTLY SET UP BEFORE IT WILL WORK
            # WHICH HAPPENS IN THE CALL TO super()
            # (SEE ABOVE)
            self.customize(customizer, inheritance_data=inheritance_data)

    def get_value_field_name(self):

        field_type = self.get_current_field_value("field_type")

        if field_type == MetadataFieldTypes.ATOMIC:
            return "atomic_value"
        elif field_type == MetadataFieldTypes.ENUMERATION:
            return "enumeration_value"
        elif field_type == MetadataFieldTypes.RELATIONSHIP:
            return "relationship_value"
        else:
            msg = "unable to determine 'value' field for fieldtype '%s'" % (field_type)
            raise QuestionnaireError(msg)

    def get_value_field(self):

        value_field_name = self.get_value_field_name()
        value_fields = self.get_fields_from_list([value_field_name])

        try:
            return value_fields[0]
        except:
            return None

    def customize(self, customizer, **kwargs):

        # customization is done both in the form (here) and in the template

        inheritance_data = kwargs.pop("inheritance_data", None)
        self.customizer = customizer

        from .forms_edit import create_new_edit_subforms_from_models, create_existing_edit_subforms_from_models, create_edit_subforms_from_data

        property = self.instance

        value_field_name = self.get_value_field_name()
        value_field = self.fields[value_field_name]

        # the stuff that gets done specifically for atomic/enumeration/relationship fields can be hard-coded

        if customizer.field_type == MetadataFieldTypes.ATOMIC:
            atomic_type = customizer.atomic_type
            if atomic_type:
                atomic_field = self.fields["atomic_value"]
                if atomic_type != MetadataAtomicFieldTypes.DEFAULT:
                    custom_widget_class = METADATA_ATOMICFIELD_MAP[atomic_type][0]
                    custom_widget_args = METADATA_ATOMICFIELD_MAP[atomic_type][1]
                    atomic_field.widget = custom_widget_class(**custom_widget_args)
                    if atomic_type == MetadataAtomicFieldTypes.TEXT:
                        # force TextInput to be a pretty size, as per #82
                        set_field_widget_attributes(atomic_field, {"cols": "40", "rows": "5", })
                update_field_widget_attributes(atomic_field, {"class": atomic_type.lower()})

        elif customizer.field_type == MetadataFieldTypes.ENUMERATION:
            custom_widget_attributes = {"class": "multiselect"}
            all_enumeration_choices = customizer.enumerate_choices()
            if customizer.enumeration_nullable:
                all_enumeration_choices += NULL_CHOICE
                custom_widget_attributes["class"] += " nullable"
            if customizer.enumeration_open:
                all_enumeration_choices += OTHER_CHOICE
                custom_widget_attributes["class"] += " open"
            if customizer.enumeration_multi:
                custom_widget_attributes["class"] += " multiple"
                self.fields["enumeration_value"].set_choices(all_enumeration_choices, multi=True)
            else:
                custom_widget_attributes["class"] += " single"
                # all_enumeration_choices = EMPTY_CHOICE + all_enumeration_choices
                self.fields["enumeration_value"].set_choices(all_enumeration_choices, multi=False)
            update_field_widget_attributes(self.fields["enumeration_value"], custom_widget_attributes)

        elif customizer.field_type == MetadataFieldTypes.RELATIONSHIP:
            if customizer.relationship_show_subform:
                # TODO: BEGIN THE REALLY HORRIBLE UGLY PIECE OF CODE I DON'T LIKE
                subform_customizer = customizer.subform_customizer

                (model_customizer, standard_category_customizers, standard_property_customizers, nested_scientific_category_customizers, nested_scientific_property_customizers) = \
                    MetadataCustomizer.get_existing_customizer_set(subform_customizer, MetadataVocabulary.objects.none())
                standard_property_proxies = [standard_property_customizer.proxy for standard_property_customizer in standard_property_customizers]
                scientific_property_customizers = get_joined_keys_dict(nested_scientific_property_customizers)
                scientific_property_proxies = {key: [spc.proxy for spc in value] for key, value in scientific_property_customizers.items()}
                # for vocabulary_key,scientific_property_customizer_dict in nested_scientific_property_customizers.iteritems():
                #     for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
                #         model_key = u"%s_%s" % (vocabulary_key, component_key)
                #         scientific_property_customizers[model_key] = scientific_property_customizer_list
                #         scientific_property_proxies[model_key] = [scientific_property_customizer.proxy for scientific_property_customizer in scientific_property_customizer_list]


                # determine if the subforms ought to be a 1-to-1 (ie: a subformset w/ 1 item) or a m-to-m (ie: a subformset w/ multiple items)
                # even though the underlying model uses a m-to-m field, this restricts how many items users can add
                render_as_formset = customizer.render_as_formset()
                subform_min, subform_max = [int(val) if val != "*" else val for val in customizer.relationship_cardinality.split("|")]

                if property.pk:

                    models = property.relationship_value.all()
                    if models:
                        (models, standard_properties, scientific_properties) = \
                            MetadataModel.get_existing_subrealization_set(models, model_customizer)

                        if not self.is_bound:
                            (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
                                create_existing_edit_subforms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix=self.prefix, subform_min=subform_min, subform_max=subform_max, inheritance_data=inheritance_data)
                        else:
                            (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
                                create_edit_subforms_from_data(self.data, models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix=self.prefix, subform_min=subform_min, subform_max=subform_max, inheritance_data=inheritance_data)

                            self.subform_validity = all(validity)
                            if self.subform_validity:
                                for standard_properties_formset in standard_properties_formsets.values():
                                    standard_properties_formset.force_clean()

                    else:
                        (models, standard_properties, scientific_properties) = \
                            MetadataModel.get_new_subrealization_set(subform_customizer.project, subform_customizer.version, subform_customizer.proxy, standard_property_proxies, scientific_property_proxies, model_customizer, MetadataVocabulary.objects.none(), self.parent.vocabulary_key, self.parent.component_key )

                        if not self.is_bound:
                            (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
                                create_new_edit_subforms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix=self.prefix, subform_min=subform_min, subform_max=subform_max, inheritance_data=inheritance_data)
                        else:
                            (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
                                create_edit_subforms_from_data(self.data, models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix=self.prefix, subform_min=subform_min, subform_max=subform_max, inheritance_data=inheritance_data)

                            self.subform_validity = all(validity)
                            if self.subform_validity:
                                for standard_properties_formset in standard_properties_formsets.values():
                                    standard_properties_formset.force_clean()

                else:
                    (models, standard_properties, scientific_properties) = \
                        MetadataModel.get_new_subrealization_set(subform_customizer.project, subform_customizer.version, subform_customizer.proxy, standard_property_proxies, scientific_property_proxies, model_customizer, MetadataVocabulary.objects.none(), self.parent.vocabulary_key, self.parent.component_key )

                    if not self.is_bound:
                        (model_formset, standard_properties_formsets, scientific_properties_formsets) = \
                            create_new_edit_subforms_from_models(models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix=self.prefix, subform_min=subform_min, subform_max=subform_max, inheritance_data=inheritance_data)

                    else:
                        (validity, model_formset, standard_properties_formsets, scientific_properties_formsets) = \
                            create_edit_subforms_from_data(self.data, models, model_customizer, standard_properties, standard_property_customizers, scientific_properties, scientific_property_customizers, subform_prefix=self.prefix, subform_min=subform_min, subform_max=subform_max, inheritance_data=inheritance_data)

                        self.subform_validity = all(validity)
                        if self.subform_validity:
                            for standard_properties_formset in standard_properties_formsets.values():
                                standard_properties_formset.force_clean()

                self.subform_tuple = (subform_customizer, model_formset, standard_properties_formsets, scientific_properties_formsets)

                # TODO: END THE REALLY HORRIBLE UGLY PIECE OF CODE I DON'T LIKE

        # the other stuff is common to all and can be generic (ie: use 'value_field_name')

        value_field.help_text = customizer.documentation

        if customizer.required:
            update_field_widget_attributes(value_field, {"class": "required"})
        else:
            update_field_widget_attributes(value_field, {"class": "optional"})

        if not customizer.editable:
            update_field_widget_attributes(value_field, {"class": "readonly", "readonly": "readonly"})

        if customizer.inherited:
            update_field_widget_attributes(value_field, {"class": "inherited"})
            if customizer.enumeration_open:
                update_field_widget_attributes(self.fields["enumeration_other_value"], {"class": "inherited"})
            if inheritance_data:
                self.inherit(inheritance_data)

        if customizer.suggestions:
            update_field_widget_attributes(value_field, {"class": "autocomplete"})
            update_field_widget_attributes(value_field, {"suggestions": customizer.suggestions})

    def inherit(self, inheritance_data):
        """
        updates fields w/ inheritance_data, removing data as it goes
        then re-caches the new smaller inheritance_data
        :param inheritance_data: dictionary of all data sent from the client
        :return:
        """

        customizer = self.customizer
        assert customizer.inherited

        value_field_name = self.get_value_field_name()
        value_field_id = self.get_id_from_field_name(value_field_name)

        # I thought that I would have to treat bound forms differently,
        # but the fact is that the only reason to be in this fn
        # is if the form is unloaded; and if that's the case,
        # then the clean fns don't bother checking data instead they use initial

        if customizer.field_type != MetadataFieldTypes.ENUMERATION:

            if value_field_id in inheritance_data:
                inherited_value = inheritance_data.pop(value_field_id)
                if customizer.atomic_type == MetadataAtomicFieldTypes.BOOLEAN:
                    self.initial[value_field_name] = inherited_value == u"true"
                else:
                    self.initial[value_field_name] = inherited_value

        else:  # customizer.field_type == MetadataFieldTypes.ENUMERATION

            ignore_other = False
            inherited_enumeration_values = {k: v == u"true" for k, v in inheritance_data.items() if k.startswith(value_field_id)}
            if inherited_enumeration_values:
                ordered_inherited_enumeration_values = OrderedDict(sorted(inherited_enumeration_values.items(), key=lambda value: value[0]))
                enumeration_choices = self.fields[value_field_name].choices
                inherited_values = []
                for i, ordered_inherited_enumeration_value in enumerate(ordered_inherited_enumeration_values.items()):
                    # TODO: IS THERE AN ASSERTION I USE HERE
                    # TODO: TO MAKE SURE ordered_inherited_enumeration_values & enumeration_choices
                    # TODO: ARE IN THE SAME ORDER?
                    if ordered_inherited_enumeration_value[1]:
                        inherited_values.append(enumeration_choices[i][0])
                        if enumeration_choices[i] == NULL_CHOICE[0]:
                            ignore_other = True
                    inheritance_data.pop(ordered_inherited_enumeration_value[0])
                if customizer.enumeration_multi:
                    self.initial[value_field_name] = inherited_values
                else:
                    if len(inherited_values):
                        inherited_value = inherited_values[0]
                    else:
                        inherited_value = None
                    self.initial[value_field_name] = inherited_value

            if customizer.enumeration_open:
                other_field_name = "enumeration_other_value"
                other_field_id = self.get_id_from_field_name(other_field_name)
                if other_field_id in inheritance_data:
                    inherited_value = inheritance_data.pop(other_field_id)
                    if not ignore_other:
                        # only inherit "other" if NONE is not also in inherited_values
                        self.initial[other_field_name] = inherited_value

        # re-set the inheritance_data now that some of it has been used and removed
        set_cached_inheritance_data(inheritance_data)

    def is_valid(self, loaded=True):

        validity = super(MetadataAbstractStandardPropertyForm, self).is_valid(loaded=loaded)

        field_type = self.get_current_field_value("field_type")
        if field_type == MetadataFieldTypes.RELATIONSHIP:
            if self.customizer.relationship_show_subform:
                validity = validity and self.subform_validity

        return validity

    def get_subform_tuple(self):
        field_type = self.get_current_field_value("field_type")
        assert(field_type == MetadataFieldTypes.RELATIONSHIP)
        assert(len(self.subform_tuple) == 4)
        return self.subform_tuple

    def get_subform_customizer(self):
        subform_tuple = self.get_subform_tuple()
        return subform_tuple[0]

    def get_model_subformset(self):
        subform_tuple = self.get_subform_tuple()
        model_subformset = subform_tuple[1]
        # (thought I could get away w/ just returning the single form)
        # (since there should only ever be 1 form in this formset)
        # (but b/c I'm dealing w/ a formset, I need the whole thing)
        # (in order to get access to the management form)
        return model_subformset

    def get_standard_properties_subformsets(self):
        subform_tuple = self.get_subform_tuple()
        return subform_tuple[2]

    def get_scientific_properties_subformsets(self):
        subform_tuple = self.get_subform_tuple()
        return subform_tuple[3]


class MetadataStandardPropertyForm(MetadataAbstractStandardPropertyForm):

    class Meta:
        model = MetadataStandardProperty
        fields = [
            # hidden fields...
            "proxy", "field_type", "name", "order", "is_label", "id",
            # value fields...
            "atomic_value", "enumeration_value", "enumeration_other_value", "relationship_value",
        ]

    # set of fields that will be the same for all members of a formset; allows me to cache the query (for relationship fields)
    cached_fields = []

    _value_fields = ["atomic_value", "enumeration_value", "enumeration_other_value", "relationship_value", ]
    _hidden_fields = ["proxy", "field_type", "name", "order", "is_label", "id", ]

    def has_changed(self):
        # StandardProperties at this "top-level" (ie: not in a subform) should always be saved
        # since top-level models are always saved and a model w/out its full compliment of standard properties doesn't make sense
        # For StandardProperties which are nested w/in subforms (MetadataStandardPropertySubForm), we only want to save them if they
        # have changed.  So I use the show_hidden_initial attribute to track this on the visible fields and do not override has_changed
        return True


class MetadataStandardPropertySubForm(MetadataAbstractStandardPropertyForm):

    class Meta:
        model = MetadataStandardProperty
        fields = [
            # hidden fields...
            "proxy", "field_type", "name", "order", "is_label", "id",
            # value fields...
            "atomic_value", "enumeration_value", "enumeration_other_value", "relationship_value",
        ]

    # set of fields that will be the same for all members of a formset; allows me to cache the query (for relationship fields)
    cached_fields = []

    _value_fields = ["atomic_value", "enumeration_value", "enumeration_other_value", "relationship_value", ]
    _hidden_fields = ["proxy", "field_type", "name", "order", "is_label", "id", ]

    def __init__(self, *args, **kwargs):

        super(MetadataStandardPropertySubForm, self).__init__(*args, **kwargs)

        # this is really really important!
        # this ensures that there is something to compare field data against so that I can truly tell is the model has changed
        # [http://stackoverflow.com/questions/11710845/in-django-1-4-do-form-has-changed-and-form-changed-data-which-are-undocument]
        for field_name in self._value_fields:
            # see comment above (MetadataStandardPropertyForm.has_changed) for an explanation of this line
            self.fields[field_name].show_hidden_initial = True

    def force_clean(self):
        # alright, this is very confusing...
        # in __init__ I add hidden initial fields to let me know if something has changed
        # that works fine when I am determining whether or not to save a subform
        # but, subform_has_changed uses the boolean "any" to work out whether to save the full set
        # for those subforms in the subformset that have not changed, they will have not run a full clean
        # therefore their "cleaned_data" will be emtpy
        # therefore saving them will create properties w/ emtpy content
        # so this function exists to do what full_clean would have done if has_changed had returned True
        # I call it in save_valid_subforms below
        # [code is taken from "full_clean" in django.forms.forms.BaseForm.full_clean()]
        self._clean_fields(loaded=self.is_loaded())
        self._clean_form()
        self._post_clean()

    def has_changed(self):
        return True


class MetadataStandardPropertyInlineFormSet(MetadataEditingInlineFormSet):

    def get_number_of_forms(self):
        return self.number_of_properties

    # def _construct_form(self, i, **kwargs):
    #
    #     if self.is_bound and i < self.initial_form_count():
    #         # Import goes here instead of module-level because importing
    #         # django.db has side effects.
    #         from django.db import connections
    #         pk_key = "%s-%s" % (self.add_prefix(i), self.model._meta.pk.name)
    #         pk = self.data[pk_key]
    #         pk_field = self.model._meta.pk
    #         pk = pk_field.get_db_prep_lookup('exact', pk,
    #             connection=connections[self.get_queryset().db])
    #         if isinstance(pk, list):
    #             pk = pk[0]
    #         kwargs['instance'] = self._existing_object(pk)
    #     if i < self.initial_form_count() and not kwargs.get('instance'):
    #
    #         try:
    #             kwargs['instance'] = self.get_queryset()[i]
    #         except IndexError:
    #             # if this formset has changed based on add/delete via AJAX
    #             # then the underlying queryset may not have updated
    #             # if so - since I've already worked out the pk above - just get the model directly
    #             kwargs['instance'] = MetadataStandardProperty.objects.get(pk=pk)
    #
    #     if i >= self.initial_form_count() and self.initial_extra:
    #         # Set initial values for extra forms
    #         try:
    #             kwargs['initial'] = self.initial_extra[i-self.initial_form_count()]
    #         except IndexError:
    #             pass
    #     form = super(MetadataStandardPropertyInlineFormSet, self)._construct_form(i, **kwargs)
    #
    #     if self.save_as_new:
    #         # Remove the primary key from the form's data, we are only
    #         # creating new instances
    #         form.data[form.add_prefix(self._pk_field.name)] = None
    #
    #         # Remove the foreign key from the form's data
    #         form.data[form.add_prefix(self.fk.name)] = None
    #
    #     # Set the fk value here so that the form can do its validation.
    #     setattr(form.instance, self.fk.get_attname(), self.instance.pk)
    #
    #     # this speeds up loading time
    #     # (see "cached_fields" attribute in the form class)
    #     for cached_field_name in form.cached_fields:
    #         cached_field = form.fields[cached_field_name]
    #         cached_field_key = u"%s_%s" % (self.prefix, cached_field_name)
    #         cached_field.cache_choices = True
    #
    #         if hasattr(cached_field,"_choices"):
    #             # it's a ChoiceField or something similar
    #             cached_choices = getattr(self, '_cached_choices_%s' % (cached_field_key), None)
    #             if cached_choices is None:
    #                 cached_choices = list(cached_field.choices)
    #                 setattr(self, "_cached_choices_%s" % (cached_field_key), cached_choices)
    #             cached_field.choices = cached_choices
    #
    #         # this is not working for modelchoicefields
    #         # instead I use a custom "CachedModelChoiceField" directly in the form
    #         # elif hasattr(cached_field,"_queryset"):
    #         #     # it's a ModelChoiceField or something similar
    #         #     cached_queryset = getattr(self, '_cached_queryset_%s' % (cached_field_key), None)
    #         #     if cached_queryset is None:
    #         #         cached_queryset = cached_field.queryset
    #         #         setattr(self, "_cached_queryset_%s" % (cached_field_key), cached_queryset)
    #         #     cached_field.queryset = cached_queryset
    #
    #     return form

    def force_clean(self):
        for form in self.forms:
            form.force_clean()


def MetadataStandardPropertyInlineFormSetFactory(*args, **kwargs):
    _DEFAULT_PREFIX = "_standard_properties"

    _prefix = kwargs.pop("prefix", "") + _DEFAULT_PREFIX
    _data = kwargs.pop("data", None)
    _initial = kwargs.pop("initial", [])
    _queryset = kwargs.pop("queryset", MetadataStandardProperty.objects.none())
    _instance = kwargs.pop("instance")
    _customizers = kwargs.pop("customizers", None)
    _inheritance_data = kwargs.pop("inheritance_data", None)

    new_kwargs = {
        "can_delete": False,
        "extra": kwargs.pop("extra", 0),
        "formset": MetadataStandardPropertyInlineFormSet,
        "form": MetadataStandardPropertyForm,
        "fk_name": "model"  # required in-case there are more than 1 fk's to "metadatamodel"; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)

    _formset = inlineformset_factory(MetadataModel, MetadataStandardProperty, *args, **new_kwargs)
    _formset.form = staticmethod(curry(MetadataStandardPropertyForm, customizers=_customizers, parent=_instance, inheritance_data=_inheritance_data))

    if _initial:
        _formset.number_of_properties = len(_initial)
    elif _queryset:
        _formset.number_of_properties = len(_queryset)
    elif _data:
        # see the comment in MetadataScientificPropertyInlineFormSetFactory (in "forms_edit_scientific_properties.py"
        # for an explanation of why get is used w/ a default value;
        # this is unlikely to matter for standard properties, but I've added it here for future-proofing
        total_forms_key = u"%s-TOTAL_FORMS" % _prefix
        _formset.number_of_properties = int(_data.get(total_forms_key, 0))
    else:
        _formset.number_of_properties = 0

    if _data:
        return _formset(_data, initial=_initial, instance=_instance, prefix=_prefix)

    # notice how both "queryset" and "initial" are passed
    # this handles both existing and new models
    # (in the case of existing models, "queryset" is used)
    # (in the case of new models, "initial" is used)
    # but both arguments are needed so that "extra" is used properly
    return _formset(queryset=_queryset, initial=_initial, instance=_instance, prefix=_prefix)


def MetadataStandardPropertyInlineSubFormSetFactory(*args, **kwargs):
    _DEFAULT_PREFIX = "_standard_properties"

    _prefix = kwargs.pop("prefix", "") + _DEFAULT_PREFIX
    _data = kwargs.pop("data", None)
    _initial = kwargs.pop("initial", [])
    _queryset = kwargs.pop("queryset", MetadataStandardProperty.objects.none())
    _instance = kwargs.pop("instance")
    _customizers = kwargs.pop("customizers", None)
    _inheritance_data = kwargs.pop("inheritance_data", None)

    new_kwargs = {
        "can_delete": True,
        "extra": kwargs.pop("extra", 0),
        "formset": MetadataStandardPropertyInlineFormSet,
        "form": MetadataStandardPropertySubForm,
        "fk_name": "model"  # required in-case there are more than 1 fk's to "metadatamodel"; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)

    _formset = inlineformset_factory(MetadataModel, MetadataStandardProperty, *args, **new_kwargs)
    if _customizers:
        # no longer dealing w/ iterators and making sure everything is in the same order
        # now I just pass the entire set of customizers and work out which one to use in the __init__ method
        #_formset.customizers = iter(_customizers)
        _formset.form = staticmethod(curry(MetadataStandardPropertySubForm, customizers=_customizers, parent=_instance, inheritance_data=_inheritance_data))

    if _initial:
        _formset.number_of_properties = len(_initial)
    elif _queryset:
        _formset.number_of_properties = len(_queryset)
    elif _data:
        # see the comment in MetadataScientificPropertyInlineFormSetFactory (in "forms_edit_scientific_properties.py"
        # for an explanation of why get is used w/ a default value;
        # this is unlikely to matter for standard properties, but I've added it here for future-proofing
        total_forms_key = u"%s-TOTAL_FORMS" % _prefix
        _formset.number_of_properties = int(_data.get(total_forms_key, 0))
    else:
        _formset.number_of_properties = 0

    if _data:
        return _formset(_data, initial=_initial, instance=_instance, prefix=_prefix)

    # notice how both "queryset" and "initial" are passed
    # this handles both existing and new models
    # (in the case of existing models, "queryset" is used)
    # (in the case of new models, "initial" is used)
    # but both arguments are needed so that "extra" is used properly
    return _formset(queryset=_queryset, initial=_initial, instance=_instance, prefix=_prefix)
