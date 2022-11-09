""" Create lists for unique components and each corresponding dataset """

import os
from .urc_common import RasterGroup, rasterize
from osgeo import gdal
from .da_calc import run_pe_score_da
from .ds_calc import run_pe_score_ds
from .urc_common import UrcWorkspace


def collect_index_rasters(inworkspace):
    """Pull in all indices rasters from the workspace, specifically:
        * ld_inds
        * lg_inds
        * sd_inds
        * ud_inds
        * sa_inds (optional)

    Args:
        inworkspace (UrcWorkspace):

    Returns:
        RasterGroup: The loaded indices rasters.
    """

    inpaths = {k: inworkspace[f'{k}_inds'] for k in ('ld', 'lg', 'sd', 'ud')}

    # special case: check if sa exists; if not remove from workspace
    if inworkspace.exists('sa_inds'):
        inpaths['sa'] = inworkspace['sa_inds']
    else:
        print('NOTE SA Index file not found; skipping.')

    return RasterGroup(**inpaths)


def run_pe_score(gdb_path, in_workspace, out_workspace, do_da=True, do_ds=True, rasters_only=False, post_prog=None):
    """ Run the URC method for calculating the PE score for DA and/or DS.

    Args:
        gdb_path (str): Path to the .gdb (or .sqlite) file to evaluate.
        in_workspace (UrcWorkspace): Holds all the input filepaths.
        out_workspace (UrcWorkspace): Holds all the output filepaths.
        do_da (bool): If `True`, include DA analysis.
        do_ds (bool): If `True`, include DS analysis.
        rasters_only (bool): If true, exit after all intermediate rasters have been created,
            skipping the actual analysis.
        post_prog (function, optional): Optional progress update function. Will be pass a value from 0 to 100 for
           progress of current analysis (da or ds).

    Raises:
        ValueError: If both do_da and doDS are `False`.
    """

    if not (do_da or do_ds):
        raise ValueError("Either do_da or do_ds must be true.")

    gdb_ds = gdal.OpenEx(gdb_path, gdal.OF_VECTOR)

    index_rasters = collect_index_rasters(in_workspace)
    index_mask = index_rasters.generate_nodata_mask()

    clip_mask = None
    if 'clip_layer' in in_workspace:
        clip_mask = gdal.OpenEx(in_workspace['clip_layer'], gdal.OF_VECTOR)
        clip_mask = rasterize('clip_raster', [clip_mask.GetLayer(0)], clip_mask, index_rasters.raster_x_size,
                              index_rasters.raster_y_size, index_rasters.geotransform, index_rasters.spatialref,
                              nodata=0)

    ret_workspace = UrcWorkspace()
    if do_da:
        da_results = run_pe_score_da(gdb_ds, index_rasters, index_mask, out_workspace, rasters_only, clip_mask,
                                     post_prog)
        ret_workspace.update(da_results)
    if do_ds:
        ds_results = run_pe_score_ds(gdb_ds, index_rasters, index_mask, out_workspace, rasters_only, clip_mask,
                                     post_prog)
        ret_workspace.update(ds_results)

    # if all((do_da, do_ds)):
        # TODO: add dx here.
        # Dx_m = Ds_m/Da_m - (1. - ( Ds_m/Da_m))
        # grab unstructured DS (presently DS_*_Add) from ds_results
        # ...
    # else:
    #     print(
    #         f'Skipping Dx calculations; only {"DA" if do_da else "DS"} calculated; Dx requires both DA and DS.')

    return ret_workspace
