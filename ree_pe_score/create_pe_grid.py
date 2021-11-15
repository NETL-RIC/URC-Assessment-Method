"""Create grid to be used for PE Scoring."""

from .common_utils import *
from time import process_time

def ClipLayer(scratchDS,inputLayer,clippingLayer):
    """Clip one layer with the geometry of another.

    Args:
        scratchDS (gdal.Dataset): Dataset to hold newly created layer.
        inputLayer (ogr.Layer): The layer to be clipped.
        clippingLayer (ogr.Layer): The layer to clip by.

    Returns:
        ogr.Layer: The newly clipped layer.
    """
    def clipProg(percent, msg, data):
        display = int(percent * 100)
        if display % 10 == 0:
            print(f'{display}...', end='')

    coordTrans = osr.CoordinateTransformation(clippingLayer.GetSpatialRef(), inputLayer.GetSpatialRef())
    # transform filter coords

    reprojLyr = None
    if inputLayer.GetSpatialRef().IsSame(clippingLayer.GetSpatialRef()) == 0:
        # we need to reproject
        reprojLyr = scratchDS.CreateLayer("reproj", inputLayer.GetSpatialRef())

        # we can ignore attributes since we are just looking at geometry
        for feat in clippingLayer:
            geom = feat.GetGeometryRef()
            geom.Transform(coordTrans)
            tFeat = ogr.Feature(reprojLyr.GetLayerDefn())
            tFeat.SetGeometry(geom)
            reprojLyr.CreateFeature(tFeat)

        clippingLayer = reprojLyr
    clipOut = scratchDS.CreateLayer(inputLayer.GetName()+"_clipped", inputLayer.GetSpatialRef())

    print(f'Clipping {inputLayer.GetName()}: ', end='')
    inputLayer.Intersection(clippingLayer, clipOut, callback=clipProg)
    print('Done')

    if reprojLyr is not None:
        scratchDS.DeleteLayer(reprojLyr.GetName())

    return clipOut

def IndexCalc(domainType, lyr):
    """ Calculates index field for an STA domain type.

    Args:
        domainType (str): Name of the domain type.  Only the following two-letter strings should be used:
          * 'LD' (lithologic domain)
          * 'SD' (structural domain)
          * 'SA' (secondary alteration)
        lyr (osgeo.ogr.Layer) The layer to index.

    Returns:
        osgeo.gdal.Dataset: A copy of the input dataset with a new field for the domain index.
            **IMPORTANT**: This file will be saved to the same directory as `domainDS`.
    """

    domain_output_file = os.path.splitext(lyr.GetName())[0] + "_indexed.shp"

    drvr = gdal.GetDriverByName("ESRI Shapefile")
    DeleteFile(domain_output_file)
    outputDS = drvr.Create(domain_output_file, 0, 0, 0, gdal.GDT_Unknown)

    outLyr = outputDS.CopyLayer(lyr,lyr.GetName())

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

def indexDomainType(domainType,input_DS,lyr):
    """Index domain for Layer in dataset.

    Args:
        domainType (str): Name of the domain type.  Only the following two-letter strings should be used:
          * 'LD' (lithologic domain)
          * 'SD' (structural domain)
          * 'SA' (secondary alteration)

        input_DS (osgeo.gdal.Dataset): The loaded dataset.
        lyr (osgeo.ogr.Layer): The target layer from `input_DS`

    Returns:
        tuple: Containing the following:
          * osgeo.gdal.Dataset: The newly indexed Dataset or `input_DS` if indexing not needed.
          * osgeo.ogr.Layer: The newly created layer or `lyr` if indexing not needed.
    """


    idx_test = ListFieldNames(lyr)
    test = [i for i in idx_test if domainType in i]  # test if there is a field name containing domainType
    if len(test) == 0:  # if blank, calculate index field
        print(f"Calculating {domainType} index field...")
        input_DS = IndexCalc(domainType, lyr)
        lyr = input_DS.GetLayer(0)
    return input_DS,lyr

