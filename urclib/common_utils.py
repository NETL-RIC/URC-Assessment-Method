"""Collection of functions that are used in both grid creation and score analyses."""

from osgeo import gdal,ogr,osr
import os
import numpy as np
from contextlib import contextmanager
from time import time

gdt_np_map = {
    gdal.GDT_Byte: np.uint8,
    gdal.GDT_UInt16: np.uint16,
    gdal.GDT_Int16: np.int16,
    gdal.GDT_UInt32: np.uint32,
    gdal.GDT_Int32: np.int32,
    gdal.GDT_Float32: np.float32,
    gdal.GDT_Float64: np.float64,
    gdal.GDT_CInt16: np.int16,
    gdal.GDT_CInt32: np.int32,
    gdal.GDT_CFloat32: np.float32,
    gdal.GDT_CFloat64: np.float64,
}

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

        self.prefix = prefix

    def __getitem__(self, lbl):
        """ Retrieve label with prefix applied.

        Args:
            lbl (str): The label to prefix.

        Returns:
            str: The prefixed label.
        """
        return '_'.join([self.prefix, lbl])

    def __repr__(self):
        return f'Prefix: "{self.prefix}"'

class REE_Workspace(object):
    """Manages filepaths associated with a collection of data.

    Attributes:
        workspace (str,optional): Path to the root directory of the workspace collection; defaults to current working
        directory.

    Args:
        workspace_dir (str): The root directory for the workspace.
        **kwargs: Additional key-path pairs to assign.

    """

    def __init__(self,workspace_dir=None,**kwargs):
        if workspace_dir is None:
            workspace_dir ='.'
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

    def __len__(self):
        return len(self._entries)

    def __delitem__(self, key):
        del self._entries[key]

    def update(self,inVals):
        self._entries.update(inVals)

    def __repr__(self):
        return f'Root:"{self.workspace}" Tags: {self._entries}'

    def keys(self):
        return self._entries.keys()

    def get(self,key,default):
        """Retrieve value of key if it exists; otherwise return the default value.

        Args:
            key (str): The tag of the path to retrieve.
            default (object): The default value to pass if a value for `key` does not exist.

        Returns:
            object: The value for `key`, or the value of `default` if no value for `key` exists.
        """
        if key in self:
            return self[key]
        return default

    def DeleteFiles(self,*args,**kwargs):
        """Delete the specified files.

        Args:
            *args: List of keys of files to delete.
            **kwargs: Optional keyword arguments.

        Keyword Args:
            printFn (Callable(str...),optional): function invoked for printing messages.
                Should conform to print function signature.
        """

        toDelete = args if len(args)>0 else self._entries.keys()
        for k in toDelete:
            if k in self:
                DeleteFile(self[k])

    def TestFilesExist(self):
        """Test each path entry to determine if path exists.

        Returns:
            list: (label,exists) for each entry in REE_workspace, where "exists" is `True` or `False` depending on
              whether a file is found at location pointed to by associated path.
        """

        # use self.__getitem__ to ensure path is expanded
        entries = ((k,self[k]) for k in self._entries.keys())
        return [(k,os.path.exists(v)) for (k,v) in entries]

    def exists(self,key):
        return key in self and os.path.exists(self[key])

@contextmanager
def do_time_capture():
    start=time()
    try:
        yield
    finally:
        end = time()
        printTimeStamp(end-start)

def printTimeStamp(rawSeconds):
    """
    Print raw seconds in nicely hour, minute, seconds format.

    Args:
        rawSeconds (int): The raw seconds to print.
    """

    totMin, seconds = divmod(rawSeconds, 60)
    hours, minutes = divmod(totMin, 60)
    print(f"Runtime: {hours} hours, {minutes} minutes, {round(seconds, 2)} seconds.")


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


def DeleteFile(path):
    """Remove a file if present.

    Args:
        path (str): The file to delete, if present.
    """

    if os.path.exists(path):
        os.remove(path)
        print("Deleted existing files:", path)
    else:
        print(path, "not found in geodatabase!  Creating new...")

def rasterDomainIntersect(inCoords, inMask, srcSRef, joinLyr, fldName, nodata=-9999):
    """Create intersect raster for specific field values in vector layer

    Args:
        inCoords (np.ndarray): Map from pixel to space coordinates.
        inMask (np.ndarray): Raw data from mask layer, with 1 is include, 0 is exclude.
        srcSRef (osr.SpatialReference): The spatial reference to project into.
        joinLyr (ogr.Layer): The vector layer to parse.
        fldName (str): The name of the field to use for indexing.
        nodata (int,optional): The value to use to represent "no data" pixels. defaults to **-9999**.

    Returns:
        np.ndarray: index values corresponding to pixel coordinates as defined with `inCoords`.
    """
    buff = np.full([inCoords.shape[0]*inCoords.shape[1]], nodata, dtype=np.int32)

    transform=osr.CoordinateTransformation(srcSRef,joinLyr.GetSpatialRef())

    for i,(x,y) in enumerate(inCoords.reshape(inCoords.shape[0]*inCoords.shape[1],inCoords.shape[2])):
        if inMask[i]==0:
            continue
        pt = ogr.Geometry(ogr.wkbPoint)
        pt.AddPoint(x,y)
        pt.Transform(transform)

        for jFeat in joinLyr:
            g = jFeat.GetGeometryRef()
            if pt.Within(g):
                fld = jFeat.GetFieldAsString(fldName)
                buff[i]=int(fld[2:])
                break
        joinLyr.ResetReading()

    return buff.reshape(inCoords.shape[0],inCoords.shape[1])

