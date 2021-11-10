from typing import Callable,Optional

import numpy as np
from osgeo import gdal

from common_utils import *

def GetDSDistances(src_rasters:RasterGroup,cache_dir:Optional[str]=...,mask:Optional[np.ndarray]=...)->RasterGroup:
    ...

def RunPEScoreDS(gdbDS:gdal.Dataset,indexRasters:RasterGroup,indexMask:np.ndarray,outWorkspace : REE_Workspace,rasters_only:bool=...,postProg:Optional[Callable[[int],None]]=...):
    ...