def CopyLayer(scratchDS,inPath,sRef=None):
    """Copy a layer, optionally applying a spatial transformation.

    Args:
        scratchDS (osgeo.gdal.Dataset): The Dataset to store the copied layer.
        inPath (str): Path to dataset containing Layer to copy (at index 0).
        sRef (osgeo.osr.SpatialReference,optional): Optional Spatial Reference to apply

    Returns:
        osgeo.ogr.Layer: The new copy of the layer residing in `scratchDS`, properly reprojected if needed.
    """

    tmpDS = gdal.OpenEx(inPath, gdal.OF_VECTOR)
    inLyr = tmpDS.GetLayer(0)
    if not sRef:
        return scratchDS.CopyLayer(tmpDS.GetLayer(0), tmpDS.GetLayer(0).GetName())

    trans = osr.CoordinateTransformation(inLyr.GetSpatialRef(), sRef)
    oldDefn = inLyr.GetLayerDefn()
    outLyr = scratchDS.CreateLayer(inLyr.GetName()+'_repoject', sRef, oldDefn.GetGeomType())
    for i in range(oldDefn.GetFieldCount()):
        outLyr.CreateField(oldDefn.GetFieldDefn(i))

    nDefn = outLyr.GetLayerDefn()
    for feat in inLyr:
        geom = feat.GetGeometryRef()
        geom.Transform(trans)

        newFeat = ogr.Feature(nDefn)
        newFeat.SetGeometry(geom)
        for i in range(nDefn.GetFieldCount()):
            newFeat.SetField(i, feat.GetField(i))
        outLyr.CreateFeature(newFeat)
    return outLyr


def buildIndices(workspace, outputs, cellWidth, cellHeight,sRef=None):
    """Create PE_Grid step 1 of 3: Create indexes for local grids and SD, LD, SA domains

    Args:
        workspace (common_utils.REE_Workspace): Input workspace object.
        outputs (common_utils.REE_Workspace): Output workspace object.
        cellWidth (float): The height to apply to generated grid; units derived from `ds`.
        cellHeight (float): The width to apply to generated grid; units derived from `ds`.
        sRef (osgeo.osr.SpatialReference,optional): Optional spatial reference to apply.
    Returns:
        tuple: Contains the following:
          * osgeo.gdal.Dataset: The mask layer.
          * numpy.ndarray: LD data.
          * numpy.ndarray: SD data.
    """

    drvr = gdal.GetDriverByName("memory")
    scratchDS = drvr.Create('scratch', 0, 0, 0, gdal.OF_VECTOR)

    lyrLD = CopyLayer(scratchDS,workspace['LD_input_file'],sRef)
    lyrSD = CopyLayer(scratchDS,workspace['SD_input_file'],sRef)

    if 'clip_geom' in workspace:
        clipDS = gdal.OpenEx(workspace['clip_geom'],gdal.OF_VECTOR)
        clipLyr = clipDS.GetLayer(0)
        lyrLD = ClipLayer(scratchDS, lyrLD, clipLyr)
        lyrSD = ClipLayer(scratchDS, lyrSD, clipLyr)

    print("\nCreating grid...")


    # Create a grid of rectangular polygon features
    # gridLyr = IndexFeatures(ds, inFeatures.GetLayer(0), cellWidth, cellHeight, [ogr.FieldDefn('OBJECTID', ogr.OFTInteger), ogr.FieldDefn("LG_index", ogr.OFTString)])
    coordMap,maskLyr = IndexFeatures(lyrLD, cellWidth, cellHeight)

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
    SD_input_DS,lyrSD = indexDomainType('SD',scratchDS,lyrSD)

    sd_data= rasterDomainIntersect(coordMap,flatMask,maskLyr.GetSpatialRef(),lyrSD, 'SD_index')
    writeRaster(maskLyr,sd_data,outputs['sd'],gdtype=gdal.GDT_Int32)
    print("Structure domains Processed.")


    ##### LITHOLOGIC DOMAINS #####
    # Generate index field for domains if not already present
    LD_input_DS,lyrLD = indexDomainType('LD',scratchDS,lyrLD)

    ld_data = rasterDomainIntersect(coordMap, flatMask, maskLyr.GetSpatialRef(), lyrLD, 'LD_index')
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

def RunCreatePEGrid(workspace, outWorkspace, gridWidth, gridHeight, postProg=None):
    """Create a series of index rasters representing the gridded version of a collection
    of vector records.

    Args:
        workspace (REE_Workspace): Container for all input filepaths.
        outWorkspace (REE_Workspace): Container for all output filepaths.
        gridWidth (int): The desired width of the grid, in cells.
        gridHeight (int): The desired height of the grid, in cells.
        postProg (function,optional): Optional function to deploy for updating incremental progress feedback.
            function should expect a single integer as its argument, in the range of [0,100]

    """
    t_start = process_time()
    proj = None
    if 'prj_file' in workspace:
        proj = osr.SpatialReference()
        with open(workspace['prj_file'], 'r') as inFile:
            proj.ImportFromESRI(inFile.readlines())
    # outDS = drvr.Create(os.path.join(args.outWorkspace.workspace,'outputs.shp'),0,0,0,gdal.OF_VECTOR)
    maskLyr,sd_data,ld_data = buildIndices(workspace, outWorkspace, gridWidth, gridHeight, proj)
    print("\nStep 1 complete")

    calcUniqueDomains(maskLyr, sd_data, ld_data, outWorkspace)
    t_end = process_time()
    print("\nStep 2 complete")
    print('Creation complete.')
    printTimeStamp(t_end-t_start)
