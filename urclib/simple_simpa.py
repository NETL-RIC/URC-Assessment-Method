import os
import ctypes
import platform
from osgeo import gdal
import numpy as np
from .common_utils import write_raster
from .urc_common import RasterGroup
from .common_utils import ReeWorkspace
from . import urc_fl as fl


def _dtype_to_ctype(dtype):
    """Convert a numpy dType to a ctype.

    Args:
        dtype (str): string of numpy dtype to match.

    Returns:
        ctype: The matching ctype.

    Raises:
        KeyError: If inDType does not map to an existing ctype.
    """

    lookup = {'byte': ctypes.c_byte,
              'uint8': ctypes.c_ubyte,
              'uint16': ctypes.c_ushort,
              'int16': ctypes.c_short,
              'uint32': ctypes.c_uint,
              'int32': ctypes.c_int,
              'float32': ctypes.c_float,
              'float64': ctypes.c_double
              }
    return lookup[str(dtype)]


def _create_shim(rasters):
    """Create an empty dataset with the same attributes as the provided raster group. This dataset
    can be used to act as a "shim" for components that do not have any data yet are to be included in
    the SIMPA analysis.

    Args:
        rasters (RasterGroup): The group of Rasters to model the shim after.

    Returns:
        gdal.Dataset: The raster to use as a nodata "shim".
    """

    drvr = gdal.GetDriverByName("mem")
    ds = drvr.Create('missing_shim', rasters.raster_x_size, rasters.raster_y_size, 1, gdal.GDT_Float32)
    ds.SetGeoTransform(rasters.geotransform)

    nodata = -np.inf
    band = ds.GetRasterBand(1)
    buff = band.ReadAsArray()
    buff.fill(nodata)
    band.SetNoDataValue(nodata)
    band.WriteArray(buff)
    return ds


def simple_simpa(outpath, mult_rasters, mproc=False):
    """Runs SIMPA method using pre-generated fuzzylogic python logic.

    The content of urc_fl is generated from URC_FL.sijn project file
    using the fuzzylogic package's **generate** tool.

    Args:
        outpath (str): Path to the outputs directory
        mult_rasters (RasterGroup): The rasters to include.
        mproc (bool,optional): If `True` run SIMPA in parallel using Python's `multiprocessing` module. Defaults to
            `False`.

    Returns:
        ReeWorkspace: Path to SIMPA outputs.
    """

    # grab expected names
    fieldnames = fl.recordMissingKeys({})
    keys = mult_rasters.raster_names
    simpa_rasters = {}
    for f in fieldnames:
        for k in keys:
            if k.endswith(f):
                simpa_rasters[f] = (
                    mult_rasters[k].ReadAsArray().ravel(), mult_rasters[k].GetRasterBand(1).GetNoDataValue())
                break
    # grab missing rasters
    missing = fl.recordMissingKeys(simpa_rasters)
    shim_ds = _create_shim(mult_rasters)
    shim_ds.SetSpatialRef(mult_rasters.spatialref)
    shim_nodata = shim_ds.GetRasterBand(1).GetNoDataValue()
    shim_data = shim_ds.ReadAsArray().flatten()
    for m in missing:
        simpa_rasters[m] = (shim_data, shim_nodata)

    if not mproc:
        print("Parallel SIMPA disabled")
        # grab generated nodata sentinel
        nds = fl.gen_nodata_sentinel()
        # initialize master collections
        flsets, out_names = fl.initialize()
        outbands = {n: np.zeros(shim_data.shape[0]) for n in out_names}

        invals = {}
        for i in range(shim_data.shape[0]):
            print(f'{i}/{shim_data.shape[0]}')
            for f in fieldnames:
                val = simpa_rasters[f][0][i]
                nodata = simpa_rasters[f][1]
                if val == nodata:
                    val = nds
                invals[f] = val
            impls = fl.get_implications(flsets, invals)

            pxls = fl.apply_combiners(impls)
            for n in out_names:
                val = pxls[n]
                if isinstance(val, fl.NoDataSentinel):
                    val = shim_nodata
                outbands[n][i] = val
    else:
        outbands = launch_mproc(simpa_rasters, shim_data, fieldnames, shim_nodata)

    out_group = RasterGroup()
    ret = ReeWorkspace()
    for name, outData in outbands.items():
        path = os.path.join(outpath, name + '.tif')
        ret[name] = path
        ds = write_raster(shim_ds, outData.reshape([shim_ds.RasterYSize, shim_ds.RasterXSize]), path,
                          gdtype=gdal.GDT_Float32,
                          nodata=shim_nodata)

        out_group.add(name, ds)

    # calculate max values
    max_raster = out_group.calc_max_values(prefix='PE_', out_nodata=shim_nodata)
    path = os.path.join(outpath, 'PE_max.tif')
    write_raster(shim_ds, max_raster, path, gdtype=gdal.GDT_Float32, nodata=shim_nodata)
    return ret


