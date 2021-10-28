""" Create lists for unique components and each corresponding dataset """

from .common_utils import *

from time import process_time
import pandas as pd
import sys
import os
import fnmatch
from osgeo import gdal, ogr
import numpy as np

def printTimeStamp(rawSeconds):
    """
    Print raw seconds in nicely hour, minute, seconds format.

    Args:
        rawSeconds (int): The raw seconds to print.
    """

    totMin,seconds = divmod(rawSeconds,60)
    hours,minutes = divmod(totMin,60)
    print(f"Runtime: {hours} hours, {minutes} minutes, {round(seconds,2)} seconds.")

######################################################################################################################
def ListFeatureClassNames(ds, wildCard, first_char=0, last_char=sys.maxsize):
    """Function that creates a list of all unique REE-Coal components in an ESRI GDB Feature Dataset, for use in use in
        calculating PE score from DA and DS databases.

    Args:
        ds (osgeo.gdal.Dataset): The dataset to query.
        wildCard (str): Criteria used to limit the results returned.
        first_char (int,optional): Index of first character to include in the filename.
            Defaults to 0.
        last_char (int,optional): Index of lastcharacter to include in the filename.
            Defaults to position of last character in string.

    Returns:
        list: sorted, non-repeating iterable sequence of layer names based on the WildCard criteria
    """

    fcNames = [ds.GetLayer(i).GetName() for i in range(ds.GetLayerCount())]
    # match against wildcard
    fcNames=[x[first_char:last_char] for x in fnmatch.filter(fcNames,wildCard)]

    return sorted(set(fcNames))


######################################################################################################################
def ListFeatureClasses(ds,wildCard):
    """Function that creates a list of all unique REE-Coal components in an ESRI GDB Feature Dataset, for use in use in
        calculating PE score from DA and DS databases.

    Args:
        ds (osgeo.gdal.Dataset): The dataset to query.
        wildCard (str): Criteria used to limit the results returned.

    Returns:
        list: sorted, non-repeating iterable sequence of Layers based on the WildCard criteria
    """

    fcNames=ListFeatureClassNames(ds, wildCard)

    fcList = []
    for i in range(ds.GetLayerCount()):
        lyr = ds.GetLayer(i)
        if lyr.GetName() in fcNames:
            fcList.append(lyr)


    return fcList


######################################################################################################################
def replaceNULL(feature_class, field):
    """Replace NULL values with zeros for a field in a feature class

    Args:
        feature_class (osgeo.ogr.Layer): Layer containing the field to be modified.
        field (str): Name of the field to be evaluated and modified if necessary.
    """

    idx = feature_class.GetLayerDefn().GetFieldIndex(field)
    for feat in feature_class:
        if feat.IsFieldNull(idx):
            feat.SetField(idx,0)
    feature_class.ResetReading()


def FindUniqueComponents(gdbDS,prefix):
    """Step 0: find the collections to be used in subsequent steps.

    Args:
        gdbDS (osgeo.gdal.Dataset): Dataset containing features to parse. Expected to
          originate from a file geodatabase (.gdb) file.
        prefix (str): The prefix used to filter returned layers.

    Returns:
        tuple:
            0. list: List of unique layer names.
            1. list: Layer objects corresponding to labels in entry 0.
    """

    # Create a list of all unique code prefixes for the component IDs
    unique_components = ListFeatureClassNames(gdbDS, wildCard=prefix+"*", first_char=0, last_char=14)

    # An array comprising all components and their respective feature classes
    components_data = {}

    # Generate a list of feature classes for each Emplacement Type, Influence Extent, AND Component ID combination
    for uc in unique_components:
        component_datasets = ListFeatureClasses(gdbDS, wildCard=(uc + "*"))

        # Append list to a single array
        components_data[uc] = component_datasets

    return components_data


