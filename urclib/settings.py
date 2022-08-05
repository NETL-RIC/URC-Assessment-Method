import json

SETTINGS_VERSION=[0,0,1]

def saveSettings(path, outDict):

    dumpDict = {'version':SETTINGS_VERSION}
    dumpDict.update(outDict)

    with open(path,'w') as outFile:
        json.dump(dumpDict,outFile)


def loadSettings(path):

    with open(path,'r') as inFile:
        inDict = json.load(inFile)

        # grab version and do something if needed
        version = inDict['version']

        return inDict

def defaultSettings():

    return {
        'active':[0,0],
        'display_results':False,
        'create_grid': {
            'sd_path':None,
            'ld_path':None,
            'width':1000,
            'height':1000,
            'out_dir':None,
            'ld_inds':'ld_inds.tif',
            'lg_inds': 'lg_inds.tif',
            'sd_inds': 'sd_inds.tif',
            'ud_inds': 'ud_inds.tif',
            'proj_source':'From File',
            'proj_file':None,
            'do_proj':False,
        },
        'pe_score': {
            'inpath':None,
            'index_dir':None,
            'use_clip':False,
            'clip_path':None,
            'ld_inds':'ld_inds.tif',
            'lg_inds': 'lg_inds.tif',
            'sd_inds': 'sd_inds.tif',
            'ud_inds': 'ud_inds.tif',
            'limit_dads':False,
            'use_only':'DA',
            'save_sub_rasters':False,
            'sub_raster_dir':None,
            'skip_calcs':False,
            'out_dir': None,
        }
    }