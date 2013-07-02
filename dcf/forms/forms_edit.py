
####################
#   Django-CIM-Forms
#   Copyright (c) 2012 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Jun 12, 2013 12:17:41 PM"

"""
.. module:: forms_edit

Summary of module goes here

"""

from django.forms import *
from django.utils.functional import curry
from django.forms.models import BaseForm, BaseFormSet, BaseInlineFormSet, BaseModelFormSet, formset_factory, inlineformset_factory, modelform_factory, modelformset_factory


from dcf.models import *
from dcf.utils import *


class SubFormType(EnumeratedType):
    """
    An enumeration of the different types of subForms that can be used by a parent form.
    """
    pass

SubFormTypes = EnumeratedTypeList([
    SubFormType("FORM","Form",BaseForm),
    SubFormType("FORMSET","FormSet",BaseFormSet),
])

def MetadataFormFactory(model_class,customizer,*args,**kwargs):
    kwargs["form"] = kwargs.pop("form",MetadataForm)
    kwargs["formfield_callback"] = metadata_formfield_callback
    _request = kwargs.pop("request",None)

    _form = modelform_factory(model_class,**kwargs)
    _form.customizer = customizer
    _form.request    = _request

    return _form



def MetadataFormSetFactory(model_class,customizer,*args,**kwargs):
    _queryset   = kwargs.pop("queryset",None)
    _initial    = kwargs.pop("initial",None)
    _prefix     = kwargs.pop("prefix","formset")
    _request    = kwargs.pop("request",None)

    form_class  = MetadataFormFactory(model_class,customizer)

    new_kwargs = {
        "extra"       : kwargs.pop("extra",1),
        "can_delete"  : True,
        "formset"     : MetadataModelFormSet,
        "form"        : form_class
    }
    new_kwargs.update(kwargs)

    _formset = modelformset_factory(model_class,*args,**new_kwargs)
    _formset.form       = staticmethod(curry(form_class,request=_request))
    _formset.prefix     = _prefix
    _formset.customizer = customizer

#    if _request and _request.method == "POST":
#        return _formset(_request.POST,prefix=_prefix)
        
    return _formset

def metadata_formfield_callback(field):
    formfield = field.formfield()

    if isinstance(field,MetadataField):

        if isinstance(field,MetadataAtomicField):
            pass

            if isinstance(field,models.DateField):
                update_field_widget_attributes(formfield,{"class":"datepicker"})


        if isinstance(field,MetadataRelationshipField):
            pass

        if isinstance(field,MetadataEnumerationField):
            pass


        pass

    return formfield

class MetadataModelFormSet(BaseModelFormSet):
    _type = SubFormTypes.FORMSET
    customizer = None   # this gets set by the factory method

    def __init__(self,*args,**kwargs):
        super(MetadataModelFormSet,self).__init__(*args,**kwargs)

    def getType(self):
        return self._type

    def is_valid(self):
        validity = [form.is_valid() for form in self.forms]
        return all(validity)

#    def clean(self):
#        for form in self.forms:
#            form.clean()
    

