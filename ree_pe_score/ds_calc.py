from .common_utils import *
from .urc_common import *
from time import process_time
from osgeo import gdal

def GetDSDistances(src_rasters,cache_dir=None,mask=None):

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

    raise Exception("Under Construction")
    # TODO:
    #   --> Capture / extract domains for each layer (DS only)
    #   --> Euclidean distance for DS, source Domain Rasters (precomputed in creategrid?)
    #   --> Euclidean distance for extracted domains.
    #   --> combine implicit distance + explicit distance Then normalize. (Combine on CID)
    #        --> normalize each raster first, then multiply
    #   --> SIMPA
    #
    # Fuzzy Rules
    # P:\02_DataWorking\REE\URC_Fuzzy_Logic\UCR_FL.sijn

    # TODO: update everything below this line for Raster work

    # drvr = gdal.GetDriverByName('memory')
    # scratchDS=drvr.Create('scratch',0,0,0,gdal.OF_VECTOR)
    #
    # workingLyr=FeaturesPresent(PE_Grid, unique_components, components_data_array, scratchDS, outWorkspace)
    # print("\nStep 1 complete")
    # WriteIfRequested(workingLyr,outWorkspace,'step1_grid',drvrName='sqlite',)
    #
    # # begin dbg inject
    # # import wingoDbg as dbg
    # #
    # # dbgDS = gdal.OpenEx(r"C:/Users/wingop/dev_stuff/Python_workspace/REE_PE_Score/testData/SumTroubleshoot/step1.sqlite",gdal.OF_VECTOR)
    # # workingLyr = dbgDS.GetLayer(0)
    # # end dbg inject
    #
    # # workingLyr=DetermineDAForComponents(workingLyr,unique_components)
    # # print("\nStep 2 complete")
    # print("\nStep 2 Omitted (not necessary)")
    #
    # df_dict_LG_domains_ALL=DistribOverDomains(workingLyr, unique_components)
    # print("\nStep 3 complete")
    # if 'step3_dataframe' in outWorkspace:
    #     df_dict_LG_domains_ALL['compiled'].to_csv(outWorkspace['step3_dataframe'],
    #                                                                          index=True)
    #
    #     # pd.concat([pd.DataFrame({'indicies':df_dict_LG_domains_ALL['indicies']}),
    #      #            df_dict_LG_domains_ALL['LG'],df_dict_LG_domains_ALL['LD'],
    #      #            df_dict_LG_domains_ALL['UD'],'compiled'],axis=1).to_csv(args.output_dir['step3_dataframe'],index=True)
    #
    #
    # CalcSum(df_dict_LG_domains_ALL, workingLyr, unique_components,targetData,outWorkspace)
    # print("\nStep 4 complete")
    #
    # # scratchDS.FlushCache()
    # WriteIfRequested(workingLyr,outWorkspace,'final_grid',drvrName='sqlite')
    #
    # print("Done.")
    #
    # t_allStop = process_time()
    # seconds = t_allStop - t_allStart
    # print('Total time:',end=' ')
    # printTimeStamp(seconds)