def FeaturesPresent(PE_Grid, unique_components, components_data_array, scratchDS, outputs):
    """Step 1 of 4: Presence/absence for each feature class in the target Feature Dataset.
        Creates a new field in PE_Grid for each feature class in the geodatabase.

    Args:
        PE_Grid (osgeo.ogr.Layer): The layer to query.
        unique_components (list): Names of Layers/feature sets included in processing.
        components_data_array (list): Layers to use in evaluations.
        scratchDS (osgeo.gdal.Dataset): Dataset for storing any temporary and returned Layers.
        outputs (common_utils.REE_Workspace): Outputs workspace object.

    Returns:
        osgeo.ogr.Layer: The layer containing the intersection records.
    """


    # List field names
    field_names = ListFieldNames(PE_Grid)

    print("PE_Grid attributes:", field_names, "/n")

    t_start = process_time()  # track processing time

    processing = {}  # dictionary for processing time

    PE_Grid_working = scratchDS.CreateLayer(PE_Grid.GetName(),PE_Grid.GetSpatialRef(),PE_Grid.GetGeomType())
    # add existing fields
    peDefn = PE_Grid.GetLayerDefn()
    wDefn = PE_Grid_working.GetLayerDefn()
    for i in range(peDefn.GetFieldCount()):
        wDefn.AddFieldDefn(peDefn.GetFieldDefn(i))
    # add join fields
    allFieldsIdx=set()
    for component_datasets in components_data_array:
        # Test for intersect between PE_Grid cells and data features
        for feature_class in component_datasets:
            field = ogr.FieldDefn(feature_class.GetName(),ogr.OFTInteger)
            field.SetDefault('0') # might not work with shp/gdb
            allFieldsIdx.add(wDefn.AddFieldDefn(field))


    for uc in unique_components:
        if uc not in field_names:
            print("Adding field:", uc)
            fDefn=ogr.FieldDefn(uc,ogr.OFTInteger)
            fDefn.SetDefault('0')
            allFieldsIdx.add(wDefn.AddFieldDefn(fDefn))
        else:
            print("Field exists:", uc)
            allFieldsIdx.add(wDefn.GetFieldIndex(uc))

    # copy features
    PE_Grid_working.Update(PE_Grid,PE_Grid_working)

    # print("Building Domains...",end=' ')
    # geoms, gFeats = BuildDomainFeatureGeoms(PE_Grid_working,('LD_index','UD_index','SD_index'))
    # print('Done')

    totDt=0
    featClasses = []
    for component_datasets in components_data_array:
        featClasses+=component_datasets

    domInds=BuildLookups(PE_Grid_working,('LD_index','UD_index','SD_index'))

    hitMatrix = np.zeros(shape=[len(domInds),len(featClasses)],dtype=np.uint8)

    # Iterate through features for each component, add new field with the code prefix, test for intersection with PE_Grid and features, add DA
    for counter,feature_class in enumerate(featClasses):
        fName = feature_class.GetName()
        t1 = process_time()

        #        # this variable is the component code prefix (e.g., DA_Eo_LD_CID16) at the current iteration step
        #         component = unique_components[component_datasets.index(feature_class)]

        # Create new field with same name as component code prefix and feature class
        #         arcpy.AddField_management(PE_Grid, feature_class, "SHORT")
        #         print("added field for feature_class:", feature_class)

        print(counter+1,"/",len(featClasses),' ',fName,':',sep='')
        # Find intersected Geometry, mark as hit for the joined features
        MarkIntersectingFeatures(PE_Grid_working,feature_class,domInds,counter,hitMatrix,print)
        # for feat in GetFilteredFeatures(PE_Grid_working, feature_class):
        #     feat.SetField(fName,1)

        # print processing times for each feature class
        t2 = process_time()
        dt = t2 - t1
        totDt+=dt
        processing[feature_class.GetName()] = round(dt, 2)  # update the processing time dictionary
        print("   Time:", round(dt, 2), "seconds (Avg:",round(totDt/(counter+1),2),')')

    print("Applying lookups")

    # Take intersections recorded into hit matrix, and
    # distribute flags back into features
    #
    # for each feature in working layer:
    #   for each domain:
    #     if feature has domain marked:
    #        get index for domain
    #        for each entry in hitMatrix where domain is marked:
    #           mark each layer marked as '1' in field of feature.

    #with open('hit_dbg.csv','w') as dbgFile:
        #print('Feature', 'index', 'record', sep=',', file=dbgFile)
    for pgw in range(PE_Grid_working.GetFeatureCount()):
        feat = PE_Grid_working.GetFeature(pgw)
        for f in ('LD_index','SD_index','UD_index'):
            key = feat.GetField(f)
            if key is not None and key !='0' and key!=0:
                ind = domInds[key]
                for i in range(hitMatrix.shape[1]):
                    if hitMatrix[ind,i]==1:
                        #print(featClasses[i].GetName(),f,i,sep=',',file=dbgFile)
                        feat.SetField(featClasses[i].GetName(),1)
        PE_Grid_working.SetFeature(feat)

    t_stop = process_time()
    seconds = t_stop - t_start
    printTimeStamp(seconds)

    # print processing times to csv file
    print("Generating Time Series...")
    step1_time = pd.Series(processing, name='seconds')
    if 'step1_performance' in outputs:
        step1_time.to_csv(outputs['step1_performance'], header=True)

    print("Cleaning up...")
    return PE_Grid_working

def DetermineDataForComponents(PE_Grid, unique_components):
    """Step 2 of 4: Determine DA/DS for each component; if multiple available datasets for a single component,
        DA/DS is set to 1.

    Args:
        PE_Grid (osgeo.ogr.Layer):  Layer to query.
        unique_components (list): Attributes to add to `PE_Grid`.

    Returns:
        osgeo.ogr.Layer: The same layer as `PE_Grid`.
    """


    t_start = process_time()  # track processing time

    # Update field names
    field_names = ListFieldNames(PE_Grid)

    lyrDefn = PE_Grid.GetLayerDefn()
    for uc in unique_components:
        if uc not in field_names:
            print("Adding field:", uc)
            fDefn=ogr.FieldDefn(uc,ogr.OFTInteger)
            fDefn.SetDefault('0')
            lyrDefn.AddFieldDefn(fDefn)
        else:
            print("Field exists:", uc)

    # refresh features
    for feat in PE_Grid:
        for uc in unique_components:
            if uc not in field_names:
                feat.SetField(uc,0)
        PE_Grid.SetFeature(feat)

    # print processing time
    t_stop = process_time()
    seconds = t_stop - t_start
    printTimeStamp(seconds)

    return PE_Grid