def Rasterize(id, fc_list, inDS, xSize, ySize, geotrans, srs, drvrName="mem", prefix='', suffix='', nodata=-9999,
              gdType=gdal.GDT_Int32,opts=None):
    """Convert specified Vector layers to raster.

    Args:
        id (str): The id for the new Raster dataset.
        fc_list (list): A list of list of layers to Rasterize.
        inDS (gdal.Dataset): The input dataset.
        xSize (int): The width of the new raster, in pixels.
        ySize (int): The height of the new raster, in pixels.
        geotrans (tuple): Matrix of float values describing geographic transformation.
        srs (osr.SpatialReference): The Spatial Reference System to provide for the new Raster.
        drvrName (str,optional): Name of driver to use to create new raster; defaults to "MEM".
        prefix (str,optional): Prefix to apply to `compName` for gdal.Dataset label; this could be a path to a directory
           if raster is being saved to disk.
        suffix (str,optional): Suffix to apply to `compName` for gdal.Dataset label; this could be the file extension
           if raster is being saved to disk.
        nodata (numeric,optional): The value to represent no-data in the new Raster; default is -9999
        gdType (int,optional): Flag indicating the data type for the raster; default is "gdal.GDT_Int32".

    Returns:
        gdal.Dataset: The rasterized vector layer.
    """

    path = os.path.join(prefix, id) + suffix
    drvr = gdal.GetDriverByName(drvrName)
    inOpts=[]
    if opts is not None:
        inOpts=opts
    ds = drvr.Create(path, xSize, ySize, 1, gdType,options=inOpts)

    ds.SetGeoTransform(geotrans)
    ds.SetSpatialRef(srs)
    b = ds.GetRasterBand(1)
    b.SetNoDataValue(nodata)
    fill = np.full([ySize, xSize], nodata, dtype=gdt_np_map[gdType])
    b.WriteArray(fill)

    ropts = gdal.RasterizeOptions(
        layers=[fc.GetName() for fc in fc_list]
    )
    gdal.Rasterize(ds, inDS, options=ropts)

    return ds


def IndexFeatures(inLyr, cellWidth,cellHeight,clipPath):
    """Build a fishnet grid that is culled to existing geometry.

    Args:
        inLyr (osgeo.ogr.Layer): The Layer containing the geometry to act as a rough mask.
        cellWidth (float): The width of each cell.
        cellHeight (float): The height of each cell.
        drivername (str,optional): The driver to use for generating the mask raster. Defaults to **MEM**.
        nodata (int,optional): The value to use to represent "no data" pixels. defaults to **-9999**.


    Returns:
        tuple: numpy array for coordinate mapping, and gdal.Dataset with masking info.
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

    coordMap = np.array(list(zip(xVals.ravel(),yVals.ravel()))).reshape(*xVals.shape,2)
    coordMap=np.flip(coordMap,axis=0)
    rawMask = np.zeros(xVals.shape)

    geoTrans=(coordMap[0,0,0],cellWidth,0,coordMap[0,0,1],0,cellHeight)
    clipMask = gdal.OpenEx(clipPath, gdal.OF_VECTOR)
    clipMask = Rasterize('mask', [clipMask.GetLayer(0)], clipMask, coordMap.shape[1],
                         coordMap.shape[0], geoTrans, inLyr.GetSpatialRef(), nodata=0)

    return coordMap,clipMask

def writeRaster(maskLyr, data, name, drivername='GTiff', gdtype=gdal.GDT_Byte, nodata=-9999):
    """Write a raster data to a new gdal.Dataset object

    Args:
        maskLyr (gdal.Dataset): Raster object containing mask, dimension, and geotransform information.
        data (np.ndarray): The data to write to the Dataset
        name (str): The unique identifier and (depending on the driver) the path to the file to write.
        drivername (str,optional): The driver to use to create the dataset. Defaults to **GTiff**.
        gdtype (int,optinal): The internal data type to use in the generated raster. Defaults to `gdal.GDT_Byte`.
        nodata (int,optional): The value to use to represent "no data" pixels. defaults to **-9999**.

    Returns:
        gdal.Dataset: Reference to newly created dataset; can be safely ignored if just writing to disk.
    """

    opts=[]
    if drivername.lower()=='gtiff':
        opts=['GEOTIFF_KEYS_FLAVOR=ESRI_PE']
    drvr = gdal.GetDriverByName(drivername)
    ds = drvr.Create(name, maskLyr.RasterXSize,maskLyr.RasterYSize,1,gdtype,options=opts)
    ds.SetProjection(maskLyr.GetProjection())
    ds.SetGeoTransform(maskLyr.GetGeoTransform())
    b = ds.GetRasterBand(1)
    b.SetNoDataValue(nodata)
    b.WriteArray(data)

    return ds
