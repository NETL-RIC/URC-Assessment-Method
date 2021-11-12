from typing import Callable,Optional

import numpy as np
from osgeo import gdal

from .urc_common import *
from .common_utils import REE_Workspace
from .simpa_core.settings import Settings

def createShim(rasters:RasterGroup)->gdal.Dataset:
    ...

def injectURCSettings(rasters:RasterGroup,simpaSettings:Settings,outWorkspace:REE_Workspace):
    ...

def GetDSDistances(src_rasters:RasterGroup,cache_dir:Optional[str]=...,mask:Optional[np.ndarray]=...)->RasterGroup:
    ...

def RunPEScoreDS(gdbDS:gdal.Dataset,indexRasters:RasterGroup,indexMask:np.ndarray,outWorkspace : REE_Workspace,rasters_only:bool=...,postProg:Optional[Callable[[int],None]]=...):
    ...
