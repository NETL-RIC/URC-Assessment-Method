"""Module for loading and saving user-defined runtime settings."""
import json

SETTINGS_VERSION = [0, 0, 1]


def save_settings(path, out_dict):
    """Save run configuration settings to disk.

    Args:
        path (str): The path to the (*.json) file to write.
        out_dict (dict): Dict of settings to save.
    """

    dump_dict = {'version': SETTINGS_VERSION}
    dump_dict.update(out_dict)

    with open(path, 'w') as outFile:
        json.dump(dump_dict, outFile)


def load_settings(path):
    """Load saved settings from a file.

    Args:
        path (str): The path to the (*.json) file to load.

    Returns:
        dict: The settings found in the file at `path`.
    """

    with open(path, 'r') as inFile:
        in_dict = json.load(inFile)

        # grab version and do something if needed
        version = in_dict['version']

        return in_dict


def default_settings():
    """Retrieve default user settings for an initial state.

    Returns:
        dict: The default values for various settings.
    """

    return {
        'active': [0, 0],
        'display_results': False,
        'create_grid': {
            'sd_path': None,
            'ld_path': None,
            'use_sa': False,
            'sa_path': None,
            'width': 1000,
            'height': 1000,
            'out_dir': None,
            'ld_inds': 'ld_inds.tif',
            'lg_inds': 'lg_inds.tif',
            'sa_inds': 'sa_inds.tif',
            'sd_inds': 'sd_inds.tif',
            'ud_inds': 'ud_inds.tif',
            'proj_source': 'From File',
            'proj_file': None,
            'do_proj': False,
        },
        'pe_score': {
            'inpath': None,
            'index_dir': None,
            'use_clip': False,
            'clip_path': None,
            'ld_inds': 'ld_inds.tif',
            'lg_inds': 'lg_inds.tif',
            'sa_inds': 'sa_inds.tif',
            'sd_inds': 'sd_inds.tif',
            'ud_inds': 'ud_inds.tif',
            'limit_dads': False,
            'use_only': 'DA',
            'save_sub_rasters': False,
            'sub_raster_dir': None,
            'skip_calcs': False,
            'out_dir': None,
        }
    }
