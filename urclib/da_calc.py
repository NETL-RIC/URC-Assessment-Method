"""Module for DA specific calculations."""
from .urc_common import *


def calc_sum(df_hits):
    """Perform DA scoring calculation based on field component names.

    Args:
        df_hits (pandas.DataFrame): The initial values for any components counted.

    Returns:
        pandas.DataFrame: The results of the calculations, in tabular form.
    """

    # Comprehensive list of all possible components, including those deemed 'not testable' and
    # 'not evalutated (duplicate)'.  This list current as of 2020-03-24.  Values copied from Google Sheet
    # "REE Enrichment Tree Related Data - Google Sheets 'Component_Codes_asof_2020-03-24'!Y2:FR2"
    components_all = ['DA_Fl_LD_CID01', 'DA_Fl_LD_CID02', 'DA_Fl_LD_CID03', 'DA_Fl_LD_CID04', 'DA_Fl_LD_CID05',
                      'DA_Fl_LD_CID06', 'DA_Fl_LD_CID07', 'DA_Fl_LD_CID08', 'DA_Fl_LD_CID09', 'DA_Eo_LD_CID10',
                      'DA_Fl_NE_CID11', 'DA_Fl_NE_CID12', 'DA_Fl_NE_CID13', 'DA_Eo_LG_CID14', 'DA_Eo_LG_CID15',
                      'DA_Eo_LD_CID16', 'DA_Fl_LD_CID17', 'DA_Fl_LG_CID18', 'DA_Fl_NT_CID19', 'DA_Fl_LD_CID19',
                      'DA_Eo_NT_CID20', 'DA_Fl_NT_CID20', 'DA_Eo_NT_CID21', 'DA_Eo_LD_CID21', 'DA_Eo_NE_CID21',
                      'DA_Eo_NT_CID22', 'DA_Eo_NT_CID23', 'DA_MA_LD_CID24', 'DA_MA_LD_CID25', 'DA_MA_LD_CID26',
                      'DA_MA_LD_CID27', 'DA_MA_LD_CID28', 'DA_MA_LD_CID29', 'DA_MA_LD_CID30', 'DA_MA_LD_CID31',
                      'DA_MA_LD_CID32', 'DA_MA_NE_CID33', 'DA_MA_NE_CID34', 'DA_MA_NE_CID35', 'DA_MA_NE_CID36',
                      'DA_MA_UD_CID37', 'DA_MA_UD_CID38', 'DA_MA_UD_CID39', 'DA_MA_UD_CID40', 'DA_MA_UD_CID41',
                      'DA_MA_LG_CID42', 'DA_MA_UD_CID43', 'DA_MA_NT_CID44', 'DA_HP_UD_CID45', 'DA_HP_LG_CID46',
                      'DA_MA_LG_CID47', 'DA_MA_LG_CID48', 'DA_MA_LG_CID49', 'DA_MA_LG_CID50', 'DA_MA_NT_CID51',
                      'DA_MA_LG_CID52', 'DA_MA_NT_CID53', 'DA_MA_LG_CID54', 'DA_MP_NT_CID55', 'DA_MP_LG_CID56',
                      'DA_MP_LG_CID57', 'DA_MP_NT_CID58', 'DA_MA_NT_CID59', 'DA_Fl_LD_CID10', 'DA_Fl_NT_CID21',
                      'DA_Fl_LD_CID21', 'DA_Fl_NE_CID21', 'DA_Fl_NT_CID22', 'DA_Fl_NT_CID23', 'DA_MP_LD_CID24',
                      'DA_MP_LD_CID25', 'DA_MP_LD_CID26', 'DA_MP_LD_CID27', 'DA_MP_LD_CID28', 'DA_MP_LD_CID29',
                      'DA_MP_LD_CID30', 'DA_MP_LD_CID31', 'DA_MP_LD_CID32', 'DA_MP_NE_CID33', 'DA_MP_NE_CID34',
                      'DA_MP_NE_CID35', 'DA_MP_NE_CID36', 'DA_MP_UD_CID37', 'DA_MP_UD_CID38', 'DA_MP_UD_CID39',
                      'DA_MP_UD_CID40', 'DA_MP_UD_CID41', 'DA_MP_LG_CID42', 'DA_MP_UD_CID43', 'DA_MP_NT_CID44',
                      'DA_HA_LG_CID47', 'DA_HA_LG_CID48', 'DA_HA_LG_CID49', 'DA_MP_LG_CID50', 'DA_MP_NT_CID51',
                      'DA_MP_LG_CID52', 'DA_MP_NT_CID53', 'DA_HA_LG_CID54', 'DA_HP_NT_CID55', 'DA_HP_LG_CID56',
                      'DA_HP_LG_CID57', 'DA_HP_NT_CID58', 'DA_HA_NT_CID59', 'DA_HA_LD_CID24', 'DA_HA_LD_CID25',
                      'DA_HA_LD_CID26', 'DA_HA_LD_CID27', 'DA_HA_LD_CID28', 'DA_HA_LD_CID29', 'DA_HA_LD_CID30',
                      'DA_HA_LD_CID31', 'DA_HA_LD_CID32', 'DA_HA_NE_CID33', 'DA_HA_NE_CID34', 'DA_HA_NE_CID35',
                      'DA_HA_NE_CID36', 'DA_HA_UD_CID37', 'DA_HA_UD_CID38', 'DA_HA_UD_CID39', 'DA_HA_UD_CID40',
                      'DA_HA_UD_CID41', 'DA_HA_LG_CID42', 'DA_HA_UD_CID43', 'DA_HA_UD_CID45', 'DA_HA_LG_CID50',
                      'DA_HA_NT_CID51', 'DA_HA_LG_CID52', 'DA_HA_NT_CID53', 'DA_HP_LD_CID24', 'DA_HP_LD_CID25',
                      'DA_HP_LD_CID26', 'DA_HP_LD_CID27', 'DA_HP_LD_CID28', 'DA_HP_LD_CID29', 'DA_HP_LD_CID30',
                      'DA_HP_LD_CID31', 'DA_HP_LD_CID32', 'DA_HP_NE_CID33', 'DA_HP_NE_CID34', 'DA_HP_NE_CID35',
                      'DA_HP_NE_CID36', 'DA_HP_UD_CID37', 'DA_HP_UD_CID38', 'DA_HP_UD_CID39', 'DA_HP_UD_CID40',
                      'DA_HP_UD_CID41', 'DA_HP_LG_CID42', 'DA_HP_UD_CID43', 'DA_HP_LG_CID50', 'DA_HP_NT_CID51',
                      'DA_HP_NT_CID53']  # Added DA_HP_NT_CID53 #DJ

    # create empty frame with all columns to capture any missing columns
    df_pe_calc = pd.DataFrame(data=df_hits, columns=['LG_index'] + components_all)
    df_pe_calc['LG_index'] = df_hits.index
    df_pe_calc.set_index('LG_index', inplace=True)
    df_pe_calc.fillna(0)

    ############################################################################################################

    # Generic assignment for all cells
    # df_pe_calc['DA_Eo_NT_CID20'] = True  # Accumulation of peat # No specific data for this component, data must prove
    #                                      # ash was deposited at the same time of peat accumulation (ex. same
    #                                      # formation). -DJ
    # df_pe_calc['DA_Fl_NT_CID20'] = True  # Accumulation of peat # No specific data for this component, data must prove
    #                                      # ash was deposited at the same time of peat accumulation (ex. same
    #                                      # formation). -DJ

    # df_pe_calc['DA_Fl_NT_CID22'] = True  # Burial of peat # Presence of coal is proof that there was burial of peat,
    #                                      # use either this or CID23, not both for DA count. -DJ.

    df_pe_calc['DA_Fl_NT_CID23'] = True     # Conversion of peat to coal # using this component to represent that there
                                            # is coal present in the study area -DJ.

    df_pe_calc['DA_HA_LG_CID52'] = True     # Coal and/or related strata # using this component to represent that there
                                            # is coal present in the study area -DJ.
    df_pe_calc['DA_HP_LG_CID52'] = True     # Coal and/or related strata # using this component to represent that there
                                            # is coal present in the study area -DJ.
    df_pe_calc['DA_MA_LG_CID52'] = True     # Coal and/or related strata # using this component to represent that there
                                            # is coal present in the study area -DJ.
    df_pe_calc['DA_MP_LG_CID52'] = True     # Coal and/or related strata # using this component to represent that there
                                            # is coal present in the study area -DJ.

    # Powder River Basin assignment for all cells (PRB)
    # df_pe_calc['DA_Eo_LG_CID14'] = True  # Mire downwind of volcanism (this is true for PRB) #Should not be assumed to
    #                                      # be true, data should represet this component -DJ.
    # df_pe_calc['DA_Fl_LD_CID17'] = True  # Mire in same paleo-drainage basin #Should not be assumed to be true, data
    #                                      # should represet this component -DJ.
    # df_pe_calc['DA_Fl_LG_CID18'] = True  # Mire downstream of REE source #Should not be assumed to be true, data
    #                                      # should represet this component -DJ.

    ############################################################################################################

    # Eo relevant components.  Not testable: CID15, CID21

    # Fl relevant components.  Not testable: CID17, CID18, CID19, CID21
    df_pe_calc['DA_Fl_NE_CID11'] = df_pe_calc[['DA_Fl_LD_CID01', 'DA_Fl_LD_CID02', 'DA_Fl_LD_CID03', 'DA_Fl_LD_CID04',
                                               'DA_Fl_LD_CID05', 'DA_Fl_LD_CID06']].max(axis=1)  # Bedrock REE deposit
    df_pe_calc['DA_Fl_NE_CID12'] = df_pe_calc[['DA_Fl_LD_CID07', 'DA_Fl_LD_CID08', 'DA_Fl_LD_CID09']].max(
        axis=1)  # Sed REE deposit
    df_pe_calc['DA_Fl_NE_CID13'] = df_pe_calc[['DA_Fl_LD_CID10', 'DA_Fl_NE_CID11', 'DA_Fl_NE_CID12']].max(
        axis=1)  # REE source

    # HA relevant components.  Not testable: CID47, CID48, CID49, CID51, CID53, CID59
    df_pe_calc['DA_HA_NE_CID33'] = df_pe_calc[['DA_HA_UD_CID37', 'DA_HA_UD_CID38', 'DA_HA_UD_CID39',
                                               'DA_HA_UD_CID40', 'DA_HA_UD_CID41']].max(axis=1)  # Alkaline volcanic ash
    df_pe_calc['DA_HA_NE_CID34'] = df_pe_calc[['DA_HA_LD_CID24', 'DA_HA_LD_CID25', 'DA_HA_LD_CID26',
                                               'DA_HA_LD_CID27', 'DA_HA_LD_CID28', 'DA_HA_LD_CID29']].max(
        axis=1)  # Bedrock REE deposit
    df_pe_calc['DA_HA_NE_CID35'] = df_pe_calc[['DA_HA_LD_CID30', 'DA_HA_LD_CID31', 'DA_HA_LD_CID32']].max(
        axis=1)  # Sed REE deposit
    df_pe_calc['DA_HA_NE_CID36'] = df_pe_calc[['DA_HA_NE_CID33', 'DA_HA_NE_CID34', 'DA_HA_NE_CID35']].max(
        axis=1)  # REE source
    df_pe_calc['DA_HA_UD_CID45'] = df_pe_calc[['DA_HA_LG_CID42', 'DA_HA_UD_CID43', 'DA_HA_UD_CID45']].max(
        axis=1)  # Conduit for fluid flow # Added CID45 because there is data that represents it and 42 and 43 combine
    # to make up 45 as well (OR relationships) -DJ.

    # HP relevant components.  Not testable: CID47, CID48, CID49, CID51, CID53, CID55, CID58
    df_pe_calc['DA_HP_NE_CID33'] = df_pe_calc[['DA_HP_UD_CID37', 'DA_HP_UD_CID38', 'DA_HP_UD_CID39',
                                               'DA_HP_UD_CID40', 'DA_HP_UD_CID41']].max(axis=1)  # Alkaline volcanic ash
    df_pe_calc['DA_HP_NE_CID34'] = df_pe_calc[['DA_HP_LD_CID24', 'DA_HP_LD_CID25', 'DA_HP_LD_CID26',
                                               'DA_HP_LD_CID27', 'DA_HP_LD_CID28', 'DA_HP_LD_CID29']].max(
        axis=1)  # Bedrock REE deposit
    df_pe_calc['DA_HP_NE_CID35'] = df_pe_calc[['DA_HP_LD_CID30', 'DA_HP_LD_CID31', 'DA_HP_LD_CID32']].max(
        axis=1)  # Sed REE deposit
    df_pe_calc['DA_HP_NE_CID36'] = df_pe_calc[['DA_HP_NE_CID33', 'DA_HP_NE_CID34', 'DA_HP_NE_CID35']].max(
        axis=1)  # REE source
    df_pe_calc['DA_HP_UD_CID45'] = df_pe_calc[['DA_HP_LG_CID42', 'DA_HP_UD_CID43', 'DA_HP_UD_CID45']].max(
        axis=1)  # Conduit for fluid flow # Added CID45 because there is data that represents it and 42 and 43 combine
    # to make up 45 as well (OR relationships) #DJ.
    df_pe_calc['DA_HP_NE_57_46'] = df_pe_calc[['DA_HP_LG_CID57', 'DA_HP_LG_CID46']].max(axis=1)  # Dissolve phosphorus

    # MA relevant components.  Not testable:  CID44, CID47, CID48, CID49, CID51, CID53, CID59
    df_pe_calc['DA_MA_NE_CID33'] = df_pe_calc[['DA_MA_UD_CID37', 'DA_MA_UD_CID38', 'DA_MA_UD_CID39',
                                               'DA_MA_UD_CID40', 'DA_MA_UD_CID41']].max(axis=1)  # Alkaline volcanic ash
    df_pe_calc['DA_MA_NE_CID34'] = df_pe_calc[['DA_MA_LD_CID24', 'DA_MA_LD_CID25', 'DA_MA_LD_CID26',
                                               'DA_MA_LD_CID27', 'DA_MA_LD_CID28', 'DA_MA_LD_CID29']].max(
        axis=1)  # Bedrock REE deposit
    df_pe_calc['DA_MA_NE_CID35'] = df_pe_calc[['DA_MA_LD_CID30', 'DA_MA_LD_CID31', 'DA_MA_LD_CID32']].max(
        axis=1)  # Sed REE deposit
    df_pe_calc['DA_MA_NE_CID36'] = df_pe_calc[['DA_MA_NE_CID33', 'DA_MA_NE_CID34', 'DA_MA_NE_CID35']].max(
        axis=1)  # REE source
    df_pe_calc['DA_MA_NT_CID44'] = df_pe_calc[['DA_MA_LG_CID42', 'DA_MA_UD_CID43', 'DA_MA_NT_CID44']].max(
        axis=1)  # Conduit for fluid flow # Added CID44 because there is data that represents it and 42 and 43 combine
    # to make up 44 as well (OR relationships) -DJ.

    # MP relevant components.  Not testable: CID47, CID48, CID49, CID51, CID53, CID55, CID58
    df_pe_calc['DA_MP_NE_CID33'] = df_pe_calc[['DA_MP_UD_CID37', 'DA_MP_UD_CID38', 'DA_MP_UD_CID39',
                                               'DA_MP_UD_CID40', 'DA_MP_UD_CID41']].max(axis=1)  # Alkaline volcanic ash
    df_pe_calc['DA_MP_NE_CID34'] = df_pe_calc[['DA_MP_LD_CID24', 'DA_MP_LD_CID25', 'DA_MP_LD_CID26',
                                               'DA_MP_LD_CID27', 'DA_MP_LD_CID28', 'DA_MP_LD_CID29']].max(
        axis=1)  # Bedrock REE deposit
    df_pe_calc['DA_MP_NE_CID35'] = df_pe_calc[['DA_MP_LD_CID30', 'DA_MP_LD_CID31', 'DA_MP_LD_CID32']].max(
        axis=1)  # Sed REE deposit
    df_pe_calc['DA_MP_NE_CID36'] = df_pe_calc[['DA_MP_NE_CID33', 'DA_MP_NE_CID34', 'DA_MP_NE_CID35']].max(
        axis=1)  # REE source
    df_pe_calc['DA_MP_NT_CID44'] = df_pe_calc[['DA_MP_LG_CID42', 'DA_MP_UD_CID43', 'DA_MP_NT_CID44']].max(
        axis=1)  # Conduit for fluid flow # Added CID44 because there is data that represents it and 42 and 43 combine
    # to make up 44 as well (OR relationships) -DJ.

    ############################################################################################################
    # DR components (NOTE: this is NOT the entire list of DR components; only those that are considered testable)
    dr_eo = ['DA_Eo_LD_CID10', 'DA_Eo_LG_CID14', 'DA_Eo_LD_CID16', 'DA_Fl_NT_CID20',
             'DA_Fl_NT_CID23']  # Changed CID22 to CID20 #DJ.
    dr_fl = ['DA_Fl_NE_CID13', 'DA_Fl_LD_CID17', 'DA_Fl_LG_CID18', 'DA_Fl_LD_CID19', 'DA_Fl_NT_CID20',
             'DA_Fl_NT_CID23']  # Changed CID22 to CID20, and added CID17/18/19 #DJ.
    dr_ha = ['DA_HA_LG_CID52', 'DA_HA_NE_CID36', 'DA_HA_UD_CID45', 'DA_HA_LG_CID54', 'DA_HA_NT_CID51',
             'DA_HA_NT_CID53']  # Removed DA_HA_LG_CID50 because it is not required and DA_HA_NE_CID42_43 because its
    # captured in CID45. Added DA_HA_NT_CID51/53 becaue they are required even if not
    # testable -DJ
    dr_hp = ['DA_HP_UD_CID45', 'DA_HP_LG_CID52', 'DA_HP_NE_CID36', 'DA_HP_NT_CID51', 'DA_HP_NT_CID53', 'DA_HP_NT_CID55',
             'DA_HP_LG_CID56']  # Removed DA_HP_LG_CID50 because it is not required, DA_HP_NE_CID42_43 because its
    # captured in CID45. and DA_HP_NE_57_46 because it is not required. Added
    # DA_HA_NT_CID51/53/55 becaue they are required even if not testable -DJ
    dr_ma = ['DA_MA_NT_CID44', 'DA_MA_LG_CID52', 'DA_MA_NE_CID36', 'DA_MA_LG_CID50', 'DA_MA_LG_CID54', 'DA_MA_NT_CID51',
             'DA_MA_NT_CID53']  # Removed DA_MA_NE_CID42_43 because its captured in CID44. Added DA_HA_NT_CID51/53
    # because they are required even if not testable -DJ
    dr_mp = ['DA_MP_NT_CID44', 'DA_MP_LG_CID52', 'DA_MP_NE_CID36', 'DA_MP_LG_CID50', 'DA_MP_LG_CID56', 'DA_MP_NT_CID51',
             'DA_MP_NT_CID53',
             'DA_MP_NT_CID55']  # Removed DA_MP_NE_CID42_43 because its captured in CID44. Added DA_HA_NT_CID51/53/55
    # because they are required even if not testable -DJ

    dr_types = [dr_eo, dr_fl, dr_ha, dr_hp, dr_ma, dr_mp]  # A list of required components (DR) for each mechanism type
    dr_labels = ['DR_EO', 'DR_FL', 'DR_HA', 'DR_HP', 'DR_MA',
                 'DR_MP']  # A list of required components (DR) for each mechanism type
    ############################################################################################################

    # Add sum fields to dataframe
    df_pe_calc['Eo_sum'] = df_pe_calc[dr_eo].sum(axis=1)
    df_pe_calc['Fl_sum'] = df_pe_calc[dr_fl].sum(axis=1)
    df_pe_calc['HA_sum'] = df_pe_calc[dr_ha].sum(axis=1)
    df_pe_calc['HP_sum'] = df_pe_calc[dr_hp].sum(axis=1)
    df_pe_calc['MA_sum'] = df_pe_calc[dr_ma].sum(axis=1)
    df_pe_calc['MP_sum'] = df_pe_calc[dr_mp].sum(axis=1)

    # Calculate DA_sum/DR
    for i in range(len(dr_types)):
        col = 'DA_' + dr_types[i][0][3:5] + '_sum_DR'  # Assemble column heading (e.g., 'DA_Eo_sum_DR')
        df_pe_calc[col] = df_pe_calc[dr_types[i][0][3:5] + '_sum'] / len(
            dr_types[i])  # Divide mechanism sum by DR (e.g., Eo_sum / dr_eo)

    print('DR counts:')
    for lbl, typ in zip(dr_labels, dr_types):
        print(f'  {lbl}: {len(typ)}')

    print('DA calculation complete.')

    return df_pe_calc


