"""Module for DS specific calculations."""
from .urc_common import *
from .simple_simpa import simpleSIMPA
from time import process_time
from osgeo import gdal


def GetDSDistances(src_rasters,cache_dir=None,mask=None):
    """Create interpolated rasters for DS Datasets.

    Args:
        src_rasters (RasterGroup): The rasters to sample distances from.
        cache_dir (str,optional): location to write out new rasters, if provided.
          Otherwise, rasters are kept in memory.
        mask (numpy.ndarray,optional): No data mask to apply.

    Returns:
        RasterGroup: The newly generated distance Rasters.
    """
    src_data={'gdType':gdal.GDT_Float32,
              'drvrName':'mem',
              'prefix':'',
              'suffix':'',
              'mask':mask,
              }

    if cache_dir is not None:
        src_data['drvrName'] = 'GTiff'
        src_data['prefix'] = cache_dir
        src_data['suffix'] = '.tif'

    outRasters=RasterGroup()
    dsKeys = [k for k in src_rasters.rasterNames if k.startswith('DS')]
    for k in dsKeys:
        print(f'Finding distance for  {k}...')
        id = f'{k}_distance'
        rstr = RasterDistance(id, src_rasters[k],**src_data)
        outRasters[k] = rstr

    return outRasters


def RunPEScoreDS(gdbDS, indexRasters,indexMask,outWorkspace, rasters_only=False,clipping_mask=None,postProg=None):
    """Calculate the PE score for DS values using the URC method.

    Args:
        gdbDS (gdal.Dataset): The Database/dataset containing the vector layers representing the components to include.
        indexRasters (RasterGroup): The raster representing the indexes generated for the grid.
        indexMask (numpy.ndarray): Raw values representing the cells to include or exclude from the analysis.
        outWorkspace (common_utils.REE_Workspace): The container for all output filepaths.
        rasters_only (bool): If true, skip analysis after all intermediate rasters are written.
           Only has an effect if `outWorkspace` has 'raster_dir' defined.
        postProg (function,optional): Optional function to deploy for updating incremental progress feedback.
            function should expect a single integer as its argument, in the range of [0,100].
    """

    print("Begin DS PE Scoring...")
    rasterDir = outWorkspace.get('raster_dir', None)
    t_allStart = process_time()
    print('Finding components...')
    components_data_dict = FindUniqueComponents(gdbDS,'DS')
    testRasters = RasterizeComponents(indexRasters,gdbDS,components_data_dict,rasterDir)

    print('Done')
    print('Calculating distances')
    domDistRasters,hitMaps = GenDomainIndexRasters(indexRasters, True,rasterDir, indexMask)
    distanceRasters = GetDSDistances(testRasters,rasterDir,indexMask)
    combineRasters = FindDomainComponentRasters(domDistRasters,hitMaps,testRasters,rasterDir)

    multRasters=NormMultRasters(combineRasters, distanceRasters, rasterDir)

    # Add non-multipled normalized LG rasters
    multRasters.update(NormLGRasters(distanceRasters,rasterDir))
    print('Done')

    if clipping_mask is not None:
        multRasters.clipWithRaster(clipping_mask,True)
        if rasterDir is not None:
            multRasters.copyRasters('GTiff',rasterDir,'_clipped.tif')

    emptyNames = []
    for rg in (domDistRasters,distanceRasters,combineRasters,multRasters):
        emptyNames+=rg.emptyRasterNames
    if len(emptyNames) > 0:
        print("The Following DS rasters are empty:")
        for en in emptyNames:
            print(f'   {en}')
    else:
        print("No empty DS rasters detected.")

    if 'raster_dir' in outWorkspace and rasters_only:
        print('Exit on rasters specified; exiting')
        return

    # Fuzzy Rules
    # P:\02_DataWorking\REE\URC_Fuzzy_Logic\UCR_FL.sijn

    print('**** Begin SIMPA processing ****')
    simpleSIMPA(outWorkspace.workspace,multRasters)


    print("**** End SIMPA processing ****")
    t_allEnd = process_time()
    print(f"DS scoring complete.")
    printTimeStamp(t_allEnd-t_allStart)