def DistribOverDomains(PE_Grid, unique_components):
    """ Step 3 of 4: Distribute DA/DS across appropriate domain areas.  Assigns presence/absence
        for a dataset within a geologic domain.

    Args:
        PE_Grid (osgeo.ogr.Layer):  Layer to query.
        unique_components (list): Attributes to add to `PE_Grid`.

    Returns:
        dict: A dictionary of DataFrames ('df_dict_LG_domains_ALL') for each component spatial type (e.g., 'LD')
          post-spatial distribution, and a master DataFrame with all components (local and domains).
    """

    t_start = process_time()  # track processing time

    # Create a list of local grid index values, then create DataFrame
    LG_index_values = FieldValues(PE_Grid, 'LG_index')
    df_index_cols = pd.DataFrame(LG_index_values, columns={'LG_index'})
    df_index_cols.set_index('LG_index',inplace=True)  # Set 'LG_index' as dataframe index
    df_dict_LG_domains_ALL = {"indicies": df_index_cols,
                              "ind_cols": pd.DataFrame()}  # This dict will contain all of the calculated DA fields

    # Add LG components to master DataFrame "df_dict_LG_domains_ALL"
    print("Adding LG_index components to master DataFrame.../n")
    LG_components = [i for i in unique_components if 'LG' in i]  # List of LG components
    LG_cols = {'LG_index': LG_index_values}  # Include LG_index for joining
    for i in LG_components:
        LG_cols[i] = FieldValues(PE_Grid, i)
    df_LG_fieldvalues = pd.DataFrame(LG_cols)
    df_LG_fieldvalues.set_index('LG_index', inplace=True)  # Set 'LG_index' as dataframe index
    df_dict_LG_domains_ALL['LG'] = df_index_cols.join(df_LG_fieldvalues)

    # Determine which domain types have available datasets for the AOI
    domainTypes_ALL = ["LD", "SD", "SA", "UD"]
    domainTypes = []
    for domainType in domainTypes_ALL:
        count = [i for i in unique_components if domainType in i]
        if len(count) > 0:
            domainTypes.append(domainType)

    # Create a dict of lists for each domain type (components with domain subtext (e.g., LD) in the name)
    domainType_components = {}

    # Distribute presence across domain for each domain type
    for domainType in domainTypes:

        print(domainType, "distribution started...")

        # Create a list of domain index values (e.g, LD1, LD2, LD3, LD4), then add to DataFrame
        domainType_index_values = FieldValues(PE_Grid, domainType + '_index')
        df_index_cols[domainType + '_index'] = domainType_index_values
        df_index_cols.fillna(value={domainType + '_index': 0}, inplace=True)
        print("created list of domain index values")

        # Update dict of lists for each domain type
        domainType_components[domainType] = [i for i in unique_components if domainType in i]

        # Create DataFrame with values for records for each domainType
        domain_cols = {'LG_index': LG_index_values}  # Include LG_index for joining
        for i in domainType_components[domainType]:
            domain_cols[i] = FieldValues(PE_Grid, i)
        df_domainType_fieldvalues = pd.DataFrame(domain_cols)
        df_domainType_fieldvalues.set_index('LG_index', inplace=True)  # Set 'LG_index' as dataframe index
        print("created dataframe with values for records")

        # Join into a new DataFrame the domainType_index and domainType_components/values columns
        df_domainType_joined = df_index_cols.join(df_domainType_fieldvalues, sort=False)

        # Group by unique domainType_index values
        df_domainType_grouped = df_domainType_joined.groupby([domainType + '_index'])

        # Determine max of DA for each domainType_index group, return in "DA_...domainType..._distributed" column
        df_domainType_max = df_domainType_grouped.max()
        for i in domainType_components[domainType]:
            df_domainType_max.rename(columns={i: (i + "_distributed")}, inplace=True)
        # df_domainType_max.drop(['LG_index'], axis=1, inplace=True)  # LG_index is erroneously overwritten without this line

        # Join index and DA_max columns in a new DataFrame
        #     df_domainType_export = df_index_cols.merge(df_domainType_max, on = domainType + '_index')
        df_domainType_export = df_index_cols.join(df_domainType_max, on=domainType + '_index')
        #     df_domainType_all = df_domainType_joined.merge(df_domainType_max, on = domainType + '_index')

        # Combine all domain types into a list/dict of DataFrames
        #     df_domainALL = df_domainType_joined.join(df_domainType_export, on='LG_index', lsuffix='', rsuffix='_from'+domainType)
        df_dict_LG_domains_ALL[domainType] = df_domainType_export.copy()

        print(domainType, "distribution finished./n")
        df_dict_LG_domains_ALL['ind_cols'][domainType+'_index']=df_domainType_export[domainType+'_index'].copy()
        df_index_cols.drop( columns=[domainType + '_index'],inplace=True)

    print("All domain types distributed./n")

    # Compile a master dataframe in 'df_dict_LG_domains_ALL' for all spatial types (local and domains)
    spatialTypes = domainTypes.copy()  # Create a list for all spatial types
    spatialTypes.insert(0, 'LG')  # Include 'LG_index' for joining
    df_dict_LG_domains_ALL['compiled'] = df_dict_LG_domains_ALL['indicies'].copy()  # This is the master dataframe
    for i in spatialTypes:
        df_dict_LG_domains_ALL['compiled'] = df_dict_LG_domains_ALL['compiled'].join(df_dict_LG_domains_ALL[i], lsuffix='',
                                                                                     rsuffix='_from' + i)

    # Create a copy of LG component columns (named "..._local") to serve as QA/QC record
    for i in LG_components:
        df_dict_LG_domains_ALL['LG'][i + "_local"] = df_dict_LG_domains_ALL['LG'][i].copy()

    # print processing time
    t_stop = process_time()
    seconds = t_stop - t_start
    printTimeStamp(seconds)

    return df_dict_LG_domains_ALL

