from osgeo import gdal,ogr,osr
import os
import math
import numpy as np
import pandas as pd

from typing import Callable

gdal.UseExceptions()

class PE_Workspace(object):

    def __init__(self,workspace_dir,**kwargs):
        self.workspace = workspace_dir
        self._entries={}
        self._entries.update(kwargs)

    def __getitem__(self, item):

        try:
            basename = self._entries[item]
        except KeyError:
            raise KeyError(f"Path '{item}' not found in {self.__class__.__name__}")
        if not os.path.isabs(basename):
            return os.path.abspath(os.path.join(self.workspace,basename)).replace('\\','/')
        return basename

    def __setitem__(self, key, value):
        if not isinstance(value,str):
            raise ValueError("value must be of type 'str'")
        self._entries[key] = value

    def __contains__(self,item):
        return item in self._entries

    def __iter__(self):
        for k in self._entries.keys():
            yield self[k]

    def __dict__(self):
        ret = {}
        for k in self._entries.keys():
            ret[k]=self[k]
        return ret

    def __len__(self):
        return len(self._entries)

    def DeleteFiles(self,*args,**kwargs):
        printFn = kwargs.get('printFn',print)
        toDelete = args if len(args)>0 else self._entries.keys()
        for k in toDelete:
            if k in self:
                DeleteFile(self[k],printFn)

def ListFieldNames(featureclass):
    """
    Lists the fields in a feature class, shapefile, or table in a specified dataset.

    Parameters
    ----------
    featureclass: <ogr.Layer
        Layer to query for field names
    Returns
    -------
    <list>
        Field names
    """

    fDefn = featureclass.GetLayerDefn()
    field_names = [fDefn.GetFieldDefn(i).GetName() for i in range(fDefn.GetFieldCount())]

    return field_names



def FieldValues(lyr, field):
    """
    Create a list of unique values from a field in a feature class.

    Parameters
    ----------
    table: <str>
        Name of the table or feature class

    field: <str>
        Name of the field

    Returns
    -------
    unique_values: <list>
        Field values
    """

    unique_values = [None] * lyr.GetFeatureCount()
    for i,feat in enumerate(lyr):
        unique_values[i] = feat.GetField(field)
    lyr.ResetReading()

    return unique_values


def DeleteFile(path,printFn=print):
    """Remove a file if present

    Parameters
    ----------
    path: <str>
        The file to delete, if present

    printFn: <Callable(str...)>
        Function that takes in one or more strings meant for feedback messages. Defaults to std print.

    """
    if os.path.exists(path):
        os.remove(path)
        printFn("Deleted existing files:", path)
    else:
        printFn(path, "not found in geodatabase!  Creating new...")


def IndexFeatures(outDS:gdal.Dataset,inLyr : ogr.Layer, cellWidth : float,cellHeight : float,addlFields:list=None) -> (gdal.Dataset,ogr.Layer):

    # https://stackoverflow.com/questions/59189072/creating-fishet-grid-using-python
    xMin,xMax,yMin,yMax = inLyr.GetExtent()


    dx = cellWidth / 2
    dy = cellHeight / 2

    xVals, yVals = np.meshgrid(
        np.arange(xMin+dx,xMax+dx,cellWidth),
        np.arange(yMin + dy, yMax + dy, cellHeight),
    )

    outLyr = outDS.CreateLayer('indexed_features',inLyr.GetSpatialRef(),ogr.wkbPolygon)

    fDefn = outLyr.GetLayerDefn()
    if addlFields is not None:
        for fld in addlFields:
            fDefn.AddFieldDefn(fld)

    for x,y in zip(xVals.ravel(),yVals.ravel()):
        poly_wkt = f'POLYGON (({x-dx} {y-dy},' \
                   f'{x+dx} {y-dy},' \
                   f'{x+dx} {y+dy},' \
                   f'{x-dx} {y+dy},' \
                   f'{x-dx} {y-dy}))'

        feat = ogr.Feature(fDefn)
        feat.SetGeometry(ogr.CreateGeometryFromWkt(poly_wkt))
        outLyr.CreateFeature(feat)

    return outLyr


