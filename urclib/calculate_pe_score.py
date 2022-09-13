""" Create lists for unique components and each corresponding dataset """

import os
from .urc_common import RasterGroup,Rasterize
from osgeo import gdal
from .da_calc import RunPEScoreDA
from .ds_calc import RunPEScoreDS
from .urc_common import REE_Workspace

def CollectIndexRasters(inWorkspace):
    """Pull in all indices rasters from the workspace, specifically:
        * ld_inds
        * lg_inds
        * sd_inds
        * ud_inds
        * sa_inds (optional)

    Args:
        inWorkspace (REE_Workspace):

    Returns:
        RasterGroup: The loaded indices rasters.
    """

    inpaths = {k: inWorkspace[f'{k}_inds'] for k in ('ld','lg','sd','ud')}

    # special case: check if sa exists; if not remove from workspace
    if inWorkspace.exists('sa_inds'):
        inpaths['sa'] = inWorkspace['sa_inds']
    else:
        print('NOTE SA Index file not found; skipping.')

    return RasterGroup(**inpaths)


def RunPEScore(gdbPath,inWorkspace,outWorkspace,doDA=True,doDS=True,rasters_only=False,postProg=None):
    """ Run the URC method for calculating the PE score for DA and/or DS.

    Args:
        gdbPath (str): Path to the .gdb (or .sqlite) file to evaluate.
        inWorkspace (REE_Workspace): Holds all the input filepaths.
        outWorkspace (REE_Workspace): Holds all the output filepaths.
        doDA (bool): If `True`, include DA analysis.
        doDS (bool): If `True`, include DS analysis.
        rasters_only (bool): If true, exit after all intermediate rasters have been created,
            skipping the actual analysis.
        postProg (function, optional): Optional progress update function. Will be pass a value from 0 to 100 for
           progress of current analysis (da or ds).

    Raises:
        ValueError: If both doDA and doDS are `False`.
    """

    if not (doDA or doDS):
        raise ValueError("Either doDA or doDS must be true.")

    gdbDS = gdal.OpenEx(gdbPath, gdal.OF_VECTOR)

    indexRasters = CollectIndexRasters(inWorkspace)
    indexMask = indexRasters.generateNoDataMask()

    retWorkspace = REE_Workspace()
    if doDA:
        retWorkspace.update(RunPEScoreDA(gdbDS,indexRasters,indexMask,outWorkspace,rasters_only,postProg))
    if doDS:
        retWorkspace.update(RunPEScoreDS(gdbDS,indexRasters,indexMask,outWorkspace,rasters_only,postProg))
    return retWorkspace