def CalcSum(df_dict_LG_domains_ALL, inFeatures,  unique_components,prefix,outputs):
    """Step 4 of 4: Calculate sum for each REE emplacement type (explicit tally of components;
        not implicit score).

    Args:
        df_dict_LG_domains_ALL (dict): dictionary of DataFrames for each component spatial type (e.g., 'LD')
          post-spatial distribution, and a master DataFrame with all components (local and domains).
        inFeatures (osgeo.ogr.Layer): Layer containing features with data for analysis.
        prefix (str): Prefix used to distinguish relevant fields; typically _DA_ or _DS_.
        outputs (REE_Workspace): Outputs object.

    """

    p = DataPrefix(prefix)
    ### THIS CODE WILL BE IN FINAL SCRIPT ###

    ### TESTED AND SUCCESSFUL ###

    t_start = process_time()  # track processing time

    # Comprehensive list of all possible components, including those deemed 'not testable' and
    # 'not evalutated (duplicate)'.  This list current as of 2020-03-24.  Values copied from Google Sheet
    # "REE Enrichment Tree Related Data - Google Sheets 'Component_Codes_asof_2020-03-24'!Y2:FR2"
    componentsALL = [p['Fl_LD_CID01'], p['Fl_LD_CID02'], p['Fl_LD_CID03'], p['Fl_LD_CID04'], p['Fl_LD_CID05'],
                     p['Fl_LD_CID06'], p['Fl_LD_CID07'], p['Fl_LD_CID08'], p['Fl_LD_CID09'], p['Eo_LD_CID10'],
                     p['Fl_NE_CID11'], p['Fl_NE_CID12'], p['Fl_NE_CID13'], p['Eo_LG_CID14'], p['Eo_LG_CID15'],
                     p['Eo_LD_CID16'], p['Fl_LD_CID17'], p['Fl_LG_CID18'], p['Fl_NT_CID19'], p['Fl_LD_CID19'],
                     p['Eo_NT_CID20'], p['Fl_NT_CID20'], p['Eo_NT_CID21'], p['Eo_LD_CID21'], p['Eo_NE_CID21'],
                     p['Eo_NT_CID22'], p['Eo_NT_CID23'], p['MA_LD_CID24'], p['MA_LD_CID25'], p['MA_LD_CID26'],
                     p['MA_LD_CID27'], p['MA_LD_CID28'], p['MA_LD_CID29'], p['MA_LD_CID30'], p['MA_LD_CID31'],
                     p['MA_LD_CID32'], p['MA_NE_CID33'], p['MA_NE_CID34'], p['MA_NE_CID35'], p['MA_NE_CID36'],
                     p['MA_UD_CID37'], p['MA_UD_CID38'], p['MA_UD_CID39'], p['MA_UD_CID40'], p['MA_UD_CID41'],
                     p['MA_LG_CID42'], p['MA_UD_CID43'], p['MA_NT_CID44'], p['HP_UD_CID45'], p['HP_LG_CID46'],
                     p['MA_LG_CID47'], p['MA_LG_CID48'], p['MA_LG_CID49'], p['MA_LG_CID50'], p['MA_NT_CID51'],
                     p['MA_LG_CID52'], p['MA_NT_CID53'], p['MA_LG_CID54'], p['MP_NT_CID55'], p['MP_LG_CID56'],
                     p['MP_LG_CID57'], p['MP_NT_CID58'], p['MA_NT_CID59'], p['Fl_LD_CID10'], p['Fl_NT_CID21'],
                     p['Fl_LD_CID21'], p['Fl_NE_CID21'], p['Fl_NT_CID22'], p['Fl_NT_CID23'], p['MP_LD_CID24'],
                     p['MP_LD_CID25'], p['MP_LD_CID26'], p['MP_LD_CID27'], p['MP_LD_CID28'], p['MP_LD_CID29'],
                     p['MP_LD_CID30'], p['MP_LD_CID31'], p['MP_LD_CID32'], p['MP_NE_CID33'], p['MP_NE_CID34'],
                     p['MP_NE_CID35'], p['MP_NE_CID36'], p['MP_UD_CID37'], p['MP_UD_CID38'], p['MP_UD_CID39'],
                     p['MP_UD_CID40'], p['MP_UD_CID41'], p['MP_LG_CID42'], p['MP_UD_CID43'], p['MP_NT_CID44'],
                     p['HA_LG_CID47'], p['HA_LG_CID48'], p['HA_LG_CID49'], p['MP_LG_CID50'], p['MP_NT_CID51'],
                     p['MP_LG_CID52'], p['MP_NT_CID53'], p['HA_LG_CID54'], p['HP_NT_CID55'], p['HP_LG_CID56'],
                     p['HP_LG_CID57'], p['HP_NT_CID58'], p['HA_NT_CID59'], p['HA_LD_CID24'], p['HA_LD_CID25'],
                     p['HA_LD_CID26'], p['HA_LD_CID27'], p['HA_LD_CID28'], p['HA_LD_CID29'], p['HA_LD_CID30'],
                     p['HA_LD_CID31'], p['HA_LD_CID32'], p['HA_NE_CID33'], p['HA_NE_CID34'], p['HA_NE_CID35'],
                     p['HA_NE_CID36'], p['HA_UD_CID37'], p['HA_UD_CID38'], p['HA_UD_CID39'], p['HA_UD_CID40'],
                     p['HA_UD_CID41'], p['HA_LG_CID42'], p['HA_UD_CID43'], p['HA_UD_CID45'], p['HA_LG_CID50'],
                     p['HA_NT_CID51'], p['HA_LG_CID52'], p['HA_NT_CID53'], p['HP_LD_CID24'], p['HP_LD_CID25'],
                     p['HP_LD_CID26'], p['HP_LD_CID27'], p['HP_LD_CID28'], p['HP_LD_CID29'], p['HP_LD_CID30'],
                     p['HP_LD_CID31'], p['HP_LD_CID32'], p['HP_NE_CID33'], p['HP_NE_CID34'], p['HP_NE_CID35'],
                     p['HP_NE_CID36'], p['HP_UD_CID37'], p['HP_UD_CID38'], p['HP_UD_CID39'], p['HP_UD_CID40'],
                     p['HP_UD_CID41'], p['HP_LG_CID42'], p['HP_UD_CID43'], p['HP_LG_CID50'], p['HP_NT_CID51']]

    # Create dict of unique_components for each emplacement mechanism with data in the geodatabase
    mechanismTypes = ['Eo', 'Fl', 'HA', 'HP', 'MA', 'MP']
    mechanismComponents = {}
    for mechanism in mechanismTypes:
        mechanismComponents[mechanism] = [i for i in unique_components if mechanism in i]

    # Create dict of all possible components (including those that are untestable) for each emplacement mechanism
    mechanismComponentsALL = {}
    for mechanism in mechanismTypes:
        mechanismComponentsALL[mechanism] = sorted([i for i in componentsALL if mechanism in i])

    # # DEVELOPMENT ONLY: Create a list of components that are 'not testable' or 'not evaluated', set to 'False'
    # NotTestable = []
    # for k in mechanismComponentsALL.keys():
    #     I = [x for x in mechanismComponentsALL[k] if 'N' in x]
    #     for i in I:
    #         NotTestable.append(i)
    # for i in NotTestable:
    #     df_PE_calc[i] = False

    # Create a copy of the DataFrame that contains post-processed tallies.
    df_keys = df_dict_LG_domains_ALL.keys()
    df_dict_PostProcessed = {}
    for key in df_keys:
        df_dict_PostProcessed[key] = df_dict_LG_domains_ALL[key].copy()

    # Rename fields to simplified component names (e.g., remove "_distributed", etc.)
    sel = df_dict_PostProcessed['compiled'].columns  # list of fields
    rename_fields = [i for i in sel if "_distributed" in i]  # list of fields to be renamed
    for i in rename_fields:
        df_dict_PostProcessed['compiled'].rename(columns={i: (i[:14])}, inplace=True)

        # Create an 'empty' dataframe that has columns for all components and row values = 'False'
    df_PE_empty = df_dict_LG_domains_ALL['indicies'].copy()
    for component in componentsALL:
        df_PE_empty[component] = False

    # Create new DataFrame (df_PE_calc), update values from PostProcessed DataFrame
    df_PE_calc = df_PE_empty.copy()
    df_PE_calc.update(df_dict_PostProcessed['compiled'])

    ############################################################################################################

    ### Generic assignment for all cells
    df_PE_calc[p['Eo_NT_CID20']] = True  # Accumulation of peat
    df_PE_calc[p['Fl_NT_CID20']] = True  # Accumulation of peat

    df_PE_calc[p['Fl_NT_CID22']] = True  # Burial of peat

    df_PE_calc[p['Fl_NT_CID23']] = True  # Conversion of peat to coal

    df_PE_calc[p['HA_LG_CID52']] = True  # Coal and/or related strata
    df_PE_calc[p['HP_LG_CID52']] = True  # Coal and/or related strata
    df_PE_calc[p['MA_LG_CID52']] = True  # Coal and/or related strata
    df_PE_calc[p['MP_LG_CID52']] = True  # Coal and/or related strata

    ### Powder River Basin assignment for all cells (PRB)
    df_PE_calc[p['Eo_LG_CID14']] = True  # Mire downwind of volcanism (this is true for PRB)
    df_PE_calc[p['Fl_LD_CID17']] = True  # Mire in same paleo-drainage basin
    df_PE_calc[p['Fl_LG_CID18']] = True  # Mire downstream of REE source

    ############################################################################################################

    ### Eo relevant components.  Not testable: CID15, CID21


    ### Fl relevant components.  Not testable: CID17, CID18, CID19, CID21
    df_PE_calc[p['Fl_NE_CID11']] = df_PE_calc[[p['Fl_LD_CID01'], p['Fl_LD_CID02'], p['Fl_LD_CID03'], p['Fl_LD_CID04'],
                                               p['Fl_LD_CID05'], p['Fl_LD_CID06']]].max(axis=1)  # Bedrock REE deposit
    df_PE_calc[p['Fl_NE_CID12']] = df_PE_calc[[p['Fl_LD_CID07'], p['Fl_LD_CID08'], p['Fl_LD_CID09']]].max(
        axis=1)  # Sed REE deposit
    df_PE_calc[p['Fl_NE_CID13']] = df_PE_calc[[p['Fl_LD_CID10'], p['Fl_NE_CID11'], p['Fl_NE_CID12']]].max(
        axis=1)  # REE source

    ### HA relevant components.  Not testable: CID47, CID48, CID49, CID51, CID53, CID59
    df_PE_calc[p['HA_NE_CID33']] = df_PE_calc[[p['HA_UD_CID37'], p['HA_UD_CID38'], p['HA_UD_CID39'],
                                               p['HA_UD_CID40'], p['HA_UD_CID41']]].max(axis=1)  # Alkaline volcanic ash
    df_PE_calc[p['HA_NE_CID34']] = df_PE_calc[[p['HA_LD_CID24'], p['HA_LD_CID25'], p['HA_LD_CID26'],
                                               p['HA_LD_CID27'], p['HA_LD_CID28'], p['HA_LD_CID29']]].max(
        axis=1)  # Bedrock REE deposit
    df_PE_calc[p['HA_NE_CID35']] = df_PE_calc[[p['HA_LD_CID30'], p['HA_LD_CID31'], p['HA_LD_CID32']]].max(
        axis=1)  # Sed REE deposit
    df_PE_calc[p['HA_NE_CID36']] = df_PE_calc[[p['HA_NE_CID33'], p['HA_NE_CID34'], p['HA_NE_CID35']]].max(
        axis=1)  # REE source
    df_PE_calc[p['HA_NE_42_43']] = df_PE_calc[[p['HA_LG_CID42'], p['HA_UD_CID43']]].max(axis=1)  # Conduit for fluid flow

    ### HP relevant components.  Not testable: CID47, CID48, CID49, CID51, CID53, CID55, CID58
    df_PE_calc[p['HP_NE_CID33']] = df_PE_calc[[p['HP_UD_CID37'], p['HP_UD_CID38'], p['HP_UD_CID39'],
                                               p['HP_UD_CID40'], p['HP_UD_CID41']]].max(axis=1)  # Alkaline volcanic ash
    df_PE_calc[p['HP_NE_CID34']] = df_PE_calc[[p['HP_LD_CID24'], p['HP_LD_CID25'], p['HP_LD_CID26'],
                                               p['HP_LD_CID27'], p['HP_LD_CID28'], p['HP_LD_CID29']]].max(
        axis=1)  # Bedrock REE deposit
    df_PE_calc[p['HP_NE_CID35']] = df_PE_calc[[p['HP_LD_CID30'], p['HP_LD_CID31'], p['HP_LD_CID32']]].max(
        axis=1)  # Sed REE deposit
    df_PE_calc[p['HP_NE_CID36']] = df_PE_calc[[p['HP_NE_CID33'], p['HP_NE_CID34'], p['HP_NE_CID35']]].max(
        axis=1)  # REE source
    df_PE_calc[p['HP_NE_42_43']] = df_PE_calc[[p['HP_LG_CID42'], p['HP_UD_CID43']]].max(axis=1)  # Conduit for fluid flow
    df_PE_calc[p['HP_NE_57_46']] = df_PE_calc[[p['HP_LG_CID57'], p['HP_LG_CID46']]].max(axis=1)  # Dissolve phosphorus

    ### MA relevant components.  Not testable:  CID44, CID47, CID48, CID49, CID51, CID53, CID59
    df_PE_calc[p['MA_NE_CID33']] = df_PE_calc[[p['MA_UD_CID37'], p['MA_UD_CID38'], p['MA_UD_CID39'],
                                               p['MA_UD_CID40'], p['MA_UD_CID41']]].max(axis=1)  # Alkaline volcanic ash
    df_PE_calc[p['MA_NE_CID34']] = df_PE_calc[[p['MA_LD_CID24'], p['MA_LD_CID25'], p['MA_LD_CID26'],
                                               p['MA_LD_CID27'], p['MA_LD_CID28'], p['MA_LD_CID29']]].max(
        axis=1)  # Bedrock REE deposit
    df_PE_calc[p['MA_NE_CID35']] = df_PE_calc[[p['MA_LD_CID30'], p['MA_LD_CID31'], p['MA_LD_CID32']]].max(
        axis=1)  # Sed REE deposit
    df_PE_calc[p['MA_NE_CID36']] = df_PE_calc[[p['MA_NE_CID33'], p['MA_NE_CID34'], p['MA_NE_CID35']]].max(
        axis=1)  # REE source
    df_PE_calc[p['MA_NE_42_43']] = df_PE_calc[[p['MA_LG_CID42'], p['MA_UD_CID43']]].max(axis=1)  # Conduit for fluid flow

    ### MP relevant components.  Not testable: CID47, CID48, CID49, CID51, CID53, CID55, CID58
    df_PE_calc[p['MP_NE_CID33']] = df_PE_calc[[p['MP_UD_CID37'], p['MP_UD_CID38'], p['MP_UD_CID39'],
                                               p['MP_UD_CID40'], p['MP_UD_CID41']]].max(axis=1)  # Alkaline volcanic ash
    df_PE_calc[p['MP_NE_CID34']] = df_PE_calc[[p['MP_LD_CID24'], p['MP_LD_CID25'], p['MP_LD_CID26'],
                                               p['MP_LD_CID27'], p['MP_LD_CID28'], p['MP_LD_CID29']]].max(
        axis=1)  # Bedrock REE deposit
    df_PE_calc[p['MP_NE_CID35']] = df_PE_calc[[p['MP_LD_CID30'], p['MP_LD_CID31'], p['MP_LD_CID32']]].max(
        axis=1)  # Sed REE deposit
    df_PE_calc[p['MP_NE_CID36']] = df_PE_calc[[p['MP_NE_CID33'], p['MP_NE_CID34'], p['MP_NE_CID35']]].max(
        axis=1)  # REE source
    df_PE_calc[p['MP_NE_42_43']] = df_PE_calc[[p['MP_LG_CID42'], p['MP_UD_CID43']]].max(axis=1)  # Conduit for fluid flow

    ############################################################################################################
    # DR components (NOTE: this is NOT the entire list of DR components; only those that are considered testable)
    DR_Eo = [p['Eo_LD_CID10'], p['Eo_LG_CID14'], p['Eo_LD_CID16'], p['Fl_NT_CID22'], p['Fl_NT_CID23']]
    DR_Fl = [p['Fl_NE_CID13'], p['Fl_NT_CID20'], p['Fl_NT_CID22'], p['Fl_NT_CID23']]
    DR_HA = [p['HA_NE_42_43'], p['HA_LG_CID52'], p['HA_NE_CID36'], p['HA_UD_CID45'], p['HA_LG_CID50'], p['HA_LG_CID54']]
    DR_HP = [p['HP_NE_42_43'], p['HP_LG_CID52'], p['HP_NE_CID36'], p['HP_UD_CID45'], p['HP_LG_CID50'], p['HP_LG_CID56'],
             p['HP_NE_57_46']]
    DR_MA = [p['MA_NE_42_43'], p['MA_LG_CID52'], p['MA_NE_CID36'], p['MA_LG_CID50'], p['MA_LG_CID54']]
    DR_MP = [p['MP_NE_42_43'], p['MP_LG_CID52'], p['MP_NE_CID36'], p['MP_LG_CID50'], p['MP_LG_CID56']]

    DR_Types = [DR_Eo, DR_Fl, DR_HA, DR_HP, DR_MA, DR_MP]  # A list of required components (DR) for each mechanism type
    ############################################################################################################


    # Add sum fields to dataframe
    df_PE_calc['Eo_sum'] = df_PE_calc[DR_Eo].sum(axis=1)
    df_PE_calc['Fl_sum'] = df_PE_calc[DR_Fl].sum(axis=1)
    df_PE_calc['HA_sum'] = df_PE_calc[DR_HA].sum(axis=1)
    df_PE_calc['HP_sum'] = df_PE_calc[DR_HP].sum(axis=1)
    df_PE_calc['MA_sum'] = df_PE_calc[DR_MA].sum(axis=1)
    df_PE_calc['MP_sum'] = df_PE_calc[DR_MP].sum(axis=1)

    # Calculate DA_sum/DR
    sumDR_cols = []  # To be columns of DA_sum / DR
    for i in range(len(DR_Types)):
        col = prefix + '_' + DR_Types[i][0][3:5] + '_sum_DR'  # Assemble column heading (e.g., 'DA_Eo_sum_DR')
        df_PE_calc[col] = df_PE_calc[DR_Types[i][0][3:5] + '_sum'] / len(
            DR_Types[i])  # Divide mechanism sum by DR (e.g., Eo_sum / DR_Eo)
        sumDR_cols.append(col)  # Append column name to this list

    joinField = 'LG_index'
    fieldList = list(sumDR_cols)
    print(f'Joining {prefix} Data frames to',inFeatures.GetName())
    OgrPandasJoin(inFeatures,joinField,df_PE_calc,copyFields=fieldList)

    if 'pe_calc_dataframe' in outputs:
        pd.concat([df_dict_LG_domains_ALL['ind_cols'],df_PE_calc],axis=1).to_csv(outputs['pe_calc_dataframe'], index=True)

    # Print processing time
    t_stop = process_time()
    seconds = t_stop - t_start
    printTimeStamp(seconds)