# <editor-fold desc="Multiprocessing stuff">
def init_mproc(g_ins, g_outs):
    global g_inRasters
    global g_outRasters
    global g_fieldnames
    global g_inNoVals
    global g_sentinel
    global g_flsets
    global g_outKeys
    global g_nodataVal

    g_fieldnames = g_ins['keys']
    g_inRasters = g_ins['rasters']
    g_inNoVals = g_ins['ndvals']
    g_sentinel = g_ins['sentinel']
    g_flsets = g_ins['fl_sets']

    g_outRasters = g_outs['outputs']
    g_outKeys = g_outs['keys']
    g_nodataVal = g_outs['nodataval']


def process_mproc(index):
    global g_inRasters
    global g_outRasters
    global g_fieldnames
    global g_inNoVals
    global g_sentinel
    global g_flsets
    global g_outKeys
    global g_nodataVal

    # create local references to globals (optimization)
    in_rasters = g_inRasters
    in_novals = g_inNoVals
    nd_sentinel = g_sentinel
    flsets = g_flsets
    out_keys = g_outKeys
    nd_val = g_nodataVal
    out_rasters = g_outRasters

    invals = {}
    for i, f in enumerate(g_fieldnames):
        val = in_rasters[i][index]
        nodata = in_novals[i]
        if val == nodata:
            val = nd_sentinel
        invals[f] = val
    impls = fl.get_implications(flsets, invals)

    pxls = fl.apply_combiners(impls)
    for i, k in enumerate(out_keys):
        val = pxls[k]
        if isinstance(val, fl.NoDataSentinel):
            val = nd_val
        out_rasters[i][index] = val


# mproc entry point
def launch_mproc(in_rasters, out_proto, fieldnames, out_nodata_val):
    from concurrent.futures import ProcessPoolExecutor
    from multiprocessing import sharedctypes

    sorted_names = sorted(fieldnames)
    # grab generated nodata sentinel
    nds = fl.gen_nodata_sentinel()
    # initialize master collections
    flsets, out_names = fl.initialize()
    g_ins = {
        'keys': sorted_names,
        'rasters': [sharedctypes.RawArray(_dtype_to_ctype(in_rasters[r][0].dtype), in_rasters[r][0]) for r in
                    sorted_names],
        'ndvals': [in_rasters[r][1] for r in sorted_names],
        # 'count': len(in_rasters),
        'sentinel': nds,
        'fl_sets': flsets,
    }
    count = in_rasters[sorted_names[0]][0].shape[0]

    sorted_names = sorted(out_names)
    g_outs = {
        'outputs': [sharedctypes.RawArray(_dtype_to_ctype(out_proto.dtype), out_proto.shape[0]) for _ in
                    range(len(sorted_names))],
        'keys': sorted_names,
        'nodataval': out_nodata_val,
    }

    # workaround for python bug on Windows
    max_workers = None
    if platform.system() == "Windows":
        max_workers = 60
    i = 0
    with ProcessPoolExecutor(max_workers=max_workers, initializer=init_mproc, initargs=(g_ins, g_outs)) as executor:
        for _ in executor.map(process_mproc, list(range(count))):
            i += 1
            print(f'{i}/{count} Processed')

    # copy back
    out_rasters = {}
    for i, n in enumerate(sorted_names):
        out_rasters[n] = np.asarray(g_outs['outputs'][i])

    return out_rasters
# </editor-fold>
