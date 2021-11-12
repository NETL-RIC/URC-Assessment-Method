"""Module containing methods for tasks that can be optimized to run in parallel.

This module uses the multiprocessing module to carry out parallel tasks, focusing
on SIMD problems.

External Dependencies:
    * `numpy <http://www.numpy.org/>`_

"""

from __future__ import absolute_import, division, print_function, unicode_literals

import ctypes
import time

from multiprocessing import sharedctypes, Pool, cpu_count, Queue, Value

from .compat2or3 import dict_iteritems
from .drawutils import *
from ..fuzzylogic.nodata_handling import NoDataSentinel
from .. import fuzzylogic as fl


##############################################################################
# Entry points

def prep_raster_for_display(inbuff, minval, maxval, nodata, colors):
    """Generates a draw-friendly raster using data from an input raster.

    Utilizes multiple cores/processes.

    Args:
        inbuff (numpy.ndarray): Buffer containing data in a 2D Array.
        minval (number): The minimum value encountered in inBuff.
        maxval (number): The maximum value encountered in inBuff.
        nodata (number): The maximum value encountered in inBuff.
        colors (dict): reference color values.

    Returns:
        numpy.ndarray:  A 2D array suitable for drawing.
    """

    count = inbuff.shape[0] * inbuff.shape[1]

    # copy numpy arrays as shared types.
    g_in = sharedctypes.RawArray(_dtype_to_ctype(inbuff.dtype), inbuff.reshape(inbuff.shape[0] * inbuff.shape[1]))

    outshared = sharedctypes.RawArray(ctypes.c_uint, count)

    # job indices
    jobcount = cpu_count()
    workpool = Pool(initializer=_init_pix_for_display, initargs=(g_in, outshared, minval, maxval - minval, nodata,
                                                                 colors,), processes=jobcount)
    workpool.map(_process_pix_for_display, range(count))

    outbuff = np.ctypeslib.as_array(outshared)
    outbuff.shape = inbuff.shape

    return outbuff