def CollectIndexRasters(inWorkspace):

    inpaths = {k: inWorkspace[f'{k}_inds'] for k in ('ld','lg','sd','ud')}
    return RasterGroup(**inpaths)

def RasterizeComponents(src_rasters,gdbDS,component_data,cache_dir=None):

    src_gtf = src_rasters.geoTransform
    src_data={'xSize':src_rasters.RasterXSize,
              'ySize':src_rasters.RasterYSize,
              'geotrans':src_rasters.geoTransform,
              'srs':src_rasters.spatialRef,
              'nodata':0,
              'gdType':gdal.GDT_Byte,
              'drvrName':'mem',
              'prefix':'',
              'suffix':'',
              }

    if cache_dir is not None:
        src_data['drvrName'] = 'GTiff'
        src_data['prefix'] = cache_dir
        src_data['suffix'] = '.tif'

    outRasters=RasterGroup()
    for id,fc_list in component_data.items():
        print(f'Rasterizing {id}...')
        rstr = Rasterize(id, fc_list,gdbDS, **src_data)
        outRasters[id] = rstr

    return outRasters

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

def GenDomainDistances(src_rasters,cache_dir=None,mask=None):

    src_data = {'gdType': gdal.GDT_Float32,
                'drvrName': 'mem',
                'prefix': '',
                'suffix': '',
                'mask': mask,
                }

    if cache_dir is not None:
        src_data['drvrName'] = 'GTiff'
        src_data['prefix'] = cache_dir
        src_data['suffix'] = '.tif'

    outRasters = RasterGroup()
    hitmaps={}

    # scratch buffer
    drvr = gdal.GetDriverByName("mem")
    scratchDS = drvr.Create("scratch",src_rasters.RasterXSize,src_rasters.RasterYSize,1,gdal.GDT_Int32)
    scratchDS.SetGeoTransform(src_rasters.geoTransform)
    scratchDS.SetSpatialRef(src_rasters.spatialRef)
    scratchBand = scratchDS.GetRasterBand(1)
    scratchBand.SetNoDataValue(0)

    for k in ('ld','ud','sd'):

        print(f'Distancing for {k} domains...')
        srcBand=src_rasters[k].GetRasterBand(1)
        _,maxVal=srcBand.ComputeRasterMinMax(1)
        maxVal=int(maxVal)
        ndVal = srcBand.GetNoDataValue()
        hitList = [False]*(maxVal+1)
        # separate values out for individual domains
        subBuffs=np.zeros([maxVal+1,src_rasters.RasterYSize,src_rasters.RasterXSize],dtype=np.uint8)
        srcBuff = srcBand.ReadAsArray()
        for i in range(src_rasters.RasterYSize):
            for j in range(src_rasters.RasterXSize):
                px = srcBuff[i,j]
                if px != ndVal:
                    subBuffs[px,i,j] = 1
                    hitList[px]=True

        # cache hitmaps
        hitmaps[k] = subBuffs

        # build distances for each domain
        for i in range(subBuffs.shape[0]):
            if not hitList[i]:
                continue
            scratchBand.WriteArray(subBuffs[i])
            id = f'{k}_{i}'
            rstr = RasterDistance(id,scratchDS, **src_data)
            outRasters[id] = rstr

    return outRasters,hitmaps

