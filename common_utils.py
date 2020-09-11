from osgeo import gdal,ogr,osr
import os
import math
import numpy as np
import pandas as pd

gdal.UseExceptions()

# generate key for type labels
_ogrTypeLabels={getattr(ogr, n): n for n in dir(ogr) if n.find('wkb') == 0}
_ogrPointTypes=[ k for k, v in _ogrTypeLabels.items() if v.find('Point') != -1]
_ogrLineTypes=[ k for k, v in _ogrTypeLabels.items() if v.find('Line') != -1]
_ogrPolyTypes=[ k for k, v in _ogrTypeLabels.items() if v.find('Polygon') != -1]
_ogrMultiTypes=[ k for k, v in _ogrTypeLabels.items() if v.find('Multi') != -1]

_ogrErrLabels={getattr(ogr, n): n for n in dir(ogr) if n.find('OGRERR_') == 0}

class REE_Workspace(object):

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


def ParseWorkspaceArgs(vals,workspace,outputs):

    for k,v in vals.items():
        if isinstance(v,str):
            if k.startswith('IN_'):
                workspace[k[3:]]=v
            elif k.startswith('OUT_'):
                outputs[k[4:]]=v

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

def FieldBeginsWithValues(lyr, field):
    """
        Create a list of unique values from any field that starts with the provided field name.

        Parameters
        ----------
        table: <str>
            Name of the table or feature class

        field: <str>
            Name of the field

        Returns
        -------
        unique_values: <list>
            list of Field values for each matched field
        """

    names = ListFieldNames(lyr)
    ret = []
    for n in names:
        if n.find(field)==0:
           ret.append(FieldValues(lyr,n))

    return ret

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


def SpatialJoinCentroid(targetLyr, joinLyr, outDS):
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

        # add feature to output
        outLyr.CreateFeature(newFeat)

    targetLyr.ResetReading()

    return outLyr


def IndexFeatures(outDS,inLyr, cellWidth,cellHeight,addlFields=None):

    # https://stackoverflow.com/questions/59189072/creating-fishet-grid-using-python
    xMin,xMax,yMin,yMax = inLyr.GetExtent()

    # create reference geometry
    refGeom=ogr.Geometry(ogr.wkbMultiPolygon)
    for feat in inLyr:
        refGeom.AddGeometry(feat.GetGeometryRef())

    refGeom = refGeom.UnionCascaded()

    dx = cellWidth / 2
    dy = cellHeight / 2

    # offset for nearest even boundaries(shift by remainder in difference of extent and cell size intervals)
    # I don't see any offest with arc results along the x, so let's do that.
    xOffs = 0# (xMax - xMin) % cellWidth
    yOffs=(yMax-yMin)%cellHeight
    xVals, yVals = np.meshgrid(
        np.arange(xMin+dx+xOffs,xMax+dx+xOffs,cellWidth),
        np.arange(yMax + dy-yOffs, yMin + dy-yOffs, -cellHeight),
    )

    outLyr = outDS.CreateLayer('indexed_features',inLyr.GetSpatialRef(),ogr.wkbPolygon)

    fDefn = outLyr.GetLayerDefn()
    if addlFields is not None:
        for fld in addlFields:
            fDefn.AddFieldDefn(fld)


    for x,y in zip(xVals.ravel(),yVals.ravel()):
        # use function calls instead of wkt string to avoid excessive string construction
        ring=ogr.Geometry(ogr.wkbLinearRing)

        ring.AddPoint(x - dx,y - dy)
        ring.AddPoint(x + dx,y - dy)
        ring.AddPoint(x + dx,y + dy)
        ring.AddPoint(x - dx,y + dy)
        ring.AddPoint(x - dx,y - dy)

        # poly_wkt = f'POLYGON (({x-dx} {y-dy},' \
        #            f'{x+dx} {y-dy},' \
        #            f'{x+dx} {y+dy},' \
        #            f'{x-dx} {y+dy},' \
        #            f'{x-dx} {y-dy}))'

        testGeom=ogr.Geometry(ogr.wkbPolygon)
        testGeom.AddGeometry(ring)
        if testGeom.Intersects(refGeom):
            feat = ogr.Feature(fDefn)
            feat.SetGeometry(testGeom)
            outLyr.CreateFeature(feat)



    return outLyr


