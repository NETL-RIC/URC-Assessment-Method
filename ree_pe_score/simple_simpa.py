import os
from osgeo import gdal
import numpy as np
from .common_utils import writeRaster

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

def simpleSIMPA(outpath,multRasters):
    """"""

    from . import urc_fl as fl
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
    shimNoData = shimDs.GetRasterBand(1).GetNoDataValue()
    shimData = shimDs.ReadAsArray().flatten()
    for m in missing:
        simpaRasters[m] = (shimData, shimNoData)

    nds = fl.gen_nodata_sentinel()
    flsets, combos = fl.initialize()
    outbands = {k: np.zeros(shimData.shape[0]) for k in combos.keys()}
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

        pxls = fl.apply_combiners(impls, combos)
        for k in combos.keys():
            val = pxls[k]
            if isinstance(val, fl.NoDataSentinel):
                val = shimNoData
            outbands[k][i] = val

    for name, outData in outbands.items():
        path = os.path.join(outpath, name + '.tif')
        writeRaster(shimDs, outData.reshape([shimDs.RasterYSize, shimDs.RasterXSize]), path, gdtype=gdal.GDT_Float32,
                    nodata=shimNoData)