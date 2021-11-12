"""Module for DS specific calculations."""

from .urc_common import *
from time import process_time
from osgeo import gdal
import os

def createShim(rasters):
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

def injectURCSettings(rasters,simpaSettings,outWorkspace):
    """Override settings for a SIMPA model run in a fashion suitable for being embedded in a URC DS
       Scoring analysis. This involves:
       * Replacing any component inputs with preloaded datasets mapped from this tool.
       * Replacing the output directory with one designated by the PE Score tool.

    Args:
        rasters (RasterGroup): The group of rasters to be injected.
        simpaSettings (simpa_core.settings.Settings): The settings object to modify.
        outWorkspace (REE_Workspace): The workspace containing the appropriate output directory.
    """

    # start by setting output directory
    simpaSettings.outputDir= outWorkspace.workspace

    # create an empty raster to act as a shim for undefined variables
    shimDs = createShim(rasters)

    # remove basenames and add preloaded to inputFiles
    # MAP CID## to **_**_**_CID## (duplicates don't matter)

    keys = rasters.rasterNames
    for entry in simpaSettings.dataInputs:
        entry['baseName']=None
        hits = [k for k in keys if k.endswith(entry['fieldName'])]
        if len(hits)>0:
            # add preloaded raster
            # print(f'{hits[0]} --> {entry["fieldName"]}')
            entry['preloaded'] = rasters[hits[0]]
        else:
            # CID## is placeholder; use dummy empty layer as surrogate
            entry['preloaded'] = shimDs


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


def RunPEScoreDS(gdbDS, indexRasters,indexMask,outWorkspace, rasters_only=False,postProg=None):
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
    # import SIMPA here to avoid imports not relevant anywhere else
    from .simpa_core import model as simpaModel

    rasterDir = outWorkspace.get('raster_dir', None)
    t_allStart = process_time()
    print('Finding components...')
    components_data_dict = FindUniqueComponents(gdbDS,'DS')
    testRasters = RasterizeComponents(indexRasters,gdbDS,components_data_dict,rasterDir)

    print('Done')
    print('Calculating distances')
    domDistRasters,hitMaps = GenDomainIndexRasters(indexRasters, True,rasterDir, indexMask)
    distanceRasters = GetDSDistances(testRasters,rasterDir,indexMask)
    combineRaster = FindDomainComponentRasters(domDistRasters,hitMaps,testRasters,rasterDir)

    multRasters=NormMultRasters(combineRaster, distanceRasters, rasterDir)
    print('Done')
    if 'raster_dir' in outWorkspace and rasters_only:
        print('Exit on rasters specified; exiting')
        return

    # Fuzzy Rules
    # P:\02_DataWorking\REE\URC_Fuzzy_Logic\UCR_FL.sijn

    print('**** Begin SIMPA processing ****')
    simpaModel.useMultiProc = not os.environ.get('URC_SIMPA_DISABLE_MULTI',False)  # for testing
    if postProg is not None:
        simpaModel.MdlProg = postProg
    theModel = simpaModel.ModelRunner()
    theModel.load_inputsfile(os.path.join(os.path.dirname(__file__),'UCR_FL.sijn'))

    injectURCSettings(multRasters,theModel.settings,outWorkspace)

    theModel.run_model()
    theModel.write_outputs()

    print("**** End SIMPA processing ****")
    print("DS scoring complete.")