def process_cells(srunner, outshape, checkinterrupt, nvsentinel):
    """Process each stack of pixels/cells in a parallel fashion.

    Args:
        srunner (model.SimRunner): Object that is executing the simulation.
        outshape (tuple): Dimensions of the output numpy.ndarrays.
        checkinterrupt (function): Handle to function to call to check for user interrupt signal.
        nvsentinel (components.core.noDataHandling.NoDataSentinel): Sentinel for handling any encountered no data
                                                                    values.

    """

    # add import here to avoid python 2.x limitation (circular import)
    from . import model

    count = outshape[0] * outshape[1]

    odcount = len(srunner._outData)
    # initialize shared inputs
    g_ins = {'keys': sorted(srunner._rasterSets), 'colCount': outshape[1], 'rowCount': outshape[0],
             'depthCount': len(srunner._rasterSets), 'sentinel': nvsentinel}
    # grab names to keep consistant
    g_ins['rasters'] = [None] * len(g_ins['keys'])
    for n, r in dict_iteritems(srunner._rasterSets):
        raw = r._data
        g_ins['rasters'][g_ins['keys'].index(n)] = sharedctypes.RawArray(_dtype_to_ctype(raw.dtype),
                                                                         raw.reshape(raw.shape[0] * raw.shape[1]))

    # load output buffers
    g_outs = [None] * odcount
    for i in range(odcount):
        raw = srunner._outData[i]
        g_outs[i] = sharedctypes.RawArray(_dtype_to_ctype(raw.dtype), raw.reshape(raw.shape[0] * raw.shape[1]))

    g_ndstats = sharedctypes.RawArray(ctypes.c_uint, count * len(srunner._rasterSets))

    jobcount = cpu_count()

    # there's a bug in Python 3.7-3.9 with an off by one issue with cpu_count on windows
    # todo; remove fix when move to Python 3.10
    # begin temp fix...
    from sys import version_info,platform
    if platform=='win32' and version_info.major <= 3 and 6 < version_info.minor < 10:
        jobcount = max(1, jobcount-4)
    # ... end temp fix

    # ids will be used to identify specific threads
    jobids = Queue()
    for i in range(jobcount):
        jobids.put(i)

    model.MdlPrint("{0} Pixels across {1} processes.".format(count, jobcount))
    lastprog = 0
    workpool = Pool(initializer=_init_processing_sr, initargs=(srunner, jobids, g_ins, g_outs, g_ndstats),
                    processes=jobcount)
    # workpool.map(_process_cell_sr, range(count))

    # loop is for showing progress
    # https://stackoverflow.com/questions/5666576/show-the-progress-of-a-python-multiprocessing-pool-map-call/5666996
    for i, msg in enumerate(workpool.imap_unordered(_process_cell_sr, range(count), (count // jobcount) + 1)):

        # check for termination, kill if needed
        try:
            checkinterrupt()
        except Exception as exc:
            workpool.terminate()
            workpool.join()
            raise exc

        currprog = (i * 100) // count
        if currprog > lastprog:
            # to prevent message flooding, only send progress update when count has advanced by 1%
            model.MdlProg(currprog)
            lastprog = currprog

        if msg is not None and len(msg) > 0:
            model.MdlPrint(msg)

    # result = workpool.map_async(_process_cell_sr,range(count))
    # result.get()
    #  finished=0
    #  while finished < count:
    #      time.sleep(1)
    #      finished=sum(progRec)
    #      model.MdlProg((finished*100)//count)
    #      while msgQ.empty()==False:
    #          model.MdlPrint(msgQ.get())
    #      model.MdlPrint(str(finished))

    model.MdlProg(100)
    # copy outputs back in to srunner

    for i, theOut in enumerate(g_outs):
        outbuff = np.ctypeslib.as_array(theOut)
        outbuff.shape = outshape
        srunner._outData[i] = outbuff

    out_ndstats = np.ctypeslib.as_array(g_ndstats)
    out_ndstats.shape = (outshape[0], outshape[1], len(srunner._rasterSets))
    srunner._outStats['noData'] = out_ndstats


############################################################################
# Utilities

# -- Image processing

def _init_pix_for_display(inshared, outshared, minval, diff, nodata, colors):
    """Initializes work thread for pixel conversion process.

    Args:
        inshared (multiprocessing.sharedctypes.RawArray): Shared input 1D-array.
        outshared (multiprocessing.sharedctypes.RawArray): Shared output 1D-array.
        minval (number): The minimum value to be encountered.
        diff (number): The difference between the maxval and minval.
        nodata (number): The value that represents a pixel containing no data.
        colors (dict): reference color values.
    """

    global gIn
    global gOut
    global gMinVal
    global gDiff
    global gNoData
    global gLColor
    global gHColor
    global gNDColor

    gIn = inshared
    gOut = outshared
    gMinVal = minval
    gDiff = diff
    gNoData = nodata
    gLColor = colors['lowColor']
    gHColor = colors['highColor']
    gNDColor = colors['ndColor'].uint32_argb if colors['useND'] is True else 0


def _process_pix_for_display(job):
    """Converts one pixel into from input data to RGBA pixel.

    Args:
        job (int): Index of pixel to process.

    Raises:
        OverflowError: If there is a mismatch between expected and actual input type for input raster.
    """

    if abs(gNoData - gIn[job]) > 1E-4:
        # normalize pixel value to color channel value, which exists in [0,255]
        mixval = (gIn[job] - gMinVal) / gDiff

        # convert to ARGB (look like RGBA below, but that's little endian for you
        gOut[job] = mix_colors(gHColor, gLColor, mixval).uint32_argb

    else:
        gOut[job] = gNDColor


# -- Sim Processing

def _dtype_to_ctype(dtype):
    """Convert a numpy dType to a ctype.

    Args:
        dtype (str): string of numpy dtype to match.

    Returns:
        ctype: The matching ctype.

    Raises:
        KeyError: If inDType does not map to an existing ctype.
    """

    lookup = {'byte': ctypes.c_byte,
              'uint8': ctypes.c_ubyte,
              'uint16': ctypes.c_ushort,
              'int16': ctypes.c_short,
              'uint32': ctypes.c_uint,
              'int32': ctypes.c_int,
              'float32': ctypes.c_float,
              'float64': ctypes.c_double
              }
    return lookup[str(dtype)]

    # 'c': ctypes.c_char, 'u': ctypes.c_wchar,
    # 'b': ctypes.c_byte, 'B': ctypes.c_ubyte,
    # 'h': ctypes.c_short, 'H': ctypes.c_ushort,
    # 'i': ctypes.c_int, 'I': ctypes.c_uint,
    # 'l': ctypes.c_long, 'L': ctypes.c_ulong,
    # 'f': ctypes.c_float, 'd': ctypes.c_double
    #


def _init_processing_sr(srunner, jobids, indict, outbuffs, ndstats):
    """Initialize a process for processing cells.

    Args:
        srunner (model.SimRunner): The object managing the simulation run.
        jobids (multithread.Queue): A queue of unique ids to assign to each process as the come on-line.
        indict (dict): Dictionary of inbound arguments.
        outbuffs (list): Collection of output values.
        ndstats (numpy.ndarray): Collection of statistical outputs.

    """
    global gColCount
    global gDepthCount
    global gRasters
    global gInKeys
    global gSentinel
    global gNoVal
    global gFuzzData
    global gOutKeys
    global gOuts  # from dict
    global gOutStats
    global gJobId
    global gNDStats

    gColCount = indict['colCount']
    gRasters = indict['rasters']
    gDepthCount = indict['depthCount']
    gInKeys = indict['keys']
    gSentinel = indict['sentinel']
    gNoVal = srunner._noVal
    gFuzzData = srunner.fuzzyData
    gOutKeys = srunner._outKeys

    gOuts = outbuffs
    gNDStats = ndstats

    gJobId = jobids.get(timeout=1)


def _process_cell_sr(job):
    """Process a single stack of pixels within a single process.

    Args:
        job (int): The index of the current pixel stack.

    Returns:
        str: Any messages to be reported back to the user.

    """

    # a hint for handling reduction stuff
    # https://stackoverflow.com/questions/29785427/how-to-parallel-sum-a-loop-using-multiprocessing-in-python

    allnoval = True
    t = 0
    i = job // gColCount
    j = job % gColCount
    msgs = []
    currargs = {}
    ndlookup = {}
    comboargs = {'SRC_NO_DATA': ndlookup}
    currimps = {}
    for r, n in zip(gRasters, gInKeys):
        val = r[job]
        allnoval = allnoval and val == gNoVal
        if val == gNoVal:
            val = gSentinel
        currargs[n] = val

        # noData stuff
        isnoval = isinstance(val, NoDataSentinel)
        ndlookup[n] = isnoval

        # record nodata stats
        gNDStats[(i * gColCount * gDepthCount) + (j * gDepthCount) + t] = int(isnoval)
        t += 1

    if allnoval:
        # if we have all no vals, then we are actually done here
        # and can skip to next iteration
        for theOut in gOuts:
            theOut[job] = gNoVal
        # move on to next iteration
        # MdlPrint(" --> No Data Value",False)

        return '\n'.join(msgs)

    for n, s in dict_iteritems(gFuzzData.flsets):
        try:
            currimps[n] = s.evaluate_rules(currargs)
        except fl.FuzzyNoValError as err:
            currimps[n] = err
    # - combine sets using rules(ie relative weighting).
    #    - Write final value to cell

    for n, c in dict_iteritems(gFuzzData.combiners):
        try:
            outval = c.evaluate(currimps, comboargs)

            if isinstance(outval, NoDataSentinel):
                outval = gNoVal
            gOuts[gOutKeys.index(n)][job] = outval
        except fl.FuzzyNoValError as err:
            msgs.append("cell ({0},{1}) Skipped: {2}".format(i, j, err.args[0]))
            gOuts[n][job] = gNoVal

    # gMsgQ.put("Thread {0} Count:{1}".format(gJobId, gProgRec[gJobId]))
    # msgs.append("Thread {0} Processed cell({1},{2})".format(gJobId,i,j))

    return '\n'.join(msgs)
