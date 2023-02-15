"""Create grid to be used for PE Scoring."""

from .common_utils import *
from time import process_time


def clip_layer(scratch_ds, input_layer, clipping_layer):
    """Clip one layer with the geometry of another.

    Args:
        scratch_ds (gdal.Dataset): Dataset to hold newly created layer.
        input_layer (ogr.Layer): The layer to be clipped.
        clipping_layer (ogr.Layer): The layer to clip by.

    Returns:
        ogr.Layer: The newly clipped layer.
    """

    def clip_prog(percent, msg, data):
        """Hook for GDAL to use to display incremental updates.

        Args:
            percent (float): The total progress, in [0.,1.].
            msg (str): Unused.
            data (object): Unused.
        """
        display = int(percent * 100)
        if display % 10 == 0:
            print(f'{display}...', end='')

    coordtrans = osr.CoordinateTransformation(clipping_layer.GetSpatialRef(), input_layer.GetSpatialRef())
    # transform filter coords

    reproj_lyr = None
    if input_layer.GetSpatialRef().IsSame(clipping_layer.GetSpatialRef()) == 0:
        # we need to reproject
        reproj_lyr = scratch_ds.CreateLayer("reproj", input_layer.GetSpatialRef())

        # we can ignore attributes since we are just looking at geometry
        for feat in clipping_layer:
            geom = feat.GetGeometryRef()
            # NOTE: if the line below fails, use a newer version of gdal.
            geom.Transform(coordtrans)
            tfeat = ogr.Feature(reproj_lyr.GetLayerDefn())
            tfeat.SetGeometry(geom)
            reproj_lyr.CreateFeature(tfeat)

        clipping_layer = reproj_lyr
    clip_out = scratch_ds.CreateLayer(input_layer.GetName() + "_clipped", input_layer.GetSpatialRef())

    print(f'Clipping {input_layer.GetName()}: ', end='')
    input_layer.Intersection(clipping_layer, clip_out, callback=clip_prog)
    print('Done')

    if reproj_lyr is not None:
        scratch_ds.DeleteLayer(reproj_lyr.GetName())

    return clip_out


