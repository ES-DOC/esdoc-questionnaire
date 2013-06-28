
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
__date__ ="Jun 6, 2013 1:03:04 PM"

"""
.. module:: external_models

Summary of module goes here

"""

from dcf.models import *
from dcf.cim_1_8_1.models import *

######
# XS #
######

class XS_AnySimpleType(MetadataModel):

    class Meta:
        app_label = "cim_1_8_1"
        abstract = False
    _abstract = True

    _name        = "AnySimpleType"
    _title       = "Any Simple Type"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(XS_AnySimpleType,self).__init__(*args,**kwargs)

    value = MetadataAtomicField.Factory("textfield",blank=True,)


class XS_Token(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False
    _abstract = True

    _name        = "XS_Token"
    _title       = "XS Token"
    _description = " "

    def __init__(self,*args,**kwargs):
        super(XS_Token,self).__init__(*args,**kwargs)

    value = MetadataAtomicField.Factory("textfield",blank=True)

#########
# XLINK #
#########

#######
# GML #
#######

#######
# GMD #
#######

class GMD_RoleType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "GMD_RoleType"
    _title       = "GMD Role Type"
    _description = ""

    CHOICES = [
        'Metadata Author',
        'Principle Investigator',
    ]

    open     = True
    nullable = False
    multi    = False

class GMD_Contact(MetadataModel):

    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "GMD_Contact"
    _title       = "GMD Contact"
    _description = ""


    def __init__(self,*args,**kwargs):
        super(GMD_Contact,self).__init__(*args,**kwargs)

    # TODO: EXPAND THESE OUT; I DELIBERATELY SIMPLIFIED THIS CLASS
    phone  = MetadataAtomicField.Factory("charfield",blank=True)
    address = MetadataAtomicField.Factory("textfield",blank=True)
    onlineResource = MetadataAtomicField.Factory("urlfield",blank=True)
    hoursOfService = MetadataAtomicField.Factory("charfield",blank=True)
    contactInstructions = MetadataAtomicField.Factory("textfield",blank=True)

class GMD_ResponsibleParty(MetadataModel):

    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "GMD_ResponsibleParty"
    _title       = "GMD Responsible Party"
    _description = ""


    def __init__(self,*args,**kwargs):
        super(GMD_ResponsibleParty,self).__init__(*args,**kwargs)

    individualName  = MetadataAtomicField.Factory("charfield",blank=True)
    organisationName = MetadataAtomicField.Factory("charfield",blank=True)
    positionName = MetadataAtomicField.Factory("charfield",blank=True)
    contactInfo = MetadataManyToManyField(sourceModel='cim_1_8_1.GMD_ResponsibleParty',targetModel='cim_1_8_1.GMD_Contact',blank=True,)
    role = MetadataEnumerationField(enumeration='cim_1_8_1.GMD_RoleType',blank=True,)