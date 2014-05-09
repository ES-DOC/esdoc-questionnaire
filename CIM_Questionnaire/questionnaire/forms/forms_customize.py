
####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Dec 28, 2013 4:56:56 PM"

"""
.. module:: forms_customize

Summary of module goes here

"""

from django.forms import *

from django.forms.models import BaseInlineFormSet
from django.forms.models import inlineformset_factory

from django.template.defaultfilters import slugify
from django.utils.functional        import curry

from django.forms.util  import ErrorList
from collections        import OrderedDict

from questionnaire.utils        import *
from questionnaire.models       import *
from questionnaire.fields       import MetadataFieldTypes, EMPTY_CHOICE
from questionnaire.forms        import MetadataCustomizerForm


class MetadataModelCustomizerForm(ModelForm):

    class Meta:
        model   = MetadataModelCustomizer
        
        fields  = [
                    # hidden fields...
                    "proxy","project","version","vocabulary_order",
                    # customizer fields...
                    "name","description","vocabularies","default",
                    # document fields...
                    "model_title","model_description","model_show_all_categories","model_show_all_properties","model_show_hierarchy","model_hierarchy_name","model_root_component",
                    # other fields...
                    "standard_categories_content","standard_categories_tags",
                  ]

    hidden_fields       = ("proxy","project","version","vocabulary_order",)
    customizer_fields   = ("name","description","default","vocabularies",)
    document_fields     = ("model_title","model_description","model_show_all_categories","model_show_all_properties","model_show_hierarchy","model_hierarchy_name","model_root_component",)
    
    standard_categories_content = CharField(required=False,widget=Textarea)                 # the categories themselves
    standard_categories_tags    = CharField(label="Available Categories",required=False)    # the field used by the tagging widget
    standard_categories_tags.help_text = "This widget contains the standard set of categories associated with the CIM version. If this set is unsuitable, or empty, then the categorization should be updated. Please contact your administrator."

    # scientific categories are done on a per-cv / per-component basis in __init__ below

    standard_categories_to_process = []
    scientific_categories_to_process = {}
    
    def get_hidden_fields(self):
        fields = list(self)
        return [field for field in fields if field.name in self.hidden_fields]
    
    def get_customizer_fields(self):
        fields = list(self)
        return [field for field in fields if field.name in self.customizer_fields]

    def get_document_fields(self):
        fields = list(self)
        return [field for field in fields if field.name in self.document_fields]
   
    def __init__(self,*args,**kwargs):
        is_subform = kwargs.pop("is_subform",False)
        
        super(MetadataModelCustomizerForm,self).__init__(*args,**kwargs)

        #import ipdb; ipdb.set_trace()
###        model_customizer = self.instance

        
        
        if is_subform:
            #update_field_widget_attributes(self.fields["name"],{"class":"readonly","readonly":"readonly"})
            #update_field_widget_attributes(self.fields["default"],{"class":"readonly","readonly":"readonly"})
            del(self.fields["name"])
            del(self.fields["default"])
            del(self.fields["vocabularies"])
            del(self.fields["vocabulary_order"])
            del(self.fields["model_show_hierarchy"])
            del(self.fields["model_root_component"])
            all_vocabularies = []
        else:
###            all_vocabularies = model_customizer.project.vocabularies.filter(document_type__iexact=model_customizer.proxy.name)
            all_vocabularies = MetadataVocabulary.objects.filter(pk__in=self.data["vocabularies"])


            # doing this on document load in javascript
            #if model_customizer.pk:
            #    vocabulary_order = [int(order) for order in model_customizer.vocabulary_order.split(',')]
            #    sorted(all_vocabularies, key=lambda vocabulary: vocabulary_order.index(vocabulary.pk))
            self.fields["vocabularies"].queryset = all_vocabularies

###            if not model_customizer.pk:
###                self.initial["vocabularies"] = [vocabulary.pk for vocabulary in all_vocabularies]
###                self.initial["vocabulary_order"] = ",".join([str(vocabulary.pk) for vocabulary in all_vocabularies])
            update_field_widget_attributes(self.fields["vocabularies"],{"class":"multiselect"})
            update_field_widget_attributes(self.fields["model_show_hierarchy"],{"class":"enabler"})
            set_field_widget_attributes(self.fields["model_show_hierarchy"],{"onchange":"enable(this,'true',['model_root_component','model_hierarchy_name']);",})

        set_field_widget_attributes(self.fields["description"],{"cols":"60","rows":"4"})

        set_field_widget_attributes(self.fields["model_description"],{"cols":"60","rows":"4"})

