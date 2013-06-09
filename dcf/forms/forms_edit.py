
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
__date__ ="Feb 1, 2013 4:42:53 PM"

"""
.. module:: forms_edit

Summary of module goes here

"""
from django.forms import *
from django.forms.models import BaseForm, BaseFormSet, BaseInlineFormSet, BaseModelFormSet, formset_factory, inlineformset_factory, modelform_factory, modelformset_factory

from django.utils.functional import curry

import inspect

from dcf.models import *
from dcf.utils import *


def MetadataFormFactory(model_class,customizer,*args,**kwargs):
    kwargs["form"] = kwargs.pop("form",MetadataForm)
    kwargs["formfield_callback"] = metadata_formfield_callback

    _form = modelform_factory(model_class,**kwargs)
    _form.customizer = customizer
    _form



    return _form

def MetadataFormSetFactory(submodel_class,attribute_customizer,*args,**kwargs):

    formset = kwargs.pop("formset",MetadataFormSet)
    can_delete = kwargs.pop("can_delete",True)

    submodel_customizer = attribute_customizer.subform_customizer
    # I'm going to be lenient;
    # if a submodel_customizer was never defined,
    # then just create a new one here
    # (it will have all the default CIM values)
    if not submodel_customizer:
        filterParameters = {}
        filterParameters["project"] = attribute_customizer.project
        filterParameters["version"] = attribute_customizer.version
        filterParameters["model"]   = submodel_class.getName()
        filterParameters["name"]    = attribute_customizer.parent.name
        (submodel_customizer,created) = MetadataModelCustomizer.objects.get_or_create(**filterParameters)

        print "the customizer is for the model: %s" % submodel_class
        print "and the new customizer has the following %s/%s/%s/%s" % (submodel_customizer.project,submodel_customizer.model,submodel_customizer.version,submodel_customizer.name)
        print "the model has the following attributes: %s" % submodel_class.getAttributes()
        print "and the customizer has the following corresponding attribute_customizers: %s" % submodel_customizer.attributes



#    print "the customizer for %s has the following attributes %s" % (submodel_customizer.model,submodel_customizer.attributes.count())

        
    subform_class = MetadataFormFactory(submodel_class,submodel_customizer,*args,**kwargs)

    kwargs["formset"] = formset
    kwargs["can_delete"] = can_delete
    _formset = modelformset_factory(submodel_class,*args,**kwargs)

    _formset.attribute_customizer = attribute_customizer
    _formset.model_customizer = submodel_customizer
    # TODO: DOUBLE-CHECK THIS CALL TO staticmethod(curry(...))
    # this ensures that the request and other kwargs passed to formsets gets propagated to all the child forms
    _formset.form = staticmethod(curry(subform_class,request=MetadataFormSet._request))

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