def FindDomainComponentRasters(domDistRasters,hitMaps,testRasters,cache_dir=None):

    comboRasters = RasterGroup()
    fixedArgs = {
                'drvrName': 'mem',
                'prefix': '',
                'suffix': '',
                'comboRasters':comboRasters,
                'domDistRasters':domDistRasters,
                }

    if cache_dir is not None:
        fixedArgs['drvrName'] = 'GTiff'
        fixedArgs['prefix'] = cache_dir
        fixedArgs['suffix'] = '_domain_distance.tif'

    for id,srcDS in testRasters.items():
        domKey = id[6:8].lower()
        if domKey not in hitMaps:
            continue
        testBand = srcDS.GetRasterBand(1)
        testBuff = testBand.ReadAsArray()
        nd = testBand.GetNoDataValue()
        hm = hitMaps[domKey]
        found= set() # {x for x in testBand.ReadAsArray().ravel() if x!=nd}
        for i in range(domDistRasters.RasterYSize):
            for j in range(domDistRasters.RasterXSize):
                v = testBuff[i,j]
                if v!=nd and v!=0:
                    for h in range(hm.shape[0]):
                        if hm[h,i,j]!=0:
                            found.add(h)
        CombineDomDistRasters(found,domKey,id,**fixedArgs)
    return comboRasters


