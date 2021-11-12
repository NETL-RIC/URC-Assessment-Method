"""SIMPA Model engine logic.

External Dependencies:
    * `numpy <http://www.numpy.org/>`_
    * `GDAL <http://gdal.org>`_

Attributes:
    useMultiProc (bool): If true, informs the simulation to use parallel processing methods where available.
    MdlPrint (function): Function called when a new status message is emitted.
    MdlProg (function): Function called when the progress status is updated (an int in [0,100] representing approximate
                        progress).
    CheckInterrupt (function): Function called whenever the simulation thread is checking for an interrupt signal.

"""

from __future__ import absolute_import, division, print_function, unicode_literals

from .settings import Settings, load_settings
from .containers import *
import os
from .compat2or3 import *
from osgeo import gdal, ogr
import numpy as np
from ..fuzzylogic.nodata_handling import NoDataSentinel
from csv import writer as csv_writer
from . import mproc_methods as mproc

useMultiProc = False


# default print
def defaultprint(msg, newline=True):
    """The default message printing function. Prints any messages to stdout.

    Args:
        msg (str): The message to display/print/record.
        newline (bool,optional): If true, append a newline character to msg. Defaults to True.

    """
    if newline:
        print(msg)
    else:
        sys.stdout.write(msg)
        sys.stdout.flush()


# no print option (use to disable output
def noprint(msg, newline):
    """Printing function that does nothing.

    Args:
        msg (str): The message to display/print/record.
        newline (bool,optional): If true, append a newline character to msg. Defaults to True.

    """
    pass


def noprog(percent):
    """Status function that does nothing.

    Args:
        percent (int): The progress as a value in [0,100].
    """
    pass


def nointerrupt():
    """Interrupt check function that does nothing.
    """
    pass


# global print function; ressign for alternate output
MdlPrint = defaultprint
MdlProg = noprog
CheckInterrupt = nointerrupt

# we want gdal to use exceptions instead of just printing errors
gdal.UseExceptions()