###        if model_customizer.pk:
###            standard_category_customizers = model_customizer.standard_property_category_customizers.all()
###        else:
###            standard_category_proxies = model_customizer.proxy.get_standard_category_proxies()
###            standard_category_customizers = [MetadataStandardCategoryCustomizer(model_customizer=model_customizer,proxy=proxy) for proxy in standard_category_proxies]
###            for standard_category_customizer in standard_category_customizers:
###                standard_category_customizer.reset()
###
        
###        self.fields["standard_categories_content"].initial  = JSON_SERIALIZER.serialize(standard_category_customizers)
###        self.fields["standard_categories_tags"].initial     = "|".join([category.name for category in standard_category_customizers])
        update_field_widget_attributes(self.fields["standard_categories_tags"],{"class":"tags"})

        for vocabulary in all_vocabularies:
            vocabulary_key = slugify(vocabulary.name)
            for component_proxy in vocabulary.component_proxies.all():
                component_key = slugify(component_proxy.name)
                scientific_categories_content_field_name                = vocabulary_key+"_"+component_key + "_scientific_categories_content"
                scientific_categories_tags_field_name                   = vocabulary_key+"_"+component_key + "_scientific_categories_tags"
                self.fields[scientific_categories_content_field_name]   = CharField(required=False,widget=Textarea)               # the categories themselves
                self.fields[scientific_categories_tags_field_name]      = CharField(label="Available Categories",required=False)  # the field used by the tagging widget
                self.fields[scientific_categories_tags_field_name].help_text = "This widget contains the set of categories associated with this component of this CV.  Users can add to this set via this customization."
###
###
###                if model_customizer.pk:
###                    scientific_category_customizers = MetadataScientificCategoryCustomizer.objects.filter(model_customizer=model_customizer,vocabulary_key=vocabulary_key,component_key=component_key)
###                else:
###                    scientific_category_proxies = component_proxy.categories.all()
###                    scientific_category_customizers = [MetadataScientificCategoryCustomizer(model_customizer=model_customizer,proxy=proxy) for proxy in scientific_category_proxies]
###                    for scientific_category_customizer in scientific_category_customizers:
###                        scientific_category_customizer.reset()
###
###                self.fields[scientific_categories_content_field_name].initial  = JSON_SERIALIZER.serialize(scientific_category_customizers)
###                self.fields[scientific_categories_tags_field_name].initial     = "|".join([category.name for category in scientific_category_customizers])
                update_field_widget_attributes(self.fields[scientific_categories_tags_field_name],{"class":"tags"})
        
        
    def clean_default(self):
        cleaned_data = self.cleaned_data
        default = cleaned_data.get("default") # using the get fn instead of directly accessing the dictionary in-case the field is missing, as w/ subform customizers
        if default:
            other_customizer_filter_kwargs = {
                "default"   : True,
                "proxy"     : cleaned_data["proxy"],
                "project"   : cleaned_data["project"],
                "version"   : cleaned_data["version"],
            }
            other_customizers = MetadataModelCustomizer.objects.filter(**other_customizer_filter_kwargs)
            this_customizer = self.instance
            if this_customizer.pk:
                other_customizers = other_customizers.exclude(pk=this_customizer.pk)
            if other_customizers.count() != 0:
                raise ValidationError("A default customizer already exists.")
            
        return default

    def clean(self):
        # calling the parent class's clean fun automatically sets a
        # flag that forces unique (and unique_together) validation
        super(MetadataModelCustomizerForm,self).clean()
        cleaned_data = self.cleaned_data

        # categories have to be saved separately
        # since they are manipulated via a JQuery tagging widget
        # and therefore aren't part of the form

        # NOTE: MAKE SURE NOT TO ACCESS THE CATEGORY_CONTENT FIELDS BEFORE DESERIALIZING THEM, AS THIS CAUSES ERRORS LATER ON
        self.standard_categories_to_process[:] = [] # fancy way of clearing the list, making sure any references are also updated
        for deserialized_standard_category_customizer in serializers.deserialize("json", cleaned_data["standard_categories_content"],ignorenonexistent=True):
            self.standard_categories_to_process.append(deserialized_standard_category_customizer)