def CombineDomDistRasters(found,domKey,compName,domDistRasters,comboRasters,prefix='',suffix='',drvrName='mem'):

    path = os.path.join(prefix,compName) + suffix
    outND = np.inf
    outBuff = np.full([domDistRasters.RasterYSize,domDistRasters.RasterXSize],outND,dtype=np.float32)
    for index in found:
        ds = domDistRasters[f'{domKey}_{index}']
        b = ds.GetRasterBand(1)
        inND = b.GetNoDataValue()
        readBuff = b.ReadAsArray()
        for i in range(ds.RasterYSize):
            for j in range(ds.RasterXSize):
                if readBuff[i,j]==inND:
                    continue
                if outBuff[i,j]==outND or outBuff[i,j]>readBuff[i,j]:
                    outBuff[i, j] = readBuff[i, j]

    drvr = gdal.GetDriverByName(drvrName)
    print("Combine: writing "+path)
    outDS = drvr.Create(path, domDistRasters.RasterXSize, domDistRasters.RasterYSize, 1, gdal.GDT_Float32)
    outDS.SetGeoTransform(domDistRasters.geoTransform)
    outDS.SetSpatialRef(domDistRasters.spatialRef)
    outBand = outDS.GetRasterBand(1)
    outBand.SetNoDataValue(outND)
    outBand.WriteArray(outBuff)
    comboRasters.add(compName,outDS)


