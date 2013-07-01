
################
#   Django-CIM-Forms
#   Copyright (c) 2012 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
################

__author__="allyn.treshansky"
__date__ ="Jul 1, 2013 10:52:19 AM"

"""
.. module:: custom_models

Summary of module goes here

"""


from dcf.models import *
from dcf.cim_1_8_1.models import *
    
class GridTypeEnum(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "GridType"
    _title       = "Grid Type"
    _description = ""

    CHOICES = [
        "cubed_sphere",
        "displaced_pole",
        "icosohedra_geodesic",
        "reduced_gaussian",
        "regular_lat_lon",
        "spectra_gaussian",
        "tripolar",
        "yin_yang",
        "composite",
        "other",
    ]

    open     = True
    nullable = False
    multi    = False


class RefinementTypeEnum(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "RefinementType"
    _title       = "Refinement Type"
    _description = ""

    CHOICES = [
        "none",
        "integer",
        "rational",
    ]

    open     = True
    nullable = False
    multi    = False


class DiscretizationEnum(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "DiscretizationEnum"
    _title       = "Discretization Enum"
    _description = ""

    CHOICES = [
        "logically_rectangular",
        "structured_triangular",
        "unstructured_triangular",
        "pixel-based_catchment",
        "unstructured_polygonal",
        "spherical_harmonics",
        "other",
     ]

    open     = True
    nullable = False
    multi    = False

class GeometryTypeEnum(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "GeometryTypeEnum"
    _title       = "GeometryType Enum"
    _description = ""

    CHOICES = [
        "ellipsoid",
        "plane",
        "sphere",
     ]

    open     = True
    nullable = False
    multi    = False


class VerticalCoordinateTypeEnum(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "VerticalCoordinateTypeEnum"
    _title       = "VerticalCoordinateTypeEnum"
    _description = ""

    CHOICES = [
        "terrain-following",
        "space-based",
        "mass-based",
        "hybrid",
        "not-applicable",
     ]

    open     = True
    nullable = False
    multi    = False

class VerticalCoordinateFormEnum(MetadataEnumeration):
    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "VerticalCoordinateFormEnum"
    _title       = "VerticalCoordinateFormEnum"
    _description = ""

    CHOICES = [
        "sigma",
        "S-coordinate",
        "Z*-coordinate",
        "isopycnic",
        "isentropic",
        "pressure",
        "natrual log pressure",
        "pressure-height",
        "P*-coordinate",
        "Z-coordinate",
        "Z**-coordinate",
        "hybrid-sigma-pressure",
        "hybrid-sigma-z",
        "hybrid-height",
        "hybrid Z-S",
        "double sigma",
        "hybrid Z-isopycnic",
        "hybrid floating Lagrangian",
        "depth",
     ]

    open     = True
    nullable = False
    multi    = False





###
###
###


class GridExtent(MetadataModel):

    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "GridExtent"
    _title       = "Grid Extent"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(GridExtent,self).__init__(*args,**kwargs)

    latMin          = MetadataAtomicField.Factory("integerField")
    latMax          = MetadataAtomicField.Factory("integerField")
    lonMin          = MetadataAtomicField.Factory("integerField")
    lonMax          = MetadataAtomicField.Factory("integerField")
    #units           = MetadataEnumerationField(enumeration='cim_1_8_1.UnitType',blank=True,)
    units           = MetadataAtomicField.Factory("charField")



class CoordList(MetadataModel):

    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "CoordList"
    _title       = "Coord List"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(CoordList,self).__init__(*args,**kwargs)

    length              = MetadataAtomicField.Factory("integerField",blank=True)
    hasConstantOffset   = MetadataAtomicField.Factory("booleanField",blank=True)
    uom                 = MetadataAtomicField.Factory("charField",blank=True)
    list                = MetadataAtomicField.Factory("charField")


class VerticalCoordList(CoordList):

    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "VerticalCoordList"
    _title       = "Vertical Coord List"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(VerticalCoordList,self).__init__(*args,**kwargs)

    coordinateType    = MetadataEnumerationField(enumeration='cim_1_8_1.VerticalCoordinateTypeEnum',blank=True,)
    coordinateForm    = MetadataEnumerationField(enumeration='cim_1_8_1.VerticalCoordinateFormEnum',blank=True,)


class SimpleGridGeometry(MetadataModel):

    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "SimpleGridGeometry"
    _title       = "Simple Grid Geometry"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(SimpleGridGeometry,self).__init__(*args,**kwargs)

    xcoords             = MetadataManyToOneField(sourceModel='cim_1_8_1.SimpleGridGeometry',targetModel='cim_1_8_1.CoordList',blank=False)
    ycoords             = MetadataManyToOneField(sourceModel='cim_1_8_1.SimpleGridGeometry',targetModel='cim_1_8_1.CoordList',blank=False)
    zcoords             = MetadataManyToOneField(sourceModel='cim_1_8_1.SimpleGridGeometry',targetModel='cim_1_8_1.VerticalCoordList',blank=True)
    numDims             = MetadataAtomicField.Factory("integerField")
    dimOrder            = MetadataAtomicField.Factory("charField")
    isMesh              = MetadataAtomicField.Factory("booleanField")

class GridTile(MetadataModel):

    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "GridTile"
    _title       = "Grid Tile"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(GridTile,self).__init__(*args,**kwargs)

    _id                 = MetadataAtomicField.Factory("charField")
    nx                  = MetadataAtomicField.Factory("integerField")
    ny                  = MetadataAtomicField.Factory("integerField")
    nz                  = MetadataAtomicField.Factory("integerField")
    discretizationType  = MetadataEnumerationField(enumeration='cim_1_8_1.DiscretizationEnum',blank=True,)
    geometryType        = MetadataEnumerationField(enumeration='cim_1_8_1.GeometryTypeEnum',blank=True,)
    isConformal         = MetadataAtomicField.Factory("booleanField")
    isRegular           = MetadataAtomicField.Factory("booleanField")
    isTerrainFollowing  = MetadataAtomicField.Factory("booleanField")
    isUniform           = MetadataAtomicField.Factory("booleanField")
    refinementScheme    = MetadataEnumerationField(enumeration='cim_1_8_1.RefinementTypeEnum',blank=True,)
    #area
    #cellArray           = MetadataManyToOneField(sourceModel='cim_1_8_1.GridTile',targetModel='cim_1_8_1.GridCellArray',blank=True)
    #cellRefArray        = MetadataManyToOneField(sourceModel='cim_1_8_1.GridTile',targetModel='cim_1_8_1.GridCellRefArray',blank=True)
    coordFile           = MetadataAtomicField.Factory("charField")
    #coordinatePole
    description         = MetadataAtomicField.Factory("textField")
    extent              = MetadataManyToOneField(sourceModel='cim_1_8_1.GridTile',targetModel='cim_1_8_1.GridExtent',blank=True)
    #gridNorthPole
    #horizontalCRS
    #horizontalResolution
    longName            = MetadataAtomicField.Factory("charField")
    mnemonic            = MetadataAtomicField.Factory("charField")
    shortName           = MetadataAtomicField.Factory("charField")
    simpleGridGeom      = MetadataManyToOneField(sourceModel='cim_1_8_1.GridTile',targetModel='cim_1_8_1.SimpleGridGeometry',blank=True)
    #verticalCRS
    #verticalResolution
    zcoords             = MetadataManyToOneField(sourceModel='cim_1_8_1.GridTile',targetModel='cim_1_8_1.VerticalCoordList',blank=True)



class GridMosaic(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "GridMosaic"
    _title       = "Grid Mosaic"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(GridMosaic,self).__init__(*args,**kwargs)

    _id                 = MetadataAtomicField.Factory("charField")
    shortName           = MetadataAtomicField.Factory("charField")
    longName            = MetadataAtomicField.Factory("charField")
    description         = MetadataAtomicField.Factory("textField")
    gridType            = MetadataEnumerationField(enumeration='cim_1_8_1.GridTypeEnum',blank=False,)
    congruentTiles      = MetadataAtomicField.Factory("booleanField")
    isLeaf              = MetadataAtomicField.Factory("booleanField")
    extent              = MetadataManyToOneField(sourceModel='cim_1_8_1.GridMosaic',targetModel='cim_1_8_1.GridExtent',blank=True)
    mnemonic            = MetadataAtomicField.Factory("charField")
    refinementScheme    = MetadataEnumerationField(enumeration='cim_1_8_1.RefinementTypeEnum',blank=True,)
    numTiles            = MetadataAtomicField.Factory("integerField")
    numMosaics          = MetadataAtomicField.Factory("integerField")
    gridTile            = MetadataManyToManyField(sourceModel='cim_1_8_1.GridMosaic',targetModel='cim_1_8_1.GridTile',blank=True)
    gridMosaic          = MetadataManyToManyField(sourceModel='cim_1_8_1.GridMosaic',targetModel='cim_1_8_1.GridMosaic',blank=True)

class CustomGrid(MetadataModel):


    class Meta:
        app_label = "cim_1_8_1"
        abstract = False

    _name        = "CustomGrid"
    _title       = "Custom Grid"
    _description = ""

    def __init__(self,*args,**kwargs):
        super(CustomGrid,self).__init__(*args,**kwargs)

    esmModelGrid        = MetadataManyToManyField(sourceModel='cim_1_8_1.CustomGrid',targetModel='cim_1_8_1.GridMosaic',blank=True)
    esmExchangeGrid     = MetadataManyToManyField(sourceModel='cim_1_8_1.CustomGrid',targetModel='cim_1_8_1.GridMosaic',blank=True)


