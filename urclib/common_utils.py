# This file is part of URC Assessment Method.
#
# URC Assessment Method is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# URC Assessment Method is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with URC Assessment Method. If not, see
# <https://www.gnu.org/licenses/>.

"""Collection of functions that are used in both grid creation and score analyses."""

from osgeo import gdal, ogr, osr
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
_ogrTypeLabels = {getattr(ogr, n): n for n in dir(ogr) if n.find('wkb') == 0}
_ogrPointTypes = [k for k, v in _ogrTypeLabels.items() if v.find('Point') != -1]
_ogrLineTypes = [k for k, v in _ogrTypeLabels.items() if v.find('Line') != -1]
_ogrPolyTypes = [k for k, v in _ogrTypeLabels.items() if v.find('Polygon') != -1]
_ogrMultiTypes = [k for k, v in _ogrTypeLabels.items() if v.find('Multi') != -1]

_ogrErrLabels = {getattr(ogr, n): n for n in dir(ogr) if n.find('OGRERR_') == 0}

GEOTIFF_OPTIONS = ['GEOTIFF_KEYS_FLAVOR=STANDARD', 'TFW=YES']
# GEOTIFF_OPTIONS = ['TFW=YES']

#
# class DataPrefix(object):
#     """ Manage Data-related prefix labelling for generalized field labels.
#
#     Args:
#         prefix (str): The prefix to assign to any requested field name
#
#     """
#
#     def __init__(self, prefix):
#         self.prefix = prefix
#
#     def __getitem__(self, lbl):
#         """ Retrieve dlg_label with prefix applied.
#
#         Args:
#             lbl (str): The dlg_label to prefix.
#
#         Returns:
#             str: The prefixed dlg_label.
#         """
#         return '_'.join([self.prefix, lbl])
#
#     def __repr__(self):
#         return f'Prefix: "{self.prefix}"'


class UrcWorkspace(object):
    """Manages filepaths associated with a collection of data.

    Attributes:
        workspace (str,optional): Path to the root directory of the workspace collection; defaults to current working
          directory.

    Args:
        workspace_dir (str): The root directory for the workspace.
        **kwargs: Additional key-path pairs to assign.

    """

    def __init__(self, workspace_dir=None, **kwargs):
        if workspace_dir is None:
            workspace_dir = '.'
        self.workspace = workspace_dir
        self._entries = {}
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
            return os.path.abspath(os.path.join(self.workspace, basename)).replace('\\', '/')
        return basename

    def __setitem__(self, key, value):
        """Assign a path to a key.

        Args:
            key (str): The key to identify the path with.
            value (str): The path to assign.

        Raises:
            ValueError: `value` is not of type `str`.
        """

        if not isinstance(value, str):
            raise ValueError("value must be of type 'str'")
        self._entries[key] = value

    def __contains__(self, item):
        return item in self._entries

    def __iter__(self):
        for k in self._entries.keys():
            yield self[k]

    def __len__(self):
        return len(self._entries)

    def __delitem__(self, key):
        del self._entries[key]

    def update(self, invals):
        """Update contents of workspaces with that of a dict.

        Args:
            invals (dict): The content to update the workspace with.
        """

        self._entries.update(invals)

    def __repr__(self):
        return f'Root:"{self.workspace}" Tags: {self._entries}'

    def keys(self):
        """Retrieve the keys for filepaths.

        Returns:
            dict_keys: The names used to identify individual file paths.
        """

        return self._entries.keys()

    def items(self):
        """Provide Iterator for walking through labels, and associated paths.

        Yields:
            Tuple: label, and full path, respectively
        """
        for k in self._entries.keys():
            yield k,self[k]

    def get(self, key, default=None):
        """Retrieve value of key if it exists; otherwise return the default value.

        Args:
            key (str): The tag of the path to retrieve.
            default (object,optional): The default value to pass if a value for `key` does not exist.

        Returns:
            object: The value for `key`, or the value of `default` if no value for `key` exists.

        Raises:
            KeyError: if `key` is not present in the in_workspace and `default` is `None`.
        """
        if key in self:
            return self[key]
        return default

    def delete_files(self, *args):
        """Delete the specified files.

        Args:
            *args: List of keys of files to delete.

        """

        to_delete = args if len(args) > 0 else self._entries.keys()
        for k in to_delete:
            if k in self:
                delete_file(self[k])

    def test_files_exist(self):
        """Test each path entry to determine if path exists.

        Returns:
            list: (dlg_label,exists) for each entry in REE_workspace, where "exists" is `True` or `False` depending on
              whether a file is found at location pointed to by associated path.
        """

        # use self.__getitem__ to ensure path is expanded
        entries = ((k, self[k]) for k in self._entries.keys())
        return [(k, os.path.exists(v)) for (k, v) in entries]

    def exists(self, key):
        """Test to see if a given file exists in the filesystem.

        Args:
            key (str): The dlg_label for the path to query.

        Returns:
            bool: `True` if the key and associated file both exist; `False` otherwise.
        """

        return key in self and os.path.exists(self[key])