def SpatialJoinCentroid(targetLyr : ogr.Layer, joinLyr : ogr.Layer, outDS : gdal.Dataset) -> ogr.Layer:
    """

    Parameters
    ----------
    targetLyr
    joinLyr
    outDS

    Returns
    -------

    """

    transform=osr.CoordinateTransformation(targetLyr.GetSpatialRef(),joinLyr.GetSpatialRef())
    # create output fields
    outLyr = outDS.CreateLayer("merged",targetLyr.GetSpatialRef(),targetLyr.GetGeomType())

    # define union of fields
    outDefn = outLyr.GetLayerDefn()

    tDefn = targetLyr.GetLayerDefn()
    joinFldOffset = tDefn.GetFieldCount()
    for i in range(joinFldOffset):
        outDefn.AddFieldDefn(tDefn.GetFieldDefn(i))

    jDefn = joinLyr.GetLayerDefn()
    for i in range(jDefn.GetFieldCount()):
        outDefn.AddFieldDefn(jDefn.GetFieldDefn(i))

    # run through features in target;
    # get centroid;
    # find domain overlap;
    # copy geometry
    for tFeat in targetLyr:
        geom = tFeat.GetGeometryRef()
        newFeat = ogr.Feature(outDefn)
        newFeat.SetGeometry(geom)

        # copy targLayer fields
        for i in range(tDefn.GetFieldCount()):
            newFeat.SetField(i,tFeat.GetField(i))

        # find geom in join, if any
        centroid = geom.Centroid()
        centroid.Transform(transform)
        selFeat = None
        for jFeat in joinLyr:
            if jFeat.GetGeometryRef().Contains(centroid):
                selFeat = jFeat
                break
        joinLyr.ResetReading()

        # append fields if intersect is found
        if selFeat is not None:
            for i in range(jDefn.GetFieldCount()):
                newFeat.SetField(joinFldOffset+i,selFeat.GetField(i))

        #add feature to output
        outLyr.CreateFeature(newFeat)

    targetLyr.ResetReading()

    return outLyr


def CreateCopy(inDS : gdal.Dataset,path : str,driverName : str) -> gdal.Dataset:

    drvr = gdal.GetDriverByName(driverName)
    return drvr.CreateCopy(path,inDS)

def WriteIfRequested(inLayer : ogr.Layer,workspace: PE_Workspace,tag : str,drvrName : str = 'ESRI Shapefile',printFn : Callable[...,None] =print):

    if tag in workspace:

        drvr = gdal.GetDriverByName(drvrName)
        outPath = workspace[tag]
        if os.path.exists(outPath):
            DeleteFile(outPath,printFn)
        ds= drvr.Create(outPath,0,0,0,gdal.OF_VECTOR)
        ds.CopyLayer(inLayer,inLayer.GetName())
        printFn("Created new file:", outPath)

def OgrPandasJoin(inLyr : ogr.Layer, inField : str, joinDF : pd.DataFrame, joinField : str,copyFields : list = None):

    # ensure that fields exist
    lyrDefn = inLyr.GetLayerDefn()
    if lyrDefn.GetFieldDefn(lyrDefn.GetFieldIndex(inField)) is None:
        raise Exception("'inField' not in 'inLyr'")

    if joinField not in joinDF:
        raise Exception("'joinField' not in 'joinDF'")

    # assume joining all fields if
    if copyFields is None:
        copyFields = list(joinDF.columns)

    # add fields to layer definition

    for f in copyFields:
        fldType = ogr.OFTReal if joinDF.dtypes[f]==np.str else ogr.OFTString
        # for now
        inLyr.CreateField(ogr.FieldDefn(f,fldType))

    # build join map
    jCol = joinDF[joinField]
    lookupTable = {}
    for r, v in enumerate(jCol):
        lookupTable[v] = r

    #proceed to iterate through features, joining attributes
    for feat in inLyr:
        val=feat.GetField(inField)
        row = lookupTable[val]

        for n in copyFields:
            feat.SetField(n,joinDF[n][row])
    inLyr.ResetReading()