class MetadataForm(ModelForm):
    _type = SubFormTypes.FORM

    _subForms = {}
    _propertyForms = {}

    customizer = None   # this gets set by the factory method
    request    = None   # this either gets set by the factory method, or can be passed into __init__

    standard_property_customizers   = {}
    scientific_property_customizers = {}

    def getType(self):
        return self._type

    def getStandardPropertyCustomizers(self):
        return self.standard_property_customizers

    def getScientificPropertyCustomizers(self):
        return self.scientific_property_customizers
    
    def __init__(self,*args,**kwargs):
        _request = kwargs.pop("request",None)
        super(MetadataForm,self).__init__(*args,**kwargs)
        if _request:
            self.request = _request

        model_customizer = self.customizer # this will have been set by the factory

        self.fields["active"].widget               = HiddenInput()
        self.fields["published"].widget            = HiddenInput()
        self.fields["component_name"].widget       = HiddenInput()
        self.fields["parent_content_type"].widget  = HiddenInput()
        self.fields["parent_id"].widget            = HiddenInput()
        #self.fields["parent_object"].widget        = HiddenInput()


        self.standard_property_customizers = {}
        for standard_property_customizer in model_customizer.getStandardPropertyCustomizers().order_by("order"):
            if standard_property_customizer.displayed:
                category_key = standard_property_customizer.category.key if standard_property_customizer.category else "NONE"
                if not category_key in self.standard_property_customizers:
                    self.standard_property_customizers[category_key] = []
                self.standard_property_customizers[category_key].append(standard_property_customizer)
        
        self.scientific_property_customizers = {}
        for scientific_property_customizer in model_customizer.getScientificPropertyCustomizers().order_by("order"):
            if scientific_property_customizer.displayed:
                component_name_key = scientific_property_customizer.component_name.lower()
                if not component_name_key in self.scientific_property_customizers:
                    self.scientific_property_customizers[component_name_key] = {}
                category_key = scientific_property_customizer.category.key if scientific_property_customizer.category else "NONE"
                if not category_key in self.scientific_property_customizers[component_name_key]:
                    self.scientific_property_customizers[component_name_key][category_key] = []
                self.scientific_property_customizers[component_name_key][category_key].append(scientific_property_customizer)

        self._subForms = {}
        for standard_property_customizer_set in self.standard_property_customizers.itervalues():
            for standard_property_customizer in standard_property_customizer_set:

                # do the standard customization that every field gets...
                self.customize_field(standard_property_customizer)
                
                # then check to see if I have to deal w/ subforms...
                if standard_property_customizer.customize_subform and standard_property_customizer.displayed:
                    metadata_field = self.get_metadata_field(standard_property_customizer.name)
                    # TODO THE FIX FOR BULK_CREATE IN SQLITE
                    # CAUSES SOME LOOKUPS W/ CONTENTTYPE TO FAIL
                    # SO FOR NOW I AM REPLACING THOSE W/ THE SAVED CLASSES IN THE VERSION
                    #target_model_class = metadata_field.getTargetModelClass()
                    target_model_class = self.customizer.version.getModelClass(metadata_field.targetModelName)
                    target_model_name = target_model_class.getName().lower()
                    (target_model_customizer,created) = MetadataModelCustomizer.objects.get_or_create(
                        project = self.customizer.project,
                        version = self.customizer.version,
                        model   = target_model_name,
                        name    = self.customizer.name,
                    )
                    
                    if created:
                        # if users never specified one in the customizer, just create a default one
                        # that means I need to initialize it and create all the standard properties
                        target_model_proxy = MetadataModelProxy.objects.get(
                            version = self.customizer.version,
                            model_name__iexact  = target_model_name,
                        )
                        target_model_customizer.reset(target_model_proxy)
                        target_model_customizer.save()
                        target_standard_property_proxies = MetadataStandardPropertyProxy.objects.filter(
                            version = self.customizer.version,
                            model_name__iexact = target_model_class.getName(),
                        )
                        for target_standard_property_proxy in target_standard_property_proxies:
                            target_standard_property_customizer = MetadataStandardPropertyCustomizer(
                                project = self.customizer.project,
                                version = self.customizer.version,
                                model   = target_model_name,
                            )
                            target_standard_property_customizer.reset(target_standard_property_proxy)
                            target_standard_property_customizer.setParent(target_model_customizer)
                            target_standard_property_customizer.save()

                    prefix = self.instance.component_name + "_" + standard_property_customizer.name
                    if standard_property_customizer.field_type == "manytomanyfield":
                        subform_type        = SubFormTypes.FORMSET
                        subform_class       = MetadataFormSetFactory(target_model_class,target_model_customizer,request=self.request)
                        try:
                            subform_queryset    = getattr(self.instance,standard_property_customizer.name).all()
                        except ValueError: # ValueError ocurrs if the m2m field doesn't exist yet b/c the parent model hasn't been saved yet
                            subform_queryset    = target_model_class.objects.none()
                        if self.request and self.request.method == "POST":
                            subform_instance    = subform_class(self.request.POST,queryset=subform_queryset,prefix=prefix)
                        else:
                            subform_instance    = subform_class(queryset=subform_queryset,prefix=prefix)
                    elif standard_property_customizer.field_type == "manytoonefield":
                        subform_type        = SubFormTypes.FORM
                        subform_class       = MetadataFormFactory(target_model_class,target_model_customizer,request=self.request)
                        submodel_instance   = getattr(self.instance,standard_property_customizer.name)
                        if not submodel_instance:                            
                            submodel_instance = target_model_class()
                            submodel_instance.project = self.customizer.project
                        if self.request and self.request.method == "POST":
                            subform_instance    = subform_class(self.request.POST,instance=submodel_instance,prefix=prefix)
                        else:
                            subform_instance    = subform_class(instance=submodel_instance,prefix=prefix)

                    self._subForms[standard_property_customizer.name] = \
                        (subform_type,subform_class,subform_instance)

