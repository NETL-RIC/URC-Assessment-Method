"""Module for DS specific calculations."""
from .urc_common import *
from .simple_simpa import simple_simpa
from osgeo import gdal


def get_ds_distances(src_rasters, cache_dir=None, mask=None):
    """Create interpolated rasters for DS Datasets.

    Args:
        src_rasters (RasterGroup): The rasters to sample distances from.
        cache_dir (str,optional): location to write out new rasters, if provided.
          Otherwise, rasters are kept in memory.
        mask (numpy.ndarray,optional): No data mask to apply.

    Returns:
        RasterGroup: The newly generated distance Rasters.
    """
    src_data = {'gdtype': gdal.GDT_Float32,
                'drvr_name': 'mem',
                'prefix': '',
                'suffix': '',
                'mask': mask,
                }

    if cache_dir is not None:
        src_data['drvr_name'] = 'GTiff'
        src_data['prefix'] = cache_dir
        src_data['suffix'] = '.tif'

    out_rasters = RasterGroup()
    ds_keys = [k for k in src_rasters.raster_names if k.startswith('DS')]
    for k in ds_keys:
        print(f'Finding distance for  {k}...')
        id = f'{k}_distance'
        rstr = raster_distance(id, src_rasters[k], **src_data)
        out_rasters[k] = rstr

    return out_rasters


def run_pe_score_ds(gdb_ds, index_rasters, index_mask, out_workspace, rasters_only=False, clipping_mask=None,
                    post_prog=None):
    """Calculate the PE score for DS values using the URC method.

    Args:
        gdb_ds (gdal.Dataset): The Database/dataset containing the vector layers representing the components to include.
        index_rasters (RasterGroup): The raster representing the indexes generated for the grid.
        index_mask (numpy.ndarray): Raw values representing the cells to include or exclude from the analysis.
        out_workspace (common_utils.UrcWorkspace): The container for all output filepaths.
        rasters_only (bool): If true, skip analysis after all intermediate rasters are written.
           Only has an effect if `out_workspace` has 'raster_dir' defined.
        clipping_mask (gdal.Dataset,optional): Clipping mask to apply, if any.
        post_prog (function,optional): Optional function to deploy for updating incremental progress feedback.
            function should expect a single integer as its argument, in the range of [0,100].
    """

    print("Begin DS PE Scoring...")
    raster_dir = out_workspace.get('raster_dir', None)

    with do_time_capture():
        print('Finding components...')
        components_data_dict = find_unique_components(gdb_ds, 'DS')
        test_rasters = rasterize_components(index_rasters, gdb_ds, components_data_dict, raster_dir)

        print('Done')
        print('Calculating distances')
        dom_dist_rasters, hitmaps = gen_domain_index_rasters(index_rasters, True, raster_dir, index_mask)
        distance_rasters = get_ds_distances(test_rasters, raster_dir, index_mask)
        combine_rasters = find_domain_component_rasters(dom_dist_rasters, hitmaps, test_rasters, raster_dir)

        mult_rasters = norm_multrasters(combine_rasters, distance_rasters, raster_dir)

        # Add non-multipled normalized LG rasters
        mult_rasters.update(norm_lg_rasters(distance_rasters, raster_dir))
        print('Done')

        if clipping_mask is not None:
            # True to enable multiprocessing
            mult_rasters.clip_with_raster(clipping_mask, True)
            if raster_dir is not None:
                mult_rasters.copy_rasters('GTiff', raster_dir, '_clipped.tif')

        empty_names = []
        for rg in (dom_dist_rasters, distance_rasters, combine_rasters, mult_rasters):
            empty_names += rg.empty_raster_names
        if len(empty_names) > 0:
            print("The Following DS rasters are empty:")
            for en in empty_names:
                print(f'   {en}')
        else:
            print("No empty DS rasters detected.")

        if 'raster_dir' in out_workspace and rasters_only:
            print('Exit on rasters specified; exiting')
            return

        print('**** Begin SIMPA processing ****')
        disabled_multi = int(os.environ.get('REE_DISABLE_MULTI', 0)) != 0
        out_files = simple_simpa(out_workspace.workspace, mult_rasters, not disabled_multi)

        print("**** End SIMPA processing ****")
        print(f"DS scoring complete.")
        return UrcWorkspace(**out_files)