def CreateCopy(inDS,path,driverName):

    drvr = gdal.GetDriverByName(driverName)
    return drvr.CreateCopy(path,inDS)

def WriteIfRequested(inLayer,workspace,tag,drvrName = 'ESRI Shapefile',printFn =print):

    if tag in workspace:

        drvr = gdal.GetDriverByName(drvrName)
        outPath = workspace[tag]
        if os.path.exists(outPath):
            DeleteFile(outPath,printFn)
        ds= drvr.Create(outPath,0,0,0,gdal.OF_VECTOR)
        outLyr=ds.CopyLayer(inLayer,inLayer.GetName())
        ds.FlushCache()

        printFn("Created new file:", outPath)

def OgrPandasJoin(inLyr, inField, joinDF, joinField=None,copyFields = None):

    # ensure that fields exist
    lyrDefn = inLyr.GetLayerDefn()
    if lyrDefn.GetFieldDefn(lyrDefn.GetFieldIndex(inField)) is None:
        raise Exception("'inField' not in 'inLyr'")

    if joinField is None:
        keys = joinDF.index
    else:
        if joinField not in joinDF:
            raise Exception("'joinField' not in 'joinDF'")
        keys = joinDF[joinField]

    # assume joining all fields if
    if copyFields is None:
        copyFields = list(joinDF.columns)

    # add fields to layer definition

    for f in copyFields:
        fldType = ogr.OFTReal if joinDF.dtypes[f]!=object else ogr.OFTString
        # for now
        inLyr.CreateField(ogr.FieldDefn(f,fldType))

    # build join map
    lookupTable = {}
    for r, v in enumerate(keys):
        lookupTable[v] = r

    #proceed to iterate through features, joining attributes
    for feat in inLyr:
        val=feat.GetField(inField)
        row = lookupTable[val]

        for n in copyFields:
            feat.SetField(n,joinDF[n][row])

        # refresh feature
        inLyr.SetFeature(feat)
    inLyr.ResetReading()

def LayerToGeom(lyr):

    gType = lyr.GetGeomType()

    ret = None
    if gType in _ogrPointTypes:
        ret = ogr.Geometry(ogr.wkbMultiPoint)

    elif gType in _ogrLineTypes:
        ret = ogr.Geometry(ogr.wkbMultiLineString)
    elif gType in _ogrPolyTypes:
        ret = ogr.Geometry(ogr.wkbMultiPolygon)
    else:
        print(f"Unsupported Geometry Type: {_ogrTypeLabels[gType]}")

    if gType not in _ogrMultiTypes:
        for feat in lyr:
            res=ret.AddGeometry(feat.GetGeometryRef().Clone())
            if res!=ogr.OGRERR_NONE:
                raise Exception(f"Geometry Error {_ogrErrLabels[res]}; {feat.ExportToWkt()}")
        lyr.ResetReading()
    else:
        for feat in lyr:
            for sub in feat.GetGeometryRef():
                res=ret.AddGeometry(sub)
                if res!=ogr.OGRERR_NONE:
                    raise Exception(f"Geometry Error {_ogrErrLabels[res]}; {sub.ExportToWkt()}")
        lyr.ResetReading()

    return ret

def MarkIntersectingFeatures(testLyr,filtLyr):

    # cache field index
    idx = testLyr.GetLayerDefn().GetFieldIndex(filtLyr.GetName())
    coordTrans = osr.CoordinateTransformation(filtLyr.GetSpatialRef(), testLyr.GetSpatialRef())
    # transform filter coords

    # convert geometry to multi-eqivalent
    filtGeom = LayerToGeom(filtLyr)

    filtGeom.Transform(coordTrans)

    # apply filter, and mark any geom encountered
    testLyr.SetSpatialFilter(filtGeom)
    for feat in testLyr:
        feat.SetField(idx,1)
        # ensure change propagates
        testLyr.SetFeature(feat)
    testLyr.ResetReading()
    testLyr.SetSpatialFilter(None)

