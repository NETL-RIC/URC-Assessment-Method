from osgeo import gdal,ogr
import os
import math
import numpy as np
from typing import Callable

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
            return os.path.join(self.workspace,basename)
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

def ListFieldNames(featureclass : ogr.Layer) -> list:
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



def FieldValues(lyr : ogr.Layer, field : str) -> list:
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
    fIdx = lyr.GetFeatureDefn().GetFieldIndex(field)
    for i in range(lyr.GetFeatureCount()):
        feat = lyr.GetFeature(i)
        unique_values[i] = feat.GetFieldAsDouble(field)

    return unique_values


def DeleteFile(path : str,printFn : Callable[...,None] =print):
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


def IndexFeatures(inLyr : ogr.Layer, outpath, cellWidth : float,cellHeight : float) -> (gdal.Dataset,ogr.Layer):

    # https://stackoverflow.com/questions/59189072/creating-fishet-grid-using-python
    xMin,xMax,yMin,yMax = inLyr.GetExtent()


    dx = cellWidth / 2
    dy = cellHeight / 2

    xVals, yVals = np.meshgrid(
        np.arange(xMin+dx,xMax+dx,cellWidth),
        np.arange(yMin + dy, yMax + dy, cellHeight),
    )

    drvr = gdal.GetDriverByName('ESRI Shapefile')
    outDS =drvr.Create(outpath,0,0,0,gdal.OF_VECTOR)
    outLyr = outDS.CreateLayer(outpath,inLyr.GetSpatialRef(),ogr.wkbPolygon)

    fDefn = outLyr.GetLayerDefn()

    for x,y in zip(xVals.ravel(),yVals.ravel()):
        poly_wkt = f'POLYGON (({x-dx} {y-dy},' \
                   f'{x+dx} {y-dy},' \
                   f'{x+dx} {y+dy},' \
                   f'{x-dx} {y+dy},' \
                   f'{x-dx} {y-dy}))'

        feat = ogr.Feature(fDefn)
        feat.SetGeometry(ogr.CreateGeometryFromWkt(poly_wkt))
        outLyr.CreateFeature(feat)
    return outDS,outLyr


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

    # create output fields
    outLyr = outDS.CreateLayer("merged",targetLyr.GetSpatialRef(),targetLyr.GetGeomType())

    # define union of fields
    outDefn = outLyr.GetLayerDefn()

    tDefn = targetLyr.GetLayerDefn()
    joinFldOffset = tDefn.GetLayerCount()
    for i in range(joinFldOffset):
        outDefn.AddField(tDefn.GetField(i))
    jDefn = joinLyr.GetLayerDefn()
    for i in range(jDefn.GetLayerCount()):
        outDefn.AddField(jDefn.GetField(i))

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
            newFeat.AddField(tFeat.GetField(i))

        # find geom in join, if any
        centroid = geom.Centroid()
        selFeat = None
        for jFeat in joinLyr:
            if jFeat.GetGeometryRef().Contains(centroid):
                selFeat = jFeat
                break
        joinLyr.ResetReading()

        # append fields if intersect is found
        if selFeat is not None:
            for i in range(jDefn.GetFieldCount()):
                newFeat.AddField(selFeat.GetField(i))

        #add feature to output
        outLyr.CreateFeature(selFeat)

    targetLyr.ResetReading()

    return outLyr


def CreateCopy(inDS : gdal.Dataset,path : str,driverName : str) -> gdal.Dataset:

    drvr = gdal.GetDriverByName(driverName)
    return drvr.CreateCopy(path,inDS)