import os
import ctypes
import platform
from osgeo import gdal
import numpy as np
from .common_utils import writeRaster
from .urc_common import RasterGroup
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

def _createShim(rasters):
    """Create an empty dataset with the same attributes as the provided raster group. This dataset
    can be used to act as a "shim" for components that do not have any data yet are to be included in
    the SIMPA analysis.

    Args:
        rasters (RasterGroup): The group of Rasters to model the shim after.

    Returns:
        gdal.Dataset: The raster to use as a nodata "shim".
    """

    drvr = gdal.GetDriverByName("mem")
    ds = drvr.Create('missing_shim',rasters.RasterXSize,rasters.RasterYSize,1,gdal.GDT_Float32)
    ds.SetGeoTransform(rasters.geoTransform)

    noData = -np.inf
    band = ds.GetRasterBand(1)
    buff = band.ReadAsArray()
    buff.fill(noData)
    band.SetNoDataValue(noData)
    band.WriteArray(buff)
    return ds

def simpleSIMPA(outpath,multRasters,mproc=False):
    """Runs SIMPA method using pre-generated fuzzylogic python logic.

    The content of urc_fl is generated from URC_FL.sijn project file
    using the fuzzylogic package's **generate** tool.

    Args:
        outpath:
        multRasters:

    Returns:

    """

    # grab expected names
    fieldnames = fl.recordMissingKeys({})
    keys = multRasters.rasterNames
    simpaRasters = {}
    for f in fieldnames:
        for k in keys:
            if k.endswith(f):
                simpaRasters[f] = (
                multRasters[k].ReadAsArray().ravel(), multRasters[k].GetRasterBand(1).GetNoDataValue())
                break
    # grab missing rasters
    missing = fl.recordMissingKeys(simpaRasters)
    shimDs = _createShim(multRasters)
    shimDs.SetSpatialRef(multRasters.spatialRef)
    shimNoData = shimDs.GetRasterBand(1).GetNoDataValue()
    shimData = shimDs.ReadAsArray().flatten()
    for m in missing:
        simpaRasters[m] = (shimData, shimNoData)

    if not mproc:
        print("Parallel SIMPA disabled")
        # grab generated nodata sentinel
        nds = fl.gen_nodata_sentinel()
        # initialize master collections
        flsets,outNames = fl.initialize()
        outbands = {n: np.zeros(shimData.shape[0]) for n in outNames}

        invals = {}
        for i in range(shimData.shape[0]):
            print(f'{i}/{shimData.shape[0]}')
            for f in fieldnames:
                val = simpaRasters[f][0][i]
                noData = simpaRasters[f][1]
                if val == noData:
                    val = nds
                invals[f] = val
            impls = fl.get_implications(flsets, invals)

            pxls = fl.apply_combiners(impls)
            for n in outNames:
                val = pxls[n]
                if isinstance(val, fl.NoDataSentinel):
                    val = shimNoData
                outbands[n][i] = val
    else:
        outbands=launch_mproc(simpaRasters,shimData,fieldnames,shimNoData)

    outGroup=RasterGroup()
    for name, outData in outbands.items():
        path = os.path.join(outpath, name + '.tif')
        ds=writeRaster(shimDs, outData.reshape([shimDs.RasterYSize, shimDs.RasterXSize]), path, gdtype=gdal.GDT_Float32,
                    nodata=shimNoData)

        outGroup.add(name,ds)

    # calculate max values
    maxRaster=outGroup.calcMaxValues(prefix='PE_',outNoData=shimNoData)
    path = os.path.join(outpath,'PE_max.tif')
    writeRaster(shimDs,maxRaster,path,gdtype=gdal.GDT_Float32,nodata=shimNoData)


# <editor-fold desc="Multiprocessing stuff">
def init_mproc(g_ins,g_outs):
    global g_inRasters
    global g_outRasters
    global g_fieldnames
    global g_inNoVals
    global g_sentinel
    global g_flsets
    global g_outKeys
    global g_nodataVal

    g_fieldnames=g_ins['keys']
    g_inRasters=g_ins['rasters']
    g_inNoVals=g_ins['ndvals']
    g_sentinel=g_ins['sentinel']
    g_flsets = g_ins['fl_sets']

    g_outRasters=g_outs['outputs']
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
    inRasters = g_inRasters
    inNoVals = g_inNoVals
    ndSentinel = g_sentinel
    flsets= g_flsets
    outKeys = g_outKeys
    ndVal = g_nodataVal
    outRasters = g_outRasters

    invals={}
    for i,f in enumerate(g_fieldnames):
        val = inRasters[i][index]
        noData = inNoVals[i]
        if val == noData:
            val = ndSentinel
        invals[f] = val
    impls = fl.get_implications(flsets, invals)

    pxls = fl.apply_combiners(impls)
    for i,k in enumerate(outKeys):
        val = pxls[k]
        if isinstance(val, fl.NoDataSentinel):
            val = ndVal
        outRasters[i][index] = val


# mproc entry point
def launch_mproc(inRasters,outProto,fieldnames,outnoDataVal):

    from concurrent.futures import ProcessPoolExecutor
    from multiprocessing import sharedctypes

    sortedNames=sorted(fieldnames)
    # grab generated nodata sentinel
    nds = fl.gen_nodata_sentinel()
    # initialize master collections
    flsets, outNames = fl.initialize()
    g_ins = {
        'keys':sortedNames,
        'rasters':[sharedctypes.RawArray(_dtype_to_ctype(inRasters[r][0].dtype),inRasters[r][0]) for r in sortedNames],
        'ndvals':[inRasters[r][1] for r in sortedNames],
        # 'count': len(inRasters),
        'sentinel': nds,
        'fl_sets':flsets,
    }
    count =inRasters[sortedNames[0]][0].shape[0]

    sortedNames = sorted(outNames)
    g_outs = {
        'outputs': [sharedctypes.RawArray(_dtype_to_ctype(outProto.dtype),outProto.shape[0]) for _ in range(len(sortedNames))],
        'keys':sortedNames,
        'nodataval':outnoDataVal,
    }

    # workaround for python bug on Windows
    max_workers=None
    if platform.system()=="Windows":
        max_workers=60
    i=0
    with ProcessPoolExecutor(max_workers=max_workers,initializer=init_mproc,initargs=(g_ins,g_outs)) as executor:
        for _ in executor.map(process_mproc,list(range(count))):
            i+=1
            print(f'{i}/{count}')

    # copy back
    outRasters={}
    for i,n in enumerate(sortedNames):
        outRasters[n]=np.asarray(g_outs['outputs'][i])



    return outRasters
# </editor-fold>