###
###        if self.customizer:
###
###            vocabulary = self.customizer.project.vocabularies.all()[0]
###            for component_name in vocabulary.getComponentList():
###                properties_of_component = MetadataScientificPropertyProxy.objects.filter(vocabulary=vocabulary,component_name__iexact=component_name[0].lower())
###
###                PropertiesFormSet = MetadataScientificPropertyFormSetFactory(
###                    extra=len(properties_of_component)
###                )
###                self._propertyForms[component_name.lower()] = PropertiesFormSet


    def is_valid(self):
        subform_validity = [subForm[2].is_valid() for subForm in self.getAllSubForms().itervalues() if subForm[2]]
        mainform_validity = super(MetadataForm,self).is_valid()
        validity = all(subform_validity) and mainform_validity
        return validity

    def clean(self):
        cleaned_data = self.cleaned_data
        
        standard_property_customizers = self.customizer.getStandardPropertyCustomizers()

        model_class = self.Meta.model

        for (field_name,field_value) in cleaned_data.iteritems():            
            try:
                property_customizer = standard_property_customizers.get(name=field_name)
                    
                # check all the different ways a field can be invalid according to a customizer...
                if property_customizer.unique:
                    filter_args = { field_name : field_value }
                    existing_models = model_class.objects.filter(**filter_args).exclude(_guid=self.instance.getGUID())
                    if existing_models:
                        msg = "This value must be unique."
                        self._errors[field_name] = self.error_class([msg])

                if property_customizer.required and not field_value:
                    self._errors[field_name] = "This field is required"
                    del cleaned_data[field_name]

                    
            except ObjectDoesNotExist:
                # some fields don't have customizers
                # (active, published, component_name, parent)
                # that's okay - just ignore them
                pass
            
        return cleaned_data

    def save(self,*args,**kwargs):
        saved_instance = super(MetadataForm,self).save(*args,**kwargs)

        for (key,value) in self.getAllSubForms().iteritems():
            subFormType     = value[0]
            subFormClass    = value[1]
            subFormInstance = value[2]

            if subFormInstance.has_changed():

                if subFormType == "FORM":

                    subModelInstance = subFormInstance.save(commit=False)
                    subModelInstance.save()
                    subFormInstance.save_m2m()

                    setattr(saved_instance,key,subModelInstance)

                elif subFormType == "FORMSET":

                    subModelInstances = subFormInstance.save(commit=False)
                    for subModelInstance in subModelInstances:
                        subModelInstance.save()
                    subFormInstance.save_m2m()

                    # TODO: I AM HERE; THIS DOESN'T WORK
                    setattr(saved_instance,key,subModelInstances)


        return saved_instance

#    def save(self,*args,**kwargs):
#        cleaned_data = self.cleaned_data
#
#        for (key,value) in self.getAllSubForms().iteritems():
#            subFormType     = value[0]
#            subFormClass    = value[1]
#            subFormInstance = value[2]
#
#            if subFormType == "FORM":
#                subModelInstance = subFormInstance.save(commit=False)
#                subModelInstance.save()
#                subFormInstance.save_m2m()
#                cleaned_data[key] = subModelInstance
#
#            elif subFormType == "FORMSET":
#                subModelInstances = subFormInstance.save(commit=False)
#                _instances = []
#                for subModelInstance in subModelInstances:
#                    _instances.append(subModelInstance.save())
#                subFormInstance.save_m2m()
#                cleaned_data[key] = _instances
#
#
#        return super(MetadataForm,self).save(*args,**kwargs)

    def getAllSubForms(self):
