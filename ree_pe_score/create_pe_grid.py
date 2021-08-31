"""Create grid to be used for PE Scoring."""
import os
from osgeo import ogr,gdal,osr
from .common_utils import *
import pandas as pd


def IndexCalc(domainType, domainDS):
    """ Calculates index field for an STA domain type.

    Args:
        domainType (str): Name of the domain type.  Only the following two-letter strings should be used:
          * 'LD' (lithologic domain)
          * 'SD' (structural domain)
          * 'SA' (secondary alteration)
        domainDS (osgeo.gdal.Dataset): Dataset containing the featues to index.

    Returns:
        osgeo.gdal.Dataset: A copy of the input dataset with a new field for the domain index.
            **IMPORTANT**: This file will be saved to the same directory as `domainDS`.
    """

    domain_output_file = os.path.splitext(domainDS.GetFileList()[0])[0] + "_indexed.shp"

    drvr = gdal.GetDriverByName("ESRI Shapefile")
    DeleteFile(domain_output_file)
    outputDS = drvr.Create(domain_output_file, 0, 0, 0, gdal.GDT_Unknown)

    outputDS.CopyLayer(domainDS.GetLayer(0), domainDS.GetLayer(0).GetName())
    outLyr = outputDS.GetLayer(0)

    # Add to output file a new field for the index
    newLbl = domainType + '_index'
    newField = ogr.FieldDefn(newLbl,ogr.OFTString)
    outLyr.CreateField(newField)
    idx = outLyr.GetLayerDefn().GetFieldIndex(newLbl)

    # Calculate index field, starting at index_0


    for counter,feat in enumerate(outLyr):
        feat.SetFieldString(idx,domainType + str(counter))
    outLyr.ResetReading()

    return outputDS

def indexDomainType(domainType,input_file,layerInd=0):
    """Index domain for Layer in dataset.

    Args:
        domainType (str): Name of the domain type.  Only the following two-letter strings should be used:
          * 'LD' (lithologic domain)
          * 'SD' (structural domain)
          * 'SA' (secondary alteration)

        input_file (str): Path to the file to load.
        layerInd (int): Index to the layer to load. The default (0) will work for shape files.

    Returns:
        osgeo.gdal.Dataset: The newly loaded and indexed Dataset.
    """

    input_DS = gdal.OpenEx(input_file,gdal.OF_VECTOR)
    idx_test = ListFieldNames(input_DS.GetLayer(layerInd))
    test = [i for i in idx_test if domainType in i]  # test if there is a field name containing domainType
    if len(test) == 0:  # if blank, calculate index field
        print(f"Calculating {domainType} index field...")
        input_DS = IndexCalc(domainType, input_DS)
    return input_DS