@contextmanager
def do_time_capture():
    """Context which prints the time it took to get from beginning to end of the with block, in seconds.
    """
    start = time()
    try:
        yield
    finally:
        end = time()
        print_timestamp(end - start)


def print_timestamp(raw_seconds):
    """
    Print raw seconds in nicely hour, minute, seconds format.

    Args:
        raw_seconds (float): The raw seconds to print.
    """

    tot_min, seconds = divmod(raw_seconds, 60)
    hours, minutes = divmod(tot_min, 60)
    print(f"Runtime: {hours} hours, {minutes} minutes, {round(seconds, 2)} seconds.")


def parse_workspace_args(vals, workspace, outputs):
    """Parse out script arguments into a workspace.

    Args:
        vals (dict): The arguments to parse.
        workspace (UrcWorkspace): The destination of any values prefixed with `IN_`.
        outputs (UrcWorkspace): The destination of any values prefixed with `OUT_`.
    """

    for k, v in vals.items():
        if isinstance(v, str):
            if k.startswith('IN_'):
                workspace[k[3:]] = v
            elif k.startswith('OUT_'):
                outputs[k[4:]] = v


def list_fieldnames(featureclass):
    """
    Lists the fields in a feature class, shapefile, or table in a specified dataset.

    Args:
        featureclass (osgeo.ogr.Layer): Layer to query for field names.

    Returns:
        list: The names of each field (as strs).
    """

    fdefn = featureclass.GetLayerDefn()
    field_names = [fdefn.GetFieldDefn(i).GetName() for i in range(fdefn.GetFieldCount())]

    return field_names


def delete_file(path):
    """Remove a file if present.

    Args:
        path (str): The file to delete, if present.

    Returns:
        bool: `True` if file existed and deleted; `False` if file was not present
    """

    exists=os.path.exists(path)
    if exists:
        os.remove(path)
    return exists

def raster_domain_intersect(in_coords, in_mask, src_sref, join_lyr, fld_name, nodata=-9999):
    """Create intersect raster for specific field values in vector layer

    Args:
        in_coords (np.ndarray): Map from pixel to space coordinates.
        in_mask (np.ndarray): Raw data from mask layer, with 1 is include, 0 is exclude.
        src_sref (osr.SpatialReference): The spatial reference to project into.
        join_lyr (ogr.Layer): The vector layer to parse.
        fld_name (str): The name of the field to use for indexing.
        nodata (int,optional): The value to use to represent "no data" pixels. defaults to **-9999**.

    Returns:
        np.ndarray: index values corresponding to pixel coordinates as defined with `inCoords`.
    """
    buff = np.full([in_coords.shape[0] * in_coords.shape[1]], nodata, dtype=np.int32)

    transform = osr.CoordinateTransformation(src_sref, join_lyr.GetSpatialRef())

    for i, (x, y) in enumerate(in_coords.reshape(in_coords.shape[0] * in_coords.shape[1], in_coords.shape[2])):
        if in_mask[i] == 0:
            continue
        pt = ogr.Geometry(ogr.wkbPoint)
        x,y,_ = transform.TransformPoint(x,y)
        pt.AddPoint(x, y)

        for jFeat in join_lyr:
            g = jFeat.GetGeometryRef()
            if pt.Within(g):
                fld = jFeat.GetFieldAsString(fld_name)
                buff[i] = int(fld[2:])
                break
        join_lyr.ResetReading()

    return buff.reshape(in_coords.shape[0], in_coords.shape[1])


def rasterize(id, fc_list, in_ds, xsize, ysize, geotrans, srs, drvr_name="mem", prefix='', suffix='', nodata=-9999,
              gdtype=gdal.GDT_Int32, opts=None):
    """Convert specified Vector layers to raster.

    Args:
        id (str): The id for the new Raster dataset.
        fc_list (list): A list of list of layers to rasterize.
        in_ds (gdal.Dataset): The input dataset.
        xsize (int): The width of the new raster, in pixels.
        ysize (int): The height of the new raster, in pixels.
        geotrans (tuple): Matrix of float values describing geographic transformation.
        srs (osr.SpatialReference): The Spatial Reference System to provide for the new Raster.
        drvr_name (str,optional): Name of driver to use to create new raster; defaults to "MEM".
        prefix (str,optional): Prefix to apply to `comp_name` for gdal.Dataset dlg_label; this could be a path to a directory
           if raster is being saved to disk.
        suffix (str,optional): Suffix to apply to `comp_name` for gdal.Dataset dlg_label; this could be the file extension
           if raster is being saved to disk.
        nodata (numeric,optional): The value to represent no-data in the new Raster; default is -9999
        gdtype (int,optional): Flag indicating the data type for the raster; default is "gdal.GDT_Int32".
        opts (list,optional): String flags to forward to GDAL drivers, if any.

    Returns:
        gdal.Dataset: The rasterized vector layer.
    """

    path = os.path.join(prefix, id) + suffix
    drvr = gdal.GetDriverByName(drvr_name)
    if opts is None:
        opts = []
    ds = drvr.Create(path, xsize, ysize, 1, gdtype, options=opts)

    ds.SetGeoTransform(geotrans)
    ds.SetSpatialRef(srs)
    b = ds.GetRasterBand(1)
    b.SetNoDataValue(nodata)
    fill = np.full([ysize, xsize], nodata, dtype=gdt_np_map[gdtype])
    b.WriteArray(fill)

    ropts = gdal.RasterizeOptions(
        layers=[fc.GetName() for fc in fc_list]
    )
    gdal.Rasterize(ds, in_ds, options=ropts)
    # force writing of data here so data is available in the case of writing to disk. Good for recovering from crash
    # down the line
    ds.FlushCache()

    return ds


