
from typing import Callable,Optional

import pandas
import numpy as np
from osgeo import gdal

from common_utils import *
from urc_common import RasterGroup

def CalcSum(df_hits: pandas.DataFrame)->pandas.DataFrame:
    ...

def RunPEScoreDA(gdbDS:gdal.Dataset,indexRasters:RasterGroup,indexMask:np.ndarray,outWorkspace: REE_Workspace,rasters_only:bool=...,postProg:Optional[Callable[[int],None]]=...):
    ...