#        # returns the union of all subforms for all ancestor classes
#        allSubForms = {}
#        model_class = self.Meta.model
#        for ancestor_model in reversed(inspect.getmro(model_class)):
#            if issubclass(ancestor_model,MetadataModel):
#                # I AM HERE !!!!
#                pass

        return self._subForms

    def customize_field(self,property_customizer):

        field_name = property_customizer.name
        field_type = property_customizer.type


        if field_type == MetadataFieldTypes.ATOMIC:

            if property_customizer.suggestions:
                update_field_widget_attributes(self.fields[field_name],{"class":"autocomplete"})
                update_field_widget_attributes(self.fields[field_name],{"suggestions":property_customizer.suggestions})
        
            if not property_customizer.editable:
                update_field_widget_attributes(self.fields[field_name],{"class":"readonly","readonly":"readonly"})

            if property_customizer.default_value:
                self.initial[field_name] = property_customizer.default_value

        
        elif field_type == MetadataFieldTypes.RELATIONSHIP:

            pass

        elif field_type == MetadataFieldTypes.ENUMERATION:

            multiwidget = self.fields[field_name].widget.widgets
            multifield  = self.fields[field_name].fields

         
            # set the choices of the field


            try:

                current_choices = [(choice,choice) for choice in property_customizer.enumeration_values.split("|")]
                default_choices = [choice for choice in property_customizer.enumeration_default.split("|")]
                if property_customizer.enumeration_nullable:
                    current_choices += NULL_CHOICE

                if property_customizer.enumeration_open:
                    current_choices += OPEN_CHOICE

                if property_customizer.enumeration_multi:
                    multiwidget[0] = SelectMultiple(choices=current_choices)
                else:
                    multiwidget[0] = Select(choices=current_choices)

                if not property_customizer.editable:
                    update_widget_attributes(multiwidget[0],{"disabled":"true"})
                    update_widget_attributes(multiwidget[1],{"disabled":"true"})

                if property_customizer.enumeration_multi:
                    self.initial[field_name] = [default_choices,"please enter custom selection"]
                else:
                    self.initial[field_name] = [default_choices[0],"please enter custom selection"]

                if property_customizer.suggestions:
                    update_widget_attributes(multiwidget[1],{"class":"autocomplete"})
                    update_widget_attributes(multiwidget[1],{"suggestions":property_customizer.suggestions})

            except:
                pass
            
            # some custom CSS added to enumeration widgets
            update_widget_attributes(multiwidget[0],{"class":"enumeration-value multiselect"})
            update_widget_attributes(multiwidget[1],{"class":"enumeration-other"})

        else:
            pass

    def get_metadata_field(self,field_name):
        return self.instance.getField(field_name)