def buildIndices(ds, workspace, outputs, cellWidth, cellHeight):
    """Create PE_Grid step 1 of 3: Create indexes for local grids and SD, LD, SA domains

    Args:
        ds (osgeo.gdal.Dataset): The Dateset to analyze.
        workspace (common_utils.REE_Workspace): Input workspace object.
        outputs (common_utils.REE_Workspace): Output workspace object.
        cellWidth (float): The height to apply to generated grid; units derived from `ds`.
        cellHeight (float): The width to apply to generated grid; units derived from `ds`.

    Returns:
        osgeo.ogr.Layer: Fully indexed culled fishnet Layer, which resides in `ds`.
    """
    # Final output files
    ds.CreateLayer("build_indices")

    print("\nCreating grid...")

    inPath=workspace['LD_input_file']
    inFeatures = gdal.OpenEx(inPath,gdal.OF_VECTOR)
    # Create a grid of rectangular polygon features
    # gridLyr = IndexFeatures(ds, inFeatures.GetLayer(0), cellWidth, cellHeight, [ogr.FieldDefn('OBJECTID', ogr.OFTInteger), ogr.FieldDefn("LG_index", ogr.OFTString)])
    coordMap,maskLyr = IndexFeatures(inFeatures.GetLayer(0), cellWidth, cellHeight)

    # Calculate LG_index field, starting at LG0
    maskBand = maskLyr.GetRasterBand(1)
    flatMask = maskBand.ReadAsArray()
    flatMask = flatMask.ravel()
    lgInds = np.full(flatMask.shape,-9999,dtype=np.int)
    lgid=0
    for i in range(len(lgInds)):
        if not flatMask[i]==0:
            lgInds[i]=lgid
            lgid+=1

    writeRaster(
        maskLyr,
        lgInds.reshape(maskLyr.RasterYSize,maskLyr.RasterXSize),
        outputs['lg'],
        gdtype=gdal.GDT_Int32
    )

    print("LG_index generated. \n")

    ##### STRUCTURE DOMAINS #####
    # Generate index field for domains if not already present
    SD_input_DS = indexDomainType('SD',workspace['SD_input_file'])

    sd_data= rasterDomainIntersect(coordMap,flatMask,maskLyr.GetSpatialRef(),SD_input_DS.GetLayer(0), 'SD_index')
    writeRaster(maskLyr,sd_data,outputs['sd'],gdtype=gdal.GDT_Int32)
    print("Structure domains Processed.")


    ##### LITHOLOGIC DOMAINS #####
    # Generate index field for domains if not already present
    LD_input_DS = indexDomainType('LD',workspace['LD_input_file'])

    ld_data = rasterDomainIntersect(coordMap, flatMask, maskLyr.GetSpatialRef(), LD_input_DS.GetLayer(0), 'LD_index')
    writeRaster(maskLyr, ld_data, outputs['ld'], gdtype=gdal.GDT_Int32)
    print("Lithology domains processed.\n")

    return maskLyr,sd_data,ld_data

def calcUniqueDomains(inMask,inSD_data,inLD_data,outputs,nodata=-9999):
    """Create PE_Grid step 2 of 3: Calculate unique domains (UD) using Pandas DataFrame.

    Args:
        inMask (osgeo.gdal.Dataset): The mask raster layer.
        inSD_data (np.ndarray): The SD indices conforming to the dimensions of `inMask`.
        inLD_data (np.ndarray): The LD indices conforming to the dimensions of `inMask`.
        outputs (common_utils.REE_Workspace): The outputs workspace object.
        nodata (int,optional): The value to use to represent "no data" pixels. defaults to **-9999**.
    """

    ud_data = np.full(inSD_data.shape,nodata,dtype=np.int32)
    flat_ud = ud_data.ravel()
    max_SD = inSD_data.max()

    def _toUD(ld,sd):
        # ???: Is this the correct way to calculate UD?
        return (max_SD*ld)+sd

    for i,(ld_v,sd_v) in enumerate(zip(inLD_data.ravel(),inSD_data.ravel())):
        if ld_v != nodata and sd_v != nodata:
            flat_ud[i] = _toUD(ld_v,sd_v)

    writeRaster(
        inMask,
        ud_data,
        outputs['ud'],
        gdtype=gdal.GDT_Int32,
        nodata=nodata
    )

def RunCreatePEGrid(workspace,output_dir,gridWidth,gridHeight,postProg=None):

    #add outputs here:
    output_dir['lg']='lg_inds.tif'
    output_dir['sd']='sd_inds.tif'
    output_dir['ld'] ='ld_inds.tif'
    output_dir['ud'] ='ud_inds.tif'

    # ClearPEDatasets(workspace)
    drvr = gdal.GetDriverByName("memory")
    scratchDS = drvr.Create('scratch', 0, 0, 0, gdal.OF_VECTOR)
    drvr = gdal.GetDriverByName("ESRI Shapefile")

    # outDS = drvr.Create(os.path.join(args.output_dir.workspace,'outputs.shp'),0,0,0,gdal.OF_VECTOR)
    maskLyr,sd_data,ld_data = buildIndices(scratchDS, workspace, output_dir, gridWidth, gridHeight)
    print("\nStep 1 complete")

    calcUniqueDomains(maskLyr,sd_data,ld_data, output_dir)
    print("\nStep 2 complete")


    print('Creation complete.')