class MetadataForm(ModelForm):
    _type = SubFormTypes.FORM
    
    _request    = None
    _prefix     = None

    _subForms   = {}
    
    customizer  = None


    def customize_attribute(self,attribute_customizer):
        # each type of attribute (field) has a different set of customization options...
        if attribute_customizer.isEnumerationField():
            
            multiwidget = self.fields[attribute_customizer.attribute_name].widget.widgets
            multifield  = self.fields[attribute_customizer.attribute_name].fields
            # set the choices of the field
            current_choices = [(choice,choice) for choice in attribute_customizer.enumerations.split("|")]
            default_choices = [choice for choice in attribute_customizer.default_enumerations.split("|")]
            if attribute_customizer.nullable:
                current_choices += NULL_CHOICE
            else:
                pass
            if attribute_customizer.open:
                current_choices += OPEN_CHOICE
            else:
                pass
            if attribute_customizer.multi:
                multiwidget[0] = SelectMultiple(choices=current_choices)
            else:
                multiwidget[0] = Select(choices=current_choices)
            # set whether the field is editable
            if not attribute_customizer.editable:
                update_widget_attributes(multiwidget[0],{"disabled":"true"})
                update_widget_attributes(multiwidget[1],{"disabled":"true"})
            # set the default value
            if attribute_customizer.multi:
                self.initial[attribute_customizer.attribute_name] = [default_choices,"please enter custom selection"]
            else:
                self.initial[attribute_customizer.attribute_name] = [default_choices[0],"please enter custom selection"]

            # some custom CSS added to enumeration widgets
            update_widget_attributes(multiwidget[0],{"class":"enumeration-value dropdownchecklist"})
            update_widget_attributes(multiwidget[1],{"class":"enumeration-other"})

        elif attribute_customizer.isRelationshipField():
            pass

        else:   # attribute_customizer.isAtomicField()
            # set the default value
            self.initial[attribute_customizer.attribute_name] = attribute_customizer.default_value

    def __init__(self,*args,**kwargs):
        request = kwargs.pop('request', None)
        super(MetadataForm,self).__init__(*args,**kwargs)

        self._request = request
        modelInstance = self.instance
        customizer = self.customizer # this was set by the factory

        print "IN INIT"
        print "ONE: %s"%len(customizer.attributes.all())
        for attribute_customizer in customizer.attributes.all():
            self.customize_attribute(attribute_customizer)
        print "TWO: %s"%len(customizer.attributes.all())



        # TODO: MOVE THE FOLLOWING CODE INTO THE CUSTOMIZE METHOD (CALLED ABOVE)
        attributes_to_replace_with_subForms = [(attribute,modelInstance.getField(attribute.attribute_name)) for attribute in customizer.attributes.all() if attribute.displayed and attribute.customize_subform]
        for (attribute_customizer,attribute) in attributes_to_replace_with_subForms:

            if attribute.getType()=="manytomanyfield":
                subForm_type = SubFormTypes.FORMSET

                submodel_class = attribute.getTargetModelClass()
                submodel_customizer = attribute_customizer.subform_customizer

                # TODO: AGAIN, MOVE ALL OF THIS LOGIC INTO THE SAVE METHOD OF ATTRIBUTE_CUSTOMIZER RATHER THAN HERE!!!
                # I'm going to be lenient;
                # if a submodel_customizer was never defined,
                # then just create a new one here
                # (it will have all the default CIM values)
                if not submodel_customizer:
                    filterParameters = {}
                    filterParameters["project"] = attribute_customizer.project
                    filterParameters["version"] = attribute_customizer.version
                    filterParameters["model"]   = submodel_class.getName()
                    filterParameters["name"]    = attribute_customizer.parent.name
                    (submodel_customizer,created) = MetadataModelCustomizer.objects.get_or_create(**filterParameters)
                    if created:
                        print "CREATED NEW CUSTOMIZER FOR SUBFORMSET"
                        # so, ordinarily, a customizer would have its attributes saved by virtue of saving the form
                        # but this one is created internally, so I have to do this manually
                        # users really ought to customize every form they are going to use
                        # but if not, this will catch their oversight
                        for temporary_attribute in submodel_customizer.temporary_attributes:
                            temporary_attribute.parent = submodel_customizer
                            temporary_attribute.save()
                        submodel_customizer.temporary_attributes = []
                        submodel_customizer.save()
                        attribute_customizer.subform_customizer = submodel_customizer
                        attribute_customizer.save()

                subForm_class = MetadataFormSetFactory(attribute.getTargetModelClass(),attribute_customizer)
                
                try:
                    subForm_queryest = getattr(modelInstance,attribute.getName()).all()
                except ValueError: # ValueError ocurrs if the m2m field doesn't exist yet b/c the parent model hasn't been saved yet
                    subForm_queryset = attribute.getTargetModelClass().objects.none()

                subForm_instance = subForm_class(queryset=subForm_queryset)
            
            elif attribute.getType()=="manytoonefield":                
                subForm_type = SubFormTypes.FORM

                submodel_class = attribute.getTargetModelClass()
                submodel_customizer = attribute_customizer.subform_customizer

                # I'm going to be lenient;
                # if a submodel_customizer was never defined,
                # then just create a new one here
                # (it will have all the default CIM values)
                if not submodel_customizer:
                    filterParameters = {}
                    filterParameters["project"] = attribute_customizer.project
                    filterParameters["version"] = attribute_customizer.version
                    filterParameters["model"]   = submodel_class.getName()
                    filterParameters["name"]    = attribute_customizer.parent.name
                    (submodel_customizer,created) = MetadataModelCustomizer.objects.get_or_create(**filterParameters)
                    if created:
                        print "CREATED NEW CUSTOMIZER FOR SUBFORM"
                        # so, ordinarily, a customizer would have its attributes saved by virtue of saving the form
                        # but this one is created internally, so I have to do this manually
                        # users really ought to customize every form they are going to use
                        # but if not, this will catch their oversight
                        for temporary_attribute in submodel_customizer.temporary_attributes:
                            temporary_attribute.parent = submodel_customizer
                            temporary_attribute.save()
                        submodel_customizer.temporary_attributes = []
                        submodel_customizer.save()

                subForm_class = MetadataFormFactory(submodel_class,submodel_customizer)
                subForm_instance = subForm_class()
                                
            else:
                msg = "unknown type of subForm associated w/ attribute '%s' of type: '%s'" % (attribute.getName(),attribute.getType())
                raise MetadataError(msg)

            self._subForms[attribute.getName()] = (subForm_type,subForm_class,subForm_instance)
        print "THREE: %s"%len(customizer.attributes.all())

    def getCustomizer(self):
        return self.customizer

    def getType(self):
        return self._type

    def getAllSubForms(self):
        # returns the union of all subforms for all ancestor classes
        allSubForms = {}
        model_class = self.Meta.model
        for ancestor_model in reversed(inspect.getmro(model_class)):
            if issubclass(ancestor_model,MetadataModel):

                # I AM HERE !!!!
                print ancestor_model

        return self._subForms

###
###        for ancestor in reversed(inspect.getmro())
###        modelClass = self.getModelClass()
###        for ancestor in reversed(inspect.getmro(modelClass)):
###            if issubclass(ancestor,MetadataModel):
###                ancestorForm = getFormClassFromModelClass(ancestor)
###                if ancestorForm:
###                    allSubForms = dict(allSubForms.items() + ancestorForm._subForms.items())
###        return allSubForms

class MetadataFormSet(BaseModelFormSet):
    _type = SubFormTypes.FORMSET

    _request = None
    _prefix  = None

    model_customizer = None         # the customizer for the model that this formset is rendering
    attribute_customizer = None     # the customizer for the attribute that this formset is replacing

    def getType(self):
        return self._type

    def getRequest(self):
        return self._request

    def getPrefix(self):
        return self._prefix

    def getAttributeCustomizer(self):
        return self.attribute_customizer

    def getModelCustomizer(self):
        return self.model_customizer

    @classmethod
    def getDefaultPrefix(cls):
        return str(uuid4())

    def __init__(self,*args,**kwargs):
        request = kwargs.pop("request",None)
        prefix  = kwargs.pop("prefix",self.getDefaultPrefix())

        self.form = curry(self.form,request=request)

        super(MetadataFormSet,self).__init__(*args,**kwargs)

        self._request = request
        self._prefix = prefix