def run_pe_score_da(gdb_ds, index_rasters, index_mask, out_workspace, rasters_only=False, clipping_mask=None,
                    post_prog=None):
    """Calculate the PE score for DA values using the URC method.

    Args:
        gdb_ds (gdal.Dataset): The Database/dataset containing the vector layers representing the components to include.
        index_rasters (RasterGroup): The raster representing the indexes generated for the grid.
        index_mask (numpy.ndarray): Raw values representing the cells to include or exclude from the analysis.
        out_workspace (common_utils.UrcWorkspace): The container for all output filepaths.
        rasters_only (bool): If true, skip analysis after all intermediate rasters are written.
           Only has an effect if `out_workspace` has 'raster_dir' defined.
        post_prog (function,optional): Optional function to deploy for updating incremental progress feedback.
            function should expect a single integer as its argument, in the range of [0,100].
        clipping_mask (gdal.Dataset,optional): Clipping mask to apply, if any.
    """

    print("Begin DA PE Scoring...")
    with do_time_capture():
        raster_dir = out_workspace.get('raster_dir', None)
        components_data_dict = find_unique_components(gdb_ds, 'DA')
        test_rasters = rasterize_components(index_rasters, gdb_ds, components_data_dict, raster_dir, index_mask)
        print('Rasterization Complete')
        empty_names = test_rasters.empty_raster_names
        if len(empty_names) > 0:
            print("The Following DA rasters are empty:")
            for en in empty_names:
                print(f'   {en}')
        else:
            print("No empty DA rasters detected.")
        # domIndRasters,hit_maps=gen_domain_index_rasters(index_rasters, False,raster_dir, index_mask)
        # combo_rasters=find_domain_component_rasters(domIndRasters,hit_maps,test_rasters,raster_dir)

        if clipping_mask is not None:
            # True to enable multiprocessing
            test_rasters.clip_with_raster(clipping_mask, True)
            if raster_dir is not None:
                test_rasters.copy_rasters('GTiff', raster_dir, '_clipped.tif',GEOTIFF_OPTIONS)

        if 'raster_dir' in out_workspace and rasters_only:
            print('Exit on rasters specified; exiting')
            return UrcWorkspace()

        df = build_pandas_dataframe(index_rasters, test_rasters)  # combo_rasters)
        df_results = calc_sum(df)

        print("Writing out DA/DR rasters...")
        dr_cols = [col for col in df_results.columns if col.endswith('DR')]
        dr_rasters = dataframe_to_rastergroup(df_results, index_rasters['lg'], dr_cols)
        if clipping_mask is not None:
            # True to enable multiprocessing
            dr_rasters.clip_with_raster(clipping_mask, True)
        copies = dr_rasters.copy_rasters('GTiff', out_workspace.workspace, '.tif',GEOTIFF_OPTIONS)

        print("DA complete")

    ret = UrcWorkspace()
    for ds in copies:
        path = ds.GetDescription()
        ret[os.path.splitext(os.path.basename(path))[0]] = path
    return ret