def NormMultRasters(implicits,explicits,cache_dir=None):

    multRasters = RasterGroup()

    kwargs = {'geotrans':implicits.geoTransform,
              'spatRef': implicits.spatialRef,
              'drvrName':'mem'
              }

    prefix=''
    suffix=''
    if cache_dir is not None:
        kwargs['drvrName'] = 'GTiff'
        prefix = cache_dir
        suffix = '_norm_product.tif'

    for k in implicits.rasterNames:
        imp = implicits[k]
        exp = explicits[k]

        normImp,impND=normalizeRaster(imp)
        normExp,expND=normalizeRaster(exp)

        id = os.path.join(prefix,k)+suffix
        multRasters[k]=MultBandData(normImp,normExp,id,impND,expND,**kwargs)

    return multRasters

def RunPEScoreCalc(gdbPath, targetData, inWorkspace, outWorkspace, rasters_only=False,postProg=None):


    t_allStart = process_time()
    gdbDS=gdal.OpenEx(gdbPath,gdal.OF_VECTOR)

    rasterDir = outWorkspace.get('raster_dir',None)
    indexRasters = CollectIndexRasters(inWorkspace)
    indexMask = indexRasters.generateNoDataMask()
    print('Finding components...')
    components_data_dict = FindUniqueComponents(gdbDS,targetData)
    testRasters = RasterizeComponents(indexRasters,gdbDS,components_data_dict,rasterDir)
    print('Done')
    print('Calculating distances')
    domDistRasters,hitMaps = GenDomainDistances(indexRasters,rasterDir,indexMask)
    distanceRasters = GetDSDistances(testRasters,rasterDir,indexMask)
    combineRaster = FindDomainComponentRasters(domDistRasters,hitMaps,testRasters,rasterDir)

    multRasters=NormMultRasters(combineRaster, distanceRasters, rasterDir)
    print('Done')
    if 'raster_dir' in outWorkspace and rasters_only:
        print('Exit on rasters specified; exiting')
        exit(0)

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

    # TODO: implement DA/DR
    #   --> Convert to pandas df, use existing code
    # TODO: update everything below this line for Raster work
    print(testRasters.generateHitMap().shape)
    drvr = gdal.GetDriverByName('memory')
    scratchDS=drvr.Create('scratch',0,0,0,gdal.OF_VECTOR)

    workingLyr=FeaturesPresent(PE_Grid, unique_components, components_data_array, scratchDS, outWorkspace)
    print("/nStep 1 complete")
    WriteIfRequested(workingLyr,outWorkspace,'step1_grid',drvrName='sqlite',)

    # begin dbg inject
    # import wingoDbg as dbg
    #
    # dbgDS = gdal.OpenEx(r"C:/Users/wingop/dev_stuff/Python_workspace/REE_PE_Score/testData/SumTroubleshoot/step1.sqlite",gdal.OF_VECTOR)
    # workingLyr = dbgDS.GetLayer(0)
    # end dbg inject

    # workingLyr=DetermineDAForComponents(workingLyr,unique_components)
    # print("/nStep 2 complete")
    print("/nStep 2 Omitted (not necessary)")

    df_dict_LG_domains_ALL=DistribOverDomains(workingLyr, unique_components)
    print("/nStep 3 complete")
    if 'step3_dataframe' in outWorkspace:
        df_dict_LG_domains_ALL['compiled'].to_csv(outWorkspace['step3_dataframe'],
                                                                             index=True)

        # pd.concat([pd.DataFrame({'indicies':df_dict_LG_domains_ALL['indicies']}),
         #            df_dict_LG_domains_ALL['LG'],df_dict_LG_domains_ALL['LD'],
         #            df_dict_LG_domains_ALL['UD'],'compiled'],axis=1).to_csv(args.output_dir['step3_dataframe'],index=True)


    CalcSum(df_dict_LG_domains_ALL, workingLyr, unique_components,targetData,outWorkspace)
    print("/nStep 4 complete")

    # scratchDS.FlushCache()
    WriteIfRequested(workingLyr,outWorkspace,'final_grid',drvrName='sqlite')

    print("Done.")

    t_allStop = process_time()
    seconds = t_allStop - t_allStart
    print('Total time:',end=' ')
    printTimeStamp(seconds)
