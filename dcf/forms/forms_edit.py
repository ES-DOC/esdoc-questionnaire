
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

    return _form

def MetadataFormSetFactory(submodel_class,attribute_customizer,*args,**kwargs):

    formset = kwargs.pop("formset",MetadataFormSet)
    can_delete = kwargs.pop("can_delete",True)

    # TODO: IF subform_customizer is None, then create a dummy one here
    submodel_customizer = attribute_customizer.subform_customizer
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

    return formfield

class MetadataForm(ModelForm):
    _request    = None
    _prefix     = None

    _subForms   = {}
    
    customizer  = None


    def __init__(self,*args,**kwargs):
        request = kwargs.pop('request', None)
        super(MetadataForm,self).__init__(*args,**kwargs)

        self._request = request
        modelInstance = self.instance
        customizer = self.customizer # this was set by the factory

        attributes_to_replace_with_subForms = [(attribute,modelInstance.getField(attribute.attribute_name)) for attribute in customizer.attributes.all() if attribute.displayed and attribute.customize_subform]
        for (attribute_customizer,attribute) in attributes_to_replace_with_subForms:

            if attribute.getType()=="manytomanyfield":
                subForm_type = SubFormTypes.FORMSET
                subForm_class = MetadataFormSetFactory(attribute.getTargetModelClass(),attribute_customizer)
                

                try:
                    subForm_queryest = getattr(modelInstance,attribute.getName()).all()
                except ValueError: # ValueError ocurrs if the m2m field doesn't exist yet b/c the parent model hasn't been saved yet
                    subForm_queryset = attribute.getTargetModelClass().objects.none()

                subForm_instance = subForm_class(queryset=subForm_queryset)

                self._subForms[attribute.getName()] = (subForm_type,subForm_class,subForm_instance)
            elif attribute.getType()=="manytoonefield":
                # TODO: WORK THROUGH AN EXAMPLE HERE
                subForm_type = SubFormTypes.FORM
                subForm_class = MetadataFormFactory(attribute.getTargetModelClass())
                subForm_instance = subForm_class()
                self._subForms[attribute.getName()] = (subForm_type,subForm_class,subForm_instance)
            else:
                msg = "unknown type of subForm associated w/ attribute '%s' of type: '%s'" % (attribute.getName(),attribute.getType())
                raise MetadataError(msg)


    def getCustomizer(self):
        return self.customizer


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