class MetadataScientificPropertyForm(ModelForm):
    class Meta:
        model = MetadataProperty

    _type = SubFormTypes.FORM
    property_customizer     = None
    property_value_field    = None
    extra_fields   = ("standard_name","long_name","description",)

    def getType(self):
        return self._type

    def getExtraFields(self):
        fields = list(self)
        return [field for field in fields if field.name in self.extra_fields]
        

    def getPropertyValueField(self):
        try:
            return self["property_enumeration"]
        except KeyError:
            return self["property_freetext"]
    
    def __init__(self,*args,**kwargs):
        _request = kwargs.pop("request",None)
        super(MetadataScientificPropertyForm,self).__init__(*args,**kwargs)

        property_data = {}
        if self.data:
            # (not sure why I can't do this in a list comprehension)
            for key,value in self.data.iteritems():
                if key.startswith(self.prefix+"-"):
                    property_data[key.split(self.prefix+"-")[1]] = value[0] if isinstance(value,tuple) else value
        else:
            property_data = self.initial

        self.property_customizer = property_data["customizer"]
        if not isinstance(self.property_customizer,MetadataScientificPropertyCustomizer):
            self.property_customizer = MetadataScientificPropertyCustomizer.objects.get(pk=property_data["customizer"])

        self.fields["category"].widget            = HiddenInput()
        self.fields["customizer"].widget          = HiddenInput()
        self.fields["component_name"].widget      = HiddenInput()
        self.fields["name"].widget                = HiddenInput()
        self.fields["choice"].widget              = HiddenInput()
        self.fields["model_content_type"].widget  = HiddenInput()
        self.fields["model_id"].widget            = HiddenInput()
        #self.fields["model_object"].widget        = HiddenInput()

        self.fields["description"].widget.attrs["rows"] = 3
        self.fields["property_enumeration"].label       = "Value"
        self.fields["property_freetext"].label          = "Value"

        choice = property_data["choice"]


        if choice == "keyboard":

            self.property_value_field = self["property_freetext"]

            del self.fields["property_enumeration"]

            update_field_widget_attributes(self.fields["property_freetext"],{"onchange":"set_label(this,'property_value');"})

            if self.property_customizer.suggestions:
                update_field_widget_attributes(self.fields["property_freetext"],{"class":"autocomplete"})
                update_field_widget_attributes(self.fields["property_freetext"],{"suggestions":property_customizer.suggestions})

        else:

            self.property_value_field = self["property_enumeration"]

            del self.fields["property_freetext"]

            update_field_widget_attributes(self.fields["property_enumeration"],{"onchange":"set_label(this,'property_value');"})
            
            multiwidget = self.fields["property_enumeration"].widget.widgets
            multifield  = self.fields["property_enumeration"].fields

            current_choices = [(choice,choice) for choice in self.property_customizer.value.split("|")]
            default_choices = [choice for choice in self.property_customizer.value_default.split("|")]
            if self.property_customizer.nullable:
                current_choices += NULL_CHOICE

            if self.property_customizer.open:
                current_choices += OPEN_CHOICE

            if self.property_customizer.multi:
                multiwidget[0] = SelectMultiple(choices=current_choices)
            else:
                multiwidget[0] = Select(choices=current_choices)

            if not self.property_customizer.editable:
                update_widget_attributes(multiwidget[0],{"disabled":"true"})
                update_widget_attributes(multiwidget[1],{"disabled":"true"})

            if self.property_customizer.multi:
                self.initial["property_enumerations"] = [default_choices,"please enter custom selection"]
            else:
                self.initial["property_choices"] = [default_choices[0],"please enter custom selection"]

            if self.property_customizer.suggestions:
                update_widget_attributes(multiwidget[1],{"class":"autocomplete"})
                update_widget_attributes(multiwidget[1],{"suggestions":self.property_customizer.suggestions})

            # some custom CSS added to enumeration widgets
            update_widget_attributes(multiwidget[0],{"class":"enumeration-value multiselect"})
            update_widget_attributes(multiwidget[1],{"class":"enumeration-other"})

        
        if not self.property_customizer.edit_extra_attributes:            
            for field in self.getExtraFields():
                update_field_widget_attributes(self.fields[field.name],{"class":"readonly","readonly":"readonly"})

        
def MetadataScientificPropertyFormFactory(model_class,customizer,*args,**kwargs):
    kwargs["form"] = kwargs.pop("form",MetadataScientificPropertyForm)
    kwargs["formfield_callback"] = metadata_formfield_callback

    _form = modelform_factory(model_class,**kwargs)
    _form.customizer = customizer

    return _form

def MetadataScientificPropertyFormSetFactory(*args,**kwargs):
    _queryset       = kwargs.pop("queryset",MetadataProperty.objects.none())
    _initial        = kwargs.pop("initial",None)
    _prefix         = kwargs.pop("prefix","scientific_property")
    _customizers    = kwargs.pop("customizers",None)
    _request        = kwargs.pop("request",None)
    new_kwargs = {
        "extra"       : kwargs.pop("extra",0),
        "can_delete"  : False,
        "form"        : MetadataScientificPropertyForm
#        "form"        : MetadataScientificFormFactory(MetadataProperty,customizer)

    }
    new_kwargs.update(kwargs)

    _formset = modelformset_factory(MetadataProperty,*args,**new_kwargs)
    #_formset.form = staticmethod(curry(MetadataStandardPropertyCustomizerForm,request=_request))

    if _request and _request.method == "POST":
        return _formset(_request.POST,prefix=_prefix)

    return _formset(queryset=_queryset,initial=_initial,prefix=_prefix)