#            standard_category_customizer = deserialized_standard_category_customizer.object
#            if standard_category_customizer.pending_deletion:
#                deserialized_standard_category_customizer.delete()
#            else:
#                deserialized_standard_category_customizer.save()
        try:
            for vocabulary in self.cleaned_data["vocabularies"]:
                vocabulary_key = slugify(vocabulary.name)
                self.scientific_categories_to_process[vocabulary_key] = {}
                for component_proxy in vocabulary.component_proxies.all():
                    component_key = slugify(component_proxy.name)
                    scientific_categories_content_field_name = vocabulary_key+"_"+component_key+"_scientific_categories_content"
                    self.scientific_categories_to_process[vocabulary_key][component_key] = []
                    for deserialized_scientific_category_customizer in serializers.deserialize("json", self.data[scientific_categories_content_field_name],ignorenonexistent=True):
                        self.scientific_categories_to_process[vocabulary_key][component_key].append(deserialized_scientific_category_customizer)
    #                   scientific_category_customizer = deserialized_scientific_category_customizer.object
    #                   if scientific_category_customizer.pending_deletion:
    #                       deserialized_scientific_category_customizer.delete()
    #                   else:
    #                       deserialized_scientific_category_customizer.save()
        except KeyError:
            # this takes care of the case when this being called on a subform
            pass

        return cleaned_data
        
    def validate_unique(self):        
        model_customizer = self.instance
        try:
            model_customizer.validate_unique()
        except ValidationError, e:
            # if there is a validation error then apply that error to the individual fields
            # so it shows up in the form and is rendered nicely via JQuery
            unique_together_fields_list = model_customizer.get_unique_together()
            for unique_together_fields in unique_together_fields_list:
                if any(field.lower() in " ".join(e.messages).lower() for field in unique_together_fields):
                    msg = "Customizer with this %s already exists" % (", ".join(unique_together_fields))
                    for unique_together_field in unique_together_fields:
                        self.errors[unique_together_field] = msg

class MetadataPropertyCustomizerInlineFormSet(BaseInlineFormSet):

    number_of_properties = 0
    
    # just using this class to automatically sort the forms based on the field order

    def __iter__(self):
        """Yields the forms in the order they should (initially) be rendered"""
        forms = list(self.forms)
        try:
            forms.sort(key = lambda x: x.initial["order"])
        except KeyError:
            forms.sort(key = lambda x: x.data["%s-order"%(x.prefix)])
        return iter(forms)

    def __getitem__(self, index):
        """Returns the form at the given index, based on the rendering order"""
        forms = list(self.forms)
        try:
            forms.sort(key = lambda x: x.initial["order"])
        except KeyError:
            forms.sort(key = lambda x: x.data["%s-order"%(x.prefix)])
        return forms[index]

    # also using it to cache fk or m2m fields to avoid needless (on the order of 30K!) db hits

    def _construct_form(self, i, **kwargs):

        form = super(MetadataPropertyCustomizerInlineFormSet,self)._construct_form(i,**kwargs)

        for cached_field_name in form.cached_fields:
            cached_field = form.fields[cached_field_name]
            cached_field_key = u"%s_%s" % (self.prefix,cached_field_name)
            cached_field.cache_choices = True
            choices = getattr(self, '_cached_choices_%s'%(cached_field_key), None)
            if choices is None:
                choices = list(cached_field.choices)
                setattr(self, '_cached_choices_%s'%(cached_field_key), choices)
            cached_field.choice_cache = choices

        return form