# def MarkIntersectingFeatures(testLyr,filtLyr):
#
#     # cache field index
#     idx = testLyr.GetLayerDefn().GetFieldIndex(filtLyr.GetName())
#     coordTrans = osr.CoordinateTransformation(filtLyr.GetSpatialRef(), testLyr.GetSpatialRef())
#     # transform filter coords
#
#     geoms = []
#     for filt in filtLyr:
#         geom = filt.GetGeometryRef()
#         geoms.append(geom.Transform(coordTrans))
#     filtLyr.ResetReading()
#
#     for feat in testLyr:
#
#         for fg in geoms:
#             if feat.GetGeometryRef().Intersects(fg):
#                 feat.SetField(idx,1)
#                 # testLyr.SetFeature(feat)
#                 break
#     testLyr.ResetReading()
#

# def MarkIntersectingFeatures(testLyr,filtLyr):
#
#     # cache field index
#     idx = testLyr.GetLayerDefn().GetFieldIndex(filtLyr.GetName())
#     coordTrans = osr.CoordinateTransformation(filtLyr.GetSpatialRef(), testLyr.GetSpatialRef())
#     # transform filter coords
#
#     geoms = [filt.GetGeometryRef().Transform(coordTrans).ExportToWkt() for filt in filtLyr]
#     filtLyr.ResetReading()
#
#     import mprocs
#
#     for feat in testLyr:
#         mprocs.testIntersects(feat,geoms)
#     testLyr.ResetReading()
#


def GetFilteredFeatures(inLyr,filterLyr):

    print(f"applying filter on: {inLyr.GetName()}")
    # build coordinate transformation
    coordTrans = osr.CoordinateTransformation(filterLyr.GetSpatialRef(), inLyr.GetSpatialRef())

    # grab geometry from filterLyr as multiPolygon
    filtGeom = ogr.Geometry(ogr.wkbMultiPolygon)
    for feat in filterLyr:
        geom = feat.GetGeometryRef()
        if geom.GetGeometryType() == ogr.wkbPolygon:
            filtGeom.AddGeometry(geom)
        elif geom.GetGeometryType() == ogr.wkbMultiPolygon:
            for g in geom.GetGeometryCount():
                filtGeom.AddGeometry(geom.GetGeometryRef(g))
        else:
            #raise Exception(f"Unknown Geometry Type: {geom.GetGeometryType()}")
            print(f"Unknown Geometry Type: {_ogrTypeLabels[geom.GetGeometryType()]}")
    filterLyr.ResetReading()

    # transform filter geometry
    filtGeom.Transform(coordTrans)

    # apply filter to inLyr
    inLyr.SetSpatialFilter(filtGeom)

    ret = []
    for feat in inLyr:
        ret.append(feat)
    inLyr.ResetReading()

    # clear filter
    inLyr.SetSpatialFilter(None)

    return ret

def CopyFilteredFeatures(inLyr,filterLyr,dsOrLyr):


    # build new layer
    if isinstance(dsOrLyr,gdal.Dataset):
        outLyr=dsOrLyr.CreateLayer(inLyr.GetName()+"_selected",inLyr.GetSpatialRef(),inLyr.GetGeomType())
        inDefn = inLyr.GetLayerDefn()
        outDefn = outLyr.GetLayerDefn()
        for i in range(inDefn.GetFieldCount()):
            outDefn.AddFieldDefn(inDefn.GetFieldDefn(i))
    else:
        outLyr = dsOrLyr

    # copy filtered features into new layer
    # spatial filter is active
    for feat in GetFilteredFeatures(inLyr,filterLyr):
        outLyr.AddFeature(feat)

    return outLyr

def GetFilteredUniqueValues(inLyr,filterLyr,field):

    ret = set()

    # copy filtered features into new layer
    # spatial filter is active
    for feat in GetFilteredFeatures(inLyr,filterLyr):
        ret.add(feat.GetField(field))

    return ret