def index_features(in_lyr, cell_width, cell_height, drivername='MEM', create_options=None):
    """Build a fishnet grid that is culled to existing geometry.

    Args:
        in_lyr (osgeo.ogr.Layer): The Layer containing the geometry to act as a rough mask.
        cell_width (float): The width of each cell.
        cell_height (float): The height of each cell.
        drivername (str,optional): The driver to use for generating the mask raster. Defaults to **MEM**.
        create_options (list,optional): String flags to forward to GDAL drivers, if any.

    Returns:
        tuple: numpy array for coordinate mapping, and gdal.Dataset with masking info.
    """

    # https://stackoverflow.com/questions/59189072/creating-fishet-grid-using-python
    x_min, x_max, y_min, y_max = in_lyr.GetExtent()

    # create reference geometry
    ref_geom = ogr.Geometry(ogr.wkbMultiPolygon)
    for feat in in_lyr:
        ref_geom.AddGeometry(feat.GetGeometryRef())

    ref_geom = ref_geom.UnionCascaded()

    dx = cell_width / 2
    dy = cell_height / 2

    # offset for nearest even boundaries(shift by remainder in difference of extent and cell size intervals)
    # I don't see any offest with arc results along the x, so let's do that.
    xoffs = 0  # (x_max - x_min) % cell_width
    yoffs = (y_max - y_min) % cell_height
    xvals, yvals = np.meshgrid(
        np.arange(x_min + dx + xoffs, x_max + dx + xoffs, cell_width),
        np.arange(y_max + dy - yoffs, y_min + dy - yoffs, -cell_height),
    )

    coord_map = np.array(list(zip(xvals.ravel(), yvals.ravel()))).reshape(*xvals.shape, 2)
    coord_map = np.flip(coord_map, axis=0)
    raw_mask = np.zeros(xvals.shape)

    for x in range(xvals.shape[0]):
        for y in range(xvals.shape[1]):
            pt = ogr.Geometry(ogr.wkbPoint)
            pt.AddPoint(*coord_map[x, y])
            if pt.Intersects(ref_geom):
                raw_mask[x, y] = 1

    drvr = gdal.GetDriverByName(drivername)
    opts = []
    if create_options is not None:
        opts = create_options
    ds = drvr.Create('mask', coord_map.shape[1], coord_map.shape[0], options=opts)
    b = ds.GetRasterBand(1)
    b.WriteArray(raw_mask)
    ds.SetProjection(in_lyr.GetSpatialRef().ExportToWkt())
    ds.SetGeoTransform((coord_map[0, 0, 0], cell_width, 0, coord_map[0, 0, 1], 0, cell_height))

    return coord_map, ds


def write_raster(mask_lyr, data, name, drivername='GTiff', gdtype=gdal.GDT_Byte, nodata=-9999):
    """Write a raster data to a new gdal.Dataset object

    Args:
        mask_lyr (gdal.Dataset): Raster object containing mask, dimension, and geotransform information.
        data (np.ndarray): The data to write to the Dataset
        name (str): The unique identifier and (depending on the driver) the path to the file to write.
        drivername (str,optional): The driver to use to create the dataset. Defaults to **GTiff**.
        gdtype (int,optinal): The internal data type to use in the generated raster. Defaults to `gdal.GDT_Byte`.
        nodata (int,optional): The value to use to represent "no data" pixels. defaults to **-9999**.

    Returns:
        gdal.Dataset: Reference to newly created dataset; can be safely ignored if just writing to disk.
    """

    opts = []
    if drivername.lower() == 'gtiff':
        opts = GEOTIFF_OPTIONS
    drvr = gdal.GetDriverByName(drivername)
    ds = drvr.Create(name, mask_lyr.RasterXSize, mask_lyr.RasterYSize, 1, gdtype, options=opts)
    ds.SetProjection(mask_lyr.GetProjection())
    ds.SetGeoTransform(mask_lyr.GetGeoTransform())
    b = ds.GetRasterBand(1)
    b.SetNoDataValue(nodata)
    b.WriteArray(data)

    return ds
