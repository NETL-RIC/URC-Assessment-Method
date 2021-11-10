""" Create lists for unique components and each corresponding dataset """

from .urc_common import RasterGroup
from osgeo import gdal
from .da_calc import RunPEScoreDA
from .ds_calc import RunPEScoreDS

def CollectIndexRasters(inWorkspace):

    inpaths = {k: inWorkspace[f'{k}_inds'] for k in ('ld','lg','sd','ud')}
    return RasterGroup(**inpaths)


def RunPEScore(gdbPath,inWorkspace,outWorkspace,doDA,doDS,rasters_only,postProg=None):
    assert doDA or doDS

    gdbDS = gdal.OpenEx(gdbPath, gdal.OF_VECTOR)

    indexRasters = CollectIndexRasters(inWorkspace)
    indexMask = indexRasters.generateNoDataMask()

    if doDA:
        RunPEScoreDA(gdbDS,indexRasters,indexMask,outWorkspace,rasters_only,postProg)
    if doDS:
        RunPEScoreDS(gdbDS,indexRasters,indexMask,outWorkspace,rasters_only,postProg)