class MetadataStandardPropertyCustomizerForm(ModelForm):

    class Meta:
        model = MetadataStandardPropertyCustomizer
        fields  = [
                # hidden fields...
                # TODO: WHY DID I HAVE TO EXPLICITLY ADD ID HERE?!?
                "field_type","proxy","category","id",
                # header fields...
                "name","category_name","order",
                # common fields...
                "displayed", "required", "editable", "unique", "verbose_name", "default_value", "documentation","inline_help","inherited",
                # atomic fields...
                "atomic_type","suggestions",
                # enumeration fields...
                "enumeration_choices","enumeration_default","enumeration_open","enumeration_multi","enumeration_nullable",
                # relationship fields...
                "relationship_cardinality","relationship_show_subform",
              ]

    category_name = CharField(label="Category",required=False)
    category      = ChoiceField(required=False)

    type = None # this is set in __init__ below


    hidden_fields       = ("field_type","proxy","category","id",)
    header_fields       = ("name","category_name","order")
    common_fields       = ("displayed","required","editable","unique","verbose_name","documentation","inline_help","default_value","inherited")
    atomic_fields       = ("atomic_type","suggestions",)
    enumeration_fields  = ("enumeration_choices","enumeration_default","enumeration_open","enumeration_multi","enumeration_nullable",)
    relationship_fields = ("relationship_cardinality","relationship_show_subform",)


    # set of fields that will be the same for all members of a formset; thus I can cache the query (for relationship fields)
    cached_fields       = ["proxy","field_type","enumeration_choices","enumeration_default"]

    # TODO: IS IT FASTER TO DO THIS
    #return [field for field in self if field.name in field_list]
    # THAN THIS
    # fields = list(self)
    # ?

    def get_hidden_fields(self):
        fields = list(self)
        return [field for field in fields if field.name in self.hidden_fields]

    def get_header_fields(self):
        fields = list(self)
        return [field for field in fields if field.name in self.header_fields]

    def get_atomic_fields(self):
        fields = list(self)

        common_fields = [field for field in fields if field.name in self.common_fields]
        atomic_fields = [field for field in fields if field.name in self.atomic_fields]

        all_fields = common_fields + atomic_fields
        all_fields.sort(key=lambda field: fields.index(field))
        return all_fields

    def get_enumeration_fields(self):
        fields = list(self)

        common_fields = [field for field in fields if field.name in self.common_fields]
        atomic_fields = [field for field in fields if field.name in self.enumeration_fields]

        all_fields = common_fields + atomic_fields
        all_fields.sort(key=lambda field: fields.index(field))
        return all_fields

    def get_relationship_fields(self):
        fields = list(self)

        common_fields = [field for field in fields if field.name in self.common_fields]
        atomic_fields = [field for field in fields if field.name in self.relationship_fields]

        all_fields = common_fields + atomic_fields
        all_fields.sort(key=lambda field: fields.index(field))
        return all_fields

    def __init__(self,*args,**kwargs):
        # category_choices was passed in via curry() in the factory function below
        category_choices = kwargs.pop("category_choices",[])

        super(MetadataStandardPropertyCustomizerForm,self).__init__(*args,**kwargs)

        property_customizer = self.instance

        # when initializing formsets,
        # the fields aren't always setup in the underlying model
        # so this gets them either from the request (in the case of POST) or initial (in the case of GET)
        property_data = {}
        if self.data:
            # POST; (form already had data) request was passed into constructor
            # (not sure why I can't do this in a list comprehension)
            for key,value in self.data.iteritems():
                if key.startswith(self.prefix+"-"):
                    property_data[key.split(self.prefix+"-")[1]] = value
        else:
            # GET; initial was passed into constructor
            property_data = self.initial

        self.type = property_data["field_type"]

        if self.type == MetadataFieldTypes.ATOMIC:
            update_field_widget_attributes(self.fields["atomic_type"],{"class":"multiselect"})

        elif self.type == MetadataFieldTypes.ENUMERATION:

            all_enumeration_choices = property_customizer.get_field("enumeration_choices").get_choices()
            self.fields["enumeration_choices"].widget = SelectMultiple(choices=all_enumeration_choices)
            self.fields["enumeration_default"].widget = SelectMultiple(choices=all_enumeration_choices)
            if not property_customizer.pk:
                enumeration_choices = [choice[0] for choice in all_enumeration_choices]
                enumeration_default = []
            else:
                if "enumeration_choices" in property_data:
                    enumeration_choices = property_data["enumeration_choices"].split("|")
                else:
                    enumeration_choices = []
                if "enumeration_default" in property_data:
                    enumeration_default = property_data["enumeration_default"].split("|")
                else:
                    enumeration_default = []
            self.initial["enumeration_choices"] = enumeration_choices
            self.initial["enumeration_default"] = enumeration_default
            # TODO: I CANNOT GET THE MULTISELECT PLUGIN TO WORK W/ THE RESTRICT_OPTIONS FN
            #update_field_widget_attributes(self.fields["enumeration_choices"],{"class":"multiselect","onchange":"restrict_options(this,['%s-enumeration_default']);"%(self.prefix)})
            update_field_widget_attributes(self.fields["enumeration_choices"],{"class":"multiselect"})
            update_field_widget_attributes(self.fields["enumeration_default"],{"class":"multiselect"})

        elif self.type == MetadataFieldTypes.RELATIONSHIP:
            update_field_widget_attributes(self.fields["relationship_show_subform"],{"class":"enabler","onchange":"enable_customize_subform_button(this);"})
            if not property_customizer.pk:
                update_field_widget_attributes(self.fields["relationship_show_subform"],{"class":"readonly","readonly":"readonly"})

        else:
            msg = "invalid field type for standard property: '%s'" % (self.type)
            raise QuestionnaireError(msg)

        category = property_data["category"]
        self.fields["category"].choices = category_choices
        if isinstance(category,MetadataStandardCategoryCustomizer):
            self.initial["category"] = category.key
            self.initial["category_name"] = category.name
        elif isinstance(category,int):
            category_instance = property_customizer.category #MetadataStandardCategoryCustomizer.objects.get(pk=category)
            self.initial["category"] = category_instance.key
            self.initial["category_name"] = category_instance.name
        else: # string
            self.initial["category"] = slugify(category)
            self.initial["category_name"] = category
       
        update_field_widget_attributes(self.fields["name"],{"class":"label","readonly":"readonly"})
        update_field_widget_attributes(self.fields["category_name"],{"class":"label","readonly":"readonly"})
        update_field_widget_attributes(self.fields["order"],{"class":"label","readonly":"readonly"})

        set_field_widget_attributes(self.fields["documentation"],{"cols":"60","rows":"4"})
        set_field_widget_attributes(self.fields["suggestions"],{"cols":"60","rows":"4"})
    
    def clean(self):
        cleaned_data = self.cleaned_data

        # the "category" field is a special case
        # it was working off of _unsaved_ models
        # so there is no pk associated w/ it
        # the form will, however, haved stored the name in the "category_name" field
        # I will use that to find the appropriate category to map to in the view
        self.cleaned_data["category"] = None
        try:
            del self.errors["category"]
        except KeyError:
            pass

        return cleaned_data


