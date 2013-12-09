
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
__date__ ="Jun 6, 2013 1:02:53 PM"

"""
.. module:: default_models

Summary of module goes here

"""

from dcf.models import *
from dcf.cim_1_8_1.models import *

# this is _not_ autogenerated!


class Identifier(XS_Token):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Identifier"
    _title       = "Identifier"
    _description = "Needed so that a Numerical Requirement can be be uniquely identified and related to a specific data granule. "

    def __init__(self,*args,**kwargs):
        super(Identifier,self).__init__(*args,**kwargs)


class Document(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False
    _abstract = True

    _name        = "Document"
    _title       = "Document"
    _description = "Any class or feature with the &lt;&lt;document&gt;&gt; stereotype uses the attributes of this class. Furthermore, any class or feature with the &lt;&lt;document&gt;&gt; stereotype can form the root of an XML document."

    def __init__(self,*args,**kwargs):
        super(Document,self).__init__(*args,**kwargs)


    # UML Attribute
    documentID = MetadataAtomicField.Factory("charfield",blank=False,)
    documentID.help_text = "a unique indentifier for this document"
                # UML Attribute
    documentVersion = MetadataAtomicField.Factory("charfield",blank=False,)
# UML Attribute
    metadataID = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    metadataVersion = MetadataAtomicField.Factory("charfield",blank=True,)
# UML Attribute
    externalID = MetadataManyToOneField(sourceModel='cim_1_8_1.Document',targetModel='cim_1_8_1.StandardName',blank=True,)
    externalID.help_text = "The id of this document as referenced by an external body (ie: DOI, or even IPSL)"
                # UML Attribute
    documentAuthor = MetadataManyToOneField(sourceModel='cim_1_8_1.Document',targetModel='cim_1_8_1.ResponsibleParty',blank=True,)
    documentAuthor.help_text = "A contact for the author of this document (as opposed to the author of the artifact being described by this document; ie: the simulation or component or whatever).This includes information about the authoring institution."
                # UML Attribute
    documentCreationDate = MetadataAtomicField.Factory("datefield",blank=False,)
    documentCreationDate.help_text = "The date the document was created."
                # UML Attribute
    documentGenealogy = MetadataManyToOneField(sourceModel='cim_1_8_1.Document',targetModel='cim_1_8_1.Genealogy',blank=True,)
    documentGenealogy.help_text = "Specifies the relationship of this document with another document. Various relationship types (depending on the type of document; ie: simulation, component, etc.) are supported."
                # UML Attribute
    documentStatus = MetadataEnumerationField(enumeration='cim_1_8_1.DocumentStatusType',blank=True,)
#### UML Attribute
###    quality = MetadataManyToOneField(sourceModel='cim_1_8_1.Document',targetModel='cim_1_8_1.CIM_Quality',blank=True,)
###    quality.help_text = "a (set of) quality record(s) for this document."



###class Reference(MetadataModel):
###
###
###    class Meta:
###        app_label = "cim_1_8_1"
###        abstract = False
###    _abstract = True
###
###    _name        = "Reference"
###    _title       = "Reference"
###    _description = "Any class or feature with the &lt;&lt;reference&gt;&gt; stereotype uses the attributes of this class.  With all the different ways of pinpointing an XML item, a reference can either use XPATH to directly locate the item or it can just identifiy the document and then use the other attributes (name,type,etc.) to narrow down the particular element within that document.  "
###
###    def __init__(self,*args,**kwargs):
###        super(Reference,self).__init__(*args,**kwargs)
###
###
###    # UML Attribute
###    id = MetadataManyToOneField(sourceModel='cim_1_8_1.Reference',targetModel='cim_1_8_1.guid',blank=True,)
###    id.help_text = "the ID of the element being referenced."
###                # UML Attribute
###    name = MetadataAtomicField.Factory("charfield",blank=True,)
###    name.help_text = "The name of the instance being referenced."
###                # UML Attribute
###    type = MetadataAtomicField.Factory("charfield",blank=True,)
###    type.help_text = "The type of item being referenced (should correspond to the name of the referenced XML element)."
###                # UML Attribute
###    version = MetadataManyToOneField(sourceModel='cim_1_8_1.Reference',targetModel='cim_1_8_1.version',blank=True,)
###    version.help_text = "The version of the element being referenced."
###                # UML Attribute
###    externalID = MetadataManyToOneField(sourceModel='cim_1_8_1.Reference',targetModel='cim_1_8_1.StandardName',blank=True,)
###    externalID.help_text = "A non-CIM (non-GUID) id used to reference the element in question."
###                # UML Attribute
###    description = MetadataAtomicField.Factory("charfield",blank=True,)
###    description.help_text = "A description of the element being referenced, in the context of the current class."
###                # UML Attribute
###    change = MetadataManyToOneField(sourceModel='cim_1_8_1.Reference',targetModel='cim_1_8_1.Change',blank=True,)
###    change.help_text = "An optional description of how the item being referenced has been modified.  This is particularly useful for dealing with Ensembles (a set of simulations where something about each simulation has changed) or Conformances."


class PropertyValue(XS_AnySimpleType):

    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "PropertyValue"
    _title       = "Property Value"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(PropertyValue,self).__init__(*args,**kwargs)


    # UML Attribute
    validMin = MetadataAtomicField.Factory("decimalfield",blank=True,)
# UML Attribute
    validMax = MetadataAtomicField.Factory("decimalfield",blank=True,)
# UML Attribute
    fillValue = MetadataAtomicField.Factory("charfield",blank=True,)
    fillValue.help_text = "The value to use when the real value is unavailable (ie: cannot be coupled)."
                # UML Attribute
    numericalType = MetadataAtomicField.Factory("charfield",blank=True,)
    numericalType.help_text = "The datatype of the value: string, int, double, etc."


class Property(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False
    _abstract = True

    _name        = "Property"
    _title       = "Property"
    _description = "An abstract property is simply a name/value pair.  Properties may be grouped into PropertyGroups.  Properties are used to describe features of a class whose details can't be known beforehand and, hence, can't be hard-coded into the schema.  "

    def __init__(self,*args,**kwargs):
        super(Property,self).__init__(*args,**kwargs)


    # UML Attribute
    value = MetadataManyToOneField(sourceModel='cim_1_8_1.Property',targetModel='cim_1_8_1.PropertyValue',blank=True,)
    # UML Attribute
    name = MetadataAtomicField.Factory("charfield",blank=True,)





class PropertyGroup(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "PropertyGroup"
    _title       = "Property Group"
    _description = "A collection of Properties.  A PropertyGroup can itself contain other PropertyGroups."

    def __init__(self,*args,**kwargs):
        super(PropertyGroup,self).__init__(*args,**kwargs)


    # UML Attribute
    _id = MetadataManyToOneField(sourceModel='cim_1_8_1.PropertyGroup',targetModel='cim_1_8_1.Identifier',blank=True,)
    _id.help_text = "A unique id for this group of properties."
                # UML Attribute
    name = MetadataAtomicField.Factory("charfield",blank=True,)
    name.help_text = "The name of this group of properties."


class Change(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "Change"
    _title       = "Change"
    _description = "A description of [a set of] changes applied at a particular time, by a particular party, to a particular unit of metadata (identified using XPath). Currently unused in the CIM."

    def __init__(self,*args,**kwargs):
        super(Change,self).__init__(*args,**kwargs)


    # UML Attribute
    name = MetadataAtomicField.Factory("charfield",blank=True,)
    name.help_text = "A mnemonic for describing a particular change."
                # UML Attribute
#    changeTarget = MetadataManyToOneField(sourceModel='cim_1_8_1.Change',targetModel='cim_1_8_1.Document',blank=True,)
#    changeTarget.help_text = "The CIM element being changed.  If this is blank, then it is implied by the target of its parent (a Change instance currently can only appear as part of a reference which has a target anyway)."
                # UML Attribute
    changeDate = MetadataAtomicField.Factory("datefield",blank=True,)
    changeDate.help_text = "The date the change was implemented."
                # UML Attribute
#    changeAuthor = MetadataManyToOneField(sourceModel='cim_1_8_1.Change',targetModel='cim_1_8_1.ResponsibleParty',blank=True,)
#    changeAuthor.help_text = "The person that made the change."
                # UML Attribute
    type = MetadataEnumerationField(enumeration='cim_1_8_1.ChangePropertyType',blank=True,)
# UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)


class ChangePropertyType(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ChangePropertyType"
    _title       = "Change Property Type"
    _description = "A list of modification types.  Modifications are optional sub-elements of references that describe how the referenced element has changed.  They are particularly relevant for ensemble members and conformances (where the modification types modelMod or inputMod would be used)."

    CHOICES = [
    "InputMod",
        "ModelMod",
        "Decrement",
        "Increment",
        "Redistribution",
        "Replacement",
        "ParameterChange",
        "CodeChange",
        "AncillaryFile",
        "BoundaryCondition",
        "InitialCondition",
        "Unused",

    ]

    open     = False
    nullable = False
    multi    = False

class ChangeProperty(Property):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "ChangeProperty"
    _title       = "Change Property"
    _description = "A description of a single change applied to a single target.  Every ChangeProperty has a description, and may also have a name from a controlled vocabulary and a value.Currently unused in the CIM."

    def __init__(self,*args,**kwargs):
        super(ChangeProperty,self).__init__(*args,**kwargs)


    # UML Attribute
    description = MetadataAtomicField.Factory("charfield",blank=True,)
    description.help_text = "A text description of the change.  May be used in addition to, or instead of, the more formal description provided by the value attribute."
                # UML Attribute
    _id = MetadataManyToOneField(sourceModel='cim_1_8_1.ChangeProperty',targetModel='cim_1_8_1.Identifier',blank=True,)


