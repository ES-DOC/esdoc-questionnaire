from django.db import models

from dcf.models import *

#########################################
# this registers this version w/ the db #
#########################################

MetadataVersion.factory({"name":"CIM","version":"1.5"})

####################################
# and here are the actual classes  #
# (pretend this was autogenerated) #
####################################

class ResponsibleParty(MetadataModel):

    class Meta:
        abstract = False

    _name           = "ResponsibleParty"
    _title          = "Contact"
    _description    = ""


    individualName      = MetadataAtomicField.Factory("charfield",max_length=LIL_STRING,blank=False)
    organizationName    = MetadataAtomicField.Factory("charfield",max_length=LIL_STRING,blank=False)
    positionName        = MetadataAtomicField.Factory("charfield",max_length=LIL_STRING,blank=True)
    contactInfo         = MetadataAtomicField.Factory("charfield",max_length=LIL_STRING,blank=True)

    def __init__(self,*args,**kwargs):
        super(ResponsibleParty,self).__init__(*args,**kwargs)

class SoftwareComponent(MetadataModel):

    class Meta:
        abstract = True

    _name           = "SoftwareComponent"
    _title          = "Software Component"
    _description    = ""

    embedded            = MetadataAtomicField.Factory("booleanfield",blank=True)
    embedded.help_text  = "An embedded component cannot exist on its own as an atomic piece of software; instead it is embedded within another (parent) component. When embedded equals 'true', the SoftwareComponent has a corresponding piece of software (otherwise it is acting as a 'virtual' component which may be inexorably nested within a piece of software along with several other virtual components)."
    shortName           =  MetadataAtomicField.Factory("charfield",max_length=LIL_STRING,blank=False)
    shortName.help_text = "the name of the model that is used internally"
    longName            = MetadataAtomicField.Factory("charfield",max_length=BIG_STRING,blank=False)
    longName.help_text  = "the name of the model that is used externally"
    description         = MetadataAtomicField.Factory("textfield",blank=True)
    description.help_text = "a free-text description of the component"
    license             = MetadataAtomicField.Factory("charfield",max_length=BIG_STRING,blank=True)
    license.help_text   = "the license held by this piece of software"
    releaseDate         = MetadataAtomicField.Factory("datefield",null=True)
    releaseDate.help_text = "The date of publication of the software component code (as opposed to the date of publication of the metadata document, or the date of deployment of the model)"
    previousVersion     = MetadataAtomicField.Factory("charfield",max_length=BIG_STRING,blank=True)
    fundingSource       = MetadataAtomicField.Factory("charfield",max_length=BIG_STRING,blank=True)
    fundingSource.help_text = "The entities that funded this software component"
    onlineResource      = MetadataAtomicField.Factory("urlfield")
    responsibleParties  = MetadataManyToManyField(targetModel='cim_1_5.ResponsibleParty',sourceModel="cim_1_5.SoftwareComponent")

    def __init__(self,*args,**kwargs):
        super(SoftwareComponent,self).__init__(*args,**kwargs)


@CIMDocument()
class ModelComponent(SoftwareComponent):

    class Meta:
        abstract = False

    _name = "ModelComponent"
    _title = "Model Component"
    _description = "A ModelComponent is a scientific model; it represents code which models some physical phenomena for a particular length of time."

    pass


    def __init__(self,*args,**kwargs):
        super(ModelComponent,self).__init__(*args,**kwargs)