def MetadataStandardPropertyCustomizerInlineFormSetFactory(*args,**kwargs):
    _prefix      = kwargs.pop("prefix","standard_property")
    _request     = kwargs.pop("request",None)
    _initial     = kwargs.pop("initial",[])
    _instance    = kwargs.pop("instance")
    _categories  = kwargs.pop("categories",[])
    _queryset    = kwargs.pop("queryset",None)
    new_kwargs = {
        "can_delete" : False,
        "extra"      : kwargs.pop("extra",0),
        "formset"    : MetadataPropertyCustomizerInlineFormSet,
        "form"       : MetadataStandardPropertyCustomizerForm,
        "fk_name"    : "model_customizer" # required in-case there are more than 1 fk's to "metadatamodelcustomizer"; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)

    # using curry() to pass arguments to the individual formsets
    # in this case, the set of choices for scientific categories
    _formset = inlineformset_factory(MetadataModelCustomizer,MetadataStandardPropertyCustomizer,*args,**new_kwargs)
    _formset.form = staticmethod(curry(MetadataStandardPropertyCustomizerForm,category_choices=_categories))
    if _initial:
        _formset.number_of_properties = len(_initial)
    elif _queryset:
        _formset.number_of_properties = len(_queryset)
    
    if _request and _request.method == "POST":
        return _formset(_request.POST,instance=_instance,prefix=_prefix)

    return _formset(initial=_initial,instance=_instance,prefix=_prefix)

class MetadataScientificPropertyCustomizerForm(MetadataCustomizerForm):

    class Meta:
        model = MetadataScientificPropertyCustomizer

        fields  = [
                # hidden fields...
                # TODO: AGAIN, WHY DID I HAVE TO EXPLICITLY ADD ID HERE?!?
                # TODO: SHOULD I GET RID OF "model_customizer" SINCE THIS IS DISPLAYED VIA AN INLINE_FORMSET? (I MIGHT HAVE TO IF I START INCLUDING SCIENTIFIC PROPERTIES IN THE SUBFORMS)
                "field_type","proxy","model_customizer","is_enumeration","vocabulary_key","component_key","model_key","id",
                # header fields...
                "name","category_name","order",
                # common fields...
                "category","displayed", "required", "editable", "unique", "verbose_name", "default_value", "documentation","inline_help",
                # keyboard fields...
                "atomic_type","atomic_default",
                # enumeration fields... 
                "enumeration_choices","enumeration_default","enumeration_open","enumeration_multi","enumeration_nullable",
                # extra fields..
                "display_extra_standard_name","edit_extra_standard_name","extra_standard_name","display_extra_description","edit_extra_description","extra_description","display_extra_units","edit_extra_units","extra_units",
        ]


    category_name = CharField(label="Category",required=False)
    category      = ChoiceField(required=False) # changing from the default fk field (ModelChoiceField)
                                                # since I'm dealing w/ _unsaved_ models

    hidden_fields       = ("field_type","proxy","model_customizer","is_enumeration","vocabulary_key","component_key","model_key","id")
    header_fields       = ("name","category_name","order")
    common_fields       = ("category","displayed","required","editable","unique","verbose_name","documentation","inline_help","suggestions")
    keyboard_fields     = ("atomic_type","atomic_default")
    enumeration_fields  = ("enumeration_choices","enumeration_default","enumeration_open","enumeration_multi","enumeration_nullable")

    extra_fields        = ("display_extra_standard_name","edit_extra_standard_name","extra_standard_name","display_extra_description","edit_extra_description","extra_description","display_extra_units","edit_extra_units","extra_units")


    # set of fields that will be the same for all members of a formset; thus I can cache the query (for relationship fields)
    cached_fields       = ["proxy","field_type","category"]

    def get_hidden_fields(self):
        return self.get_fields_from_list(self.hidden_fields)

    def get_header_fields(self):
        return self.get_fields_from_list(self.header_fields)

    def get_keyboard_fields(self):
        fields = list(self)

        common_fields   = [field for field in fields if field.name in self.common_fields]
        keyboard_fields = [field for field in fields if field.name in self.keyboard_fields]

        all_fields = common_fields + keyboard_fields
        all_fields.sort(key=lambda field: fields.index(field))
        return all_fields

    def get_enumeration_fields(self):
        fields = list(self)

        common_fields      = [field for field in fields if field.name in self.common_fields]
        enumeration_fields = [field for field in fields if field.name in self.enumeration_fields]

        all_fields = common_fields + enumeration_fields
        all_fields.sort(key=lambda field: fields.index(field))
        return all_fields

    def get_fields(self):
        if self.current_values["is_enumeration"]:
            return self.get_enumeration_fields()
        else:
            return self.get_keyboard_fields()
        
    def get_extra_fields(self):
        return self.get_fields_from_list(self.extra_fields)

    def get_extra_fieldsets(self):
        fields = self.get_extra_fields()
        fieldsets = OrderedDict()
        fieldsets["Standard Name"]    = [field for field in fields if "standard_name" in field.name]
        fieldsets["Description"]      = [field for field in fields if "description" in field.name]
        fieldsets["Scientific Units"] = [field for field in fields if "units" in field.name]
        return fieldsets

    def __init__(self,*args,**kwargs):
        # category_choices was passed in via curry() in the factory function below
        category_choices = kwargs.pop("category_choices",[])

        super(MetadataScientificPropertyCustomizerForm,self).__init__(*args,**kwargs)

        property_customizer = self.instance

        category = self.current_values["category"]

        self.fields["category"].choices = EMPTY_CHOICE + category_choices
        if isinstance(category,MetadataScientificCategoryCustomizer):
            self.initial["category"] = category.key
            self.initial["category_name"] = category.name
        elif isinstance(category,int):
            category_instance = property_customizer.category #MetadataScientificCategoryCustomizer.objects.get(pk=category)
            self.initial["category"] = category_instance.key
            self.initial["category_name"] = category_instance.name
        else: # string
            self.initial["category"] = slugify(category)
            self.initial["category_name"] = category

        update_field_widget_attributes(self.fields["name"],{"class":"label","readonly":"readonly"})
        update_field_widget_attributes(self.fields["category_name"],{"class":"label","readonly":"readonly"})
        update_field_widget_attributes(self.fields["order"],{"class":"label","readonly":"readonly"})

        set_field_widget_attributes(self.fields["documentation"],{"cols":"60","rows":"4"})
        update_field_widget_attributes(self.fields["category"],{"class":"multiselect","onchange":"copy_value(this,'%s-category_name');"%(self.prefix)})

        update_field_widget_attributes(self.fields["atomic_type"],{"class":"multiselect"})

        set_field_widget_attributes(self.fields["extra_description"],{"rows":"4"})


        all_enumeration_choices = property_customizer.get_field("enumeration_choices").get_choices()

        print "THE CHOICES FOR %s ARE %s" % (property_customizer,all_enumeration_choices)
        
        self.fields["enumeration_choices"].widget = SelectMultiple(choices=all_enumeration_choices)
        self.fields["enumeration_default"].widget = SelectMultiple(choices=all_enumeration_choices)
        if not property_customizer.pk:
            enumeration_choices = [choice[0] for choice in all_enumeration_choices]
            enumeration_default = []
        else:
            if "enumeration_choices" in self.current_values:
                enumeration_choices = self.current_values["enumeration_choices"].split("|")
            else:
                enumeration_choices = []
            if "enumeration_default" in self.current_values:
                enumeration_default = self.current_values["enumeration_default"].split("|")
            else:
                enumeration_default = []
        self.initial["enumeration_choices"] = enumeration_choices
        self.initial["enumeration_default"] = enumeration_default
        update_field_widget_attributes(self.fields["enumeration_choices"],{"class":"multiselect"})
        update_field_widget_attributes(self.fields["enumeration_default"],{"class":"multiselect"})
        
    def clean(self):
        cleaned_data = self.cleaned_data

        # the "category" field is a special case
        # it was working off of _unsaved_ models
        # so there is no pk associated w/ it
        # the form will, however, haved stored the name in the "category_name" field
        # I will use that to find the appropriate category to map to in the view
        try:
            self.cleaned_data["category"] = None
            del self.errors["category"]
        except KeyError:
            pass

        return cleaned_data

def MetadataScientificPropertyCustomizerInlineFormSetFactory(*args,**kwargs):
    _prefix      = kwargs.pop("prefix","scientific_property")
    _request     = kwargs.pop("request",None)
    _initial     = kwargs.pop("initial",[])
    _instance    = kwargs.pop("instance")
    _categories  = kwargs.pop("categories",[])
    _queryset    = kwargs.pop("queryset",None)
    new_kwargs = {
        "can_delete" : False,
        "extra"      : kwargs.pop("extra",0),
        "formset"    : MetadataPropertyCustomizerInlineFormSet,
        "form"       : MetadataScientificPropertyCustomizerForm,
        "fk_name"    : "model_customizer" # required in-case there are more than 1 fk's to "metadatamodelcustomizer"; this is the one that is relevant for this inline form
    }
    new_kwargs.update(kwargs)

    # using curry() to pass arguments to the individual formsets
    _formset = inlineformset_factory(MetadataModelCustomizer,MetadataScientificPropertyCustomizer,*args,**new_kwargs)
    _formset.form = staticmethod(curry(MetadataScientificPropertyCustomizerForm,category_choices=_categories))
    if _initial:
        _formset.number_of_properties = len(_initial)
    elif _queryset:
        _formset.number_of_properties = len(_queryset)

    if _request and _request.method == "POST":
        return _formset(_request.POST,instance=_instance,prefix=_prefix)

    return _formset(queryset=_queryset,initial=_initial,instance=_instance,prefix=_prefix)
