"""Collection of functions and classes for use in REE analyses stuff."""

from osgeo import gdal,ogr,osr
import os
import numpy as np

gdal.UseExceptions()

# generate key for type labels
_ogrTypeLabels={getattr(ogr, n): n for n in dir(ogr) if n.find('wkb') == 0}
_ogrPointTypes=[ k for k, v in _ogrTypeLabels.items() if v.find('Point') != -1]
_ogrLineTypes=[ k for k, v in _ogrTypeLabels.items() if v.find('Line') != -1]
_ogrPolyTypes=[ k for k, v in _ogrTypeLabels.items() if v.find('Polygon') != -1]
_ogrMultiTypes=[ k for k, v in _ogrTypeLabels.items() if v.find('Multi') != -1]

_ogrErrLabels={getattr(ogr, n): n for n in dir(ogr) if n.find('OGRERR_') == 0}

class DataPrefix(object):
    """ Manage Data-related prefix labelling for generalized field labels.

    Args:
        prefix (str): The prefix to assign to any requested field name

    """

    def __init__(self,prefix):

        self._pref = prefix

    def __getitem__(self, lbl):
        """ Retrieve label with prefix applied.

        Args:
            lbl (str): The label to prefix.

        Returns:
            str: The prefixed label.
        """
        return '_'.join([self._pref,lbl])

    def __repr__(self):
        return f'Prefix: "{self._pref}"'

class REE_Workspace(object):
    """Manages filepaths associated with a collection of data.

    Attributes:
        workspace (str): Path to the root directory of the workspace collection.

    Args:
        workspace_dir (str): The root directory for the workspace.
        **kwargs: Additional key-path pairs to assign.

    """

    def __init__(self,workspace_dir,**kwargs):
        self.workspace = workspace_dir
        self._entries={}
        self._entries.update(kwargs)

    def __getitem__(self, item):
        """Retrieve a path for a given key.

        Args:
            item (str): The path to retrieve.

        Returns:
            str: The requested path.

        Raises:
            KeyError: If `item` does not exist in self.
        """

        try:
            basename = self._entries[item]
        except KeyError:
            raise KeyError(f"Path '{item}' not found in {self.__class__.__name__}")
        if not os.path.isabs(basename):
            return os.path.abspath(os.path.join(self.workspace,basename)).replace('\\','/')
        return basename

    def __setitem__(self, key, value):
        """Assign a path to a key.

        Args:
            key (str): The key to identify the path with.
            value (str): The path to assign.

        Raises:
        ------
            ValueError: `value` is not of type `str`.
        """

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

    def __repr__(self):
        return f'Root:"{self.workspace}" Tags: {self._entries}'

    def DeleteFiles(self,*args,**kwargs):
        """Delete the specified files.

        Args:
            *args: List of keys of files to delete.
            **kwargs: Optional keyword arguments.

        Keyword Args:
            printFn (Callable(str...),optional): function invoked for printing messages.
                Should conform to print function signature.
        """

        printFn = kwargs.get('printFn',print)
        toDelete = args if len(args)>0 else self._entries.keys()
        for k in toDelete:
            if k in self:
                DeleteFile(self[k],printFn)


def ParseWorkspaceArgs(vals,workspace,outputs):
    """Parse out script arguments into a workspace.

    Args:
        vals (dict): The arguments to parse.
        workspace (REE_Workspace): The destination of any values prefixed with `IN_`.
        outputs (REE_Workspace): The destination of any values prefixed with `OUT_`.
    """

    for k,v in vals.items():
        if isinstance(v,str):
            if k.startswith('IN_'):
                workspace[k[3:]]=v
            elif k.startswith('OUT_'):
                outputs[k[4:]]=v

def ListFieldNames(featureclass):
    """
    Lists the fields in a feature class, shapefile, or table in a specified dataset.

    Args:
        featureclass (osgeo.ogr.Layer): Layer to query for field names.

    Returns:
        list: The names of each field (as strs).
    """

    fDefn = featureclass.GetLayerDefn()
    field_names = [fDefn.GetFieldDefn(i).GetName() for i in range(fDefn.GetFieldCount())]

    return field_names