class ModelRunner(object):
    """Manages and executes SIMPA simulations.

Attributes:
    settings (simpaSettings.Settings): The current set of simulation input parameters.
    fuzzyData (simpaContainers.FLData): The FLData object containing the logic to be applied to the simulation.
    outputsWritten (list): Contains dicts of record entries for any outputs written at the conclusion of a simulation.
      Value is None if no simulation has yet been run.

Args:
    defSettings (simpaSettings.Settings,optional): The settings to apply to the Simulation by default.
    """

    def __init__(self, defsettings=Settings()):
        self.settings = defsettings
        self.fuzzyData = FLData()
        self.outputsWritten = None
        self._rasterSets = {}
        self._vectorSets = {}
        self._noVal = -99999.
        # self._tmpDir="./tmp/"
        # self._tmpFiles=[]
        self.clear_outputs()

    def load_inputsfile(self, setpath):
        """Load simulation parameters from a settings file.

        Args:
            setpath (str): Path to the input settings.

        """
        MdlPrint("Loading settings...", False)
        self.settings = load_settings(setpath)
        MdlPrint("Done.")

    def run_model(self):
        """Run the simulation using the currently loaded parameters and rule sets.

        """
        MdlPrint("Initializing...", False)
        self._init_model()
        MdlPrint("Done.")

        MdlPrint("Beginning Model Run.")
        self.clear_outputs()
        outshape = self._rasterSets[list(self._rasterSets.keys())[0]].shape

        self._outStats['noData'] = np.zeros(dtype=np.uint32,
                                            shape=(outshape[0], outshape[1], len(self._rasterSets.keys())))
        CheckInterrupt()

        self._outKeys = list(self.fuzzyData.combiners.keys())
        # use dictionary to ensure mappable access to bandData
        # ensure alpha order

        # Decompose input data into finest common denominator(grid size).
        # ...
        # Discrete modular processes:
        #  - Map data into inputs.
        bandcount = len(self.fuzzyData.combiners)
        self._outData = [np.full(outshape, self._noVal) for _ in range(bandcount)]
        self._outKeys.sort()

        # initialize sentinel
        nvsentinel = NoDataSentinel()
        if self.settings.ndMethod == 'ignore':
            nvsentinel.ignore = True
            nvsentinel.subVal = None
        elif self.settings.ndMethod == 'passthrough':
            nvsentinel.ignore = False
            nvsentinel.subVal = None
        elif self.settings.ndMethod == 'substitute':
            nvsentinel.ignore = False
            nvsentinel.subVal = self.settings.ndSubVal
        if not useMultiProc:
            self._process_cells(outshape, nvsentinel)
        else:
            MdlPrint('Running in parallel using CPU threading.')
            mproc.process_cells(self, outshape, CheckInterrupt, nvsentinel)

        MdlPrint("\nDone")
        MdlPrint("Model run complete.")
        MdlProg(100)
        # attach to storage

        # these attachments should be based on combos from sources
        # for now, assume they are all the same
        self._outShape = outshape
        self._outProj = self._rasterSets[list(self._rasterSets.keys())[0]].projection
        self._outTrans = self._rasterSets[list(self._rasterSets.keys())[0]].geotransform

    def clear_outputs(self):
        """Clear all output attributes/variables.
        """

        self._outData = None
        self._outShape = None
        self._outTrans = None
        self._outProj = None
        self._outKeys = None
        self._outStats = {}
        self.outputsWritten = None

    def write_outputs(self):
        """Write out simulation results after a simulation run.

        Raises:
            simpaContainers.SimpaExection: If method is called before the simulation has been run or there are no
              outputs to write.

        """
        # Intended to assess relative risk.
        #  - Spatial output, raster, or vector, with values per cell.
        # Risk / decision value.
        # Confidence value.
        # Optional: intermediate values(?)

        if self._outData is None:
            raise SimpaException("No outputs to write")

        MdlPrint("Writing outputs:")
        self._write_raster(self.settings.get_absoutputdir() + os.path.sep)
        self._write_stats(self.settings.get_absoutputdir() + os.path.sep)
        MdlPrint("Done.")

    def _process_cells(self, outshape, nvsentinel):
        """Process each cell in a serial fashion.

        Args:
            outshape (list): List with x,y dimensions for outputs.
            nvsentinel (components.simpa_core.noDataHandling.NoDataSentinel): Sentinel for handling any encountered no
                                                                              data values.
        """

        banddict = {k: d for k, d in zip(self._outKeys, self._outData)}

        currargs = {}
        currimps = {}
        fl.noDataValue = self._noVal
        #  - Per cell:

        ndlookup = {}
        comboargs = {'SRC_NO_DATA': ndlookup}

        CheckInterrupt()
        # This is the spot ideal for multiprocessing
        MdlPrint("Processing cells...")
        count = 0
        prog = 0
        denom = outshape[0] * outshape[1]
        for i in range(outshape[0]):
            for j in range(outshape[1]):
                # MdlPrint("\n\tProcessing cell ({0},{1})".format(i,j),False)
                #    - Run relevant fuzzy logic sets
                allnoval = True
                t = 0
                for n, r in dict_iteritems(self._rasterSets):
                    val = r[i, j]
                    allnoval = allnoval and val == self._noVal
                    if val == self._noVal:
                        val = nvsentinel
                    currargs[n] = val

                    # noData stuff
                    isnoval = isinstance(val, NoDataSentinel)
                    ndlookup[n] = isnoval
                    self._outStats['noData'][i, j, t] = int(isnoval)
                    t += 1

                if allnoval:
                    # if we have all no vals, then we are actually done here
                    # and can skip to next iteration
                    for k in self._outKeys:
                        banddict[k][i, j] = self._noVal
                    # move on to next iteration
                    # MdlPrint(" --> No Data Value",False)
                    continue

                for n, s in dict_iteritems(self.fuzzyData.flsets):
                    try:
                        currimps[n] = s.evaluate_rules(currargs)
                    except fl.FuzzyNoValError as err:
                        currimps[n] = err
                # - combine sets using rules(ie relative weighting).
                #    - Write final value to cell
                for n, c in dict_iteritems(self.fuzzyData.combiners):
                    try:
                        outval = c.evaluate(currimps, comboargs)
                        if isinstance(outval, NoDataSentinel):
                            outval = self._noVal
                        banddict[n][i, j] = outval
                    except fl.FuzzyNoValError as err:
                        MdlPrint("cell ({0},{1}) Skipped: {2}".format(i, j, err.args[0]))
                        banddict[n][i, j] = self._noVal

                count += 1
                newprog = int((count / denom) * 100)
                if newprog > prog:
                    prog = newprog
                    MdlProg(prog)
                    MdlPrint("Processed {0} cells...".format(count))
                CheckInterrupt()

    def _init_model(self):
        """Initialize the model:
             * Load input rasters.
             * Ignore any rasters that are not referred to in the Fuzzy Logic rules.
             * Prime the output containers.
             * Compile Fuzzy Logic rules.

        Raises:
            ValueError: If an input's `type` field is not 'vector' or 'raster'.

        """
        # load fuzzy logic values
        # load fuzzy logic combiners
        self.fuzzyData = FLData(self.settings.flSets, self.settings.flCombiners)

        # use a set to grab 1 instance of each input variable name found in each of the rule sets
        inp_set = set()

        # prime FuzzyLogic rules
        for _, fls in dict_iteritems(self.fuzzyData.flsets):
            fls.import_rules()
            for r in fls.rules:
                for n in r.foundinputs:
                    inp_set.add(n)

        # load all the data from the settings here
        # load data files (shp, raster, whatever)
        self._rasterSets.clear()

        indir = self.settings.get_absinputdir()

        rasters = []
        for d in self.settings.dataInputs:
            # only load raster if requested by the rule
            if d['fieldName'] not in inp_set:
                continue

            preloaded = d.get('preloaded', None)
            if preloaded is None:
                fullpath = os.path.join(indir,d['baseName']) if not os.path.isabs(d['baseName']) else d['baseName']
            datatype = d['type']

            if datatype == 'raster':

                if preloaded is None:
                    rasters.append([gdal.Open(fullpath), d['fieldName'], d['band']])
                else:
                    rasters.append([preloaded, d['fieldName'], d['band']])
                # self._add_rasterdata(fullpath,d['fieldName'],d['noVal'],d['band'])
            elif datatype == 'vector':
                self._add_vectordata(fullpath, d['fieldName'], d['col'])
            else:
                raise ValueError("unknown data type: '" + datatype + "'")

        self._prepare_rasters(rasters)

        for r in rasters:
            self._add_rasterdata(*r)

        # once the data sets are loaded, close them
        for r in rasters:
            r[0] = None
        del rasters

        # remove any preloads so as to not upset parallel code
        self.settings.purge_preloaded()

        # self.fuzzyData, errs=FLData.fldata_from_files(fullFLPaths, fullCPaths)

    # if errs is not None:
    #     raise SimpaException("Errors reading fuzzy logic data", *errs, simpaObj=self.fuzzyData)

    # match combiners and fl based on file names
    # allow orphaned FLs, but not Combiners
    # ...?

    def _add_rasterdata(self, ds, fieldname, nullval, bandind=1):
        """Add a Raster dataset to the simulation.

        Notes:
            Relies on the GDAL package to do the projection dirty work.

        Args:
            ds (osgeo.gdal.Dataset): The data to load.
            fieldname (str): The integer name of the field.
            nullval (float): The number used to indicate a cell without a value.
            bandind (int,optional): A 1-based index for which band to load. Defaults to 1.

        Raises:
            ValueError: If bandind does not refer to a valid band index in ds.
            FileNotFoundError: If ds is None.

        """

        if ds is None:
            raise FileNotFoundError()

        band = ds.GetRasterBand(bandind)
        if band is None:
            raise ValueError("band '" + str(bandind) + "' not found.")

        raw = band.ReadAsArray()
        # bandnv=band.GetNoDataValue()
        # # Ensure everyone is using the same no data value flag.
        # if bandnv!=self._noVal:
        #     for a in range(raw.shape[0]):
        #         for b in range(raw.shape[1]):
        #             if raw[a,b]==bandnv:
        #                 raw[a,b]=self._noVal
        # assign data
        grid = GriddedData(fieldname, data=raw, transform=ds.GetGeoTransform(), projection=ds.GetProjection(),
                           noVal=nullval)
        self._rasterSets[fieldname] = grid

    def _add_vectordata(self, inpath, colname):
        """This is presently a stub.

        Todo:
            Implement this method for vector/sparse data when we know how we want to interact with it.
        """
        pass

    def _write_raster(self, path):
        """Write out raster outputs.

        Notes:
            Relies on GDAL to do the writing.

        Args:
            path (str): Path to a parent dierctory.

        """
        # https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html
        driver = gdal.GetDriverByName('GTiff')
        self.outputsWritten = []
        for k, d in zip(self._outKeys, self._outData):
            rasterpath = path + k + '.tif'
            MdlPrint("\t" + rasterpath)
            outraster = driver.Create(rasterpath, self._outShape[1], self._outShape[0], 1, gdal.GDT_Float32,
                                      options=['GEOTIFF_KEYS_FLAVOR=ESRI_PE'])
            outraster.SetGeoTransform(self._outTrans)
            outraster.SetProjection(self._outProj)
            theband = outraster.GetRasterBand(1)
            theband.SetNoDataValue(self._noVal)
            theband.WriteArray(d)
            try:
                theband.ComputeRasterMinMax(False)
            except RuntimeError:
                pass
            theband.FlushCache()
            self.outputsWritten.append({'fieldName': k,
                                        'baseName': rasterpath,
                                        'band': 1,
                                        'type': 'raster'})
            # stats = theband.GetStatistics(True, True)
            # MdlPrint("{0} stats: min={1} max={2} mean={3} stdDev={4}".format(self._outKeys[i],*stats))

    def _write_stats(self, path):
        """Write statistical outputs, such as noData info

        Args:
            path (str): Absolute path to output directory.
        """

        nd_rasterdata = np.empty(self._outShape, np.uint32)
        MdlPrint("Writing stat outputs...", False)

        # write noData stuff
        nd_csvpath = path + 'nodata_summary.csv'
        with open(nd_csvpath, 'w') as outFile:
            header = ['oid', 'row', 'column', 'total'] + list(self._rasterSets.keys())
            # Windows is dumb, and therefore we need to be clear on what line ending we need.
            # not setting this will result in a bunch of extra newlines.
            writer = csv_writer(outFile, lineterminator='\n')
            writer.writerow(header)

            ndstats = self._outStats['noData']
            t = 0
            for r in range(self._outShape[0]):
                for c in range(self._outShape[1]):
                    tot = sum(ndstats[r, c])
                    nd_rasterdata[r, c] = tot
                    writer.writerow([str(t), str(r), str(c), str(tot)] + [str(x) for x in ndstats[r, c]])

                    t += 1
        self.outputsWritten.append({'fieldName': 'nodata_summary',
                                    'baseName': nd_csvpath,
                                    'type': 'csv'})

        driver = gdal.GetDriverByName('GTiff')

        rasterpath = path + 'nodata_tally.tif'
        outraster = driver.Create(rasterpath, self._outShape[1], self._outShape[0], 1, gdal.GDT_UInt32,
                                  options=['GEOTIFF_KEYS_FLAVOR=ESRI_PE'])
        outraster.SetGeoTransform(self._outTrans)
        outraster.SetProjection(self._outProj)
        theband = outraster.GetRasterBand(1)
        theband.SetNoDataValue(-99999)
        theband.WriteArray(nd_rasterdata)
        # try:
        theband.ComputeRasterMinMax(False)
        # except RuntimeError:
        #     pass
        theband.FlushCache()
        self.outputsWritten.append({'fieldName': 'nodata_tally',
                                    'baseName': rasterpath,
                                    'band': 1,
                                    'type': 'raster'})

        MdlPrint("Done")

    def _prepare_rasters(self, rasterdata):
        """Find common projection and pixel resolution to allow comparison between rasters.

        Generates a copy of each raster warped to be a consistant resolution and using the same no data value. The
        copies are stored in SIMPA's tmp directory until the conclusion of the simulation.

        Notes:
            GDAL is used to do the warping.

        Args:
            rasterdata (list): A list of raster data objects to be used as inputs in the simulation.


        """

        if len(rasterdata) == 0:
            return
        if len(rasterdata) <= 1:
            old_noval = rasterdata[0][0].GetRasterBand(rasterdata[0][2]).GetNoDataValue()
            if self._noVal != old_noval:
                oldds = rasterdata[0][0]
                opts = gdal.WarpOptions(format='VRT', dstNodata=self._noVal, srcNodata=old_noval,
                                        creationOptions=['GEOTIFF_KEYS_FLAVOR=ESRI_PE'])
                rasterdata[0][0] = gdal.Warp('', oldds, options=opts)
                # register temp files
                # self._tmpFiles += rasterdata[0][0].GetFileList()
                # close old raster
                del oldds
            return

        proj = rasterdata[0][0].GetProjection()

        # >>> dsw=gdal.Warp('warp9.tif',dsg,srcSRS=srcsrs,dstSRS=srs,width=dst.RasterXSize
        # ,height=dst.RasterYSize,dstNodata=-99999,outputBounds=[-11466180.8411,3977327.54
        # 678,-10512004.3501,4439875.96],resampleAlg="cubic")

        # find:
        # largest width, height
        # extents that enclose everyone.
        ds = rasterdata[0][0]
        width = ds.RasterXSize
        height = ds.RasterYSize
        gtrans = ds.GetGeoTransform()
        left, right, top, bottom = ModelRunner._get_raster_extents(ds)

        for i in range(1, len(rasterdata)):
            # grab the dataset

            ds = rasterdata[i][0]
            w = ds.RasterXSize
            width = width if w < width else w
            h = ds.RasterYSize
            height = height if h < height else h
            l, r, t, b = ModelRunner._get_raster_extents(ds)
            left = left if l > left else l
            right = right if r < right else r
            top = top if t < top else t
            bottom = bottom if b > bottom else b

        # warp each set to common space using specified temp directory.
        # set options consistant for all

        for rd in rasterdata:
            old_noval = rd[0].GetRasterBand(rd[2]).GetNoDataValue()
            opts = gdal.WarpOptions(format='VRT', outputBounds=(left, bottom, right, top), width=width,
                                    height=height, dstNodata=self._noVal, srcNodata=old_noval,
                                    creationOptions=['GEOTIFF_KEYS_FLAVOR=ESRI_PE'])
            oldds = rd[0]
            rd[0] = gdal.Warp('', oldds, options=opts)
            # register temp files
            # self._tmpFiles+=rasterdata[i][0].GetFileList()
            # close old raster
            # del oldds

    def _clear_tmpdir(self):
        """Clear the contents of SIMPA's tmp directory.
        """
        # for tf in self._tmpFiles:
        #     os.remove(tf)
        # self._tmpFiles.clear()

    @staticmethod
    def _get_raster_extents(ds):
        """

        Args:
            ds (osgeo.gdal.Dataset): The GDAL dataset to query.

        Returns:
            tuple: The left, right, top, and bottom extents, in that order.
        """

        # https://gis.stackexchange.com/questions/104362/how-to-get-extent-out-of-geotiff
        # [left,right,top,bottom]

        gt = ds.GetGeoTransform()
        left = gt[0]
        top = gt[3]
        right = left + gt[1] * ds.RasterXSize
        bottom = top + gt[5] * ds.RasterYSize

        return left, right, top, bottom
