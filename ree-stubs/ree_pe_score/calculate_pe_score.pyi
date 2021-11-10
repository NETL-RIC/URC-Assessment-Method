import sys
from osgeo import gdal,ogr
import pandas
from typing import Tuple,List,Union,Dict,Callable,Optional,Protocol,Any,Set
from .common_utils import REE_Workspace,RasterGroup
import numpy as np


def CollectIndexRasters(inWorkspace:REE_Workspace)->RasterGroup:
    ...

def RunPEScore(gdbPath : str,inWorkspace : REE_Workspace,outWorkspace : REE_Workspace,doDA:bool,doDS:bool,rasters_only:bool,postProg:Optional[Callable[[int],None]]=...):
    ...

