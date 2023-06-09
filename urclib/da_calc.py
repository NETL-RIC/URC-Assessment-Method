# This file is part of URC Assessment Method.
#
# URC Assessment Method is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# URC Assessment Method is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with URC Assessment Method. If not, see
# <https://www.gnu.org/licenses/>.

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
    # 'not evalutated (duplicate)'.  
    components_all = {'DA_Eo_LD_CID10', 'DA_Eo_LD_CID16', 'DA_Eo_LD_CID21', 'DA_Eo_LG_CID14', 'DA_Eo_LG_CID15',
                      'DA_Eo_NE_CID21', 'DA_Eo_NT_CID20', 'DA_Eo_NT_CID21', 'DA_Eo_NT_CID22', 'DA_Eo_NT_CID23',
                      'DA_Fl_LD_CID01', 'DA_Fl_LD_CID02', 'DA_Fl_LD_CID03', 'DA_Fl_LD_CID04', 'DA_Fl_LD_CID05',
                      'DA_Fl_LD_CID06', 'DA_Fl_LD_CID07', 'DA_Fl_LD_CID08', 'DA_Fl_LD_CID09', 'DA_Fl_LD_CID10',
                      'DA_Fl_LD_CID17', 'DA_Fl_LD_CID19', 'DA_Fl_LD_CID21', 'DA_Fl_NT_CID18', 'DA_Fl_NE_CID11',
                      'DA_Fl_NE_CID12', 'DA_Fl_NE_CID13', 'DA_Fl_NE_CID21', 'DA_Fl_NT_CID19', 'DA_Fl_NT_CID20',
                      'DA_Fl_NT_CID21', 'DA_Fl_NT_CID22', 'DA_Fl_NT_CID23', 'DA_HA_LD_CID24', 'DA_HA_LD_CID25',
                      'DA_HA_LD_CID26', 'DA_HA_LD_CID27', 'DA_HA_LD_CID28', 'DA_HA_LD_CID29', 'DA_HA_LD_CID30',
                      'DA_HA_LD_CID31', 'DA_HA_LD_CID32', 'DA_HA_LG_CID42', 'DA_HA_LG_CID47', 'DA_HA_LG_CID48',
                      'DA_HA_LG_CID49', 'DA_HA_LG_CID50', 'DA_HA_LG_CID52', 'DA_HA_LG_CID54', 'DA_HA_NE_CID33',
                      'DA_HA_NE_CID34', 'DA_HA_NE_CID35', 'DA_HA_NE_CID36', 'DA_HA_NE_CID45', 'DA_HA_NT_CID53',
                      'DA_HA_NT_CID51', 'DA_HA_NT_CID59', 'DA_HA_UD_CID37', 'DA_HA_UD_CID38', 'DA_HA_UD_CID39',
                      'DA_HA_UD_CID40', 'DA_HA_UD_CID41', 'DA_HA_UD_CID43', 'DA_HA_UD_CID45', 'DA_HP_LD_CID24',
                      'DA_HP_LD_CID25', 'DA_HP_LD_CID26', 'DA_HP_LD_CID27', 'DA_HP_LD_CID28', 'DA_HP_LD_CID29',
                      'DA_HP_LD_CID30', 'DA_HP_LD_CID31', 'DA_HP_LD_CID32', 'DA_HP_LG_CID42', 'DA_HP_LG_CID46',
                      'DA_HP_LG_CID47', 'DA_HP_LG_CID48', 'DA_HP_LG_CID49', 'DA_HP_LG_CID50', 'DA_HP_LG_CID52',
                      'DA_HP_LG_CID56', 'DA_HP_LG_CID57', 'DA_HP_NE_CID33', 'DA_HP_NE_CID34', 'DA_HP_NE_CID35',
                      'DA_HP_NE_CID36', 'DA_HP_NT_CID53', 'DA_HP_NT_CID51', 'DA_HP_NT_CID55',
                      'DA_HP_NT_CID58', 'DA_HP_UD_CID37', 'DA_HP_UD_CID38', 'DA_HP_UD_CID39', 'DA_HP_UD_CID40',
                      'DA_HP_UD_CID41', 'DA_HP_UD_CID43', 'DA_HP_UD_CID45', 'DA_MA_LD_CID24', 'DA_MA_LD_CID25',
                      'DA_MA_LD_CID26', 'DA_MA_LD_CID27', 'DA_MA_LD_CID28', 'DA_MA_LD_CID29', 'DA_MA_LD_CID30',
                      'DA_MA_LD_CID31', 'DA_MA_LD_CID32', 'DA_MA_LG_CID42', 'DA_MA_LG_CID48', 'DA_MA_LG_CID49',
                      'DA_MA_LG_CID50', 'DA_MA_LG_CID52', 'DA_MA_LG_CID54', 'DA_MA_NE_CID33', 'DA_MA_NE_CID34',
                      'DA_MA_NE_CID35', 'DA_MA_NE_CID36', 'DA_MA_NT_CID44', 'DA_MA_NT_CID51', 'DA_MA_NT_CID53',
                      'DA_MA_NT_CID59', 'DA_MA_UD_CID37', 'DA_MA_UD_CID38', 'DA_MA_UD_CID39', 'DA_MA_UD_CID40',
                      'DA_MA_UD_CID41', 'DA_MA_UD_CID43', 'DA_MP_LD_CID24', 'DA_MP_LD_CID25', 'DA_MP_LD_CID26',
                      'DA_MP_LD_CID27', 'DA_MP_LD_CID28', 'DA_MP_LD_CID29', 'DA_MP_LD_CID30', 'DA_MP_LD_CID31',
                      'DA_MP_LD_CID32', 'DA_MP_LG_CID42', 'DA_MP_LG_CID48', 'DA_MP_LG_CID49', 'DA_MP_LG_CID50',
                      'DA_MP_LG_CID52', 'DA_MP_LG_CID56', 'DA_MP_LG_CID57', 'DA_MP_NE_CID33', 'DA_MP_NE_CID34',
                      'DA_MP_NE_CID35', 'DA_MP_NE_CID36', 'DA_MP_NT_CID44', 'DA_MP_NT_CID51', 'DA_MP_NT_CID53',
                      'DA_MP_NT_CID55', 'DA_MP_NT_CID58', 'DA_MP_UD_CID37', 'DA_MP_UD_CID38', 'DA_MP_UD_CID39',
                      'DA_MP_UD_CID40', 'DA_MP_UD_CID41', 'DA_MP_UD_CID43'}

    # create empty frame with all columns to capture any missing columns
    df_pe_calc = pd.DataFrame(data=df_hits, columns=['LG_index']+list(components_all))
    df_pe_calc['LG_index'] = df_hits.index
    df_pe_calc.set_index('LG_index', inplace=True)
    df_pe_calc.fillna(0)

    ############################################################################################################
    
    """  
    DR Counts from the DaDr_Counts word document
    
    Note: 23 and 52 are automatically counted regardless of data availability; 22 removed from Eo & Fl as is not 
    testable
    
    Eo = 10 + (14|15) + 16 + 20 + 23 = 5  
    Fl = 13 + 17 + 18 + 19 + 20 + 23 = 6
    HA = (36|45) + (42|43) + 45 + (47|48|49) + 50 + 51+ 52 + 53 + 54 = 9
    HP = (36|45) + (42|43) + 45 + (47|48|49) + 50 + 51 + 52 + 53 + 55 + 56 + (46|57) = 11
    MA = 36 + (42|43) + 44 + (48|49) + 50 + 51 + 52 + 53 + 54 = 9
    MP = 36 + (42|43) + 44 + (48|49) + 50 + 51 + 52 + 53 + 55 + 56 + 57 = 11
    
    # These are intermediates for applying the OR (|) operator 
    '_DA_HA_36_45' == 'DA_HA_NE_CID36' | 'DA_HA_UD_CID45'  
    '_DA_HA_42_43' == 'DA_HA_LG_CID42' | 'DA_HA_UD_CID43' 
    '_DA_HA_47_48_49' == 'DA_HA_LG_CID47' | 'DA_HA_LG_CID48' | 'DA_HA_LG_CID49'
    '_DA_HP_36_45' == 'DA_HP_NE_CID36' | 'DA_HP_UD_CID45'
    '_DA_HP_42_43' == 'DA_HP_LG_CID42' | 'DA_HP_UD_CID43'
    '_DA_HP_47_48_49' == 'DA_HP_LG_CID47' | 'DA_HP_LG_CID48' | 'DA_HP_LG_CID49'
    '_DA_HP_46_57' == 'DA_HP_LG_CID46' | 'DA_HP_LG_CID57'
    
    '_DA_MA_42_43' == 'DA_MA_LG_CID42' | 'DA_MA_UD_CID43' 
    '_DA_MA_48_49' == 'DA_MA_LG_CID48' | 'DA_MA_LG_CID49'
    
    '_DA_MP_42_43' == 'DA_MP_LG_CID42' | 'DA_MP_UD_CID43'
    '_DA_MP_48_49' == 'DA_MP_LG_CID48' | 'DA_MP_LG_CID49'
    """
    
    # DR components       
    dr_eo = ['DA_Eo_LD_CID10', 'DA_Eo_LG_CID14', 'DA_Eo_LD_CID16', 'DA_Eo_NT_CID20', 'DA_Eo_NT_CID23']
    dr_fl = ['DA_Fl_NE_CID13', 'DA_Fl_LD_CID17', 'DA_Fl_NT_CID18', 'DA_Fl_LD_CID19', 'DA_Fl_NT_CID20', 'DA_Fl_NT_CID23']
    
    dr_ha = ['_DA_HA_36_45', '_DA_HA_42_43', 'DA_HA_UD_CID45', '_DA_HA_47_48_49', 'DA_HA_LG_CID50', 'DA_HA_NT_CID51',
             'DA_HA_LG_CID52', 'DA_HA_NT_CID53', 'DA_HA_LG_CID54']
    
    dr_hp = ['_DA_HP_36_45', '_DA_HP_42_43', 'DA_HP_UD_CID45', '_DA_HP_47_48_49', 'DA_HP_LG_CID50', 'DA_HP_NT_CID51',
             'DA_HP_LG_CID52', 'DA_HP_NT_CID53', 'DA_HP_NT_CID55', 'DA_HP_LG_CID56', '_DA_HP_46_57']
    
    dr_ma = ['DA_MA_NE_CID36', '_DA_MA_42_43', 'DA_MA_NT_CID44', '_DA_MA_48_49', 'DA_MA_LG_CID50', 'DA_MA_NT_CID51',
             'DA_MA_LG_CID52', 'DA_MA_NT_CID53', 'DA_MA_LG_CID54']
    # DR_MP: Resolved discrepancy between google sheet and DR word document. On the Google sheet 48 and 49 were listed
    #        as MA;HA.  Corrected to MA;MP;HA;HP.
    dr_mp = ['DA_MP_NE_CID36', '_DA_MP_42_43', 'DA_MP_NT_CID44', '_DA_MP_48_49', 'DA_MP_LG_CID50', 'DA_MP_NT_CID51',
             'DA_MP_LG_CID52', 'DA_MP_NT_CID53', 'DA_MP_NT_CID55', 'DA_MP_LG_CID56', 'DA_MP_LG_CID57'] 
    
    dr_types = [dr_eo, dr_fl, dr_ha, dr_hp, dr_ma, dr_mp]  # A list of required components (DR) for each mechanism type
    dr_labels = ['DR_Eo', 'DR_Fl', 'DR_HA', 'DR_HP', 'DR_MA', 'DR_MP']  # A list of required components (DR) for each
    #                                                                   # mechanism type

    ############################################################################################################

    # Generic assignment for all cells
    # df_PE_calc['DA_Eo_NT_CID20'] = True  # Accumulation of peat # No specific data for this component, data must
    #                                      # prove ash was deposited at the same time of peat accumulation (ex. same
    #                                      # formation). # DJ
    # df_PE_calc['DA_Fl_NT_CID20'] = True  # Accumulation of peat # No specific data for this component, data must prove
    #                                      # ash was deposited at the same time of peat accumulation (ex. same
    #                                      # formation). # DJ

    # df_PE_calc['DA_Fl_NT_CID22'] = True  # Burial of peat # Presence of coal is proof that there was burial of peat,
    #                                      # use either this or CID23, not both for DA count. #DJ.

    df_pe_calc['DA_Eo_NT_CID23'] = True  # Conversion of peat to coal # using this component to represent that there is
    #                                    # coal present in the study area #DJ.

    df_pe_calc['DA_Fl_NT_CID23'] = True  # Conversion of peat to coal # using this component to represent that there is
    #                                    # coal present in the study area #DJ.

    df_pe_calc['DA_HA_LG_CID52'] = True  # Coal and/or related strata # using this component to represent that there is
    #                                    # coal present in the study area #DJ.
    df_pe_calc['DA_HP_LG_CID52'] = True  # Coal and/or related strata # using this component to represent that there is
    #                                    # coal present in the study area #DJ.
    df_pe_calc['DA_MA_LG_CID52'] = True  # Coal and/or related strata # using this component to represent that there is
    #                                    # coal present in the study area #DJ.
    df_pe_calc['DA_MP_LG_CID52'] = True  # Coal and/or related strata # using this component to represent that there is
    #                                    # coal present in the study area #DJ.

    # Powder River Basin assignment for all cells (PRB)
    # df_PE_calc['DA_Eo_LG_CID14'] = True  # Mire downwind of volcanism (this is true for PRB) #Should not be assumed to
    #                                      # be true, data should represent this component #DJ.
    # df_PE_calc['DA_Fl_LD_CID17'] = True  # Mire in same paleo-drainage basin #Should not be assumed to be true, data
    #                                      # should represent this component #DJ.
    # df_PE_calc['DA_Fl_NT_CID18'] = True  # Mire downstream of REE source #Should not be assumed to be true, data
    #                                      # should represent this component #DJ.

    ############################################################################################################

    # Eo relevant components.  Not testable: CID15, CID21

    # Fl relevant components.  Not testable: CID17?, CID18?, CID19 (has instances of LD and NT), CID21 (has instances of
    # LD and NT)
    # QAQC: Change labels to NT for CID17, 18, 19, 21?

    # Bedrock REE deposit
    df_pe_calc['DA_Fl_NE_CID11'] = df_pe_calc[['DA_Fl_LD_CID01', 'DA_Fl_LD_CID02', 'DA_Fl_LD_CID03', 'DA_Fl_LD_CID04',
                                               'DA_Fl_LD_CID05', 'DA_Fl_LD_CID06']].max(axis=1)
    # Sed REE deposit
    df_pe_calc['DA_Fl_NE_CID12'] = df_pe_calc[['DA_Fl_LD_CID07', 'DA_Fl_LD_CID08', 'DA_Fl_LD_CID09']].max(axis=1)
    # REE source
    df_pe_calc['DA_Fl_NE_CID13'] = df_pe_calc[['DA_Fl_LD_CID10', 'DA_Fl_NE_CID11', 'DA_Fl_NE_CID12']].max(axis=1)
  
    # HA relevant components.  Not testable: CID51, CID53, CID59

    # Alkaline volcanic ash
    df_pe_calc['DA_HA_NE_CID33'] = df_pe_calc[['DA_HA_UD_CID37', 'DA_HA_UD_CID38', 'DA_HA_UD_CID39',
                                               'DA_HA_UD_CID40', 'DA_HA_UD_CID41']].max(axis=1)
    # Bedrock REE deposit
    df_pe_calc['DA_HA_NE_CID34'] = df_pe_calc[['DA_HA_LD_CID24', 'DA_HA_LD_CID25', 'DA_HA_LD_CID26',
                                               'DA_HA_LD_CID27', 'DA_HA_LD_CID28', 'DA_HA_LD_CID29']].max(axis=1)
    # Sed REE deposit
    df_pe_calc['DA_HA_NE_CID35'] = df_pe_calc[['DA_HA_LD_CID30', 'DA_HA_LD_CID31', 'DA_HA_LD_CID32']].max(axis=1)
    # REE source
    df_pe_calc['DA_HA_NE_CID36'] = df_pe_calc[['DA_HA_NE_CID33', 'DA_HA_NE_CID34', 'DA_HA_NE_CID35']].max(axis=1)
    # Placeholder for combination of 36 OR 45
    df_pe_calc['_DA_HP_36_45'] = df_pe_calc[['DA_HA_NE_CID36', 'DA_HA_NE_CID45']].max(axis=1)
    # Placeholder for combination of 42 OR 43
    df_pe_calc['_DA_HA_42_43'] = df_pe_calc[['DA_HA_LG_CID42', 'DA_HA_UD_CID43']].max(axis=1)
    # Placeholder for combination of 47 OR 48 OR 49
    df_pe_calc['_DA_HA_47_48_49'] = df_pe_calc[['DA_HA_LG_CID47', 'DA_HA_LG_CID48', 'DA_HA_LG_CID49']].max(axis=1)

    # HP relevant components.  Not testable: CID51, CID53, CID55, CID58
    # Alkaline volcanic ash
    df_pe_calc['DA_HP_NE_CID33'] = df_pe_calc[['DA_HP_UD_CID37', 'DA_HP_UD_CID38', 'DA_HP_UD_CID39',
                                               'DA_HP_UD_CID40', 'DA_HP_UD_CID41']].max(axis=1)
    # Bedrock REE deposit
    df_pe_calc['DA_HP_NE_CID34'] = df_pe_calc[['DA_HP_LD_CID24', 'DA_HP_LD_CID25', 'DA_HP_LD_CID26',
                                               'DA_HP_LD_CID27', 'DA_HP_LD_CID28', 'DA_HP_LD_CID29']].max(axis=1)
    # Sed REE deposit
    df_pe_calc['DA_HP_NE_CID35'] = df_pe_calc[['DA_HP_LD_CID30', 'DA_HP_LD_CID31', 'DA_HP_LD_CID32']].max(axis=1)
    # REE source
    df_pe_calc['DA_HP_NE_CID36'] = df_pe_calc[['DA_HP_NE_CID33', 'DA_HP_NE_CID34', 'DA_HP_NE_CID35']].max(axis=1)
    # Dissolve phosphorus
    df_pe_calc['DA_HP_NE_57_46'] = df_pe_calc[['DA_HP_LG_CID57', 'DA_HP_LG_CID46']].max(axis=1)
    # Placeholder for combination of 36 OR 45
    df_pe_calc['_DA_HP_36_45'] = df_pe_calc[['DA_HP_NE_CID36', 'DA_HP_UD_CID45']].max(axis=1)
    # Placeholder for combination of 42 OR 43
    df_pe_calc['_DA_HP_42_43'] = df_pe_calc[['DA_HP_LG_CID42', 'DA_HP_UD_CID43']].max(axis=1)
    # Placeholder for combination of 47 OR 48 OR 49
    df_pe_calc['_DA_HP_47_48_49'] = df_pe_calc[['DA_HP_LG_CID47', 'DA_HP_LG_CID48', 'DA_HP_LG_CID49']].max(axis=1)
    # Placeholder for combination of 46 OR 57
    df_pe_calc['_DA_HP_46_57'] = df_pe_calc[['DA_HP_LG_CID46', 'DA_HP_LG_CID57']].max(axis=1)

    # MA relevant components.  Not testable:  CID44, CID47, CID48, CID49, CID51, CID53, CID59
    # Alkaline volcanic ash
    df_pe_calc['DA_MA_NE_CID33'] = df_pe_calc[['DA_MA_UD_CID37', 'DA_MA_UD_CID38', 'DA_MA_UD_CID39',
                                               'DA_MA_UD_CID40', 'DA_MA_UD_CID41']].max(axis=1)
    # Bedrock REE deposit
    df_pe_calc['DA_MA_NE_CID34'] = df_pe_calc[['DA_MA_LD_CID24', 'DA_MA_LD_CID25', 'DA_MA_LD_CID26',
                                               'DA_MA_LD_CID27', 'DA_MA_LD_CID28', 'DA_MA_LD_CID29']].max(axis=1)
    # Sed REE deposit
    df_pe_calc['DA_MA_NE_CID35'] = df_pe_calc[['DA_MA_LD_CID30', 'DA_MA_LD_CID31', 'DA_MA_LD_CID32']].max(axis=1)
    # REE source
    df_pe_calc['DA_MA_NE_CID36'] = df_pe_calc[['DA_MA_NE_CID33', 'DA_MA_NE_CID34', 'DA_MA_NE_CID35']].max(axis=1)
    # Placeholder for combination of 42 OR 43
    df_pe_calc['_DA_MA_42_43'] = df_pe_calc[['DA_MA_LG_CID42', 'DA_MA_UD_CID43']].max(axis=1)
    # Placeholder for combination of 48 OR 49
    df_pe_calc['_DA_MA_48_49'] = df_pe_calc[['DA_MA_LG_CID48', 'DA_MA_LG_CID49']].max(axis=1)

    # MP relevant components.  Not testable: CID44, CID47, CID48, CID49, CID51, CID53, CID55, CID58
    # Alkaline volcanic ash
    df_pe_calc['DA_MP_NE_CID33'] = df_pe_calc[['DA_MP_UD_CID37', 'DA_MP_UD_CID38', 'DA_MP_UD_CID39',
                                               'DA_MP_UD_CID40', 'DA_MP_UD_CID41']].max(axis=1)
    # Bedrock REE deposit
    df_pe_calc['DA_MP_NE_CID34'] = df_pe_calc[['DA_MP_LD_CID24', 'DA_MP_LD_CID25', 'DA_MP_LD_CID26',
                                               'DA_MP_LD_CID27', 'DA_MP_LD_CID28', 'DA_MP_LD_CID29']].max(axis=1)
    # Sed REE deposit
    df_pe_calc['DA_MP_NE_CID35'] = df_pe_calc[['DA_MP_LD_CID30', 'DA_MP_LD_CID31', 'DA_MP_LD_CID32']].max(axis=1)
    # REE source
    df_pe_calc['DA_MP_NE_CID36'] = df_pe_calc[['DA_MP_NE_CID33', 'DA_MP_NE_CID34', 'DA_MP_NE_CID35']].max(axis=1)
    # Placeholder for combination of 42 OR 43
    df_pe_calc['_DA_MP_42_43'] = df_pe_calc[['DA_MP_LG_CID42', 'DA_MP_UD_CID43']].max(axis=1)
    # Placeholder for combination of 48 OR 49
    df_pe_calc['_DA_MP_48_49'] = df_pe_calc[['DA_MP_LG_CID48', 'DA_MP_LG_CID49']].max(axis=1)

    ############################################################################################################

    # capture lengths
    dr_lens=[len(dr) for dr in dr_types]

    # purge unused temporaries; if not, then df_pe_calc may complain
    for types in dr_types:

        # walk indices backwards so can remove unused without offsetting active index
        for i in range(len(types)-1,-1,-1):
            if types[i].startswith('_') and types[i] not in df_pe_calc:
                types.pop(i)

    # Add sum fields to dataframe
    df_pe_calc['Eo_sum'] = df_pe_calc[dr_eo].sum(axis=1)
    df_pe_calc['Fl_sum'] = df_pe_calc[dr_fl].sum(axis=1)
    df_pe_calc['HA_sum'] = df_pe_calc[dr_ha].sum(axis=1)
    df_pe_calc['HP_sum'] = df_pe_calc[dr_hp].sum(axis=1)
    df_pe_calc['MA_sum'] = df_pe_calc[dr_ma].sum(axis=1)
    df_pe_calc['MP_sum'] = df_pe_calc[dr_mp].sum(axis=1)

    # Calculate DA_sum/DR
    for i in range(len(dr_labels)):
        col = 'DA_' + dr_labels[i][3:5] + '_sum_DR'  # Assemble column heading (e.g., 'DA_Eo_sum_DR')
        df_pe_calc[col] = df_pe_calc[dr_labels[i][3:5] + '_sum'] / dr_lens[i]  # Divide mechanism sum by
                                                                               # DR (e.g., Eo_sum / DR_Eo)

    print('DR counts:')
    for lbl, typ_len in zip(dr_labels, dr_lens):
        print(f'  {lbl}: {typ_len}')

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
            test_rasters.clip_with_raster(clipping_mask)
            if raster_dir is not None:
                test_rasters.copy_rasters('GTiff', raster_dir, '_clipped.tif', GEOTIFF_OPTIONS)

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
            dr_rasters.clip_with_raster(clipping_mask)
        copies = dr_rasters.copy_rasters('GTiff', out_workspace.workspace, '.tif', GEOTIFF_OPTIONS)

        print("DA complete")

    ret = UrcWorkspace()
    for ds in copies:
        path = ds.GetDescription()
        ret[os.path.splitext(os.path.basename(path))[0]] = path
    return ret