def FieldValues(lyr, field):
    """Create a list of unique values from a field in a feature class.

    Args:
        lyr (osgeo.ogr.Layer): The Layer/FeatureClass to query.
        field (str): The name of the field to query.

    Returns:
        list: The values of `field` for each feature in `lyr`.
    """

    unique_values = [None] * lyr.GetFeatureCount()
    for i,feat in enumerate(lyr):
        unique_values[i] = feat.GetField(field)
    lyr.ResetReading()

    return unique_values

def DeleteFile(path,printFn=print):
    """Remove a file if present.

    Args:
        path (str): The file to delete, if present.
        printFn (Callable(str...),optional): Custom print function to use for feedback.
            Defaults to built in `print` function.
    """

    if os.path.exists(path):
        os.remove(path)
        printFn("Deleted existing files:", path)
    else:
        printFn(path, "not found in geodatabase!  Creating new...")


def SpatialJoinCentroid(targetLyr, joinLyr, outDS):
    """Join two layers based on area/centroid intersect.

    Args:
        targetLyr (osgeo.ogr.Layer): The layer containing geometry whose centroids
            will be tested.
        joinLyr (osgeo.ogr.Layer): The layer containing geometry whose area will be tested.
        outDS (osgeo.gdal.Dataset): The Dataset to contain the new Layer

    Returns:
        osgeo.ogr.Layer: The new layer representing the joined values.
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
    """Build a fishnet grid that is culled to existing geometry.

    Args:
        outDS (osgeo.gdal.DataSet): The Dataset to contain the new layer.
        inLyr (osgeo.ogr.Layer): The Layer containing the geometry to act as a rough mask.
        cellWidth (float): The width of each cell.
        cellHeight (float): The height of each cell.
        addlFields (list,None): List of fields to copy into fishnet.

    Returns:
        osgeo.ogr.Layer: The new culled fishnet grid.
    """

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

        testGeom=ogr.Geometry(ogr.wkbPolygon)
        testGeom.AddGeometry(ring)
        if testGeom.Intersects(refGeom):
            feat = ogr.Feature(fDefn)
            feat.SetGeometry(testGeom)
            outLyr.CreateFeature(feat)

    return outLyr


def CreateCopy(inDS,path,driverName):
    """Create a copy of the provided dataset.

    Args:
        inDS (osgeo.gdal.Dataset): The dataset to copy.
        path (str): The place to copy the dataset.
        driverName (str): The name of the driver to use for saving.

    Returns:
        osgeo.gdal.Dataset: The new copy of `inDS`.
    """

    drvr = gdal.GetDriverByName(driverName)
    return drvr.CreateCopy(path,inDS)

def WriteIfRequested(inLayer,workspace,tag,drvrName = 'ESRI Shapefile',printFn =print):
    """Write out a layer if the tag is in the workspace.

    Args:
        inLayer (osgeo.ogr.Layer): The layer to potentially request.
        workspace (REE_Workspace): The workspace to query.
        tag (str): The tag to search for.
        drvrName (str,optional): The GDAL/OGR driver to use to copy `inLyr`.
            Defaults to "ESRI Shapefile".
        printFn (Callable(str,...),optional): The print function for any feedback.
            Defaults to `print` function.
    """

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
    """Join Pandas fields into an OGR layer object by mapping using custom index fields.

    Args:
        inLyr (osgeo.ogr.Layer): The layer to perform join on
        inField (str): The field to index the join against.
        joinDF (pandas.Dataframe): The Dataframe to pull values from.
        joinField (str,optional): The join field to use for mapping if index column is not being used.
        copyFields (list,optional): List of columns to copy into layer. Defaults to all columns.

    Raises:
        Exception: If `inField` is not present in `inLyr`.
        Exception: If `joinField` is present but not found in `joinDF`.
    """
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


def BuildLookups(lyr,indFields):
    """Build lookup for index fields for inclusion of index-based array.

    Args:
        lyr (osgeo.ogr.Layer): The layer to query for unique values.
        indFields (list): The list of index fields to query.

    Returns:
        dict: A mapping from an index value to an index into an array.
    """
    uniques=set()

    for feat in lyr:

        for fld in indFields:
            val = feat.GetField(fld)
            if val is not None and val!='0':
                uniques.add(val)
    lyr.ResetReading()

    return {x : i for i,x in enumerate(uniques)}


# def BuildDomainFeatureGeoms(lyr,indFields):
#
#     buckets = {x : {} for x in indFields}
#     groupedFeats = {x : {} for x in indFields}
#     for feat in lyr:
#
#         for k,b in buckets.items():
#             val = feat.GetField(k)
#             if val!=None and val!='0':
#                 mFeat = b.setdefault(val,ogr.Geometry(ogr.wkbMultiPolygon))
#                 mFeat.AddGeometry(feat.GetGeometryRef())
#                 groupedFeats[k].setdefault(val,[]).append(feat)
#
#     lyr.ResetReading()
#
#     return buckets,groupedFeats

def MarkIntersectingFeatures(testLyr,filtLyr,domInds,fcInd,hitMatrix,printFn=print):
    """Mark Domain where layers intersect.

    Args:
        testLyr (osgeo.ogr.Layer): The layer to test for intersection.
        filtLyr (osgeo.ogr.Layer): The layer to test against (the "filter").
        domInds (dict): Domain key lookup for index into `hitMatrix`.
        fcInd (int): The index into the `hitMatrix` for the `filtLyr`.
        hitMatrix (numpy.array): The matrix where domain intersections are recorded.
        printFn (Callable(str,...),optional): The print function for any feedback.
            Defaults to `print` function.
    """

    drvr = gdal.GetDriverByName('memory')
    scratchDS = drvr.Create("scratch",0,0,0,gdal.OF_VECTOR)
    scratchLyr = scratchDS.CreateLayer("blah",testLyr.GetSpatialRef())
    # cache field index

    coordTrans = osr.CoordinateTransformation(filtLyr.GetSpatialRef(), testLyr.GetSpatialRef())
    # transform filter coords

    if testLyr.GetSpatialRef().IsSame(filtLyr.GetSpatialRef())==0:
        # we need to reproject
        printFn("   Reprojecting...", end=' ')
        projLyr = scratchDS.CreateLayer("reproj", testLyr.GetSpatialRef())

        # we can ignore attributes since we are just looking at geometry
        for feat in filtLyr:
            geom = feat.GetGeometryRef()
            geom.Transform(coordTrans)
            tFeat=ogr.Feature(projLyr.GetLayerDefn())
            tFeat.SetGeometry(geom)
            projLyr.CreateFeature(tFeat)

        filtLyr=projLyr
        printFn("Done")
    else:
        printFn("   Spatial Reference match")


    printFn("\r   Clipping...",end=' ')
    testLyr.Intersection(filtLyr,scratchLyr) #,["PROMOTE_TO_MULTI=YES"])
    printFn("Done")

    # apply filter, and mark any geom encountered
    printFn("\r   Comparing...",end=' ')
    for feat in testLyr:
        for i in ('UD_index', 'SD_index', 'LD_index'):
            val = feat.GetField(i)
            if val is not None and val != '0':
                hitMatrix[domInds[val], fcInd] = 1
                break
        # ensure change propagates
        testLyr.SetFeature(feat)
    testLyr.ResetReading()
    printFn("Done")



# def MarkIntersectingFeatures(testLyr,filtLyr,domInds,fcInd,hitMatrix):
#
#     # cache field index
#     idx = filtLyr.GetName()
#     coordTrans = osr.CoordinateTransformation(filtLyr.GetSpatialRef(), testLyr.GetSpatialRef())
#     # transform filter coords
#
#     geoms = [None]*filtLyr.GetFeatureCount()
#     for i,filt in enumerate(filtLyr):
#         geom = filt.GetGeometryRef().Clone()
#         geom.Transform(coordTrans)
#         geoms[i]=geom
#     filtLyr.ResetReading()
#
#     for feat in testLyr:
#
#         for fg in geoms:
#             if feat.GetGeometryRef().Intersects(fg):
#                 for i in ('UD_index','SD_index','LD_index'):
#                     val = feat.GetField(i)
#                     if val is not None and val!='0':
#                         hitMatrix[domInds[val],fcInd]=1
#                 break
#     testLyr.ResetReading()


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