def index_calc(domain_type, lyr):
    """ Calculates index field for an STA domain type.

    Args:
        domain_type (str): Name of the domain type.  Only the following two-letter strings should be used:
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
    if not delete_file(domain_output_file):
        print(domain_output_file, "not found in geodatabase!  Creating new...")
    else:
        print("Deleted existing file:", domain_output_file)

    output_ds = drvr.Create(domain_output_file, 0, 0, 0, gdal.OF_VECTOR)

    out_lyr = output_ds.CopyLayer(lyr, lyr.GetName())

    # Add to output file a new field for the index
    new_lbl = domain_type + '_index'
    new_field = ogr.FieldDefn(new_lbl, ogr.OFTString)
    out_lyr.CreateField(new_field)
    idx = out_lyr.GetLayerDefn().GetFieldIndex(new_lbl)

    # Calculate index field, starting at index_0

    for counter, feat in enumerate(out_lyr):
        feat.SetFieldString(idx, domain_type + str(counter))
        out_lyr.SetFeature(feat)
    out_lyr.ResetReading()

    return output_ds


def index_domain_type(domain_type, input_ds, lyr):
    """Index domain for Layer in dataset.

    Args:
        domain_type (str): Name of the domain type.  Only the following two-letter strings should be used:
          * 'LD' (lithologic domain)
          * 'SD' (structural domain)
          * 'SA' (secondary alteration)

        input_ds (osgeo.gdal.Dataset): The loaded dataset.
        lyr (osgeo.ogr.Layer): The target layer from `input_ds`

    Returns:
        tuple: Containing the following:
          * osgeo.gdal.Dataset: The newly indexed Dataset or `input_ds` if indexing not needed.
          * osgeo.ogr.Layer: The newly created layer or `lyr` if indexing not needed.
    """

    idx_test = list_fieldnames(lyr)
    test = [i for i in idx_test if f'{domain_type}_index' in i]  # test if there is a field name containing domain_type
    if len(test) == 0:  # if blank, calculate index field
        print(f"Calculating {domain_type} index field...")
        input_ds = index_calc(domain_type, lyr)
        lyr = input_ds.GetLayer(0)
    return input_ds, lyr


def copy_layer(scratch_ds, in_path, sref=None):
    """Copy a layer, optionally applying a spatial transformation.

    Args:
        scratch_ds (osgeo.gdal.Dataset): The Dataset to store the copied layer.
        in_path (str): Path to dataset containing Layer to copy (at index 0).
        sref (osgeo.osr.SpatialReference,optional): Optional Spatial Reference to apply

    Returns:
        osgeo.ogr.Layer: The new copy of the layer residing in `scratch_ds`, properly reprojected if needed.
    """

    tmp_ds = gdal.OpenEx(in_path, gdal.OF_VECTOR)
    inlyr = tmp_ds.GetLayer(0)
    if not sref:
        return scratch_ds.CopyLayer(tmp_ds.GetLayer(0), tmp_ds.GetLayer(0).GetName())

    trans = osr.CoordinateTransformation(inlyr.GetSpatialRef(), sref)
    old_defn = inlyr.GetLayerDefn()
    outlyr = scratch_ds.CreateLayer(inlyr.GetName() + '_repoject', sref, old_defn.GetGeomType())
    for i in range(old_defn.GetFieldCount()):
        outlyr.CreateField(old_defn.GetFieldDefn(i))

    n_defn = outlyr.GetLayerDefn()
    for feat in inlyr:
        geom = feat.GetGeometryRef()
        # NOTE: if the line below failse, use a newer version of GDAL
        geom.Transform(trans)

        new_feat = ogr.Feature(n_defn)
        new_feat.SetGeometry(geom)
        for i in range(n_defn.GetFieldCount()):
            new_feat.SetField(i, feat.GetField(i))
        outlyr.CreateFeature(new_feat)
    return outlyr


def build_indices(workspace, outputs, cell_width, cell_height, sref=None):
    """Create PE_Grid step 1 of 3: Create indexes for local grids and SD, LD, SA domains

    Args:
        workspace (common_utils.UrcWorkspace): Input workspace object.
        outputs (common_utils.UrcWorkspace): Output workspace object.
        cell_width (float): The height to apply to generated grid; units derived from `ds`.
        cell_height (float): The width to apply to generated grid; units derived from `ds`.
        sref (osgeo.osr.SpatialReference,optional): Optional spatial reference to apply.
    Returns:
        tuple: Contains the following:
          * osgeo.gdal.Dataset: The mask layer.
          * numpy.ndarray: LD data.
          * numpy.ndarray: SD data.
    """

    drvr = gdal.GetDriverByName("memory")
    scratch_ds = drvr.Create('scratch', 0, 0, 0, gdal.OF_VECTOR)

    lyr_ld = copy_layer(scratch_ds, workspace['LD_input_file'], sref)
    lyr_sd = copy_layer(scratch_ds, workspace['SD_input_file'], sref)
    lyr_sa = None
    if 'SA_input_file' in workspace:
        lyr_sa = copy_layer(scratch_ds, workspace['SA_input_file'], sref)
    print("\nCreating grid...")

    # Create a grid of rectangular polygon features
    # gridLyr = index_features(ds, inFeatures.GetLayer(0), cell_width, cell_height, [ogr.FieldDefn('OBJECTID',
    # ogr.OFTInteger), ogr.FieldDefn("LG_index", ogr.OFTString)])
    coordmap, masklyr = index_features(lyr_ld, cell_width, cell_height)

    # Calculate LG_index field, starting at LG0
    maskband = masklyr.GetRasterBand(1)
    flat_mask = maskband.ReadAsArray()
    flat_mask = flat_mask.ravel()
    lg_inds = np.full(flat_mask.shape, -9999, dtype=np.int32)
    lgid = 0
    for i in range(len(lg_inds)):
        if not flat_mask[i] == 0:
            lg_inds[i] = lgid
            lgid += 1

    write_raster(
        masklyr,
        lg_inds.reshape(masklyr.RasterYSize, masklyr.RasterXSize),
        outputs['lg'],
        gdtype=gdal.GDT_Int32
    )

    print("LG_index generated. \n")

    # ##### STRUCTURE DOMAINS #####
    # Generate index field for domains if not already present
    sd_input_ds, lyr_sd = index_domain_type('SD', scratch_ds, lyr_sd)

    sd_data = raster_domain_intersect(coordmap, flat_mask, masklyr.GetSpatialRef(), lyr_sd, 'SD_index')
    write_raster(masklyr, sd_data, outputs['sd'], gdtype=gdal.GDT_Int32)
    print("Structure domains Processed.")

    # ##### LITHOLOGIC DOMAINS #####
    # Generate index field for domains if not already present
    ld_input_ds, lyr_ld = index_domain_type('LD', scratch_ds, lyr_ld)

    ld_data = raster_domain_intersect(coordmap, flat_mask, masklyr.GetSpatialRef(), lyr_ld, 'LD_index')
    write_raster(masklyr, ld_data, outputs['ld'], gdtype=gdal.GDT_Int32)
    print("Lithology domains processed.\n")

    # ##### SECONDARY ALTERATION DOMAINS #####
    # Generate index field for domains if not already present
    if lyr_sa is not None:
        sa_input_ds, lyr_sa = index_domain_type('SA', scratch_ds, lyr_sa)

        sa_data = raster_domain_intersect(coordmap, flat_mask, masklyr.GetSpatialRef(), lyr_sa, 'SA_index')
        write_raster(masklyr, sa_data, outputs['sa'], gdtype=gdal.GDT_Int32)
        print("Secondary alteration domains processed.")
    else:
        print("NOTE: No Secondary Alteration Domains provided; skipping")
        sa_data = None
    return masklyr, sd_data, ld_data, sa_data


def calc_unique_domains(inmask, in_sd_data, in_ld_data, in_sa_data, outputs, nodata=-9999):
    """Create PE_Grid step 2 of 3: Calculate unique domains (UD).

    Args:
        inmask (osgeo.gdal.Dataset): The mask raster layer.
        in_sd_data (np.ndarray): The SD indices conforming to the dimensions of `in_mask`.
        in_ld_data (np.ndarray): The LD indices conforming to the dimensions of `in_mask`.
        in_sa_data (np.ndarray): The SA indices conforming to the dimensions of `in_mask`.
        outputs (common_utils.UrcWorkspace): The outputs workspace object.
        nodata (int,optional): The value to use to represent "no data" pixels. defaults to **-9999**.
    """

    ud_data = np.full(in_sd_data.shape, nodata, dtype=np.int32)
    flat_ud = ud_data.ravel()
    max_sd = in_sd_data.max()
    max_ld = in_ld_data.max()

    def _to_ud(ld, sd, sa=0):
        # ???: Is this the correct way to calculate UD?
        # return (max_sd*ld) + sd
        return (sa * max_sd * max_ld) + (ld * max_sd) + sd

    if in_sa_data is not None:
        for i, (ld_v, sd_v, sa_v) in enumerate(zip(in_ld_data.ravel(), in_sd_data.ravel(), in_sa_data.ravel())):
            if ld_v != nodata and sd_v != nodata and sa_v != nodata:
                flat_ud[i] = _to_ud(ld_v, sd_v, sa_v)
    else:
        for i, (ld_v, sd_v) in enumerate(zip(in_ld_data.ravel(), in_sd_data.ravel())):
            if ld_v != nodata and sd_v != nodata:
                flat_ud[i] = _to_ud(ld_v, sd_v)

    write_raster(
        inmask,
        ud_data,
        outputs['ud'],
        gdtype=gdal.GDT_Int32,
        nodata=nodata
    )


def run_create_pe_grid(workspace, out_workspace, gridwidth, gridheight, epsg=None, post_prog=None):
    """Create a series of index rasters representing the gridded version of a collection
    of vector records.

    Args:
        workspace (UrcWorkspace): Container for all input filepaths.
        out_workspace (UrcWorkspace): Container for all output filepaths.
        gridwidth (int): The desired width of the grid, in cells.
        gridheight (int): The desired height of the grid, in cells.
        epsg (int): Optional code for applying custom projection.
        post_prog (function,optional): Optional function to deploy for updating incremental progress feedback.
            function should expect a single integer as its argument, in the range of [0,100]

    """

    gdal.SetConfigOption('CPL_LOG', 'NUL' )

    with do_time_capture():
        proj = None
        if 'prj_file' in workspace:
            if epsg is not None:
                raise Exception(
                    f'both *.prg ({workspace["prj_file"]}) and EPSG code ({epsg}) provided; only one allowed.')
            proj = osr.SpatialReference()
            with open(workspace['prj_file'], 'r') as inFile:
                proj.ImportFromESRI(inFile.readlines())
        elif epsg is not None:
            proj = osr.SpatialReference()
            proj.ImportFromEPSG(epsg)
        # outDS = drvr.Create(os.path.join(args.out_workspace.workspace,'outputs.shp'),0,0,0,gdal.OF_VECTOR)
        masklyr, sd_data, ld_data, sa_data = build_indices(workspace, out_workspace, gridwidth, gridheight, proj)
        print("\nStep 1 complete")

        calc_unique_domains(masklyr, sd_data, ld_data, sa_data, out_workspace)

        print("\nStep 2 complete")
        print('Creation complete.')
